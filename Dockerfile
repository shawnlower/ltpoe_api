FROM kennethreitz/pipenv
COPY . /app

ENV FLASK_APP=ltpapi
ENV FLASK_ENV=development

ENV APP_CONFIG=config.py 

EXPOSE 5000
CMD exec gunicorn -e APP_CONFIG=$APP_CONFIG -b :5000 --access-logfile - --error-logfile - wsgi:app

