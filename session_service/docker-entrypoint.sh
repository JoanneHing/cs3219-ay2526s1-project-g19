#!/bin/sh
set -e

# run migrations
alembic upgrade head

# start app
exec "$@"
