# MWECAU Election System - Database Design Documentation

## Overview
This document outlines the database structure for a comprehensive election management system designed for educational institutions. The system manages user authentication, student registration, election processes, and voting mechanisms.

## Core Entities

### 1. Geographic states (states)
**Purpose:** Manages geographical/administrative divisions within the institution
- `state_id` (Primary Key, Auto-increment)
- `state_name` (Varchar 100, Unique) - Name of the state/state
- `created_timestamp` (DateTime) - Record creation time
- `modified_timestamp` (DateTime) - Last modification time

**Sample Data:** Kifumbu state

### 2. Academic Programs (courses)
**Purpose:** Stores information about academic courses and programs
- `program_id` (Primary Key, Auto-increment)
- `program_name` (Varchar 100) - Full name of the academic program
- `program_code` (Varchar 20, Unique) - Short identifier (e.g., CS100, CS101)
- `created_timestamp` (DateTime)
- `modified_timestamp` (DateTime)

**Sample Data:** Computer Science programs with codes CS100 and CS101

### 3. System Users (users)
**Purpose:** Central user management table storing all system participants
- `user_id` (Primary Key, Auto-increment)
- `unique_identifier` (Varchar 20, Unique) - Institution-specific ID format
- `email_address` (Varchar 254, Unique) - Contact email
- `ballot_id` (Varchar 36, Unique, Nullable) - Voting identification token
- `first_name` (Varchar 150)
- `last_name` (Varchar 150)
- `gender_type` (Varchar 10, Nullable) - male/female/other
- `state_ref` (Foreign Key to Geographic states)
- `program_ref` (Foreign Key to Academic Programs)
- `user_role` (Varchar 20) - voter/candidate/coordinator/administrator
- `verification_status` (Boolean) - Account verification flag
- `verification_date` (DateTime, Nullable)
- `access_credentials` (Varchar 128) - Encrypted password
- `account_status` (Boolean) - Active/inactive flag
- `privilege_level` (Boolean) - Administrative access flag
- `staff_designation` (Boolean) - Staff member flag
- `registration_date` (DateTime)
- `last_access_time` (DateTime, Nullable)
- `last_access_location` (Varchar 39, Nullable) - IP address tracking

**Key Roles:**
- **Administrator:** Full system access with elevated privileges
- **Coordinator:** stateal/program-specific management rights
- **Voter:** Standard participant with voting rights
- **Candidate:** Eligible for election positions

### 4. Student Registry (college_data)
**Purpose:** Pre-registration database for eligible students
- `registry_id` (Primary Key, Auto-increment)
- `student_identifier` (Varchar 20, Unique) - Matches user unique_identifier
- `first_name` (Varchar 50)
- `last_name` (Varchar 50)
- `contact_email` (Varchar 254, Unique)
- `voting_token` (Varchar 36, Unique, Nullable)
- `program_ref` (Foreign Key to Academic Programs)
- `uploaded_by` (Foreign Key to System Users) - Who added this record
- `processing_status` (Boolean) - Whether record has been used for account creation
- `record_state` (Varchar 20) - pending/processed/failed
- `upload_timestamp` (DateTime)

## Election Management Entities

### 5. Election Events (election_election)
**Purpose:** Manages election cycles and campaigns
- `election_id` (Primary Key, Auto-increment)
- `election_title` (Varchar 100) - Name of the election
- `description` (Text) - Detailed election information
- `start_datetime` (DateTime) - Election opening time
- `end_datetime` (DateTime) - Election closing time
- `active_status` (Boolean) - Currently running flag
- `completion_status` (Boolean) - Election finished flag
- `created_timestamp` (DateTime)
- `modified_timestamp` (DateTime)

**Sample Data:** "Student Election 2025" running from July 31 to August 29, 2025

### 6. Election Categories (election_electionlevel)
**Purpose:** Defines different levels or types of elections
- `category_id` (Primary Key, Auto-increment)
- `category_name` (Varchar 50) - Level description
- `category_code` (Varchar 20, Unique) - Short identifier
- `category_description` (Text) - Detailed explanation

