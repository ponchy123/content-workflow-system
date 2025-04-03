"""
改进的产品Excel导入功能
在现有的Excel导入功能基础上进行改进，确保导入过程中产品的所有必要关联数据都被创建
"""
import pandas as pd
import logging
import os
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Union
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

from apps.products.models import (
    Product, BaseFee,
    Surcharge, PeakSeasonSurcharge, ServiceProvider,
)

logger = logging.getLogger(__name__)

class ProductImportImprover:
    """
    产品导入改进工具，对现有导入功能进行扩展，确保数据完整性
    """
    def __init__(self):
        self.required_data_types = [
            'base_fees',     # 基础费率
            'surcharges'      # 附加费
        ]
    
    def check_and_improve_import(self, product_id: int) -> Dict[str, Any]:
        """
        检查给定产品ID的数据完整性，并补充缺失数据
        
        Args:
            product_id: 产品ID
            
        Returns:
            包含操作结果的字典
        """
        try:
            logger.info(f"开始检查产品ID={product_id}的数据完整性")
            product = Product.objects.get(id=product_id)
            
            # 检查并记录缺失的数据类型
            missing_data = self._check_data_integrity(product)
            
            created_data = {
                'base_fees': [],
                'surcharges': []
            }
            
            with transaction.atomic():
                # 如果缺少重量段，创建默认的
                if missing_data.get('base_fees', False):
                    created_base_fees = self._create_default_base_fees(product)
                    if created_base_fees:
                        created_data['base_fees'] = created_base_fees
                
                # 如果缺少附加费，创建默认的
                if missing_data.get('surcharges', False):
                    created_surcharges = self._create_default_surcharges(product)
                    if created_surcharges:
                        created_data['surcharges'] = created_surcharges
            
            # 统计创建的数据量
            created_count = {
                'base_fees': len(created_data['base_fees']),
                'surcharges': len(created_data['surcharges']),
            }
            
            # 更新产品的最后修改时间
            product.updated_at = timezone.now()
            product.save()
            
            # 返回操作结果
            return {
                'success': True,
                'product_id': product_id,
                'product_name': product.product_name,
                'missing_data': missing_data,
                'created_count': created_count,
                'message': f"成功完成产品 {product.product_name} 数据完整性检查和补充"
            }
        
        except Product.DoesNotExist:
            logger.error(f"产品ID={product_id}不存在")
            return {
                'success': False,
                'message': f"产品ID={product_id}不存在"
            }
        except Exception as e:
            logger.error(f"处理产品ID={product_id}时出错: {str(e)}")
            return {
                'success': False,
                'message': f"处理产品时出错: {str(e)}"
            }
    
    def _check_data_integrity(self, product: Product) -> Dict[str, bool]:
        """
        检查产品的数据完整性，确认是否所有必要的关联数据都存在
        
        Args:
            product: 产品对象
            
        Returns:
            包含各数据类型缺失状态的字典
        """
        missing_data = {}
        
        # 检查基础费率
        base_fees_count = BaseFee.objects.filter(product=product).count()
        missing_data['base_fees'] = base_fees_count == 0
        logger.info(f"产品 {product.product_name} 已有基础费率数量: {base_fees_count}")
        
        # 检查附加费
        surcharges_count = Surcharge.objects.filter(product=product).count()
        missing_data['surcharges'] = surcharges_count == 0
        logger.info(f"产品 {product.product_name} 已有附加费数量: {surcharges_count}")
        
        return missing_data
    
    def _create_default_base_fees(self, product: Product) -> List[BaseFee]:
        """
        为产品创建默认的基础费率
        
        Args:
            product: 产品对象
            
        Returns:
            创建的基础费率列表
        """
        logger.info(f"为产品 {product.product_name} 创建默认基础费率")
        created_base_fees = []
        
        # 默认的重量段和价格
        default_weights = [0.5, 1, 2, 5, 10, 20]
        default_prices = {
            'zone1': 10.0,
            'zone2': 15.0,
            'zone3': 20.0,
            'zone4': 25.0,
            'zone5': 30.0,
            'zone6': 35.0,
            'zone7': 40.0,
            'zone8': 45.0,
        }
        
        for i, weight in enumerate(default_weights):
            # 设置最小重量为前一段的最大重量，第一段为0
            min_weight = 0 if i == 0 else default_weights[i-1]
            
            # 创建基础费率记录
            base_fee = BaseFee.objects.create(
                product=product,
                min_weight=min_weight,
                weight=weight,
                weight_unit='lb',
                fee_type='STEP',
                zone1_fee=default_prices['zone1'] + i * 5,
                zone2_fee=default_prices['zone2'] + i * 5,
                zone3_fee=default_prices['zone3'] + i * 5,
                zone4_fee=default_prices['zone4'] + i * 5,
                zone5_fee=default_prices['zone5'] + i * 5,
                zone6_fee=default_prices['zone6'] + i * 5,
                zone7_fee=default_prices['zone7'] + i * 5,
                zone8_fee=default_prices['zone8'] + i * 5,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            created_base_fees.append(base_fee)
            logger.info(f"为产品 {product.product_name} 创建了基础费率: {min_weight}lb-{weight}lb")
            
        return created_base_fees
    
    def _create_default_surcharges(self, product: Product) -> List[Surcharge]:
        """
        为产品创建默认的附加费
        
        Args:
            product: 产品对象
            
        Returns:
            创建的附加费列表
        """
        logger.info(f"为产品 {product.product_name} 创建默认附加费")
        created_surcharges = []
        
        # 默认的附加费类型和价格
        default_surcharges = [
            {
                'surcharge_type': '燃油附加费',
                'sub_type': '基础燃油附加费',
                'condition_desc': '基于包裹运费的百分比',
                'zone1_fee': Decimal('15.00'),
                'zone2_fee': Decimal('15.00'),
                'zone3_fee': Decimal('15.00'),
                'zone4_fee': Decimal('15.00'),
                'zone5_fee': Decimal('15.00'),
                'zone6_fee': Decimal('15.00'),
                'zone7_fee': Decimal('15.00'),
                'zone8_fee': Decimal('15.00'),
            },
            {
                'surcharge_type': '住宅配送附加费',
                'sub_type': '住宅区域配送',
                'condition_desc': '配送到住宅地址时收取',
                'zone1_fee': Decimal('5.00'),
                'zone2_fee': Decimal('5.00'),
                'zone3_fee': Decimal('5.00'),
                'zone4_fee': Decimal('5.00'),
                'zone5_fee': Decimal('5.00'),
                'zone6_fee': Decimal('5.00'),
                'zone7_fee': Decimal('5.00'),
                'zone8_fee': Decimal('5.00'),
            },
            {
                'surcharge_type': '偏远地区附加费',
                'sub_type': '偏远地区配送',
                'condition_desc': '配送到偏远地区时收取',
                'zone1_fee': Decimal('10.00'),
                'zone2_fee': Decimal('10.00'),
                'zone3_fee': Decimal('10.00'),
                'zone4_fee': Decimal('10.00'),
                'zone5_fee': Decimal('10.00'),
                'zone6_fee': Decimal('10.00'),
                'zone7_fee': Decimal('10.00'),
                'zone8_fee': Decimal('10.00'),
            },
        ]
        
        for surcharge_data in default_surcharges:
            # 创建附加费记录
            surcharge = Surcharge.objects.create(
                product=product,
                surcharge_type=surcharge_data['surcharge_type'],
                sub_type=surcharge_data['sub_type'],
                condition_desc=surcharge_data['condition_desc'],
                zone1_fee=surcharge_data['zone1_fee'],
                zone2_fee=surcharge_data['zone2_fee'],
                zone3_fee=surcharge_data['zone3_fee'],
                zone4_fee=surcharge_data['zone4_fee'],
                zone5_fee=surcharge_data['zone5_fee'],
                zone6_fee=surcharge_data['zone6_fee'],
                zone7_fee=surcharge_data['zone7_fee'],
                zone8_fee=surcharge_data['zone8_fee'],
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            
            created_surcharges.append(surcharge)
            logger.info(f"为产品 {product.product_name} 创建了附加费: {surcharge_data['surcharge_type']} - {surcharge_data['sub_type']}")
            
        return created_surcharges


def ensure_product_data_integrity(product_id: int) -> Dict[str, Any]:
    """
    确保产品数据完整性的便捷函数
    
    Args:
        product_id: 产品ID
        
    Returns:
        包含操作结果的字典
    """
    improver = ProductImportImprover()
    return improver.check_and_improve_import(product_id)


# 下面是集成到现有Excel导入功能中的钩子代码
"""
# 在views.py中的upload_product_excel函数最后添加以下代码：

from apps.products.improve_import import ensure_product_data_integrity

# 成功导入产品后
if product:
    # 确保数据完整性
    integrity_result = ensure_product_data_integrity(product.id)
    logger.info(f"数据完整性检查结果: {integrity_result}")
    
    # 成功响应
    return Response({
        'success': True, 
        'message': f'产品 {product.name} 导入成功',
        'product_id': product.id,
        'data_integrity': integrity_result
    }, status=HTTP_200_OK)
""" 