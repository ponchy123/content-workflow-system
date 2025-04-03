import logging
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.products.models import Product

from apps.products.improve_import import ProductImportImprover, ensure_product_data_integrity

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '检查并修复产品数据完整性，确保所有产品都具有必要的关联数据'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product_id', 
            type=int, 
            help='指定要检查的产品ID，不指定则检查所有产品',
            required=False
        )
        parser.add_argument(
            '--dry_run', 
            action='store_true',
            help='仅检查缺失数据但不进行修复',
            required=False
        )
        parser.add_argument(
            '--verbose', 
            action='store_true',
            help='显示详细信息',
            required=False
        )

    def handle(self, *args, **options):
        product_id = options.get('product_id')
        dry_run = options.get('dry_run')
        verbose = options.get('verbose')
        
        # 设置日志级别
        if verbose:
            logger.setLevel(logging.DEBUG)
        
        # 创建改进工具
        improver = ProductImportImprover()
        
        if product_id:
            # 处理单个产品
            try:
                product = Product.objects.get(id=product_id)
                self.stdout.write(f"检查产品: ID={product.id}, 代码={product.code}, 名称={product.name}")
                
                if dry_run:
                    # 只检查不修复
                    missing_data = improver._check_data_integrity(product)
                    self.report_missing_data(product, missing_data)
                else:
                    # 检查并修复
                    result = ensure_product_data_integrity(product_id)
                    self.report_result(result)
            except Product.DoesNotExist:
                raise CommandError(f'产品ID={product_id}不存在')
        else:
            # 处理所有产品
            products = Product.objects.all()
            total = products.count()
            fixed = 0
            
            self.stdout.write(f"开始检查{total}个产品...")
            
            for i, product in enumerate(products, 1):
                self.stdout.write(f"[{i}/{total}] 检查产品: ID={product.id}, 代码={product.code}, 名称={product.name}")
                
                if dry_run:
                    # 只检查不修复
                    missing_data = improver._check_data_integrity(product)
                    self.report_missing_data(product, missing_data)
                    if any(missing_data.values()):
                        fixed += 1
                else:
                    # 检查并修复
                    result = ensure_product_data_integrity(product.id)
                    if result['success'] and 'before' in result and any(result['before'].values()):
                        fixed += 1
                    if verbose:
                        self.report_result(result)
            
            mode = "需要修复" if dry_run else "已修复"
            self.stdout.write(self.style.SUCCESS(f"检查完成! 共{total}个产品，{mode}{fixed}个产品的数据"))
    
    def report_missing_data(self, product, missing_data):
        """报告缺失的数据"""
        if any(missing_data.values()):
            self.stdout.write(self.style.WARNING(f"产品 {product.code} 的数据不完整:"))
            for data_type, is_missing in missing_data.items():
                status = "缺失" if is_missing else "存在"
                style = self.style.ERROR if is_missing else self.style.SUCCESS
                self.stdout.write(f"  - {data_type}: {style(status)}")
        else:
            self.stdout.write(self.style.SUCCESS(f"产品 {product.code} 的数据已完整"))
    
    def report_result(self, result):
        """报告修复结果"""
        if result['success']:
            if 'before' in result and any(result['before'].values()):
                self.stdout.write(self.style.SUCCESS(f"已成功修复产品ID={result['product_id']}的数据"))
                
                # 显示修复前后的状态
                self.stdout.write("  修复前:")
                for data_type, is_missing in result['before'].items():
                    status = "缺失" if is_missing else "存在"
                    style = self.style.ERROR if is_missing else self.style.SUCCESS
                    self.stdout.write(f"    - {data_type}: {style(status)}")
                
                self.stdout.write("  修复后:")
                for data_type, is_missing in result['after'].items():
                    status = "缺失" if is_missing else "存在"
                    style = self.style.ERROR if is_missing else self.style.SUCCESS
                    self.stdout.write(f"    - {data_type}: {style(status)}")
            else:
                self.stdout.write(self.style.SUCCESS(f"产品ID={result['product_id']}的数据已完整，无需修复"))
        else:
            self.stdout.write(self.style.ERROR(f"修复产品ID={result['product_id']}失败: {result['message']}")) 