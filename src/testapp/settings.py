from pathlib import Path

from django.utils.translation import gettext_lazy as _

SELF_DIR = Path(__file__).resolve().parent
BASE_DIR = SELF_DIR.parent.parent

INSTALLED_APPS = [
    "testapp",
]

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# LANGUAGE_CODE = "en-us"
LANGUAGE_CODE = "es-cr"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", _("English")),
    ("es", _("Spanish")),
]

LOCALE_PATHS = [
    SELF_DIR / "locale",
]
