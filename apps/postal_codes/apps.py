from django.apps import AppConfig


class PostalCodesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.postal_codes'
    verbose_name = '邮编管理'

    def ready(self):
        try:
            import apps.postal_codes.signals  # noqa
        except ImportError:
            pass 