from django.test import TestCase
from django.utils import timezone
from .models import Product, Surcharge, PeakSeasonSurcharge, BaseFee
from decimal import Decimal
from datetime import date


class ProductModelTest(TestCase):
    """产品模型测试"""
    def setUp(self):
        self.product = Product.objects.create(
            product_id='TEST001',
            provider_name='测试服务商',
            product_name='测试产品',
            dim_factor=Decimal('6000'),
            dim_factor_unit='KG/CBM',
            effective_date=date(2023, 1, 1),
            expiration_date=date(2023, 12, 31),
            country='CN',
            currency='CNY',
            weight_unit='KG',
            dim_unit='CM',
            description='测试产品描述',
            status=True
        )

    def test_product_created(self):
        """测试产品是否创建成功"""
        self.assertEqual(Product.objects.count(), 1)
        self.assertEqual(self.product.product_name, '测试产品')
        
    def test_product_str(self):
        """测试产品字符串表示"""
        self.assertEqual(str(self.product), '测试产品 (TEST001)')
        
    def test_product_provider(self):
        """测试产品服务商属性"""
        self.assertEqual(self.product.provider, '测试服务商')

    def test_product_creation(self):
        """测试产品创建"""
        self.assertEqual(self.product.product_id, 'TEST001')
        self.assertEqual(self.product.provider_name, '测试服务商')
        self.assertEqual(self.product.product_name, '测试产品')
        self.assertEqual(self.product.dim_factor, Decimal('6000'))
        self.assertEqual(self.product.dim_factor_unit, 'KG/CBM')
        self.assertEqual(self.product.country, 'CN')
        self.assertEqual(self.product.currency, 'CNY')
        self.assertEqual(self.product.weight_unit, 'KG')
        self.assertEqual(self.product.dim_unit, 'CM')
        self.assertEqual(self.product.description, '测试产品描述')
        self.assertTrue(self.product.status)
        self.assertFalse(self.product.is_deleted)


class BaseFeeModelTest(TestCase):
    """基础费用模型测试"""
    def setUp(self):
        self.product = Product.objects.create(
            product_id='TEST001',
            provider_name='Test Provider',
            product_name='Test Product',
            dim_factor=200.00,
            dim_factor_unit='lb/in³',
            effective_date=timezone.now().date(),
            expiration_date=timezone.now().date(),
            country='US',
            currency='USD',
            weight_unit='lb',
            dim_unit='in'
        )
        self.base_fee = BaseFee.objects.create(
            product=self.product,
            weight=1.00,
            weight_unit='lb',
            fee_type='STEP',
            zone_prices={'zone1': '10.00', 'zone2': '15.00'},
            zone_unit_prices={'zone1': '0.50', 'zone2': '0.75'}
        )

    def test_base_fee_creation(self):
        """测试基础费用创建"""
        self.assertEqual(self.base_fee.product, self.product)
        self.assertEqual(self.base_fee.weight, 1.00)
        self.assertEqual(self.base_fee.weight_unit, 'lb')
        self.assertEqual(self.base_fee.fee_type, 'STEP')
        self.assertEqual(self.base_fee.zone_prices['zone1'], '10.00')
        self.assertEqual(self.base_fee.zone_prices['zone2'], '15.00')
        self.assertEqual(self.base_fee.zone_unit_prices['zone1'], '0.50')
        self.assertEqual(self.base_fee.zone_unit_prices['zone2'], '0.75')
        self.assertTrue(self.base_fee.status)
        self.assertFalse(self.base_fee.is_deleted)


