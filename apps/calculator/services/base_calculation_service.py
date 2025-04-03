"""
基础计算服务
处理基本的计算逻辑
"""

import logging
import sys
import random
import string
import json
from decimal import Decimal, InvalidOperation
from typing import Dict, Any, List, Optional, Tuple

from django.utils import timezone
from django.db import transaction
from django.db.models import Q
from django.conf import settings

from apps.core.utils import (
    generate_request_id,
    round_fee,
    validate_calculation_input,
    calculate_volume_weight,
    calculate_chargeable_weight,
)
from apps.calculator.utils import unit_conversion_utils
from apps.calculator.models import Product, Calculation, CalculationDetail
from apps.core.exceptions import (
    ProductNotFoundException,
    WeightPointNotFoundException,
    ZoneRateNotFoundException,
    CalculationException,
    ValidationException,
)
from apps.products.models import BaseFee, Surcharge
from apps.postal_codes.models import ZipZone
from apps.fuel_rates.models import FuelRate
from apps.core.config import get_setting, DEFAULT_ZONE
from django.core.cache import cache

logger = logging.getLogger(__name__)

class BaseCalculationService:
    """
    基础计算服务
    处理运费基本计算逻辑
    """
    
    def __init__(self):
        """初始化基础计算服务"""
        self.logger = logging.getLogger(__name__)
    
    def _generate_random_string(self, length=6):
        """
        生成指定长度的随机字符串
        
        Args:
            length: 字符串长度，默认为6
            
        Returns:
            str: 随机字符串
        """
        letters = string.ascii_uppercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
    
    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算运费
        
        Args:
            data: 计算请求数据
            
        Returns:
            Dict[str, Any]: 计算结果
        """
        try:
            # 导入计算器模块
            from apps.calculator.fees import BaseFreightCalculator, FuelSurchargeCalculator, SurchargeCalculator
            
            # 输出计算开始信息
            print("\n========== 开始运费计算 ==========", file=sys.stdout)
            print(f"输入数据: {data}", file=sys.stdout)
            
            # 直接查询数据库中的所有BaseFee记录，并打印raw_data内容
            from apps.products.models import BaseFee
            product_id = data.get('product_id')
            fees = BaseFee.objects.filter(product__product_id=product_id, is_deleted=False)
            print(f"\n【数据库核查】找到产品ID={product_id}的{fees.count()}条费用记录:", file=sys.stdout)
            
            for i, fee in enumerate(fees):
                print(f"\n--- 费用记录[{i+1}] weight={fee.weight}, fee_type={fee.fee_type} ---", file=sys.stdout)
                if hasattr(fee, 'raw_data') and fee.raw_data:
                    try:
                        if isinstance(fee.raw_data, dict):
                            print(f"raw_data内容(dict):", file=sys.stdout)
                            for k, v in fee.raw_data.items():
                                print(f"  {k}: {v}", file=sys.stdout)
                        else:
                            # 在这里添加json模块导入
                            import json
                            raw_data = json.loads(fee.raw_data)
                            print(f"raw_data内容(parsed):", file=sys.stdout)
                            for k, v in raw_data.items():
                                print(f"  {k}: {v}", file=sys.stdout)
                    except Exception as e:
                        print(f"解析raw_data失败: {str(e)}", file=sys.stdout)
                        print(f"原始内容: {fee.raw_data}", file=sys.stdout)
                else:
                    print(f"没有raw_data数据", file=sys.stdout)
            
            # 验证输入数据
            validate_calculation_input(data)
            print("输入数据验证通过", file=sys.stdout)
            
            # 获取基本参数
            product_id = data.get('product_id')
            weight = Decimal(str(data.get('weight', 0)))
            length = Decimal(str(data.get('length', 0)))
            width = Decimal(str(data.get('width', 0)))
            height = Decimal(str(data.get('height', 0)))
            is_residential = data.get('is_residential', False)
            
            # 计算体积重和计费重量
            volume_weight = calculate_volume_weight(length, width, height, Decimal('6000'))
            chargeable_weight = calculate_chargeable_weight(weight, volume_weight)
            
            print(f"体积重: {volume_weight}, 计费重量: {chargeable_weight}", file=sys.stdout)
            
            # 获取产品信息
            product = self.get_product(product_id)
            
            # 获取区域信息
            zone = self._get_zone(data.get('from_postal'), data.get('to_postal'))
            print(f"区域信息: {zone}", file=sys.stdout)
            
            # 检查FuelRate表中的燃油附加费率
            from apps.fuel_rates.models import FuelRate
            from django.db.models import Q
            
            calculation_date = data.get('calculation_date')
            if calculation_date:
                if isinstance(calculation_date, str):
                    import datetime
                    calculation_date = datetime.datetime.strptime(calculation_date, '%Y-%m-%d').date()
            else:
                calculation_date = timezone.now().date()
                
            # 查询所有有效的燃油费率
            fuel_rates = FuelRate.objects.filter(
                Q(effective_date__lte=calculation_date),
                Q(expiration_date__gte=calculation_date) | Q(expiration_date=None),
                Q(is_deleted=False)
            ).order_by('-effective_date')
            
            print(f"\n【燃油费率检查】找到{fuel_rates.count()}条有效燃油费率记录:", file=sys.stdout)
            for i, rate in enumerate(fuel_rates):
                print(f"  费率[{i+1}] 服务商={rate.provider.name if hasattr(rate, 'provider') else 'None'}, 费率={rate.rate_value}%, 有效期={rate.effective_date}至{rate.expiration_date}", file=sys.stdout)
            
            # 检查产品单位是否与输入单位一致，若不一致则转换
            weight_unit = data.get('weight_unit', 'KG')
            if product.weight_unit != weight_unit:
                print(f"产品单位 {product.weight_unit} 与输入单位 {weight_unit} 不一致，需要转换", file=sys.stdout)
                
                # 转换重量
                if product.weight_unit == 'LB' and weight_unit == 'KG':
                    # KG转LB
                    weight = unit_conversion_utils.kg_to_lb(weight, round_up=True)
                    volume_weight = unit_conversion_utils.kg_to_lb(volume_weight, round_up=True)
                    chargeable_weight = unit_conversion_utils.kg_to_lb(chargeable_weight, round_up=True)
                    print(f"重量单位转换: KG → LB, 计费重量: {chargeable_weight} LB", file=sys.stdout)
                elif product.weight_unit == 'KG' and weight_unit == 'LB':
                    # LB转KG
                    weight = unit_conversion_utils.lb_to_kg(weight, round_up=True)
                    volume_weight = unit_conversion_utils.lb_to_kg(volume_weight, round_up=True)
                    chargeable_weight = unit_conversion_utils.lb_to_kg(chargeable_weight, round_up=True)
                    print(f"重量单位转换: LB → KG, 计费重量: {chargeable_weight} KG", file=sys.stdout)
                
                # 更新计算数据
                calc_data = {
                    'weight': weight,
                    'volume_weight': volume_weight,
                    'chargeable_weight': chargeable_weight,
                    'zone': zone,
                    'length': length,
                    'width': width,
                    'height': height,
                    'from_postal': data.get('from_postal'),
                    'to_postal': data.get('to_postal'),
                    'is_residential': is_residential,
                    'calculation_date': data.get('calculation_date'),
                    'weight_unit': product.weight_unit,
                    'dimension_unit': data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT')
                }
            
            # 重量段位对齐 - 使用产品中定义的重量段位
            print(f"查找重量段位: 产品={product.product_id}, 计费重量={chargeable_weight} {product.weight_unit}", file=sys.stdout)
            weight_fees = BaseFee.objects.filter(
                product=product,
                is_deleted=False
            ).order_by('weight')
            
            if weight_fees.exists():
                weight_points = list(weight_fees.values_list('weight', flat=True))
                print(f"产品定义的重量段位: {weight_points}", file=sys.stdout)
                
                # 找到大于等于当前重量的最小重量点
                weight_aligned = None
                for point in weight_points:
                    if point >= chargeable_weight:
                        weight_aligned = point
                        break
                
                # 如果没有找到大于等于当前重量的点，使用最大重量点
                if weight_aligned is None and weight_points:
                    weight_aligned = max(weight_points)
                
                if weight_aligned is not None:
                    print(f"重量段位对齐: 原始计费重量={chargeable_weight}, 对齐后重量={weight_aligned} {product.weight_unit}", file=sys.stdout)
                    # 更新计费重量
                    chargeable_weight = weight_aligned
                    calc_data['chargeable_weight'] = chargeable_weight
            
            # 获取产品信息
            product = self.get_product(product_id)
            
            # 获取区域信息
            zone = self._get_zone(data.get('from_postal'), data.get('to_postal'))
            print(f"区域信息: {zone}", file=sys.stdout)
            
            # 检查FuelRate表中的燃油附加费率
            from apps.fuel_rates.models import FuelRate
            from django.db.models import Q
            
            calculation_date = data.get('calculation_date')
            if calculation_date:
                if isinstance(calculation_date, str):
                    import datetime
                    calculation_date = datetime.datetime.strptime(calculation_date, '%Y-%m-%d').date()
            else:
                calculation_date = timezone.now().date()
                
            # 查询所有有效的燃油费率
            fuel_rates = FuelRate.objects.filter(
                Q(effective_date__lte=calculation_date),
                Q(expiration_date__gte=calculation_date) | Q(expiration_date=None),
                Q(is_deleted=False)
            ).order_by('-effective_date')
            
            print(f"\n【燃油费率检查】找到{fuel_rates.count()}条有效燃油费率记录:", file=sys.stdout)
            for i, rate in enumerate(fuel_rates):
                print(f"  费率[{i+1}] 服务商={rate.provider.name if hasattr(rate, 'provider') else 'None'}, 费率={rate.rate_value}%, 有效期={rate.effective_date}至{rate.expiration_date}", file=sys.stdout)
            
            # 生成请求ID
            request_id = generate_request_id('CALC')
            
            # 创建计算数据字典
            calc_data = {
                'weight': weight,
                'volume_weight': volume_weight,
                'chargeable_weight': chargeable_weight,
                'zone': zone,
                'length': length,
                'width': width,
                'height': height,
                'from_postal': data.get('from_postal'),
                'to_postal': data.get('to_postal'),
                'is_residential': is_residential,
                'calculation_date': data.get('calculation_date'),
                'weight_unit': data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT'),
                'dimension_unit': data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT')
            }
            
            # 计算基础运费
            base_freight_calculator = BaseFreightCalculator()
            base_freight_result = base_freight_calculator.calculate_base_freight(product, calc_data)
            
            # 直接查询数据库，查看ZONE8的价格字段
            print(f"\n【直接数据库查询】查看BaseFee表中该产品的raw_data内容:", file=sys.stdout)
            from django.db import connection
            cursor = connection.cursor()
            # 使用插值防止SQL注入
            cursor.execute(
                """
                SELECT fee_id, product_id, weight, fee_type, raw_data 
                FROM base_fees 
                WHERE product_id = %s AND is_deleted = 0
                ORDER BY weight
                """, 
                [product.product_id]
            )
            
            rows = cursor.fetchall()
            print(f"找到 {len(rows)} 条BaseFee记录", file=sys.stdout)
            
            for row in rows:
                fee_id = row[0]
                product_id = row[1]
                weight = row[2]
                fee_type = row[3]
                raw_data_str = row[4]
                
                print(f"\n费用ID: {fee_id}, 产品ID: {product_id}, 重量: {weight}, 费用类型: {fee_type}", file=sys.stdout)
                
                # 解析raw_data
                if raw_data_str:
                    try:
                        # 在这里添加json模块导入
                        import json
                        raw_data = json.loads(raw_data_str)
                        
                        # 打印raw_data内容
                        for key, value in raw_data.items():
                            print(f"  {key}: {value}", file=sys.stdout)
                        
                        # 检查是否包含区域价格
                        zone_number = zone.replace("ZONE", "")
                        zone_keys = []
                        
                        # 生成可能的键名列表
                        for key in raw_data.keys():
                            if f"zone{zone_number}".lower() in key.lower() or zone.lower() in key.lower():
                                zone_keys.append(key)
                        
                        if zone_keys:
                            zone8_values = []
                            # 打印找到的区域价格值
                            for i, key in enumerate(zone_keys):
                                print(f"  {key}: {raw_data[key]}", file=sys.stdout)
                                zone8_values.append(raw_data[key])
                            
                            # 识别是否找到了目标值
                            for key, value in raw_data.items():
                                if str(value) in ["8.68", "8.93", "9.13", "9.37", "9.76"]:
                                    print(f"【发现目标值】键={key}, 值={value}", file=sys.stdout)
                    
                    except Exception as e:
                        print(f"解析raw_data出错: {str(e)}", file=sys.stdout)
            
            if not base_freight_result:
                print(f"基础运费计算失败，尝试使用旧方法计算", file=sys.stdout)
                # 获取重量点
                weight_point = self.get_weight_point(product, chargeable_weight)
                # 使用旧的方法计算基础运费
                base_fee = self.calculate_base_fee(product, weight_point, chargeable_weight, zone)
            else:
                base_fee = Decimal(base_freight_result.get('amount', '0'))
            
            # 检查基础运费是否为0，如果是0则发出警告并提示需要到产品数据库里修改
            if base_fee <= 0:
                print(f"\n【严重警告】：基础运费为0，这可能是数据库配置问题。请检查产品ID={product.product_id}在区域{zone}的价格设置。", file=sys.stdout)
                logger.warning(f"基础运费计算为0，产品ID={product.product_id}，区域={zone}，重量={chargeable_weight}")
                
                # 直接查询数据库，检查raw_data中价格确实为0
                base_fees = BaseFee.objects.filter(
                    product=product,
                    is_deleted=False
                ).order_by('weight')
                
                print(f"\n【数据库检查】 - 找到 {base_fees.count()} 个基础费用记录", file=sys.stdout)
                
                zone_number = zone.replace('ZONE', '')
                
                # 尝试查找raw_data中的价格
                found_price = False
                all_prices_zero = True
                for i, fee in enumerate(base_fees):
                    print(f"\n检查记录[{i+1}] weight={fee.weight}:", file=sys.stdout)
                    
                    # 检查raw_data
                    if hasattr(fee, 'raw_data') and fee.raw_data:
                        try:
                            # 导入json模块
                            import json
                            raw_data = fee.raw_data if isinstance(fee.raw_data, dict) else json.loads(fee.raw_data)
                            
                            # 尝试不同的可能键名
                            possible_keys = [
                                f"Zone{zone_number}基础价格",
                                f"zone{zone_number}基础价格",
                                f"Zone{zone_number}",
                                f"zone{zone_number}",
                                f"ZONE{zone_number}",
                                f"zone{zone_number}_price"
                            ]
                            
                            for key in possible_keys:
                                if key in raw_data:
                                    price_value = raw_data[key]
                                    print(f"  在raw_data中找到键 '{key}' = {price_value}", file=sys.stdout)
                                    if price_value is not None:
                                        try:
                                            price = Decimal(str(price_value))
                                            found_price = True
                                            if price > 0:
                                                all_prices_zero = False
                                                print(f"  找到有效价格 {price}", file=sys.stdout)
                                            else:
                                                print(f"  【数据问题】价格为0！需要更新数据库设置非零价格", file=sys.stdout)
                                        except:
                                            pass
                        except Exception as e:
                            print(f"  解析raw_data失败: {str(e)}", file=sys.stdout)
                
                if not found_price:
                    print(f"\n【严重问题】：在raw_data中未找到任何ZONE{zone_number}的价格字段，请检查数据格式。", file=sys.stdout)
                    logger.error(f"在raw_data中未找到任何有效的价格，请检查数据。产品ID={product.product_id}，区域={zone}")
                elif all_prices_zero:
                    print(f"\n【严重问题】：在raw_data中所有ZONE{zone_number}的价格均为0，需要在数据库中设置正确的价格！", file=sys.stdout)
                    print(f"解决方法：请在数据库BaseFee表中，找到产品ID={product.product_id}的记录，修改raw_data中的ZONE{zone_number}相关价格为非零值。", file=sys.stdout)
                
                # 返回基础费用
                print(f"\n【定价建议】：产品{product.product_name}应该为ZONE{zone_number}设置合理的价格", file=sys.stdout)
            
            print(f"基础运费: {base_fee}", file=sys.stdout)
            
            # 计算燃油附加费
            fuel_calculator = FuelSurchargeCalculator()
            fuel_result = fuel_calculator.calculate_fuel_surcharge(product, calc_data, {'type': '基础运费', 'amount': str(base_fee)})
            
            if not fuel_result:
                print(f"燃油附加费计算失败，尝试使用旧方法计算", file=sys.stdout)
                # 获取当前日期或指定计算日期
                calculation_date = data.get('calculation_date')
                if calculation_date:
                    if isinstance(calculation_date, str):
                        import datetime
                        calculation_date = datetime.datetime.strptime(calculation_date, '%Y-%m-%d').date()
                else:
                    calculation_date = timezone.now().date()

                # 检查服务商的燃油费率配置
                from django.db import connection
                print(f"\n【硬编码检查】检查是否有最低燃油费率设置:", file=sys.stdout)
                with connection.cursor() as cursor:
                    # 检查服务商表是否有特殊设置
                    cursor.execute("SELECT * FROM service_providers WHERE name = %s AND is_deleted = 0", [product.provider_name])
                    if cursor.description:
                        provider_fields = [desc[0] for desc in cursor.description]
                        provider_row = cursor.fetchone()
                        if provider_row:
                            provider_data = {provider_fields[i]: provider_row[i] for i in range(len(provider_fields))}
                            print(f"服务商数据: {provider_data}", file=sys.stdout)
                            
                            # 检查是否有config字段
                            config_fields = [f for f in provider_fields if 'config' in f.lower() or 'setting' in f.lower()]
                            for field in config_fields:
                                config_value = provider_data.get(field)
                                if config_value:
                                    print(f"服务商配置字段 {field}: {config_value}", file=sys.stdout)
                                    # 检查是否包含'1.3'或'1.30'
                                    if isinstance(config_value, str) and ('1.3' in config_value or '1.30' in config_value):
                                        print(f"【发现】服务商配置中存在1.30或1.3值！", file=sys.stdout)
                    
                    # 检查自定义配置表
                    try:
                        cursor.execute("SELECT * FROM system_settings WHERE is_deleted = 0")
                        if cursor.description:
                            setting_fields = [desc[0] for desc in cursor.description]
                            rows = cursor.fetchall()
                            for row in rows:
                                setting_data = {setting_fields[i]: row[i] for i in range(len(setting_fields))}
                                print(f"系统设置: {setting_data}", file=sys.stdout)
                                
                                # 检查值中是否包含1.3或1.30
                                for field, value in setting_data.items():
                                    if isinstance(value, str) and ('1.3' in value or '1.30' in value or 'min_fuel' in value.lower()):
                                        print(f"【发现】系统设置中存在可能的最低燃油费配置: {field}={value}", file=sys.stdout)
                    except Exception as e:
                        print(f"检查系统设置表失败: {str(e)}", file=sys.stdout)

                # 直接检查代码中是否有硬编码的1.30
                print("\n【代码检查】直接在源码中搜索硬编码的燃油附加费1.30", file=sys.stdout)
                
                # 先检查产品是否设置了最低燃油费
                if hasattr(product, 'config') and product.config:
                    try:
                        if isinstance(product.config, str):
                            import json
                            product_config = json.loads(product.config)
                        else:
                            product_config = product.config
                            
                        if isinstance(product_config, dict):
                            min_fuel_keys = [k for k in product_config.keys() if 'min_fuel' in k.lower() or 'fuel_min' in k.lower()]
                            for key in min_fuel_keys:
                                print(f"产品配置包含最低燃油费设置: {key}={product_config[key]}", file=sys.stdout)
                    except Exception as e:
                        print(f"解析产品配置失败: {str(e)}", file=sys.stdout)
                    
                # 查询匹配的燃油费率
                fuel_rate_record = FuelRate.objects.filter(
                    Q(provider__name=product.provider_name),
                    Q(effective_date__lte=calculation_date),
                    Q(expiration_date__gte=calculation_date) | Q(expiration_date=None),
                    Q(is_deleted=False)
                ).order_by('-effective_date').first()
                
                # 获取费率值
                if fuel_rate_record:
                    fuel_rate = Decimal(str(fuel_rate_record.rate_value)) / 100
                    print(f"找到燃油费率: {fuel_rate_record.rate_value}%", file=sys.stdout)
                else:
                    fuel_rate = Decimal('0.0775')  # 7.75%
                    print(f"未找到燃油费率，使用默认值: {fuel_rate * 100}%", file=sys.stdout)
                    
                # 计算燃油附加费
                fuel_surcharge = base_fee * fuel_rate
                print(f"燃油附加费: {fuel_surcharge} (费率: {fuel_rate * 100}%, 基础费用: {base_fee})", file=sys.stdout)
                
                # 检查特殊情况
                if base_fee == 0 and fuel_surcharge > 0:
                    print(f"【异常情况】基础运费为0，但燃油附加费为{fuel_surcharge}，这可能是硬编码值", file=sys.stdout)
                
                # 检查是否配置了最低燃油费
                min_fuel_config = None

                # 首先，检查产品设置
                try:
                    product_config = json.loads(product.config) if hasattr(product, 'config') and product.config else {}
                    
                    # 检查产品配置中的最低燃油费设置
                    for key in product_config:
                        if 'min_fuel' in key.lower() or 'min_fuel_amount' in key.lower():
                            min_fuel_config = product_config[key]
                            print(f"产品配置包含最低燃油费设置: {key}={product_config[key]}", file=sys.stdout)
                except Exception as e:
                    print(f"解析产品配置失败: {str(e)}", file=sys.stdout)
                
                # 应用最低燃油费设置
                if min_fuel_config is not None:
                    try:
                        min_fuel = Decimal(str(min_fuel_config))
                        if fuel_surcharge < min_fuel and fuel_surcharge > 0:
                            print(f"应用最低燃油费: {min_fuel}", file=sys.stdout)
                            fuel_surcharge = min_fuel
                    except (ValueError, TypeError):
                        pass
            else:
                fuel_surcharge = Decimal(fuel_result.get('amount', '0'))
                # 修复bug，原来是从'rate'直接转换，现在正确处理带%的字符串
                rate_str = fuel_result.get('rate', '0')
                if isinstance(rate_str, str) and '%' in rate_str:
                    fuel_rate = Decimal(rate_str.replace('%', '')) / 100
                else:
                    fuel_rate = Decimal(str(rate_str)) / 100
                print(f"燃油附加费: {fuel_surcharge} (费率: {fuel_rate * 100}%, 基础费用: {base_fee})", file=sys.stdout)
                print(f"燃油费率来源: {fuel_result.get('source_description', '未知')}", file=sys.stdout)
                
                # 强制规则：基础运费为0时，燃油附加费必须为0
                if base_fee == Decimal('0') and fuel_surcharge > Decimal('0'):
                    print(f"【强制修正】基础运费为0，但燃油附加费为{fuel_surcharge}，正在修正为0", file=sys.stdout)
                    fuel_surcharge = Decimal('0')
                
                # 打印额外的调试信息
                if base_fee <= 0 and fuel_surcharge > 0:
                    print(f"【特殊情况】基础费用为0，但燃油附加费大于0，可能存在最低燃油费", file=sys.stdout)
                    if 'min_amount' in fuel_result:
                        print(f"找到最低燃油费设置: {fuel_result.get('min_amount')}", file=sys.stdout)
            
            # 计算其他附加费
            surcharge_calculator = SurchargeCalculator()
            surcharge_results = surcharge_calculator.calculate_surcharges(product, calc_data)
            
            if not surcharge_results:
                surcharges = self._calculate_surcharges(product, data, chargeable_weight, zone)
            else:
                surcharges = surcharge_results
            
            surcharge_total = sum(Decimal(str(s.get('amount', 0))) for s in surcharges)
            print(f"附加费总额: {surcharge_total}", file=sys.stdout)
            
            # 计算总费用
            total_fee = base_fee + fuel_surcharge + surcharge_total
            print(f"总运费: {total_fee}", file=sys.stdout)
            
            # 保存计算结果
            calculation_data = {
                'request_id': request_id,
                'product': product,
                'from_postal': data.get('from_postal'),
                'to_postal': data.get('to_postal'),
                'weight': weight,
                'weight_unit': data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT'),
                'dimension_unit': data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT'),
                'volume_weight': volume_weight,
                'chargeable_weight': chargeable_weight,
                'length': data.get('length'),
                'width': data.get('width'),
                'height': data.get('height'),
                'zone': zone,
                'base_fee': base_fee,
                'fuel_fee': fuel_surcharge,
                'total_fee': total_fee,
                'currency': product.currency,
                'status': 'success'
            }
            
            # 保存计算结果
            try:
                with transaction.atomic():
                    # 创建计算记录对象
                    calculation_fields = {
                        'request_id': calculation_data.get('request_id'),
                        'product': calculation_data.get('product'),
                        'from_postal': calculation_data.get('from_postal'),
                        'to_postal': calculation_data.get('to_postal'),
                        'weight': calculation_data.get('weight'),
                        'volume_weight': calculation_data.get('volume_weight'),
                        'chargeable_weight': calculation_data.get('chargeable_weight'),
                        'length': calculation_data.get('length'),
                        'width': calculation_data.get('width'),
                        'height': calculation_data.get('height'),
                        'zone': calculation_data.get('zone'),
                        'base_fee': calculation_data.get('base_fee'),
                        'fuel_fee': calculation_data.get('fuel_fee'),
                        'total_fee': calculation_data.get('total_fee'),
                        'currency': calculation_data.get('currency')
                    }
                    
                    # 创建并保存计算结果
                    calculation = Calculation(**calculation_fields)
                    calculation.save()
                    print(f"计算结果已保存，ID: {calculation.id}", file=sys.stdout)
                    
                    # 保存明细记录
                    details = calculation_data.get('details', [])
                    for detail in details:
                        detail_fields = {
                            'calculation': calculation,
                            'fee_type': detail.get('charge_type', 'OTHER'),
                            'fee_name': detail.get('charge_name', '其他费用'),
                            'amount': detail.get('amount', Decimal('0')),
                            'calculation_formula': detail.get('condition', '')
                        }
                        
                        detail_obj = CalculationDetail(**detail_fields)
                        detail_obj.save()
                        print(f"计算明细已保存: {detail_obj.fee_name}", file=sys.stdout)
                    
                    return calculation
            except Exception as e:
                print(f"保存计算结果出错: {str(e)}", file=sys.stdout)
                self.logger.error(f"保存计算结果出错: {str(e)}")
                return None
            
        except Exception as e:
            logger.exception("计算运费失败", extra={'data': str(data)[:1000]})
            raise CalculationException(f"计算运费失败: {str(e)}")
            
    def _get_zone(self, from_postal, to_postal):
        """
        获取从from_postal到to_postal的分区号
        
        Args:
            from_postal: 始发邮编
            to_postal: 目的地邮编
            
        Returns:
            str: 分区号，例如'ZONE1', 'ZONE2'等
        """
        # 加载ZipZone模型，避免循环导入
        from apps.postal_codes.models import ZipZone
        import sys
        
        try:
            print(f"正在查询区域信息: 从 {from_postal} 到 {to_postal}", file=sys.stdout)
            self.logger.info(f"正在查询区域信息: 从 {from_postal} 到 {to_postal}")
            
            # 检查起始邮编和目的邮编是否有效
            if not from_postal or not to_postal:
                print(f"警告: 邮编为空，from_postal={from_postal}, to_postal={to_postal}", file=sys.stdout)
                self.logger.warning(f"邮编为空，from_postal={from_postal}, to_postal={to_postal}")
                return "ZONE1"  # 返回默认区域
                
            # 规范化邮编
            from_postal = str(from_postal).strip().upper()
            to_postal = str(to_postal).strip().upper()
            
            # 尝试从缓存获取
            cache_key = f"zipzone_{from_postal}_{to_postal}"
            cached_zone = cache.get(cache_key)
            if cached_zone:
                print(f"从缓存获取到区域信息: {cached_zone}", file=sys.stdout)
                return cached_zone
            
            # 查询数据库
            zone_obj = None
            try:
                # 获取当前产品对应的服务提供商
                # 注意：如果没有provider_id，我们简单地查询所有区域
                provider_filter = {}
                
                # 先匹配精确的邮编
                zone_obj = ZipZone.objects.filter(
                    origin_zip=from_postal,
                    dest_zip_start__lte=to_postal,
                    dest_zip_end__gte=to_postal,
                    **provider_filter
                ).first()
                
                if not zone_obj:
                    # 再匹配邮编前缀
                    to_prefix = to_postal[:3] if len(to_postal) >= 3 else to_postal
                    zone_obj = ZipZone.objects.filter(
                        origin_zip=from_postal,
                        dest_zip_start__lte=to_prefix,
                        dest_zip_end__gte=to_prefix,
                        **provider_filter
                    ).first()
                
                if not zone_obj:
                    # 使用默认区域
                    print(f"未找到区域信息，尝试使用通配符", file=sys.stdout)
                    default_origin = from_postal  # 先尝试当前始发地的通配符
                    
                    zone_obj = ZipZone.objects.filter(
                        origin_zip=default_origin,
                        dest_zip_start='*',
                        dest_zip_end='*',
                        **provider_filter
                    ).first()
                    
                    if not zone_obj:
                        # 尝试任意始发地的通配符
                        zone_obj = ZipZone.objects.filter(
                            origin_zip='*',
                            dest_zip_start='*',
                            dest_zip_end='*',
                            **provider_filter
                        ).first()
                    
            except Exception as db_err:
                print(f"查询区域数据库出错: {str(db_err)}", file=sys.stdout)
                self.logger.error(f"查询区域数据库出错: {str(db_err)}")
                return "ZONE1"  # 返回默认区域
            
            # 获取区域号
            if zone_obj:
                zone = f"ZONE{zone_obj.zone_number}"
                # 设置缓存
                cache.set(cache_key, zone, 3600)  # 缓存1小时
                print(f"找到区域: {zone}", file=sys.stdout)
                return zone
            else:
                total_zones = ZipZone.objects.count()
                print(f"未找到区域信息，使用默认区域ZONE1。数据库中有{total_zones}条区域记录。", file=sys.stdout)
                self.logger.warning(f"未找到区域信息: 从 {from_postal} 到 {to_postal}，使用默认区域ZONE1")
                return "ZONE1"  # 返回默认区域
                
        except Exception as e:
            print(f"获取区域信息时发生错误: {str(e)}", file=sys.stdout)
            self.logger.error(f"获取区域信息时发生错误: {str(e)}")
            return "ZONE1"  # 返回默认区域
    
    def _calculate_surcharges(self, product: Product, data: Dict[str, Any], 
                              chargeable_weight: Decimal, zone: str) -> List[Dict]:
        """
        计算附加费
        
        Args:
            product: 产品对象
            data: 请求数据
            chargeable_weight: 计费重量
            zone: 区域
            
        Returns:
            List[Dict]: 附加费列表
        """
        from apps.products.models import Surcharge
        
        print(f"计算附加费 - 产品: {product.product_id}, 区域: {zone}", file=sys.stdout)
        surcharges = []
        
        try:
            # 获取产品的所有附加费
            product_surcharges = Surcharge.objects.filter(
                product=product,
                is_deleted=False
            )
            
            # 当前日期或请求指定的日期
            calculation_date = data.get('calculation_date')
            if calculation_date:
                if isinstance(calculation_date, str):
                    import datetime
                    calculation_date = datetime.datetime.strptime(calculation_date, '%Y-%m-%d').date()
            else:
                calculation_date = timezone.now().date()
            
            print(f"找到 {product_surcharges.count()} 个附加费配置", file=sys.stdout)
            
            # 获取区域号
            zone_number = int(zone.replace('ZONE', '')) if zone.startswith('ZONE') else 0
            
            # 处理每个附加费
            for surcharge in product_surcharges:
                # 检查附加费是否适用于当前请求
                is_applicable = self._check_surcharge_applicable(
                    surcharge, data, chargeable_weight, zone_number, calculation_date
                )
                
                # 获取附加费金额
                amount = Decimal('0')
                if is_applicable:
                    amount = surcharge.calculate_amount(zone)
                
                # 获取费率 
                rate = 0
                # 从zone_fees JSONField中获取费率
                zone_key = f"zone{zone_number}"
                if zone_key in surcharge.zone_fees:
                    try:
                        rate = Decimal(str(surcharge.zone_fees[zone_key]))
                    except (ValueError, TypeError):
                        rate = 0
                
                # 构建附加费信息
                surcharge_info = {
                    'type': surcharge.surcharge_type,
                    'name': surcharge.condition_desc or surcharge.surcharge_type,
                    'amount': str(amount),
                    'condition': surcharge.condition_desc or '',
                    'rate': rate,
                    'unit_price': 0,  # 附加费没有单价概念
                    'zone': zone
                }
                
                surcharges.append(surcharge_info)
                print(f"附加费: {surcharge.surcharge_type}, 金额: {amount}", file=sys.stdout)
            
            # 住宅附加费特殊处理（如果产品支持且请求中标记为住宅地址）
            if data.get('is_residential', False):
                # 检查是否已经有住宅附加费
                has_residential = any(s['type'] == '住宅附加费' for s in surcharges)
                if not has_residential:
                    # 获取住宅附加费配置
                    residential_fee = get_setting('RESIDENTIAL_SURCHARGE_AMOUNT', '0.00')
                    
                    # 添加住宅附加费
                    surcharges.append({
                        'type': '住宅附加费',
                        'name': '住宅配送费',
                        'amount': residential_fee,
                        'condition': '住宅地址配送',
                        'rate': 0,
                        'unit_price': 0,
                        'zone': zone
                    })
            
            return surcharges
            
        except Exception as e:
            print(f"计算附加费出错: {str(e)}", file=sys.stdout)
            logger.error(f"计算附加费出错: {str(e)}")
            # 出错时返回空列表
            return []
    
    def _check_surcharge_applicable(self, surcharge, data, weight, zone_number, calculation_date):
        """检查附加费是否适用"""
        try:
            # 检查日期范围
            if hasattr(surcharge, 'start_date') and surcharge.start_date:
                if calculation_date < surcharge.start_date:
                    return False
            
            if hasattr(surcharge, 'end_date') and surcharge.end_date:
                if calculation_date > surcharge.end_date:
                    return False
            
            # 检查重量范围
            if hasattr(surcharge, 'min_weight') and surcharge.min_weight:
                if weight < surcharge.min_weight:
                    return False
            
            if hasattr(surcharge, 'max_weight') and surcharge.max_weight:
                if weight > surcharge.max_weight:
                    return False
            
            # 特定条件检查
            if surcharge.surcharge_type == '住宅附加费':
                if not data.get('is_residential', False):
                    return False
            
            # 这里可以添加更多条件检查
            
            return True
            
        except Exception as e:
            print(f"检查附加费适用性出错: {str(e)}", file=sys.stdout)
            return False
    
    def _get_surcharge_amount(self, surcharge, data, zone_number):
        """获取附加费金额"""
        try:
            # 尝试获取指定区域的费用
            amount = Decimal('0')
            
            # 使用正确的区域字段名
            zone_field = f'zone{zone_number}_fee'
            
            if hasattr(surcharge, zone_field) and getattr(surcharge, zone_field) is not None:
                amount = getattr(surcharge, zone_field)
            elif hasattr(surcharge, 'fee_amount') and surcharge.fee_amount is not None:
                amount = surcharge.fee_amount
            
            return amount
            
        except Exception as e:
            print(f"获取附加费金额出错: {str(e)}", file=sys.stdout)
            return Decimal('0')

    def calculate_base_fee(self, product, weight_point, chargeable_weight, zone):
        """
        计算基础运费
        
        Args:
            product: 产品对象
            weight_point: 重量点
            chargeable_weight: 计费重量
            zone: 区域
            
        Returns:
            Decimal: 基础运费
        """
        try:
            # 尝试使用产品费率表取得基础运费
            base_fee = self._get_rate_from_table(product, weight_point, chargeable_weight, zone)
            
            # 如果从费率表获取成功，直接返回
            if base_fee > 0:
                return round_fee(base_fee)
            
            # 如果费率表没有数据，尝试查询 BaseFee 表
            base_fee_obj = BaseFee.objects.filter(
                product=product, 
                zone=zone, 
                weight_start__lte=chargeable_weight, 
                weight_end__gte=chargeable_weight
            ).first()
            
            if base_fee_obj:
                print(f"找到基础运费: {base_fee_obj.fee}", file=sys.stdout)
                return round_fee(base_fee_obj.fee)
            
            # 如果基础运费为0或找不到，使用重量点和区域计算
            # 获取该产品在该区域的每重量单位的费率
            rate = BaseFee.objects.filter(
                product=product,
                zone=zone,
                is_per_kg=True
            ).first()
            
            if rate:
                print(f"找到每公斤费率: {rate.fee}", file=sys.stdout)
                # 每额外超过起始重量，按每公斤费率收费
                extra_weight = max(chargeable_weight - weight_point.weight, Decimal('0'))
                print(f"额外重量: {extra_weight}", file=sys.stdout)
                
                # 起始重量段的费用
                first_weight_rate = BaseFee.objects.filter(
                    product=product,
                    zone=zone,
                    weight_start__lte=weight_point.weight,
                    weight_end__gte=weight_point.weight,
                    is_per_kg=False
                ).first()
                
                if first_weight_rate:
                    print(f"找到起始重量费率: {first_weight_rate.fee}", file=sys.stdout)
                    # 计算总费用 = 起始重量费用 + 额外重量 * 每公斤费率
                    total_fee = first_weight_rate.fee + (extra_weight * rate.fee)
                    return round_fee(total_fee)
                else:
                    # 如果找不到起始重量费率，直接用重量乘以每公斤费率
                    total_fee = chargeable_weight * rate.fee
                    return round_fee(total_fee)
            
            # 如果以上方法都找不到费率，尝试使用产品默认费率
            if product.base_fee > 0:
                print(f"使用产品默认费率: {product.base_fee}", file=sys.stdout)
                return round_fee(product.base_fee)
            
            # 最后实在找不到，抛出异常
            raise ZoneRateNotFoundException(f"找不到产品[{product.product_id}]在区域[{zone}]的费率")
            
        except Exception as e:
            self.logger.error(f"计算基础运费出错: {str(e)}")
            raise CalculationException(f"计算基础运费出错: {str(e)}")
    
    def get_product(self, product_id: str) -> Product:
        """
        获取产品信息
        
        Args:
            product_id: 产品ID
            
        Returns:
            Product: 产品对象
            
        Raises:
            ProductNotFoundException: 如果产品不存在
        """
        try:
            # 直接使用product_id字段进行查询，因为它是字符串类型
            product = Product.objects.get(product_id=product_id, status=True)
            
            # 输出产品详情
            print(f"获取到产品详情:", file=sys.stdout)
            print(f"  产品ID: {product.product_id}", file=sys.stdout)
            print(f"  产品名称: {product.product_name}", file=sys.stdout)
            print(f"  服务商: {product.provider_name}", file=sys.stdout)
            print(
                f"  体积重系数: {product.dim_factor} {product.dim_factor_unit}",
                file=sys.stdout)
            print(
                f"  生效日期: {product.effective_date} - {product.expiration_date}", 
                file=sys.stdout)
            print(f"  货币单位: {product.currency}", file=sys.stdout)
            
            return product
        except Product.DoesNotExist:
            print(f"错误: 产品不存在: {product_id}", file=sys.stdout)
            raise ProductNotFoundException(f'产品不存在: {product_id}')
    
    def get_weight_point(self, product: Product, weight: Decimal) -> BaseFee:
        """
        获取重量点
        
        Args:
            product: 产品对象
            weight: 重量
            
        Returns:
            BaseFee: 重量点对象
            
        Raises:
            WeightPointNotFoundException: 如果找不到合适的重量点
        """
        try:
            print(
                f"获取重量点 - 产品: {product.product_id}, 重量: {weight}", file=sys.stdout)

            # 获取大于等于当前重量的最小重量点
            weight_points = BaseFee.objects.filter(
                product=product,
                weight__gte=weight,
                is_deleted=False
            ).order_by('weight')

            print(f"找到 {weight_points.count()} 个大于等于当前重量的重量点", file=sys.stdout)

            weight_point = weight_points.first()

            if not weight_point:
                # 如果没有找到大于等于当前重量的重量点，则使用最大重量点
                print("未找到大于等于当前重量的重量点，尝试获取最大重量点", file=sys.stdout)
                weight_points = BaseFee.objects.filter(
                    product=product,
                    is_deleted=False
                ).order_by('-weight')

                print(f"找到 {weight_points.count()} 个重量点", file=sys.stdout)

                weight_point = weight_points.first()

                if not weight_point:
                    print(
                        f"错误: 找不到产品 {product.product_id} 的任何重量点",
                        file=sys.stdout)
                    raise WeightPointNotFoundException(
                        f"找不到产品 {product.product_id} 的重量点")

                print(f"使用最大重量点: {weight_point.weight}", file=sys.stdout)
            else:
                print(f"找到适合的重量点: {weight_point.weight}", file=sys.stdout)

            return weight_point
        except WeightPointNotFoundException:
            raise
        except Exception as e:
            print(f"获取重量点时出错: {str(e)}", file=sys.stdout)
            logger.error(f"获取重量点时出错: {str(e)}")
            raise WeightPointNotFoundException(f"获取重量点失败: {str(e)}")
    
    def save_calculation_result(self, data: Dict[str, Any], product: Product, zone: str, 
                               weight: Decimal, volume_weight: Decimal, chargeable_weight: Decimal,
                               base_fee: Decimal, fuel_surcharge: Decimal, fuel_rate: Decimal,
                               surcharges: List[Dict], total_fee: Decimal) -> Dict:
        """
        保存计算结果并返回格式化的结果
        """
        try:
            # 生成唯一请求ID
            request_id = generate_request_id('CALC')
            
            # 创建计算请求记录
            calculation_data = {
                'request_id': request_id,
                'product': product,
                'from_postal': data.get('from_postal'),
                'to_postal': data.get('to_postal'),
                'weight': weight,
                'weight_unit': data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT'),
                'dimension_unit': data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT'),
                'volume_weight': volume_weight,
                'chargeable_weight': chargeable_weight,
                'length': data.get('length'),
                'width': data.get('width'),
                'height': data.get('height'),
                'zone': zone,
                'base_fee': base_fee,
                'fuel_fee': fuel_surcharge,
                'total_fee': total_fee,
                'currency': product.currency,
                'status': 'success'
            }
            
            # 保存计算结果
            calculation = self.save_calculation(calculation_data)
            
            # 构建明细信息
            details = []
            for surcharge in surcharges:
                if not isinstance(surcharge, dict):
                    continue
                details.append({
                    'calculation': calculation,
                    'charge_type': 'SURCHARGE',
                    'charge_name': surcharge.get('name', '未知附加费'),
                    'amount': surcharge.get('amount', 0),
                    'condition': surcharge.get('condition', '')
                })
            
            # 添加基础运费明细
            if calculation:
                details.append({
                    'calculation': calculation,
                    'charge_type': 'BASE',
                    'charge_name': '基础运费',
                    'amount': base_fee,
                    'condition': f'计费重量: {chargeable_weight} {data.get("weight_unit", "KG")}'
                })
                
                # 添加燃油费明细
                details.append({
                    'calculation': calculation,
                    'charge_type': 'FUEL',
                    'charge_name': '燃油附加费',
                    'amount': fuel_surcharge,
                    'condition': f'燃油费率: {fuel_rate}%'
                })
            
            # 返回结果
            result = {
                'request_id': request_id,
                'from_postal': data.get('from_postal'),
                'to_postal': data.get('to_postal'),
                'product_code': product.product_id,
                'product_name': product.product_name,
                'weight': str(weight),
                'weight_unit': data.get('weight_unit', 'KG'),
                'volume_weight': str(volume_weight),
                'chargeable_weight': str(chargeable_weight),
                'zone': zone,
                'base_charge': str(base_fee),
                'fuel_surcharge': str(fuel_surcharge),
                'total_charge': str(total_fee),
                'currency': product.currency,
                'calculation_details': [
                    {
                        'step': '费用明细记录',
                        'description': '费用明细列表',
                        'fee_type': 'BASE',
                        'fee_name': '基础运费',
                        'amount': base_fee,
                        'currency': product.currency,
                        'unit_price': base_fee / chargeable_weight if chargeable_weight > 0 else Decimal('0'),
                        'weight_used': chargeable_weight,
                        'rate': '1.0',
                        'zone': zone,
                        'condition': f'计费重量: {chargeable_weight} {data.get("weight_unit") or get_setting("DEFAULT_WEIGHT_UNIT")}'
                    }
                ]
            }
            
            # 更新结果ID
            result['calculation_id'] = str(calculation.id) if calculation else ''
            
            # 添加计算详情
            if calculation and not result.get('calculation_details'):
                details_list = []
                base_detail = {
                    'step': '基础运费',
                    'description': '根据重量和区域计算基础运费',
                    'fee_type': 'BASE',
                    'fee_name': '基础运费',
                    'amount': base_fee,
                    'currency': product.currency,
                    'unit_price': base_fee / chargeable_weight if chargeable_weight > 0 else Decimal('0'),
                    'weight_used': chargeable_weight,
                    'rate': '1.0',
                    'zone': zone
                }
                details_list.append(base_detail)
                
                # 添加燃油附加费
                if fuel_surcharge > 0:
                    fuel_detail = {
                        'step': '燃油附加费',
                        'description': '根据燃油费率计算燃油附加费',
                        'fee_type': 'FUEL',
                        'fee_name': '燃油附加费',
                        'amount': fuel_surcharge,
                        'currency': product.currency,
                        'unit_price': Decimal('0'),
                        'weight_used': chargeable_weight,
                        'rate': str(fuel_rate),
                        'zone': zone
                    }
                    details_list.append(fuel_detail)
                
                # 添加其他附加费
                for surcharge in surcharges:
                    surcharge_detail = {
                        'step': surcharge.get('charge_name', '附加费'),
                        'description': surcharge.get('description', ''),
                        'fee_type': surcharge.get('charge_type', 'OTHER'),
                        'fee_name': surcharge.get('charge_name', '附加费'),
                        'amount': Decimal(str(surcharge.get('amount', '0'))),
                        'currency': product.currency,
                        'unit_price': Decimal('0'),
                        'weight_used': chargeable_weight,
                        'rate': str(surcharge.get('rate', '0')),
                        'zone': zone
                    }
                    details_list.append(surcharge_detail)
                
                result['calculation_details'] = details_list
                
            # 添加步骤描述
            if not result.get('steps'):
                result['steps'] = [
                    {
                        'step': '基本信息',
                        'description': '计算请求的基本参数',
                        'details': f'''
                            产品ID: {product.product_id}
                            起始邮编: {data.get('from_postal')}
                            目的邮编: {data.get('to_postal')}
                            重量: {weight} {data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                            尺寸: {data.get('length', '0.00')}x{data.get('width', '0.00')}x{data.get('height', '0.00')} {data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT')}
                            计算日期: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}
                            '''
                    },
                    {
                        'step': '重量计算',
                        'description': '计算体积重和计费重量',
                        'details': f'''
                            实际重量: {weight} {data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                            体积重量: {volume_weight} {data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                            计费重量: {chargeable_weight} {data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT')}
                            '''
                    },
                    {
                        'step': '基础运费计算',
                        'description': '计算基础运费',
                        'details': f'''
                            费用类型: 基础运费
                            金额: {base_fee}
                            区域: {zone}
                            '''
                    },
                    {
                        'step': '燃油附加费计算',
                        'description': '根据燃油费率计算燃油附加费',
                        'details': f'''
                            费用名称: 燃油附加费
                            金额: {fuel_surcharge}
                            '''
                    },
                    {
                        'step': '费用汇总',
                        'description': '计算总费用',
                        'details': f'''
                            基础运费: {base_fee}
                            燃油附加费: {fuel_surcharge}
                            总费用: {total_fee} {product.currency}
                            计算公式: 总费用 = 基础运费 + 燃油附加费 + 其他附加费总和
                            '''
                    }
                ]
            
            return result
            
        except Exception as e:
            logger.error(f"保存计算结果出错: {str(e)}")
            # 出错时返回基本结果
            return {
                'request_id': generate_request_id('CALC'),
                'from_postal': data.get('from_postal'),
                'to_postal': data.get('to_postal'),
                'product_code': product.product_id,
                'product_name': product.product_name,
                'weight': str(weight),
                'weight_unit': data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT'),
                'volume_weight': str(volume_weight),
                'chargeable_weight': str(chargeable_weight),
                'zone': zone,
                'base_charge': str(base_fee),
                'fuel_surcharge': str(fuel_surcharge),
                'total_charge': str(total_fee),
                'currency': product.currency,
                'error': str(e)
            }

    def save_calculation(self, calculation_data):
        """
        保存计算结果
        """
        try:
            from apps.calculator.models import Calculation, CalculationDetail
            
            # 创建计算记录对象
            calculation_fields = {
                'request_id': calculation_data.get('request_id'),
                'product': calculation_data.get('product'),
                'from_postal': calculation_data.get('from_postal'),
                'to_postal': calculation_data.get('to_postal'),
                'weight': calculation_data.get('weight'),
                'volume_weight': calculation_data.get('volume_weight'),
                'chargeable_weight': calculation_data.get('chargeable_weight'),
                'length': calculation_data.get('length'),
                'width': calculation_data.get('width'),
                'height': calculation_data.get('height'),
                'zone': calculation_data.get('zone'),
                'base_fee': calculation_data.get('base_fee'),
                'fuel_fee': calculation_data.get('fuel_fee'),
                'total_fee': calculation_data.get('total_fee'),
                'currency': calculation_data.get('currency'),
                'weight_unit': calculation_data.get('weight_unit') or get_setting('DEFAULT_WEIGHT_UNIT'),
                'dimension_unit': calculation_data.get('dimension_unit') or get_setting('DEFAULT_DIMENSION_UNIT')
            }
            
            # 创建并保存计算结果
            calculation = Calculation(**calculation_fields)
            calculation.save()
            print(f"计算结果已保存，ID: {calculation.id}", file=sys.stdout)
            
            # 保存明细记录
            details = calculation_data.get('details', [])
            for detail in details:
                detail_fields = {
                    'calculation': calculation,
                    'fee_type': detail.get('charge_type', 'OTHER'),
                    'fee_name': detail.get('charge_name', '其他费用'),
                    'amount': detail.get('amount', Decimal('0')),
                    'calculation_formula': detail.get('condition', '')
                }
                if hasattr(CalculationDetail, 'weight_used'):
                    detail_fields['weight_used'] = detail.get('weight_used')
                if hasattr(CalculationDetail, 'rate'):
                    detail_fields['rate'] = detail.get('rate')
                if hasattr(CalculationDetail, 'unit_price'):
                    detail_fields['unit_price'] = detail.get('unit_price')
                if hasattr(CalculationDetail, 'zone_info'):
                    detail_fields['zone_info'] = detail.get('zone_info')
                    
                detail_obj = CalculationDetail(**detail_fields)
                detail_obj.save()
                print(f"计算明细已保存: {detail_obj.fee_name}", file=sys.stdout)
            
            return calculation
        except Exception as e:
            print(f"保存计算结果出错: {str(e)}", file=sys.stdout)
            self.logger.error(f"保存计算结果出错: {str(e)}")
            return None

    def _get_rate_from_table(self, product, weight_point, chargeable_weight, zone):
        """
        从费率表获取基础价格
        
        Args:
            product: 产品对象
            weight_point: 重量点
            chargeable_weight: 计费重量
            zone: 区域
            
        Returns:
            Decimal: 基础价格
        """
        try:
            # 从区域获取分区号码
            zone_num = zone.replace('ZONE', '')
            if not zone_num:
                print(f"不支持的区域格式: {zone}", file=sys.stdout)
                return Decimal('0')

            print(f"\n========== 从费率表获取价格 ==========", file=sys.stdout)
            print(f"产品: {product.product_id}, 重量点: {weight_point.weight}, 区域: {zone}", file=sys.stdout)
            print(f"计费重量: {chargeable_weight}", file=sys.stdout)
            
            # 尝试从raw_data字段获取价格信息
            base_rate = None
            raw_data_price_source = None
            
            # 直接使用BaseFee的get_price方法
            print(f"直接调用BaseFee.get_price方法获取价格...", file=sys.stdout)
            try:
                # 确保使用正确的区域格式
                price = weight_point.get_price(zone_num)
                if price and price > 0:
                    print(f"从BaseFee.get_price获取价格成功: {price}", file=sys.stdout)
                    base_rate = price
                else:
                    print(f"从BaseFee.get_price获取价格为空或为零，将继续尝试其他方法", file=sys.stdout)
            except Exception as e:
                print(f"调用BaseFee.get_price时出错: {str(e)}", file=sys.stdout)

            # 如果get_price方法没有返回有效值，则尝试手动解析raw_data
            if base_rate is None or base_rate <= 0:
                if hasattr(weight_point, 'raw_data') and weight_point.raw_data:
                    print(f"尝试从raw_data获取价格信息...", file=sys.stdout)
                    try:
                        raw_data = weight_point.raw_data
                        if isinstance(raw_data, str):
                            # 导入json模块
                            import json
                            raw_data = json.loads(raw_data)
                            print(f"raw_data解析成功 (JSON字符串)", file=sys.stdout)
                        else:
                            print(f"raw_data已是字典格式", file=sys.stdout)

                        # 打印完整的raw_data内容，用于调试
                        print(f"raw_data完整内容:", file=sys.stdout)
                        for k, v in raw_data.items():
                            print(f"  {k}: {v}", file=sys.stdout)

                        # 尝试从raw_data中提取价格 - 检查多种可能的键名
                        possible_keys = [
                            f"Zone{zone_num}基础价格",
                            f"zone{zone_num}基础价格",
                            f"Zone{zone_num}",
                            f"zone{zone_num}",
                            f"ZONE{zone_num}",
                            zone,  # 完整的区域名称，如"ZONE8"
                            str(zone_num),  # 仅区域数字，如"8"
                            f"zone{zone_num}_price"
                        ]

                        print(f"尝试以下键名: {possible_keys}", file=sys.stdout)
                        for key in possible_keys:
                            if key in raw_data:
                                try:
                                    value = raw_data[key]
                                    # 检查值是否为None或空字符串
                                    if value is None or (isinstance(value, str) and not value.strip()):
                                        print(f"键 {key} 存在但值为空", file=sys.stdout)
                                        continue
                                        
                                    base_rate = Decimal(str(value))
                                    raw_data_price_source = key
                                    print(f"在raw_data中找到价格: 键名={key}, 价格={base_rate}", file=sys.stdout)
                                    break
                                except (ValueError, TypeError, InvalidOperation) as e:
                                    print(f"尝试将 {key}={raw_data[key]} 转换为Decimal时出错: {str(e)}", file=sys.stdout)

                        # 如果未找到，检查所有键值对
                        if not raw_data_price_source:
                            print(f"未通过关键字匹配找到价格，检查所有键值对...", file=sys.stdout)
                            for key, value in raw_data.items():
                                print(f"检查键值对: {key}: {value}", file=sys.stdout)
                                # 检查键名是否包含区域号或区域名
                                if (zone.lower() in key.lower() or 
                                    zone_num in key or 
                                    f"zone{zone_num}".lower() in key.lower()):
                                    try:
                                        # 检查值是否为None或空字符串
                                        if value is None or (isinstance(value, str) and not value.strip()):
                                            print(f"键 {key} 匹配但值为空", file=sys.stdout)
                                            continue
                                            
                                        base_rate = Decimal(str(value))
                                        raw_data_price_source = key
                                        print(f"通过键名匹配找到价格: {key}={base_rate}", file=sys.stdout)
                                        break
                                    except (ValueError, TypeError, InvalidOperation) as e:
                                        print(f"尝试将 {key}={value} 转换为Decimal时出错: {str(e)}", file=sys.stdout)

                    except Exception as e:
                        print(f"解析raw_data失败: {str(e)}", file=sys.stdout)
                        print(f"原始raw_data: {weight_point.raw_data}", file=sys.stdout)

            # 如果从raw_data获取失败，尝试zone_prices
            if (base_rate is None or base_rate <= 0) and hasattr(weight_point, 'zone_prices') and weight_point.zone_prices:
                print(f"尝试从zone_prices获取价格...", file=sys.stdout)
                try:
                    zone_key = f"zone{zone_num}"
                    if zone_key in weight_point.zone_prices:
                        value = weight_point.zone_prices[zone_key]
                        if value is not None:
                            base_rate = Decimal(str(value))
                            print(f"从zone_prices[{zone_key}]获取到基础价格: {base_rate}", file=sys.stdout)
                    
                    if base_rate is None or base_rate <= 0:
                        print(f"zone_prices内容:", file=sys.stdout)
                        for zone_key, price in weight_point.zone_prices.items():
                            print(f"  {zone_key}: {price}", file=sys.stdout)
                except Exception as e:
                    print(f"从zone_prices获取价格失败: {str(e)}", file=sys.stdout)

            # 获取单位价格
            unit_rate = Decimal('0')
            if hasattr(weight_point, 'get_unit_price'):
                try:
                    unit_rate = weight_point.get_unit_price(zone_num)
                    print(f"单位价格: {unit_rate}", file=sys.stdout)

                    if hasattr(weight_point, 'zone_unit_prices') and weight_point.zone_unit_prices:
                        print(f"zone_unit_prices内容:", file=sys.stdout)
                        for zone_key, price in weight_point.zone_unit_prices.items():
                            print(f"  {zone_key}: {price}", file=sys.stdout)
                except Exception as e:
                    print(f"获取单位价格失败: {str(e)}", file=sys.stdout)

            # 如果基础价格为0或没有获取到，直接返回0
            if base_rate is None or base_rate <= 0:
                print(f"警告: 没有找到有效的基础价格，返回0", file=sys.stdout)
                return Decimal('0')

            # 根据计价类型计算费用
            if hasattr(weight_point, 'fee_type') and weight_point.fee_type == 'STEP':
                print(f"计算公式: 阶梯式计价 - 直接使用基础价格: {base_rate}", file=sys.stdout)
                return base_rate
            else:
                # 线性计价，基础价格 + 超出部分的重量 * 单价
                excess_weight = max(Decimal('0'), chargeable_weight - weight_point.weight)
                final_fee = (base_rate + excess_weight * unit_rate)
                print(f"计算公式: 线性计价 - 基础价格({base_rate}) + 超出重量({excess_weight}) * 单价({unit_rate}) = {final_fee}", file=sys.stdout)
                print(f"数据来源: {'raw_data' if raw_data_price_source else 'zone_prices'}", file=sys.stdout)
                if raw_data_price_source:
                    print(f"raw_data键名: {raw_data_price_source}", file=sys.stdout)
                return final_fee

        except Exception as e:
            print(f"从费率表获取价格失败: {str(e)}", file=sys.stdout)
            # 这里只记录日志，不抛出异常，允许尝试其他方法获取价格
            return Decimal('0') 