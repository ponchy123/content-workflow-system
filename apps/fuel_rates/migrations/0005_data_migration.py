from django.db import migrations


def migrate_product_to_provider(apps, schema_editor):
    """
    将燃油费率从产品关联迁移到服务商关联
    1. 获取所有有产品关联但没有服务商关联的燃油费率
    2. 对于每条记录，获取关联的产品及其服务商
    3. 更新燃油费率记录的服务商字段
    """
    FuelRate = apps.get_model('fuel_rates', 'FuelRate')
    Product = apps.get_model('products', 'Product')
    ServiceProvider = apps.get_model('core', 'ServiceProvider')
    
    # 获取没有服务商或服务商是默认值的燃油费率记录
    fuel_rates = FuelRate.objects.filter(product__isnull=False)
    
    # 获取默认服务商，如果不存在则创建
    default_provider = ServiceProvider.objects.first()
    if not default_provider:
        default_provider = ServiceProvider.objects.create(
            name="默认服务商",
            code="DEFAULT",
            status=True
        )
    
    # 更新每条记录
    for fuel_rate in fuel_rates:
        try:
            # 获取关联的产品
            product = Product.objects.get(product_id=fuel_rate.product_id)
            # 获取产品的服务商
            provider = product.provider
            
            # 更新燃油费率记录
            fuel_rate.provider = provider
            fuel_rate.save(update_fields=['provider'])
            
            print(f"更新燃油费率 ID:{fuel_rate.rate_id}, 从产品:{product.product_name} 到服务商:{provider.name}")
        except Product.DoesNotExist:
            # 如果产品不存在，使用默认服务商
            fuel_rate.provider = default_provider
            fuel_rate.save(update_fields=['provider'])
            print(f"使用默认服务商更新燃油费率 ID:{fuel_rate.rate_id}")
        except Exception as e:
            print(f"更新燃油费率 ID:{fuel_rate.rate_id} 失败: {str(e)}")


class Migration(migrations.Migration):

    dependencies = [
        ('fuel_rates', '0004_auto_20250325_1652'),
    ]

    operations = [
        migrations.RunPython(
            migrate_product_to_provider,
            reverse_code=migrations.RunPython.noop
        ),
    ] 