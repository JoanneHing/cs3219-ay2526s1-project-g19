#!/bin/bash
set -e

DB_HOST=${DB_HOST:-localhost}
DB_PORT=${DB_PORT:-5432}
PORT=${PORT:-8000}

register_schemas() {
  if [ -f "question_service/kafka/scripts/register_schemas.py" ]; then
    echo "Registering Kafka schemas..."
    python -m question_service.kafka.scripts.register_schemas || echo "Schema registration failed or already done."
  else
    echo "No schema registration script found. Skipping schema registration..."
  fi
}

wait_for_db() {
  echo "Waiting for database at ${DB_HOST}:${DB_PORT}..."
  while ! nc -z "${DB_HOST}" "${DB_PORT}"; do
    echo "Database not ready, waiting..."
    sleep 1
  done
  echo "Database available."
}

run_migrations() {
  echo "Running migrations..."
  python manage.py migrate --noinput
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
}

main() {
  register_schemas

  if [ "${SKIP_DB_SETUP}" != "true" ]; then
    wait_for_db
    run_migrations
  else
    echo "SKIP_DB_SETUP is true; skipping migrations and collectstatic."
  fi

  echo "Starting main application..."
  exec "$@"
}

main "$@"
