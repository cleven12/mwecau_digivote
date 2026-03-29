# Email Notification & Token Management System

This document describes the comprehensive email notification and voting token management system implemented in the university election platform.

## Overview

The system automatically manages voting tokens and sends timely email notifications to voters throughout the election lifecycle. All processes are triggered by signals and executed as Celery tasks for optimal performance.

---

## Token Management

### Token Generation Workflow

**When are tokens created?**

1. **User Verification** (Signal: `core.signals.generate_tokens_on_verification`)
   - Triggered when user transitions from `is_verified=False` to `is_verified=True`
   - Generates tokens for ALL active elections
   - Only generates tokens for election levels the user is eligible for

2. **Election Activation** (Signal: `election.signals.handle_election_activation`)
   - Triggered when election transitions from `is_active=False` to `is_active=True`
   - Creates tokens for all already-verified eligible voters
   - Sends notification emails with tokens

3. **Admin Panel User Creation**
   - Voter ID auto-generated when user is created
   - Tokens generated when admin verifies the user (via signal)

### Token Eligibility

Eligibility is determined by the **election level type** and **user's state/course assignment**:

| Level Type | Eligibility Criteria |
|-----------|------------------|
| **President** | All verified voters |
| **Course** | User must have `course` assigned AND match level's course |
| **State** | User must have `state` assigned AND match level's state |

**Code:** See `_check_eligibility()` helper in `src/core/tasks.py` and `src/election/tasks.py`

### Token Properties

- **Format:** UUID4 (unique per user, election, and level)
- **Expiry:** Election end date
- **Usage:** One vote per token (marked as used after voting)
- **Storage:** `election.models.VoterToken`

---

## Email Notification Workflow

### 1. User Registration & Verification

**Trigger:** User verified (admin marks as verified or email verification completes)

**Signal:** `core.signals.generate_tokens_on_verification`

**Task:** `core.tasks.send_verification_email(user_id)`

**Email Content:**
```
Subject: MWECAU DigiVote - Registration Confirmed

Dear [Name],

Welcome to the MWECAU DigiVote!

Your account has been verified. You are now registered as a voter.
Your Voter ID: [UUID4]

[If active elections exist:]
You have been assigned to the following active elections:

[Election Title 1]:
  - President Level: [token]
  - Course Level: [token]
  - State Level: [token]

[Election Title 2]:
  - President Level: [token]

Keep your voter tokens secure and do not share them.
Vote at the election platform during the voting period.

Regards,
MWECAU Election Commission
```

---

### 2. Election Activation

**Trigger:** Election marked as active (admin activates)

**Signal:** `election.signals.handle_election_activation`

**Tasks Triggered:**
1. `election.tasks.notify_voters_of_active_election(election_id)` - Send tokens
2. `election.tasks.schedule_election_reminders(election_id)` - Schedule reminders

**Email Content (notify_voters):**
```
Subject: MWECAU DigiVote - New Election: [Title]

Dear [Name],

A new election is now active: [Title]
Description: [description]
Start Date: [date/time]
End Date: [date/time]

Your Voter Tokens:
- President Level: [token]
- [Course Name] Level: [token]
- [State Name] Level: [token]

Vote at the election platform during the voting period.
Note: Keep your voter tokens secure and do not share them.
Each token can only be used once.

Regards,
MWECAU Election Commission
```

---

### 3. Pre-Election Reminders

#### 5-Minute Pre-Start Reminder

**Trigger:** Automatically scheduled when election is activated

**Scheduled Time:** 5 minutes before `election.start_date`

**Task:** `election.tasks.send_election_starting_reminder(election_id)`

**Recipients:** All voters with valid (unused) tokens

**Email Content:**
```
Subject: REMINDER: [Election Title] - Election Starting Soon!

Dear [Name],

This is a reminder that the following election will start in approximately 5 minutes:

Election: [Title]
Start Time: [date/time]
End Time: [date/time]

Make sure you are ready to cast your vote!
Log in to the election platform to participate.

Regards,
MWECAU Election Commission
```

#### 30-Minute Pre-End Reminder

**Trigger:** Automatically scheduled when election is activated

**Scheduled Time:** 30 minutes before `election.end_date`

**Task:** `election.tasks.send_non_voters_reminder(election_id)`

**Recipients:** ONLY voters who have NOT voted (have unused tokens)

