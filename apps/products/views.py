import os
import random
import logging
import re
import time
import json
import uuid
import string
import traceback
import tempfile
import numpy as np
import pandas as pd
import io
from pandas.errors import ParserError, EmptyDataError

from datetime import datetime, timedelta, date
from decimal import Decimal
from dateutil import parser
from typing import Tuple, Dict, Any, List, Optional
from collections import Counter

from django.db import models, transaction
from django.db.models import Q, Count, Sum, Avg, Value, F, ExpressionWrapper, Prefetch
from django.db.models.functions import Lower
from django.utils import timezone
from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, JsonResponse, QueryDict
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache

from rest_framework import viewsets, permissions, status, serializers
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.filters import OrderingFilter
from django_filters import rest_framework as filters

from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter

from .models import Product, Surcharge, PeakSeasonSurcharge, BaseFee
from .serializers import (
    ProductSerializer, ProductDetailSerializer,
    SurchargeSerializer, PeakSeasonSurchargeSerializer,
    BaseFeeSerializer, ProductZoneRateImportSerializer,
    SurchargeImportSerializer, PeakSeasonSurchargeImportSerializer,
    BaseFeeImportSerializer
)
from .dto import BaseFeeInputDTO, BaseFeeOutputDTO
from .improve_import import ensure_product_data_integrity
from apps.core.models import ServiceProvider

logger = logging.getLogger(__name__)


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 1000


