#!/bin/bash
# ============================================================
# VPS Static Files Fix - Update to WhiteNoise
# ============================================================

echo "🔧 Updating VPS to use WhiteNoise for static files..."
echo "========================================================"

cd /var/www/mwecau_digivote

# Stop Gunicorn
echo "🛑 Stopping Gunicorn..."
PID=$(sudo lsof -ti :81)
if [ ! -z "$PID" ]; then
    sudo kill $PID
    sleep 2
fi

# Pull latest init-dep branch
echo "📥 Pulling init-dep branch..."
git fetch origin
git checkout init-dep
git pull origin init-dep

# Update dependencies
echo "📦 Installing WhiteNoise..."
cd src
source venv/bin/activate
pip install whitenoise gunicorn psycopg2-binary --upgrade

# Collect static files
echo "🗂️  Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn
echo "🚀 Starting Gunicorn..."
sudo venv/bin/gunicorn mw_es.wsgi:application --bind 0.0.0.0:81 --workers 3 --daemon

echo ""
echo "✅ Update Complete!"
echo "🌐 Check: http://159.65.119.182:81"
echo "📁 Static files served by WhiteNoise"
