# Contributing

Thank you for contributing to the MWECAU Digital Voting System. This document explains how to contribute changes safely and consistently.

Before you start
- Read `README.md` and `docs/ARCHITECTURE.md` to understand the code structure.
- Create an issue describing the change if one does not exist.

Workflow
- Fork or branch from `origin/version-8` (current working branch).
- Make small, focused commits with clear messages. Prefer one change per pull request.
- Run tests (if available) and linting before submitting a PR.

Coding style
- Follow existing project style (PEP8 for Python).
- Keep changes minimal and focused.

Testing & validation
- If you change models or migrations, include migration files and explain DB changes in the PR.
- Manually test registration, login, voting flow, and results aggregation when changing core election logic.

Documentation
- Update docs (`README.md`, files in `docs/`) to match changes in behavior or deployment.
- Add CHANGELOG entries for release-impacting changes.

Security
- Do not commit API keys, secrets, or passwords. Use environment variables.
- If you discover a security issue, report it privately to the repository owner instead of opening a public issue.

Pull Requests
- Title should be concise and descriptive.
- Description should explain why the change is needed and link to any relevant issue.
- Include migration notes and any required manual steps for deployment.

Contact
- For questions, open an issue or contact the repository owner.
