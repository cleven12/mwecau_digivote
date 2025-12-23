# MWECAU Digital Voting System (Club Edition)

A lightweight, HTML-first Django project for student elections. Bootstrap and collected static bundles have been removed to keep the interface plain and easy to extend.

## Quick start (development)
```bash
cd src
cp ../.env.example .env   # demo values only; set real secrets before deploy
python manage.py migrate
python manage.py runserver
```

## Environment
- All demo environment variables live in `.env.example` (no secrets committed).
- For production, copy `.env.example` and provide real values via your host/secret manager.

## Data
- No sample data or auto-seeding commands are shipped. Add users, courses, and elections manually via the admin UI or your own import tools.

## Stack
- Django with a custom `User` model (see `core` app)
- Django REST Framework with JWT + Session auth
- SQLite for development; use PostgreSQL in production

## Key URLs
- UI: `/`, `/login/`, `/register/`, `/dashboard/`
- Elections: `/elections/`, `/elections/<id>/vote/`, `/elections/<id>/results/`
- Commissioner APIs: `/api/commissioner/stats/`, `/api/commissioner/election/<id>/analytics/`

## Documentation
- [`docs/`](docs/) - Technical documentation
- [`CONTRIBUTING.md`](CONTRIBUTING.md) - How to contribute
- [`CONTRIBUTORS.md`](CONTRIBUTORS.md) - Project contributors
- [`LICENSE`](LICENSE) - MIT License

## Contributing
- Plain HTML/CSS, no Bootstrap. Feel free to style with your own CSS.
- See [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines.

## Acknowledgments
- [@cleven12](https://github.com/cleven12) (Cleven)
- [@Lajokjohn](https://github.com/Lajokjohn) (Lajokjohn)
- [@FaustineEmmanuel](https://github.com/FaustineEmmanuel) (Faustine)
- [@mwecauictclub](https://github.com/mwecauictclub) (Mwecau_ict_club, club account)

## Notes
- Celery integrations remain optional; configure a real broker if needed.
- Run `python manage.py collectstatic` in your target environment to generate static assets.