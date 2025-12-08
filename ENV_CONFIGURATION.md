# Environment Configuration Guide

This document provides comprehensive guidance on setting up and managing environment variables for the MWECAU Election Platform across different deployment environments.

## Files Overview

### `.env.development`
**Purpose**: Local development environment configuration
- Located in project root
- Used during development with Django development server
- Includes secure defaults optimized for debugging
- **Status**: Safe to commit if values are sanitized (no real secrets)

### `.env.production`
**Purpose**: Production deployment configuration
- Located in project root or deployment server
- Used in production with gunicorn/uWSGI + nginx
- Includes security-hardened settings
- **Status**: NEVER commit real secrets - use secret management tools

### `.env.example`
**Purpose**: Template for creating environment files
- Safe to commit to version control
- Copy to `.env.development` or `.env.production`
- Fill in your specific values

## How to Use

### Development Setup

1. **Copy the development template**:
   ```bash
   cp .env.example .env.development
   ```

2. **Edit with your development settings**:
   ```bash
   nano .env.development
   ```

3. **Run Django with development environment**:
   ```bash
   # Django automatically loads .env file
   python manage.py runserver
   ```

### Production Deployment

#### Option 1: Environment File Method (Simple)
1. **Create production environment file**:
   ```bash
   cp .env.example .env.production
   nano .env.production
   # Update all CHANGE_ME values with real credentials
   ```

2. **Load on server startup**:
   ```bash
   source /path/to/.env.production
   gunicorn mw_es.wsgi:application
   ```

#### Option 2: Secret Management (Recommended)
Use cloud-native secrets management:

**AWS Secrets Manager**:
```python
import json
import boto3

client = boto3.client('secretsmanager')
secret = client.get_secret_value(SecretId='election-platform/prod')
config = json.loads(secret['SecretString'])
os.environ.update(config)
```

**HashiCorp Vault**:
```python
import hvac

client = hvac.Client(url='https://vault.mwecau.ac.tz', token='YOUR_TOKEN')
secrets = client.secrets.kv.read_secret_version(path='election-platform/prod')
os.environ.update(secrets['data']['data'])
```

**GitHub Secrets** (for CI/CD):
```yaml
# .github/workflows/deploy.yml
env:
  SECRET_KEY: ${{ secrets.PROD_SECRET_KEY }}
  DB_PASSWORD: ${{ secrets.PROD_DB_PASSWORD }}
```

## Configuration Variables

### Django Core Settings

| Variable | Development | Production | Required | Notes |
|----------|-------------|-----------|----------|-------|
| `SECRET_KEY` | insecure-dev | strong-random | ✓ | Generate: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DEBUG` | `True` | `False` | ✓ | Never enable DEBUG in production |
| `ALLOWED_HOSTS` | localhost, 127.0.0.1 | domain.com | ✓ | Comma-separated list |

### Database

| Variable | Development | Production | Options |
|----------|-------------|-----------|---------|
| `DB_ENGINE` | sqlite3 | postgresql | `sqlite3`, `postgresql`, `mysql` |
| `DB_NAME` | db.sqlite3 | election_platform_prod | Database name |
| `DB_HOST` | localhost | db-prod.domain.com | Hostname |
| `DB_PORT` | 5432 | 5432 | Port number |
| `DB_USER` | postgres | election_user | Username |
| `DB_PASSWORD` | postgres | strong-password | Database password |

**Recommended Production Setup**:
```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=election_platform_prod
DB_USER=election_user
DB_PASSWORD=[use secret manager]
DB_HOST=[RDS endpoint or managed database]
DB_PORT=5432
```

### Email Configuration

| Variable | Purpose | Example |
|----------|---------|---------|
| `EMAIL_BACKEND` | Mail handling method | `django.core.mail.backends.smtp.EmailBackend` |
| `EMAIL_HOST` | SMTP server | `smtp.gmail.com` |
| `EMAIL_PORT` | SMTP port | `587` or `465` |
| `EMAIL_USE_TLS` | TLS encryption | `True` |
| `EMAIL_HOST_USER` | Sender email | `noreply@mwecau.ac.tz` |
| `EMAIL_HOST_PASSWORD` | App password | `[from Gmail/provider]` |
| `DEFAULT_FROM_EMAIL` | Default sender | `noreply@mwecau.ac.tz` |

**Gmail Setup**:
1. Enable 2-Factor Authentication
2. Create App Password at https://myaccount.google.com/apppasswords
3. Use 16-character app password

**Production SMTP Services**:
- SendGrid: `smtp.sendgrid.net:587`
- AWS SES: `email-smtp.[region].amazonaws.com:587`
- Mailgun: `smtp.mailgun.org:587`

### Celery Configuration

| Variable | Development | Production | Notes |
|----------|-------------|-----------|-------|
| `CELERY_BROKER_URL` | `django://` | `amqp://user:pass@host/vhost` | RabbitMQ or Redis |
| `CELERY_RESULT_BACKEND` | `django-db` | `redis://host:6379/0` | Task results storage |
| `CELERY_ALWAYS_EAGER` | `True` | `False` | Sync execution for debugging |

**Production Options**:

RabbitMQ:
```
CELERY_BROKER_URL=amqp://election_user:password@rabbitmq.domain.com:5672/election_vhost
CELERY_RESULT_BACKEND=redis://redis.domain.com:6379/0
```

