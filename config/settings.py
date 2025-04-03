import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import timedelta
import sys
from decimal import Decimal

# 判断是否在测试环境中
TESTING = 'pytest' in sys.modules

# Load environment variables
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'ppu30n^mbwg^$&4h@jw#^#9c)ryii9$cqr7^acy#4k0m+appel')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', 'freight.test', '0.0.0.0']

# SSL settings
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = not DEBUG
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

# CORS settings
CORS_ORIGIN_ALLOW_ALL = True if DEBUG else False
CORS_ALLOW_ALL_ORIGINS = True if DEBUG else False
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = [
    'https://127.0.0.1:5175',
    'https://localhost:5175',
    'https://freight.test',
    'http://127.0.0.1:5176',
    'http://localhost:5176',  # 添加HTTP版本
]

CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
    'x-request-id',
    'x-frontend-origin',
    'x-frontend-debug',
    'cache-control',
    'pragma',
    'expires',
    'x-debug',
    'x-raw-data',
    'x-loading-type',
]

CORS_EXPOSE_HEADERS = [
    'content-type',
    'content-length',
    'access-control-allow-origin',
    'access-control-allow-credentials',
]

CORS_PREFLIGHT_MAX_AGE = 86400  # 24小时
CORS_URLS_REGEX = r'^/api/.*$'

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else 'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '300/hour',  # 提高匿名用户限制
        'user': '3000/hour',  # 提高认证用户限制
        'auth': '60/minute',  # 认证类请求限流
        'token_refresh': '30/minute',  # token刷新限流，每分钟允许更多请求
        'login': '20/minute',  # 登录限流，防止暴力破解但更合理
        'monitoring': '300/minute',  # 监控请求限流
    },
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1'],
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'UNAUTHENTICATED_URLS': [
        'api/v1/users/token/',
        'api/v1/users/refresh/',
        'api/v1/users/login/',
        'api/v1/users/register/',
        'api/v1/users/verify/',
        'api/v1/users/reset-password/',
        'api/v1/users/reset-password-confirm/',
        'api/v1/core/health/',
        'api/v1/core/metrics/',
        'api/v1/core/csrf/',
        'api/v1/core/monitoring/slow-request/',
        'api/v1/core/monitoring/performance/',
        'api/v1/products/product-types/',
        'api/v1/products/surcharges/by_product/',
        'api/v1/products/peak-season-surcharges/by_product/',
        'api/v1/products/base-fees/by_product/',
        'admin/',
    ],
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=int(os.getenv('JWT_ACCESS_TOKEN_LIFETIME', 24))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.getenv('JWT_REFRESH_TOKEN_LIFETIME', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': os.getenv('JWT_SECRET_KEY', SECRET_KEY),
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'user_id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
    'TOKEN_USER_CLASS': 'rest_framework_simplejwt.models.TokenUser',
    'SLIDING_TOKEN_REFRESH_EXP_CLAIM': 'refresh_exp',
    'SLIDING_TOKEN_LIFETIME': timedelta(hours=24),
    'SLIDING_TOKEN_REFRESH_LIFETIME': timedelta(days=7),
    'AUTH_COOKIE': 'refresh_token',
    'AUTH_COOKIE_DOMAIN': None,
    'AUTH_COOKIE_SECURE': False if DEBUG else True,
    'AUTH_COOKIE_HTTP_ONLY': True,
    'AUTH_COOKIE_PATH': '/',
    'AUTH_COOKIE_SAMESITE': 'Lax',
}

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_NAME = 'sessionid'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 7  # 7天
SESSION_COOKIE_DOMAIN = None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_SAVE_EVERY_REQUEST = True

# CSRF settings
CSRF_COOKIE_NAME = 'csrftoken'
CSRF_HEADER_NAME = 'HTTP_X_CSRFTOKEN'
CSRF_USE_SESSIONS = False  # 使用cookie存储
CSRF_COOKIE_AGE = 60 * 60 * 24 * 7  # 7天
CSRF_COOKIE_PATH = '/'
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://127.0.0.1:5175',
    'https://localhost:5175',
    'https://freight.test',
]

CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'simple_history',
    'rosetta',
    'rest_framework.authtoken',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'django_celery_results',
    'django_extensions',
    
    # Local apps
    'apps.core.apps.CoreConfig',
    'apps.users.apps.UsersConfig',
    'apps.products.apps.ProductsConfig',
    'apps.postal_codes.apps.PostalCodesConfig',
    'apps.fuel_rates.apps.FuelRatesConfig',
    'apps.calculator.apps.CalculatorConfig',
    'channels',
]

# 根据环境配置中间件
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.JWTAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.core.middleware.RequestLoggingMiddleware',
    'apps.core.middleware.APIMonitorMiddleware',
    'apps.core.middleware.ExceptionMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'frontend', 'public'),
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'freight',
        'USER': 'root',
        'PASSWORD': 'root',
        'HOST': '127.0.0.1',
        'PORT': '3306',
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        }
    }
}

# 设置最大长度限制
DJANGO_CELERY_RESULTS_TASK_ID_MAX_LENGTH = 191  # 减小任务ID的最大长度

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_L10N = True
USE_TZ = True

# 设置可用语言
LANGUAGES = [
    ('zh-hans', '中文简体'),
]

# 添加中文本地化配置
LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'locale'),
]

# Rosetta settings
ROSETTA_SHOW_AT_ADMIN_PANEL = False  # 禁用管理面板中的Rosetta入口
ROSETTA_MESSAGES_PER_PAGE = 50
ROSETTA_ENABLE_TRANSLATION_SUGGESTIONS = False
ROSETTA_REQUIRES_AUTH = True
ROSETTA_POFILENAMES = ['django.po']
ROSETTA_WSGI_AUTO_RELOAD = True
ROSETTA_UWSGI_AUTO_RELOAD = True
ROSETTA_LANGUAGE_GROUPS = False

# 设置项目路径
SITE_ROOT = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.dirname(SITE_ROOT)
ROSETTA_EXCLUDED_PATHS = [
    os.path.join(PROJECT_ROOT, 'venv'),
    os.path.join(PROJECT_ROOT, 'frontend'),
]

# 确保翻译目录存在
LOCALE_DIR = os.path.join(BASE_DIR, 'locale')
if not os.path.exists(LOCALE_DIR):
    os.makedirs(LOCALE_DIR)
if not os.path.exists(os.path.join(LOCALE_DIR, 'zh_Hans', 'LC_MESSAGES')):
    os.makedirs(os.path.join(LOCALE_DIR, 'zh_Hans', 'LC_MESSAGES'))

# 创建一个空的翻译文件（如果不存在）
PO_FILE = os.path.join(LOCALE_DIR, 'zh_Hans', 'LC_MESSAGES', 'django.po')
if not os.path.exists(PO_FILE):
    with open(PO_FILE, 'w', encoding='utf-8') as f:
        f.write('''msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\\n"
"Report-Msgid-Bugs-To: \\n"
"POT-Creation-Date: 2025-02-17 11:00+0800\\n"
"PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE\\n"
"Last-Translator: FULL NAME <EMAIL@ADDRESS>\\n"
"Language-Team: LANGUAGE <LL@li.org>\\n"
"Language: zh_Hans\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
"Plural-Forms: nplurals=1; plural=0;\\n"
''')

# Cache Configuration
REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1')
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

if TESTING:
    CACHES['default'] = {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
    }

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = 'freight_middleware'

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles'),
    os.path.join(BASE_DIR, 'frontend', 'dist'),  # 添加前端构建目录
]

# 确保目录存在
for directory in [STATIC_ROOT] + STATICFILES_DIRS:
    if not os.path.exists(directory):
        os.makedirs(directory)

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Swagger settings
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
        }
    },
    'USE_SESSION_AUTH': False,
    'JSON_EDITOR': True,
    'SUPPORTED_SUBMIT_METHODS': [
        'get',
        'post',
        'put',
        'delete',
        'patch'
    ],
}

# Simple History settings
SIMPLE_HISTORY_HISTORY_CHANGE_REASON_USE_TEXT_FIELD = True

