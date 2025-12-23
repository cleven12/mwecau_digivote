# Club Deployment Guide

Quick guide for setting up the MWECAU Digital Voting System for club use.

## Quick Development Setup

```bash
# 1. Clone and setup
git clone https://github.com/cleven12/university_elec_api.git
cd university_elec_api
git checkout final-delivery

# 2. Environment setup
cp .env.example .env
# Edit .env with your email credentials for notifications

# 3. Install and run
cd src
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r ../requirements.txt
python manage.py migrate
python manage.py runserver
```

Visit: `http://localhost:5000`

## Initial Setup

### 1. Create Admin User
```bash
python manage.py createsuperuser
```

### 2. Add Institution Data
Via Django admin (`/admin/`):
- Add **Courses** (Computer Science, Business Admin, etc.)
- Add **States** (dormitories/locations like KIFUMBU, MAWELA)
- Add **Election Levels** (President, State Leader, Course Leader)

### 3. Create Student Accounts
Via Django admin:
- Add **Users** with registration numbers
- Assign users to courses and states
- Set user roles (VOTER, CANDIDATE, COMMISSIONER, etc.)

### 4. Verify Users
- Go to Users in admin
- Check "is_verified" for students who should be able to vote

## Creating Elections

### Via Admin Interface:
1. Go to `/admin/` → Elections → Elections
2. Create new election:
   - Set title, description
   - Choose election level (President, State, Course)
   - Set start/end dates
   - Save

### Via Commissioner Dashboard:
1. Login as commissioner
2. Go to `/commissioner/`
3. Use "Create Election" feature

## Email Configuration

For notifications to work, update `.env`:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourschool.ac.tz
```

## Production Deployment

### Environment Variables
Copy `.env.example` to production and set:
- `DEBUG=False`
- `SECRET_KEY=your-strong-secret-key`
- `ALLOWED_HOSTS=your-domain.com`
- Real database credentials
- Real email service credentials

### Database
Use PostgreSQL in production:
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=voting_system
DB_USER=voting_user
DB_PASSWORD=strong-password
DB_HOST=localhost
DB_PORT=5432
```

### Static Files
```bash
python manage.py collectstatic
```

### Web Server
Use gunicorn + nginx:
```bash
pip install gunicorn
gunicorn mw_es.wsgi:application --bind 0.0.0.0:8000
```

## Backup & Recovery

### Database Backup
```bash
python manage.py dumpdata > backup.json
```

### Database Restore
```bash
python manage.py loaddata backup.json
```

## Troubleshooting

### Common Issues:

**Email not working:**
- Check Gmail app password setup
- Verify EMAIL_* settings in .env
- Test with console backend first

**Static files missing:**
- Run `python manage.py collectstatic`
- Check `STATIC_ROOT` and `STATIC_URL` settings

**Migration errors:**
- Delete `db.sqlite3` and run `python manage.py migrate` for fresh start
- For production: backup before migrations

**Permission errors:**
- Check user roles in admin interface
- Verify users are verified (`is_verified=True`)

## Security Checklist

- [ ] `DEBUG=False` in production
- [ ] Strong `SECRET_KEY`
- [ ] Environment variables for secrets
- [ ] HTTPS enabled
- [ ] Database credentials secured
- [ ] Admin interface access restricted
- [ ] Regular backups scheduled

## Club Customization

### Branding
- Edit templates in `src/templates/`
- Update CSS in `src/static/css/style.css`
- Change site name in settings

### Features
- Add new user roles in `core/models.py`
- Create custom dashboards in `core/views.py`
- Extend API in `*_api_views.py`

### Integration
- Add SMS notifications
- Connect to student management system
- Add mobile app support

For more details, see the full documentation in `/docs/`.