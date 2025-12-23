# MWECAU Election Platform - Environment Setup Guide

Quick start guide for setting up environment variables for development and production.

## Quick Start (Development)

1. **Copy the example environment file**:
   ```bash
   cp .env.example .env.development
   ```

2. **Edit with your settings**:
   ```bash
   # Update email credentials and other settings
   nano .env.development
   ```

3. **Run the application**:
   ```bash
   python manage.py runserver
   ```

The application automatically loads `.env` or `.env.development` file on startup.

## Environment Files Included

| File | Purpose | Commit to Git | Notes |
|------|---------|---------------|-------|
| `.env.example` | ✓ Template | YES | Safe to commit - no secrets |
| `.env.development` | Local development | NO | Add to `.gitignore` |
| `.env.production` | Production deploy | NO | Add to `.gitignore` - use secret manager |
| `ENV_CONFIGURATION.md` | Full documentation | YES | Complete guide with all options |

## Development Setup

### 1. Initial Setup
```bash
# Clone repository
git clone <repo-url>
cd university_elec_api

# Create development environment file
cp .env.example .env.development

# Edit configuration
nano .env.development
```

### 2. Required for Development
Minimum variables to set in `.env.development`:
```env
SECRET_KEY=your-secret-key
DEBUG=True
DB_ENGINE=django.db.backends.sqlite3
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
SITE_URL=http://localhost:5000
```

### 3. Run Migrations
```bash
python manage.py migrate
```

### 4. Create Admin User
```bash
python manage.py create_admin_user
```

### 5. Start Development Server
```bash
python manage.py runserver
```

Access at: `http://localhost:5000`

## Production Deployment

### Prerequisites
- PostgreSQL database
- Redis for Celery
- RabbitMQ or Redis broker
- SSL certificate
- Email service account

### 1. Create Production Environment File
```bash
cp .env.example .env.production
nano .env.production
```

### 2. Update Critical Variables
```env
# Security
SECRET_KEY=[generate new strong key]
DEBUG=False
ALLOWED_HOSTS=elections.mwecau.ac.tz

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=election_platform_prod
DB_USER=election_user
DB_PASSWORD=[strong password]
DB_HOST=[RDS endpoint]
DB_PORT=5432

# Email
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST_USER=noreply@mwecau.ac.tz
EMAIL_HOST_PASSWORD=[app password]

# Celery
CELERY_BROKER_URL=redis://[host]:6379/1
CELERY_RESULT_BACKEND=redis://[host]:6379/0

# Site
SITE_URL=https://elections.mwecau.ac.tz
```

### 3. Using Secret Manager (Recommended)
Instead of `.env.production` file, use AWS Secrets Manager or similar:

```python
# In settings.py or deployment script
import boto3
import json
import os

def load_secrets():
    client = boto3.client('secretsmanager')
    secret = client.get_secret_value(SecretId='election-platform/prod')
    secrets = json.loads(secret['SecretString'])
    for key, value in secrets.items():
        os.environ[key] = value

load_secrets()
```

### 4. Deployment Commands
```bash
# Load environment
source .env.production

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Create superuser
python manage.py create_admin_user

# Start gunicorn
gunicorn mw_es.wsgi:application --bind 0.0.0.0:8000

# In separate terminal, start Celery worker
celery -A mw_es worker -l info

# In another terminal, start Celery beat
celery -A mw_es beat -l info
```

### 5. Nginx Configuration
```nginx
server {
    listen 443 ssl;
    server_name elections.mwecau.ac.tz;
    
    ssl_certificate /etc/ssl/certs/elections.crt;
    ssl_certificate_key /etc/ssl/private/elections.key;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /var/data/election_platform/staticfiles/;
    }
    
    location /media/ {
        alias /var/data/election_platform/media/;
    }
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name elections.mwecau.ac.tz;
    return 301 https://$server_name$request_uri;
}
```

## Docker Deployment

### Development with Docker
```bash
# Build image
docker build -t election-platform:dev -f Dockerfile.dev .

# Run container
docker run --env-file .env.development -p 5000:8000 election-platform:dev
```

