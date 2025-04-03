from rest_framework import permissions, viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import ZipZone, RemoteArea, ServiceProvider
from .serializers import ZipZoneSerializer, RemoteAreaSerializer
from .filters import ZipZoneFilter, RemoteAreaFilter
from django.db.models import Q
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from django.conf import settings
import pandas as pd
import os
from datetime import datetime
import logging
from django.http import JsonResponse
from rest_framework.permissions import AllowAny

logger = logging.getLogger(__name__)


class ZipZoneViewSet(viewsets.ModelViewSet):
    """
    邮编分区视图集
    """
    queryset = ZipZone.objects.all()
    serializer_class = ZipZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ZipZoneFilter
    search_fields = ['origin_zip', 'dest_zip_start', 'dest_zip_end']
    ordering_fields = ['zone_number', 'provider_id', 'origin_zip']
    
    def get_queryset(self):
        """自定义查询，支持按邮编范围过滤"""
        queryset = super().get_queryset()
        
        # 按目的邮编过滤
        dest_zip = self.request.query_params.get('dest_zip')
        if dest_zip:
            queryset = queryset.filter(
                dest_zip_start__lte=dest_zip,
                dest_zip_end__gte=dest_zip
            )
            
        return queryset


class RemoteAreaViewSet(viewsets.ModelViewSet):
    """
    偏远地区视图集
    """
    queryset = RemoteArea.objects.all()
    serializer_class = RemoteAreaSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = RemoteAreaFilter
    search_fields = ['origin_zip', 'zip_code']
    ordering_fields = ['remote_level', 'provider_id', 'origin_zip']


@api_view(['POST'])
def import_zip_zones(request):
    """
    导入邮编分区数据，支持服务商名称不区分大小写，邮编不限制位数
    """
    # 记录请求信息以便调试
    logger.info(f"接收到导入邮编分区请求 - 用户: {request.user} - 授权头: {request.META.get('HTTP_AUTHORIZATION', 'None')}")
    logger.info(f"请求方法: {request.method}")
    logger.info(f"请求体内容: {request.data}")
    logger.info(f"文件列表: {request.FILES}")
    
    if 'file' not in request.FILES:
        logger.warning("请求中没有找到'file'字段")
        return Response({'message': '请上传文件'}, status=400)
    
    file = request.FILES['file']
    file_ext = os.path.splitext(file.name)[1]
    logger.info(f"上传的文件名: {file.name}, 扩展名: {file_ext}")
    
    if file_ext not in ['.xlsx', '.xls', '.csv']:
        logger.warning(f"不支持的文件格式: {file_ext}")
        return Response({'message': '只支持Excel文件格式(xlsx, xls)或CSV格式'}, status=400)
    
    # 保存上传文件
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'postal')
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"zipzones_{timestamp}{file_ext}"
    filepath = os.path.join(upload_dir, filename)
    logger.info(f"保存文件到: {filepath}")
    
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    try:
        # 读取Excel文件
        if file_ext == '.csv':
            df = pd.read_csv(filepath)
        else:
            df = pd.read_excel(filepath)
        
        logger.info(f"成功读取文件，行数: {len(df)}, 列: {df.columns.tolist()}")
        
        # 检查必要的列是否存在
        required_columns = ['服务商', '始发地邮编', '目的地邮编起始', '目的地邮编终止', '分区号码']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            logger.warning(f"文件缺少必要的列: {missing_columns}")
            return Response({'message': f'文件缺少必要的列: {", ".join(missing_columns)}'}, status=400)
        
        # 获取所有服务商并创建名称和代码的映射（不区分大小写）
        providers = ServiceProvider.objects.all()
        provider_map = {}
        for provider in providers:
            provider_map[provider.name.lower()] = provider
            provider_map[provider.code.lower()] = provider
        
        logger.info(f"已加载服务商映射: {[p.name for p in providers]}")
        
        success_count = 0
        error_count = 0
        error_details = []
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                # 获取数据
                provider_name = str(row['服务商']).strip() if pd.notna(row['服务商']) else None
                origin_zip = str(row['始发地邮编']).strip() if pd.notna(row['始发地邮编']) else None
                dest_zip_start = str(row['目的地邮编起始']).strip() if pd.notna(row['目的地邮编起始']) else None
                dest_zip_end = str(row['目的地邮编终止']).strip() if pd.notna(row['目的地邮编终止']) else None
                zone_number = int(row['分区号码']) if pd.notna(row['分区号码']) else None
                
                # 验证必填字段
                if not provider_name or not origin_zip or not dest_zip_start or not dest_zip_end or zone_number is None:
                    error_count += 1
                    error_msg = f"第 {index+2} 行: 缺少必填字段"
                    error_details.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # 查找服务商（不区分大小写）
                provider_instance = None
                if provider_name.lower() in provider_map:
                    provider_instance = provider_map[provider_name.lower()]
                else:
                    # 尝试模糊匹配
                    for key, provider in provider_map.items():
                        if key in provider_name.lower() or provider_name.lower() in key:
                            provider_instance = provider
                            break
                
                if not provider_instance:
                    error_count += 1
                    error_msg = f"第 {index+2} 行: 找不到匹配的服务商 '{provider_name}'"
                    error_details.append(error_msg)
                    logger.warning(error_msg)
                    continue
                
                # 创建或更新邮编分区
                zip_zone, created = ZipZone.objects.update_or_create(
                    provider=provider_instance,
                    origin_zip=origin_zip,
                    dest_zip_start=dest_zip_start,
                    dest_zip_end=dest_zip_end,
                    defaults={
                        'zone_number': zone_number
                    }
                )
                
                success_count += 1
                logger.info(f"成功{'创建' if created else '更新'}第 {index+2} 行记录: {provider_instance.name}, {origin_zip}, {zone_number}")
                
            except Exception as e:
                error_count += 1
                error_msg = f"第 {index+2} 行: {str(e)}"
                error_details.append(error_msg)
                logger.error(f"导入邮编分区数据错误: {str(e)}", exc_info=True)
        
        # 返回导入结果
        result = {
            'message': f'导入完成: 成功 {success_count} 条, 失败 {error_count} 条',
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details
        }
        
        logger.info(f"导入完成: 成功 {success_count} 条, 失败 {error_count} 条")
        return Response(result)
        
    except Exception as e:
        error_msg = f"导入邮编分区文件处理错误: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return Response({'message': f'文件处理错误: {str(e)}'}, status=500)
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            os.remove(filepath)
            logger.info(f"清理临时文件: {filepath}")


