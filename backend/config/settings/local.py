"""
Local development settings.

Extends base.py with development-friendly defaults.
"""

from .base import *  # noqa: F401, F403
from .base import env

# ---------------------------------------------------------------------------
# Debug
# ---------------------------------------------------------------------------
DEBUG = env("DJANGO_DEBUG", default=True)

# ---------------------------------------------------------------------------
# Hosts
# ---------------------------------------------------------------------------
ALLOWED_HOSTS = env("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1", "0.0.0.0"])

# ---------------------------------------------------------------------------
# Email (console backend for local dev)
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# ---------------------------------------------------------------------------
# Static files — simpler storage for dev
# ---------------------------------------------------------------------------
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# ---------------------------------------------------------------------------
# Throttle rates — relaxed for development
# ---------------------------------------------------------------------------
REST_FRAMEWORK_OVERRIDE = {
    "DEFAULT_THROTTLE_RATES": {
        "anon": "600/minute",
        "user": "1200/minute",
    },
}
REST_FRAMEWORK.update(REST_FRAMEWORK_OVERRIDE)  # noqa: F405
