from typing import Self

from django.db import models
from django.utils.translation import gettext_lazy as _

from django_lookups import CharLookup, IntLookup, Lookup


class Study(IntLookup):
    abbreviation = models.CharField(max_length=20)

    ONE: Self = Lookup(_("Study One"), pk=1, abbreviation="I")
    TWO: Self = Lookup(_("Study Two"), pk=2, abbreviation="II")
    THREE: Self = Lookup(_("Study Three"), pk=3, abbreviation="III")
    FOUR: Self = Lookup(_("Study Four"), pk=4, abbreviation="IV")
    FIVE: Self = Lookup(_("Study Five"), pk=5, abbreviation="V")

    @property
    def is_active(self) -> bool:
        return self != Study.TWO


class Status(CharLookup):
    NEW: Self = Lookup(_("New"))
    IN_PROGRESS: Self = Lookup(_("In Progress"))
    COMPLETED: Self = Lookup(_("Completed"), pk="DONE")

    @property
    def is_completed(self):
        return self == Status.COMPLETED


class Other(CharLookup):
    NEW: Self = Lookup(_("New"), pk="initial")


class Order(models.Model):
    study = models.ForeignKey(Study, default=Study.ONE, on_delete=models.CASCADE)
    status = models.ForeignKey(Status, default=Status.NEW, on_delete=models.CASCADE)
