# MWECAU DigiVote

[![Python](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Django](https://img.shields.io/badge/django-5.2-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Status](https://img.shields.io/badge/status-Live-success.svg)]()
[![MWECAU ICT Club](https://img.shields.io/badge/by-MWECAU%20ICT%20Club-purple.svg)](https://github.com/mwecauictclub)
[![Security](https://img.shields.io/badge/security-JWT%20%2B%20Session-yellow.svg)]()
[![Async](https://img.shields.io/badge/async-Django%205.2%20%2B%20Uvicorn-blueviolet.svg)]()

> Secure digital voting platform for **Mwenge Catholic University** student elections.
> No queues. No paper. Just democracy.

---

```
┌─────────────────────────────────────────┐
│           MWECAU DigiVote               │
│─────────────────────────────────────────│
│  [ Login with Reg Number ]              │
│                                         │
│  Active Elections:                      │
│  ▸ Presidential Election      [VOTE →]  │
│  ▸ Residential Leadership     [VOTE →]  │
│  ▸ Course Representative      [VOTE →]  │
│                                         │
│  Your vote is anonymous & secure        │
└─────────────────────────────────────────┘
```

---

## What It Does

- **Multi-level elections** — Presidential, Residential, Course Representative
- **Secure voting** — JWT + session auth, one-time voter tokens, tamper-proof
- **Self-service password recovery** — token-based reset link via email
- **Real-time results** — live vote counts with 30-second auto-refresh
- **Vote from anywhere** — students on campus or abroad
- **Mobile responsive** — slide-out nav, touch-friendly, works on any device
- **High performance** — async Django views, Redis cache, Celery task queue

---

## Architecture

```
Internet
    │
  Nginx                  ← reverse proxy, SSL, static files
    │
  Uvicorn (ASGI)         ← async Django 5.2 app server
    │
  Django App             ← async views, DRF API, JWT + session auth
    │            ╲
  PostgreSQL      Redis  ← sessions, cache, Celery broker
                    │
              Celery Workers  ← email, notifications (batched)
```

**Why this stack:**
- Async Django views handle high concurrent load without blocking on I/O
- Redis sessions make all app instances stateless — ready for horizontal scaling
- Celery dispatches 5000+ voter emails in parallel batches of 50, not a single blocking loop
- WhiteNoise + Uvicorn serve static files and requests efficiently in production

---

## Election Scope

| Type | Who Votes |
|------|-----------|
| Presidential | All MWECAU students |
| Residential | Kifumbu, Mawela, Kwachange, White House, Moshi Mjini, On-Campus |
| Course | All undergraduate, postgraduate and diploma programs |

---

## Key URLs

| Page | URL |
|------|-----|
| Home | `/` |
| Login | `/login/` |
| Register | `/register/` |
| Forgot Password | `/password-reset/` |
| Dashboard | `/dashboard/` |
| Active Elections | `/elections/` |
| Cast Vote | `/elections/<id>/vote/` |
| Results | `/elections/<id>/results/` |
| Commissioner Panel | `/commissioner/` |
| Observer Dashboard | `/observer/` |
| Admin Panel | `/admin/` |

---

## Setup — Local Development

**Requirements:** Python 3.12+, PostgreSQL (or SQLite for dev)

```bash
# Clone and enter the project
git clone https://github.com/mwecauictclub/digivote.git
cd digivote

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database and email credentials

# Run migrations
python src/manage.py migrate

# Start development server
python src/manage.py runserver
```

---

## Setup — Production (Uvicorn + Nginx)

```bash
# Install and start Redis
sudo apt install redis-server
sudo systemctl enable redis

# Update .env for production
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
REDIS_URL=redis://127.0.0.1:6379/1
CELERY_ALWAYS_EAGER=False
DEBUG=False

# Collect static files
python src/manage.py collectstatic --noinput

# Start Uvicorn (async ASGI server)
uvicorn mw_es.asgi:application --workers 9 --loop uvloop --host 0.0.0.0 --port 8000

# Start Celery worker (separate terminal or systemd service)
celery -A celery_app worker -l info -Q email_queue -c 4
```

Configure Nginx to proxy to port 8000 and serve `/static/` and `/media/` directly.

---

## User Roles

| Role | Access |
|------|--------|
| Voter | Login, vote, view own dashboard and results |
| Candidate | Same as voter + candidate profile |
| Class Leader | Upload college data for student registration |
| Commissioner | Full election management, user verification, analytics |
| Observer | Read-only access to live results and statistics |

---

## Security

- Registration number + password authentication (custom auth backend)
- One-time voter tokens per election level (UUID, expiry-enforced)
- Vote anonymity — votes are linked to tokens, not identities
- Password reset via time-limited secure links (1-hour expiry)
- Brute-force protection — 5 failed logins trigger 15-minute lockout
- CSRF protection on all state-changing requests
- Rate limiting on API endpoints via DRF throttle classes
- Security headers — HSTS, X-Frame-Options, Content-Type-Nosniff

---

## Team

- **[Cleven](https://github.com/cleven12)** — Project Manager & Lead Developer
- **[Lajokjohn](https://github.com/Lajokjohn)** — Technical Lead
- **[Faustine Emmanuel](https://github.com/FaustineEmmanuel)** — Feature Developer
- **[almaleko2022@gmail.com](https://github.com/almaleko2022@gmail.com)** - User Research & Prototyping
- **[MWECAU ICT Club](https://github.com/mwecauictclub)** — Institution

---

**© 2026 MWECAU ICT Club** · MIT License · *One vote at a time.*