# Celery settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', REDIS_URL)
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', REDIS_URL)
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60
CELERY_BEAT_SCHEDULE = {
    'monitor-system-resources': {
        'task': 'apps.core.tasks.monitor_system_health',
        'schedule': timedelta(minutes=5),
        'options': {
            'queue': 'monitoring',
            'priority': 5,
            'retry': True,
            'retry_policy': {
                'max_retries': 3,
                'interval_start': 0,
                'interval_step': 0.2,
                'interval_max': 0.5,
            }
        }
    },
    'backup-database': {
        'task': 'apps.core.tasks.backup_database',
        'schedule': timedelta(hours=24),
        'options': {
            'queue': 'maintenance',
            'priority': 3,
            'retry': True,
            'retry_policy': {
                'max_retries': 3,
                'interval_start': 60,
                'interval_step': 60,
                'interval_max': 180,
            }
        }
    },
    'clean-old-records': {
        'task': 'apps.core.tasks.clean_old_records',
        'schedule': timedelta(days=1),
        'options': {
            'queue': 'maintenance',
            'priority': 1,
            'retry': True,
            'retry_policy': {
                'max_retries': 2,
                'interval_start': 300,
                'interval_step': 300,
                'interval_max': 900,
            }
        }
    },
    'warm-cache': {
        'task': 'apps.core.tasks.warm_cache',
        'schedule': timedelta(hours=1),
        'options': {
            'queue': 'maintenance',
            'priority': 4,
            'retry': True,
            'retry_policy': {
                'max_retries': 3,
                'interval_start': 30,
                'interval_step': 30,
                'interval_max': 90,
            }
        }
    }
}
CELERY_TASK_ALWAYS_EAGER = False

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'apps.core.middleware': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# 确保日志目录存在
LOG_DIR = os.path.join(BASE_DIR, 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Cache time to live is 15 minutes
CACHE_TTL = 60 * 15

# Security settings
SECURE_REFERRER_POLICY = 'same-origin'
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'  # 开发环境使用控制台输出
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'noreply@example.com')

# Admin settings
ADMINS = [x.split(':') for x in os.getenv('DJANGO_ADMINS', 'admin:admin@example.com').split(',')]
MANAGERS = ADMINS

# Messages settings
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Date and time formats
DATE_FORMAT = 'Y-m-d'
DATETIME_FORMAT = 'Y-m-d H:i:s'
DATE_INPUT_FORMATS = ['%Y-%m-%d']
DATETIME_INPUT_FORMATS = ['%Y-%m-%d %H:%M:%S']

