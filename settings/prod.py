from settings.base import *  # noqa
from settings.conf import BASE_DIR

DEBUG = True
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}


CORS_ALLOWED_ORIGINS = [
    "*",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
# Allow All Origins
CORS_ALLOW_CREDENTIALS = True
