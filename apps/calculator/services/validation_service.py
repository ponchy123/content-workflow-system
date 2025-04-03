"""
数据验证服务
处理运费计算输入数据的验证和预处理
"""

import logging
import re
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, Tuple, List, Optional

from apps.core.exceptions import ValidationException, InvalidParameterException

logger = logging.getLogger(__name__)

class ValidationService:
    """
    数据验证服务类
    处理输入数据的验证和预处理
    """
    
    def __init__(self):
        """初始化验证服务"""
        self.logger = logging.getLogger(__name__)
    
    def validate_calculation_input(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证计算输入数据
        
        Args:
            data: 计算请求数据
            
        Returns:
            Dict[str, Any]: 验证后的数据
            
        Raises:
            ValidationException: 如果数据无效
        """
        if not data:
            raise ValidationException("请求数据不能为空")

        # 验证必填字段
        required_fields = ['product_id', 'weight', 'from_postal', 'to_postal']
        for field in required_fields:
            if field not in data:
                raise ValidationException(f"缺少必填字段: {field}")
            if data[field] is None or data[field] == '':
                raise ValidationException(f"字段不能为空: {field}")

        # 验证产品ID
        product_id = data.get('product_id')
        if not isinstance(product_id, str):
            raise ValidationException("产品ID必须是字符串类型")

        # 验证重量
        weight = data.get('weight')
        try:
            weight_value = Decimal(str(weight))
            if weight_value <= 0:
                raise ValidationException("重量必须大于0")
            data['weight'] = weight_value  # 更新为Decimal类型
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationException("重量格式无效")

        # 验证邮编
        from_postal = data.get('from_postal')
        to_postal = data.get('to_postal')
        self._validate_postal_code(from_postal, "起始邮编")
        self._validate_postal_code(to_postal, "目的邮编")

        # 验证可选尺寸字段
        for dim in ['length', 'width', 'height']:
            if dim in data and data[dim] is not None:
                try:
                    dim_value = Decimal(str(data[dim]))
                    if dim_value < 0:
                        raise ValidationException(f"{dim}不能为负数")
                    data[dim] = dim_value  # 更新为Decimal类型
                except (InvalidOperation, TypeError, ValueError):
                    raise ValidationException(f"{dim}格式无效")

        # 验证其他布尔字段
        if 'is_residential' in data:
            if not isinstance(data['is_residential'], bool):
                try:
                    if isinstance(data['is_residential'], str):
                        data['is_residential'] = data['is_residential'].lower() in ['true', 'yes', '1', 't', 'y']
                    else:
                        data['is_residential'] = bool(data['is_residential'])
                except Exception:
                    raise ValidationException("is_residential必须是布尔值")

        # 验证日期字段
        if 'calculation_date' in data and data['calculation_date']:
            try:
                # 检查日期格式，但不转换类型
                from datetime import datetime
                calculation_date = data['calculation_date']
                if isinstance(calculation_date, str):
                    datetime.strptime(calculation_date, '%Y-%m-%d')
            except ValueError:
                raise ValidationException("calculation_date格式无效，应为YYYY-MM-DD")

        return data
    
    def preprocess_calculation_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        预处理计算数据
        
        Args:
            data: 计算请求数据
            
        Returns:
            Tuple[Dict[str, Any], List[str]]: 预处理后的数据和警告信息
        """
        processed_data = {}
        warnings = []
        
        # 处理邮编格式
        if 'from_postal' in data:
            processed_data['from_postal'] = self._normalize_postal_code(data['from_postal'])
        
        if 'to_postal' in data:
            processed_data['to_postal'] = self._normalize_postal_code(data['to_postal'])
        
        # 处理重量格式
        if 'weight' in data:
            try:
                weight = Decimal(str(data['weight']))
                processed_data['weight'] = weight
                
                # 如果重量过小，发出警告
                if weight < Decimal('0.1'):
                    warnings.append(f"警告: 重量过小 ({weight})，可能影响计算精度")
            except (InvalidOperation, TypeError, ValueError):
                # 验证函数会处理这个错误，这里不重复处理
                pass
        
        # 处理尺寸数据
        for dim in ['length', 'width', 'height']:
            if dim in data and data[dim] is not None:
                try:
                    dim_value = Decimal(str(data[dim]))
                    processed_data[dim] = dim_value
                except (InvalidOperation, TypeError, ValueError):
                    # 验证函数会处理这个错误，这里不重复处理
                    pass
        
        # 处理布尔值字段
        if 'is_residential' in data:
            if isinstance(data['is_residential'], str):
                processed_data['is_residential'] = data['is_residential'].lower() in ['true', 'yes', '1', 't', 'y']
            else:
                processed_data['is_residential'] = bool(data['is_residential'])
        
        return processed_data, warnings
    
    def _validate_postal_code(self, postal_code: str, field_name: str) -> None:
        """
        验证邮编格式
        
        Args:
            postal_code: 邮编
            field_name: 字段名称，用于错误消息
            
        Raises:
            ValidationException: 如果邮编格式无效
        """
        if not postal_code:
            raise ValidationException(f"{field_name}不能为空")
        
        if not isinstance(postal_code, str):
            raise ValidationException(f"{field_name}必须是字符串类型")
        
        # 简单的基本验证，可根据需要自定义规则
        if len(postal_code) < 3 or len(postal_code) > 12:
            raise ValidationException(f"{field_name}长度无效，应在3-12个字符之间")
        
        # 这里可以添加更多特定的邮编验证规则
    
    def _normalize_postal_code(self, postal_code: str) -> str:
        """
        标准化邮编格式
        
        Args:
            postal_code: 原始邮编
            
        Returns:
            str: 标准化后的邮编
        """
        if not postal_code or not isinstance(postal_code, str):
            return postal_code
        
        # 去除前后空格
        postal_code = postal_code.strip()
        
        # 将邮编转换为大写
        postal_code = postal_code.upper()
        
        # 去除特殊字符，如空格、连字符等
        postal_code = re.sub(r'[^A-Z0-9]', '', postal_code)
        
        return postal_code
    
    def validate_decimal(self, value, field_name: str, min_value: float = None, max_value: float = None) -> Decimal:
        """
        验证十进制数值
        
        Args:
            value: 要验证的值
            field_name: 字段名称，用于错误消息
            min_value: 最小值，默认为None
            max_value: 最大值，默认为None
            
        Returns:
            Decimal: 验证后的十进制值
            
        Raises:
            ValidationException: 如果值无效
        """
        try:
            decimal_value = Decimal(str(value))
            
            if min_value is not None and decimal_value < Decimal(str(min_value)):
                raise ValidationException(f"{field_name}不能小于{min_value}")
            
            if max_value is not None and decimal_value > Decimal(str(max_value)):
                raise ValidationException(f"{field_name}不能大于{max_value}")
            
            return decimal_value
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationException(f"{field_name}格式无效，应为有效的数值")
    
    def mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        掩码敏感数据
        
        Args:
            data: 原始数据
            
        Returns:
            Dict[str, Any]: 掩码后的数据
        """
        masked_data = data.copy()
        
        # 掩码邮编
        for field in ['from_postal', 'to_postal']:
            if field in masked_data and masked_data[field]:
                postal = str(masked_data[field])
                if len(postal) > 3:
                    masked_data[field] = postal[:2] + '*' * (len(postal) - 3) + postal[-1]
        
        # 这里可以添加其他敏感字段的掩码处理
        
        return masked_data 