# MWECAU Digital Voting System

## Overview

The MWECAU Digital Voting System is a comprehensive online platform for managing student elections at Mwenge Catholic University. The system replaces traditional paper-based voting with a secure, accessible digital solution that enables students to vote from anywhere during election periods.

**Core Purpose:** Enable transparent, secure, and accessible student elections across all MWECAU campuses with instant results and complete audit trails.

**Key Capabilities:**
- Multi-level election management (President, State Leaders, Course Leaders)
- Secure token-based voting system
- Real-time results and statistics
- Role-based access control (Voters, Candidates, Class Leaders, Commissioners)
- Student registration workflow with verification
- Email notifications for elections and verification

## Recent Changes

**October 23, 2025 - Replit Environment Setup Completed**

✅ **Replit Configuration:**
- Installed all Python dependencies via uv/pyproject.toml
- Configured Django development server on port 5000 with host 0.0.0.0
- Set up workflow for automatic server startup
- Configured deployment settings for VM deployment
- Updated .gitignore with comprehensive Python patterns
- All static files collected successfully
- Database migrations applied successfully
- Swagger API documentation available at /swagger/

**System Access:**
- Main API: http://localhost:5000/
- Swagger Docs: http://localhost:5000/swagger/
- Admin Panel: http://localhost:5000/admin/
- Django Admin credentials documented in TESTING_GUIDE.md

**Documentation Added:**
- `API_DOCUMENTATION.md` - Complete API reference with examples for all endpoints
- `SECURITY_AND_LICENSING_GUIDE.md` - Comprehensive guide for source code protection, licensing, and monetization strategies

**October 23, 2025 - Complete System Setup & Testing**

✅ **Database Setup Completed:**
- 6 States, 14 Courses, 100 College Data Entries
- 77 Users (76 verified voters + 1 admin)
- 1 Active Election with 21 Levels (1 President + 6 State + 14 Course)
- 41 Positions ready for candidates

✅ **Fixed Management Commands:**
1. **create_elections.py**: Fixed to properly create ElectionLevel instances with state/course assignments (Position doesn't have these fields)
2. **create_student_accounts.py**: Updated to use first_name/last_name fields instead of old full_name field
3. **create_sample_election.py**: Enhanced to link all election levels to elections automatically

✅ **Election System Business Logic Verified:**
1. **Vote Model Auto-Population**: Fixed `Vote.save()` to auto-populate `election`, `election_level`, and `voter` fields from token BEFORE validation
2. **Email Confirmation**: Removed invalid `.delay()` calls to `send_vote_confirmation_email` (Celery not configured)
3. **Three-Level Verification**: Architect confirmed President/Course/State levels work correctly with proper eligibility filtering

**Documentation Created:**
- `ELECTION_BUSINESS_LOGIC.md` - Comprehensive technical documentation of the partial blockchain token system
- `TESTING_GUIDE.md` - Complete testing guide with login credentials, API endpoints, and test scenarios

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Framework
**Django 5.2.7** - Python web framework providing the core application structure

**Rationale:** Django's batteries-included approach provides built-in admin interface, ORM, authentication, and security features essential for an election system. The framework's mature ecosystem and security track record make it ideal for handling sensitive voting data.

### Authentication & Authorization
**Custom User Model with Registration Number Authentication**
- Uses registration numbers instead of usernames for student identification
- Custom `UserManager` and `RegistrationNumberBackend` for authentication
- JWT tokens via `djangorestframework-simplejwt` for API authentication
- Token blacklisting support for secure logout

**Role-Based Access Control:**
- Voter: Standard students who can vote
- Candidate: Students running for positions
- Class Leader: Can upload student data
- Commissioner: Full administrative access

**Rationale:** Registration numbers are the natural identifier for university students. JWT tokens provide stateless authentication suitable for both web and potential mobile clients.

### Database Design
**SQLite** (Development) - File-based relational database

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

**Design Pattern:** The system uses a hierarchical election model where elections contain multiple levels (President, State, Course), each level has positions, and positions have candidates. This allows for complex multi-level elections in a single event.

**Rationale:** The voter token system ensures one-vote-per-position while maintaining vote anonymity. Tokens are generated per election level, allowing users to vote in all levels they're eligible for.

### API Architecture
**Django REST Framework** - RESTful API layer

**API Endpoints Structure:**
- `/api/auth/*` - Authentication (login, logout, register, verification, password reset)
- `/api/election/*` - Election operations (list, vote, results)
- Reference data endpoints for states and courses

**Serialization Strategy:**
- Separate serializers for list and detail views
- Nested serialization for related objects (courses, states, election levels)
- Context-aware serialization for user-specific data

**Rationale:** REST API design separates frontend and backend, enabling future mobile app development. DRF provides robust serialization, validation, and browsable API for development.

### Email Integration
**Django Email System** with background task functions

**Email Workflows:**
- Account verification with voter tokens (if elections active)
- Election activation notifications with level-specific tokens
- Password reset emails
- Commissioner contact form notifications

**Rationale:** Email serves as the primary communication channel for credentials and election notifications, ensuring users can access the system even if they forget login details.

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
- Database migration path to PostgreSQL for production
- Redis for caching and session management
- Celery for asynchronous task processing (email sending)
- Cloud storage (S3/GCS) for media files in production