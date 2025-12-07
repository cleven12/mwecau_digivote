# Clean Codebase Structure (branch: clean-codebase)

This document describes the clean, consolidated structure of the university election API after removing unused code.

## Core Application (`src/core/`)

### Views
- **`views_ui.py`** - All Django session-based UI views for user-facing features
  - `home()` - Landing page
  - `login_view()` - User login with registration number
  - `logout_view()` - User logout
  - `register_view()` - Student registration workflow
  - `dashboard_view()` - User dashboard (authenticated)
  - `profile_edit_view()` - Profile editing with election-aware restrictions
  
- **`views_commissioner.py`** - All commissioner dashboard and analytics endpoints
  - `commissioner_dashboard()` - Commissioner UI dashboard
  - `dashboard_stats_api()` - JSON API for overall statistics
  - `election_analytics_api()` - JSON API for election-specific analytics
  - `verify_user_api()` - JSON API for user verification
  - `pending_verifications_api()` - JSON API for pending verifications

### Data Layer
- **`serializers.py`** - All core serializers for request/response validation
  - User creation and login serializers
  - Email verification and password reset serializers
  - State/Course reference serializers

- **`models.py`** - User model and related data models
- **`admin.py`** - Django admin configuration
- **`signals.py`** - Django signals for automating user workflows
- **`tasks.py`** - Celery tasks for email notifications
- **`permissions.py`** - Custom permission classes
- **`backends.py`** - Custom authentication backend (registration number based)

### URL Configuration
- **`urls.py`** - All core app routes
  - UI routes: `/`, `/login/`, `/register/`, `/dashboard/`, `/profile/edit/`
  - Commissioner routes: `/commissioner/`, `/api/commissioner/*`

---

## Election Application (`src/election/`)

### Views
- **`views.py`** - Minimal API endpoints for voting
  - `VoteView` - POST endpoint for vote submission
  - `ResultsView` - GET endpoint for election results

- **`views_ui.py`** - All election UI views
  - `elections_list()` - List all active elections
  - `election_vote()` - Election voting page
  - `submit_vote()` - Form-based vote submission
  - `election_results()` - Display election results

### Data Layer
- **`serializers.py`** - All election-related serializers
  - Vote creation serializer with token/candidate validation
  - Position and candidate serializers
  - Results/analytics serializers

- **`models.py`** - Election domain models
  - `Election` - Election events
  - `ElectionLevel` - President/State/Course level elections
  - `Position` - Candidate positions
  - `Candidate` - Candidate profiles
  - `VoterToken` - One-time voting tokens
  - `Vote` - Vote records (anonymized)

- **`admin.py`** - Django admin configuration
- **`signals.py`** - Django signals for election workflows
- **`tasks.py`** - Celery tasks for token distribution and email notifications
- **`permissions.py`** - Custom permission classes for elections

### URL Configuration
- **`urls.py`** - All election routes
  - UI routes: `/elections/`, `/elections/<id>/vote/`, `/elections/<id>/results/`
  - Minimal API routes: `/api/<id>/submit/`, `/api/<id>/results/`

---

## Removed Files

The following files have been removed to clean up the codebase (see CHANGELOG.md for details):

### Core App Removals
- ❌ `views.py` - Deprecated old API views
- ❌ `api_views.py` - Unused API viewsets and helpers
- ❌ `api_health.py` - Unused health check endpoint

### Election App Removals
- ❌ `views_candidate.py` - Unused candidate API views
- ❌ `views_voting.py` - Unused election voting API views
- ❌ `serializers_voting.py` - Unused voting serializers
- ❌ `serializers_candidate.py` - Unused candidate serializers

---

## Architecture Summary

### Authentication Strategy
- **Session-based** for UI views (handled by Django middleware)
- **JWT-based** for minimal API endpoints (using `djangorestframework-simplejwt`)
- Custom registration number authentication backend

### Voting System
- **Token-based voting**: Each eligible user gets a unique UUID4 token per election level
- Tokens are generated when:
  - User is verified (via signals)
  - Election is activated (via task)
- One vote per token; tokens marked as used after voting
- Vote records are anonymized (linked to token, not user directly)

### Task Queue
- **Celery** configured with Django DB broker
- Tasks include:
  - Email notifications (verification, voting confirmation, reminders)
  - Token generation for elections
  - Scheduled reminders (5-min before start, 30-min before end)

### Database
- **Development**: SQLite (`db.sqlite3`)
- **Production**: PostgreSQL recommended
- For Celery: Use Redis/RabbitMQ for better performance

---

## Testing the Clean Codebase

### Start Django development server
```bash
cd src
python manage.py migrate
python manage.py runserver
```

### Start Celery worker (for async emails)
```bash
cd src
celery -A mw_es worker -Q email_queue --loglevel=info
```

### Run tests
```bash
cd src
python manage.py test
```

---

## Future Development Notes

- The codebase is now consolidated with a single view/serializer file per app purpose
- All URL routes are clearly documented in `urls.py` files
- No unused or "reference" code remains—only active, production-ready code
- Profile editing is now election-aware with appropriate restrictions
- Bug fixes include proper annotation naming to avoid model field conflicts

See `CHANGELOG.md` for a detailed list of changes made in this cleanup.
