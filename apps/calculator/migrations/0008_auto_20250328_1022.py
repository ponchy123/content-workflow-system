from django.db import migrations, models
from decimal import Decimal

class Migration(migrations.Migration):

    dependencies = [
        ('calculator', '0007_auto_20250328_1016'),
    ]

    operations = [
        # 为quantity和declared_value添加默认值
        migrations.AlterField(
            model_name='calculation',
            name='quantity',
            field=models.IntegerField(default=1, verbose_name='数量'),
        ),
        migrations.AlterField(
            model_name='calculation',
            name='declared_value',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='申报价值'),
        ),
        migrations.AlterField(
            model_name='calculation',
            name='other_fees',
            field=models.DecimalField(decimal_places=2, default=Decimal('0.00'), max_digits=10, verbose_name='其他费用'),
        ),
    ] 