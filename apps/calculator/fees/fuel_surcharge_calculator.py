"""
燃油附加费计算模块
负责计算不同产品的燃油附加费
"""
import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
import logging
import sys
import json
import inspect

from django.utils import timezone
from django.db import connection
from django.conf import settings

from apps.products.models import Product
from apps.fuel_rates.models import FuelRate
from apps.core.config import get_setting
logger = logging.getLogger(__name__)

class FuelSurchargeCalculator:
    """燃油附加费计算器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_fuel_surcharge(self, 
                              product: Product, 
                              calculation_data: Dict[str, Any],
                              base_freight: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        计算燃油附加费
        
        Args:
            product: 产品对象
            calculation_data: 计算数据
            base_freight: 基础运费
            
        Returns:
            Dict: 计算结果，包含燃油附加费
        """
        try:
            print("\n========== 开始计算燃油附加费 ==========", file=sys.stdout)
            print(f"产品: {product.product_id} ({product.product_name})", file=sys.stdout)
            print(f"区域: {calculation_data.get('zone', '')}", file=sys.stdout)
            
            # 检查FuelSurchargeCalculator类是否有最低燃油费设置(检查所有属性)
            print("\n【检查隐藏设置】检查FuelSurchargeCalculator类的属性:", file=sys.stdout)
            for attr_name in dir(self):
                if not attr_name.startswith('_') and not callable(getattr(self, attr_name, None)):
                    print(f"  属性: {attr_name} = {getattr(self, attr_name)}", file=sys.stdout)
            
            # 检查calculation_data是否包含最低燃油费设置
            print(f"\n【检查输入数据】calculation_data内容:", file=sys.stdout)
            for key, value in calculation_data.items():
                print(f"  {key}: {value}", file=sys.stdout)
            
            # 检查产品对象是否有最低燃油费设置
            print(f"\n【检查产品设置】产品对象属性:", file=sys.stdout)
            for attr_name in dir(product):
                if not attr_name.startswith('_') and not callable(getattr(product, attr_name, None)):
                    attr_value = getattr(product, attr_name, None)
                    if isinstance(attr_value, (str, int, float, bool, Decimal)) or attr_value is None:
                        print(f"  {attr_name}: {attr_value}", file=sys.stdout)
            
            # 检查config字段
            if hasattr(product, 'config'):
                print(f"\n【重要配置检查】产品config:", file=sys.stdout)
                try:
                    if isinstance(product.config, str):
                        config = json.loads(product.config)
                    else:
                        config = product.config
                    
                    if isinstance(config, dict):
                        for key, value in config.items():
                            print(f"  {key}: {value}", file=sys.stdout)
                except Exception as e:
                    print(f"  解析config失败: {str(e)}", file=sys.stdout)
            
            # 直接检查数据库中的其他燃油费率设置字段
            print(f"\n【数据库检查】查询所有燃油费率表字段:", file=sys.stdout)
            with connection.cursor() as cursor:
                cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'fuel_rates'")
                columns = [row[0] for row in cursor.fetchall()]
                print(f"  燃油费率表字段: {columns}", file=sys.stdout)
                
                # 尝试查找min_amount相关字段
                min_amount_fields = [col for col in columns if 'min' in col.lower()]
                if min_amount_fields:
                    print(f"  发现可能的最低金额字段: {min_amount_fields}", file=sys.stdout)
                
                # 检查是否有自定义字段
                cursor.execute("SELECT * FROM fuel_rates LIMIT 1")
                if cursor.description:
                    field_names = [desc[0] for desc in cursor.description]
                    print(f"  实际数据字段: {field_names}", file=sys.stdout)
                    
                    # 查找所有记录的min_amount字段
                    min_fields = [field for field in field_names if 'min' in field.lower()]
                    if min_fields:
                        fields_str = ', '.join(min_fields)
                        cursor.execute(f"SELECT rate_id, rate_value, {fields_str} FROM fuel_rates WHERE is_deleted = 0")
                        for row in cursor.fetchall():
                            print(f"  记录ID={row[0]}, 费率={row[1]}%, 最低值字段={row[2:]}", file=sys.stdout)
            
            calculation_date = calculation_data.get('calculation_date')
            if not calculation_date:
                calculation_date = timezone.now().date()
            print(f"计算日期: {calculation_date}", file=sys.stdout)
            
            # 获取燃油附加费率
            base_fuel_rate = self._get_fuel_surcharge_rate(product, calculation_date)
            if not base_fuel_rate:
                error_msg = f"未找到产品 {product.product_id} 在 {calculation_date} 的燃油附加费率"
                print(error_msg, file=sys.stdout)
                raise ValueError(error_msg)
            
            # 如果没有基础运费，则无法计算燃油附加费
            if not base_freight:
                print(f"未提供基础运费，无法计算燃油附加费", file=sys.stdout)
                return {'type': '燃油附加费', 'name': '燃油附加费', 'amount': '0.00', 'rate': f"{base_fuel_rate}%"}
            
            # 打印基础运费详情
            print(f"\n【基础运费详情】:", file=sys.stdout)
            for key, value in base_freight.items():
                print(f"  {key}: {value}", file=sys.stdout)
            
            base_amount = Decimal(base_freight.get('amount', '0'))
            print(f"基础运费金额: {base_amount}", file=sys.stdout)
            
            # 获取燃油费率
            fuel_rate = Decimal('0')
            fuel_rate_record = self._get_fuel_rate(product, calculation_data, calculation_date)
            if fuel_rate_record:
                fuel_rate = Decimal(str(fuel_rate_record.rate_value)) / 100
                print(f"找到燃油费率: {fuel_rate_record.rate_value}%", file=sys.stdout)
            else:
                # 使用配置的燃油费率
                default_rate = get_setting('DEFAULT_FUEL_RATE', 0)
                fuel_rate = Decimal(str(default_rate)) / 100
                print(f"未找到燃油费率，使用配置值: {default_rate}%", file=sys.stdout)
            
            # 正常计算燃油附加费，基于基础运费和费率
            fuel_amount = base_amount * fuel_rate
            print(f"计算的燃油附加费: {fuel_amount} (基础运费 {base_amount} * 燃油费率 {fuel_rate * 100:.2f}%)", file=sys.stdout)
            
            # 检查是否有任何地方设置最低燃油费
            min_fuel_amount = None
            # 1. 检查产品config
            if hasattr(product, 'config') and isinstance(product.config, dict) and 'min_fuel_amount' in product.config:
                min_fuel_amount = Decimal(str(product.config['min_fuel_amount']))
                print(f"从产品config获取到最低燃油费: {min_fuel_amount}", file=sys.stdout)
            
            # 2. 检查是否有程序内部设置的最低值
            if fuel_amount == Decimal('0') and base_amount == Decimal('0'):
                print(f"警告: 基础运费为0，计算出的燃油附加费也为0", file=sys.stdout)
            
            # 检查是否有最低值的设置影响计算
            print(f"当前计算值为{fuel_amount}，检查是否存在最低值设置", file=sys.stdout)
            
            # 检查是否在任何地方有最低燃油费
            if base_amount == Decimal('0') and fuel_amount > Decimal('0'):
                print(f"【严重异常】基础运费为0但燃油附加费不为0！", file=sys.stdout)
                
                # 尝试查找燃油费率记录中是否包含最低值设置
                special_rates = FuelRate.objects.filter(
                    provider__name=product.provider_name,
                    is_deleted=False
                ).order_by('-effective_date')
                
                print(f"查找到{special_rates.count()}个燃油费率记录:", file=sys.stdout)
                for rate in special_rates:
                    print(f"  ID={rate.rate_id}, 燃油费率={rate.rate_value}%, 生效日期={rate.effective_date}", file=sys.stdout)
                    # 尝试查找额外字段
                    for field in rate._meta.fields:
                        field_name = field.name
                        if 'min' in field_name.lower() or 'config' in field_name.lower() or 'extra' in field_name.lower():
                            field_value = getattr(rate, field_name, None)
                            print(f"    {field_name} = {field_value}", file=sys.stdout)
            
            # 格式化结果
            if fuel_amount == Decimal('0') and base_amount == Decimal('0'):
                # 如果基础运费为0，燃油附加费也应该为0
                fuel_amount = Decimal('0.00')
            
            fuel_amount = fuel_amount.quantize(Decimal('0.01'))
            
            # 四舍五入到美分
            fuel_amount = round(fuel_amount, 2)
            
            # 检查基础运费为0的情况 - 移到构建result之前
            if base_amount <= 0:
                print(f"【重要】基础运费小于等于0 (${base_amount})，强制将燃油附加费设为0", file=sys.stdout)
                fuel_amount = Decimal('0.00')
                print(f"基础运费为0，燃油附加费也设为0", file=sys.stdout)
            else:
                # 只有当基础运费大于0时，才考虑应用最低燃油费
                if min_fuel_amount and fuel_amount > 0 and fuel_amount < min_fuel_amount:
                    print(f"应用最低燃油费: {min_fuel_amount}", file=sys.stdout)
                    fuel_amount = min_fuel_amount
            
            # 再次确认燃油附加费为0当基础运费为0时
            if base_amount <= 0 and fuel_amount != Decimal('0.00'):
                print(f"【严重错误】基础运费为0但燃油附加费仍不为0！强制重置为0", file=sys.stdout)
                fuel_amount = Decimal('0.00')
            
            # 构建结果
            result = {
                'type': '燃油附加费',
                'name': '燃油附加费',
                'amount': str(fuel_amount),
                'rate': f"{fuel_rate * 100:.2f}%",
                'source_description': '根据基础运费和燃油费率计算'
            }
            
            # 再次确认result字典中的amount值
            if base_amount <= 0 and Decimal(result['amount']) != Decimal('0.00'):
                print(f"【严重错误】result中的amount值不为0！强制修正", file=sys.stdout)
                result['amount'] = '0.00'
            
            # 检查系统内部设置 - 本地变量
            local_vars = locals()
            print(f"\n【本地变量检查】:", file=sys.stdout)
            for var_name, var_value in local_vars.items():
                if var_name in ['fuel_amount', 'base_amount', 'fuel_rate', 'min_fuel_amount']:
                    print(f"  {var_name}: {var_value}", file=sys.stdout)
            
            if fuel_amount != Decimal('0') and base_amount == Decimal('0'):
                print(f"【严重警告】基础运费为0但燃油附加费不为0，可能是硬编码在其他地方！", file=sys.stdout)
            
            # 检查返回前燃油附加费是否被强制修改为特定值
            print(f"最终燃油附加费: {fuel_amount}", file=sys.stdout)
            print(f"最终result['amount']: {result['amount']}", file=sys.stdout)
            
            return result
        
        except ValueError as e:
            # 针对特定错误（如未找到费率）直接抛出异常
            self.logger.error(f"计算燃油附加费错误: {str(e)}")
            raise
        except Exception as e:
            print(f"计算燃油附加费错误: {str(e)}", file=sys.stdout)
            self.logger.error(f"计算燃油附加费错误: {str(e)}")
            raise ValueError(f"计算燃油附加费时发生错误: {str(e)}")
    
    def _get_calculation_date(self, data: Dict[str, Any]) -> datetime.date:
        """获取计算日期"""
        calculation_date = data.get('calculation_date')
        if not calculation_date:
            calculation_date = timezone.now().date()
        return calculation_date
    
    def _get_fuel_rate(self, 
                      product: Product, 
                      data: Dict[str, Any], 
                      calculation_date: datetime.date) -> Optional[FuelRate]:
        """
        获取燃油附加费率
        
        Args:
            product: 产品对象
            data: 输入数据
            calculation_date: 计算日期
            
        Returns:
            FuelRate: 燃油附加费率对象
        """
        try:
            # 获取服务商
            provider_id = getattr(product, 'provider_name', None)
            
            if not provider_id:
                print(f"产品 {product.product_id} 没有关联服务商，无法获取燃油附加费率", file=sys.stdout)
                return None
            
            print(f"【燃油费率查询】产品服务商={provider_id}, 计算日期={calculation_date}", file=sys.stdout)
            
            # 尝试获取适用的燃油附加费率
            fuel_rate = FuelRate.objects.filter(
                provider__name=provider_id,
                effective_date__lte=calculation_date,
                expiration_date__gte=calculation_date,
                is_deleted=False
            ).order_by('-effective_date').first()
            
            if fuel_rate:
                print(f"找到燃油附加费率记录:", file=sys.stdout)
                # 打印FuelRate对象的所有字段
                for field in fuel_rate._meta.fields:
                    field_name = field.name
                    field_value = getattr(fuel_rate, field_name, None)
                    print(f"  {field_name}: {field_value}", file=sys.stdout)
                
                # 检查是否有min_fuel_amount字段或min_amount字段
                has_min_amount = False
                if hasattr(fuel_rate, 'min_fuel_amount'):
                    print(f"  找到min_fuel_amount字段: {fuel_rate.min_fuel_amount}", file=sys.stdout)
                    has_min_amount = True
                if hasattr(fuel_rate, 'min_amount'):
                    print(f"  找到min_amount字段: {fuel_rate.min_amount}", file=sys.stdout)
                    has_min_amount = True
                
                if not has_min_amount:
                    print(f"  警告: 未找到最低燃油费字段", file=sys.stdout)
                    
                # 检查其他特殊字段
                if hasattr(fuel_rate, 'config') and fuel_rate.config:
                    print(f"  config字段: {fuel_rate.config}", file=sys.stdout)
                    if isinstance(fuel_rate.config, dict) and 'min_amount' in fuel_rate.config:
                        print(f"  在config中找到min_amount: {fuel_rate.config['min_amount']}", file=sys.stdout)
            else:
                print(f"未找到适用的燃油附加费率", file=sys.stdout)
            
            return fuel_rate
            
        except Exception as e:
            self.logger.error(f"获取燃油附加费率错误: {str(e)}")
            print(f"获取燃油附加费率错误: {str(e)}", file=sys.stdout)
            return None

    def _get_fuel_surcharge_rate(self, product: Product, calculation_date: datetime.date) -> Optional[float]:
        """
        获取燃油附加费率
        
        Args:
            product: 产品对象
            calculation_date: 计算日期
            
        Returns:
            float: 燃油附加费率(百分比)，如15.0表示15%
        """
        try:
            # 尝试从FuelRate表中获取
            fuel_rate = self._get_fuel_rate(product, {}, calculation_date)
            if fuel_rate:
                # 从FuelRate的rate_value字段获取费率值
                if hasattr(fuel_rate, 'rate_value'):
                    rate_value = float(fuel_rate.rate_value)
                    print(f"找到燃油附加费率: {rate_value}%", file=sys.stdout)
                    return rate_value
                else:
                    print(f"燃油附加费率记录缺少rate_value字段", file=sys.stdout)
                    return get_setting('DEFAULT_FUEL_RATE', 0)
            
            # 数据库中没有找到适用的费率
            return get_setting('DEFAULT_FUEL_RATE', 0)
            
        except Exception as e:
            print(f"获取燃油附加费率错误: {str(e)}", file=sys.stdout)
            self.logger.error(f"获取燃油附加费率错误: {str(e)}")
            return get_setting('DEFAULT_FUEL_RATE', 0) 