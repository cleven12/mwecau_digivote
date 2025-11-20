# MWECAU Election Platform Design Document

## Overview

The MWECAU Election Platform is a secure, transparent, and efficient web-based voting system for Mwenge Catholic University (MWECAU) student elections. It uses Django for the backend, Django REST Framework (DRF) for APIs, MySQL for the database, JWT for authentication, Celery for asynchronous tasks (e.g., email sending), Redis as the message broker for Celery, and <del>Ethereum blockchain </del>for anonymous voting. The system supports user registration, authentication, password recovery, contacting commissioners, and election voting with voter tokens.

Key features:
- Secure authentication via registration number and password.
- User verification and voter token generation for active elections.
- Asynchronous email notifications using Celery and Redis.
- >><del> Blockchain integration for immutable and anonymous vote recording.</del>
- Mobile-responsive frontend (not detailed here, assuming HTML/CSS/JS).

The project structure is:
```
mwecau_election_platform/
├── docs/
│   └── MWECAU-Voting-Guide.md
├── src/
│   ├── backend/  # Django backend with core and election apps - development phase
│   ├── frontend/  # Frontend - development phase
│   ├── full_stack/  # Integrated app - production phase
│   └── voting_services # Futured
└── README.md
```

## Technology Stack

- **Backend**: Django 5.2.5
- **API**: Django REST Framework (DRF)
- **Authentication**: Django Authentication with JWT (rest_framework_simplejwt)
- **Database**: MySQL (with tables like state_majimbo, course, users, college_data, election, election_level, voter_token)
- **Asynchronous Tasks**: Celery 5.5.3 (for emails, voting(<del>Blockchain</del>) syncing)
- **Message Broker**: Redis 6.4.0 (for Celery queues and results)
- <del>**Blockchain**: Ethereum (Sepolia testnet), web3.py, Solidity for smart contracts </del>
- <del>**Anonymity**: Blind signatures or ZKPs for votes </del>
- **Other**: Cryptography for security, logging for debugging

## Database Schema

The database uses MySQL with the following tables (based on the development ERD and models, <i>PostgreSQL DB from production</i>) :

- **state_majimbo** (State):
  - id (PK, int)
  - name (varchar, unique)
  - created_at (datetime)
  - updated_at (datetime)

- **course** (Course):
  - id (PK, int)
  - name (varchar)
  - code (varchar, unique)
  - created_at (datetime)
  - updated_at (datetime)

- **users** (User):
  - id (PK, int)
  - registration_number (varchar, unique)
  - email (varchar, unique)
  - voter_id (varchar, unique, nullable)
  - first_name (varchar)
  - last_name (varchar)
  - gender (varchar, nullable)
  - state_id (FK to state_majimbo, nullable)
  - course_id (FK to course, nullable)
  - role (varchar, default 'voter')
  - is_verified (boolean, default False)
  - date_verified (datetime, nullable)
  - last_login_ip (varchar, nullable)
  - is_staff (boolean)
  - is_superuser (boolean)
  - is_active (boolean)
  - date_joined (datetime)
  - last_login (datetime, nullable)
  - password (varchar, hashed)

- **college_data** (CollegeData):
  - id (PK, int)
  - registration_number (varchar, unique)
  - first_name (varchar)
  - last_name (varchar)
  - email (varchar, unique)
  - voter_id (varchar, unique, nullable)
  - course_id (FK to course)
  - uploaded_by_id (FK to users)
  - is_used (boolean, default False)
  - created_at (datetime)
  - status (varchar, default 'pending')

- **election** (Election):
  - id (PK, int)
  - title (varchar)
  - start_date (date)
  - end_date (date)
  - is_active (boolean, default False)
  - has_ended (boolean, default False)
  - created_at (datetime)
  - updated_at (datetime)

- **election_level** (ElectionLevel):
  - id (PK, int)
  - name (varchar)
  - code (varchar, unique)
  - created_at (datetime)
  - updated_at (datetime)

- **voter_token** (VoterToken):
  - id (PK, int)
  - user_id (FK to users)
  - election_id (FK to election)
  - token (uuid)
  - is_used (boolean, default False)
  - created_at (datetime)

Relationships:
- User → State/Course (One-to-Many, nullable/mandatory).
- CollegeData → Course/User (One-to-Many).
- VoterToken → User/Election (One-to-Many, unique per user-election).

## Architecture

The backend is structured as a Django monolith with modular apps (`core` for authentication/user management, `election` for voting logic), <del> <i>with an optional microservice for blockchain interactions </i></del>. The architecture includes:

- **Frontend Layer**: HTML/CSS/JS (responsive), interacts with DRF APIs.
- **API Layer**: DRF endpoints for authentication, user management, and elections (e.g., `/api/auth/register/`, `/api/auth/login/`, `/api/election/vote/`).
- **Business Logic Layer**: Django views and serializers handle validation, authentication (JWT), and data processing.
- **Data Layer**: MySQL for persistent storage (users, elections, tokens).
- **Asynchronous Layer**: Celery workers process tasks (e.g., emails) using Redis as broker/backend.
- **Security Layer**: JWT for authentication, cryptography for anonymity in <del> blockchain </del> voting.
- <del> **Blockchain Layer**: Ethereum smart contracts for vote recording, integrated via web3.py in a microservice or directly in views. </del>
- **Logging/Debugging**: Built-in Django logging for monitoring.

High-level diagram (text-based):