# Ensure required directories exist
for directory in [STATIC_ROOT, MEDIA_ROOT, LOG_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

# 确保URL以斜杠结尾
APPEND_SLASH = True

# 性能监控配置
PERFORMANCE_MONITORING = {
    'SLOW_QUERY_THRESHOLD': 1.0,  # 慢查询阈值（秒）
    'ENABLE_QUERY_LOGGING': True,  # 是否启用查询日志
    'ENABLE_PERFORMANCE_LOGGING': True,  # 是否启用性能日志
    'ENABLE_SECURITY_LOGGING': True,  # 是否启用安全日志
}

# 性能监控阈值设置
SLOW_REQUEST_THRESHOLD = float(os.getenv('SLOW_REQUEST_THRESHOLD', 1.0))
HIGH_CPU_THRESHOLD = int(os.getenv('HIGH_CPU_THRESHOLD', 80))
HIGH_MEMORY_THRESHOLD = int(os.getenv('HIGH_MEMORY_THRESHOLD', 80))
HIGH_DISK_THRESHOLD = int(os.getenv('HIGH_DISK_THRESHOLD', 80))
HIGH_ERROR_RATE_THRESHOLD = 5  # 错误率告警阈值(%)
HIGH_SLOW_RATE_THRESHOLD = 10  # 慢请求比例告警阈值(%)
HIGH_QUERY_TIME_THRESHOLD = 0.5  # 数据库查询时间告警阈值(秒)
LOW_CACHE_HIT_RATE_THRESHOLD = 50  # 缓存命中率告警阈值(%)

# 资源泄漏告警阈值
MEMORY_GROWTH_THRESHOLD = 10 * 1024 * 1024  # 内存增长告警阈值(字节)
THREAD_GROWTH_THRESHOLD = 5  # 线程增长告警阈值
FD_GROWTH_THRESHOLD = 10  # 文件描述符增长告警阈值

# 性能数据保留时间
PERFORMANCE_DATA_RETENTION_DAYS = 30

# 告警通知配置
ALERT_EMAIL_RECIPIENTS = os.getenv('ALERT_EMAIL_RECIPIENTS', '').split(',')
DINGTALK_WEBHOOK_URL = os.getenv('DINGTALK_WEBHOOK_URL', '')
ALERT_WEBHOOK_URL = os.getenv('ALERT_WEBHOOK_URL', '')

# 性能监控日志配置
LOGGING['loggers']['apps.core.middleware'] = {
    'handlers': ['console'],
    'level': 'INFO',
    'propagate': True,
}

# drf-spectacular settings
SPECTACULAR_SETTINGS = {
    'TITLE': '运费计算系统 API',
    'DESCRIPTION': '运费计算系统后端 API 文档',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'REDOC_DIST': 'SIDECAR',
    'COMPONENT_SPLIT_REQUEST': True,
    'SORT_OPERATIONS': False,
    'SWAGGER_UI_SETTINGS': {
        'deepLinking': True,
        'persistAuthorization': True,
        'displayOperationId': True,
    },
    'PREPROCESSING_HOOKS': [
        'apps.core.schema.preprocessing_filter_spec',
    ],
    'POSTPROCESSING_HOOKS': [
        'apps.core.schema.postprocessing_filter_spec',
    ],
    'SCHEMA_PATH_PREFIX': '/api/v1/',
    'SCHEMA_PATH_PREFIX_TRIM': True,
    'SERVE_AUTHENTICATION': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'TAGS': [
        {'name': '运费计算', 'description': '运费计算相关接口'},
        {'name': '产品管理', 'description': '产品管理相关接口'},
        {'name': '邮编管理', 'description': '邮编和分区管理相关接口'},
        {'name': '燃油费率', 'description': '燃油费率管理相关接口'},
        {'name': '系统管理', 'description': '系统配置和管理相关接口'},
        {'name': '用户管理', 'description': '用户管理相关接口'},
        {'name': '通知管理', 'description': '通知管理相关接口'},
        {'name': '系统监控', 'description': '系统监控相关接口'},
    ],
}

# 批量处理配置
MAX_BATCH_RECORDS = 100000  # 最大批量记录数
BATCH_CHUNK_SIZE = 2000     # 减小分片大小以提高并行度
MAX_WORKERS = min(50, os.cpu_count() * 4)  # 增加工作线程数
BATCH_PROCESSING_TIMEOUT = 7200  # 批量处理超时时间（秒）

# 并行处理优化
OPTIMAL_THREAD_COUNT = min(50, os.cpu_count() * 4)  # 增加最大线程数
PROCESS_POOL_SIZE = os.cpu_count()  # 进程池大小

# 缓存配置
CACHE_WARM_SAMPLE_SIZE = 2000  # 增加缓存预热的样本大小
CACHE_TTL = 3600  # 缓存过期时间（秒）

# 数据库连接池优化
DATABASE_CONNECTION_POOL_SETTINGS = {
    'MAX_OVERFLOW': 25,  # 增加最大溢出连接数
    'POOL_SIZE': 20,    # 增加连接池大小
    'RECYCLE': 300,     # 连接回收时间
}

# 最大重量限制
MAX_WEIGHT_LIMIT = Decimal('1000.00')

# 计算服务配置
MAX_WORKERS = min(32, os.cpu_count() * 2)
PROCESS_POOL_SIZE = MAX_WORKERS
CALCULATION_CACHE_TTL = 3600  # 缓存过期时间（秒）
MAX_BATCH_CALCULATION_SIZE = 100  # 单次批量计算最大记录数
BATCH_CHUNK_SIZE = 5000  # 批量处理分块大小
MAX_BATCH_RECORDS = 100000  # 最大批量记录数
BULK_INSERT_SIZE = 1000  # 批量插入大小
BATCH_PROCESSING_TIMEOUT = 7200  # 批量处理超时时间（秒）
LOCAL_CACHE_SIZE = 1000  # 本地缓存大小
EXCEL_CHUNK_SIZE = 5000  # Excel处理分块大小
CACHE_WARM_SAMPLE_SIZE = 100  # 缓存预热样本大小

# 默认单位配置
DEFAULT_WEIGHT_UNIT = 'KG'  # 默认重量单位
DEFAULT_DIMENSION_UNIT = 'CM'  # 默认尺寸单位

# 前端URL配置，用于构建重置密码链接等
FRONTEND_URL = 'https://freight.test'