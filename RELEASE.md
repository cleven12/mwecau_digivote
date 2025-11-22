# MWECAU Digital Voting System

## Overview

The MWECAU Digital Voting System is a comprehensive online platform for managing student elections at Mwenge Catholic University. The system has been converted to a lean Django server-rendered app with minimal API endpoints for voting and results.

**Core Purpose:** Enable transparent, secure, and accessible student elections across all MWECAU campuses with instant results and complete audit trails.

**Key Capabilities:**
- Multi-level election management (President, State Leaders, Course Leaders)
- Secure token-based voting system
- Django session-based authentication
- Minimal JSON API for voting submission and results
- Server-rendered UI with Django templates

## Recent Changes

**November 14, 2025 - Complete Voting System Implementation**

**Voting System Features:**
- Elections listing page showing all active elections
- Complete voting UI with candidate photos and information
- Vote submission with confirmation
- Results viewing (for commissioners, admins, or after election ends)
- Real-time vote counting and percentage calculations
- Integration with dashboard showing user's voting tokens and status

**Sample Data Created:**
- 100 verified student accounts (password: @2025)
- 1 active election: "University Elections 2025"  
- 11 candidates across President and State leader positions
- Multiple voting levels (President, State leaders)

**November 14, 2025 - Lean UI Conversion Complete**

**Major Refactor - API-First to Server-Rendered:**
- Removed heavy dependencies: JWT authentication, CORS headers, Swagger documentation
- Simplified REST framework configuration to Session authentication only
- Converted to Django session-based authentication (login, logout, register)
- Created function-based views for UI (replacing class-based API views)
- Built simple HTML templates without styling (login, register, dashboard, home)
- Kept only 2 minimal API endpoints:
  - POST /api/election/{election_id}/submit/ - Submit vote with voter token
  - GET /api/election/{election_id}/results/ - Retrieve election results (JSON)

**Updated Dependencies:**
- Removed: djangorestframework-simplejwt, django-cors-headers, drf-yasg, mysqlclient
- Kept minimal: Django 5.2.8, DRF (for API endpoints only), Pillow, psycopg2-binary
- Added: gunicorn (for production deployment)

**Configuration Changes:**
- Updated .env.example with minimal configuration
- Simplified settings.py - removed JWT/CORS/Swagger config
- Updated requirements.txt - removed heavy packages
- Clean URLs - removed unused API endpoints

**UI Implementation:**
- Home page: Introduction and navigation to login/register
- Login page: Session-based authentication with registration number and password
- Register page: New user registration with college data validation
- Dashboard: User info, voting tokens, active elections, API endpoint documentation

**November 14, 2025 - Cloud Environment Setup**
- Imported project from GitHub
- Installed Python 3.12 and all dependencies via packager tool
- Configured Django to run on port 5000 with host 0.0.0.0
- Set up SQLite database for development (db.sqlite3)
- Configured ALLOWED_HOSTS=['*'] and CSRF_TRUSTED_ORIGINS for Cloud domains
- Ran database migrations successfully
- Created static/css/style.css with clean, minimal CSS styling
- Collected static files to staticfiles/
- Created workflow for automatic server startup (webview on port 5000)
- Configured VM deployment with Gunicorn (2 workers)
- Server running successfully with professional UI styling

**Test Data Available:**
- 6 States
- 14 Courses
- 2 Users (with voting tokens)
- 1 Active Election

## System Architecture

### Backend Framework
**Django 5.2.8** - Python web framework with server-rendered templates

**Rationale:** Lean, server-rendered approach reduces frontend complexity and heavy dependencies while maintaining security and functionality.

### Authentication & Authorization
**Django Session Authentication**
- Uses registration numbers instead of usernames for student identification
- Custom `UserManager` and `RegistrationNumberBackend` for authentication
- Django's built-in session authentication for UI
- Session authentication for API endpoints

**Role-Based Access Control:**
- Voter: Standard students who can vote
- Candidate: Students running for positions
- Class Leader: Can upload student data
- Commissioner: Full administrative access

