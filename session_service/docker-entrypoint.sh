#!/bin/sh
set -e

# Register kafka schema registry schemas
if [ -f "kafka/scripts/register_schemas.py" ]; then
  echo "Registering Kafka schemas..."
  python -m kafka.scripts.register_schemas || echo "Schema registration failed or already done."
else
  echo "No schema registration script found. Skipping..."
fi

# run migrations
alembic upgrade head

# start app
exec "$@"
