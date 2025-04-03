from django.utils.decorators import method_decorator
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from django.http import FileResponse
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from .models import CalculationRequest, CalculationDetail, BatchCalculationTask
from .serializers import (
    CalculationRequestSerializer,
    CalculationDetailSerializer,
    BatchCalculationRequestSerializer,
    BatchCalculationTaskSerializer,
    SingleCalculationRequestSerializer,
    BatchCalculationResultSerializer,
    ProductComparisonRequestSerializer,
    SingleCalculationSerializer,
    BatchCalculationSerializer,
    ProductComparisonSerializer,
    CalculationRequestModelSerializer
)
from .services import (
    CalculationService,
    BatchService,
    CacheService,
    ValidationService,
    AuditService,
    BaseCalculationService
)
from .tasks import process_batch_calculation, export_calculation_results
from apps.postal_codes.models import ZipZone
from apps.products.models import Product
from apps.core.utils import generate_request_id, error_response, success_response
from apps.core.views import BaseAPIView
from apps.core.exceptions import (
    InvalidParameterException,
    ProductNotFoundException,
    CalculationException,
    handle_calculation_error
)
from apps.core.decorators import db_connection_retry
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_cookie
import logging
import os
from apps.calculator.calculator import Calculator
from apps.core.config import get_setting

logger = logging.getLogger(__name__)


