#!/bin/bash
# ============================================================
# MWECAU DigiVote - Quick Fix Deployment
# Use this after migrations are already applied
# ============================================================

echo "🔧 Fixing duplicate data and deploying..."
echo "=========================================="
echo ""

cd /var/www/mwecau_digivote/src

# Activate virtual environment
source venv/bin/activate

# Flush existing data (keeps tables)
echo "🗑️  Clearing existing data..."
python manage.py flush --no-input

# Load database dump
echo "📥 Loading database dump..."
python manage.py loaddata ../db_dump.json

# Collect static files
echo "📦 Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn on port 81
echo "🚀 Starting Gunicorn..."
sudo venv/bin/gunicorn mw_es.wsgi:application --bind 0.0.0.0:81 --workers 3 --daemon

echo ""
echo "✅ Deployment Complete!"
echo "=========================================="
echo "🌐 Access: http://159.65.119.182:81"
echo "👤 Test Login:"
echo "   Registration: T/TEST/2023/0001"
echo "   Password: TestVoter@2024"
echo ""
