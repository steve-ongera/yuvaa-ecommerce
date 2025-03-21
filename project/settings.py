import os
import dj_database_url

from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-fbdxyz@l6u0g!&gubim20i^k*y&yhinp42e$co=hw7)(dn%hx*'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*','https://c260-2c0f-6300-d09-fd00-816b-11ed-a22e-d0da.ngrok-free.app']


# Application definition

INSTALLED_APPS = [

    'accounts',
    'rest_framework.authtoken',
    'dj_rest_auth',
    'allauth.socialaccount',  # Add this for social account functionality
    
    'rest_framework_simplejwt',
    'django_filters',
    'taggit',
    'rest_framework',
    'settings',
    
    'product.apps.ProductConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    "whitenoise.runserver_nostatic",  # Add this before django.contrib.staticfiles
    'django.contrib.staticfiles',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'dj_rest_auth.registration',
    'orders',
    'rosetta',
    'drf_yasg',
    'django_bootstrap5',


]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 30 ,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

CSRF_TRUSTED_ORIGINS = [
    'https://c260-2c0f-6300-d09-fd00-816b-11ed-a22e-d0da.ngrok-free.app',
]



MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    "django.middleware.locale.LocaleMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    "allauth.account.middleware.AccountMiddleware",
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]

SITE_ID = 1


ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'settings.company_context_processor.get_company_data',
                'orders.cart_context_processor.get_or_create_cart',
                 # Add your custom context processor here
                'settings.brand_context_processors.brands_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}






# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    # # {
    # # #     'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    # # # },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en'

TIME_ZONE = 'Africa/Nairobi'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/



STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL='media/'
MEDIA_ROOT=BASE_DIR / "media"

MEDIA_ROOT = os.path.join(BASE_DIR, "media")
# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_AUTH = {
    'USE_JWT': True,
    'JWT_AUTH_COOKIE': 'jwt-auth',
}


EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

LOCALE_PATHS = ['locale']

LANGUAGES = [
    ("en", ("English")),
]


# settings.py
CELERY_BROKER_URL = 'redis://myredis:6379/0'
CELERY_RESULT_BACKEND = 'redis://myredis:6379/0'

AUTHENTICATION_BACKENDS = (
    'accounts.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
)

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'innovationhubsoftwaresltd@gmail.com'
EMAIL_HOST_PASSWORD = 'wtzg mvcn ztoe qige'
DEFAULT_FROM_EMAIL = 'Yuvaa Fashonna <yuvaafashona@gmail.com>'



MPESA_ENVIRONMENT = 'sandbox'  # Change to 'production' for live environment
MPESA_CONSUMER_KEY = 'your_consumer_key'  # Get from Safaricom Developer Portal
MPESA_CONSUMER_SECRET = 'your_consumer_secret'  # Get from Safaricom Developer Portal
MPESA_SHORTCODE = '174379'  # Your Paybill number
MPESA_PASSKEY = 'your_passkey'  # Get from Safaricom
MPESA_CONFIRMATION_URL = 'https://your-domain.com/mpesa/confirmation/'  # For C2B integration
MPESA_VALIDATION_URL = 'https://your-domain.com/mpesa/validation/'  # For C2B integration


from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'debug',
    messages.INFO: 'info',
    messages.SUCCESS: 'success',
    messages.WARNING: 'warning',
    messages.ERROR: 'error',
}
