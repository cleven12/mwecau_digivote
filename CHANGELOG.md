# Changelog

All notable changes to this project should be documented in this file.

Formatting: This project follows a simplified Keep a Changelog style.

Unreleased
---------

### Comprehensive Email Notification & Token Management System (2025-12-07)

**Email Notifications:**
- User verification email sent when user is verified (self-registered or admin-approved)
- Verification email includes voting tokens for all active elections user is eligible for
- Election activation emails sent to all eligible voters with their per-level tokens
- 5-minute pre-election start reminder emails to all voters with active tokens
- 30-minute pre-election end reminder emails ONLY to non-voters, showing which levels they haven't voted in
- Post-vote confirmation congratulation emails thanking voter for participation
- Custom notification emails from admin panel to election voters

**Token Management:**
- Voter ID automatically generated when user is created (applies to both self-registered and admin-created users)
- Voting tokens automatically generated when user is verified (via Django signal)
- Tokens created for all eligible election levels based on user's state/course assignment
- Tokens generated when election is activated for all verified eligible voters
- Token eligibility determined by:
  - President level: All verified voters eligible
  - Course level: Only voters assigned to that course
  - State level: Only voters assigned to that state

**Signal Improvements:**
- Refactored `src/core/signals.py`:
  - `capture_old_verification_state` - Tracks old verification status
  - `generate_voter_id_on_create` - Auto-generates voter ID for new users
  - `generate_tokens_on_verification` - Triggers token generation and email when user is verified
  - `notify_on_state_change` - Notifies users of state changes
- Refactored `src/election/signals.py`:
  - `capture_old_election_state` - Tracks old election state
  - `handle_election_activation` - Triggers voter notifications AND scheduled reminders when election is activated

**Task Improvements (src/core/tasks.py):**
- `send_verification_email()` - Enhanced to generate tokens for active elections
- `send_password_reset_email()` - Unchanged
- `send_commissioner_contact_email()` - Unchanged
- Helper `_check_eligibility()` - Determines token eligibility for users

**Task Improvements (src/election/tasks.py):**
- `send_verification_email()` - Redundant (kept in core/tasks.py as primary)
- `notify_voters_of_active_election()` - Generates and sends tokens to all eligible voters
- `schedule_election_reminders()` - NEW: Schedules 5-min and 30-min reminder tasks using Celery ETA
- `send_election_starting_reminder()` - 5-minute pre-start notification
- `send_vote_confirmation_email()` - Congratulation email after successful vote
- `send_non_voters_reminder()` - 30-minute pre-end reminder ONLY for non-voters, grouped by level
- `send_custom_election_notification()` - Custom admin notifications
- Helper `_check_eligibility()` - Consistent eligibility logic

**Error Handling:**
- All Celery tasks have try/except blocks with meaningful logging
- Fallback to synchronous execution if async queueing fails
- Missing emails handled gracefully (user.email checks)
- Non-existent objects handled properly (User, Election, ElectionLevel)

### Code Cleanup & Consolidation (2025-12-07)

**Removed Unused Files:**
- `src/core/views.py` - Deprecated old API views (replaced by `views_ui.py` with Django session auth)
- `src/core/api_views.py` - Unused API viewsets and helpers (not registered in any URL patterns)
- `src/core/api_health.py` - Unused API health check endpoint
- `src/election/views_candidate.py` - Unused candidate API views (not exposed in URLs)
- `src/election/views_voting.py` - Unused election voting API views (not exposed in URLs)
- `src/election/serializers_voting.py` - Unused voting serializers
- `src/election/serializers_candidate.py` - Unused candidate serializers

**Consolidated View Structure:**
- `src/core/` now contains only:
  - `views_ui.py` - All Django session-based UI views (home, login, register, dashboard, profile edit, commissioner dashboard)
  - `views_commissioner.py` - All commissioner-specific JSON API endpoints
  - `serializers.py` - All core serializers (user, login, verification, password reset)
  
- `src/election/` now contains only:
  - `views.py` - Minimal API endpoints for vote submission and results (VoteView, ResultsView)
  - `views_ui.py` - All election UI views (elections list, vote form, results display)
  - `serializers.py` - All election serializers (vote validation, results)

**Profile Editing Enhancement:**
- Profile editing (email/gender) now allowed when:
  - **No elections are active** (unrestricted editing window)
  - **24 hours before an election starts** (pre-election editing window)
- Editing is **blocked** during active elections
- Updated `profile_edit_view()` to detect upcoming elections and display appropriate messages
- Enhanced template with context-aware alerts for all three states

**Bug Fixes:**
- Fixed `election_results` view annotation conflict: renamed `votes=Count('vote')` to `vote_total=Count('votes')` to avoid conflict with `Candidate.votes` related manager

**Documentation Updates:**
- Updated `docs/ARCHITECTURE.md` to reflect clean codebase structure
- Removed references to deprecated files (`api_views.py`, `api_health.py`)
- Updated `TESTING_GUIDE.md` with correct minimal API endpoints

### Documentation Reconciliation (2025-12-07)
- Documentation: Reconciled docs with code

2025-11-21
-----------
- Added Celery task support and configured `django-celery-beat`/`django-celery-results`.
- Implemented JWT-based API authentication using `djangorestframework-simplejwt`.

2025-10-23
-----------
- Initial conversion and sample data seeding (historical entries may exist in repo history).

Notes
-----
- Use this file when creating releases or pull requests that change behavior, migrations, public API endpoints, or deployment requirements.
