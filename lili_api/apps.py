from django.apps import AppConfig


class LiliApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lili_api'

    def ready(self):
        import lili_api.signals
