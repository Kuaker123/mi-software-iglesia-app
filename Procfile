release: python manage.py migrate --noinput && DJANGO_SUPERUSER_USERNAME=$DJANGO_SUPERUSER_USERNAME DJANGO_SUPERUSER_EMAIL=$DJANGO_SUPERUSER_EMAIL DJANGO_SUPERUSER_PASSWORD=$DJANGO_SUPERUSER_PASSWORD python manage.py createsuperuser --noinput || echo "Superuser already exists, skipping creation"
web: gunicorn iglesia_project.wsgi:application --log-file -
