"""
基础运费计算模块
负责计算不同产品的基础运费
"""
from decimal import Decimal
from typing import Dict, Any, Optional
import logging
import sys
import json
import decimal

from apps.products.models import Product, BaseFee

logger = logging.getLogger(__name__)

class BaseFreightCalculator:
    """基础运费计算器，负责计算不同产品的基础运费"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def calculate_base_freight(self, product: Product, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        计算基础运费
        
        Args:
            product: 产品对象
            data: {
                'weight': 重量,
                'chargeable_weight': 计费重量,
                'zone': 区域,
                ...
            }
        Returns:
            Dict: 包含基础运费信息的字典或None
        """
        try:
            print(f"\n========== 开始计算基础运费 ==========", file=sys.stdout)
            print(f"产品: {product.product_id} ({product.product_name})", file=sys.stdout)
            print(f"区域: {data.get('zone', '')}", file=sys.stdout)
            print(f"重量: {data.get('weight', 0)}kg, 计费重量: {data.get('chargeable_weight', 0)}kg", file=sys.stdout)
            
            # 获取运费费率
            base_fee = self._get_base_fee(product, data)
            if not base_fee:
                print(f"未找到匹配的运费费率", file=sys.stdout)
                return None
            
            print(f"找到匹配的基础费用: {base_fee}", file=sys.stdout)
            
            # 计算基础运费
            result = self._calculate_fee(product, base_fee, data)
            print(f"基础运费计算结果: {result}", file=sys.stdout)
            
            return result
            
        except Exception as e:
            self.logger.error(f"计算基础运费错误: {str(e)}")
            print(f"计算基础运费错误: {str(e)}", file=sys.stdout)
            return None
    
    def _get_base_fee(self, product: Product, data: Dict[str, Any]) -> Optional[BaseFee]:
        """获取适合的基础运费费率"""
        zone = data.get('zone', '')
        chargeable_weight = Decimal(str(data.get('chargeable_weight', 0)))
        
        if not zone:
            print(f"缺少区域信息", file=sys.stdout)
            return None
        
        # 查询匹配的运费费率
        try:
            # 将zone格式转换为数字
            zone_number = zone.replace('ZONE', '')
            
            # 按产品和重量查询基础费用
            base_fees = BaseFee.objects.filter(
                product=product,
                is_deleted=False
            ).order_by('weight')
            
            print(f"找到 {base_fees.count()} 个基础费用记录", file=sys.stdout)
            
            # 无匹配费率
            if not base_fees.exists():
                print(f"未找到产品 {product.product_id} 的基础费用", file=sys.stdout)
                return None
            
            # 查找第一个大于等于计费重量的费用点，直接检查raw_data
            for fee in base_fees:
                if fee.weight >= chargeable_weight and fee.raw_data:
                    # 直接查看是否有匹配的价格
                    try:
                        raw_data = fee.raw_data if isinstance(fee.raw_data, dict) else json.loads(fee.raw_data)
                        print(f"\n【关键调试】raw_data类型: {type(raw_data)}", file=sys.stdout)
                        print(f"raw_data包含这些键: {list(raw_data.keys())}", file=sys.stdout)
                        
                        # 增加可能的键名，包括可能的大小写和格式变体
                        possible_keys = [
                            f"Zone{zone_number}基础价格",
                            f"zone{zone_number}基础价格",
                            f"Zone{zone_number}",
                            f"zone{zone_number}",
                            f"ZONE{zone_number}",
                            f"zone{zone_number}_price",
                            f"Zone {zone_number} 基础价格",
                            f"ZONE{zone_number}基础价格",
                            f"Zone{zone_number}价格",
                            f"zone{zone_number}价格",
                            f"Zone{zone_number}基本价格",
                            f"Zone{zone_number}基础运费",
                            f"zone{zone_number}_base_price",
                            # 尝试不同的数字格式
                            f"Zone {zone_number}",
                            f"Zone_{zone_number}",
                            f"ZONE_{zone_number}",
                            # 尝试其他可能的格式
                            f"Zone{zone_number}基础价值"
                        ]
                        
                        # 检查是否有任何键存在(不管价格是否为0)
                        for key in possible_keys:
                            if key in raw_data and raw_data[key] is not None:
                                try:
                                    # 转换为Decimal，检查是否有效
                                    price = Decimal(str(raw_data[key]))
                                    # 即使价格为0也返回该费用点
                                    print(f"找到适合的费用点 weight={fee.weight}，{key}={price}", file=sys.stdout)
                                    return fee
                                except (ValueError, TypeError):
                                    continue
                                    
                        # 如果所有预定义键都没找到，则检查所有可能包含zone和价格的键
                        for key in raw_data.keys():
                            if (zone_number.lower() in key.lower() or zone.lower() in key.lower()) and any(price_term in key.lower() for price_term in ['价格', 'price', '费用', 'fee']):
                                try:
                                    price = Decimal(str(raw_data[key]))
                                    print(f"通过模糊匹配找到价格键: {key}={price}", file=sys.stdout)
                                    return fee
                                except (ValueError, TypeError):
                                    continue
                    except Exception as e:
                        print(f"解析raw_data时出错: {str(e)}", file=sys.stdout)
                        continue
            
            # 如果没有找到大于等于计费重量的费用点，使用第一个有价格的费用点
            for fee in base_fees:
                if fee.raw_data:
                    try:
                        raw_data = fee.raw_data if isinstance(fee.raw_data, dict) else json.loads(fee.raw_data)
                        
                        # 打印完整raw_data内容以进行调试
                        print(f"\n【第二轮查找】打印完整raw_data内容:", file=sys.stdout)
                        for key, value in raw_data.items():
                            print(f"  {key}: {value}", file=sys.stdout)
                        
                        # 检查是否有任何键包含zone和区域编号
                        for key in raw_data.keys():
                            if (f"zone{zone_number}".lower() in key.lower() or f"zone {zone_number}".lower() in key.lower() or zone.lower() in key.lower()):
                                try:
                                    if raw_data[key] is not None:
                                        price = Decimal(str(raw_data[key]))
                                        print(f"按照部分匹配找到价格键: {key}={price}", file=sys.stdout)
                                        return fee
                                except (ValueError, TypeError):
                                    continue
                            
                            # 检查是否有任何键含有有效价格值
                            if isinstance(raw_data[key], (int, float, str)) and raw_data[key] is not None:
                                try:
                                    value = str(raw_data[key])
                                    if value.replace('.', '').isdigit():  # 检查是否可能是数字
                                        price = Decimal(value)
                                        if price > 0:
                                            print(f"找到有效价格值: {key}={price}", file=sys.stdout)
                                            # 不立即返回，优先使用与区域相关的键
                                except (ValueError, TypeError):
                                    continue
                    except Exception as e:
                        print(f"第二轮解析raw_data出错: {str(e)}", file=sys.stdout)
                        continue
            
            # 如果还找不到，返回第一个有效的BaseFee对象，即使没有价格
            print(f"未找到有价格的费用点，使用第一个费用点", file=sys.stdout)
            return base_fees.first()
            
        except Exception as e:
            self.logger.error(f"获取基础费用错误: {str(e)}")
            print(f"获取基础费用错误: {str(e)}", file=sys.stdout)
            return None
    
    def _calculate_fee(self, product: Product, base_fee: BaseFee, data: Dict[str, Any]) -> Dict[str, Any]:
        """根据基础费用和数据计算实际费用"""
        chargeable_weight = Decimal(str(data.get('chargeable_weight', 0)))
        zone = data.get('zone', '')
        zone_number = zone.replace('ZONE', '')
        
        # 基础信息
        result = {
            'type': '基础运费',
            'name': f"{product.product_name} {zone}",
            'amount': '0'
        }
        
        # 如果计费重量为0，则直接返回0费用
        if chargeable_weight <= 0:
            print(f"计费重量为0，费用为0", file=sys.stdout)
            return result
        
        # 从数据库查询价格 - 对所有zone通用
        print(f"\n查询{zone}价格 - 重量: {chargeable_weight}", file=sys.stdout)
        
        # 从BaseFee表中直接查找匹配的价格记录
        try:
            from django.db.models import Q
            
            # 查找所有重量大于等于当前重量的记录
            matching_fees = BaseFee.objects.filter(
                product=product,
                weight__gte=chargeable_weight,
                is_deleted=False
            ).order_by('weight')
            
            if matching_fees:
                matching_fee = matching_fees.first()
                print(f"找到匹配的费用记录: ID={matching_fee.id}, 重量={matching_fee.weight}", file=sys.stdout)
                
                # 从数据库查询中获取价格
                price = self._extract_zone_price_from_db(matching_fee, zone)
                if price > 0:
                    print(f"从数据库获取到{zone}价格: {price}", file=sys.stdout)
                    result['amount'] = str(price)
                    result['calculation'] = f"从数据库获取{zone}价格: {price}"
                    return result
            
            # 如果没有找到匹配的记录或价格为0，查询所有记录并分析
            all_fees = BaseFee.objects.filter(product=product, is_deleted=False).order_by('weight')
            for fee in all_fees:
                price = self._extract_zone_price_from_db(fee, zone)
                if price > 0:
                    print(f"从其他重量记录获取到{zone}价格: {price}", file=sys.stdout)
                    result['amount'] = str(price)
                    result['calculation'] = f"使用最接近重量的价格: {price}"
                    return result
            
            print(f"未能从数据库中找到有效的{zone}价格", file=sys.stdout)
        except Exception as e:
            print(f"数据库查询{zone}价格出错: {str(e)}", file=sys.stdout)
        
        # 直接从raw_data获取价格
        base_price = Decimal('0')
        unit_price = Decimal('0')
        
        if base_fee.raw_data:
            try:
                raw_data = base_fee.raw_data if isinstance(base_fee.raw_data, dict) else json.loads(base_fee.raw_data)
                
                # 直接打印完整的raw_data内容
                print(f"\n【重要】完整的raw_data内容:", file=sys.stdout)
                for key, value in raw_data.items():
                    print(f"  {key}: {value}", file=sys.stdout)
                print("", file=sys.stdout)
                
                # 尝试查找product_id值，可能隐藏重要线索
                if hasattr(product, 'product_id'):
                    print(f"当前产品ID: {product.product_id}", file=sys.stdout)
                    
                # 查找任何可能的价格值
                found_price = False
                for key, value in raw_data.items():
                    if isinstance(value, (int, float, str)) and value is not None:
                        try:
                            val_str = str(value)
                            if val_str.replace('.', '').isdigit():  # 检查是否可能是数字
                                price = Decimal(val_str)
                                if price > 0:
                                    print(f"【发现可能的价格值】键={key}, 值={price}", file=sys.stdout)
                                    # 不直接使用找到的价格，而是优先查找与zone相关的键
                                    found_price = True
                        except (ValueError, TypeError):
                            continue
                
                # 尝试更多可能的键名格式
                base_price_keys = [
                    f"Zone{zone_number}基础价格",
                    f"Zone{zone_number}基础价值",
                    f"zone{zone_number}基础价格",
                    f"Zone{zone_number}",
                    f"zone{zone_number}",
                    f"ZONE{zone_number}",
                    f"zone{zone_number}_price",
                    f"Zone{zone_number}base_price",
                    f"Zone {zone_number}",
                    f"Zone_{zone_number}",
                    f"Zone{zone_number}价格",
                    f"Zone{zone_number}_price"
                ]
                
                # 移除区域8的硬编码
                if zone_number != '8':
                    # 动态生成与当前区域相关的键
                    base_price_keys.extend([
                        f"Zone{zone_number}基础价值",
                        f"Zone{zone_number}基础价格",
                        f"zone{zone_number}基础价格",
                        f"ZONE{zone_number}基础价格",
                        f"Zone{zone_number}基础运费"
                    ])
                
                # 尝试不同的可能键名，找到任何值（包括0）
                base_price_found = False
                for key in base_price_keys:
                    if key in raw_data and raw_data[key] is not None:
                        try:
                            base_price = Decimal(str(raw_data[key]))
                            print(f"从raw_data获取到基础价格: {base_price}，键名={key}", file=sys.stdout)
                            base_price_found = True
                            break
                        except (ValueError, TypeError):
                            continue
                
                if not base_price_found:
                    print(f"在raw_data中未找到{zone}区域的基础价格，尝试模糊匹配", file=sys.stdout)
                    # 尝试模糊匹配含有zone和价格相关词的键
                    for key in raw_data.keys():
                        if (zone_number.lower() in key.lower() or zone.lower() in key.lower()) and any(price_term in key.lower() for price_term in ['价格', 'price', '费用', 'fee']):
                            try:
                                if raw_data[key] is not None:
                                    base_price = Decimal(str(raw_data[key]))
                                    print(f"通过模糊匹配找到价格键: {key}={base_price}", file=sys.stdout)
                                    base_price_found = True
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    # 最后尝试查找任何名称包含zone8的键
                    if not base_price_found:
                        for key in raw_data.keys():
                            if zone.lower() in key.lower() or f"zone{zone_number}".lower() in key.lower():
                                try:
                                    if raw_data[key] is not None and str(raw_data[key]).replace('.', '').isdigit():
                                        base_price = Decimal(str(raw_data[key]))
                                        print(f"最后尝试通过zone名称匹配找到价格: {key}={base_price}", file=sys.stdout)
                                        base_price_found = True
                                        break
                                except (ValueError, TypeError):
                                    continue
                
                # 尝试获取单位价格(如果是线性费用)
                if base_fee.fee_type == 'LINEAR':
                    unit_price_keys = [
                        f"Zone{zone_number}单价",
                        f"zone{zone_number}单价",
                        f"Zone{zone_number}_unit_price",
                        f"zone{zone_number}_unit_price",
                        f"ZONE{zone_number}_unit_price"
                    ]
                    
                    unit_price_found = False
                    for key in unit_price_keys:
                        if key in raw_data and raw_data[key] is not None:
                            try:
                                unit_price = Decimal(str(raw_data[key]))
                                print(f"从raw_data获取到单价: {unit_price}，键名={key}", file=sys.stdout)
                                unit_price_found = True
                                break
                            except (ValueError, TypeError):
                                continue
                    
                    if not unit_price_found:
                        print(f"在raw_data中未找到{zone}区域的单价", file=sys.stdout)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"处理raw_data获取价格时出错: {str(e)}", file=sys.stdout)
        else:
            print(f"该费用点没有raw_data数据", file=sys.stdout)
        
        # 根据费用类型计算
        amount = Decimal('0')
        if base_fee.fee_type == 'STEP':
            # 阶梯式费用，直接使用基础价格
            amount = base_price
            calculation_desc = f"阶梯式费用: {base_price}"
        elif base_fee.fee_type == 'LINEAR':
            # 线性费用，需要乘以重量
            amount = base_price + (chargeable_weight * unit_price)
            calculation_desc = f"线性费用: 基础价格({base_price}) + 重量({chargeable_weight}) × 单价({unit_price})"
        else:
            # 未知费用类型，使用基础价格
            amount = base_price
            calculation_desc = f"未知费用类型({base_fee.fee_type}): 使用基础价格 {base_price}"
        
        result['amount'] = str(amount)
        result['calculation'] = calculation_desc
        
        print(f"计算得出费用: {amount}，计算公式: {calculation_desc}", file=sys.stdout)
        return result
    
    def _extract_zone_price_from_db(self, fee: BaseFee, zone: str) -> Decimal:
        """从BaseFee记录中提取指定区域的价格"""
        try:
            zone_number = zone.replace('ZONE', '')
            
            if fee.raw_data:
                # 解析raw_data
                raw_data = fee.raw_data if isinstance(fee.raw_data, dict) else json.loads(fee.raw_data)
                
                if not isinstance(raw_data, dict):
                    print(f"警告: raw_data不是字典类型: {type(raw_data)}", file=sys.stdout)
                    return Decimal('0')
                
                # 打印完整内容查看结构
                print(f"\n费用记录 ID={fee.id}, 重量={fee.weight} 的raw_data内容:", file=sys.stdout)
                for key, value in raw_data.items():
                    print(f"  {key}: {value}", file=sys.stdout)
                
                # 尝试各种可能的键名格式获取价格
                possible_keys = [
                    f"zone{zone_number}_base_price",
                    f"Zone{zone_number}基础价格",
                    f"zone{zone_number}基础价格",
                    f"Zone{zone_number}",
                    f"zone{zone_number}",
                    f"ZONE{zone_number}",
                    f"zone{zone_number}_price",
                    f"Zone{zone_number}价格",
                ]
                
                # 尝试匹配键名
                for key in possible_keys:
                    if key in raw_data and raw_data[key] is not None:
                        try:
                            price = Decimal(str(raw_data[key]))
                            print(f"找到价格: {key}={price}", file=sys.stdout)
                            return price
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            continue
                
                # 尝试模糊匹配
                for key, value in raw_data.items():
                    # 检查键是否包含区域编号
                    if zone_number in key or zone.lower() in key.lower():
                        try:
                            if value is not None:
                                price = Decimal(str(value))
                                print(f"通过模糊匹配找到价格: {key}={price}", file=sys.stdout)
                                return price
                        except (ValueError, TypeError, decimal.InvalidOperation):
                            continue
                
                # 查找任何带有数字的值
                for key, value in raw_data.items():
                    try:
                        if value is not None:
                            value_str = str(value)
                            if value_str.replace('.', '', 1).isdigit():
                                price = Decimal(value_str)
                                if price > 0:
                                    print(f"找到数值类型价格: {key}={price}", file=sys.stdout)
                                    return price
                    except:
                        continue
                        
                print(f"未能从记录中找到有效价格", file=sys.stdout)
            else:
                print(f"记录ID={fee.id}没有raw_data数据", file=sys.stdout)
                
            return Decimal('0')
            
        except Exception as e:
            print(f"从记录中提取价格出错: {str(e)}", file=sys.stdout)
            return Decimal('0') 