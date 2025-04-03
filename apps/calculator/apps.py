from django.apps import AppConfig


class CalculatorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.calculator'
    verbose_name = "运费计算器"

    def ready(self):
        """应用就绪时的初始化操作"""
        try:
            from . import signals  # noqa
        except ImportError:
            pass 