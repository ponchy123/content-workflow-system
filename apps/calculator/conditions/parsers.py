import re
import sys
import logging
from decimal import Decimal
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class ConditionParser:
    """条件解析器"""

    def parse(self, condition_desc):
        """解析条件描述"""
        if not condition_desc:
            return None

        # 根据描述确定条件类型
        if self._is_length_girth_condition(condition_desc):
            return self.parse_length_girth_condition(condition_desc)
        elif self._is_length_condition(condition_desc):
            return self.parse_length_condition(condition_desc)
        elif self._is_weight_condition(condition_desc):
            return self.parse_weight_condition(condition_desc)
        elif self._is_residential_condition(condition_desc):
            return self.parse_residential_condition(condition_desc)
        elif self._is_remote_condition(condition_desc):
            return self.parse_remote_condition(condition_desc)
        elif self._is_date_condition(condition_desc):
            return self.parse_date_condition(condition_desc)
        
        # 尝试解析特殊条件
        special_condition = self.parse_special_condition(condition_desc)
        if special_condition:
            return special_condition
            
        # 尝试解析维度条件
        dimension_condition = self.parse_dimension_condition(condition_desc)
        if dimension_condition:
            return dimension_condition
            
        # 尝试解析日期范围条件
        date_range_condition = self.parse_date_range_condition(condition_desc)
        if date_range_condition:
            return date_range_condition

        return None

    def _is_length_girth_condition(self, condition_desc):
        """是否为长度+周长条件"""
        lower_desc = condition_desc.lower()
        return ('长+周长' in condition_desc or
                '长度+周长' in condition_desc or
                'length+girth' in lower_desc or
                'length +girth' in lower_desc or
                'length+ girth' in lower_desc)

    def _is_length_condition(self, condition_desc):
        """是否为长度条件"""
        lower_desc = condition_desc.lower()
        return ('最长边' in condition_desc or 
                'longest side' in lower_desc or
                ('长度' in condition_desc and not '周长' in condition_desc) or
                ('length' in lower_desc and not 'girth' in lower_desc))

    def _is_weight_condition(self, condition_desc):
        """是否为重量条件"""
        lower_desc = condition_desc.lower()
        return ('重量' in condition_desc or 
                'weight' in lower_desc or
                '磅' in condition_desc or
                '公斤' in condition_desc or
                'lb' in lower_desc or
                'kg' in lower_desc)

    def _is_residential_condition(self, condition_desc):
        """是否为住宅条件"""
        lower_desc = condition_desc.lower()
        return '住宅' in condition_desc or 'residential' in lower_desc

    def _is_remote_condition(self, condition_desc):
        """是否为偏远地区条件"""
        lower_desc = condition_desc.lower()
        return '偏远' in condition_desc or 'remote' in lower_desc

    def _is_date_condition(self, condition_desc):
        """是否为日期条件"""
        # 匹配常见日期格式
        date_patterns = [
            r'\d{4}-\d{1,2}-\d{1,2}',  # YYYY-MM-DD
            r'\d{1,2}/\d{1,2}/\d{4}',  # MM/DD/YYYY
            r'\d{1,2}月\d{1,2}日'       # 中文日期格式
        ]
        for pattern in date_patterns:
            if re.search(pattern, condition_desc):
                return True
        return False

    def parse_length_girth_condition(self, condition_desc):
        """解析长度+周长条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        # 提取所有数字
        numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
        if numbers:
            # 尝试智能判断条件逻辑
            params = {'text': condition_desc, 'values': [Decimal(n) for n in numbers]}
            
            # 根据条件描述中的关键词推断条件类型
            if any(op in condition_desc.lower() for op in ['>', '大于', 'greater', 'more', 'over', '超过']):
                if len(numbers) >= 1:
                    params['min'] = Decimal(numbers[0])
                    print(f"    推断为大于条件: 最小值 = {params['min']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['<', '小于', 'less', 'under', 'below', '低于']):
                if len(numbers) >= 1:
                    params['max'] = Decimal(numbers[0])
                    print(f"    推断为小于条件: 最大值 = {params['max']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['between', '介于', '在...之间']):
                if len(numbers) >= 2:
                    params['min'] = Decimal(numbers[0])
                    params['max'] = Decimal(numbers[1])
                    print(f"    推断为介于条件: {params['min']} 到 {params['max']}", file=sys.stdout)
            
            return Condition(ConditionType.LENGTH_GIRTH, params)
        
        return None

    def parse_weight_condition(self, condition_desc):
        """解析重量条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        # 提取所有数字
        numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
        if numbers:
            # 尝试智能判断条件逻辑
            params = {'text': condition_desc, 'values': [Decimal(n) for n in numbers]}
            
            # 根据条件描述中的关键词推断条件类型
            if any(op in condition_desc.lower() for op in ['>', '大于', 'greater', 'more', 'over', '超过']):
                if len(numbers) >= 1:
                    params['min'] = Decimal(numbers[0])
                    print(f"    推断为大于重量条件: 最小值 = {params['min']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['<', '小于', 'less', 'under', 'below', '低于']):
                if len(numbers) >= 1:
                    params['max'] = Decimal(numbers[0])
                    print(f"    推断为小于重量条件: 最大值 = {params['max']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['between', '介于', '在...之间']):
                if len(numbers) >= 2:
                    params['min'] = Decimal(numbers[0])
                    params['max'] = Decimal(numbers[1])
                    print(f"    推断为介于重量条件: {params['min']} 到 {params['max']}", file=sys.stdout)
            
            return Condition(ConditionType.WEIGHT, params)
        
        return None

    def parse_length_condition(self, condition_desc):
        """解析长度条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        # 提取所有数字
        numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
        if numbers:
            # 尝试智能判断条件逻辑
            params = {'text': condition_desc, 'values': [Decimal(n) for n in numbers]}
            
            # 根据条件描述中的关键词推断条件类型
            if any(op in condition_desc.lower() for op in ['>', '大于', 'greater', 'more', 'over', '超过']):
                if len(numbers) >= 1:
                    params['min'] = Decimal(numbers[0])
                    print(f"    推断为大于长度条件: 最小值 = {params['min']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['<', '小于', 'less', 'under', 'below', '低于']):
                if len(numbers) >= 1:
                    params['max'] = Decimal(numbers[0])
                    print(f"    推断为小于长度条件: 最大值 = {params['max']}", file=sys.stdout)
            elif any(op in condition_desc.lower() for op in ['between', '介于', '在...之间']):
                if len(numbers) >= 2:
                    params['min'] = Decimal(numbers[0])
                    params['max'] = Decimal(numbers[1])
                    print(f"    推断为介于长度条件: {params['min']} 到 {params['max']}", file=sys.stdout)
            
            return Condition(ConditionType.LENGTH, params)
        
        return None

    def parse_residential_condition(self, condition_desc):
        """解析住宅条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        params = {'text': condition_desc, 'is_residential': True}
        
        # 如果条件描述中明确说明"非住宅"，则修改参数
        if any(term in condition_desc.lower() for term in ['非住宅', '商业', 'commercial', 'non-residential']):
            params['is_residential'] = False
            print(f"    推断为商业地址条件", file=sys.stdout)
        else:
            print(f"    推断为住宅地址条件", file=sys.stdout)
            
        return Condition(ConditionType.RESIDENTIAL, params)

    def parse_remote_condition(self, condition_desc):
        """解析偏远地区条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        params = {'text': condition_desc}
        
        # 尝试从描述中提取偏远程度
        if 'extended' in condition_desc.lower() or '极偏远' in condition_desc:
            params['remote_level'] = 2
            print(f"    推断为极偏远地区条件", file=sys.stdout)
        else:
            params['remote_level'] = 1
            print(f"    推断为一般偏远地区条件", file=sys.stdout)
            
        return Condition(ConditionType.REMOTE, params)

    def parse_special_condition(self, condition_desc):
        """解析特殊条件(如服务类型、包装要求等)"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        lower_desc = condition_desc.lower()
        
        # 特殊条件类型识别
        if 'fedex home delivery' in lower_desc:
            print(f"    推断为FedEx Home Delivery服务类型条件", file=sys.stdout)
            return Condition(ConditionType.RESIDENTIAL, {'is_residential': True, 'text': condition_desc})
        
        if 'signature' in lower_desc or '签名' in condition_desc:
            print(f"    推断为签名服务条件", file=sys.stdout)
            return Condition(ConditionType.UNKNOWN, {'text': condition_desc, 'special_type': 'signature'})
        
        if '修改地址' in condition_desc or 'address correction' in lower_desc:
            print(f"    推断为地址修改条件", file=sys.stdout)
            return Condition(ConditionType.UNKNOWN, {'text': condition_desc, 'special_type': 'address_correction'})
        
        # 检查第二长边条件
        if '第二长边' in condition_desc or 'second longest' in lower_desc:
            numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
            if numbers and any(op in condition_desc for op in ['>', '<', '=', '>=', '<=']):
                print(f"    推断为第二长边条件", file=sys.stdout)
                params = {'text': condition_desc, 'dimension_type': 'second_longest'}
                
                if '>' in condition_desc:
                    params['min'] = Decimal(numbers[0])
                elif '<' in condition_desc:
                    params['max'] = Decimal(numbers[0])
                    
                return Condition(ConditionType.LENGTH, params)
        
        return None
    
    def parse_dimension_condition(self, condition_desc):
        """解析尺寸条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        # 检查是否是尺寸相关条件
        if ('尺寸' in condition_desc or 
            'dimension' in condition_desc.lower() or 
            '体积' in condition_desc or 
            'volume' in condition_desc.lower()):
            
            # 提取所有数字
            numbers = re.findall(r'(\d+(?:\.\d+)?)', condition_desc)
            if numbers:
                # 尝试智能判断条件逻辑
                params = {'text': condition_desc, 'values': [Decimal(n) for n in numbers]}
                
                # 检查是否是体积重量条件
                if '体积重' in condition_desc or 'volumetric weight' in condition_desc.lower():
                    print(f"    推断为体积重量条件", file=sys.stdout)
                    # 根据条件描述中的关键词推断条件类型
                    if any(op in condition_desc.lower() for op in ['>', '大于', 'greater', 'more', 'over', '超过']):
                        if len(numbers) >= 1:
                            params['min'] = Decimal(numbers[0])
                    elif any(op in condition_desc.lower() for op in ['<', '小于', 'less', 'under', 'below', '低于']):
                        if len(numbers) >= 1:
                            params['max'] = Decimal(numbers[0])
                    
                    return Condition(ConditionType.WEIGHT, params)  # 使用重量条件类型处理体积重量
                
                # 默认返回未知类型的条件
                print(f"    推断为一般尺寸条件", file=sys.stdout)
                return Condition(ConditionType.UNKNOWN, params)
        
        return None
        
    def parse_date_range_condition(self, condition_desc):
        """解析日期范围条件"""
        from apps.calculator.conditions.condition_types import ConditionType, Condition
        
        # 检查日期范围模式
        date_range_pattern = r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})\s*(?:到|至|to|-)\s*(\d{4}[-/]\d{1,2}[-/]\d{1,2})'
        date_match = re.search(date_range_pattern, condition_desc)
        
        if date_match:
            start_date_str = date_match.group(1)
            end_date_str = date_match.group(2)
            
            # 尝试解析日期
            try:
                # 根据日期格式解析
                if '-' in start_date_str:
                    start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                else:
                    start_date = datetime.strptime(start_date_str, '%Y/%m/%d').date()
                    
                if '-' in end_date_str:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                else:
                    end_date = datetime.strptime(end_date_str, '%Y/%m/%d').date()
                    
                print(f"    推断为日期范围条件: {start_date} 到 {end_date}", file=sys.stdout)
                
                # 创建条件参数
                params = {
                    'text': condition_desc,
                    'start_date': start_date,
                    'end_date': end_date
                }
                
                return Condition(ConditionType.UNKNOWN, params)
            except Exception as e:
                print(f"    日期解析异常: {str(e)}", file=sys.stdout)
        
        return None

    # 其他解析方法根据需要按照类似方式实现 