class SurchargeModelTest(TestCase):
    """附加费模型测试"""
    def setUp(self):
        self.product = Product.objects.create(
            product_id='TEST001',
            provider_name='Test Provider',
            product_name='Test Product',
            dim_factor=200.00,
            dim_factor_unit='lb/in³',
            effective_date=timezone.now().date(),
            expiration_date=timezone.now().date(),
            country='US',
            currency='USD',
            weight_unit='lb',
            dim_unit='in'
        )
        self.surcharge = Surcharge.objects.create(
            product=self.product,
            surcharge_type='FUEL',
            sub_type='DOMESTIC',
            condition_desc='Test Condition',
            zone1_fee=10.00,
            zone2_fee=20.00,
            zone3_fee=30.00,
            zone4_fee=40.00,
            zone5_fee=50.00,
            zone6_fee=60.00,
            zone7_fee=70.00,
            zone8_fee=80.00,
            zone17_fee=90.00
        )

    def test_surcharge_creation(self):
        """测试附加费创建"""
        self.assertEqual(self.surcharge.product, self.product)
        self.assertEqual(self.surcharge.surcharge_type, 'FUEL')
        self.assertEqual(self.surcharge.sub_type, 'DOMESTIC')
        self.assertEqual(self.surcharge.condition_desc, 'Test Condition')
        self.assertEqual(self.surcharge.zone1_fee, 10.00)
        self.assertEqual(self.surcharge.zone2_fee, 20.00)
        self.assertEqual(self.surcharge.zone3_fee, 30.00)
        self.assertEqual(self.surcharge.zone4_fee, 40.00)
        self.assertEqual(self.surcharge.zone5_fee, 50.00)
        self.assertEqual(self.surcharge.zone6_fee, 60.00)
        self.assertEqual(self.surcharge.zone7_fee, 70.00)
        self.assertEqual(self.surcharge.zone8_fee, 80.00)
        self.assertEqual(self.surcharge.zone17_fee, 90.00)
        self.assertTrue(self.surcharge.status)
        self.assertFalse(self.surcharge.is_deleted)


class PeakSeasonSurchargeModelTest(TestCase):
    """旺季附加费模型测试"""
    def setUp(self):
        self.product = Product.objects.create(
            product_id='TEST001',
            provider_name='Test Provider',
            product_name='Test Product',
            dim_factor=200.00,
            dim_factor_unit='lb/in³',
            effective_date=timezone.now().date(),
            expiration_date=timezone.now().date(),
            country='US',
            currency='USD',
            weight_unit='lb',
            dim_unit='in'
        )
        self.peak_season_surcharge = PeakSeasonSurcharge.objects.create(
            product=self.product,
            surcharge_type='PEAK',
            start_date=timezone.now().date(),
            end_date=timezone.now().date(),
            fee_amount=100.00
        )

    def test_peak_season_surcharge_creation(self):
        """测试旺季附加费创建"""
        self.assertEqual(self.peak_season_surcharge.product, self.product)
        self.assertEqual(self.peak_season_surcharge.surcharge_type, 'PEAK')
        self.assertEqual(self.peak_season_surcharge.fee_amount, 100.00)
        self.assertTrue(self.peak_season_surcharge.status)
        self.assertFalse(self.peak_season_surcharge.is_deleted)


class ZoneRateModelTest(TestCase):
    """分区费率模型测试"""
    def setUp(self):
        self.product = Product.objects.create(
            product_id='TEST001',
            provider_name='Test Provider',
            product_name='Test Product',
            dim_factor=200.00,
            dim_factor_unit='lb/in³',
            effective_date=timezone.now().date(),
            expiration_date=timezone.now().date(),
            country='US',
            currency='USD',
            weight_unit='lb',
            dim_unit='in'
        )
        self.base_fee = BaseFee.objects.create(
            product=self.product,
            weight=1.00,
            weight_unit='lb',
            fee_type='STEP',
            zone_prices={'zone1': '10.00'},
            zone_unit_prices={'zone1': '0.50'}
        )

    def test_base_fee_zone_rates(self):
        """测试基础费用的区域费率"""
        self.assertEqual(self.base_fee.product, self.product)
        self.assertEqual(self.base_fee.zone_prices['zone1'], '10.00')
        self.assertEqual(self.base_fee.zone_unit_prices['zone1'], '0.50')


