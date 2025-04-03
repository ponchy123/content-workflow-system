import logging
from django.core.management.base import BaseCommand
from apps.products.models import BaseFee

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = '从raw_data更新BaseFee模型中的zone_prices字段'

    def handle(self, *args, **options):
        logger.info('开始更新BaseFee zone_prices')
        base_fees = BaseFee.objects.all()
        logger.info(f'找到{base_fees.count()}条BaseFee记录')
        
        updated = 0
        errors = 0
        
        for i, base_fee in enumerate(base_fees):
            try:
                for zone_num in range(1, 9):
                    zone = f'zone{zone_num}'
                    price = base_fee.get_price(zone)
                    logger.debug(f'费用ID: {base_fee.fee_id}, {zone}价格: {price}')
                
                base_fee.save()
                updated += 1
                
                if (i + 1) % 100 == 0:
                    logger.info(f'已处理 {i + 1} 条记录')
                    
            except Exception as e:
                logger.error(f'更新费用ID {base_fee.fee_id} 时出错: {str(e)}')
                errors += 1
        
        self.stdout.write(self.style.SUCCESS(f'成功更新了 {updated} 条记录，失败 {errors} 条')) 