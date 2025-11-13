web: gunicorn product_importer.wsgi:application --bind 0.0.0.0:$PORT
worker: celery -A product_importer worker --loglevel=info --pool=solo
