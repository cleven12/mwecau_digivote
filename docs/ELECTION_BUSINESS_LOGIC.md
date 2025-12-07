# MWECAU Digital Voting System - Business Logic (code-verified)

This document summarizes the implemented election business logic. It is derived from the code in `src/election/` and related modules.

VoterToken (summary)
- The system issues a per-user, per-election, per-election-level token implemented in the `VoterToken` model.
- Tokens are UUID4 values and have `is_used` and `expiry_date` fields. Typical lifecycle:
  1. Token created when an election is activated for eligible users.
 2. Token may be emailed to users (via Celery task) or inspected in the DB for testing.
 3. Token used once when a vote is cast; it is then marked used and cannot be reused.

Token generation
- Implemented by the `notify_voters_of_active_election` Celery task (`src/election/tasks.py`).
- Eligibility rules (from code):
  - President level: all verified users with a `voter_id` are eligible.
  - Course level: users whose `user.course_id` matches the level's `course_id`.
  - State level: users whose `user.state_id` matches the level's `state_id`.
- The task creates tokens with `expiry_date` set to the election `end_date` and avoids creating duplicates (`get_or_create`).

Vote casting (API)
- Endpoint (code): `POST /elections/api/<election_id>/submit/` (`VoteView` in `src/election/views.py`).
- Authentication: requires an authenticated user (JWT or session per `REST_FRAMEWORK` settings).
- Payload (JSON):
  - `token` (UUID string) — the voter token
  - `candidate_id` (integer) — the candidate to vote for
- Validation (implemented in `VoteCreateSerializer`, `src/election/serializers.py`):
  1. The token UUID maps to a `VoterToken` record.
  2. The token is valid (not used and not expired).
  3. The token's election is currently ongoing (`Election.is_ongoing()`).
  4. The candidate exists and belongs to the same election and election level as the token.
- On success: a `Vote` record is created, the token is marked used, and the code calls the vote confirmation helper. The helper is defined as a Celery task but may be invoked synchronously if no worker is running.

Vote model behavior
- When a `Vote` is saved the model auto-populates `election`, `election_level`, and `voter` from the token (see `Vote.save()` logic). Validation ensures that the vote's election and level match the token and candidate.

Results aggregation (API)
- Endpoint (code): `GET /elections/api/<election_id>/results/` (`ResultsView`).
- Access control: commissioners and staff can view results anytime; regular users can view results only after the election has ended (`election.has_ended`).
- Aggregation logic: for each level and each position in the level the view aggregates votes per candidate and computes percentages. The view returns a list of positions with candidate counts and percentages.

Concurrency & integrity
- Token single-use is enforced by `is_used` and by validation in serializers and model save logic.
- Vote creation and token marking are performed in the view; consider wrapping both in an atomic transaction if you harden against race conditions further.

Emailing and Celery notes
- Celery tasks for notifications and confirmations are declared in `src/election/tasks.py` and the project settings include `django-celery-beat` and `django-celery-results` with a DB broker by default.
- Many task helpers (e.g., `send_vote_confirmation_email`) are invoked as functions in the code; to execute them asynchronously run a Celery worker and `celery beat`.

Testing tips
- To get tokens for testing query the `voter_tokens` table or use the `notify_voters_of_active_election` task in local dev (or invoke the task function directly).
- For manual tests: cast a vote with the `token` and `candidate_id` payload at `POST /elections/api/<id>/submit/`, then confirm `VoterToken.is_used` and check `Vote` entries.

Where to read the code
- Token generation and notifications: `src/election/tasks.py`
- Vote endpoint and results endpoint: `src/election/views.py`
- Serializers and validation: `src/election/serializers.py`
- Models: `src/election/models.py`
# MWECAU Digital Voting System - Business Logic Documentation

## Overview
This document outlines the complete business logic for the three-level election system with a partial blockchain token architecture.

## Partial Blockchain Token System

### VoterToken Architecture
The system implements a "partial blockchain" approach through the VoterToken model:

**Key Characteristics:**
- **Immutability**: Once a token is marked as `is_used=True`, it cannot be reused
- **Uniqueness**: Database constraint `unique_together = ['user', 'election', 'election_level']` ensures one token per user per election per level
- **Cryptographic Security**: Each token uses UUID4 for unpredictable, unique identifiers
- **Audit Trail**: Tracks `created_at` and `used_at` timestamps for complete voting history
- **Expiration**: Tokens expire at election end_date to prevent voting outside election period

**Database Schema:**
```python
VoterToken:
  - user (FK to User)
  - election (FK to Election)
  - election_level (FK to ElectionLevel)
  - token (UUID, unique=True)
  - is_used (Boolean, default=False)
  - expiry_date (DateTime)
  - created_at (DateTime, auto)
  - used_at (DateTime, nullable)
```

## Three-Level Election System

### 1. President Level
**Eligibility**: All verified voters with a voter_id
**Filtering Logic**: No filtering - university-wide election

```python
# From election/tasks.py line 20
if level.type == ElectionLevel.TYPE_PRESIDENT:
    # All verified voters get a token
    token, _ = VoterToken.objects.get_or_create(
        user=user,
        election=election,
        election_level=level,
        defaults={'token': uuid.uuid4(), 'expiry_date': election.end_date}
    )
```

**Model Constraints** (from election/models.py line 59):
```python
elif self.type == self.TYPE_PRESIDENT:
    if self.course or self.state:
        raise ValidationError("President level should not have a course or state assigned.")
```

### 2. Course Level
**Eligibility**: Only voters whose `user.course` matches `election_level.course`
**Filtering Logic**: Course-specific elections

```python
# From election/tasks.py line 21
elif level.type == ElectionLevel.TYPE_COURSE and user.course and level.course == user.course:
    # Only matching course voters get tokens
    token, _ = VoterToken.objects.get_or_create(...)
```

**Model Constraints** (from election/models.py line 49):
```python
if self.type == self.TYPE_COURSE:
    if not self.course:
        raise ValidationError("Course level must have a specific course assigned.")
    if self.state:
        raise ValidationError("Course level should not have a state assigned.")
```

### 3. State Level
**Eligibility**: Only voters whose `user.state` matches `election_level.state`
**Filtering Logic**: State/region-specific elections

```python
# From election/tasks.py line 22
elif level.type == ElectionLevel.TYPE_STATE and user.state and level.state == user.state:
    # Only matching state voters get tokens
    token, _ = VoterToken.objects.get_or_create(...)
```

**Model Constraints** (from election/models.py line 54):
```python
elif self.type == self.TYPE_STATE:
    if not self.state:
        raise ValidationError("State level must have a specific state assigned.")
    if self.course:
        raise ValidationError("State level should not have a course assigned.")
```

## Voting Flow

### Token Generation Process
**Trigger**: When an election is activated (via `notify_voters_of_active_election` task)

**Steps**:
1. Retrieve all verified users with voter_id
2. For each user, iterate through all election levels
3. Check eligibility based on level type (president/course/state)
4. Generate or retrieve existing token for eligible users
5. Send email with all tokens user is eligible for

### Vote Casting Process

**API Endpoint**: `POST /api/election/vote/`

**Request Payload**:
```json
{
  "token": "uuid-string",
  "candidate_id": 123
}
```

**Validation Chain** (from election/serializers.py VoteCreateSerializer):

1. **Token Validation**:
   - Token UUID exists in database
   - Token is not expired (`expiry_date > now`)
   - Token is not used (`is_used = False`)

2. **Election Validation**:
   - Associated election is currently ongoing (`is_active=True` and within date range)

3. **Candidate Validation**:
   - Candidate exists
   - Candidate belongs to the same election as token
   - Candidate's position level matches token's election level

4. **Vote Creation**:
   - Create Vote record with token and candidate
   - Vote.save() auto-populates election, election_level, voter from token
   - Mark token as used (`token.mark_as_used()`)
   - Send confirmation email

**Vote Model Auto-Population** (from election/models.py line 262):
```python
if self.token:
    self.election = self.token.election
    self.election_level = self.token.election_level
    self.voter = self.token.user
```

This ensures vote integrity and links the vote to the correct election context.

### Data Integrity Safeguards