class FuelSurchargeTest(TestCase):
    """燃油附加费计算测试"""
    
    def setUp(self):
        """设置测试数据"""
        from django.utils import timezone
        from apps.calculator.services import CalculationService
        from decimal import Decimal
        
        # 创建测试产品
        self.product = Product.objects.create(
            product_id='FUEL001',
            provider_name='燃油测试服务商',
            product_name='燃油测试产品',
            dim_factor=Decimal('6000'),
            dim_factor_unit='KG/CBM',
            effective_date=date(2023, 1, 1),
            expiration_date=date(2024, 12, 31),
            country='CN',
            currency='CNY',
            weight_unit='KG',
            dim_unit='CM',
            status=True
        )
        
        # 创建基础费用
        self.base_fee = BaseFee.objects.create(
            fee_id='BF001',
            product=self.product,
            weight=Decimal('1.00'),
            weight_unit='KG',
            fee_type='STEP',
            zone_prices={'zone1': '100.00', 'zone2': '200.00'},
            zone_unit_prices={'zone1': '0.00', 'zone2': '0.00'},
            status=True
        )
        
        # 创建附加费
        self.surcharge = Surcharge.objects.create(
            product=self.product,
            surcharge_type='测试附加费',
            effective_date=date(2023, 1, 1),
            expiration_date=date(2024, 12, 31),
            fee_amount=Decimal('50.00'),
            status=True
        )
        
        # 初始化计算服务
        self.calculation_service = CalculationService()
        
        # Mock燃油费率计算方法
        self.original_calculate_fuel_surcharge = self.calculation_service._calculate_fuel_surcharge
        
        # 替换为mock方法
        def mock_calculate_fuel_surcharge(product, total_fee):
            # 模拟10%的燃油费率
            rate = Decimal('0.10')
            return (total_fee * rate).quantize(Decimal('0.01'))
            
        self.calculation_service._calculate_fuel_surcharge = mock_calculate_fuel_surcharge
        
    def tearDown(self):
        """清理测试数据"""
        # 恢复原始方法
        if hasattr(self, 'original_calculate_fuel_surcharge'):
            self.calculation_service._calculate_fuel_surcharge = self.original_calculate_fuel_surcharge
        
    def test_fuel_surcharge_calculation(self):
        """测试燃油附加费计算逻辑"""
        from decimal import Decimal
        
        # 基础数据
        base_fee = Decimal('100.00')
        surcharge_amount = Decimal('50.00')
        
        # 手动计算预期的燃油附加费
        expected_fee_for_fuel = base_fee + surcharge_amount
        expected_fuel_surcharge = expected_fee_for_fuel * Decimal('0.10')  # 10%
        
        # 使用_calculate_fuel_surcharge方法测试
        actual_fuel_surcharge = self.calculation_service._calculate_fuel_surcharge(
            self.product, expected_fee_for_fuel
        )
        
        # 验证结果
        self.assertEqual(actual_fuel_surcharge.quantize(Decimal('0.01')), 
                        expected_fuel_surcharge.quantize(Decimal('0.01')))
        
        # 测试整个计算流程
        calculation_data = {
            'product_id': 'FUEL001',
            'from_postal': '100000',
            'to_postal': '200000',
            'weight': Decimal('1.00'),
            'length': Decimal('10.00'),
            'width': Decimal('10.00'),
            'height': Decimal('10.00')
        }
        
        # 模拟区域和远程区域方法
        self.calculation_service._get_zone = lambda p, f, t: 'ZONE1'
        self.calculation_service._get_remote_level = lambda p, f, t: None
        self.calculation_service._get_weight_point = lambda p, w: self.base_fee
        
        # 执行实际计算
        result = self.calculation_service.calculate_single(calculation_data)
        
        # 验证结果中的燃油附加费基于（基础费用+附加费）计算
        self.assertAlmostEqual(
            float(result['fuel_surcharge']), 
            float((base_fee + surcharge_amount) * Decimal('0.10')),
            places=2
        ) 