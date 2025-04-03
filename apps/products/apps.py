from django.apps import AppConfig


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = '产品管理'

    def ready(self):
        try:
            import apps.products.signals  # noqa
        except ImportError:
            pass 