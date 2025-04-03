"""
单位转换工具模块
提供统一的单位转换函数，确保系统中的单位转换一致性
"""
from decimal import Decimal, ROUND_UP, ROUND_HALF_UP, ROUND_CEILING
from typing import Optional, Union

# 常量定义
CM_TO_IN = Decimal('2.54')  # 1英寸 = 2.54厘米
KG_TO_LB = Decimal('2.20462')  # 1千克 = 2.20462磅
LB_TO_KG = Decimal('0.453592')  # 1磅 = 0.453592千克

def cm_to_in(cm: Union[Decimal, float, int, str], round_up: bool = False, 
           precision: int = 2) -> Decimal:
    """
    将厘米转换为英寸
    
    Args:
        cm: 厘米值
        round_up: 是否向上取整
        precision: 保留的小数位数
    
    Returns:
        Decimal: 转换后的英寸值
    """
    if not isinstance(cm, Decimal):
        cm = Decimal(str(cm))
    
    result = cm / CM_TO_IN
    
    if round_up:
        return result.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        return result.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)

def in_to_cm(inches: Union[Decimal, float, int, str], round_up: bool = False, 
           precision: int = 2) -> Decimal:
    """
    将英寸转换为厘米
    
    Args:
        inches: 英寸值
        round_up: 是否向上取整
        precision: 保留的小数位数
    
    Returns:
        Decimal: 转换后的厘米值
    """
    if not isinstance(inches, Decimal):
        inches = Decimal(str(inches))
    
    result = inches * CM_TO_IN
    
    if round_up:
        return result.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        return result.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)

def kg_to_lb(kg: Union[Decimal, float, int, str], round_up: bool = False, 
           precision: int = 2) -> Decimal:
    """
    将千克转换为磅
    
    Args:
        kg: 千克值
        round_up: 是否向上取整
        precision: 保留的小数位数
    
    Returns:
        Decimal: 转换后的磅值
    """
    if not isinstance(kg, Decimal):
        kg = Decimal(str(kg))
    
    result = kg * KG_TO_LB
    
    if round_up:
        return result.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        return result.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)

def lb_to_kg(lb: Union[Decimal, float, int, str], round_up: bool = False, 
           precision: int = 2) -> Decimal:
    """
    将磅转换为千克
    
    Args:
        lb: 磅值
        round_up: 是否向上取整
        precision: 保留的小数位数
    
    Returns:
        Decimal: 转换后的千克值
    """
    if not isinstance(lb, Decimal):
        lb = Decimal(str(lb))
    
    result = lb * LB_TO_KG
    
    if round_up:
        return result.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        return result.quantize(Decimal(f'0.{"0" * precision}'), rounding=ROUND_HALF_UP)

def convert_dimensions(
    length: Union[Decimal, float, int, str],
    width: Union[Decimal, float, int, str],
    height: Union[Decimal, float, int, str],
    from_unit: str,
    to_unit: str,
    round_up: bool = True
) -> tuple[Decimal, Decimal, Decimal]:
    """
    转换尺寸单位（长宽高）
    
    Args:
        length: 长度值
        width: 宽度值
        height: 高度值
        from_unit: 原始单位('CM'或'IN')
        to_unit: 目标单位('CM'或'IN')
        round_up: 是否向上取整
    
    Returns:
        tuple: (转换后的长度, 转换后的宽度, 转换后的高度)
    """
    if from_unit.upper() == to_unit.upper():
        # 单位相同，无需转换
        return (
            Decimal(str(length)),
            Decimal(str(width)),
            Decimal(str(height))
        )
    
    if from_unit.upper() == 'CM' and to_unit.upper() == 'IN':
        # 厘米转英寸
        return (
            cm_to_in(length, round_up),
            cm_to_in(width, round_up),
            cm_to_in(height, round_up)
        )
    elif from_unit.upper() == 'IN' and to_unit.upper() == 'CM':
        # 英寸转厘米
        return (
            in_to_cm(length, round_up),
            in_to_cm(width, round_up),
            in_to_cm(height, round_up)
        )
    else:
        raise ValueError(f"不支持的单位转换: {from_unit} -> {to_unit}")

def calculate_volumetric_weight(
    length: Union[Decimal, float, int, str],
    width: Union[Decimal, float, int, str],
    height: Union[Decimal, float, int, str],
    dim_factor: Union[Decimal, float, int, str],
    dim_unit: str,
    weight_unit: str,
    round_up: bool = True
) -> Decimal:
    """
    计算体积重量
    
    Args:
        length: 长度值
        width: 宽度值
        height: 高度值
        dim_factor: 体积重系数
        dim_unit: 尺寸单位('CM'或'IN')
        weight_unit: 重量单位('KG'或'LB')
        round_up: 是否向上取整
    
    Returns:
        Decimal: 计算的体积重量
    """
    if not all(isinstance(x, Decimal) for x in [length, width, height, dim_factor]):
        length = Decimal(str(length))
        width = Decimal(str(width))
        height = Decimal(str(height))
        dim_factor = Decimal(str(dim_factor))
    
    # 计算体积重量: 长×宽×高 / 体积重系数
    volumetric_weight = (length * width * height) / dim_factor
    
    if round_up:
        return volumetric_weight.quantize(Decimal('1'), rounding=ROUND_CEILING)
    else:
        return volumetric_weight.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

def calculate_girth(
    length: Union[Decimal, float, int, str],
    width: Union[Decimal, float, int, str],
    height: Union[Decimal, float, int, str]
) -> Decimal:
    """
    计算长+周长
    长+2×(宽+高)，通常用于包裹尺寸限制检查
    
    Args:
        length: 长度值
        width: 宽度值
        height: 高度值
    
    Returns:
        Decimal: 长+周长值
    """
    if not all(isinstance(x, Decimal) for x in [length, width, height]):
        length = Decimal(str(length))
        width = Decimal(str(width))
        height = Decimal(str(height))
    
    return length + Decimal('2') * (width + height) 