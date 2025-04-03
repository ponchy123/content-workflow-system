import re
import sys
import math
from decimal import Decimal
from datetime import datetime
from typing import Dict, Any, Optional

class ConditionType:
    """条件类型常量"""
    WEIGHT = 'WEIGHT'           # 重量条件
    LENGTH = 'LENGTH'           # 长度条件
    LENGTH_GIRTH = 'LENGTH_GIRTH'  # 长度+周长条件
    RESIDENTIAL = 'RESIDENTIAL'  # 住宅地址条件
    REMOTE = 'REMOTE'           # 偏远地区条件
    COMPOUND = 'COMPOUND'       # 复合条件
    UNKNOWN = 'UNKNOWN'         # 未知条件

class Condition:
    """条件类，用于评估条件是否满足"""
    
    def __init__(self, condition_type, params=None):
        self.type = condition_type
        self.params = params or {}
        
    def evaluate(self, data):
        """评估条件是否满足"""
        try:
            # 根据条件类型调用相应的评估方法
            if self.type == ConditionType.WEIGHT:
                return self._evaluate_weight_condition(data.get('weight', 0))
            elif self.type == ConditionType.LENGTH:
                return self._evaluate_length_condition(data.get('length', 0))
            elif self.type == ConditionType.LENGTH_GIRTH:
                # 计算周长
                width = data.get('width', 0)
                height = data.get('height', 0)
                length = data.get('length', 0)
                girth = 2 * (width + height)
                total_length = length + girth
                return self._evaluate_length_girth_condition(total_length)
            elif self.type == ConditionType.RESIDENTIAL:
                return self._evaluate_residential_condition(data.get('is_residential', False))
            elif self.type == ConditionType.REMOTE:
                return self._evaluate_remote_condition(data.get('remote_level', 0))
            elif self.type == ConditionType.COMPOUND:
                # 复合条件需要额外参数
                return self._evaluate_compound_condition(
                    data.get('weight', 0),
                    data.get('length', 0),
                    data.get('width', 0),
                    data.get('height', 0),
                    data.get('length', 0) + 2 * (data.get('width', 0) + data.get('height', 0)),
                    data.get('is_residential', False),
                    data.get('remote_level', 0)
                )
            else:
                # 通用条件评估
                return self._evaluate_generic_condition(data)
        except Exception as e:
            print(f"    条件评估异常: {str(e)}", file=sys.stdout)
            return False
            
    def _evaluate_weight_condition(self, weight):
        """评估重量条件"""
        try:
            # 确保weight是Decimal类型
            if not isinstance(weight, Decimal):
                weight = Decimal(str(weight))
                
            if 'min' in self.params and 'max' in self.params:
                min_value = self.params['min']
                max_value = self.params['max']
                min_inclusive = self.params.get('min_inclusive', False)
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if min_inclusive and max_inclusive:
                    result = min_value <= weight <= max_value
                    print(f"    检查条件: {min_value}磅 <= 实际重量({weight}) <= {max_value}磅, 结果={result}", file=sys.stdout)
                elif min_inclusive and not max_inclusive:
                    result = min_value <= weight < max_value
                    print(f"    检查条件: {min_value}磅 <= 实际重量({weight}) < {max_value}磅, 结果={result}", file=sys.stdout)
                elif not min_inclusive and max_inclusive:
                    result = min_value < weight <= max_value
                    print(f"    检查条件: {min_value}磅 < 实际重量({weight}) <= {max_value}磅, 结果={result}", file=sys.stdout)
                else:
                    result = min_value < weight < max_value
                    print(f"    检查条件: {min_value}磅 < 实际重量({weight}) < {max_value}磅, 结果={result}", file=sys.stdout)
                return result

            elif 'min' in self.params:
                min_value = self.params['min']
                min_inclusive = self.params.get('min_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))

                if min_inclusive:
                    result = weight >= min_value
                    print(f"    检查条件: 实际重量({weight}) >= {min_value}磅, 结果={result}", file=sys.stdout)
                else:
                    result = weight > min_value
                    print(f"    检查条件: 实际重量({weight}) > {min_value}磅, 结果={result}", file=sys.stdout)
                return result

            elif 'max' in self.params:
                max_value = self.params['max']
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if max_inclusive:
                    result = weight <= max_value
                    print(f"    检查条件: 实际重量({weight}) <= {max_value}磅, 结果={result}", file=sys.stdout)
                else:
                    result = weight < max_value
                    print(f"    检查条件: 实际重量({weight}) < {max_value}磅, 结果={result}", file=sys.stdout)
                return result

            return False
        except Exception as e:
            print(f"    重量条件评估异常: {str(e)}", file=sys.stdout)
            return False
    
    def _evaluate_length_girth_condition(self, total_length):
        """评估长度+周长条件"""
        try:
            # 确保total_length是Decimal类型
            if not isinstance(total_length, Decimal):
                total_length = Decimal(str(total_length))
                
            if 'min' in self.params and 'max' in self.params:
                min_value = self.params['min']
                max_value = self.params['max']
                min_inclusive = self.params.get('min_inclusive', False)
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if min_inclusive and max_inclusive:
                    result = min_value <= total_length <= max_value
                    print(f"    检查条件: {min_value}英寸 <= 长+周长({total_length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                elif min_inclusive and not max_inclusive:
                    result = min_value <= total_length < max_value
                    print(f"    检查条件: {min_value}英寸 <= 长+周长({total_length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                elif not min_inclusive and max_inclusive:
                    result = min_value < total_length <= max_value
                    print(f"    检查条件: {min_value}英寸 < 长+周长({total_length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = min_value < total_length < max_value
                    print(f"    检查条件: {min_value}英寸 < 长+周长({total_length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                return result

            elif 'min' in self.params:
                min_value = self.params['min']
                min_inclusive = self.params.get('min_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))

                if min_inclusive:
                    result = total_length >= min_value
                    print(f"    检查条件: 长+周长({total_length}) >= {min_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = total_length > min_value
                    print(f"    检查条件: 长+周长({total_length}) > {min_value}英寸, 结果={result}", file=sys.stdout)
                return result

            elif 'max' in self.params:
                max_value = self.params['max']
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if max_inclusive:
                    result = total_length <= max_value
                    print(f"    检查条件: 长+周长({total_length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = total_length < max_value
                    print(f"    检查条件: 长+周长({total_length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                return result

            return False
        except Exception as e:
            print(f"    长度+周长条件评估异常: {str(e)}", file=sys.stdout)
            return False
            
    def _evaluate_length_condition(self, length):
        """评估长度条件"""
        try:
            # 确保length是Decimal类型
            if not isinstance(length, Decimal):
                length = Decimal(str(length))
                
            # 检查是否是第二长边条件
            if self.params.get('dimension_type') == 'second_longest':
                print(f"    评估第二长边条件，但当前实现只检查最长边，结果=False", file=sys.stdout)
                return False
                
            if 'min' in self.params and 'max' in self.params:
                min_value = self.params['min']
                max_value = self.params['max']
                min_inclusive = self.params.get('min_inclusive', False)
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if min_inclusive and max_inclusive:
                    result = min_value <= length <= max_value
                    print(f"    检查条件: {min_value}英寸 <= 最长边({length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                elif min_inclusive and not max_inclusive:
                    result = min_value <= length < max_value
                    print(f"    检查条件: {min_value}英寸 <= 最长边({length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                elif not min_inclusive and max_inclusive:
                    result = min_value < length <= max_value
                    print(f"    检查条件: {min_value}英寸 < 最长边({length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = min_value < length < max_value
                    print(f"    检查条件: {min_value}英寸 < 最长边({length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                return result

            elif 'min' in self.params:
                min_value = self.params['min']
                min_inclusive = self.params.get('min_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(min_value, Decimal):
                    min_value = Decimal(str(min_value))

                if min_inclusive:
                    result = length >= min_value
                    print(f"    检查条件: 最长边({length}) >= {min_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = length > min_value
                    print(f"    检查条件: 最长边({length}) > {min_value}英寸, 结果={result}", file=sys.stdout)
                return result

            elif 'max' in self.params:
                max_value = self.params['max']
                max_inclusive = self.params.get('max_inclusive', False)
                
                # 确保值是Decimal类型
                if not isinstance(max_value, Decimal):
                    max_value = Decimal(str(max_value))

                if max_inclusive:
                    result = length <= max_value
                    print(f"    检查条件: 最长边({length}) <= {max_value}英寸, 结果={result}", file=sys.stdout)
                else:
                    result = length < max_value
                    print(f"    检查条件: 最长边({length}) < {max_value}英寸, 结果={result}", file=sys.stdout)
                return result

            return False
        except Exception as e:
            print(f"    长度条件评估异常: {str(e)}", file=sys.stdout)
            return False
            
    def _evaluate_residential_condition(self, is_residential):
        """评估住宅条件"""
        try:
            # 获取条件中要求的住宅状态
            expected_is_residential = self.params.get('is_residential', True)
            
            # 比较条件与实际值
            result = is_residential == expected_is_residential
            
            if expected_is_residential:
                print(f"    检查条件: 是否为住宅地址({is_residential})==需要住宅地址, 结果={result}", file=sys.stdout)
            else:
                print(f"    检查条件: 是否为住宅地址({is_residential})==需要非住宅地址, 结果={result}", file=sys.stdout)
                
            return result
        except Exception as e:
            print(f"    住宅条件评估异常: {str(e)}", file=sys.stdout)
            return False

    def _evaluate_remote_condition(self, remote_level):
        """评估偏远地区条件"""
        try:
            # 获取条件中要求的偏远等级
            expected_remote_level = self.params.get('remote_level', 1)
            
            # 比较条件与实际值
            result = remote_level >= expected_remote_level
            
            print(f"    检查条件: 偏远等级({remote_level})>={expected_remote_level}, 结果={result}", file=sys.stdout)
            return result
        except Exception as e:
            print(f"    偏远条件评估异常: {str(e)}", file=sys.stdout)
            return False
            
    def _evaluate_generic_condition(self, data):
        """评估通用/未知条件"""
        # 对于特殊条件，直接输出信息并返回默认值
        special_type = self.params.get('special_type')
        if special_type:
            print(f"    特殊条件类型: {special_type}, 无法自动评估, 默认返回False", file=sys.stdout)
        else:
            print(f"    未知条件类型: {self.type}, 无法评估, 默认返回False", file=sys.stdout)
        return False

    # 其他评估方法可以继续添加 