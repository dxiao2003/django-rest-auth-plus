
def pytest_configure():
    import django
    from django.conf import settings

    settings.configure(
        DEBUG_PROPAGATE_EXCEPTIONS=True,
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:'
            }
        },
        SITE_ID=1,
        SECRET_KEY='not very secret in tests',
        USE_I18N=True,
        USE_L10N=True,
        STATIC_URL='/static/',
        ROOT_URLCONF='tests.urls',
        REST_FRAMEWORK={
            'DEFAULT_AUTHENTICATION_CLASSES': (
                'rest_framework.authentication.BasicAuthentication',
            )
        },
        TEMPLATES = [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'DIRS': [],
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        # Already defined Django-related contexts here

                        # `allauth` needs this from django
                        'django.template.context_processors.request',
                    ],
                },
            },
        ],
        TEMPLATE_LOADERS=(
            'django.template.loaders.filesystem.Loader',
            'django.template.loaders.app_directories.Loader',
        ),
        MIDDLEWARE_CLASSES=(
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ),
        INSTALLED_APPS=(
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'rest_framework.authtoken',
            'rest_auth',
            'allauth',
            'allauth.account',
            'allauth.socialaccount',
            'allauth.socialaccount.providers.facebook',
            'allauth.socialaccount.providers.google',
            'django.contrib.staticfiles',
            'tests',
        ),
        PASSWORD_HASHERS=(
            'django.contrib.auth.hashers.MD5PasswordHasher',
        ),
        REST_SESSION_LOGIN=False,
        SOCIALACCOUNT_PROVIDERS= \
            {'facebook':
                 {'METHOD': 'oauth2',
                  'SCOPE': ['email', 'public_profile', 'user_friends'],
                  'FIELDS': [
                      'id',
                      'email',
                      'name',
                      'first_name',
                      'last_name',
                      'verified',
                      'locale',
                      'timezone',
                      'link',
                      'gender',
                      'updated_time'],
                  'EXCHANGE_TOKEN': True,
                  'VERIFIED_EMAIL': False,
                  'VERSION': 'v2.6'}}
    )

    try:
        import django
        django.setup()
    except AttributeError:
        pass