class BatchCalculationTaskViewSet(viewsets.ModelViewSet):
    """批量计算任务视图集"""
    queryset = BatchCalculationTask.objects.all()
    serializer_class = BatchCalculationTaskSerializer
    permission_classes = [IsAuthenticated]
    basename = 'batchcalculationtask'
    router_name = 'calculator'
    lookup_field = 'task_id'
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def perform_create(self, serializer):
        """创建任务时的额外处理"""
        serializer.save(
            task_id=generate_request_id('BATCH'),
            status='PENDING',
            created_by=self.request.user
        )
    
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    @action(detail=True, methods=['get'], url_path='progress', url_name='progress')
    def progress(self, request, task_id=None):
        """获取任务进度"""
        try:
            task = self.get_object()
            return Response({
                'status': task.status,
                'progress': task.progress,
                'total_records': task.total_records,
                'processed_records': task.processed_records,
                'success_records': task.success_records,
                'error_records': task.error_records,
                'last_error': task.last_error
            })
        except BatchCalculationTask.DoesNotExist:
            return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    @action(detail=True, methods=['get'], url_path='export', url_name='export')
    def export(self, request, task_id=None):
        """导出任务结果"""
        try:
            task = self.get_object()
            
            # 检查任务状态
            if task.status != 'COMPLETED':
                return Response({'error': '任务尚未完成'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 启动导出任务
            export_task = export_calculation_results.delay(task.id)
            
            return Response({
                'task_id': export_task.id,
                'message': '导出任务已提交'
            })
            
        except BatchCalculationTask.DoesNotExist:
            return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"导出任务结果失败: {str(e)}")
            return Response({'error': '导出失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'], url_path='download-result', url_name='download-result')
    def download_result(self, request, task_id=None):
        """下载计算结果"""
        try:
            task = self.get_object()
            
            # 检查任务状态和文件是否存在
            if not task.result_file or not os.path.exists(task.result_file):
                return Response({'error': '结果文件不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 返回文件响应
            response = FileResponse(
                open(task.result_file, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(task.result_file)}"'
            return response
        except BatchCalculationTask.DoesNotExist:
            return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"下载结果文件失败: {str(e)}")
            return Response({'error': '下载失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'], url_path='download-errors', url_name='download-errors')
    def download_errors(self, request, task_id=None):
        """下载错误记录"""
        try:
            task = self.get_object()
            
            # 检查任务状态和文件是否存在
            if not task.error_file or not os.path.exists(task.error_file):
                return Response({'error': '错误记录文件不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 返回文件响应
            response = FileResponse(
                open(task.error_file, 'rb'),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="{os.path.basename(task.error_file)}"'
            return response
        except BatchCalculationTask.DoesNotExist:
            return Response({'error': '任务不存在'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"下载错误记录失败: {str(e)}")
            return Response({'error': '下载失败'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(tags=['运费计算'])
class CalculationView(APIView):
    """运费计算视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = SingleCalculationRequestSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation_service = CalculationService()

    @extend_schema(
        request=SingleCalculationRequestSerializer,
        responses={200: SingleCalculationSerializer},
        description='单件运费计算'
    )
    @handle_calculation_error
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def post(self, request, *args, **kwargs):
        """处理运费计算请求"""
        try:
            # 日志记录请求信息
            logger.info(f"接收到运费计算请求: {request.data}")
            
            # 验证请求数据
            serializer = self.serializer_class(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # 保证邮编不为空
            validated_data = serializer.validated_data
            if not validated_data.get('from_postal'):
                raise InvalidParameterException("起始邮编不能为空")
            if not validated_data.get('to_postal'):
                raise InvalidParameterException("目的地邮编不能为空")
                
            # 计算运费
            result = self.calculation_service.calculate_single(validated_data)
            
            # 确保计算详情字段存在
            if 'calculation_details' not in result or not result['calculation_details']:
                logger.info("API响应没有计算详情，添加默认详情")
                
                # 创建默认计算详情
                details = [
                    {
                        'step': '基本信息',
                        'description': '计算请求的基本参数',
                        'details': f"""
                        产品ID: {result.get('product_code', 'N/A')}
                        起始邮编: {validated_data.get('from_postal', '')}
                        目的邮编: {validated_data.get('to_postal', '')}
                        重量: {validated_data.get('weight', '')} {validated_data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                        尺寸: {validated_data.get('length', '0')}x{validated_data.get('width', '0')}x{validated_data.get('height', '0')} 
                        计算日期: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                        """
                    },
                    {
                        'step': '重量计算',
                        'description': '计算体积重和计费重量',
                        'details': f"""
                        实际重量: {validated_data.get('weight', '')} {validated_data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                        体积重量: {result.get('volume_weight', '0')} 
                        计费重量: {result.get('chargeable_weight', '0')}
                        """
                    },
                    {
                        'step': '基础运费计算',
                        'description': '计算基础运费',
                        'details': f"""
                        费用类型: 基础运费
                        金额: {result.get('base_fee', '0')}
                        区域: {result.get('zone', 'N/A')}
                        """
                    },
                    {
                        'step': '燃油附加费计算',
                        'description': '根据燃油费率计算燃油附加费',
                        'details': f"""
                        费用名称: 燃油附加费
                        金额: {result.get('fuel_surcharge', '0')}
                        """
                    },
                    {
                        'step': '费用汇总',
                        'description': '计算总费用',
                        'details': f"""
                        基础运费: {result.get('base_fee', '0')}
                        燃油附加费: {result.get('fuel_surcharge', '0')}
                        总费用: {result.get('total_fee', '0')} {result.get('currency', 'USD')}
                        计算公式: 总费用 = 基础运费 + 燃油附加费 + 其他附加费总和
                        """
                    }
                ]
                
                # 添加到结果中
                result['calculation_details'] = details
                logger.info(f"已添加 {len(details)} 个默认计算详情步骤")
            
            # 返回结果
            return Response(result)
            
        except InvalidParameterException as e:
            logger.warning(f"无效参数: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except ProductNotFoundException as e:
            logger.warning(f"产品不存在: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)
        except CalculationException as e:
            logger.error(f"计算失败: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            logger.exception(f"运费计算未处理异常: {str(e)}")
            return Response({"error": "服务器内部错误"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@extend_schema(tags=['运费计算'])
class BatchCalculationView(APIView):
    """批量运费计算视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = BatchCalculationRequestSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation_service = CalculationService()

    @extend_schema(
        request=BatchCalculationRequestSerializer,
        responses={200: BatchCalculationResultSerializer},
        description='批量运费计算'
    )
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def post(self, request, *args, **kwargs):
        """处理批量运费计算请求"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.calculation_service.calculate_batch(serializer.validated_data['items'])
        return Response(result)

@extend_schema(tags=['运费计算'])
class ProductComparisonView(APIView):
    """产品比较视图"""
    permission_classes = [IsAuthenticated]
    serializer_class = ProductComparisonRequestSerializer
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculation_service = CalculationService()

    @extend_schema(
        request=ProductComparisonRequestSerializer,
        responses={200: ProductComparisonSerializer},
        description='产品价格对比'
    )
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def post(self, request, *args, **kwargs):
        """处理产品比较请求"""
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = self.calculation_service.compare_products(serializer.validated_data)
        return Response(result)

class CalculatorViewSet(viewsets.ViewSet):
    """计算器视图集"""
    permission_classes = [IsAuthenticated]
    basename = 'calculation'
    router_name = 'calculator'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calculator = Calculator()  # 使用新的Calculator类
        self.logger = logging.getLogger(__name__)

    @handle_calculation_error
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def calculate_single(self, request):
        """
        单件运费计算
        """
        result = self.calculator.calculate(request.data)  # 使用新的calculate方法
        return Response({
            'status': 'success',
            'code': 'SUCCESS',
            'message': '计算完成',
            'data': result,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    @handle_calculation_error
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def calculate_batch(self, request):
        """
        批量运费计算
        """
        records = request.data.get('items', [])
        if not records:
            raise InvalidParameterException('请提供计算记录')
        
        # 这里需要实现一个批量计算方法，可以在Calculator类中添加
        # 临时方案：遍历调用单个计算
        results = []
        for record in records:
            try:
                result = self.calculator.calculate(record)
                results.append({
                    'status': 'success',
                    'data': result,
                    'error': None
                })
            except Exception as e:
                results.append({
                    'status': 'error',
                    'data': None,
                    'error': str(e)
                })
        
        return Response({
            'status': 'success',
            'code': 'SUCCESS',
            'message': '批量计算完成',
            'data': {
                'results': results,
                'total': len(records),
                'success': len([r for r in results if r['status'] == 'success']),
                'failed': len([r for r in results if r['status'] == 'error'])
            },
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

    @handle_calculation_error
    @db_connection_retry(max_retries=3, retry_delay=0.5)
    def compare_products(self, request):
        """
        产品价格对比
        """
        result = self.calculation_service.compare_products(request.data)
        return Response({
            'status': 'success',
            'code': 'SUCCESS',
            'message': '产品价格对比完成',
            'data': result,
            'timestamp': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)

class BatchCalculatorView(APIView):
    """批量计算视图"""
    permission_classes = [IsAuthenticated]
    
    def __init__(self):
        super().__init__()
        self.service = BatchService()
        self.logger = logging.getLogger(__name__)

    def post(self, request):
        """处理批量计算请求"""
        try:
            # 验证输入数据
            serializer = BatchCalculationRequestSerializer(data=request.data)
            if not serializer.is_valid():
                response_data, status_code = error_response(
                    message=serializer.errors,
                    code='VALIDATION_ERROR',
                    http_status=status.HTTP_400_BAD_REQUEST
                )
                return Response(response_data, status=status_code)

            # 创建批量计算任务
            task = BatchCalculationTask.objects.create(
                task_id=generate_request_id('BATCH'),
                status='PENDING',
                created_by=request.user,
                total_records=len(serializer.validated_data['items'])
            )

            # 启动异步任务
            process_batch_calculation.delay(task.task_id, serializer.validated_data['items'])

            response_data, status_code = success_response(
                data={'task_id': task.task_id},
                message='批量计算任务已创建'
            )
            return Response(response_data, status=status_code)

        except ValidationError as e:
            response_data, status_code = error_response(
                message=str(e),
                code='VALIDATION_ERROR',
                http_status=status.HTTP_400_BAD_REQUEST
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            self.logger.error(f"批量计算请求处理失败: {str(e)}", exc_info=True)
            response_data, status_code = error_response(
                message="处理请求时发生错误",
                code='SERVER_ERROR',
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)

    def get(self, request, task_id):
        """获取批量计算任务进度"""
        try:
            task = BatchCalculationTask.objects.get(task_id=task_id)
            response_data, status_code = success_response(
                data=BatchCalculationResultSerializer(task).data,
                message='获取进度成功'
            )
            return Response(response_data, status=status_code)

        except BatchCalculationTask.DoesNotExist:
            response_data, status_code = error_response(
                message='任务不存在',
                code='TASK_NOT_FOUND',
                http_status=status.HTTP_404_NOT_FOUND
            )
            return Response(response_data, status=status_code)
        except Exception as e:
            self.logger.error(f"获取任务进度失败: {str(e)}", exc_info=True)
            response_data, status_code = error_response(
                message='获取任务进度失败',
                code='PROGRESS_ERROR',
                http_status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            return Response(response_data, status=status_code)

@extend_schema(
    tags=['运费计算'],
    description='获取计算历史记录',
    responses={200: CalculationRequestModelSerializer(many=True)}
)
@api_view(['GET'])
def calculation_history(request):
    """获取计算历史记录"""
    user = request.user
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))
    
    # 获取用户的计算历史
    calculations = CalculationRequest.objects.filter(created_by=user).order_by('-created_at')
    
    # 简单分页
    start = (page - 1) * page_size
    end = start + page_size
    paginated_calculations = calculations[start:end]
    
    # 序列化结果
    serializer = CalculationRequestModelSerializer(paginated_calculations, many=True)
    
    # 构建响应
    response_data = {
        'total': calculations.count(),
        'page': page,
        'page_size': page_size,
        'results': serializer.data
    }
    
    return Response(response_data)

@extend_schema(
    tags=['运费计算'],
    description='获取计算详情',
    responses={200: CalculationDetailSerializer}
)
@api_view(['GET'])
def calculation_detail(request, request_id):
    """获取计算详情"""
    try:
        # 获取计算请求
        calculation = CalculationRequest.objects.get(request_id=request_id, created_by=request.user)
        
        # 获取计算明细
        details = CalculationDetail.objects.filter(calculation=calculation)
        
        # 序列化结果
        calculation_serializer = CalculationRequestModelSerializer(calculation)
        details_serializer = CalculationDetailSerializer(details, many=True)
        
        # 构建响应
        response_data = {
            'calculation': calculation_serializer.data,
            'details': details_serializer.data
        }
        
        return Response(response_data)
    except CalculationRequest.DoesNotExist:
        return Response(
            {'error': '计算记录不存在'},
            status=status.HTTP_404_NOT_FOUND
        )