### Database Design
**SQLite** (Development) - File-based relational database
**PostgreSQL/MySQL** (Production-ready via psycopg2-binary)

**Core Data Models:**

1. **User Management:**
   - `User`: Central authentication with voter IDs, registration numbers, roles
   - `CollegeData`: Pre-registration student data for validation
   - `State`: Geographic/administrative divisions
   - `Course`: Academic programs

2. **Election System:**
   - `Election`: Election events with date ranges and active status
   - `ElectionLevel`: Multi-level election hierarchy (President, State, Course)
   - `Position`: Specific roles within elections (with gender restrictions)
   - `Candidate`: User candidacies for positions
   - `VoterToken`: Unique per-user, per-election, per-level voting tokens
   - `Vote`: Anonymized voting records

**Design Pattern:** The system uses a hierarchical election model where elections contain multiple levels (President, State, Course), each level has positions, and positions have candidates.

### API Architecture
**Minimal REST API** - Only for voting and results

**API Endpoints (JSON):**
- POST /api/election/{election_id}/submit/ - Submit vote with voter token in payload
- GET /api/election/{election_id}/results/ - Retrieve election results

**Authentication:**
- Session authentication (must be logged in via UI first)
- Voter token validation in payload for voting endpoint

### Security Features

1. **Vote Anonymity:** Votes are not linked to users in the database
2. **Token-Based Voting:** Unique UUIDs prevent duplicate votes
3. **CSRF Protection:** Enabled for all form submissions
4. **Password Hashing:** Django's built-in secure password hashing
5. **Session Security:** Django's secure session management
6. **Verification System:** Two-step registration with admin verification

### Multi-Level Election System

**Three Election Levels:**
1. **President:** University-wide, all students eligible
2. **State Leader:** State-specific, filtered by student's state
3. **Course Leader:** Course-specific, filtered by student's course

**Eligibility Logic:** Users receive tokens only for levels they're eligible to vote in based on their state and course assignments.

### Frontend Architecture
**Server-Side Rendered Templates** with minimal custom CSS

**Technology Stack:**
- Django Template Language
- Custom CSS with gradient purple theme
- Function-based views
- Django forms and validation
- Responsive design with clean UI

**URL Structure:**
- / - Home page
- /login/ - Login page
- /register/ - Registration page
- /dashboard/ - User dashboard
- /admin/ - Django admin panel

## External Dependencies

### Python Packages (Minimal)
- **Django 5.2.8** - Web framework
- **djangorestframework** - Minimal REST API (voting & results only)
- **Pillow** - Image processing
- **psycopg2-binary** - PostgreSQL adapter
- **python-dotenv** - Environment variable management
- **requests** - HTTP library
- **gunicorn** - Production WSGI server

### Minimal Frontend Dependencies
- Pure HTML templates with Django template language
- Custom CSS (static/css/style.css) - clean, minimal styling
- No CSS frameworks (Bootstrap, Tailwind, etc.)
- No JavaScript libraries required
- Server-rendered only with beautiful gradient design

## Cloud Environment

### Access Points
- Main Application: Webview (port 5000)
- Home: / (redirects to dashboard if logged in)
- Login: /login/
- Register: /register/
- Dashboard: /dashboard/
- Admin Panel: /admin/
- API: /api/election/{id}/submit/ and /api/election/{id}/results/

### Environment Variables (.env)
Located in `src/.env` with Cloud-compatible configuration:
- DEBUG=True
- ALLOWED_HOSTS includes *.dev and *.co
- CSRF_TRUSTED_ORIGINS configured for Cloud domains
- SQLite database configured
- Email console backend for development

### Workflow
- **Django Server**: `cd src && python manage.py runserver 0.0.0.0:8000`
- Auto-starts on Cloud
- Bound to 0.0.0.0:8000 for webview access

### Deployment Configuration
- **Target**: VM (always-on server for stateful election system)
- **Command**: gunicorn with 2 workers
- **Reloadable**: Database migrations and static files collection via Django

## User Preferences

Preferred communication style: Simple, everyday language.
