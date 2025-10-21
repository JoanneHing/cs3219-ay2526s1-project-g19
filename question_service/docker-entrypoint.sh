#!/bin/bash
set -e

# Register kafka schema registry schemas
if [ -f "question_service/kafka/scripts/register_schemas.py" ]; then
  echo "Registering Kafka schemas..."
  python -m question_service.kafka.scripts.register_schemas || echo "Schema registration failed or already done."
else
  echo "No schema registration script found. Skipping..."
fi

# Start main service
echo "Starting main application..."
exec "$@"


if [ "$SKIP_DB_SETUP" != "true" ]; then
  DB_HOST=${DB_HOST:-localhost}
  DB_PORT=${DB_PORT:-5432}
  PORT=${PORT:-8000}

  echo "Waiting for database at $DB_HOST:$DB_PORT..."
  while ! nc -z $DB_HOST $DB_PORT; do
    echo "Database not ready, waiting..."
    sleep 1
  done
  echo "Database started"

  echo "Running migrations..."
  python manage.py makemigrations --noinput
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput
  echo "Starting server on port $PORT..."
else
  echo "Starting Kafka consumer..."
fi

exec "$@"
