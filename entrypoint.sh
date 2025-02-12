#!/bin/sh

echo "Waiting for db_user_tracking to be ready..."
./wait-for-it.sh db_user_tracking 5432 60

echo "Run migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collect static files..."
python manage.py collectstatic --noinput

echo "Create superuser (if not have)..."
python manage.py shell <<EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("Superuser 'admin' create!")
else:
    print("Superuser has already been created")
EOF

echo "Starting Gunicorn..."
exec gunicorn --bind 0.0.0.0:8000 user_tracking.wsgi:application