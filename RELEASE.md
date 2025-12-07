# Release Notes

This file provides a concise, code-verified summary of notable releases and changes. It focuses on the implemented features in the repository as of the current branch.

## Unversioned - Working Repository (2025-12-07)

- Hybrid UI/API: server-rendered Django templates plus REST API endpoints (Django REST Framework).
- JWT authentication is available for API endpoints (`rest_framework_simplejwt` present in settings).
- Celery is configured (DB broker by default) with `django-celery-beat` and `django-celery-results` installed and referenced in settings.
- Development DB: SQLite (`db.sqlite3`). Production recommendations: PostgreSQL + a proper Celery broker (Redis/RabbitMQ).

## Notes
- Several older documentation drafts referenced a pure server-rendered, session-only architecture; the codebase contains DRF and JWT configuration — this is the source of truth.
- The Celery setup uses the Django DB broker by default; to use Redis in production, update `CELERY_BROKER_URL` and production `requirements.txt` accordingly.

For frequently updated changelog entries tied to releases, see `CHANGELOG.md`.

