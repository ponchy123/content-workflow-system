"""
基础费率数据传输对象(DTO)
负责处理前端到后端以及后端到前端的数据格式转换
"""

import logging
import re
from decimal import Decimal
from typing import Dict, Any, List, Optional, Union

logger = logging.getLogger(__name__)

class BaseFeeInputDTO:
    """
    基础费率输入DTO - 处理从前端到后端的数据转换
    将前端的Zone1,Zone2等格式转换为后端的zone_prices标准格式
    """
    
    @staticmethod
    def transform(data: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
        """
        将前端发送的基础费率数据转换为后端标准格式
        
        Args:
            data: 前端提交的数据
            request_id: 请求ID，用于日志追踪
            
        Returns:
            转换后的标准格式数据
        """
        result = data.copy()
        
        # 初始化zone_prices字典
        if 'zone_prices' not in result or not isinstance(result.get('zone_prices'), dict):
            result['zone_prices'] = {}
            
        # 初始化zone_unit_prices字典
        if 'zone_unit_prices' not in result or not isinstance(result.get('zone_unit_prices'), dict):
            result['zone_unit_prices'] = {}
            
        # 处理Zone格式的价格字段
        for key, value in list(data.items()):
            # 匹配Zone+数字模式，但排除包含"单位"或"UnitPrice"的键
            if re.match(r'^Zone\d+$', key) and not ('单位' in key or 'UnitPrice' in key):
                try:
                    # 提取区域编号
                    zone_num = key.replace('Zone', '')
                    zone_key = f'zone{zone_num}'
                    
                    # 转换为数值并保存到zone_prices
                    if value is not None:
                        numeric_value = float(value)
                        result['zone_prices'][zone_key] = numeric_value
                        
                        # 记录日志
                        if request_id:
                            logger.debug(f"[请求ID:{request_id}] 从{key}提取价格 {zone_key}={numeric_value}")
                except (ValueError, TypeError) as e:
                    if request_id:
                        logger.warning(f"[请求ID:{request_id}] 无法转换{key}值为数值，值={value}, 错误: {str(e)}")
            
            # 处理单位价格字段 (例如: Zone1UnitPrice 或 Zone1单位重量价格)
            elif (re.match(r'^Zone\d+UnitPrice$', key) or 
                  (key.startswith('Zone') and ('单位重量价格' in key or '单位重量价 格' in key))):
                try:
                    # 提取区域编号
                    zone_num = re.search(r'Zone(\d+)', key).group(1)
                    zone_key = f'zone{zone_num}'
                    
                    # 转换为数值并保存到zone_unit_prices
                    if value is not None:
                        numeric_value = float(value)
                        result['zone_unit_prices'][zone_key] = numeric_value
                        
                        # 记录日志
                        if request_id:
                            logger.debug(f"[请求ID:{request_id}] 从{key}提取单位价格 {zone_key}={numeric_value}")
                except (ValueError, TypeError, AttributeError) as e:
                    if request_id:
                        logger.warning(f"[请求ID:{request_id}] 无法转换{key}单位价格值为数值，值={value}, 错误: {str(e)}")
        
        # 确保weight字段是数值类型
        if 'weight' in result:
            try:
                result['weight'] = float(result['weight'])
            except (ValueError, TypeError):
                if request_id:
                    logger.warning(f"[请求ID:{request_id}] 无效的重量值 {result.get('weight')}")
                result['weight'] = 0.0
                
        return result
    
    @staticmethod
    def transform_list(data_list: List[Dict[str, Any]], request_id: str = None) -> List[Dict[str, Any]]:
        """
        批量转换基础费率数据列表
        
        Args:
            data_list: 前端提交的数据列表
            request_id: 请求ID，用于日志追踪
            
        Returns:
            转换后的标准格式数据列表
        """
        return [
            BaseFeeInputDTO.transform(item, request_id) 
            for item in data_list
        ]


class BaseFeeOutputDTO:
    """
    基础费率输出DTO - 处理从后端到前端的数据转换
    将后端的zone_prices标准格式转换为前端期望的Zone1,Zone2等格式
    """
    
    @staticmethod
    def transform(data: Dict[str, Any], request_id: str = None) -> Dict[str, Any]:
        """
        将后端标准格式的基础费率数据转换为前端期望格式
        
        Args:
            data: 后端数据
            request_id: 请求ID，用于日志追踪
            
        Returns:
            转换后的前端格式数据
        """
        result = data.copy()
        
        # 处理zone_prices字段
        zone_prices = result.get('zone_prices', {})
        if zone_prices and isinstance(zone_prices, dict):
            for zone_key, price in zone_prices.items():
                if zone_key.startswith('zone'):
                    zone_num = zone_key.replace('zone', '')
                    try:
                        result[f'Zone{zone_num}'] = float(price)
                    except (TypeError, ValueError):
                        result[f'Zone{zone_num}'] = 0.0
        
        # 处理zone_unit_prices字段
        zone_unit_prices = result.get('zone_unit_prices', {})
        if zone_unit_prices and isinstance(zone_unit_prices, dict):
            for zone_key, price in zone_unit_prices.items():
                if zone_key.startswith('zone'):
                    zone_num = zone_key.replace('zone', '')
                    try:
                        result[f'Zone{zone_num}UnitPrice'] = float(price)
                    except (TypeError, ValueError):
                        result[f'Zone{zone_num}UnitPrice'] = 0.0
        
        return result
    
    @staticmethod
    def transform_list(data_list: List[Dict[str, Any]], request_id: str = None) -> List[Dict[str, Any]]:
        """
        批量转换基础费率数据列表
        
        Args:
            data_list: 后端数据列表
            request_id: 请求ID，用于日志追踪
            
        Returns:
            转换后的前端格式数据列表
        """
        return [
            BaseFeeOutputDTO.transform(item, request_id) 
            for item in data_list
        ] 