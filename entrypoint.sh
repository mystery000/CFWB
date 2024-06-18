#!/bin/sh

case "$1" in
  "start_app")
    echo "Starting your application..."
    cd app && python run.py
    ;;
  "db_migration")
    echo "run migration..."
    cd app && python3 database.py && alembic upgrade head
    ;;
  *)
    echo "Unknown command: $1"
    exit 1
    ;;
esac