from functools import cached_property
from typing import ClassVar

from django.conf import settings
from django.db import models
from django.db.models.base import ModelBase
from django.utils import translation
from django.utils.functional import Promise

from .registry import lookups


class LookupBase(ModelBase):
    # LookupModels stash their Lookup descriptors on the class.
    # Typed here so its not public API.
    _lookups: ClassVar[list["Lookup"]]

    def __iter__(cls):
        """Iterating over a LookupModel should yield all defined lookups."""
        for lkup in cls._lookups:
            yield lkup.db_object

    def __getitem__(cls, key):
        """Defined lookups can be retrieved by pk or name."""
        for obj in cls:
            if key in (obj.pk, obj.name):
                return obj
        raise IndexError(f"{cls.__name__}[{key!r}]")

    def _prepare(cls):
        """Only called for non-abstract models, which is what we want."""
        super()._prepare()
        lookups.register(cls)


class LookupModel(models.Model, metaclass=LookupBase):
    name = models.CharField(
        max_length=100,
        help_text="Name defined on the class",
        null=True,
        blank=True,
        unique=True,
        default=None,
    )
    msgid = models.TextField(help_text="Base language text (msgid when localizing)")
    translations = models.JSONField(
        default=dict,
        help_text="All known translations of msgid",
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.label

    @property
    def label(self):
        # Fast path for if i18n is turned off or we don't have any translations.
        if not settings.USE_I18N or not self.translations:
            return self.msgid
        lang_code = translation.get_language() or settings.LANGUAGE_CODE
        # First look for the specific language (like `es-mx`) in translations.
        if lang_code in self.translations:
            return self.translations[lang_code]
        # If it's not there, check for just the base language (`es`).
        lang = lang_code.split("-")[0]
        if lang in self.translations:
            return self.translations[lang]
        # Otherwise use the untranslated msgid.
        return self.msgid

    @classmethod
    def install(cls):
        objects = list(cls)
        if not objects:
            return
        cls.objects.bulk_create(
            objects,
            update_conflicts=True,
            update_fields=[f.name for f in cls._meta.fields if not f.primary_key],
            unique_fields=(cls._meta.pk.name,),
        )


class IntLookup(LookupModel):
    id = models.IntegerField(primary_key=True)

    class Meta:
        abstract = True

    def __int__(self):
        """
        This is so we can be directly cast to an int (e.g. `int(Status.NEW)`), which is
        what Django does when filtering.
        """
        return self.pk

    def __eq__(self, other):
        if isinstance(other, int):
            return self.pk == other
        return super().__eq__(other)

    def __hash__(self):
        # This won't be automatically inherited since we override __eq__.
        return hash(self.pk)


class CharLookup(LookupModel):
    id = models.CharField(max_length=100, primary_key=True)

    class Meta:
        abstract = True

    def __eq__(self, other):
        if isinstance(other, str):
            return self.pk == other
        return super().__eq__(other)

    def __hash__(self):
        # This won't be automatically inherited since we override __eq__.
        return hash(self.pk)


class Lookup:
    def __init__(self, label: str | Promise, pk=None, **attrs):
        self.translations = {}
        if settings.USE_I18N and isinstance(label, Promise):
            with translation.override(None):
                self.msgid = str(label)
            for lang, _name in settings.LANGUAGES:
                with translation.override(lang):
                    self.translations[lang] = str(label)
        else:
            self.msgid = str(label)
        self.pk = pk
        self.attrs = attrs
        # These get set in contribute_to_class
        self.name = None
        self.model = None

    def _instance(self, **overrides):
        return self.model(
            **{
                self.model._meta.pk.name: self.pk,
                "name": self.name,
                "msgid": self.msgid,
                "translations": self.translations,
                **self.attrs,
                **overrides,
            }
        )

    @cached_property
    def db_object(self):
        return self._instance()

    def __get__(self, instance, owner):
        """Always return the singleton instance of the DB object."""
        return self.db_object

    def contribute_to_class(self, cls: type[LookupModel], name: str, **kwargs):
        self.model = cls
        self.name = name
        if not hasattr(self.model, "_lookups"):
            self.model._lookups = []
        self.model._lookups.append(self)
        # Allow CharLookups to omit a `pk` and just use the defined name.
        if self.pk is None:
            # We don't have access to cls._meta.pk here, so this is a brittle subclass
            # check. We could probably do this in a custom cls._prepare, but that's
            # even less documented/supported than this.
            if not issubclass(cls, CharLookup):
                raise TypeError(
                    "{cls.__name__}.{name}: `pk` may only be omitted for CharLookup"
                )
            self.pk = name
        setattr(cls, name, self)