class ProductViewSet(viewsets.ModelViewSet):
    """
    产品视图集
    """
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    pagination_class = StandardResultsSetPagination
    
    # 添加获取产品类型列表的方法
    @action(detail=False, methods=['get'])
    def product_types(self, request):
        """获取所有产品列表，供前端下拉选择"""
        try:
            products = Product.objects.filter(status=True).order_by('product_name')
            result = []
            for product in products:
                result.append({
                    'product_id': product.product_id,
                    'product_name': product.product_name,
                    'provider_name': product.provider_name,
                    'currency': product.currency,
                    'status': product.status,
                    'dim_unit': product.dim_unit,
                    'weight_unit': product.weight_unit,
                    'dim_factor': product.dim_factor,
                    'dim_factor_unit': product.dim_factor_unit
                })
            return Response(result)
        except Exception as e:
            logger.error(f"获取产品类型失败: {str(e)}")
            return Response(
                {"error": f"获取产品类型失败: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _parse_date(self, date_str):
        """
        解析日期字符串为日期对象
        支持多种格式:
        - YYYY/MM/DD
        - YYYY-MM-DD
        - DD/MM/YYYY
        - MM/DD/YYYY
        - Excel数字日期格式
        - pandas Timestamp对象
        """
        if date_str is None or date_str == '' or pd.isna(date_str):
            return None
        
        # 如果已经是日期对象，直接返回
        if isinstance(date_str, (date, datetime)):
            return date_str.date() if isinstance(date_str, datetime) else date_str
            
        # 如果是pandas的Timestamp对象
        if hasattr(date_str, 'date') and callable(getattr(date_str, 'date')):
            try:
                return date_str.date()
            except:
                pass

        # 转换为字符串处理
        if not isinstance(date_str, str):
            date_str = str(date_str).strip()
        else:
            date_str = date_str.strip()
            
        # 尝试不同的日期格式
        date_formats = [
            '%Y/%m/%d', '%Y-%m-%d',   # 年/月/日
            '%d/%m/%Y', '%d-%m-%Y',   # 日/月/年
            '%m/%d/%Y', '%m-%d-%Y',   # 月/日/年
            '%Y年%m月%d日', '%Y年%m月%d号',  # 中文格式
            '%Y.%m.%d', '%d.%m.%Y', '%m.%d.%Y'  # 点分隔格式
        ]
        
        for date_format in date_formats:
            try:
                return datetime.strptime(date_str, date_format).date()
            except ValueError:
                continue
                
        # 尝试处理Excel数字日期格式
        try:
            # 检查是否为数字
            if date_str.replace('.', '', 1).isdigit():
                number = float(date_str)
                # Excel日期是从1900-01-01开始的天数
                # 需要减去Excel的日期偏移（通常为1，有时为2）
                excel_epoch = datetime(1899, 12, 30)
                delta_days = int(number)
                return (excel_epoch + timedelta(days=delta_days)).date()
        except:
            pass
            
        # 尝试使用dateutil解析
        try:
            from dateutil import parser
            return parser.parse(date_str).date()
        except:
            pass
            
        # 如果所有尝试都失败，返回None
        print(f"无法解析日期: {date_str}，类型: {type(date_str)}")
        return None
    
    def get_serializer_class(self):
        if self.action == 'retrieve' or self.action == 'detail':
            return ProductDetailSerializer
        return ProductSerializer
    
    def perform_create(self, serializer):
        serializer.save()
    
    def destroy(self, request, *args, **kwargs):
        """
        删除产品
        """
        try:
            logger.info(f"开始处理产品删除请求，ID: {kwargs.get('pk')}")
            logger.info(f"请求方法: {request.method}, 请求头: {request.headers}")
            
            # 获取产品对象
            instance = self.get_object()
            product_id = instance.product_id
            product_name = instance.product_name
            
            logger.info(f"找到产品: {product_name} (ID: {product_id})")
            
            # 检查是否有关联数据
            has_related_base_fees = BaseFee.objects.filter(
                product=instance).exists()
            has_related_surcharges = Surcharge.objects.filter(
                product=instance).exists()
            has_related_peak_surcharges = PeakSeasonSurcharge.objects.filter(
                product=instance).exists()

            logger.info(
                f"关联检查 - 基础费率: {has_related_base_fees}, 附加费: {has_related_surcharges}, 旺季费: {has_related_peak_surcharges}")
            
            # 创建数据库事务
            with transaction.atomic():
                # 先删除关联数据
                if has_related_base_fees:
                    base_fees = BaseFee.objects.filter(product=instance)
                    logger.info(f"删除关联基础费率数据: {base_fees.count()} 条")
                    base_fees.delete()
                
                if has_related_surcharges:
                    surcharges = Surcharge.objects.filter(product=instance)
                    logger.info(f"删除关联附加费数据: {surcharges.count()} 条")
                    surcharges.delete()
                
                if has_related_peak_surcharges:
                    peak_surcharges = PeakSeasonSurcharge.objects.filter(
                        product=instance)
                    logger.info(f"删除关联旺季附加费数据: {peak_surcharges.count()} 条")
                    peak_surcharges.delete()
                
                # 最后删除产品本身
                response = super().destroy(request, *args, **kwargs)
                logger.info(f"成功删除产品: {product_name} (ID: {product_id})")
                return response
        
        except Exception as e:
            logger.error(f"删除产品时出错: {str(e)}")
            return Response({'error': f'删除产品时出错: {str(e)}'},
     status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """获取当前有效的产品"""
        today = timezone.now().date()
        products = Product.objects.filter(
            effective_date__lte=today,
            expiration_date__gte=today,
            status=True
        )
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def public_product_list(self, request):
        """
        公开的产品列表接口，用于测试，无需身份认证
        """
        try:
            # 获取所有产品
            queryset = Product.objects.all().order_by('-created_at')
            
            # 输出调试信息
            print(f"产品总数: {queryset.count()}")
            print(f"产品IDs: {list(queryset.values_list('id', flat=True))}")
            
            # 序列化数据
            serializer = ProductSerializer(queryset, many=True)
            data = serializer.data
            
            # 构建响应
            response_data = {
                'count': len(data),
                'results': data,
                'status': 'success',
                'message': '获取产品列表成功'
            }
            
            return Response(response_data)
        except Exception as e:
            print(f"获取公开产品列表出错: {str(e)}")
            import traceback
            print(traceback.format_exc())
            return Response({
                'status': 'error',
                'message': f'获取产品列表出错: {str(e)}',
                'count': 0,
                'results': []
            })
    
    def list(self, request, *args, **kwargs):
        """
        获取产品列表
        """
        try:
            logger.info("自定义list方法被调用 - 开始处理产品列表请求")
            logger.info(f"查询参数: {request.query_params}")
            
            # 获取查询参数
            search = request.query_params.get('search', '')
            provider = request.query_params.get('provider', '')
            show_all = request.query_params.get(
                'show_all', 'true').lower() == 'true'  # 默认显示所有产品
            
            logger.debug(
                f"查询参数: search={search}, provider={provider}, show_all={show_all}")
            
            # 构建查询集
            queryset = self.get_queryset()
            logger.debug(f"初始查询集记录数: {queryset.count()}")
            
            # 应用搜索过滤
            if search:
                queryset = queryset.filter(
                    Q(name__icontains=search) |
                    Q(code__icontains=search) |
                    Q(provider__name__icontains=search)
                )
            
            # 应用服务商过滤
            if provider:
                queryset = queryset.filter(provider__name__iexact=provider)
            
            # 无论如何显示所有产品，不进行日期过滤，确保所有产品都能显示
            # 仅当明确请求不显示所有产品时才应用日期过滤
            if not show_all:
                current_date = timezone.now().date()
                queryset = queryset.filter(
                    Q(effective_date__lte=current_date) &
                    (Q(expiration_date__gte=current_date)
                     | Q(expiration_date__isnull=True))
                )
            
            logger.debug(f"过滤后查询集记录数: {queryset.count()}")
            logger.debug(
                f"过滤后查询集IDs: {list(queryset.values_list('product_id', flat=True))}")
            
            # 应用分页
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                data = serializer.data
                response_data = {
                    'count': self.paginator.page.paginator.count,
                    'next': self.paginator.get_next_link() if page else None,
                    'previous': self.paginator.get_previous_link() if page else None,
                    'results': data
                }
                logger.info(
                    f"返回分页数据，总数: {response_data['count']}, 当前页数据量: {len(data)}")
                logger.debug(f"序列化后的数据: {data}")
                return Response(response_data)
            
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
            response_data = {
                'count': len(data),
                'next': None,
                'previous': None,
                'results': data
            }
            logger.info(f"返回所有数据，总数: {len(data)}")
            logger.debug(f"序列化后的数据: {data}")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"获取产品列表出错: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            })
    
    @action(detail=False, methods=['POST'], url_path='upload_product_excel')
    def upload_product_excel(self, request):
        """上传产品Excel文件"""
        try:
            # 检查是否存在文件上传
            if 'file' not in request.FILES:
                return Response({"error": "未找到上传的文件"},
                                status=status.HTTP_400_BAD_REQUEST)

            # 获取上传的文件
            uploaded_file = request.FILES['file']

            # 创建临时文件存储Excel
            with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
                for chunk in uploaded_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            # 记录Excel处理开始
            file_name = uploaded_file.name
            print(
                f"\n==================== 开始处理Excel文件: {file_name} ====================")

            # 使用pandas读取Excel文件
            df_info = None
            try:
                # 尝试使用openpyxl引擎
                print("尝试使用引擎 openpyxl 读取Excel")
                df_info = pd.read_excel(
                    temp_file_path, sheet_name=None, engine='openpyxl')
                print("使用 openpyxl 引擎成功读取Excel")
            except Exception as e:
                print(f"openpyxl引擎读取失败: {str(e)}")
                try:
                    # 尝试使用xlrd引擎
                    print("尝试使用引擎 xlrd 读取Excel")
                    df_info = pd.read_excel(
                        temp_file_path, sheet_name=None, engine='xlrd')
                    print("使用 xlrd 引擎成功读取Excel")
                except Exception as e:
                    print(f"xlrd引擎读取失败: {str(e)}")
                    return Response(
                        {"error": f"无法读取Excel文件: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

            # 删除临时文件
            os.unlink(temp_file_path)

            # 检查Excel中的sheet
            sheet_names = list(df_info.keys())
            print(f"\nExcel文件 {file_name} 包含的sheet页: {sheet_names}")

            # 映射表单名称
            sheet_mapping = {
                '基本信息': '基本信息表',
                '基础费用': '基础费用表',
                '基础费用表': '基础费用表',
                '附加费': '附加费表',
                '附加费表': '附加费表',
                '旺季附加费': '旺季附加费表',
                '旺季附加费表': '旺季附加费表'
            }

            # 查找每个需要的sheet
            processed_sheets = {}
            for sheet_name in sheet_names:
                for key, value in sheet_mapping.items():
                    if sheet_name == key:
                        processed_sheets[value] = sheet_name
                        print(f"找到{value}: {sheet_name}")
                        break

            # 处理每个sheet
            processors = {
                '基本信息表': self._process_product_info,
                '基础费用表': self._process_base_rates,
                '附加费表': self._process_surcharges,
                '旺季附加费表': self._process_peak_season
            }

            results = {}

            # 创建一个单独的事务
            with transaction.atomic():
                # 首先处理基本信息
                if '基本信息表' in processed_sheets:
                    product_sheet_name = processed_sheets['基本信息表']
                    product_info_df = df_info[product_sheet_name]
                    results['基本信息'] = []

                    print(f"\n==================== 处理基本信息表 ====================")
                    product_result = self._process_product_info(product_info_df)
                    results['基本信息'] = product_result

                    if product_result and product_result.get('success') > 0:
                        # 获取已创建的产品
                        product_id = product_result.get('product_id')
                        product = Product.objects.get(product_id=product_id)
                        
                        # 如果成功创建了产品，继续处理其他sheet
                        if '基础费用表' in processed_sheets and product:
                            base_fees_sheet_name = processed_sheets['基础费用表']
                            base_fees_df = df_info[base_fees_sheet_name]
                            results['基础费用'] = self._process_base_rates(
                                base_fees_df, product)

                        if '附加费表' in processed_sheets and product:
                            surcharges_sheet_name = processed_sheets['附加费表']
                            surcharges_df = df_info[surcharges_sheet_name]
                            results['附加费'] = self._process_surcharges(
                                surcharges_df, product)

                        if '旺季附加费表' in processed_sheets and product:
                            peak_season_sheet_name = processed_sheets['旺季附加费表']
                            peak_season_df = df_info[peak_season_sheet_name]
                            results['旺季附加费'] = self._process_peak_season(
                                peak_season_df, product)
                    else:
                        error_msg = product_result.get('error') if product_result else "处理产品基本信息失败"
                        return Response({"error": error_msg},
                                        status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response({"error": "Excel文件中缺少基本信息表"},
                                    status=status.HTTP_400_BAD_REQUEST)

            return Response({
                "message": "Excel导入成功",
                "results": results,
                "detail": {
                    "基本信息": results.get('基本信息', {}),
                    "基础费用": results.get('基础费用', {}),
                    "附加费": results.get('附加费', {}),
                    "旺季附加费": results.get('旺季附加费', {})
                },
                "状态": "成功",
                "导入时间": timezone.now().strftime("%Y-%m-%d %H:%M:%S")
            })
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": f"处理Excel文件时出错: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _process_base_rates(self, df, product):
        """处理基础费用表数据"""
        try:
            print("\n==================== 处理基础费用表 ====================")
            
            # 清除现有的基础费用
            BaseFee.objects.filter(product=product).delete()
            
            # 清理列名（去除空格和换行符）
            df.columns = [str(col).strip().replace('\n', '') for col in df.columns]

            # 显示数据预览和完整内容
            print("\n数据预览:")
            print(df.head())
            
            print("\nDataFrame完整结构:")
            pd.set_option('display.max_columns', None)  # 显示所有列
            pd.set_option('display.max_rows', None)     # 显示所有行
            pd.set_option('display.width', 1000)        # 设置显示宽度
            print(df.to_string())
            
            # 保存基础费用数据到数据库，直接读取DataFrame的值
            success_count = 0
            errors = []
            
            # 直接将DataFrame转为字典列表并保存
            records = df.to_dict('records')
            for index, record in enumerate(records):
                try:
                    # 提取必要的字段
                    weight = None
                    for col_name in ['重量', '重量(LB)', '重量(KG)', 'weight']:
                        if col_name in record and record[col_name] is not None:
                            weight = record[col_name]
                            break
                    
                    if weight is None:
                        errors.append(f"行 {index + 1}: 缺少重量值")
                        continue
                    
                    try:
                        weight = float(weight)
                    except (ValueError, TypeError):
                        error_msg = f"行 {index + 1}: 重量值无效: {weight}"
                        errors.append(error_msg)
                        continue
                    
                    # 解析费用类型和重量单位
                    fee_type = None
                    for col_name in ['计价类型', '费用类型', 'fee_type']:
                        if col_name in record and record[col_name] is not None:
                            fee_type = str(record[col_name]).upper().strip()
                            break
                    
                    if fee_type in ['STEP', 'STEPWISE', '阶梯']:
                        fee_type = 'STEP'
                    elif fee_type in ['LINEAR', 'PROPORTIONAL', '线性']:
                        fee_type = 'LINEAR'
                    else:
                        fee_type = 'STEP'  # 默认使用阶梯计费
                    
                    weight_unit = None
                    for col_name in ['单位', '重量单位', 'weight_unit']:
                        if col_name in record and record[col_name] is not None:
                            weight_unit = str(record[col_name]).upper().strip()
                            break
                    
                    if weight_unit not in ['LB', 'KG', 'OZ']:
                        weight_unit = 'LB'  # 默认使用磅
                    
                    # 创建基础费用记录并直接使用原始数据
                    base_fee = BaseFee(
                        product=product,
                        weight=weight,
                        weight_unit=weight_unit,
                        fee_type=fee_type,
                        raw_data=record  # 保存原始记录
                    )
                    
                    # 保存区域相关数据 - 使用智能检测识别区域列
                    zone_prices = {}
                    zone_unit_prices = {}
                    
                    # 简单处理：根据列名判断区域和类型
                    for col, value in record.items():
                        col_lower = str(col).lower()
                        
                        # 忽略空值
                        if pd.isna(value) or value is None:
                            continue
                            
                        # 尝试从列名中提取区域编号
                        zone_match = None
                        for pattern in [r'(?:zone|区域|分区|z)[_\s]*(\d+)', r'^(\d+)[-_\s]', r'(\d+)区']:
                            match = re.search(pattern, col_lower)
                            if match:
                                zone_match = match.group(1)
                                break
                        
                        if zone_match:
                            zone_num = zone_match
                            zone_key = f'zone{zone_num}'
                            
                            # 尝试判断是否是单价列
                            is_unit_price = any(keyword in col_lower for keyword in ['单价', 'unit', 'price', '每重量', '每公斤', '每磅'])
                            
                            # 转换数值
                            try:
                                if isinstance(value, str):
                                    value = value.replace('$', '').replace(',', '').strip()
                                price_value = float(value) if value else 0
                            except (ValueError, TypeError):
                                price_value = 0
                                print(f"警告: 无法转换值 '{value}' 到数字")
                            
                            # 根据列类型保存到不同字典
                            if is_unit_price:
                                zone_unit_prices[zone_key] = price_value
                                print(f"区域{zone_num}单价: {price_value} (从列 '{col}')")
                            else:
                                zone_prices[zone_key] = price_value
                                print(f"区域{zone_num}价格: {price_value} (从列 '{col}')")
                    
                    # 保存处理过的区域数据
                    base_fee.zone_prices = zone_prices
                    base_fee.zone_unit_prices = zone_unit_prices
                    base_fee.save()
                    
                    print(f"行 {index + 1}: 成功保存基础费用数据")
                    success_count += 1
                    
                except Exception as e:
                    error_msg = f"行 {index + 1}: 处理出错 - {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)
            
            print(f"基础费用表处理完成: 成功 {success_count} 行")
            if errors:
                print(f"错误: {len(errors)} 条")
                for error in errors[:5]:  # 仅显示前5条错误
                    print(f"- {error}")
                if len(errors) > 5:
                    print(f"... 还有 {len(errors) - 5} 条错误未显示")
            
            # 返回的数据结构保留了原始DataFrame
            return {
                "success": success_count,
                "errors": errors,
                "total": len(df),
                "raw_dataframe": df.to_dict('records'),  # 保留原始数据
                "data_summary": f"成功导入 {success_count}/{len(df)} 行基础费用数据"
            }
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"处理基础费用表出错: {str(e)}")
            return {"success": 0, "error": str(e)}

    def _process_surcharges(self, df, product):
        """处理附加费表数据"""
        try:
            print("\n==================== 处理附加费表 ====================")

            # 清理列名（去除空格和换行符）
            df.columns = [str(col).strip().replace('\n', '') for col in df.columns]

            # 显示数据预览
            print("\n数据预览:")
            print(df.head())
            
            # 添加原始DataFrame内容的完整显示
            print("\n原始DataFrame完整内容:")
            pd.set_option('display.max_columns', None)  # 显示所有列
            pd.set_option('display.max_rows', None)     # 显示所有行
            pd.set_option('display.width', 1000)        # 设置显示宽度
            print(df.to_string())
            
            # 恢复显示设置
            pd.reset_option('display.max_columns')
            pd.reset_option('display.max_rows')
            pd.reset_option('display.width')
            
            # 数据处理跟踪
            print("\n数据处理跟踪:")
            conversion_details = {}
            for col in df.columns:
                if 'Zone' in col or '区域' in col:
                    sample_values = df[col].head(3).tolist()
                    conversion_details[col] = {
                        'sample_values': sample_values,
                        'sample_types': [type(v).__name__ for v in sample_values],
                        'contains_na': df[col].isna().any(),
                        'unique_values': df[col].nunique(),
                    }
            print(f"区域列转换详情: {conversion_details}")

            # 显示数据类型
            print("\n数据类型:")
            print(df.dtypes)

            # 打印总行数
            print(f"\n共 {len(df)} 行数据")

            # 基本列名映射
            column_mapping = {
                '附加费类型': 'surcharge_type',
                '类型': 'surcharge_type',
                '子类型': 'sub_type',
                '条件描述': 'condition_desc',
                '条件': 'condition_desc',
                '描述': 'condition_desc',
            }
            
            # 检查必要列是否存在
            required_fields = ['surcharge_type']
            missing_fields = []

            # 检查数据框中的列名
            excel_columns = set(df.columns)
            print(f"Excel文件中的列名: {excel_columns}")

            # 查找分区列名
            # 可能的模式有：Zone1, Zone2, 区域1, 分区1等
            zone_column_patterns = [
                r'Zone(\d+)',
                r'区域(\d+)',
                r'分区(\d+)',
                r'ZONE(\d+)',
                r'zone(\d+)',
                r'(\d+)区',
                r'(\d+)区域',
                r'(\d+)分区'
            ]

            # 存储找到的区域列名
            zone_fee_columns = {}  # 格式: {zone编号: 列名}

            # 查找所有匹配分区模式的列名
            for col in excel_columns:
                for pattern in zone_column_patterns:
                    match = re.search(pattern, col, re.IGNORECASE)  # 使用re.search而不是re.match，并忽略大小写
                    if match:
                        zone_num = match.group(1)
                        zone_fee_columns[zone_num] = col
                        print(f"找到区域{zone_num}附加费列: {col}")
                        break

            print(f"找到的附加费列: {zone_fee_columns}")

            # 检查必要字段
            for field in required_fields:
                field_found = False
                for excel_col in excel_columns:
                    if excel_col in column_mapping and column_mapping[excel_col] == field:
                        field_found = True
                        break

                if not field_found:
                    missing_fields.append(field)

            if missing_fields:
                error_msg = f"附加费表缺少必要字段: {', '.join(missing_fields)}"
                print(error_msg)
                return {"success": 0, "error": error_msg}

            # 处理每一行数据
            success_count = 0
            errors = []

            # 首先删除该产品的所有现有附加费
            Surcharge.objects.filter(product=product).delete()

            for index, row in df.iterrows():
                try:
                    print(f"\n处理第 {index + 1} 行数据")

                    # 获取字段值的辅助函数
                    def get_field_value(field_key, default_value=None):
                        """
                        从Excel行中获取字段值
                        """
                        for col_name in df.columns:
                            if col_name in column_mapping and column_mapping[col_name] == field_key:
                                value = row[col_name]
                                print(
                                    f"找到字段 {field_key} 对应列名 {col_name}，值: {value}")
                                return value
                        return default_value

                    # 提取基本字段
                    surcharge_type = get_field_value('surcharge_type')
                    if surcharge_type is None or pd.isna(surcharge_type):
                        print(f"行 {index + 1}: 跳过 - 附加费类型字段为空")
                        continue

                    surcharge_type = str(surcharge_type).strip()
                    sub_type = get_field_value('sub_type', '')
                    if sub_type is not None and not pd.isna(sub_type):
                        sub_type = str(sub_type).strip()
                    else:
                        sub_type = ''

                    condition_desc = get_field_value('condition_desc', '')
                    if condition_desc is not None and not pd.isna(condition_desc):
                        condition_desc = str(condition_desc).strip()
                    else:
                        condition_desc = ''

                    # 提取各区域费用，并将它们放入zone_fees字段中
                    zone_fees = {}

                    # 处理所有找到的区域列
                    for zone_num, col_name in zone_fee_columns.items():
                        value = row[col_name]
                        if value is not None and not pd.isna(value):
                            try:
                                fee = float(value)
                                zone_fees[f'zone{zone_num}'] = fee
                                print(f"区域 {zone_num} 附加费: {fee}")
                            except (ValueError, TypeError):
                                print(f"无法转换区域 {zone_num} 附加费值: {value}")
                                zone_fees[f'zone{zone_num}'] = 0
                        else:
                            zone_fees[f'zone{zone_num}'] = 0

                    # 创建附加费记录
                    surcharge = Surcharge(
                        product=product,
                        surcharge_type=surcharge_type,
                        sub_type=sub_type,
                        condition_desc=condition_desc,
                        display_order=index + 1,  # 使用Excel中的顺序
                        zone_fees=zone_fees
                    )
                    surcharge.save()

                    print(
                        f"行 {index + 1}: 创建附加费 - 类型: {surcharge_type}, 子类型: {sub_type}")
                    success_count += 1
                except Exception as e:
                    error_msg = f"行 {index + 1}: 处理出错 - {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)

            print(f"附加费表处理完成: 成功 {success_count} 行")
            if errors:
                print(f"错误: {len(errors)} 条")
                for error in errors[:5]:  # 仅显示前5条错误
                    print(f"- {error}")
                if len(errors) > 5:
                    print(f"... 还有 {len(errors) - 5} 条错误未显示")

            return {
                "success": success_count,
                "errors": errors,
                "total": len(df)
            }

        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"处理附加费表出错: {str(e)}")
            return {"success": 0, "error": str(e)}

    def _process_peak_season(self, df, product):
        """处理旺季附加费表数据"""
        try:
            print("\n==================== 处理旺季附加费表 ====================")

            # 清理列名（去除空格和换行符）
            df.columns = [str(col).strip().replace('\n', '') for col in df.columns]

            # 显示数据预览
            print("\n数据预览:")
            print(df.head())
            
            # 添加原始DataFrame内容的完整显示
            print("\n原始DataFrame完整内容:")
            pd.set_option('display.max_columns', None)  # 显示所有列
            pd.set_option('display.max_rows', None)     # 显示所有行
            pd.set_option('display.width', 1000)        # 设置显示宽度
            print(df.to_string())
            
            # 恢复显示设置
            pd.reset_option('display.max_columns')
            pd.reset_option('display.max_rows')
            pd.reset_option('display.width')
            
            # 数据转换前后对比
            print("\n数据转换前后对比:")
            date_columns = [col for col in df.columns if '日期' in col or 'date' in col.lower()]
            if date_columns:
                print("日期列转换示例:")
                for col in date_columns:
                    original_values = df[col].head(3).tolist()
                    converted_values = []
                    for val in original_values:
                        try:
                            converted_values.append(self._parse_date(str(val)))
                        except:
                            converted_values.append("转换失败")
                    print(f"  {col}: 原始值 {original_values} -> 转换值 {converted_values}")

            # 显示数据类型
            print("\n数据类型:")
            print(df.dtypes)

            # 打印总行数
            print(f"\n共 {len(df)} 行数据")

            # 基本列名映射
            column_mapping = {
                '附加费类型': 'surcharge_type',
                '类型': 'surcharge_type',
                '开始日期': 'start_date',
                '生效日期': 'start_date',
                '结束日期': 'end_date',
                '失效日期': 'end_date',
                '费用金额': 'fee_amount',
                '金额': 'fee_amount',
                '费用': 'fee_amount',
            }

            # 检查数据框中的列名
            excel_columns = set(df.columns)
            print(f"Excel文件中的列名: {excel_columns}")

            # 检查必要列是否存在
            required_fields = ['surcharge_type', 'start_date', 'end_date', 'fee_amount']
            missing_fields = []

            # 检查数据框中的列名
            excel_columns = set(df.columns)
            print(f"Excel文件中的列名: {excel_columns}")

            # 检查必要字段
            for field in required_fields:
                field_found = False
                for excel_col in excel_columns:
                    if excel_col in column_mapping and column_mapping[excel_col] == field:
                        field_found = True
                        break

                if not field_found:
                    missing_fields.append(field)

            if missing_fields:
                error_msg = f"旺季附加费表缺少必要字段: {', '.join(missing_fields)}"
                print(error_msg)
                return {"success": 0, "error": error_msg}

            # 处理每一行数据
            success_count = 0
            errors = []

            # 首先删除该产品的所有现有旺季附加费
            PeakSeasonSurcharge.objects.filter(product=product).delete()

            for index, row in df.iterrows():
                try:
                    print(f"\n处理第 {index + 1} 行数据")

                    # 获取字段值的辅助函数
                    def get_field_value(field_key, default_value=None):
                        """
                        从Excel行中获取字段值
                        """
                        for col_name in df.columns:
                            if col_name in column_mapping and column_mapping[col_name] == field_key:
                                value = row[col_name]
                                print(
                                    f"找到字段 {field_key} 对应列名 {col_name}，值: {value}")
                                return value
                        return default_value

                    # 提取基本字段
                    surcharge_type = get_field_value('surcharge_type')
                    if surcharge_type is None or pd.isna(surcharge_type):
                        print(f"行 {index + 1}: 跳过 - 附加费类型字段为空")
                        continue

                    surcharge_type = str(surcharge_type).strip()

                    # 处理日期字段
                    start_date = get_field_value('start_date')
                    if start_date is None or pd.isna(start_date):
                        error_msg = f"行 {index + 1}: 开始日期为空"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    end_date = get_field_value('end_date')
                    if end_date is None or pd.isna(end_date):
                        error_msg = f"行 {index + 1}: 结束日期为空"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    # 将日期转换为日期对象
                    try:
                        start_date = self._parse_date(start_date)
                        end_date = self._parse_date(end_date)
                    except Exception as e:
                        error_msg = f"行 {index + 1}: 日期格式错误 - {str(e)}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    # 检查日期有效性
                    if start_date and end_date and start_date > end_date:
                        error_msg = f"行 {index + 1}: 开始日期不能晚于结束日期"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    # 提取费用金额
                    fee_amount = get_field_value('fee_amount')
                    if fee_amount is None or pd.isna(fee_amount):
                        error_msg = f"行 {index + 1}: 费用金额为空"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    try:
                        fee_amount = float(fee_amount)
                    except (ValueError, TypeError):
                        error_msg = f"行 {index + 1}: 费用金额格式错误: {fee_amount}"
                        print(error_msg)
                        errors.append(error_msg)
                        continue

                    # 创建旺季附加费记录
                    peak_surcharge = PeakSeasonSurcharge(
                        product=product,
                        surcharge_type=surcharge_type,
                        start_date=start_date,
                        end_date=end_date,
                        fee_amount=fee_amount
                    )
                    peak_surcharge.save()

                    print(
                        f"行 {index + 1}: 创建旺季附加费 - 类型: {surcharge_type}, 日期: {start_date} 到 {end_date}, 金额: {fee_amount}")
                    success_count += 1
                except Exception as e:
                    error_msg = f"行 {index + 1}: 处理出错 - {str(e)}"
                    print(error_msg)
                    errors.append(error_msg)

            print(f"旺季附加费表处理完成: 成功 {success_count} 行")
            if errors:
                print(f"错误: {len(errors)} 条")
                for error in errors[:5]:  # 仅显示前5条错误
                    print(f"- {error}")
                if len(errors) > 5:
                    print(f"... 还有 {len(errors) - 5} 条错误未显示")
            
            return {
                "success": success_count,
                "errors": errors,
                "total": len(df)
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"处理旺季附加费表出错: {str(e)}")
            return {"success": 0, "error": str(e)}
    
    def _process_product_info(self, df):
        """处理产品基本信息"""
        try:
            # 清理列名（去除空格和换行符）
            df.columns = [str(col).strip().replace('\n', '') for col in df.columns]
            
            # 显示数据预览
            print("\n原始列名:", list(df.columns))
            
            # 清理后的列名
            print("\n清理后的列名:", list(df.columns))
            print("\n数据预览:")
            print(df.head())
            
            # 显示数据类型
            print("\n数据类型:")
            print(df.dtypes)
            
            # 打印总行数
            print(f"\n共 {len(df)} 行数据")
            
            # 字段映射
            field_mappings = {
                'product_name': ['产品名称', '名称', 'Name', 'ProductName', 'product_name'],
                'provider_name': ['服务商', 'Provider', 'provider_name', 'ProviderName'],
                'effective_date': ['生效日期', '有效期开始', 'StartDate', 'EffectiveDate'],
                'expiration_date': ['失效日期', '有效期结束', 'EndDate', 'ExpirationDate'],
                'dim_factor': ['体积重系数', '体积重', 'DimFactor', 'DIM'],
                'dim_factor_unit': ['体积重系数单位', '体积重单位', 'DimUnit', 'WeightUnit'],
                'country': ['国家', 'Country', 'Nation'],
                'currency': ['币种', '货币', 'Currency', 'CurrencyCode'],
                'description': ['描述', 'Description', 'Desc', 'Remark'],
                'status': ['状态', 'Status', 'Active'],
                'enabled_start_date': ['启用开始日期', '启用日期', 'EnabledStartDate', 'EnabledFrom'],
                'enabled_end_date': ['启用结束日期', '禁用日期', 'EnabledEndDate', 'EnabledTo']
            }
            
            # 如果DataFrame为空，提前返回
            if df.empty:
                print("基本信息表为空")
                return None
            
            # 处理第一行数据
            row = df.iloc[0]
            print(f"\n处理第 1 行数据")
            
            # 获取所有列名
            columns = set(df.columns)
            print(f"Excel文件中的列名: {columns}")
            
            # 获取字段值的辅助函数
            def get_field_value(field_key, default_value=''):
                """从Excel行中获取字段值"""
                for possible_name in field_mappings[field_key]:
                    if possible_name in columns:
                        value = row[possible_name]
                        print(f"找到字段 {field_key} 对应列名 {possible_name}，值: {value}")
                        return value
                return default_value
            
            # 构建基本数据字典
            data_dict = {
                'product_name': get_field_value('product_name'),
                'provider_name': get_field_value('provider_name'),
                'effective_date': get_field_value('effective_date'),
                'expiration_date': get_field_value('expiration_date'),
                'dim_factor': get_field_value('dim_factor', '200'),
                'dim_factor_unit': get_field_value('dim_factor_unit', 'lb/in³'),
                'country': get_field_value('country', '美国'),
                'currency': get_field_value('currency', 'USD'),
                'description': get_field_value('description', ''),
                'status': get_field_value('status', '启用'),
                'enabled_start_date': get_field_value('enabled_start_date'),
                'enabled_end_date': get_field_value('enabled_end_date'),
                'weight_unit': 'lb',  # 默认重量单位
                'dim_unit': 'in'      # 默认尺寸单位
            }
            
            # 验证和清理数据
            cleaned_data = self._validate_and_clean_product_data(data_dict)
            
            # 验证必填字段
            product_name = cleaned_data.get('product_name')
            provider_name = cleaned_data.get('provider_name')
            
            print(f"处理产品: {product_name} ({provider_name})")
            
            if not product_name or not provider_name:
                logger.error("缺少必要的产品信息：产品名称或服务商")
                return {
                    "success": 0, 
                    "errors": ["缺少必要的产品信息：产品名称或服务商"], 
                    "total": 1,
                    "error": "缺少必要的产品信息：产品名称或服务商"
                }
            
            # 检查产品是否已存在
            existing_product = Product.objects.filter(
                product_name=product_name,
                provider_name=provider_name
            ).first()
            
            # 生成产品ID的函数
            def generate_product_id():
                """生成一个唯一的产品ID"""
                # 取服务商和产品名称的首字母
                prefix = ''.join([p[0].upper() for p in provider_name.split() if p])[:2]
                if not prefix:
                    prefix = 'P'
                
                # 添加时间戳和随机字符
                timestamp = str(int(time.time()))[-6:]
                random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
                
                product_id = f"{prefix}{timestamp}{random_chars}"
                # 确保长度不超过12
                if len(product_id) > 12:
                    product_id = product_id[:12]
                
                return product_id
            
            if existing_product:
                # 产品已存在，更新现有产品
                product = existing_product
                for field, value in cleaned_data.items():
                    if field != 'product_name' and field != 'provider_name':  # 不更新主键字段
                        setattr(product, field, value)
                
                product.save()
                created = False
                logger.info(f"更新产品: {product_name} ({provider_name}), ID: {product.product_id}")
            else:
                # 创建新产品
                product_id = generate_product_id()
                
                # 确保product_id唯一
                while Product.objects.filter(product_id=product_id).exists():
                    product_id = generate_product_id()
                
                # 创建产品对象
                cleaned_data['product_id'] = product_id
                product = Product.objects.create(**cleaned_data)
                created = True
                logger.info(f"创建产品: {product_name} ({provider_name}), ID: {product.product_id}")
            
            print(f"行 1: {'创建' if created else '更新'} 产品 {product.product_name}-{product.provider_name}")
            return {
                "success": 1,
                "errors": [],
                "total": 1,
                "product_id": product.product_id,
                "product_name": product.product_name,
                "provider_name": product.provider_name,
                "action": "created" if created else "updated"
            }
        except Exception as e:
            print(f"处理产品基本信息失败: {str(e)}")
            traceback.print_exc()
            return {
                "success": 0, 
                "errors": [str(e)], 
                "total": 1,
                "error": str(e)
            }
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def download_product_template(self, request):
        """
        下载产品Excel模板
        """
        try:
            # 创建一个Excel文件
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # 创建产品信息表
                products_df = pd.DataFrame(columns=[
                    '产品名称', '服务商', '体积重系数', '体积重系数单位', 
                    '生效日期', '失效日期', '国家', '币种', 
                    '描述', '状态', '启用开始日期', '启用结束日期'
                ])
                # 只添加表头，不添加示例数据
                products_df.to_excel(writer, sheet_name='基本信息', index=False)
                
                # 创建基础费用表（包含计价类型和单位重量价格）
                base_rates_df = pd.DataFrame(columns=[
                    '重量', '单位', '计价类型',
                    'Zone1基础价格', 'Zone2基础价格', 'Zone3基础价格', 'Zone4基础价格', 'Zone5基础价格', 
                    'Zone6基础价格', 'Zone7基础价格', 'Zone8基础价格', 'Zone17基础价格',
                    'Zone1单位重量价格', 'Zone2单位重量价格', 'Zone3单位重量价格', 'Zone4单位重量价格', 'Zone5单位重量价格', 
                    'Zone6单位重量价格', 'Zone7单位重量价格', 'Zone8单位重量价格', 'Zone17单位重量价格'
                ])
                # 只添加表头，不添加示例数据
                base_rates_df.to_excel(writer, sheet_name='基础费用表', index=False)
                
                # 创建附加费表
                surcharges_df = pd.DataFrame(columns=[
                    '附加费类型', '子类型', '条件描述', 'Zone1', 'Zone2', 'Zone3', 'Zone4', 'Zone5', 'Zone6', 'Zone7', 'Zone8', 'Zone17'
                ])
                # 只添加表头，不添加示例数据
                surcharges_df.to_excel(writer, sheet_name='附加费表', index=False)
                
                # 创建旺季附加费表
                pss_df = pd.DataFrame(columns=[
                    '附加费类型', '开始日期', '结束日期', '费用金额'
                ])
                # 只添加表头，不添加示例数据
                pss_df.to_excel(writer, sheet_name='旺季附加费表', index=False)
                
            # 设置response
            output.seek(0)
            response = HttpResponse(
                output.read(),
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=product_template.xlsx'
            return response
            
        except Exception as e:
            logger.exception(f"生成产品模板时出错: {str(e)}")
            return Response({'error': f'生成模板时出错: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['get'])
    def detail(self, request, pk=None):
        """获取产品详情"""
        product = self.get_object()
        
        print(f"\n======= 产品详情请求 {product.product_id} ({pk}) =======")
        
        # ===== 1. 获取基础费用表数据 =====
        base_fees = BaseFee.objects.filter(product=product).order_by('weight')
        
        print(f"\n基础费率数据（共{base_fees.count()}条）：")
        for fee in base_fees:
            print(f"ID:{fee.fee_id} 重量:{fee.weight}{fee.weight_unit} 类型:{fee.fee_type}")
        
        # 收集所有可能的区域
        all_zones = set()
        for fee in base_fees:
            if fee.zone_prices:
                all_zones.update([key for key in fee.zone_prices.keys() if key.startswith('zone')])
        
        # 构建基础费用数据
        base_rates_data = []
        for fee in base_fees:
            base_fee_data = {
                'id': fee.fee_id,
                'weight': str(fee.weight),
                'unit': fee.weight_unit,
                'fee_type': fee.fee_type,
            }
            
            # 为所有可能的区域添加基础价格
            for zone in all_zones:
                zone_num = zone[4:]  # zone1 -> 1
                zone_ui_key = f'Zone{zone_num}基础价格'  # Zone1基础价格
                base_fee_data[zone_ui_key] = '-'
            
            # 为所有可能的区域添加单位价格
            for zone in all_zones:
                zone_num = zone[4:]  # zone1 -> 1
                zone_ui_key = f'Zone{zone_num}单位重量价格'  # Zone1单位重量价格
                base_fee_data[zone_ui_key] = '-'
            
            # 从JSON字段中获取各区域基础价格
            if fee.zone_prices:
                for zone_key, price in fee.zone_prices.items():
                    if zone_key.startswith('zone'):
                        zone_num = zone_key[4:]
                        zone_ui_key = f'Zone{zone_num}基础价格'
                        base_fee_data[zone_ui_key] = str(price)
            
            # 从JSON字段中获取各区域单位价格
            if fee.zone_unit_prices:
                for zone_key, price in fee.zone_unit_prices.items():
                    if zone_key.startswith('zone'):
                        zone_num = zone_key[4:]
                        zone_ui_key = f'Zone{zone_num}单位重量价格'
                        base_fee_data[zone_ui_key] = str(price)
            
            base_rates_data.append(base_fee_data)
        
        # 尝试将重量作为数字排序
        try:
            base_rates_data.sort(key=lambda x: float(x['weight']))
        except (ValueError, TypeError) as e:
            print(f"排序时出错: {str(e)}，将使用默认顺序")
        
        print(f"处理后的基础费率表行数: {len(base_rates_data)}")
        if base_rates_data:
            print(f"基础费率表第一行样例: {base_rates_data[0]}")
        else:
            print("警告：基础费率表无数据")
        
        # ===== 2. 获取附加费数据 =====
        surcharges = Surcharge.objects.filter(product=product).order_by('display_order')
        
        # 收集所有附加费的区域
        surcharge_zones = set()
        for s in surcharges:
            if s.zone_fees:
                surcharge_zones.update([key for key in s.zone_fees.keys() if key.startswith('zone')])
        
        print(f"\n附加费数据（共{surcharges.count()}条）：")
        surcharges_data = []
        for s in surcharges:
            surcharge_data = {
                'id': s.surcharge_id,
                'surcharge_type': s.surcharge_type,
                'sub_type': s.sub_type,
                'condition_desc': s.condition_desc,
                'display_order': s.display_order
            }
            
            # 为所有可能的区域添加默认值
            for zone in surcharge_zones:
                zone_ui_key = 'Zone' + zone[4:]  # zone1 -> Zone1
                surcharge_data[zone_ui_key] = '-'
            
            # 从JSON字段获取各区域费用
            if s.zone_fees:
                for zone_key, fee in s.zone_fees.items():
                    if zone_key.startswith('zone'):
                        zone_num = zone_key[4:]
                        zone_ui_key = f'Zone{zone_num}'
                        surcharge_data[zone_ui_key] = str(fee)
            
            surcharges_data.append(surcharge_data)
            print(f"附加费: {s.surcharge_type} ({s.sub_type})")
        
        # ===== 3. 获取旺季附加费数据 =====
        peak_surcharges = PeakSeasonSurcharge.objects.filter(product=product).order_by('start_date')
        
        print(f"\n旺季附加费数据（共{peak_surcharges.count()}条）：")
        peak_surcharges_data = []
        for ps in peak_surcharges:
            ps_data = {
                'id': ps.id,
                'surcharge_type': ps.surcharge_type,
                'start_date': ps.start_date.strftime('%Y-%m-%d'),
                'end_date': ps.end_date.strftime('%Y-%m-%d'),
                'fee_amount': str(ps.fee_amount)
            }
            peak_surcharges_data.append(ps_data)
            print(f"旺季附加费: {ps.surcharge_type} ({ps.start_date} - {ps.end_date})")
        
        # ===== 4. 构建最终响应 =====
        serializer = self.get_serializer(product)
        data = serializer.data
        
        # 添加所有表的数据
        data.update({
            'base_rates': base_rates_data,
            'surcharges': surcharges_data,
            'peak_surcharges': peak_surcharges_data
        })
        
        return Response(data)
    
    @action(detail=True, methods=['get'])
    def zone_rates(self, request, pk=None):
        """获取产品区域费率"""
        product = self.get_object()
        base_fees = BaseFee.objects.filter(product=product).order_by('weight')
        
        # 构建区域费率数据
        result = []
        for fee in base_fees:
            if fee.zone_prices:
                for zone_key, price in fee.zone_prices.items():
                    if zone_key.startswith('zone'):
                        result.append({
                            'id': f"{fee.fee_id}_{zone_key}",
                            'product_id': product.product_id,
                            'weight': fee.weight,
                            'weight_unit': fee.weight_unit,
                            'zone': zone_key,
                            'base_rate': price,
                            'fee_type': fee.fee_type
                        })
        
        return Response(result)
    
    @action(detail=True, methods=['get'])
    def surcharges(self, request, pk=None):
        """获取产品的附加费"""
        product = self.get_object()
        surcharges = Surcharge.objects.filter(product=product)
        serializer = SurchargeSerializer(surcharges, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def peak_season_surcharges(self, request, pk=None):
        """获取产品的旺季附加费"""
        product = self.get_object()
        peak_season_surcharges = PeakSeasonSurcharge.objects.filter(product=product)
        serializer = PeakSeasonSurchargeSerializer(peak_season_surcharges, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'], url_path='surcharges/by_product', permission_classes=[])
    def surcharges_by_product(self, request):
        """
        根据产品ID获取附加费数据
        """
        product_id = request.query_params.get('product_id')
        include_all = request.query_params.get('include_all', 'false').lower() == 'true'
        return_inactive = request.query_params.get('return_inactive', 'false').lower() == 'true'
        return_all_potential = request.query_params.get('return_all_potential', 'false').lower() == 'true'
        
        if not product_id:
            return Response(
                {"error": "必须提供产品ID(product_id)参数"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 查找产品
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response(
                    {"error": f"找不到ID为 {product_id} 的产品"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 获取该产品的附加费
            surcharges = Surcharge.objects.filter(product=product)
            
            # 根据参数过滤
            if include_all:
                # 不做额外过滤，返回所有附加费
                pass
            elif return_all_potential:
                # 返回所有潜在的附加费，包括可能不适用的
                pass
            elif return_inactive:
                # 包括非活动的附加费
                pass
            else:
                # 默认只返回活动的附加费
                surcharges = surcharges.filter(is_deleted=False)

                # 默认只返回未删除的附加费
                # 注：这行代码是冗余的，上面已经过滤了is_deleted=False
                # surcharges = surcharges.filter(is_deleted=False)
            
            # 序列化数据
            serializer = SurchargeSerializer(surcharges, many=True)
            
            # 构建标准响应格式
            response_data = {
                "status": "success",
                "message": "获取附加费成功",
                "surcharges": serializer.data
            }
            
            logger.info(f"查询产品附加费成功，产品ID: {product_id}, 记录数: {surcharges.count()}")
            return Response(response_data)
                
        except Exception as e:
            logger.error(f"获取产品附加费数据时出错: {str(e)}")
            return Response({"error": str(e)}, status=500)
    
    @action(detail=False, methods=['get'], url_path='peak-season-surcharges/by_product', permission_classes=[])
    def peak_season_surcharges_by_product(self, request):
        """
        根据产品ID获取旺季附加费数据
        """
        product_id = request.query_params.get('product_id')
        
        if not product_id:
            return Response({"error": "Missing product_id parameter"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # 查找产品
            product = get_object_or_404(Product, product_id=product_id)
            
            # 获取该产品的旺季附加费
            peak_season_surcharges = PeakSeasonSurcharge.objects.filter(product=product)
            
            # 序列化数据
            serializer = PeakSeasonSurchargeSerializer(peak_season_surcharges, many=True)
            
            # 修改响应格式，以符合前端期望
            response_data = {
                "status": "success",
                "message": "获取旺季附加费成功",
                "peak_season_surcharges": serializer.data
            }
            
            logger.info(f"查询产品旺季附加费成功，产品ID: {product_id}, 记录数: {peak_season_surcharges.count()}")
            return Response(response_data)
            
        except Exception as e:
            logger.error(f"查询产品旺季附加费失败: {str(e)}")
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='base-fees/by_product', permission_classes=[])
    def update_base_fees_by_product(self, request):
        """
        更新产品的基础费率
        """
        try:
            # 获取请求数据
            product_id = request.data.get('product_id')
            base_fees_data = request.data.get('base_fees', [])
            
            logger.info(f"开始更新产品基础费率，产品ID: {product_id}")
            logger.info(f"基础费率数据: {json.dumps(base_fees_data)}")
            
            if not product_id:
                return Response({"error": "产品ID不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(base_fees_data, list):
                return Response({"error": "基础费率数据必须是数组格式"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 查找产品
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response({"error": f"产品(ID: {product_id})不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 使用事务处理，确保数据一致性
            with transaction.atomic():
                # 获取并记录现有的基础费率数据，以便进行比较和日志记录
                existing_fees = BaseFee.objects.filter(product=product)
                logger.info(f"当前产品基础费率数量: {existing_fees.count()}")
                for fee in existing_fees:
                    logger.info(f"现有基础费率: ID={fee.fee_id}, 重量={fee.weight}, 类型={fee.fee_type}, 区域价格={fee.zone_prices}")
                
                # 先删除现有的基础费率
                delete_count = BaseFee.objects.filter(product=product).delete()[0]
                logger.info(f"已删除 {delete_count} 条现有基础费率记录")
                
                # 添加新的基础费率
                created_fees = []
                for fee_data in base_fees_data:
                    try:
                        # 记录处理前的数据
                        logger.info(f"处理费率数据: {json.dumps(fee_data)}")
                        
                        # 准备基础费率数据
                        prepared_data = dict(fee_data)
                        
                        # 确保产品ID正确
                        prepared_data['product'] = product.product_id
                        
                        # 确保区域价格格式正确
                        if 'zone_prices' not in prepared_data or not prepared_data['zone_prices']:
                            prepared_data['zone_prices'] = {}
                            
                            # 从各个Zone字段收集区域价格
                            for key, value in fee_data.items():
                                # 匹配Zone1, Zone2, zone1, zone2等格式
                                if re.match(r'^[Zz]one\d+$', key):
                                    zone_key = key.lower()
                                    prepared_data['zone_prices'][zone_key] = float(value) if value is not None else 0.0
                        
                        # 确保单位价格格式正确
                        if 'zone_unit_prices' not in prepared_data or not prepared_data['zone_unit_prices']:
                            prepared_data['zone_unit_prices'] = {}
                            
                            # 从各个ZoneXUnitPrice字段收集单位价格
                            for key, value in fee_data.items():
                                # 匹配Zone1UnitPrice, zone1_unit_price等格式
                                if '_unit_price' in key.lower() or 'unitprice' in key.lower():
                                    match = re.search(r'zone(\d+)', key.lower())
                                    if match:
                                        zone_num = match.group(1)
                                        zone_key = f'zone{zone_num}'
                                        prepared_data['zone_unit_prices'][zone_key] = float(value) if value is not None else 0.0
                        
                        # 创建序列化器
                        serializer = BaseFeeSerializer(data=prepared_data)
                        
                        if serializer.is_valid():
                            logger.info(f"基础费率数据验证通过: {serializer.validated_data}")
                            new_fee = serializer.save()
                            created_fees.append(new_fee)
                            logger.info(f"成功创建基础费率: ID={new_fee.fee_id}, 重量={new_fee.weight}, 类型={new_fee.fee_type}")
                        else:
                            # 记录验证错误
                            logger.error(f"基础费率数据验证失败: {serializer.errors}")
                            # 继续处理下一条记录，而不是中断整个操作
                    except Exception as e:
                        logger.error(f"处理基础费率记录时出错: {str(e)}")
                        logger.error(traceback.format_exc())
                
                # 检查是否成功创建了记录
                if not created_fees:
                    logger.error("没有成功创建任何基础费率记录")
                    return Response({"error": "未能成功创建任何基础费率记录"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 记录成功创建的记录
                logger.info(f"成功创建 {len(created_fees)} 条基础费率记录")
                
                # 返回成功响应和新创建的数据
                serializer = BaseFeeSerializer(created_fees, many=True)
                return Response({
                    "message": "基础费率更新成功",
                    "base_fees": serializer.data
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"更新产品基础费率失败: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": f"更新基础费率时发生错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='surcharges/by_product', permission_classes=[])
    def update_surcharges_by_product(self, request):
        """批量更新产品的附加费"""
        try:
            product_id = request.data.get('product_id')
            surcharges_data = request.data.get('surcharges', [])
            
            logger.info(f"开始更新产品 {product_id} 的附加费，收到 {len(surcharges_data)} 条数据")
            logger.info(f"附加费数据: {json.dumps(surcharges_data, ensure_ascii=False)}")
            
            if not product_id:
                return Response({'error': f'缺少产品ID参数'}, status=status.HTTP_400_BAD_REQUEST)
            
            # 查找产品
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response({'error': f'产品 {product_id} 不存在'}, status=status.HTTP_404_NOT_FOUND)
            
            # 获取现有附加费数据，用于在数据无效时恢复
            existing_surcharges = Surcharge.objects.filter(product=product)
            existing_count = existing_surcharges.count()
            logger.info(f"产品 {product_id} 现有 {existing_count} 条附加费记录")
            
            # 预处理和验证数据
            valid_surcharges = []
            
            for index, surcharge_data in enumerate(surcharges_data):
                logger.info(f"处理第{index + 1}条附加费数据: {json.dumps(surcharge_data, ensure_ascii=False)}")
                
                # 必填字段验证
                if not surcharge_data.get('surcharge_type'):
                    logger.warning(f"缺少必填字段'surcharge_type': {surcharge_data}")
                    continue
                    
                # 处理区域费用
                zone_fees = {}
                for key, value in surcharge_data.items():
                    if key.lower().startswith('zone'):
                        try:
                            zone_num = ''.join(filter(str.isdigit, key))
                            if zone_num:
                                zone_key = f'zone{zone_num}'
                                try:
                                    zone_fees[zone_key] = float(value) if value is not None else 0.0
                                except (TypeError, ValueError):
                                    zone_fees[zone_key] = 0.0
                        except Exception as e:
                            logger.warning(f"处理区域费用时出错: {str(e)}")
                
                # 收集有效数据
                valid_surcharge = {
                    'surcharge_type': surcharge_data.get('surcharge_type'),
                    'sub_type': surcharge_data.get('sub_type'),
                    'condition_desc': surcharge_data.get('condition_desc'),
                    'zone_fees': zone_fees,
                    'display_order': index + 1
                }
                valid_surcharges.append(valid_surcharge)
            
            # 如果没有有效数据，返回原始数据
            if not valid_surcharges:
                logger.warning(f"没有有效的附加费数据，保留原有数据")
                serializer = SurchargeSerializer(existing_surcharges, many=True)
                return Response({
                    'message': '没有有效的附加费数据，保留现有数据',
                    'surcharges': serializer.data
                })
            
            # 使用事务处理，确保数据一致性
            with transaction.atomic():
                # 删除现有附加费
                deleted_count = Surcharge.objects.filter(product=product).delete()[0]
                logger.info(f"删除了 {deleted_count} 条现有附加费记录")
                
                # 添加新的附加费记录
                created_items = []
                for index, surcharge_data in enumerate(valid_surcharges):
                    try:
                        surcharge = Surcharge(
                            product=product,
                            surcharge_type=surcharge_data['surcharge_type'],
                            sub_type=surcharge_data.get('sub_type'),
                            condition_desc=surcharge_data.get('condition_desc'),
                            zone_fees=surcharge_data['zone_fees'],
                            display_order=surcharge_data['display_order']
                        )
                        surcharge.save()
                        created_items.append(surcharge)
                        logger.info(f"成功创建附加费: ID={surcharge.surcharge_id}, 类型={surcharge.surcharge_type}")
                    except Exception as e:
                        logger.error(f"创建附加费记录时出错: {str(e)}")
                        logger.error(traceback.format_exc())
                
                # 如果没有成功创建任何记录，回滚事务
                if not created_items:
                    logger.error("没有成功创建任何附加费记录，回滚事务")
                    transaction.set_rollback(True)
                    serializer = SurchargeSerializer(existing_surcharges, many=True)
                    return Response({
                        'message': '保存失败，没有成功创建任何附加费记录',
                        'surcharges': serializer.data
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # 返回创建的数据
                logger.info(f"成功创建 {len(created_items)} 条附加费记录")
                serializer = SurchargeSerializer(created_items, many=True)
                return Response({
                    'message': f'附加费更新成功: 共创建 {len(created_items)} 条记录',
                    'surcharges': serializer.data
                })
        
        except Exception as e:
            logger.error(f"更新附加费时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            
            # 返回原始数据
            try:
                existing_surcharges = Surcharge.objects.filter(product__product_id=product_id)
                serializer = SurchargeSerializer(existing_surcharges, many=True)
                return Response({
                    'error': f'更新附加费时发生错误: {str(e)}',
                    'surcharges': serializer.data
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            except:
                return Response({
                    'error': f'更新附加费时发生错误: {str(e)}'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='peak-season-surcharges/by_product', permission_classes=[])
    def update_peak_season_surcharges_by_product(self, request):
        """
        更新产品的旺季附加费
        """
        try:
            # 获取请求数据
            product_id = request.data.get('product_id')
            peak_season_surcharges_data = request.data.get('peak_season_surcharges', [])
            
            logger.info(f"开始更新产品旺季附加费，产品ID: {product_id}")
            logger.info(f"旺季附加费数据: {json.dumps(peak_season_surcharges_data, ensure_ascii=False)}")
            
            if not product_id:
                return Response({"error": "产品ID不能为空"}, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(peak_season_surcharges_data, list):
                return Response({"error": "旺季附加费数据必须是数组格式"}, status=status.HTTP_400_BAD_REQUEST)
            
            # 查找产品
            try:
                product = Product.objects.get(product_id=product_id)
            except Product.DoesNotExist:
                return Response({"error": f"产品(ID: {product_id})不存在"}, status=status.HTTP_404_NOT_FOUND)
            
            # 提前验证数据有效性，确保不会删除现有数据后再发现新数据无效
            valid_records = []
            for surcharge_data in peak_season_surcharges_data:
                # 验证必填字段
                if not all(k in surcharge_data for k in ['surcharge_type', 'start_date', 'end_date', 'fee_amount']):
                    logger.warning(f"旺季附加费数据缺少必要字段: {surcharge_data}")
                    continue
                
                # 移除模型中不存在的字段
                if 'status' in surcharge_data:
                    surcharge_data.pop('status')
                    
                valid_records.append(surcharge_data)
            
            # 如果没有有效数据，不进行操作，保留现有数据
            if not valid_records:
                logger.warning(f"没有有效的旺季附加费数据，保留现有数据")
                return Response({
                    "message": "没有有效的旺季附加费数据，保留现有数据",
                    "count": 0,
                    "peak_season_surcharges": []
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 使用事务处理，确保数据一致性
            with transaction.atomic():
                # 先删除现有的旺季附加费
                deleted_count = PeakSeasonSurcharge.objects.filter(product=product).delete()[0]
                logger.info(f"已删除{deleted_count}条现有旺季附加费记录")
                
                # 添加新的旺季附加费
                created_items = []
                for surcharge_data in valid_records:
                    # 创建新的旺季附加费记录
                    try:
                        # 创建附加费，不手动设置pss_id，让数据库自动生成
                        peak_surcharge = PeakSeasonSurcharge(
                            product=product,
                            surcharge_type=surcharge_data['surcharge_type'],
                            start_date=surcharge_data['start_date'],
                            end_date=surcharge_data['end_date'],
                            fee_amount=surcharge_data['fee_amount'],
                            created_by=request.user.username if hasattr(request, 'user') else None,
                            updated_by=request.user.username if hasattr(request, 'user') else None
                        )
                        peak_surcharge.save()
                        
                        # 处理区域费用数据 - 将区域费用字段添加到数据库
                        # 遍历surcharge_data中的所有键值对
                        for key, value in surcharge_data.items():
                            # 检查键是否为区域费用字段 (Zone1, Zone2等)
                            if key.startswith('Zone') and isinstance(value, (int, float, str)):
                                # 使用setattr添加区域费用字段
                                setattr(peak_surcharge, key, value)
                        
                        # 再次保存以确保区域费用字段被保存
                        peak_surcharge.save()
                        
                        created_items.append(peak_surcharge)
                        logger.info(f"成功创建旺季附加费: {peak_surcharge.pss_id} - {peak_surcharge.surcharge_type}")
                    except Exception as e:
                        logger.error(f"创建旺季附加费失败: {str(e)}")
                        logger.error(traceback.format_exc())
                        # 继续处理其他记录
                
                logger.info(f"更新产品旺季附加费成功，产品ID: {product_id}，共创建 {len(created_items)} 条记录")
                
                # 返回创建的数据
                serializer = PeakSeasonSurchargeSerializer(created_items, many=True)
                return Response({
                    "message": "旺季附加费更新成功",
                    "count": len(created_items),
                    "peak_season_surcharges": serializer.data
                }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"更新产品旺季附加费失败: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": f"更新旺季附加费时发生错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def import_zone_rates(self, request, pk=None):
        """导入区域费率到BaseFee模型"""
        product = self.get_object()
        data = request.data
        
        # 验证数据
        if 'items' not in data:
            return Response({"error": "Missing 'items' field in request"}, status=status.HTTP_400_BAD_REQUEST)
        
        items = data['items']
        serializer = ProductZoneRateImportSerializer(data=items, many=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # 创建基础费用
        created_base_fees = []
        
        try:
            with transaction.atomic():
                for item in serializer.validated_data:
                    weight = item['weight']
                    weight_unit = item['weight_unit']
                    
                    # 准备区域价格数据
                    zone_prices = {}
                    zone_unit_prices = {}
                    
                    # 从JSON字段中提取区域价格
                    if 'zone_prices' in item:
                        zone_prices = item['zone_prices']
                    
                    # 从请求中提取或构建定价类型
                    fee_type = item.get('pricing_type', 'STEP')
                    
                    # 创建或更新BaseFee记录
                    base_fee, created = BaseFee.objects.update_or_create(
                        product=product,
                        weight=weight,
                        weight_unit=weight_unit,
                        defaults={
                            'fee_type': fee_type,
                            'zone_prices': zone_prices,
                            'zone_unit_prices': zone_unit_prices
                        }
                    )
                    
                    if created:
                        created_base_fees.append(base_fee)
                
                return Response({
                'status': 'success',
                'created_base_fees': len(created_base_fees),
                'message': f'Successfully imported {len(created_base_fees)} base fees'
                })
                
        except Exception as e:
            logger.exception(f"导入区域费率时出错: {str(e)}")
            return Response({
                'status': 'error',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET', 'PUT', 'POST'], permission_classes=[])
    def base_fees_by_product(self, request):
        """
        获取或更新产品的基础费率
        GET: 获取产品的基础费率
        PUT/POST: 更新产品的基础费率
        """
        # 处理GET请求 - 查询基础费率
        if request.method == 'GET':
            request_id = uuid.uuid4()
            try:
                # 获取产品ID
                product_id = request.query_params.get('product_id')
                
                logger.info(f"[请求ID:{request_id}] 开始查询产品基础费率，产品ID: {product_id}")
                
                if not product_id:
                    return Response({"error": "产品ID不能为空"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 查找产品
                try:
                    product = Product.objects.get(product_id=product_id)
                except Product.DoesNotExist:
                    logger.error(f"[请求ID:{request_id}] 产品不存在，产品ID: {product_id}")
                    return Response({"error": f"产品(ID: {product_id})不存在"}, status=status.HTTP_404_NOT_FOUND)
                
                # 查询基础费率
                base_fees = BaseFee.objects.filter(product=product)
                logger.info(f"[请求ID:{request_id}] 找到基础费率记录 {base_fees.count()} 条")
                
                # 在序列化前，确保数据格式正确
                for base_fee in base_fees:
                    # 记录原始数据
                    logger.debug(f"[请求ID:{request_id}] 基础费率记录 ID:{base_fee.fee_id}, 重量:{base_fee.weight}, 单位:{base_fee.weight_unit}, 区域价格:{base_fee.zone_prices}")
                    
                    # 1. 确保zone_prices是字典类型
                    if not isinstance(base_fee.zone_prices, dict):
                        logger.warning(f"[请求ID:{request_id}] 修正zone_prices类型: {type(base_fee.zone_prices)} -> dict, ID:{base_fee.fee_id}")
                        base_fee.zone_prices = {}
                    
                    # 2. 确保zone_unit_prices是字典类型
                    if not isinstance(base_fee.zone_unit_prices, dict):
                        logger.warning(f"[请求ID:{request_id}] 修正zone_unit_prices类型: {type(base_fee.zone_unit_prices)} -> dict, ID:{base_fee.fee_id}")
                        base_fee.zone_unit_prices = {}
                    
                    # 3. 处理raw_data中的价格数据
                    if base_fee.raw_data:
                        for key, value in base_fee.raw_data.items():
                            # 处理基础价格字段 (Zone1基础价格, Zone2基础价格, ...)
                            if '基础价格' in key:
                                try:
                                    zone_num = key.replace('Zone', '').replace('基础价格', '')
                                    # 移除可能的中文空格
                                    zone_num = zone_num.strip()
                                    zone_key = f'zone{zone_num}'
                                    if value is not None:
                                        # 确保价格是浮点数
                                        numeric_value = float(value)
                                        base_fee.zone_prices[zone_key] = numeric_value
                                        logger.debug(f"[请求ID:{request_id}] 从raw_data同步价格: {zone_key}={numeric_value}, ID:{base_fee.fee_id}")
                                except Exception as e:
                                    logger.warning(f"[请求ID:{request_id}] 处理基础价格时出错: {e}, 键: {key}, 值: {value}, ID:{base_fee.fee_id}")
                            
                            # 处理单位重量价格字段
                            elif '单位重量价格' in key:
                                try:
                                    # 移除"价格"前可能的空格
                                    cleaned_key = key.replace('Zone', '').replace('单位重量价格', '').replace('单位重量价 格', '')
                                    # 移除可能的中文空格
                                    zone_num = cleaned_key.strip()
                                    zone_key = f'zone{zone_num}'
                                    if value is not None:
                                        # 确保价格是浮点数
                                        numeric_value = float(value)
                                        base_fee.zone_unit_prices[zone_key] = numeric_value
                                        logger.debug(f"[请求ID:{request_id}] 从raw_data同步单位价格: {zone_key}={numeric_value}, ID:{base_fee.fee_id}")
                                except Exception as e:
                                    logger.warning(f"[请求ID:{request_id}] 处理单位重量价格时出错: {e}, 键: {key}, 值: {value}, ID:{base_fee.fee_id}")
                
                # 序列化数据
                serializer = BaseFeeSerializer(base_fees, many=True)
                
                # 使用DTO转换为前端期望的格式
                response_data = BaseFeeOutputDTO.transform_list(serializer.data, request_id)
                
                # 打印返回数据的第一条记录样本（如果有数据）
                if response_data and len(response_data) > 0:
                    sample = {k: v for k, v in response_data[0].items() if k in ['fee_id', 'weight', 'weight_unit']}
                    # 添加几个Zone字段的示例
                    for zone_key in ['Zone1', 'Zone2', 'Zone8', 'Zone17']:
                        if zone_key in response_data[0]:
                            sample[zone_key] = response_data[0][zone_key]
                    logger.info(f"[请求ID:{request_id}] 返回数据样本: {sample}")
                
                logger.info(f"[请求ID:{request_id}] 查询产品基础费率成功，产品ID: {product_id}, 记录数: {len(response_data)}")
                return Response(response_data)
                
            except Exception as e:
                request_id = getattr(request, 'request_id', uuid.uuid4())
                logger.error(f"[请求ID:{request_id}] 查询产品基础费率失败: {str(e)}")
                logger.error(traceback.format_exc())
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 处理PUT/POST请求 - 更新基础费率
        elif request.method in ['PUT', 'POST']:
            request_id = uuid.uuid4()
            try:
                # 获取请求数据
                product_id = request.query_params.get('product_id')
                if not product_id:
                    product_id = request.data.get('product_id')
                    
                base_fees_data = request.data.get('base_fees', [])
                
                logger.info(f"[请求ID:{request_id}] 开始更新产品基础费率(方法:{request.method})，产品ID: {product_id}")
                logger.info(f"[请求ID:{request_id}] 收到基础费率数据条数: {len(base_fees_data)}")
                
                # 记录第一条数据样本（如果有数据）
                if base_fees_data and len(base_fees_data) > 0:
                    # 记录原始数据样本
                    original_sample = {}
                    for key in ['fee_id', 'weight', 'weight_unit']:
                        if key in base_fees_data[0]:
                            original_sample[key] = base_fees_data[0][key]
                    # 添加Zone字段样本
                    for zone_key in ['Zone1', 'Zone2', 'Zone8', 'Zone17']:
                        if zone_key in base_fees_data[0]:
                            original_sample[zone_key] = base_fees_data[0][zone_key]
                    logger.info(f"[请求ID:{request_id}] 收到数据样本（原始）: {original_sample}")
                
                if not product_id:
                    logger.error(f"[请求ID:{request_id}] 产品ID不能为空")
                    return Response({"error": "产品ID不能为空"}, status=status.HTTP_400_BAD_REQUEST)
                
                if not isinstance(base_fees_data, list):
                    logger.error(f"[请求ID:{request_id}] 基础费率数据必须是数组格式, 实际类型: {type(base_fees_data)}")
                    return Response({"error": "基础费率数据必须是数组格式"}, status=status.HTTP_400_BAD_REQUEST)
                
                # 查找产品
                try:
                    product = Product.objects.get(product_id=product_id)
                    logger.info(f"[请求ID:{request_id}] 找到产品: {product.product_name} (ID: {product_id})")
                except Product.DoesNotExist:
                    logger.error(f"[请求ID:{request_id}] 产品不存在，产品ID: {product_id}")
                    return Response({"error": f"产品(ID: {product_id})不存在"}, status=status.HTTP_404_NOT_FOUND)
                
                # 使用DTO转换数据格式
                processed_data = BaseFeeInputDTO.transform_list(base_fees_data, request_id)
                
                # 记录处理后的第一条数据样本（如果有数据）
                if processed_data and len(processed_data) > 0:
                    # 记录处理后的数据样本
                    processed_sample = {}
                    for key in ['fee_id', 'weight', 'weight_unit']:
                        if key in processed_data[0]:
                            processed_sample[key] = processed_data[0][key]
                    # 添加zone_prices样本
                    if 'zone_prices' in processed_data[0]:
                        # 只展示部分zone_prices内容
                        zone_sample = {}
                        for zone_key in ['zone1', 'zone2', 'zone8', 'zone17']:
                            if zone_key in processed_data[0]['zone_prices']:
                                zone_sample[zone_key] = processed_data[0]['zone_prices'][zone_key]
                        processed_sample['zone_prices'] = zone_sample
                    logger.info(f"[请求ID:{request_id}] DTO处理后数据样本: {processed_sample}")
                
                # 为每个数据项添加产品ID
                for item in processed_data:
                    item['product'] = product.product_id
                
                # 使用事务处理，确保数据一致性
                with transaction.atomic():
                    # 创建保存点，以便在出错时回滚
                    save_point = transaction.savepoint()
                    
                    try:
                        # 记录删除前的数据状态
                        existing_fees = BaseFee.objects.filter(product=product)
                        existing_count = existing_fees.count()
                        logger.info(f"[请求ID:{request_id}] 删除前：产品【{product_id}】共有 {existing_count} 条基础费率记录")
                        
                        # 记录现有数据的所有zone_prices值
                        if existing_count > 0 and existing_count <= 10:  # 限制记录数量，避免日志过大
                            for i, fee in enumerate(existing_fees):
                                logger.info(f"[请求ID:{request_id}] 现有基础费率[{i+1}/{existing_count}]: ID={fee.fee_id}, 重量={fee.weight}, 单位={fee.weight_unit}, 区域价格={fee.zone_prices}")
                        
                        # 先删除现有的基础费率
                        delete_count, details = BaseFee.objects.filter(product=product).delete()
                        logger.info(f"[请求ID:{request_id}] 已删除 {delete_count} 条基础费率记录, 删除详情: {details}")
                        
                        # 添加新的基础费率
                        created_items = []
                        failed_items = []
                        
                        for i, fee_data in enumerate(processed_data):
                            try:
                                logger.debug(f"[请求ID:{request_id}] 创建基础费率记录[{i+1}/{len(processed_data)}]: 重量={fee_data.get('weight')}, 区域价格={fee_data.get('zone_prices')}")
                                
                                serializer = BaseFeeSerializer(data=fee_data)
                                if serializer.is_valid():
                                    # 保存前记录数据
                                    base_fee = serializer.save()
                                    created_items.append(base_fee)
                                    logger.info(f"[请求ID:{request_id}] 成功创建基础费率记录: ID={base_fee.fee_id}, 重量={base_fee.weight}, 单位={base_fee.weight_unit}, 区域价格={base_fee.zone_prices}")
                                else:
                                    # 如果验证失败，记录错误信息，并继续尝试创建其他记录
                                    logger.error(f"[请求ID:{request_id}] 基础费率数据验证失败: {serializer.errors}, 数据: {fee_data}")
                                    failed_items.append({"data": fee_data, "errors": serializer.errors})
                            except Exception as e:
                                logger.error(f"[请求ID:{request_id}] 处理基础费率记录[{i+1}/{len(processed_data)}]时发生异常: {str(e)}")
                                logger.error(traceback.format_exc())
                                failed_items.append({"data": fee_data, "error": str(e)})
                        
                        # 验证创建结果
                        if not created_items:
                            logger.error(f"[请求ID:{request_id}] 没有成功创建任何基础费率记录")
                            # 如果没有成功创建任何记录，回滚事务
                            transaction.savepoint_rollback(save_point)
                            
                            # 返回错误信息
                            error_details = {
                                "message": "基础费率更新失败，未能成功创建任何记录",
                                "failed_items": failed_items
                            }
                            return Response(error_details, status=status.HTTP_400_BAD_REQUEST)
                        
                        # 确认事务
                        transaction.savepoint_commit(save_point)
                        
                        # 记录失败项
                        if failed_items:
                            logger.warning(f"[请求ID:{request_id}] {len(failed_items)}/{len(processed_data)} 条记录创建失败")
                        
                        # 清除产品缓存
                        product.clear_cache()
                        logger.info(f"[请求ID:{request_id}] 已清除产品缓存: {product_id}")
                        
                        logger.info(f"[请求ID:{request_id}] 更新产品基础费率成功，产品ID: {product_id}，成功创建: {len(created_items)}/{len(processed_data)} 条记录")
                        
                        # 记录创建后的数据状态
                        updated_fees = BaseFee.objects.filter(product=product)
                        logger.info(f"[请求ID:{request_id}] 创建后：产品【{product_id}】共有 {updated_fees.count()} 条基础费率记录")
                        
                        # 记录新创建数据的所有zone_prices值
                        if updated_fees.count() > 0 and updated_fees.count() <= 10:  # 限制记录数量，避免日志过大
                            for i, fee in enumerate(updated_fees):
                                logger.info(f"[请求ID:{request_id}] 新创建基础费率[{i+1}/{updated_fees.count()}]: ID={fee.fee_id}, 重量={fee.weight}, 单位={fee.weight_unit}, 区域价格={fee.zone_prices}")
                        
                        # 返回创建的数据，先序列化再使用DTO转换为前端期望格式
                        response_serializer = BaseFeeSerializer(created_items, many=True)
                        response_output_data = BaseFeeOutputDTO.transform_list(response_serializer.data, request_id)
                        
                        response_data = {
                            "message": f"基础费率更新成功，共创建 {len(created_items)}/{len(processed_data)} 条记录",
                            "base_fees": response_output_data,
                            "failed_count": len(failed_items),
                            "failed_details": failed_items if failed_items else None,
                            "timestamp": timezone.now().isoformat()
                        }
                        
                        # 记录响应样本
                        if response_output_data and len(response_output_data) > 0:
                            sample = {}
                            for key in ['fee_id', 'weight', 'weight_unit']:
                                if key in response_output_data[0]:
                                    sample[key] = response_output_data[0][key]
                            # 添加Zone字段示例
                            for zone_key in ['Zone1', 'Zone2', 'Zone8', 'Zone17']:
                                if zone_key in response_output_data[0]:
                                    sample[zone_key] = response_output_data[0][zone_key]
                            logger.info(f"[请求ID:{request_id}] 响应数据样本: {sample}")
                        
                        return Response(response_data, status=status.HTTP_200_OK)
                    
                    except Exception as e:
                        # 回滚事务
                        transaction.savepoint_rollback(save_point)
                        logger.error(f"[请求ID:{request_id}] 事务处理中发生错误，已回滚: {str(e)}")
                        logger.error(traceback.format_exc())
                        raise
            
            except Exception as e:
                logger.error(f"[请求ID:{request_id}] 更新产品基础费率失败: {str(e)}")
                logger.error(traceback.format_exc())
                return Response({"error": f"更新基础费率时发生错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=False, methods=['get'])
    def by_product(self, request):
        """根据产品ID获取基础费用"""
        product_id = request.query_params.get('product_id')
        if not product_id:
            return Response({'error': '缺少产品ID参数'}, status=400)
        
        base_fees = BaseFee.objects.filter(product_id=product_id).order_by('weight')
        
        if not base_fees.exists():
            print(f"产品 {product_id} 没有基础费用记录")
            return Response([])
        
        # 直接返回基础费率数据，只保留基本字段和中文字段
        result = []
        for fee in base_fees:
            # 创建基本数据结构，只保留基本信息
            weight_band = {
                'id': fee.fee_id,
                'product': fee.product_id,
                'weight': float(fee.weight),
                'unit': fee.weight_unit,
                'fee_type': fee.fee_type,
            }
            
            # 添加所有原始Excel数据中的中文字段
            if hasattr(fee, 'raw_data') and fee.raw_data:
                for key, value in fee.raw_data.items():
                    # 检查是否是中文字段或者其他需要保留的字段
                    if re.search(r'[\u4e00-\u9fff]', str(key)) or key.endswith('基础价格') or key.endswith('单位重量价格'):
                        try:
                            if isinstance(value, (int, float)) or (isinstance(value, str) and re.match(r'^[\d\.]+$', value)):
                                weight_band[key] = float(value)
                            else:
                                weight_band[key] = value
                        except (ValueError, TypeError):
                            weight_band[key] = value
            
            result.append(weight_band)
        
        # 打印要返回的数据结构
        print(f"为产品 {product_id} 返回 {len(result)} 条基础费用记录")
        if result:
            print(f"第一条记录示例: {result[0]}")
            
        return Response(result)
    
    @action(detail=True, methods=['POST'])
    def clear_cache(self, request, pk=None):
        """清除产品相关的缓存"""
        request_id = uuid.uuid4()
        try:
            product = Product.objects.get(product_id=pk)
            
            # 记录日志
            logger.info(f"[请求ID:{request_id}] 开始清除产品缓存，产品ID: {pk}")
            
            # 调用产品的清除缓存方法
            cleared = product.clear_cache()
            
            # 记录清除结果
            if cleared:
                logger.info(f"[请求ID:{request_id}] 产品缓存清除成功，产品ID: {pk}")
                return Response({"message": f"产品 {pk} 的缓存已清除"}, status=status.HTTP_200_OK)
            else:
                logger.warning(f"[请求ID:{request_id}] 产品缓存清除无效果，产品ID: {pk}")
                return Response({"message": f"产品 {pk} 没有活跃缓存"}, status=status.HTTP_200_OK)
                
        except Product.DoesNotExist:
            logger.error(f"[请求ID:{request_id}] 产品不存在，产品ID: {pk}")
            return Response({"error": f"产品(ID: {pk})不存在"}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"[请求ID:{request_id}] 清除产品缓存时发生错误: {str(e)}")
            logger.error(traceback.format_exc())
            return Response({"error": f"清除缓存时发生错误: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _validate_and_clean_product_data(self, data_dict):
        """
        验证和清理产品数据，设置默认值并转换字段格式
        
        Args:
            data_dict: 包含产品数据的字典
            
        Returns:
            清理后的数据字典
        """
        cleaned_data = {}
        
        # 1. 处理必填字段
        required_fields = {
            'product_name': {'default': None, 'type': str},
            'provider_name': {'default': None, 'type': str},
        }
        
        # 2. 处理可选字段及其默认值
        optional_fields = {
            'effective_date': {'default': timezone.now().date(), 'type': 'date'},
            'expiration_date': {'default': None, 'type': 'date'},
            'dim_factor': {'default': Decimal('200'), 'type': Decimal},
            'dim_factor_unit': {'default': 'lb/in³', 'type': str},
            'country': {'default': '美国', 'type': str},
            'currency': {'default': 'USD', 'type': str},
            'description': {'default': '', 'type': str},
            'status': {'default': True, 'type': bool},
            'enabled_start_date': {'default': None, 'type': 'date'},
            'enabled_end_date': {'default': None, 'type': 'date'},
            'weight_unit': {'default': 'lb', 'type': str},
            'dim_unit': {'default': 'in', 'type': str},
        }
        
        # 3. 处理必填字段
        for field, config in required_fields.items():
            value = data_dict.get(field)
            if value is None or value == '':
                cleaned_data[field] = config['default']
                print(f"警告: 必填字段 {field} 为空")
            else:
                # 确保类型正确
                try:
                    cleaned_data[field] = config['type'](value)
                except (ValueError, TypeError):
                    cleaned_data[field] = value
                    print(f"警告: 字段 {field} 类型转换失败，使用原始值")
        
        # 4. 处理可选字段
        for field, config in optional_fields.items():
            value = data_dict.get(field)
            
            # 日期字段特殊处理
            if config['type'] == 'date':
                cleaned_data[field] = self._parse_date(value) if value else config['default']
                continue
                
            # 其他字段处理
            if value is None or value == '':
                cleaned_data[field] = config['default']
            else:
                # 确保类型正确
                try:
                    if config['type'] == Decimal:
                        # Decimal类型特殊处理
                        if isinstance(value, str):
                            value = value.replace(',', '')
                        cleaned_data[field] = Decimal(str(value))
                    elif config['type'] == bool:
                        # 布尔类型特殊处理
                        if isinstance(value, bool):
                            cleaned_data[field] = value
                        elif isinstance(value, (int, float)):
                            cleaned_data[field] = bool(value)
                        else:
                            value_str = str(value).strip().lower()
                            cleaned_data[field] = value_str in ['启用', 'true', '1', 'yes', 'active', '是']
                    else:
                        cleaned_data[field] = config['type'](value)
                except (ValueError, TypeError):
                    cleaned_data[field] = value
                    print(f"警告: 字段 {field} 类型转换失败，使用原始值")
        
        # 5. 处理特殊字段关系
        # 如果生效日期为空，设置为当前日期
        if cleaned_data['effective_date'] is None:
            cleaned_data['effective_date'] = timezone.now().date()
            
        # 如果失效日期为空，设置为生效日期后一年
        if cleaned_data['expiration_date'] is None:
            effective_date = cleaned_data['effective_date']
            cleaned_data['expiration_date'] = effective_date.replace(year=effective_date.year + 1)
            
        return cleaned_data
    
    