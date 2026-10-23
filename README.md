# django-lookups-i18n

A project born of the desire to stop defining separate enums for every lookup model. Lookups can have either integer or string primary keys and work just like normal Django models (because they are!):

```python
from typing import Self
from django_lookups.models import CharLookup, IntLookup, Lookup


class Study(IntLookup):
    # Lookups can have extra fields, passed as kwargs to `Lookup` when defined.
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
    # String lookups use the defined name as PK, but can be overridden.
    NEW: Self = Lookup(_("New"))
    IN_PROGRESS: Self = Lookup(_("In Progress"))
    COMPLETED: Self = Lookup(_("Completed"), pk="DONE")

    @property
    def is_completed(self):
        return self == Status.COMPLETED
```

Notice the lookups are typed as `Self` -- `Lookup` is a descriptor that will return actual model singletons when accessed. So `Study.ONE` is an actual `Study` instance (and will be the same instance every time).


## Installing lookups

If you want all defined lookups to be installed on migration, add `django_lookups` to your `INSTALLED_APPS`. Otherwise, you can call `django_lookups.install()` to manually create all registered lookups.


## Translations

When you pass a translatable string for the lookup label, a translation for each language in `LANGUAGES` is computed and stored. The `LookupModel.label` property (called by `__str__`) will get the current translation and return the translated label if available. `LookupModel.msgid` is always the untranslated label string. Setting `USE_I18N` to `False` bypasses translations entirely. It is recommended to limit `LANGUAGES` to those you have (or expect) translations for.


## Equality and hashability

In order to make these lookup models behave more similar to enums, `CharLookup` will compare equal to PK strings, and `IntLookup` will compare equal to PK ints. So from the models above, `Study.ONE == 1` and `Status.NEW == "NEW"` are both `True`. This also means they are interchangeable as dict keys, so `{Study.ONE: "yes"}[1] == "yes"` and `{1: "yes"}[Study.ONE] == "yes"`. See the unit tests for more examples.
