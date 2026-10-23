import typing

if typing.TYPE_CHECKING:
    from .models import LookupModel


class LookupRegistry:
    lookups: list[type["LookupModel"]]

    def __init__(self):
        self.lookups = []

    def register(self, model: type["LookupModel"]):
        if model not in self.lookups:
            self.lookups.append(model)

    def install(self):
        """Installs all registered lookups."""
        for model in self.lookups:
            model.install()


lookups = LookupRegistry()