**Email Content (IMPORTANT - Includes level details):**
```
Subject: URGENT: [Election Title] - Voting Ending Soon!

Dear [Name],

This is an URGENT reminder that the following election will end in approximately 30 minutes:

Election: [Title]
End Time: [date/time]

You have not voted yet for these levels:
  - President Level
  - [Course Name] Level
  - [State Name] Level

This is your LAST CHANCE to have your voice heard!
Please log in to the election platform immediately to cast your vote.

Your voter tokens are available in your dashboard.
Each token can only be used once.

Regards,
MWECAU Election Commission
```

**Note:** The reminder lists ONLY the election levels the user hasn't voted in (has unused tokens for).

---

### 4. Post-Vote Confirmation

**Trigger:** User successfully votes (via `election.views.VoteView`)

**Task:** `election.tasks.send_vote_confirmation_email(user_id, election_id, level_id)`

**Email Content:**
```
Subject: MWECAU DigiVote - Vote Confirmation: [Title]

Dear [Name],

Thank you for participating in the [Election Title]!

Your vote for the [Level Name] level has been successfully recorded.
Time: [date/time]

Your vote is secure, anonymous, and counts!
Results will be available after the election ends.

Regards,
MWECAU Election Commission
```

---

### 5. Custom Admin Notifications

**Trigger:** Admin sends custom notification from commissioner dashboard

**Task:** `election.tasks.send_custom_election_notification(election_id, custom_message)`

**Recipients:** All voters with tokens for the election

**Email Content:**
```
Subject: Election Notification - [Election Title]

Dear [Name],

[Custom message from admin]

Election: [Title]
Start Date: [date]
End Date: [date]

Regards,
MWECAU Election Commission
```

---

## Implementation Details

### Signal Handlers

#### Core Signals (src/core/signals.py)

```python
@receiver(post_save, sender=User)
def generate_voter_id_on_create(sender, instance, created, **kwargs):
    """Generate voter ID when user is created"""
    # Applies to: self-registered users, admin-created users

@receiver(post_save, sender=User)
def generate_tokens_on_verification(sender, instance, created, **kwargs):
    """Generate tokens when user is verified"""
    # Listens for: is_verified transition from False → True
    # Triggers: send_verification_email async task
```

#### Election Signals (src/election/signals.py)

```python
@receiver(post_save, sender=Election)
def handle_election_activation(sender, instance, created, **kwargs):
    """Handle election activation"""
    # Listens for: is_active transition from False → True
    # Triggers:
    #   1. notify_voters_of_active_election (send tokens)
    #   2. schedule_election_reminders (schedule 5-min & 30-min reminders)
```

### Celery Tasks

#### Token Management

| Task | Location | Purpose | Triggered By |
|------|----------|---------|--------------|
| `send_verification_email` | `core.tasks` | Generate tokens for active elections, send welcome email | User verification signal |
| `notify_voters_of_active_election` | `election.tasks` | Generate tokens for new election, send notifications | Election activation signal |
| `schedule_election_reminders` | `election.tasks` | Schedule reminder tasks via Celery ETA | Election activation signal |

#### Email Notifications

| Task | Queue | Purpose | Timing |
|------|-------|---------|--------|
| `send_election_starting_reminder` | email_queue | 5-min pre-start reminder | Scheduled via ETA |
| `send_vote_confirmation_email` | email_queue | Post-vote thank you | Immediately after vote |
| `send_non_voters_reminder` | email_queue | 30-min pre-end reminder | Scheduled via ETA |
| `send_custom_election_notification` | email_queue | Admin custom messages | On-demand |

---

## Workflow Diagrams

### User Registration Flow

```
User Created (admin or self-registered)
    ↓
Signal: post_save User
    ↓
generate_voter_id_on_create()
    ├─ Generate voter_id if missing
    └─ Save to database
    ↓
[Later] User Verified (admin or email confirmation)
    ↓
Signal: post_save User (is_verified: False → True)
    ↓
generate_tokens_on_verification()
    ├─ Query active elections
    ├─ For each election level:
    │  └─ Check eligibility
    │     └─ If eligible: create VoterToken
    └─ Trigger: send_verification_email (async)
        ├─ Generate tokens for each active election
        └─ Send email with tokens
```

### Election Activation Flow

