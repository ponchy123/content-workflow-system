from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Product, Surcharge, PeakSeasonSurcharge, BaseFee


@receiver(post_save, sender=Product)
def product_post_save(sender, instance, **kwargs):
    """产品保存后的处理"""
    if not instance.created_by:
        instance.created_by = 'system'
    instance.updated_by = 'system'


@receiver(post_delete, sender=Product)
def product_post_delete(sender, instance, **kwargs):
    """产品删除后的处理"""
    # Implementation needed
    pass


@receiver(post_save, sender=Surcharge)
def surcharge_post_save(sender, instance, **kwargs):
    """附加费保存后的处理"""
    if not instance.created_by:
        instance.created_by = 'system'
    instance.updated_by = 'system'


@receiver(post_delete, sender=Surcharge)
def surcharge_post_delete(sender, instance, **kwargs):
    """附加费删除后的处理"""
    # Implementation needed
    pass


@receiver(post_save, sender=PeakSeasonSurcharge)
def set_peak_season_surcharge_created_by(sender, instance, **kwargs):
    """旺季附加费保存后的处理"""
    if not instance.created_by:
        instance.created_by = 'system'
    instance.updated_by = 'system'


@receiver(post_delete, sender=PeakSeasonSurcharge)
def peak_season_surcharge_post_delete(sender, instance, **kwargs):
    """旺季附加费删除后的处理"""
    # Implementation needed
    pass 