**Vote Model Validation** (from election/models.py line 248):
```python
def save(self, *args, **kwargs):
    if self.candidate and self.election != self.candidate.election:
        raise ValidationError("Vote election must match candidate's election.")
    
    if self.candidate and self.election_level != self.candidate.position.election_level:
        raise ValidationError("Vote level must match candidate's position level.")
    
    if self.token and self.election != self.token.election:
        raise ValidationError("Vote election must match the token's election.")
    
    if self.token and self.election_level != self.token.election_level:
        raise ValidationError("Vote level must match the token's election level.")
```

## Results Calculation

**API Endpoint**: `GET /api/election/results/<election_id>/`

**Access Control**:
- Commissioners can view anytime
- Staff can view anytime
- Regular users can view only after `election.has_ended = True`

**Aggregation Logic** (from election/views.py ResultsView):

1. Retrieve all election levels for the election
2. For each level, get all positions
3. For each position, aggregate votes by candidate:
   ```python
   Vote.objects.filter(
       election=election,
       election_level=level,
       candidate__position=position
   ).values('candidate').annotate(vote_count=Count('candidate'))
   ```
4. Calculate vote percentages per candidate
5. Return structured results grouped by position

**Response Structure**:
```json
[
  {
    "position_id": 1,
    "position_title": "President",
    "total_votes_cast": 100,
    "candidates": [
      {
        "candidate_id": 1,
        "candidate_name": "John Doe",
        "candidate_image_url": "http://...",
        "vote_count": 60,
        "vote_percentage": 60.0
      },
      {
        "candidate_id": 2,
        "candidate_name": "Jane Smith",
        "vote_count": 40,
        "vote_percentage": 40.0
      }
    ]
  }
]
```

## Security Features

### Vote Anonymity
- Votes are linked to tokens, not directly to users
- While the Vote model has a `voter` field (for admin oversight), the token acts as the primary identifier
- Results only show aggregated counts, never individual voter choices

### Token Security
- UUID4 provides 128-bit randomness (2^122 possible values)
- Tokens are single-use and expire with the election
- Database unique constraint prevents duplicate token usage
- Token validation happens in serializer before any database writes

### Race Condition Prevention
- The `is_used` flag on VoterToken prevents concurrent usage
- Token is marked used immediately after vote creation
- Database transaction ensures atomicity of vote creation + token marking

### Access Control
- All voting endpoints require authentication (`IsAuthenticated`)
- Results have role-based access (commissioners/staff/ended elections)
- Token generation restricted to verified users with voter_id

## Email Notifications

### Token Distribution Email
**Sent**: When election is activated
**Recipients**: All eligible verified voters
**Content**: Election details + all tokens user is eligible for (separated by level)

### Vote Confirmation Email
**Sent**: After successful vote casting
**Recipients**: The voter
**Content**: Election title, level voted in, timestamp

## Database Indexes

Optimized for query performance:

```python
VoterToken:
  - Index on 'token' (for fast lookup during voting)
  - Index on ['election', 'election_level'] (for token generation)
  - Index on 'is_used' (for filtering unused tokens)
  - Index on 'expiry_date' (for expiry checks)

Vote:
  - Index on 'token' (unique)
  - Index on 'candidate' (for vote counting)
  - Index on ['election', 'election_level'] (for results aggregation)
  - Index on 'timestamp' (for audit trails)

ElectionLevel:
  - Index on 'type', 'code', 'course', 'state' (for eligibility filtering)
```

## Critical Business Rules

1. **One Vote Per Level**: The `unique_together` constraint on VoterToken ensures one token per user per election per level
2. **Level Isolation**: President, Course, and State elections are completely isolated - votes cannot cross levels
3. **No Revoting**: Once a token is used, it cannot be reused (immutable)
4. **Time Boundaries**: Tokens expire with elections, preventing votes outside the voting period
5. **Eligibility Enforcement**: Tokens are only generated for eligible users based on level type
6. **Data Integrity**: Vote model validates all relationships before saving

## API Endpoints Summary

### Core Endpoints
- `GET /api/election/list/` - List active elections with levels
- `POST /api/election/vote/` - Cast a vote using a token
- `GET /api/election/results/<id>/` - View election results

### Supporting Endpoints
- `GET /api/states/` - List all states (for registration)
- `GET /api/courses/` - List all courses (for registration)

