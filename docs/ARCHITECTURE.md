# MWECAU Digital Voting System - Architecture & Design (code-verified)

This document reflects the architecture implemented in this repository (verified against the code). It focuses on the current, runnable configuration and components found under `src/`.

Overview
- The project is a hybrid Django application: server-rendered templates for the main UI and a REST API (Django REST Framework) for programmatic access.
- API endpoints use JWT authentication via `djangorestframework-simplejwt` where applicable.
- Celery is configured and present in the codebase; by default it uses the Django database broker (`CELERY_BROKER_URL='django://'`) and `django-celery-beat`/`django-celery-results` are enabled in settings.
- Development DB is SQLite (`db.sqlite3`). Production should use PostgreSQL or another robust RDBMS.

Key implementation notes
- Hybrid UI/API: both server-side HTML views and API endpoints are actively used in the codebase.
- Authentication: server views use Django sessions while API endpoints rely on JWT; check `src/mw_es/settings.py` and `src/core/api_views.py` for exact configuration.
- Celery: present and configured to use the Django DB broker in development. The code contains Celery tasks (`src/core/tasks.py`, `src/election/tasks.py`) and Celery app initialization (`src/celery_app.py`, `src/mw_es/celery_app.py`).
- Redis: not required by the current repository. References to Redis in older docs are design notes; the code uses the DB broker by default but can be upgraded to Redis in production.

Operational guidance
- Development:
  - From repo root run: `cd src && python manage.py runserver` (default port 8000).
  - Celery tasks will run if Celery workers are started; otherwise many tasks fall back to synchronous execution depending on code paths.
- Production recommendations:
  - Set `DEBUG=False` and configure `SECRET_KEY`, `ALLOWED_HOSTS`, and database via environment variables.
  - Use PostgreSQL for the DB.
  - Use Redis or RabbitMQ as Celery broker and configure `CELERY_BROKER_URL`.
  - Run Celery workers and `celery beat` under a process manager.

Where to look in code
- Settings: `src/mw_es/settings.py`
- Celery config: `src/celery_app.py`, `src/mw_es/celery_app.py`
- API views and serializers: `src/core/api_views.py`, `src/core/serializers.py`, `src/election/serializers*.py`
- Tasks: `src/core/tasks.py`, `src/election/tasks.py`
- Models and business logic: `src/election/models.py`, `src/core/models.py`

Notes on outdated docs
- Some older documentation in this repo described a pure server-rendered, session-only architecture. That is outdated: the repository contains JWT/DRF and Celery configuration. This file supersedes earlier architecture drafts and should be updated again if the codebase changes.

Document Version: 2.0
Last Updated: 2025-12-07

**Author**: MWECAU ICT Club  
**Contact**: [Your contact information]