### 7. Voting Positions (election_position)
**Purpose:** Defines available positions in elections
- `position_id` (Primary Key, Auto-increment)
- `position_title` (Varchar 100) - Name of the position
- `position_description` (Text) - Role responsibilities
- `gender_requirement` (Varchar 10) - Gender restrictions if any
- `program_restriction` (Foreign Key to Academic Programs, Nullable)
- `state_restriction` (Foreign Key to Geographic states, Nullable)
- `category_ref` (Foreign Key to Election Categories)

### 8. Election Candidates (election_candidate)
**Purpose:** Stores candidate information for specific positions
- `candidate_id` (Primary Key, Auto-increment)
- `candidate_ref` (Foreign Key to System Users)
- `election_ref` (Foreign Key to Election Events)
- `position_ref` (Foreign Key to Voting Positions)
- `biography` (Text) - Candidate background
- `platform` (Text) - Campaign promises/agenda
- `vote_tally` (Integer, Unsigned) - Current vote count

### 9. Voting Tokens (election_votertoken)
**Purpose:** Manages secure voting access tokens
- `token_id` (Primary Key, Auto-increment)
- `voter_ref` (Foreign Key to System Users)
- `election_ref` (Foreign Key to Election Events)
- `access_token` (UUID, Unique) - Cryptographic voting token
- `usage_status` (Boolean) - Whether token has been used
- `issue_timestamp` (DateTime) - When token was generated
- `usage_timestamp` (DateTime, Nullable) - When token was consumed

### 10. Vote Records (election_vote)
**Purpose:** Stores actual voting records
- `vote_id` (Primary Key, Auto-increment)
- `candidate_ref` (Foreign Key to Election Candidates)
- `election_ref` (Foreign Key to Election Events)
- `token_ref` (Foreign Key to Voting Tokens)
- `cast_timestamp` (DateTime) - When vote was recorded

## System Infrastructure Tables

### 11. Access Permissions (auth_permission)
**Purpose:** Defines granular system permissions
- Standard permission management with 68 predefined permissions
- Covers create, read, update, delete operations for all entities

### 12. User Groups (auth_group)
**Purpose:** Role-based access control groupings
- Currently unused but available for future role hierarchies

### 13. Content Classification (server_content_type)
**Purpose:** System metadata for entity type management
- Maps each database table to its corresponding system module

### 14. Session Management (server_session)
**Purpose:** Handles user session persistence and security
- Secure session token storage with expiration tracking

### 15. Token Security (token_blacklist_outstandingtoken, token_blacklist_blacklistedtoken)
**Purpose:** Advanced authentication token management
- Outstanding tokens: Valid authentication tokens in circulation
- Blacklisted tokens: Revoked or expired tokens for security

### 16. System Audit (server_admin_log)
**Purpose:** Tracks administrative actions and changes
- Comprehensive audit trail of system modifications

### 17. Database Evolution (server_migrations)
**Purpose:** Manages database schema versioning
- Tracks all structural changes and updates to the database

## Relationships and Data Flow

### Primary Relationships:
1. **Users ↔ states:** One state contains multiple users
2. **Users ↔ Programs:** One program has multiple enrolled users
3. **Student Registry ↔ Programs:** Pre-registration data linked to academic programs
4. **Voting Tokens ↔ Users:** One-to-many relationship for election participation
5. **Candidates ↔ Positions:** Many-to-many through election context
6. **Votes ↔ Candidates:** Direct voting relationship with token validation

### Security Architecture:
- **Token-Based Voting:** Each eligible voter receives unique cryptographic tokens
- **Audit Trail:** Complete logging of all administrative actions
- **Session Security:** Encrypted session management with IP tracking
- **Permission Matrix:** Granular access control for different user roles

## Data Privacy and Security Features

### Anonymization Measures:
- Voting tokens are cryptographically separate from user identities
- Vote records link to tokens, not directly to users
- IP address logging for security without personal identification

### Access Control:
- Multi-tier permission system (68 distinct permissions)
- Role-based access (voter, candidate, coordinator, administrator)
- Geographic and program-based access restrictions

### Data Integrity:
- Unique constraints on all critical identifiers
- Foreign key relationships maintain referential integrity
- Timestamp tracking for all major operations