### Production with Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  web:
    image: election-platform:latest
    env_file: .env.production
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
      - rabbitmq
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: election_platform_prod
      POSTGRES_USER: election_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
  
  redis:
    image: redis:7
    command: redis-server --requirepass ${REDIS_PASSWORD}
  
  rabbitmq:
    image: rabbitmq:3.12
    environment:
      RABBITMQ_DEFAULT_USER: election_user
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
  
  celery:
    image: election-platform:latest
    env_file: .env.production
    command: celery -A mw_es worker -l info
    depends_on:
      - web
      - redis
      - rabbitmq

volumes:
  postgres_data:
```

Run with:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Email Configuration

### Gmail (Development)
1. Enable 2-Factor Authentication
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Use in `.env.development`:
   ```env
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_USE_TLS=True
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-16-char-app-password
   ```

### SendGrid (Production)
1. Create API key at https://app.sendgrid.com/settings/api_keys
2. Configure in environment:
   ```env
   EMAIL_BACKEND=sendgrid_backend.SendgridBackend
   SENDGRID_API_KEY=SG.xxxxx
   ```

### AWS SES (Production)
```env
EMAIL_BACKEND=django_ses.SESBackend
AWS_SES_REGION_NAME=us-east-1
AWS_SES_REGION_ENDPOINT=email.us-east-1.amazonaws.com
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
```

## Database Setup

### SQLite (Development)
No setup needed - automatically created

### PostgreSQL (Production)
```bash
# Create database and user
createdb election_platform_prod
createuser -P election_user  # Enter password when prompted

# Grant permissions
psql -U postgres -d election_platform_prod
GRANT ALL PRIVILEGES ON DATABASE election_platform_prod TO election_user;
```

## Celery & Redis Setup

### Development
Default uses Django database as broker. For Redis:
```bash
# Install Redis
brew install redis  # macOS
sudo apt-get install redis-server  # Ubuntu

# Start Redis
redis-server

# Set in .env.development
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### Production
Use managed Redis or RabbitMQ:
```env
# Redis
CELERY_BROKER_URL=redis://redis-prod.mwecau.ac.tz:6379/1
CELERY_RESULT_BACKEND=redis://redis-prod.mwecau.ac.tz:6379/0

# Or RabbitMQ
CELERY_BROKER_URL=amqp://election_user:password@rabbitmq.mwecau.ac.tz:5672/election_vhost
CELERY_RESULT_BACKEND=redis://redis-prod.mwecau.ac.tz:6379/0
```

## Verification Checklist

### Development
- [ ] `.env.development` created and configured
- [ ] `SECRET_KEY` set
- [ ] `DEBUG=True`
- [ ] Email backend configured
- [ ] Database migrations run
- [ ] Admin user created
- [ ] Application starts without errors

### Production
- [ ] `.env.production` created and secured
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` is strong and unique
- [ ] `ALLOWED_HOSTS` configured correctly
- [ ] SSL certificate installed
- [ ] Database credentials correct
- [ ] Email service configured
- [ ] Celery broker running
- [ ] Redis/Cache configured
- [ ] Static files collected
- [ ] Backup enabled
- [ ] Monitoring configured

## Troubleshooting

### Email Not Sending
```bash
# Test email configuration
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Message', 'from@example.com', ['to@example.com'])
```

### Database Connection Failed
```bash
# Test connection
python -c "import psycopg2; psycopg2.connect('dbname=election_platform_prod user=election_user password=xxx host=localhost')"
```

### Celery Tasks Not Running
```bash
# Check broker connection
celery -A mw_es inspect active

# Check worker status
celery -A mw_es inspect stats
```

### Static Files 404
```bash
# Collect static files
python manage.py collectstatic --noinput --clear
```

## Support

For detailed configuration options, see `ENV_CONFIGURATION.md`.

For issues, check:
1. Environment variables are set correctly
2. All services (DB, Redis, RabbitMQ) are running
3. Secrets have proper permissions
4. Logs for error messages
