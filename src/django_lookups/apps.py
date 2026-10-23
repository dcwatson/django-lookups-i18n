from django.apps import AppConfig
from django.db.models.signals import post_migrate

from .registry import lookups


class LookupsConfig(AppConfig):
    name = "django_lookups"

    def install_lookups(self, sender, **kwargs):
        lookups.install()

    def ready(self):
        post_migrate.connect(self.install_lookups, sender=self)