```
Frontend (HTML/CSS/JS) <--> DRF APIs (JWT Auth)
  |
  v
Django Views/Serializers (Core & Election Apps)
  |
  v
MySQL Database (Users, Elections, Tokens)
  |
  v
Celery Tasks (Emails, Syncing) <--> Redis (Broker/Backend)
  |
  v
Blockchain Microservice (Ethereum, web3.py) <<Future Intergration>>
```

## Sequential Flow of Actions

The flow is described sequentially, including registration, token generation, email (Celery/Redis), forgotten password, login (JWT), contacting commissioner, and election voting.

### 1. User Registration (/api/auth/register/)
- User sends POST request with `registration_number` (e.g., `T/DEG/2020/0003`).
- View (`UserRegisterView`):
  - Queries `CollegeData` for matching `registration_number`.
  - Checks if `User` exists or `CollegeData.is_used=True` → Return 400 if true.
  - Checks if `college_data.course` exists → Return 400 if not.
  - Prepares data: `registration_number`, `first_name`, `last_name`, `email` (handled if blank), `is_verified: False`, `role: 'voter'`, `course: college_data.course.pk`.
  - Validates with `UserSerializer` (outputs `course` as name via `CharField(source='course.name')`).
- Response: 200 with serialized data (e.g., `"course": "Computer Science"`).

### 2. Registration Completion (/api/auth/complete-registration/)
- User sends POST request with `registration_number`, `state`, `email`, `password`, `course_id`.
- View (`CompleteRegistrationView`):
  - Validates data with `UserSerializer`.
  - Checks if `email` is unique.
  - Queries `CollegeData` (must be `is_used=False`).
  - Creates `User` from `CollegeData`: Sets password, `state`, `course`, `is_verified=True`, `date_verified=now`.
  - Updates `CollegeData.is_used=True`.
  - Generates `VoterToken` for active elections (one per election, UUID token).
  - Queues Celery task: `send_verification_email.delay(user.id, voter_tokens)` (uses Redis queue).
- Celery/Redis:
  - Celery worker processes `send_verification_email`: Sends email with voter tokens.
  - Redis stores task queue and results.
- Response: 201 with message, `voter_id`, `voter_tokens`.

### 3. Login (/api/auth/login/)
- User sends POST request with `registration_number`, `password`.
- View (`UserLoginView`):
  - Uses `CustomTokenObtainPairSerializer`: Authenticates via custom backend (`RegistrationNumberBackend`).
  - If valid, generates JWT access/refresh tokens using `RefreshToken.for_user(user)`.
- Response: 200 with `access` and `refresh` tokens.

### 4. Forgotten Password (/api/auth/forgot-password/)
- User sends POST request with `registration_number`, `email`, `state`, `course`, `first_name` (optional), `last_name` (optional).
- View (`ForgotPasswordView`):
  - Validates with `ForgotPasswordSerializer`.
  - Queries `User` matching fields.
  - If match, generates new password, sets it on `User`.
  - Queues Celery task: `send_password_reset_email.delay(user.id, new_password)` (via Redis).
- Celery/Redis:
  - Celery worker processes `send_password_reset_email`: Sends email with new password.
- Response: 200 with "Password reset email sent".

### 5. Contact Election Commissioner (/api/auth/contact-commissioner/)
- Authenticated user sends POST request with `message`.
- View (`ContactCommissionerView`):
  - Validates message.
  - Queues Celery task: `send_commissioner_contact_email.delay(user.id, message)` (via Redis).
- Celery/Redis:
  - Celery worker processes `send_commissioner_contact_email`: Sends email to commissioners.
- Response: 200 with "Message sent to commissioners".

### 6. Election Voting
- Authenticated user sends POST request to `/api/election/vote/` with `election_id`, `candidate_id`.
- View (`VoteView` or similar in election app):
  - Checks if election is active.
  - Retrieves or creates `VoterToken` for user and election (one-time token, UUID).
  - If token used, return 400.
 <del> - Prepares blinded vote for anonymity (using cryptography).
  - Sends to blockchain microservice or directly submits via web3.py to Ethereum smart contract.
  - Marks token as used.
- Celery/Redis:
  - <del> Queues task for syncing vote tallies from blockchain to database (e.g., `sync_blockchain_votes.delay(election_id)`).
  - <del> Celery worker processes sync: Polls blockchain events, updates election tallies.
- <del> Blockchain:
  - Smart contract records anonymous vote (using blind signatures or ZKPs). </del>
 - <del> Returns transaction hash. </del>
- Response: 200 with success and tx_hash.

### Authentication (JWT)
- All protected endpoints use `IsAuthenticated` permission.
- JWT tokens from login are used in headers (`Authorization: Bearer <access_token>`).
- Refresh tokens for new access tokens via `/api/auth/token/refresh/`.
- Logout blacklists refresh token.

## Sequential Flow Diagram

The following is a high-level sequential flow:

1. User registers → Validates CollegeData → Returns details.
2. User completes registration → Creates User, generates VoterToken → Celery sends email.
3. User logs in → JWT tokens issued.
4. Forgotten password → Validates → Celery sends reset email.
5. Contact commissioner → Validates → Celery sends message email.
6. Election voting → Validates token → <del> Submits to blockchain </del> → Celery syncs results.

For a detailed flowchart, refer to the Mermaid diagram [here](./Flow_chart.png).

## Deployment Considerations
- Run Django: `python manage.py runserver`.
- Celery: `celery -A mw_es.celery_app worker --loglevel=info -Q email_queue`.
- Redis: `redis-server`.
- <del>Blockchain: Use Infura for Ethereum node, deploy Solidity contract via Remix.</del>
