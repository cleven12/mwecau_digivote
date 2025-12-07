# MWECAU Digital Voting System

This repository implements a student election platform built with Django and Django REST Framework.

Quick facts (code-verified)
- Backend: Django (custom `User` model in `core`)
- API: Django REST Framework with JWT (`djangorestframework-simplejwt`) and Session authentication enabled
- Tasks: Celery tasks are defined (`django-celery-beat`, `django-celery-results`) and the default broker in settings is the Django DB broker (`django://`).
- DB (dev): SQLite (`db.sqlite3`). Production: use PostgreSQL and a proper Celery broker (Redis/RabbitMQ).

Running locally
```bash
cd src
python manage.py migrate
python manage.py runserver
```

Start Celery (optional, for async email/notifications):
```bash
cd src
celery -A mw_es worker -Q email_queue --loglevel=info
celery -A mw_es beat --loglevel=info
```

Key URLs (code-verified)
- UI: `/`, `/login/`, `/register/`, `/dashboard/`, `/commissioner/`
- Election UI: `/elections/`, `/elections/<id>/vote/`, `/elections/<id>/results/`
- Election API: `POST /elections/api/<id>/submit/` and `GET /elections/api/<id>/results/`
- Commissioner APIs: `/api/commissioner/stats/`, `/api/commissioner/election/<id>/analytics/`, `/api/commissioner/verify-user/<id>/`

Docs
- `docs/ARCHITECTURE.md` — architecture notes (code-verified)
- `docs/API_DOCUMENTATION.md` — concise API reference (updated)
- `docs/ELECTION_BUSINESS_LOGIC.md` — business rules and token lifecycle (updated)
- `docs/TESTING_GUIDE.md` — testing steps (updated)
- `CHANGELOG.md`, `CONTRIBUTING.md` — contributor guidance

Contributing
- See `CONTRIBUTING.md` for guidelines and how to run the project locally.

If you want me to also tidy remaining docs, archive older drafts, or run the test suite, tell me which you'd like next.
- Nested serialization for related objects (courses, states, election levels)
- Context-aware serialization for user-specific data

**Rationale:** REST API design separates frontend and backend, enabling future mobile app development. DRF provides robust serialization, validation, and browsable API for development.

### Email Integration
**Django Email System** with Celery background tasks

**Email Workflows:**
- Account verification with voter tokens (if elections active) - automated
- Election activation notifications with level-specific tokens - automated
- Password reset emails - automated
- Commissioner contact form notifications - automated
- 5-minute pre-start election reminders - scheduled
- 30-minute pre-end reminders for non-voters - scheduled
- Custom admin notifications - on-demand from admin panel

**Task Queue:** Celery with Django database broker (easily upgradeable to Redis for production)

**Rationale:** Email serves as the primary communication channel for credentials and election notifications. Celery ensures emails don't block request/response cycle and enables scheduled notifications.

### Security Features

1. **Vote Anonymity:** Votes are not linked to users in the database
2. **Token-Based Voting:** Unique UUIDs prevent duplicate votes
3. **CSRF Protection:** Enabled for all form submissions
4. **Password Hashing:** Django's built-in secure password hashing
5. **JWT Token Blacklisting:** Prevents token reuse after logout
6. **Verification System:** Two-step registration with admin verification

**Rationale:** Election integrity requires both security (preventing fraud) and privacy (anonymous voting). The token system achieves both by separating user identity from vote records.

### Multi-Level Election System

**Three Election Levels:**
1. **President:** University-wide, all students eligible
2. **State Leader:** State-specific, filtered by student's state
3. **Course Leader:** Course-specific, filtered by student's course

**Eligibility Logic:** Users receive tokens only for levels they're eligible to vote in based on their state and course assignments.

**Rationale:** This mirrors real-world university governance structures where students elect representatives at multiple organizational levels.

### Frontend Architecture
**Server-Side Rendered Templates** with Bootstrap 5

**Technology Stack:**
- Django Template Language
- Bootstrap 5 for responsive UI
- Font Awesome for icons
- Minimal JavaScript for countdowns and form validation

**Template Structure:**
- `base.html`: Common layout with navigation
- App-specific templates in `core/` and `election/` directories
- Reusable components via template inheritance

**Rationale:** Server-side rendering simplifies deployment and reduces client-side complexity. Bootstrap provides professional UI with minimal custom CSS.

## External Dependencies

### Python Packages
- **Django 5.2.7** - Web framework
- **djangorestframework** - REST API framework
- **djangorestframework-simplejwt** - JWT authentication
- **django-cors-headers** - CORS support for API access
- **drf-yasg** - API documentation (Swagger/ReDoc)

### Frontend Libraries (CDN)
- **Bootstrap 5.3** - CSS framework
- **Font Awesome 6.4** - Icon library

### Email Service
- Uses Django's email backend (configurable for SMTP, SendGrid, etc.)
- Currently configured for development with console backend

### Media Storage
- Local filesystem storage for candidate images
- Configured via `MEDIA_ROOT` and `MEDIA_URL`

### Future Considerations
- Database migration path to PostgreSQL/MySQL for production
- Redis for caching and session management
- Celery for asynchronous task processing (email sending)
- Cloud storage (S3/GCS) for media files in production