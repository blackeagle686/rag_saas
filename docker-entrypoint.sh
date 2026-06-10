#!/bin/bash
set -e

echo "Starting RAGaaS Entrypoint script..."

# Wait for database to be ready
echo "Waiting for PostgreSQL to be ready..."
# We use python to ping the database instead of installing psql client
python -c "
import sys, psycopg2, os
from urllib.parse import urlparse

db_url = os.environ.get('DATABASE_URL')
if not db_url:
    print('No DATABASE_URL found')
    sys.exit(1)

# Replace postgresql+asyncpg with postgresql for psycopg2
db_url = db_url.replace('+asyncpg', '')

try:
    conn = psycopg2.connect(db_url)
    conn.close()
    print('Database connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'Database connection failed: {e}')
    sys.exit(1)
" || {
    echo "PostgreSQL is not ready or database doesn't exist yet."
    echo "Attempting to create database and user from DATABASE_URL..."
    
    # Optional: If you need python to auto-create the DB by connecting to the default postgres database
    # This requires superuser access which the connection string might not have.
    # In Docker, the postgres container automatically creates the DB and user using POSTGRES_DB and POSTGRES_USER.
}

echo "Applying database migrations..."
python manage.py migrate --noinput || echo "Warning: Migrations failed. Database might not be fully ready."

# Initialize local embedding model before starting the server
echo "Ensuring embedding models are downloaded..."
python -m scripts.download_embedding_model || echo "Warning: Could not download embedding model."

echo "Starting application server..."
exec "$@"
