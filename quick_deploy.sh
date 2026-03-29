#!/bin/bash
# ULTRA QUICK DEPLOY SCRIPT - RUN THIS ON VPS

set -e

echo "🚀 MWECAU DigiVote - Quick Deploy to Port 81"
echo "=============================================="

# Navigate to project
cd /var/www/mwecau_digivote/src

# Activate venv
source venv/bin/activate

# Migrate
echo "📦 Running migrations..."
python manage.py migrate

# Load data
if [ -f "../db_dump.json" ]; then
    echo "📥 Loading database..."
    python manage.py loaddata ../db_dump.json
fi

# Collect static
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Stop existing
echo "🛑 Stopping existing process..."
sudo pkill -f "gunicorn.*mw_es.wsgi" || true

# Start
echo "🚀 Starting on port 81..."
sudo venv/bin/gunicorn mw_es.wsgi:application --bind 0.0.0.0:81 --workers 3 --daemon

# Check
sleep 2
if sudo lsof -i :81 > /dev/null; then
    echo "✅ SUCCESS! Running on http://159.65.119.182:81"
else
    echo "❌ FAILED! Check logs"
fi
