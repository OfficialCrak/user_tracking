# Django Traffic Tracking

## Описание
`django-traffic` — это приложение для отслеживания пользовательской активности в Django-проектах. Оно использует middleware и API-интерфейс для сбора информации о посещениях пользователей.

## Установка
1. Установите зависимости:
    ```bash
    pip install django-tracking2
    ```

2. Добавьте `traffic` и `tracking` в `INSTALLED_APPS` в `settings.py`:
    ```python
    INSTALLED_APPS = [
        'django.contrib.admin',
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        'django.contrib.postgres',
        'django_filters',

        'tracking',
        'traffic',

        'drf_yasg',
        'rest_framework',
        'rest_framework.authtoken',
        'corsheaders',
        'rest_framework_swagger',
    ]
    ```

3. Добавьте middleware в `MIDDLEWARE`:
    ```python
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'tracking.middleware.VisitorTrackingMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'traffic.middleware.TrafficTrackingMiddleware',
        'corsheaders.middleware.CorsMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
    ```

4. Настройте шаблоны в `TEMPLATES`:
    ```python
    TEMPLATES = [
        {
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'DIRS': [
                BASE_DIR / 'templates',
                BASE_DIR / 'user_tracking' / 'traffic' / 'templates',
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
    ```

5. Добавьте маршруты `traffic` в `urls.py`:
    ```python
    from django.contrib import admin
    from django.urls import path, include, re_path
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi

    schema_view = get_schema_view(
        openapi.Info(
            title="Traffic API",
            default_version='v1',
        ),
        public=True,
    )

    urlpatterns = [
        path('admin/', admin.site.urls),
        path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^tracking/', include('tracking.urls')),
        path('api/traffic/', include('traffic.urls')),
    ]
    ```

## API
Приложение также предоставляет REST API для получения данных о посещениях.
Документацию можно просмотреть по адресу:
[http://127.0.0.1:8000/docs/](http://127.0.0.1:8000/docs/)

