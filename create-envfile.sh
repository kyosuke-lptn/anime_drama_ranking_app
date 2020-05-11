#!/bin/sh

cat << EOS > /usr/src/django/ranking_app/ranking_uwsgi.ini
[uwsgi]
# Django-related settings
# the base directory (full path)
chdir           = /usr/src/django/ranking_app/
SOCKET=127.0.0.1:8001
# Django's wsgi file
module          = ranking_app.wsgi
# process-related settings
# master
master          = true
# maximum number of worker processes
processes       = 10
# the socket (use the full path to be safe
socket          = ${SOCKET}
# ... with appropriate permissions - may be needed
chmod-socket    = 664
# clear environment on exit
vacuum          = true
EOS

cat << EOS > /usr/src/django/ranking_app/.env
# Django
SECRET_KEY=${SECRET_KEY}

# MySQL
DB_ENGINE=${DB_ENGINE}
DB_NAME=${DB_NAME}
DB_USER=${DB_USER}
DB_PASSWORD=${DB_PASSWORD}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

# Twitter API
CONSUMER_KEY=${CONSUMER_KEY}
CONSUMER_SECRET=${CONSUMER_SECRET}
ACCESS_TOKEN=${ACCESS_TOKEN}
SECRET_TOKEN=${SECRET_TOKEN}
EOS

uwsgi --ini /usr/src/django/ranking_app/ranking_uwsgi.ini