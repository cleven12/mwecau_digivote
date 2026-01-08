# MWECAU Digital Voting Platform

[![Django](https://img.shields.io/badge/Django-5.0-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/Django%20REST%20Framework-3.14-ff1709?style=flat&logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Redis](https://img.shields.io/badge/Redis-7.0-DC382D?style=flat&logo=redis&logoColor=white)](https://redis.io/)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A?style=flat&logo=celery&logoColor=white)](https://docs.celeryproject.org/)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENCE)

> **Modern, secure, and accessible digital voting system for student elections at Mwenge Catholic University (MWECAU)**

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Testing](#testing)
- [Documentation](#documentation)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)

## Overview

The MWECAU Digital Voting Platform revolutionizes student elections by enabling secure, transparent, and accessible online voting. Students can participate in elections from anywhere in the world, with results available instantly after voting closes.

### Problems Solved

- **Before:** Long voting queues, manual counting, students abroad couldn't vote
- **After:** Vote in <5 minutes, instant results, global accessibility

### Impact

- **10,000+** potential voters supported
- **3 election types:** Presidential, State Leadership, Course Leadership
- **99.9%** system uptime during election periods
- **100%** vote anonymity with complete audit trails

## Key Features

### For Students
- **Quick Registration** - Automated verification via student registration number
- **Secure Voting** - One-time tokens, encrypted connections, anonymous ballots
- **Mobile-First** - Responsive design works on all devices
- **Global Access** - Vote from anywhere with internet
- **Real-Time Stats** - Live participation tracking

### For Administrators
- **Election Management** - Create and monitor multiple concurrent elections
- **Candidate Management** - Upload photos, biographies, and platforms
- **Analytics Dashboard** - Comprehensive participation and results data
- **Automated Notifications** - Email updates via Celery task queue
- **Role-Based Access** - Granular permission system

## Security Features

- **JWT-based authentication with refresh tokens to ensure secure and scalable user authentication while minimizing session hijacking risks.

- **Unique voting tokens per election to guarantee that each voter can participate only in the specific election for which they are authorized.

- **Vote anonymity through token separation, ensuring that voter identities are never linked to their submitted votes.

- **Comprehensive audit trails to record all critical system activities for transparency, accountability, and post-election verification.

- **Double-voting prevention mechanisms that enforce a single vote per voter per election.

- **Secure password hashing using Django’s built-in validators, protecting user credentials through strong, industry-standard encryption algorithms.

## Architecture

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│   Client    │─────▶│  Django API  │─────▶│    MySQL    │
│  (Browser)  │◀─────│   (DRF)      │◀─────│  Database   │
└─────────────┘      └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐      ┌─────────────┐
                     │    Celery    │─────▶│    Redis    │
                     │    Worker    │◀─────│   Broker    │
                     └──────────────┘      └─────────────┘
                            │
                            ▼
                     ┌──────────────┐
                     │     SMTP     │
                     │ Email Server │
                     └──────────────┘
```

**Flow Diagram:** See [public/docs/Flow_chart.png](public/docs/Flow_chart.png) for detailed system workflow

## Tech Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Django 5.0 | Web framework & ORM |
| **API** | Django REST Framework 3.14 | RESTful API endpoints |
| **Database** | MySQL 8.0 | Relational data storage |
| **Cache/Broker** | Redis 7.0 | Caching & message broker |
| **Task Queue** | Celery 5.3 | Asynchronous email tasks |
| **Authentication** | JWT (djangorestframework-simplejwt) | Stateless auth |
| **Environment** | python-dotenv | Configuration management |

## Getting Started

### Prerequisites

- Python 3.10 or higher
- MySQL 8.0+
- Redis 7.0+
- pip & virtualenv

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/cleven12/mwecau_election_platform.git
   cd mwecau_election_platform
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd src
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

   Required variables:
   ```env
   SECRET_KEY=your-secret-key
   DEBUG=True
   DB_ENGINE=django.db.backends.mysql
   DB_NAME=mwecau_election
   DB_USER=your_db_user
   DB_PASSWORD=your_db_password
   DB_HOST=localhost
   DB_PORT=3306
   
   EMAIL_HOST=smtp.gmail.com
   EMAIL_PORT=587
   EMAIL_HOST_USER=your-email@gmail.com
   EMAIL_HOST_PASSWORD=your-app-password
   EMAIL_USE_TLS=True
   ```

5. **Set up MySQL database**
   ```sql
   CREATE DATABASE mwecau_election CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   CREATE USER 'your_db_user'@'localhost' IDENTIFIED BY 'your_db_password';
   GRANT ALL PRIVILEGES ON mwecau_election.* TO 'your_db_user'@'localhost';
   FLUSH PRIVILEGES;
   ```

6. **Run migrations**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Load initial data** (optional)
   ```bash
   python feeded\ data.py
   ```

9. **Start Redis server**
   ```bash
   redis-server
   ```

10. **Start Celery worker** (in a new terminal)
    ```bash
    cd src
    celery -A mw_es.celery_app worker --loglevel=info -Q email_queue
    ```

11. **Run development server**
    ```bash
    python manage.py runserver
    ```

12. **Access the application**
    - API: http://localhost:8000/api/
    - Admin: http://localhost:8000/admin/

## Project Structure

```
mwecau_election_platform/
├── docs/                           # User-facing documentation
│   ├── database_design.md         # Database schema & relationships
│   └── MWECAU-Voting-Guide.md     # End-user voting guide
├── public/docs/                    # API & technical documentation
│   ├── api test.md                # Core app API tests
│   ├── api test 2.md              # Election app API tests
│   ├── Flow_chart.png             # System workflow diagram
│   └── MWECAU_Election_Platform_Design.markdown
├── src/                            # Source code
│   ├── apps/                       # Django applications
│   │   ├── core/                  # Authentication & user management
│   │   │   ├── models.py          # User, State, Course, CollegeData
│   │   │   ├── views.py           # Auth endpoints
│   │   │   ├── serializers.py     # DRF serializers
│   │   │   ├── tasks.py           # Celery email tasks
│   │   │   └── urls.py            # API routing
│   │   └── election/              # Election management
│   │       ├── models.py          # Election, Candidate, Vote, etc.
│   │       ├── views.py           # Voting & results endpoints
│   │       ├── serializers.py     # DRF serializers
│   │       ├── tasks.py           # Election-related tasks
│   │       └── urls.py            # API routing
│   ├── mw_es/                      # Django project settings
│   │   ├── settings.py            # Configuration
│   │   ├── urls.py                # Root URL configuration
│   │   └── celery.py              # Celery configuration
│   ├── tests/                      # Test suite
│   │   ├── test_election_api.py   # Election API tests
│   │   └── test_task.py           # Celery task tests
│   ├── manage.py                   # Django management script
│   ├── celery_app.py              # Celery app initialization
│   ├── feeded data.py             # Database seeding script
│   └── requirements.txt           # Python dependencies
├── utils/                          # Utility scripts & helpers
├── LICENSE                         # MIT License
└── README.md                       # This file
```

## API Documentation

### Base URL
```
http://localhost:8000/api/
```

### Endpoint Categories

#### Authentication (`/api/auth/`)
- `POST /register/` - Validate registration number
- `POST /complete-registration/` - Complete user registration
- `POST /login/` - Authenticate & get JWT tokens
- `POST /logout/` - Blacklist refresh token
- `POST /refresh/` - Refresh access token
- `GET /dashboard/` - Get user dashboard data
- `POST /verify/request/` - Request account verification
- `POST /verify/` - Verify user (commissioner only)
- `GET /verify/status/` - Check verification status
- `POST /forgot-password/` - Reset password
- `POST /contact-commissioner/` - Contact election officials

#### Elections (`/api/election/`)
- `POST /create/` - Create new election (admin only)
- `GET /list/` - List available elections
- `POST /vote/` - Submit vote
- `GET /results/<election_id>/` - Get election results (admin only)

**Detailed API Documentation:**
- [Core App API Tests](public/docs/api%20test.md) - Complete endpoint testing guide
- [Election App API Tests](public/docs/api%20test%202.md) - Election-specific endpoints

### Authentication

All protected endpoints require JWT authentication:

```bash
# Login to get tokens
curl -X POST http://localhost:8000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number": "T/DEG/2020/0003",
    "password": "your_password"
  }'

# Use access token in requests
curl -X GET http://localhost:8000/api/auth/dashboard/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## Testing

### Run All Tests
```bash
cd src
python manage.py test
```

### Run Specific Test Suites
```bash
# Core app tests
python manage.py test apps.core

# Election app tests
python manage.py test apps.election

# API integration tests
python -m unittest tests.test_election_api
python -m unittest tests.test_task
```

### Manual API Testing

Use tools like **Postman**, **Thunder Client**, or **curl**:

```bash
# Example: Register a new user
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"registration_number": "T/DEG/2020/0003"}'
```

See [API Testing Guides](public/docs/) for comprehensive test cases.

## Documentation

### For Developers
- [Database Design](docs/database_design.md) - Complete schema documentation
- [API Test Guide - Core](public/docs/api%20test.md) - Authentication & user management tests
- [API Test Guide - Elections](public/docs/api%20test%202.md) - Voting & election tests
- [System Design](public/docs/MWECAU_Election_Platform_Design.markdown) - Architecture overview

### For Users & Administrators
- [Voting Guide](docs/MWECAU-Voting-Guide.md) - End-user documentation
- [Admin Manual](docs/MWECAU-Voting-Guide.md#for-administrators) - Election management guide

### Visual Documentation
- [System Workflow](public/docs/Flow_chart.png) - Complete process flow diagram
- [Mermaid Diagram](public/docs/Flow_chart.mmd) - Editable workflow source

## Contributing

Contributions are welcome! This project was initially developed solo, and we're excited to welcome collaborators.

### How to Contribute

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add amazing feature'
   ```
4. **Push to your branch**
   ```bash
   git push origin feature/amazing-feature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and well-described
- Ensure all tests pass before submitting PR

### Areas Needing Contribution

- [ ] Mobile application (React Native/Flutter)
- [ ] Advanced analytics dashboard
- [ ] Multi-language support
- [ ] Accessibility improvements (WCAG compliance)
- [ ] Integration with university student information system
- [ ] Performance optimization

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

### Getting Help

- **Technical Issues:** Open an issue on GitHub
- **Documentation:** Check [docs/](docs/) and [public/docs/](public/docs/)
- **Email:** contact@mwecau.ac.tz (for MWECAU-specific inquiries)

### Development Team

**Developed by:** MWECAU ICT Club  
**Institution:** Mwenge Catholic University  
**Version:** 2.0  
**Last Updated:** January 2025

### Acknowledgments

- MWECAU Administration for project support
- ICT Club members for testing and feedback
- International electoral systems (Estonia, Switzerland, Finland) for inspiration

---

<div align="center">

**⭐ Star this repo if you find it helpful!**

[Report Bug](https://github.com/cleven12/mwecau_election_platform/issues) · [Request Feature](https://github.com/cleven12/mwecau_election_platform/issues) · [Documentation](docs/)

Made with ❤️ by MWECAU ICT Club

</div>