@api_view(['POST'])
def import_remote_areas(request):
    """
    导入偏远地区数据，支持服务商名称不区分大小写，邮编不限制位数
    同时支持灵活的偏远等级描述文本
    """
    if 'file' not in request.FILES:
        return Response({'message': '请上传文件'}, status=400)
    
    file = request.FILES['file']
    file_ext = os.path.splitext(file.name)[1]
    
    if file_ext not in ['.xlsx', '.xls']:
        return Response({'message': '只支持Excel文件格式'}, status=400)
    
    # 保存上传文件
    upload_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'postal')
    os.makedirs(upload_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = f"remote_areas_{timestamp}{file_ext}"
    filepath = os.path.join(upload_dir, filename)
    
    with open(filepath, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)
    
    try:
        # 读取Excel文件
        df = pd.read_excel(filepath)
        
        # 检查必要的列是否存在
        required_columns = ['服务商', '始发地邮编', '偏远地区邮编', '偏远等级']
        for col in required_columns:
            if col not in df.columns:
                return Response({'message': f'文件缺少必要的列: {col}'}, status=400)
        
        # 获取所有服务商并创建名称和代码的映射（不区分大小写）
        providers = ServiceProvider.objects.all()
        provider_map = {}
        for provider in providers:
            provider_map[provider.name.lower()] = provider
            provider_map[provider.code.lower()] = provider
        
        success_count = 0
        error_count = 0
        error_details = []
        
        # 处理每一行数据
        for index, row in df.iterrows():
            try:
                # 获取数据
                provider_name = str(row['服务商']).strip() if pd.notna(row['服务商']) else None
                origin_zip = str(row['始发地邮编']).strip() if pd.notna(row['始发地邮编']) else None
                zip_code = str(row['偏远地区邮编']).strip() if pd.notna(row['偏远地区邮编']) else None
                remote_level = str(row['偏远等级']).strip() if pd.notna(row['偏远等级']) else None
                
                # 验证必填字段
                if not provider_name or not origin_zip or not zip_code or not remote_level:
                    error_count += 1
                    error_details.append(f"第 {index+2} 行: 缺少必填字段")
                    continue
                
                # 查找服务商（不区分大小写）
                provider_instance = None
                if provider_name.lower() in provider_map:
                    provider_instance = provider_map[provider_name.lower()]
                else:
                    # 尝试模糊匹配
                    for key, provider in provider_map.items():
                        if key in provider_name.lower() or provider_name.lower() in key:
                            provider_instance = provider
                            break
                
                if not provider_instance:
                    error_count += 1
                    error_details.append(f"第 {index+2} 行: 找不到匹配的服务商 '{provider_name}'")
                    continue
                
                # 验证偏远等级 - 保留原始输入，不做限制
                if not remote_level or remote_level.strip() == '':
                    remote_level = '一级偏远'  # 默认设为一级偏远
                
                # 记录日志，便于调试
                logger.info(f"导入偏远地区: 服务商={provider_instance.name}, 始发地={origin_zip}, 偏远地区={zip_code}, 偏远等级={remote_level}")
                
                # 创建或更新偏远地区
                remote_area, created = RemoteArea.objects.update_or_create(
                    provider=provider_instance,
                    origin_zip=origin_zip,
                    zip_code=zip_code,
                    defaults={
                        'remote_level': remote_level
                    }
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                error_details.append(f"第 {index+2} 行: {str(e)}")
                logger.error(f"导入偏远地区数据错误: {str(e)}")
        
        # 返回导入结果
        return Response({
            'message': f'导入完成: 成功 {success_count} 条, 失败 {error_count} 条',
            'success_count': success_count,
            'error_count': error_count,
            'error_details': error_details
        })
        
    except Exception as e:
        logger.error(f"导入偏远地区文件处理错误: {str(e)}")
        return Response({'message': f'文件处理错误: {str(e)}'}, status=500)
    finally:
        # 清理临时文件
        if os.path.exists(filepath):
            os.remove(filepath) 


@api_view(['GET'])
@authentication_classes([])  # 完全禁用认证
@permission_classes([AllowAny])
def direct_query_zip_zone(request):
    """独立的邮编分区查询API，直接路由到这个视图函数"""
    logger.info(f"直接查询邮编分区API - 路径: {request.path}, 方法: {request.method}")
    logger.info(f"请求参数: {request.GET}")
    
    provider_id = request.GET.get('provider_id')
    origin_zip = request.GET.get('origin_zip')
    dest_zip = request.GET.get('dest_zip')
    
    if not all([provider_id, origin_zip, dest_zip]):
        logger.warning(f"缺少必要参数: provider_id={provider_id}, origin_zip={origin_zip}, dest_zip={dest_zip}")
        return JsonResponse({
            'error': '缺少必要的查询参数',
            'required': ['provider_id', 'origin_zip', 'dest_zip']
        }, status=400)
    
    try:
        # 查找匹配的分区
        zone = ZipZone.objects.filter(
            provider_id=provider_id,
            origin_zip=origin_zip,
            dest_zip_start__lte=dest_zip,
            dest_zip_end__gte=dest_zip
        ).first()
        
        if zone:
            logger.info(f"找到匹配分区: {zone.id}, zone_number={zone.zone_number}")
            # 直接返回分区对象数据，不使用嵌套结构
            return JsonResponse({
                'provider_id': zone.provider_id,
                'origin_zip': zone.origin_zip,
                'dest_zip_start': zone.dest_zip_start,
                'dest_zip_end': zone.dest_zip_end,
                'zone_number': zone.zone_number
            })
        else:
            logger.info(f"未找到匹配分区, 查询条件: provider_id={provider_id}, origin_zip={origin_zip}, dest_zip={dest_zip}")
            # 返回空对象，但保持相同的字段
            return JsonResponse({
                'provider_id': int(provider_id),
                'origin_zip': origin_zip,
                'dest_zip': dest_zip,
                'zone_number': None
            })
    except Exception as e:
        logger.error(f"查询邮编分区失败: {str(e)}")
        return JsonResponse({
            'error': f'查询邮编分区失败: {str(e)}'
        }, status=500) 