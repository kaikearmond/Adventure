"""Configuração Django do Pixelmon Adventures.

O projeto usa SQLite apenas no desenvolvimento local. Em Vercel/produção,
configure DATABASE_URL para um PostgreSQL persistente (por exemplo Neon).
"""

import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url
from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


IS_VERCEL = bool(os.getenv("VERCEL"))
DEBUG = env_bool("DEBUG", default=not IS_VERCEL)
_raw_secret_key = os.getenv("DJANGO_SECRET_KEY", "").strip()
if IS_VERCEL and not _raw_secret_key:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY é obrigatório na Vercel.")
SECRET_KEY = _raw_secret_key or "django-insecure-local-development-only"

site_url = os.getenv("SITE_URL", "").strip().rstrip("/")
vercel_url = os.getenv("VERCEL_URL", "").strip()

ALLOWED_HOSTS = ["127.0.0.1", "localhost", ".vercel.app"]
if site_url:
    parsed = urlparse(site_url)
    if parsed.hostname:
        ALLOWED_HOSTS.append(parsed.hostname)
if vercel_url:
    ALLOWED_HOSTS.append(vercel_url)
for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(","):
    host = host.strip()
    if host:
        ALLOWED_HOSTS.append(host)

CSRF_TRUSTED_ORIGINS = ["https://*.vercel.app"]
if site_url.startswith(("http://", "https://")):
    CSRF_TRUSTED_ORIGINS.append(site_url)
for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(","):
    origin = origin.strip()
    if origin:
        CSRF_TRUSTED_ORIGINS.append(origin)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "store",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "store.middleware.PlayerGateMiddleware",
]

ROOT_URLCONF = "pixelmon_adventures.urls"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "store.context_processors.player_context",
            ],
        },
    },
]
WSGI_APPLICATION = "pixelmon_adventures.wsgi.application"

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if DATABASE_URL:
    DATABASES = {
        "default": dj_database_url.parse(
            DATABASE_URL,
            conn_max_age=0,
            conn_health_checks=True,
        )
    }
else:
    if IS_VERCEL:
        raise ImproperlyConfigured("DATABASE_URL é obrigatório na Vercel. Conecte um PostgreSQL persistente antes do deploy.")
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PLAYER_SESSION_KEY = "pixelmon_nickname"
CART_SESSION_KEY = "pixelmon_cart"

# Mercado Pago. Access Token e Webhook Secret nunca devem entrar no Git.
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY", "").strip()
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "").strip()
MERCADOPAGO_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "").strip()
MERCADOPAGO_API_BASE = "https://api.mercadopago.com"
MERCADOPAGO_MAX_INSTALLMENTS = 6
MERCADOPAGO_NOTIFICATION_URL = os.getenv("MERCADOPAGO_NOTIFICATION_URL", "").strip()
SITE_URL = site_url

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