```
Election Marked Active
    ↓
Signal: post_save Election (is_active: False → True)
    ↓
handle_election_activation()
    ├─ Trigger: notify_voters_of_active_election (async)
    │  ├─ Query all verified voters
    │  ├─ For each voter:
    │  │  ├─ Check eligibility for each level
    │  │  ├─ Create tokens if eligible
    │  │  └─ Send email with tokens
    │  └─ Return
    │
    └─ Trigger: schedule_election_reminders (async)
       ├─ Calculate 5-min reminder time
       ├─ Calculate 30-min reminder time
       ├─ Schedule: send_election_starting_reminder (ETA)
       └─ Schedule: send_non_voters_reminder (ETA)
```

### Voting & End-of-Election Flow

```
Voter Submits Vote
    ↓
VoteView.post()
    ├─ Validate token & candidate
    ├─ Create Vote record
    ├─ Mark token as used
    └─ Trigger: send_vote_confirmation_email (async)
       └─ Send congratulation email

[Before Election Ends - 30 Minutes]
    ↓
Scheduled: send_non_voters_reminder
    ├─ Query voters with unused tokens
    ├─ Group by user
    ├─ For each user without votes:
    │  └─ Send reminder with list of levels not voted
    └─ Return
```

---

## Configuration

### Email Backend

The system uses Django's email backend configured in `src/mw_es/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.tutamail.com'  # or your mail server
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'
```

### Celery Queues

Emails are sent via the dedicated `email_queue`:

```python
# All email tasks use: @shared_task(queue='email_queue')
# To process emails:
celery -A mw_es worker -Q email_queue --loglevel=info
```

### Beat Schedule

Reminders are scheduled automatically when election is activated. No manual beat schedule needed.

---

## Error Handling & Logging

All tasks include comprehensive error handling:

```python
try:
    # Task logic
    send_mail(...)
    print(f"Success: Email sent to {user.email}")
except Exception as e:
    print(f"Error: Failed to send email: {e}")
```

**Console output samples:**
```
Verification email sent to user@example.com
Election notification complete: 45 sent, 2 failed
Non-voter reminder sent for election 1: 12 sent, 1 failed
Vote confirmation sent to user@example.com for election 1, level 2
```

---

## Testing the System

### Test User Verification Email

```bash
# Create a test user
python manage.py shell

from core.models import User
from django.utils import timezone

user = User.objects.create_user(
    registration_number='TEST/2024/001',
    password='testpass',
    first_name='Test',
    last_name='User',
    email='test@example.com',
    is_verified=True  # This triggers the signal
)
# Email should be sent automatically
```

### Test Election Activation Emails

```bash
# In admin panel or shell:
from election.models import Election

election = Election.objects.get(id=1)
election.is_active = True
election.save()  # This triggers the signal

# Emails and scheduled reminders should be sent/scheduled
```

### Monitor Celery Tasks

```bash
# In separate terminal:
celery -A mw_es worker -Q email_queue -l info

# Watch email queue:
celery -A mw_es inspect active
```

---

## Troubleshooting

### Emails Not Sending

1. **Check email configuration** in `settings.py`
2. **Verify Celery worker is running** for `email_queue`
3. **Check Django logs** for task errors
4. **Test SMTP credentials** manually

### Tokens Not Generated

1. **Verify user is marked as verified** (`is_verified=True`)
2. **Check election is marked active** (`is_active=True`)
3. **Verify user eligibility** (state/course match)
4. **Check database** for VoterToken records

### Reminders Not Scheduled

1. **Verify Celery Beat is running** (if using Beat scheduler)
2. **Check election activation** triggered signal
3. **Verify `schedule_election_reminders` task** executed successfully
4. **Check Celery tasks** are queued correctly

---

## Summary

The email and token system provides:

 - **Automatic token generation** - No manual token creation needed
 - **Timely notifications** - Users informed at every stage
 - **Eligibility-based tokens** - Only eligible voters get tokens
 - **Smart reminders** - Non-voters reminded about unused levels
 - **Reliable delivery** - Async tasks with error handling
 - **Audit trail** - Logs of all sent emails and token creation
 - **Admin control** - Ability to send custom notifications

---

For more information, see:
- `CHANGELOG.md` - Detailed feature changelog
- `CODEBASE_STRUCTURE.md` - Application architecture
- `src/core/signals.py` - Core user signals
- `src/election/signals.py` - Election signals
- `src/core/tasks.py` - Core email tasks
- `src/election/tasks.py` - Election email tasks