Redis Only:
```
CELERY_BROKER_URL=redis://:password@redis.domain.com:6379/1
CELERY_RESULT_BACKEND=redis://:password@redis.domain.com:6379/0
```

### Security Settings (Production)

```
SESSION_COOKIE_SECURE=True           # HTTPS only
CSRF_COOKIE_SECURE=True              # HTTPS only
SESSION_COOKIE_HTTPONLY=True         # No JavaScript access
CSRF_COOKIE_HTTPONLY=True            # No JavaScript access
SESSION_COOKIE_SAMESITE=Strict       # CSRF protection
CSRF_COOKIE_SAMESITE=Strict          # CSRF protection
SECURE_SSL_REDIRECT=True              # Redirect HTTP to HTTPS
SECURE_HSTS_SECONDS=31536000         # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
```

### External Services

| Service | Provider | Required Keys |
|---------|----------|----------------|
| SMS | Twilio | `SMS_API_KEY`, `SMS_API_SECRET` |
| SMS | Africa's Talking | `SMS_API_KEY`, `SMS_API_SECRET` |
| Error Tracking | Sentry | `SENTRY_DSN` |
| Performance | New Relic | `NEW_RELIC_CONFIG_FILE` |

## Environment-Specific Settings

### Development Environment
```
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.localhost
DB_ENGINE=sqlite3
EMAIL_BACKEND=console
CELERY_ALWAYS_EAGER=True
SESSION_COOKIE_SECURE=False
ENABLE_DEBUG_TOOLBAR=True
```

### Staging Environment
```
DEBUG=False
ALLOWED_HOSTS=staging.elections.mwecau.ac.tz
DB_ENGINE=postgresql
EMAIL_BACKEND=smtp
CELERY_ALWAYS_EAGER=False
SESSION_COOKIE_SECURE=True
ENABLE_DEBUG_TOOLBAR=False
```

### Production Environment
```
DEBUG=False
ALLOWED_HOSTS=elections.mwecau.ac.tz,api.elections.mwecau.ac.tz
DB_ENGINE=postgresql
EMAIL_BACKEND=smtp
CELERY_ALWAYS_EAGER=False
SESSION_COOKIE_SECURE=True
ENABLE_API_THROTTLING=True
BACKUP_ENABLED=True
```

## Loading Environment Variables in Settings

The application uses `python-dotenv` to load environment variables:

```python
# In mw_es/settings.py
from dotenv import load_dotenv
import os

load_dotenv(BASE_DIR / '.env')  # Automatically loads .env or specific file

SECRET_KEY = os.getenv('SECRET_KEY', 'default-insecure-key')
DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'
```

## Environment Variable Precedence

1. **System Environment Variables** (highest priority)
2. **.env File Variables**
3. **Python Default Values** (lowest priority)

Example:
```bash
# System variable overrides .env file
export SECRET_KEY="system-secret-key"
python manage.py runserver
```

## Security Best Practices

### ✅ DO:
- Use `.gitignore` to exclude `.env` files from version control
- Use `.env.example` as a template (commit without secrets)
- Rotate secrets regularly
- Use separate credentials per environment
- Enable HTTPS in production
- Store secrets in secret managers
- Audit secret access logs
- Use strong, unique passwords
- Enable 2FA on email accounts

### ❌ DON'T:
- Commit real secrets to git
- Use weak or default passwords
- Share credentials via email/chat
- Use same credentials across environments
- Disable HTTPS in production
- Log sensitive information
- Hardcode secrets in code
- Use development secrets in production

## Docker Deployment

### Dockerfile Environment Setup
```dockerfile
# Load from environment variables passed at runtime
ENV DEBUG=False
ENV ALLOWED_HOSTS=elections.mwecau.ac.tz

# Or use .env.production
COPY .env.production .env
```

### Docker Compose
```yaml
services:
  web:
    build: .
    env_file:
      - .env.production
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - DB_PASSWORD=${DB_PASSWORD}
```

### Docker Run
```bash
docker run \
  --env-file .env.production \
  -e SECRET_KEY="$(cat /run/secrets/secret_key)" \
  election-platform:latest
```

## Troubleshooting

### Issue: "SECRET_KEY not configured"
**Solution**: Ensure `.env` file exists and contains `SECRET_KEY` variable

### Issue: "Database connection refused"
**Solution**: Check `DB_HOST`, `DB_PORT`, and database service is running

### Issue: "Email not sending"
**Solution**: Verify `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, and enable "Less Secure Apps" (Gmail)

### Issue: "Celery tasks not executing"
**Solution**: Check `CELERY_BROKER_URL` and ensure RabbitMQ/Redis is running

### Issue: "Static files returning 404"
**Solution**: Run `python manage.py collectstatic` and verify `STATIC_ROOT`, `STATIC_URL`

## Verification Checklist

Before deploying to production:

- [ ] All required variables are set
- [ ] `DEBUG=False`
- [ ] `SECRET_KEY` is strong and unique
- [ ] Database credentials are correct
- [ ] HTTPS is enabled
- [ ] Email is configured
- [ ] Celery broker is running
- [ ] Static files are collected
- [ ] Secrets are stored securely
- [ ] Backup is enabled
- [ ] Monitoring is configured
- [ ] Load balancer is configured (if applicable)

## Additional Resources

- [Django Settings Documentation](https://docs.djangoproject.com/en/5.2/topics/settings/)
- [12 Factor App - Config](https://12factor.net/config)
- [OWASP Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/)
- [HashiCorp Vault](https://www.vaultproject.io/)
