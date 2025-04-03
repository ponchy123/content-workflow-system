"""
运费计算系统主计算器
整合各模块功能，提供统一的计算接口
"""
from decimal import Decimal, ROUND_CEILING
from typing import Dict, Any, List, Optional
import logging
import sys

from django.utils import timezone

from apps.calculator.fees.surcharge_calculator import SurchargeCalculator
from apps.calculator.fees.base_freight_calculator import BaseFreightCalculator
from apps.calculator.fees.fuel_surcharge_calculator import FuelSurchargeCalculator
from apps.products.models import Product
from apps.core.utils import (
    generate_request_id,
    validate_calculation_input,
    calculate_volume_weight,
    calculate_chargeable_weight,
    preprocess_calculation_data
)
from apps.calculator.models import Calculation, CalculationDetail
from django.db import transaction
from apps.calculator.services.base_calculation_service import BaseCalculationService
from apps.core.config import get_setting

logger = logging.getLogger(__name__)

class Calculator:
    """运费计算器主类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # 初始化各计算器组件
        self.surcharge_calculator = SurchargeCalculator()
        self.base_freight_calculator = BaseFreightCalculator()
        self.fuel_surcharge_calculator = FuelSurchargeCalculator()
    
    def calculate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        计算运费
        
        Args:
            data: 计算请求数据，包含以下字段:
                - product_id: 产品ID
                - weight: 重量
                - length: 长(可选)
                - width: 宽(可选)
                - height: 高(可选)
                - from_postal: 始发邮编
                - to_postal: 目的邮编
                - is_residential: 是否住宅地址(可选)
                - calculation_date: 计算日期(可选)
                - dimension_unit: 尺寸单位(CM/IN)
                - weight_unit: 重量单位(KG/LB)
        
        Returns:
            Dict[str, Any]: 计算结果
        """
        try:
            # 输出计算开始信息
            print("\n========== 开始运费计算 ==========", file=sys.stdout)
            print(f"输入数据: {data}", file=sys.stdout)
            
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
            dimension_unit = data.get('dimension_unit', 'CM')
            weight_unit = data.get('weight_unit', 'KG')
            
            # 预处理数据
            processed_data, _ = preprocess_calculation_data(data)
            data.update(processed_data)
            
            # 获取产品信息
            product = self._get_product(product_id)
            
            # 单位转换常量
            CM_TO_IN = Decimal('2.54')  # 1 inch = 2.54 cm
            KG_TO_LB = Decimal('2.20462')  # 1 kg = 2.20462 lbs
            
            # 尺寸单位转换（向上取整）
            if dimension_unit != product.dim_unit:
                if dimension_unit == 'CM' and product.dim_unit == 'IN':
                    length = Decimal(str(length / CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                    width = Decimal(str(width / CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                    height = Decimal(str(height / CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                elif dimension_unit == 'IN' and product.dim_unit == 'CM':
                    length = Decimal(str(length * CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                    width = Decimal(str(width * CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                    height = Decimal(str(height * CM_TO_IN)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                print(f"尺寸单位转换: {data.get('length')}x{data.get('width')}x{data.get('height')} {dimension_unit} -> "
                      f"{length}x{width}x{height} {product.dim_unit}", file=sys.stdout)
            
            # 重量单位转换（向上取整）
            if weight_unit != product.weight_unit:
                if weight_unit == 'KG' and product.weight_unit == 'LB':
                    weight = Decimal(str(weight * KG_TO_LB)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                elif weight_unit == 'LB' and product.weight_unit == 'KG':
                    weight = Decimal(str(weight / KG_TO_LB)).quantize(Decimal('1'), rounding=ROUND_CEILING)
                print(f"重量单位转换: {data.get('weight')} {weight_unit} -> {weight} {product.weight_unit}", 
                      file=sys.stdout)
            
            # 使用250作为FedEx Ground的体积重系数
            dim_factor = Decimal('250') if product.code == 'FEDEX_GROUND' else Decimal('6000')
            
            # 计算体积重（使用转换后的尺寸，向上取整）
            volume_weight = Decimal(str((length * width * height) / dim_factor)).quantize(
                Decimal('1'), 
                rounding=ROUND_CEILING
            )
            
            # 计算计费重量（取较大值，向上取整）
            chargeable_weight = max(weight, volume_weight).quantize(
                Decimal('1'), 
                rounding=ROUND_CEILING
            )
            
            print(f"体积重计算: ({length} x {width} x {height}) / {dim_factor} = {volume_weight} {product.weight_unit}", 
                  file=sys.stdout)
            print(f"计费重量确定: max({weight}, {volume_weight}) = {chargeable_weight} {product.weight_unit}", 
                  file=sys.stdout)
            
            # 更新计算数据
            calculation_data = {
                **data,
                'weight': weight,
                'length': length,
                'width': width,
                'height': height,
                'volume_weight': volume_weight,
                'chargeable_weight': chargeable_weight,
                'dimension_unit': product.dim_unit,
                'weight_unit': product.weight_unit
            }
            
            # 获取分区信息
            zone = self._get_zone(product, data.get('from_postal'), data.get('to_postal'))
            calculation_data['zone'] = zone
            
            # 计算基础运费
            base_freight = self.base_freight_calculator.calculate_base_freight(product, calculation_data)
            if not base_freight:
                raise ValueError(f"无法计算基础运费，请检查产品 {product_id} 在区域 {zone} 的费率设置")
            
            # 计算燃油附加费
            fuel_surcharge = self.fuel_surcharge_calculator.calculate_fuel_surcharge(
                product, 
                calculation_data,
                base_freight
            )
            
            # 计算其他附加费
            surcharges = self.surcharge_calculator.calculate_surcharges(product, calculation_data)
            
            # 计算总费用
            base_amount = Decimal(base_freight.get('amount', '0'))
            fuel_amount = Decimal(fuel_surcharge.get('amount', '0'))
            surcharge_total = sum(Decimal(s.get('amount', '0')) for s in surcharges)
            
            total_amount = base_amount + fuel_amount + surcharge_total
            
            # 收集包裹不符合规范的原因
            unauthorized_package_exists = False
            unauthorized_reasons = []
            
            for surcharge in surcharges:
                if '不可发包裹' in surcharge.get('type', '') or 'Unauthorized' in surcharge.get('type', ''):
                    unauthorized_package_exists = True
                    unauthorized_reasons.append(surcharge.get('condition', ''))
            
            # 生成请求ID
            request_id = generate_request_id('CALC')
                
            # 构建返回结果
            result = {
                'request_id': request_id,
                'product_code': product.product_id,
                'product_name': product.product_name,
                'chargeable_weight': str(chargeable_weight),
                'volume_weight': str(volume_weight),
                'base_fee': str(base_amount),
                'fuel_surcharge': str(fuel_amount),
                'surcharges': surcharges,
                'total_fee': str(total_amount),
                'currency': product.currency,
                'zone': zone,
                'remote_level': None,
                'destination_info': {
                    'zone': zone,
                    'remote_level': None,
                    'remote_area': False
                },
                'unauthorized_package': unauthorized_package_exists,
                'unauthorized_reasons': unauthorized_reasons if unauthorized_package_exists else [],
                'calculation_details': []
            }
            
            print("\n========== 计算完成 ==========", file=sys.stdout)
            print(f"总费用: {total_amount} {product.currency}", file=sys.stdout)
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算失败: {str(e)}")
            print(f"计算失败: {str(e)}", file=sys.stdout)
            raise
    
    def _get_product(self, product_id: str) -> Product:
        """获取产品信息"""
        try:
            return Product.objects.get(product_id=product_id, status=True)
        except Product.DoesNotExist:
            raise ValueError(f"产品不存在: {product_id}")
    
    def _get_zone(self, product: Product, from_postal: str, to_postal: str) -> str:
        """获取区域信息"""
        # 从输入的data参数中获取zone信息
        # 这是在calculate方法中传入的，但在这里无法直接访问
        # 因此，我们需要修改方法调用，直接读取data中的zone
        # 临时解决方案：从to_postal参数推断zone
        if hasattr(self, 'current_data') and isinstance(self.current_data, dict) and 'zone' in self.current_data:
            zone = self.current_data.get('zone')
        else:
            # 从数据库查询区域
            service = BaseCalculationService()
            zone = service._get_zone(from_postal, to_postal)
        
        # 确保格式正确（大写且以ZONE开头）
        if isinstance(zone, str) and zone:
            zone = zone.upper()
            if not zone.startswith('ZONE'):
                zone = f"ZONE{zone}"
        
        return zone
    
    def _get_remote_level(self, product: Product, from_postal: str, to_postal: str) -> Optional[int]:
        """获取偏远地区等级"""
        # 这里简化处理，实际应从RemoteArea表查询
        # 如果不是偏远地区，返回None
        # 如果是偏远地区，返回偏远等级(1-3)
        return None  # 示例返回值
    
    def _save_calculation_result(self, data: Dict[str, Any], product: Product,
                               chargeable_weight: Decimal, volume_weight: Decimal,
                               base_freight: Optional[Dict], fuel_surcharge: Optional[Dict],
                               surcharges: List[Dict], total_fee: Decimal,
                               zone: str) -> Calculation:
        """保存计算结果"""
        try:
            # 生成唯一请求ID
            request_id = generate_request_id('CALC')
            
            # 基础运费金额
            base_amount = Decimal(base_freight.get('amount', '0')) if base_freight else Decimal('0')
            
            # 燃油附加费金额
            fuel_amount = Decimal(fuel_surcharge.get('amount', '0')) if fuel_surcharge else Decimal('0')
            
            # 创建计算结果
            calculation_data = {
                'request_id': request_id,
                'from_postal': data.get('from_postal', ''),
                'to_postal': data.get('to_postal', ''),
                'weight': data.get('weight', 0),
                'base_fee': base_amount,
                'fuel_fee': fuel_amount,
                'total_fee': total_fee,
                'currency': product.currency,
                'status': 'SUCCESS',
                'product_id': product.product_id
            }
            
            # 收集明细记录
            detail_records = []
            
            # 添加基础运费明细
            if base_freight:
                detail_records.append({
                    'fee_type': '基础运费',
                    'fee_name': base_freight.get('name', '基础运费'),
                    'amount': base_freight.get('amount', '0'),
                    'weight_used': chargeable_weight,
                    'calculation_formula': f"根据{zone}区域费率计算，计费重量{chargeable_weight}kg"
                })
            
            # 添加燃油附加费明细
            if fuel_surcharge:
                detail_records.append({
                    'fee_type': '燃油附加费',
                    'fee_name': fuel_surcharge.get('name', '燃油附加费'),
                    'amount': fuel_surcharge.get('amount', '0'),
                    'calculation_formula': fuel_surcharge.get('condition', '')
                })
            
            # 添加其他附加费明细
            for surcharge in surcharges:
                detail_records.append({
                    'fee_type': surcharge.get('type', '附加费'),
                    'fee_name': surcharge.get('name', '附加费'),
                    'amount': surcharge.get('amount', '0'),
                    'calculation_formula': surcharge.get('condition', '')
                })
            
            # 使用事务保存数据
            with transaction.atomic():
                # 创建计算结果
                calculation = Calculation.objects.create(**calculation_data)
                
                # 批量创建明细记录
                detail_objects = []
                for detail in detail_records:
                    detail_obj = CalculationDetail(
                        calculation=calculation,
                        fee_type=detail['fee_type'],
                        fee_name=detail['fee_name'],
                        amount=detail['amount']
                    )
                    
                    # 添加可选字段
                    if 'weight_used' in detail and detail['weight_used'] is not None:
                        detail_obj.weight_used = detail['weight_used']
                    
                    if 'calculation_formula' in detail and detail['calculation_formula']:
                        detail_obj.calculation_formula = detail['calculation_formula']
                    
                    detail_objects.append(detail_obj)
                
                # 批量创建明细记录
                if detail_objects:
                    CalculationDetail.objects.bulk_create(detail_objects)
            
            return calculation
            
        except Exception as e:
            self.logger.error(f"保存计算结果失败: {str(e)}")
            raise
    
    def _get_calculation_details(self, calculation: Calculation) -> List[Dict]:
        """获取计算明细，包括计算过程的详细步骤"""
        try:
            # 从数据库获取详细记录
            db_details = CalculationDetail.objects.filter(
                calculation=calculation
            ).values('fee_type', 'fee_name', 'amount', 'weight_used', 'calculation_formula')
            
            calculation_steps = []
            
            # 安全获取属性的辅助函数
            def get_attr_safe(obj, attr_name, default="未提供"):
                return getattr(obj, attr_name, default) if hasattr(obj, attr_name) else default
            
            # 1. 基本信息
            calculation_steps.append({
                'step': '基本信息',
                'description': '计算请求的基本参数',
                'details': f"""
                产品ID: {calculation.product.product_id if hasattr(calculation, 'product') else 'N/A'}
                产品名称: {calculation.product.product_name if hasattr(calculation, 'product') else 'N/A'}
                重量: {get_attr_safe(calculation, 'weight', 0)}
                从: {get_attr_safe(calculation, 'from_postal', '')}
                到: {get_attr_safe(calculation, 'to_postal', '')}
                """
            })
            
            # 2. 基础运费计算
            base_fee_detail = next((d for d in db_details if '基础运费' in d['fee_type']), None)
            if base_fee_detail:
                calculation_steps.append({
                    'step': '基础运费计算',
                    'description': '根据重量和目的地计算基本运费',
                    'details': f"""
                    费用名称: {base_fee_detail['fee_name']}
                    金额: {base_fee_detail['amount']}
                    计费重量: {base_fee_detail.get('weight_used', 0)}
                    计算公式: {base_fee_detail.get('calculation_formula', '根据费率表计算')}
                    """
                })
            
            # 3. 燃油费计算
            fuel_fee_detail = next((d for d in db_details if '燃油' in d['fee_type']), None)
            if fuel_fee_detail:
                calculation_steps.append({
                    'step': '燃油附加费计算',
                    'description': '根据燃油费率计算燃油附加费',
                    'details': f"""
                    费用名称: {fuel_fee_detail['fee_name']}
                    金额: {fuel_fee_detail['amount']}
                    计算公式: {fuel_fee_detail.get('calculation_formula', '基础运费 × 燃油费率')}
                    """
                })
            
            # 4. 其他附加费
            other_fees = [d for d in db_details if '基础运费' not in d['fee_type'] and '燃油' not in d['fee_type']]
            if other_fees:
                surcharge_details = "\n".join([
                    f"• {fee['fee_name']}: {fee['amount']} - {fee.get('calculation_formula', '固定费用')}"
                    for fee in other_fees
                ])
                
                calculation_steps.append({
                    'step': '附加费计算',
                    'description': '计算其他适用的附加费',
                    'details': f"""
                    适用的附加费:
                    {surcharge_details}
                    """
                })
            
            # 5. 总费用计算
            calculation_steps.append({
                'step': '费用汇总',
                'description': '计算总费用',
                'details': f"""
                基础运费: {get_attr_safe(calculation, 'base_fee', 0)}
                燃油附加费: {get_attr_safe(calculation, 'fuel_fee', 0)}
                其他附加费: {sum(float(d['amount']) for d in other_fees) if other_fees else 0}
                总费用: {get_attr_safe(calculation, 'total_fee', 0)} {get_attr_safe(calculation, 'currency', 'USD')}
                """
            })
            
            return calculation_steps
            
        except Exception as e:
            self.logger.error(f"获取计算详情失败: {str(e)}")
            return [{
                'step': '计算过程',
                'description': '获取详细计算过程时出错',
                'details': f"出现错误: {str(e)}\n请联系系统管理员检查日志。"
            }] 