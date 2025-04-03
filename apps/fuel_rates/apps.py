from django.apps import AppConfig


class FuelRatesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fuel_rates'
    verbose_name = '燃油费率'

    def ready(self):
        try:
            import apps.fuel_rates.signals  # noqa
        except ImportError:
            pass
