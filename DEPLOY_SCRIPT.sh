#!/bin/bash
# ============================================================
# MWECAU DigiVote - VPS Deployment Script
# Target: 159.65.119.182:81
# ============================================================

echo "🚀 MWECAU DigiVote Deployment Script"
echo "===================================="
echo ""

# ============================================================
# STEP 1: Setup (First Time Only)
# ============================================================
echo "📦 STEP 1: Clone and setup environment..."
cd /var/www && \
sudo git clone https://github.com/mwecauictclub/mwecau_digivote.git && \
sudo chown -R $USER:$USER mwecau_digivote && \
cd mwecau_digivote/src && \
python3 -m venv venv && \
source venv/bin/activate && \
pip install -r requirements.txt gunicorn psycopg2-binary

echo "✅ Environment setup complete!"
echo ""

# ============================================================
# STEP 2: PostgreSQL Database with Full Permissions
# ============================================================
echo "🗄️  STEP 2: Creating PostgreSQL database..."
sudo -u postgres psql << SQLEOF
CREATE DATABASE digivote_db;
CREATE USER digivote_user WITH PASSWORD 'DigiVote2024!';
GRANT ALL PRIVILEGES ON DATABASE digivote_db TO digivote_user;
\c digivote_db
GRANT ALL ON SCHEMA public TO digivote_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO digivote_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO digivote_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO digivote_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO digivote_user;
\q
SQLEOF

echo "✅ Database created with full permissions!"
echo ""

# ============================================================
# STEP 3: Upload Database Dump
# ============================================================
echo "📤 STEP 3: Upload db_dump.json from local machine:"
echo "Run this on your LOCAL machine:"
echo "scp /home/cleven/Private/mwecau-ict-github/mwecau_digivote/db_dump.json root@159.65.119.182:/tmp/"
echo ""
read -p "Press Enter when upload is complete..."

# ============================================================
# STEP 4: Deploy & Run
# ============================================================
echo "🚀 STEP 4: Deploying application..."
cd /var/www/mwecau_digivote/src

# Create .env file
cat > .env << 'ENVEOF'
DEBUG=False
SECRET_KEY=dj4ng0-s3cr3t-k3y-ch4ng3-m3-pl34s3-$(date +%s)
ALLOWED_HOSTS=159.65.119.182,localhost
CSRF_TRUSTED_ORIGINS=http://159.65.119.182:81

DB_ENGINE=django.db.backends.postgresql
DB_NAME=digivote_db
DB_USER=digivote_user
DB_PASSWORD=DigiVote2024!
DB_HOST=localhost
DB_PORT=5432

EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=mwecauictclub@gmail.com
EMAIL_HOST_PASSWORD=app-password-here
DEFAULT_FROM_EMAIL=MWECAU DigiVote <mwecauictclub@gmail.com>
ENVEOF

# Activate venv and run migrations
source venv/bin/activate
python manage.py migrate

# Load data
mv /tmp/db_dump.json ../
python manage.py loaddata ../db_dump.json

# Collect static files
python manage.py collectstatic --noinput

# Start Gunicorn
sudo venv/bin/gunicorn mw_es.wsgi:application --bind 0.0.0.0:81 --workers 3 --daemon

echo ""
echo "✅ Deployment Complete!"
echo "===================================="
echo "🌐 Access: http://159.65.119.182:81"
echo "👤 Test Login:"
echo "   Registration: T/TEST/2023/0001"
echo "   Password: TestVoter@2024"
echo ""
