from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': (
                ('django.template.loaders.cached.Loader', (
                    'hamlpy.template.loaders.HamlPyFilesystemLoader',
                    'hamlpy.template.loaders.HamlPyAppDirectoriesLoader',
                )),
            ),
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': env('DB_ENGINE'),
        'NAME': env('DB_NAME'),
        'USER': env('DB_USER'),
        'PASSWORD': env('DB_PASSWORD'),
        'HOST': env('DB_HOST'),
        'PORT': env('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
        },
        'ATOMIC_REQUESTS': True,
    }
}

# TODO (sumitani) 本番環境でのLOG設定を追加する

# TODO (sumitani) staticファイルを配信する時に本番環境では、プロキシサーバなどに配置するように設定する
