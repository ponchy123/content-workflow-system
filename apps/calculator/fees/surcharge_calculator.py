"""
附加费计算模块
负责处理各种附加费的计算和应用
"""
from decimal import Decimal
from typing import Dict, Any, List
import logging

import sys
from django.utils import timezone
from django.conf import settings

from apps.calculator.conditions.checker import ConditionChecker
from apps.products.models import Product, Surcharge, PeakSeasonSurcharge

logger = logging.getLogger(__name__)

class SurchargeCalculator:
    """附加费计算器，负责计算各种附加费"""
    
    def __init__(self):
        self.condition_checker = ConditionChecker()
        self.logger = logging.getLogger(__name__)
    
    def calculate_surcharges(self, product: Product, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        计算附加费

        优化逻辑说明：
        1. 同一附加费类型的多个子类型，只计算金额最大的一个
           例如：如果有多个长度相关的'OVERSIZE_SURCHARGE'，只计算金额最大的那个
        2. 对于不同附加费类型，如果它们基于相同维度（如都是长度相关），也只计算金额最大的一个
           例如：如果有长度相关的'OVERSIZE_SURCHARGE'和'UNAUTHORIZED_PACKAGE'，只计算金额最大的那个
        3. 特殊类型'OVERSIZE_SURCHARGE'和'UNAUTHORIZED_PACKAGE'可以同时应用多个不同的子类型
        4. 按照维度类型分类：
           - LENGTH: 长度相关
           - WIDTH: 宽度相关
           - HEIGHT: 高度相关
           - WEIGHT: 重量相关
           - LENGTH_GIRTH: 长度+周长相关
           - RESIDENTIAL: 住宅地址相关
           - REMOTE: 偏远地区相关

        Args:
            product: 产品对象
            data: {
                'weight': 重量,
                'length': 长,
                'width': 宽,
                'height': 高,
                'is_residential': 是否住宅地址,
                'remote_level': 偏远等级,
                'zone': 区域,
                'calculation_date': 计算日期(可选)
            }
        Returns:
            list: 附加费列表，每项包含type, name, amount, condition
        """
        surcharges = []
        applied_types = {}  # 用于跟踪已应用的附加费类型
        dimension_related_surcharges = {}  # 用于跟踪基于维度的附加费

        print(f"\n========== 开始计算附加费 ==========", file=sys.stdout)
        print(f"输入数据摘要:", file=sys.stdout)
        print(f"  产品: {product.product_id} ({product.product_name})", file=sys.stdout)
        print(f"  重量: {data.get('weight', 0)}, 计费重量: {data.get('chargeable_weight', 0)}", file=sys.stdout)
        print(f"  尺寸: {data.get('length', 0)}x{data.get('width', 0)}x{data.get('height', 0)}", file=sys.stdout)
        print(f"  区域: {data.get('zone', '')}", file=sys.stdout)
        print(f"  偏远等级: {data.get('remote_level', '无')}", file=sys.stdout)
        print(f"  住宅地址: {data.get('is_residential', False)}", file=sys.stdout)

        # 获取所有可能的附加费
        all_surcharges = Surcharge.objects.filter(product=product, is_deleted=False)

        print(f"\n找到 {all_surcharges.count()} 个潜在附加费", file=sys.stdout)

        # 先处理旺季附加费
        peak_surcharges = self._calculate_peak_surcharges(product, data)
        if peak_surcharges:
            surcharges.extend(peak_surcharges)

        # 收集所有满足条件的附加费
        temp_surcharges = []
        print("\n========== 常规附加费 ==========", file=sys.stdout)
        for surcharge in all_surcharges:
            print(f"\n检查附加费: {surcharge.surcharge_type}", file=sys.stdout)
            print(f"  子类型: {surcharge.sub_type or '无'}", file=sys.stdout)
            print(f"  条件描述: {surcharge.condition_desc or '无条件'}", file=sys.stdout)
            if hasattr(surcharge, 'zone_fees') and surcharge.zone_fees:
                print(f"  区域费用: {surcharge.zone_fees}", file=sys.stdout)

            # 跳过后期产生的附加费类型
            if surcharge.surcharge_type in ['ADDRESS_CORRECTION', 'SIGNATURE_REQUIRED',
                                          'SHIPPING_CHARGE_CORRECTION', 'WEIGHT_DIMENSION_MISMATCH']:
                print(f"  跳过后期产生的附加费类型", file=sys.stdout)
                continue

            # 检查条件是否满足
            print(f"  开始检查条件是否满足...", file=sys.stdout)
            is_condition_met = self.condition_checker.check_condition(surcharge.condition_desc, data)
            print(f"  条件检查结果: {is_condition_met}", file=sys.stdout)

            if is_condition_met:
                # 获取对应zone的费用
                zone_key = f"zone{data['zone'].replace('ZONE', '')}"
                print(f"  获取区域 {zone_key} 费用...", file=sys.stdout)

                amount = Decimal(str(surcharge.zone_fees.get(zone_key, '0')))
                print(f"  区域费用: {amount}", file=sys.stdout)

                if amount > 0:
                    # 创建附加费项
                    surcharge_item = {
                        'type': self._get_surcharge_type_display(surcharge.surcharge_type),
                        'name': surcharge.sub_type or surcharge.surcharge_type,
                        'amount': str(amount),
                        'condition': surcharge.condition_desc,
                        'surcharge_type': surcharge.surcharge_type,  # 添加原始类型，用于后续处理
                        # 获取维度类型
                        'dimension_type': self._get_dimension_type(surcharge.condition_desc)
                    }
                    temp_surcharges.append(surcharge_item)
                    print(f"  添加到临时附加费列表，维度类型：{surcharge_item['dimension_type']}", file=sys.stdout)
                else:
                    print(f"  区域费用为0，不添加此附加费", file=sys.stdout)
            else:
                print(f"  条件不满足，跳过此附加费", file=sys.stdout)

        # 对临时附加费列表进行处理
        # 1. 按类型分组，每组只取最大值
        type_groups = {}
        dimension_groups = {}

        for item in temp_surcharges:
            s_type = item['surcharge_type']
            dim_type = item['dimension_type']
            amount = Decimal(item['amount'])

            # 按附加费类型分组
            if s_type not in type_groups:
                type_groups[s_type] = []
            type_groups[s_type].append(item)

            # 按维度类型分组
            if dim_type and dim_type != 'NONE':
                if dim_type not in dimension_groups:
                    dimension_groups[dim_type] = []
                dimension_groups[dim_type].append(item)

        # 对于每种附加费类型，只保留金额最大的
        selected_surcharges = []
        for s_type, items in type_groups.items():
            # 只有UNAUTHORIZED_PACKAGE可以有多个，其他类型包括OVERSIZE_SURCHARGE都只取最大的一项
            if s_type == 'UNAUTHORIZED_PACKAGE':
                selected_surcharges.extend(items)
            else:
                # 取金额最大的一项
                max_item = max(items, key=lambda x: Decimal(x['amount']))
                selected_surcharges.append(max_item)
                print(f"  选择了附加费类型 {s_type} 中金额最大的: {max_item['name']}, 金额: {max_item['amount']}", file=sys.stdout)

        # 对于相同维度的不同附加费类型，也只保留金额最大的
        selected_by_dimension = {
            'WEIGHT': {'amount': Decimal('0'), 'name': None, 'type': None, 'subtype': None},
            'LENGTH': {'amount': Decimal('0'), 'name': None, 'type': None, 'subtype': None},
            'LENGTH_GIRTH': {'amount': Decimal('0'), 'name': None, 'type': None, 'subtype': None}
        }
        
        # 循环处理每个符合条件的附加费
        for surcharge in selected_surcharges:
            amount = Decimal(str(surcharge['amount']))
            
            # 根据附加费类型分组
            surcharge_type = surcharge['type']
            dimension_type = surcharge['dimension_type']
            
            # 按附加费类型选择最大值
            if surcharge_type not in selected_by_dimension:
                selected_by_dimension[surcharge_type] = {
                    'amount': amount,
                    'name': surcharge['name'],
                    'type': surcharge_type,
                    'subtype': surcharge['name']
                }
            elif amount > selected_by_dimension[surcharge_type]['amount']:
                selected_by_dimension[surcharge_type] = {
                    'amount': amount,
                    'name': surcharge['name'],
                    'type': surcharge_type,
                    'subtype': surcharge['name']
                }
            
            # 按维度类型选择最大值
            if dimension_type not in selected_by_dimension:
                # 如果维度类型不在字典中，添加它
                selected_by_dimension[dimension_type] = {
                    'amount': amount,
                    'name': surcharge['name'],
                    'type': surcharge_type,
                    'subtype': surcharge['name']
                }
            elif amount > selected_by_dimension[dimension_type]['amount']:
                selected_by_dimension[dimension_type] = {
                    'amount': amount,
                    'name': surcharge['name'],
                    'type': surcharge_type,
                    'subtype': surcharge['name']
                }

        # 合并结果，确保每种维度只包含一项，且不重复计算
        final_surcharges = []
        processed_items = set()

        # 首先添加基于维度的最大项
        for dim_type, item in selected_by_dimension.items():
            item_key = f"{item['type']}_{item['name']}"
            if item_key not in processed_items:
                final_item = {k: v for k, v in item.items() if k not in ['type', 'dimension_type']}
                final_surcharges.append(final_item)
                processed_items.add(item_key)
                print(f"  添加基于维度 {dim_type} 的最大附加费: {item['name']}, 金额: {item['amount']}", file=sys.stdout)

        # 然后添加其他不基于维度的项
        for item in selected_surcharges:
            item_key = f"{item['type']}_{item['name']}"
            dim_type = item['dimension_type']

            # 如果这个项已经通过维度选择添加过，或者它有维度类型但不是该维度的最大项，则跳过
            if item_key in processed_items or (dim_type and dim_type != 'NONE' and item != selected_by_dimension.get(dim_type)):
                continue

            final_item = {k: v for k, v in item.items() if k not in ['type', 'dimension_type']}
            final_surcharges.append(final_item)
            processed_items.add(item_key)
            print(f"  添加非维度相关或其他维度的附加费: {item['name']}, 金额: {item['amount']}", file=sys.stdout)

        print(f"\n附加费计算完成，共 {len(final_surcharges)} 项", file=sys.stdout)
        return surcharges + final_surcharges

    def _calculate_peak_surcharges(self, product: Product, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """计算旺季附加费

        Args:
            product: 产品对象
            data: 计算数据，可以包含'calculation_date'字段指定计算日期

        Returns:
            List[Dict[str, Any]]: 旺季附加费列表
        """
        peak_surcharges = []

        try:
            # 检查是否指定了计算日期，如果没有则使用当前日期
            if 'calculation_date' in data and data['calculation_date']:
                try:
                    if isinstance(data['calculation_date'], str):
                        # 尝试解析字符串格式的日期
                        from datetime import datetime
                        calculation_date = datetime.strptime(data['calculation_date'], '%Y-%m-%d').date()
                    elif isinstance(data['calculation_date'], datetime.date):
                        calculation_date = data['calculation_date']
                    else:
                        calculation_date = timezone.now().date()
                        logger.warning(f"无法识别的日期格式: {data['calculation_date']}，使用当前日期")
                except Exception as e:
                    calculation_date = timezone.now().date()
                    logger.warning(f"日期转换错误: {str(e)}，使用当前日期")
            else:
                calculation_date = timezone.now().date()

            logger.info(f"使用计算日期: {calculation_date} 计算旺季附加费")

            # 获取适用的旺季附加费 - 基于指定日期
            applicable_peak_surcharges = PeakSeasonSurcharge.objects.filter(
                product=product,
                start_date__lte=calculation_date,
                end_date__gte=calculation_date,
                is_deleted=False
            )

            print(f"\n========== 旺季附加费检查 ==========", file=sys.stdout)
            print(f"计算日期: {calculation_date}", file=sys.stdout)
            all_peak_surcharges = PeakSeasonSurcharge.objects.filter(product=product, is_deleted=False)
            print(f"产品 {product.product_name} (ID: {product.product_id}) 的旺季附加费总数: {all_peak_surcharges.count()}", file=sys.stdout)

            # 记录详细日志
            if all_peak_surcharges.count() > 0:
                print("所有旺季附加费设置:", file=sys.stdout)
                for ps in all_peak_surcharges:
                    print(f"  - {ps.surcharge_type}: {ps.start_date} 到 {ps.end_date}, 金额: {ps.fee_amount}", file=sys.stdout)
                    print(f"    是否在计算日期内: {'是' if ps.start_date <= calculation_date <= ps.end_date else '否'}", file=sys.stdout)

            print(f"当前有效的旺季附加费数量: {applicable_peak_surcharges.count()}", file=sys.stdout)

            # 处理每个旺季附加费
            if applicable_peak_surcharges.exists():
                print("\n当前有效的旺季附加费:", file=sys.stdout)
                for ps in applicable_peak_surcharges:
                    try:
                        print(f"旺季附加费: {ps.surcharge_type}", file=sys.stdout)
                        print(f"  时间段: {ps.start_date} 到 {ps.end_date}", file=sys.stdout)
                        print(f"  金额: {ps.fee_amount}", file=sys.stdout)

                        # 检查金额是否大于0
                        if ps.fee_amount <= 0:
                            print(f"  金额为0或负数，不添加到附加费列表", file=sys.stdout)
                            continue

                        # 添加到附加费列表
                        surcharge_item = {
                            'type': '旺季附加费(Peak Season Surcharge)',
                            'name': ps.surcharge_type,
                            'amount': str(ps.fee_amount),
                            'condition': f"旺季附加费 {ps.start_date} 至 {ps.end_date}"
                        }
                        peak_surcharges.append(surcharge_item)
                        print(f"  添加到附加费列表: 金额 = {ps.fee_amount}", file=sys.stdout)
                    except Exception as e:
                        logger.warning(f"处理旺季附加费时出错: {str(e)}")
                        continue
            else:
                print("\n没有适用的旺季附加费", file=sys.stdout)
                if all_peak_surcharges.count() > 0:
                    print("原因可能是:", file=sys.stdout)
                    print(f"  1. 计算日期 {calculation_date} 不在任何旺季附加费的有效期内", file=sys.stdout)
                    print(f"  2. 产品没有配置有效的旺季附加费", file=sys.stdout)

            return peak_surcharges

        except Exception as e:
            logger.error(f"计算旺季附加费失败: {str(e)}")
            return []
    
    def _get_dimension_type(self, condition_desc):
        """
        根据条件描述确定附加费的维度类型

        返回值:
            'LENGTH': 长度相关
            'WIDTH': 宽度相关
            'HEIGHT': 高度相关
            'WEIGHT': 重量相关
            'LENGTH_GIRTH': 长度+周长相关
            'RESIDENTIAL': 住宅地址相关
            'REMOTE': 偏远地区相关
            'NONE': 无特定维度
        """
        if not condition_desc:
            return 'NONE'

        if '最长边' in condition_desc or '长度 >' in condition_desc:
            return 'LENGTH'

        if '宽度 >' in condition_desc:
            return 'WIDTH'

        if '高度 >' in condition_desc:
            return 'HEIGHT'

        if '实际重量' in condition_desc or '重量 >' in condition_desc:
            return 'WEIGHT'

        if '长+周长' in condition_desc or '长度+周长' in condition_desc:
            return 'LENGTH_GIRTH'

        if '住宅地址' in condition_desc or 'Residential' in condition_desc or 'Home Delivery' in condition_desc:
            return 'RESIDENTIAL'

        if '偏远地区' in condition_desc or 'Remote' in condition_desc:
            return 'REMOTE'

        return 'NONE'

    def _get_surcharge_type_display(self, surcharge_type):
        """
        获取附加费类型的显示名称
        """
        type_mapping = {
            'RESIDENTIAL_SURCHARGE': '住宅地址附加费(Residential Surcharge)',
            'REMOTE_AREA_SURCHARGE': '偏远地区附加费(Delivery Area Surcharge)',
            'OVERSIZE_SURCHARGE': '超大超尺寸费(Oversize)',
            'UNAUTHORIZED_PACKAGE': '不可发包裹(Unauthorized)',
            'ADDITIONAL_HANDLING': '额外处理费(Additional Handling)',
            'PEAK_SURCHARGE': '旺季附加费(Peak Surcharge)'
        }
        return type_mapping.get(surcharge_type, surcharge_type) 