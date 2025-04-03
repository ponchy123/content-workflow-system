import re
import sys
import math
import logging
from decimal import Decimal
from typing import Dict, Any, List

from apps.calculator.conditions.parsers import ConditionParser
from apps.calculator.conditions.config_loader import ConditionConfigLoader
from apps.core.config import get_setting

logger = logging.getLogger(__name__)

class ConditionChecker:
    """条件检查器，用于检查各种条件是否满足"""
    
    def __init__(self):
        """初始化条件检查器"""
        # 加载条件配置
        self.condition_config = ConditionConfigLoader.load_config()
        self.parser = ConditionParser()
    
    def check_condition(self, condition_desc, data):
        """检查条件是否满足"""
        if not condition_desc:
            print(f"    无条件描述，默认满足", file=sys.stdout)
            return True
        
        try:
            # 获取原始数据
            weight = Decimal(str(data.get('weight', '0')))
            length = Decimal(str(data.get('length', '0')))
            width = Decimal(str(data.get('width', '0')))
            height = Decimal(str(data.get('height', '0')))
            weight_unit = data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')
            dimension_unit = data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT')
            is_residential = data.get('is_residential', False)
            remote_level = data.get('remote_level', 0)
            calculation_date = data.get('calculation_date')
            product_id = data.get('product_id')
            
            # 单位转换为条件判断所需的单位（磅和英寸）并向上取整
            if weight_unit == 'KG':
                # 使用float转换避免Decimal与float操作的问题
                weight_float = float(weight) * 2.20462
                weight = Decimal(str(math.ceil(weight_float)))
                print(f"    重量转换: {data.get('weight')}KG -> {weight}LB (向上取整)", file=sys.stdout)
            elif weight_unit == 'OZ':
                weight_float = float(weight) / 16
                weight = Decimal(str(math.ceil(weight_float)))
                print(f"    重量转换: {data.get('weight')}OZ -> {weight}LB (向上取整)", file=sys.stdout)
            
            if dimension_unit == 'CM':
                # 使用float转换避免Decimal与float操作的问题
                length_float = float(length) / 2.54
                width_float = float(width) / 2.54
                height_float = float(height) / 2.54
                
                length = Decimal(str(math.ceil(length_float)))
                width = Decimal(str(math.ceil(width_float)))
                height = Decimal(str(math.ceil(height_float)))
                print(f"    尺寸转换: {data.get('length')}x{data.get('width')}x{data.get('height')}CM -> ", file=sys.stdout)
                print(f"              {length}x{width}x{height}IN (向上取整)", file=sys.stdout)
            
            # 计算辅助值
            girth = 2 * (width + height)
            total_length = length + girth
            
            print(f"\n    条件描述: {condition_desc}", file=sys.stdout)
            print(f"    原始参数: 重量={data.get('weight')} {weight_unit}, 尺寸={data.get('length')}x{data.get('width')}x{data.get('height')} {dimension_unit}", file=sys.stdout)
            print(f"    转换参数: 重量={weight}LB, 尺寸={length}x{width}x{height}IN", file=sys.stdout)
            print(f"    计算值: 周长={girth}IN, 总长度(长+周长)={total_length}IN", file=sys.stdout)
            print(f"    其他参数: 住宅地址={is_residential}, 偏远等级={remote_level}", file=sys.stdout)
            
            # 1. 从配置文件中读取条件规则
            if '不可发包裹' in condition_desc or 'Unauthorized' in condition_desc.lower():
                # 检查是否为不可发包裹条件
                unauthorized_conditions = ConditionConfigLoader.get_unauthorized_conditions(self.condition_config)
                result = self._check_unauthorized_conditions(
                    unauthorized_conditions, weight, length, width, height, total_length)
                if result:
                    return True
            
            # 2. 获取产品特定条件
            if product_id:
                product_conditions = ConditionConfigLoader.get_product_conditions(
                    self.condition_config, product_id)
                if product_conditions:
                    result = self._check_product_conditions(
                        product_conditions, weight, length, width, height, total_length)
                    if result:
                        return True
            
            # 3. 使用条件解析器处理
            condition = self.parser.parse(condition_desc)
            
            # 评估条件
            if condition:
                try:
                    result = condition.evaluate({
                        'weight': weight,
                        'length': length,
                        'width': width,
                        'height': height,
                        'is_residential': is_residential,
                        'remote_level': remote_level,
                        'calculation_date': calculation_date,
                        'weight_unit': 'LB',  # 已转换为磅
                        'dimension_unit': 'IN'  # 已转换为英寸
                    })
                    print(f"    条件判断结果: {result}", file=sys.stdout)
                    return result
                except Exception as eval_error:
                    print(f"    条件评估异常: {str(eval_error)}", file=sys.stdout)
                    # 备用处理：从条件描述中尝试提取关键信息
                    return self._fallback_check(condition_desc, weight, length, total_length)
            else:
                print(f"    无法解析条件，尝试备用检查", file=sys.stdout)
                return self._fallback_check(condition_desc, weight, length, total_length)
                
        except Exception as e:
            print(f"    条件检查异常: {str(e)}", file=sys.stdout)
            # 记录异常堆栈
            import traceback
            traceback.print_exc(file=sys.stdout)
            return False
    
    def _check_unauthorized_conditions(self, conditions, weight, length, width, height, total_length):
        """检查不可发包裹条件"""
        for rule in conditions:
            condition_type = rule.get('type')
            operator = rule.get('operator')
            threshold = rule.get('value')
            
            if not all([condition_type, operator, threshold]):
                continue
                
            try:
                threshold_dec = Decimal(str(threshold))
                
                # 长度+周长条件
                if condition_type == 'LENGTH_GIRTH' and operator == '>':
                    if total_length > threshold_dec:
                        print(f"    配置规则匹配: 长+周长({total_length}) > {threshold_dec}英寸", file=sys.stdout)
                        return True
                        
                # 最长边条件
                elif condition_type == 'LENGTH' and operator == '>':
                    if length > threshold_dec:
                        print(f"    配置规则匹配: 最长边({length}) > {threshold_dec}英寸", file=sys.stdout)
                        return True
                        
                # 重量条件
                elif condition_type == 'WEIGHT' and operator == '>':
                    if weight > threshold_dec:
                        print(f"    配置规则匹配: 重量({weight}) > {threshold_dec}磅", file=sys.stdout)
                        return True
            except Exception as rule_error:
                print(f"    规则评估异常: {str(rule_error)}, 规则: {rule}", file=sys.stdout)
        
        return False
    
    def _check_product_conditions(self, conditions, weight, length, width, height, total_length):
        """检查产品特定条件"""
        # 与_check_unauthorized_conditions类似，但针对产品特定条件
        return self._check_unauthorized_conditions(conditions, weight, length, width, height, total_length)
    
    def _fallback_check(self, condition_desc, weight, length, total_length):
        """备用条件检查逻辑"""
        condition_text = condition_desc.lower()
        
        # 从配置中获取默认阈值
        default_thresholds = self.condition_config.get('thresholds', {})
        length_girth_threshold = Decimal(str(default_thresholds.get('length_girth', '165')))
        length_threshold = Decimal(str(default_thresholds.get('length', '108'))) 
        weight_threshold = Decimal(str(default_thresholds.get('weight', '150')))
        
        # 检查长+周长条件
        if ('长+周长' in condition_desc or '长度+周长' in condition_desc or 'length+girth' in condition_text):
            if '>' in condition_desc:
                numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
                threshold = Decimal(numbers[0]) if numbers else length_girth_threshold
                result = total_length > threshold
                print(f"    备用判断: 长+周长({total_length}) > {threshold}英寸, 结果={result}", file=sys.stdout)
                return result
        
        # 检查最长边条件
        if ('最长边' in condition_desc or 'longest side' in condition_text):
            if '>' in condition_desc:
                numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
                threshold = Decimal(numbers[0]) if numbers else length_threshold
                result = length > threshold
                print(f"    备用判断: 最长边({length}) > {threshold}英寸, 结果={result}", file=sys.stdout)
                return result
        
        # 检查重量条件
        if ('重量' in condition_desc or 'weight' in condition_text):
            if '>' in condition_desc:
                numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
                threshold = Decimal(numbers[0]) if numbers else weight_threshold
                result = weight > threshold
                print(f"    备用判断: 重量({weight}) > {threshold}磅, 结果={result}", file=sys.stdout)
                return result
        
        return False 