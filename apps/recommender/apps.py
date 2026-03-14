from django.apps import AppConfig


class RecommenderConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.recommender"

    def ready(self):
        import apps.recommender.extractors  # noqa: F401
        import apps.recommender.signals  # noqa: F401
