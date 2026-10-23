from django.test import TestCase
from django.utils import translation

from django_lookups import lookups

from .models import Order, Other, Status, Study


class BasicTests(TestCase):
    def setUp(self):
        lookups.install()

    def test_int_lookup(self):
        # Test that IntLookups can be compared directly to ints.
        self.assertEqual(Study.ONE, 1)
        # Test that Lookups can be used as dict keys and accessed by pk, and vice versa.
        d = {1: "yes"}
        self.assertEqual(d[Study.ONE], "yes")
        d = {Study.ONE: "yes"}
        self.assertEqual(d[1], "yes")
        # Test that filter lookups work (calls __int__ in this case).
        s = Study.objects.get(pk=Study.ONE)
        self.assertEqual(s, Study.ONE)
        # Tests non-pk/label attribute lookups.
        self.assertEqual(s.abbreviation, Study.ONE.abbreviation)
        # Test properties.
        self.assertFalse(Study.TWO.is_active)
        with self.assertRaises(AttributeError):
            _ = Study.TWO.unknown_attr

    def test_str_lookup(self):
        # Test that CharLookups can be compared directly to strs.
        self.assertEqual(Status.NEW, "NEW")
        # Test that Lookups can be used as dict keys and accessed by pk, and vice versa.
        d = {"NEW": "yes"}
        self.assertEqual(d[Status.NEW], "yes")
        d = {Status.NEW: "yes"}
        self.assertEqual(d["NEW"], "yes")
        # Test that filter lookups work (calls __int__ in this case).
        s = Status.objects.get(pk=Status.NEW.pk)
        self.assertEqual(s, Status.NEW)
        self.assertEqual(Status.COMPLETED.name, "COMPLETED")
        self.assertEqual(Status.COMPLETED.pk, "DONE")

    def test_translation_and_unnamed(self):
        s = Study.objects.create(
            pk=100,
            msgid="Unnamed Study",
            translations={"es": "Translated"},
        )
        self.assertNotIn(s, set(Study))
        self.assertIn(Study.ONE, set(Study))
        with translation.override("es"):
            self.assertEqual(Study.FOUR.pk, 4)
            self.assertEqual(Study.FOUR.name, "FOUR")
            self.assertEqual(Study.FOUR.msgid, "Study Four")
            self.assertEqual(Study.FOUR.label, "Estudio Quatro")
            self.assertEqual(str(Study.FOUR), "Estudio Quatro")
            # Not all lookups need to be defined on the class
            self.assertEqual(s.pk, 100)
            self.assertIsNone(s.name)
            self.assertEqual(s.msgid, "Unnamed Study")
            self.assertEqual(s.label, "Translated")
            self.assertEqual(str(s), "Translated")
            self.assertEqual(Status.NEW.label, "Nuevo")
            self.assertEqual(Status.NEW.pk, "NEW")
            self.assertEqual(Other.NEW.label, "Nuevo")
            self.assertEqual(Other.NEW.pk, "initial")
        # Unknown languages fall back to the msgid.
        for lang in ("en", "fr"):
            with translation.override(lang):
                self.assertEqual(Study.FOUR.label, "Study Four")
                self.assertEqual(s.label, "Unnamed Study")

    def test_instance_lookup(self):
        self.assertIs(Study.ONE.TWO, Study.TWO)

    def test_equality(self):
        self.assertIsInstance(Status.NEW, Status)
        self.assertNotEqual(Status.NEW, Status.IN_PROGRESS)
        self.assertNotEqual(Status.NEW, Other.NEW)
        self.assertEqual(Status.NEW, "NEW")
        # CharLookup compares equal to its pk, not its name.
        self.assertEqual(Other.NEW, "initial")
        self.assertNotEqual(Other.NEW, "NEW")

    def test_iterable(self):
        self.assertEqual(
            list(Status),
            [Status.NEW, Status.IN_PROGRESS, Status.COMPLETED],
        )

    def test_subscript(self):
        self.assertEqual(Study[1], Study.ONE)
        self.assertEqual(Study["ONE"], Study.ONE)
        self.assertEqual(Status["NEW"], Status.NEW)
        self.assertEqual(Other["NEW"], Other.NEW)
        self.assertEqual(Other["initial"], Other.NEW)
        for key in ("asdf", 17, 0, None):
            with self.assertRaises(IndexError) as cm:
                Study[key]
            self.assertEqual(str(cm.exception), f"Study[{key!r}]")

    def test_keys(self):
        o = Order.objects.create()
        self.assertEqual(o.study, Study.ONE)
        self.assertEqual(o.study_id, Study.ONE)
        self.assertEqual(o.status, Status.NEW)
        self.assertEqual(o.status_id, Status.NEW)
        self.assertNotEqual(o.status, Other.NEW)
        self.assertEqual(Order.objects.filter(study=Study.ONE).count(), 1)
        self.assertEqual(Order.objects.filter(study_id=Study.ONE).count(), 1)
        # This works because IntLookup defines __int__
        self.assertEqual(Order.objects.filter(study__pk=Study.ONE).count(), 1)
        self.assertEqual(
            Order.objects.filter(study__abbreviation=Study.ONE.abbreviation).count(), 1
        )
        self.assertEqual(Order.objects.filter(status=Status.NEW).count(), 1)
        self.assertEqual(Order.objects.filter(status_id=Status.NEW).count(), 1)
        # String queries can't use the lookup directly since __str__ returns label
        self.assertEqual(Order.objects.filter(status__pk=Status.NEW.pk).count(), 1)
        self.assertFalse(o.status.is_completed)
        with self.assertRaises(ValueError):
            Order.objects.filter(status=Other.NEW)
        with self.assertRaises(ValueError):
            Order.objects.filter(status_id=Other.NEW)

    def test_install(self):
        # Override abbreviation so we can test that it gets reset on install.
        Study.objects.filter(pk=1).update(abbreviation="1")
        s = Study.objects.get(pk=1)
        self.assertEqual(s.abbreviation, "1")
        Study.install()
        s.refresh_from_db()
        self.assertEqual(s.abbreviation, "I")
