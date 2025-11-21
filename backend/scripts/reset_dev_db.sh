#!/bin/bash
# Reset development database
# This script drops all tables, re-runs migrations, and seeds data

set -e

echo "🔄 Resetting development database..."
echo

# Drop all tables (use with caution!)
echo "⚠️  Dropping all tables..."
psql $DATABASE_URL -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"

echo "📦 Running migrations..."
cd "$(dirname "$0")/.."
alembic upgrade head

echo "🌱 Seeding development data..."
python -m scripts.seed_dev_data

echo
echo "✅ Database reset complete!"

