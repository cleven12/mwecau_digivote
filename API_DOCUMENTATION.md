# MWECAU Digital Voting System - API Documentation

## Base URL
```
Production: https://your-repl-name.repl.co
Development: http://localhost:5000
```

## Authentication
Most endpoints require JWT (JSON Web Token) authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## 1. AUTHENTICATION ENDPOINTS

### 1.1 Login
**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required  
**Description:** Authenticate user and receive JWT tokens

**Request Body:**
```json
{
  "registration_number": "REG-001",
  "password": "@2025"
}
```

**Success Response (200 OK):**
```json
{
  "refresh": "eyJhbGc...",
  "access": "eyJhbGc..."
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Invalid credentials"
}
```

### 1.2 Logout
**Endpoint:** `POST /api/auth/logout/`  
**Authentication:** Required  
**Description:** Blacklist refresh token to logout user

**Request Body:**
```json
{
  "refresh": "eyJhbGc..."
}
```

**Success Response (205 Reset Content):**
```json
{
  "message": "Successfully logged out"
}
```

### 1.3 Refresh Token
**Endpoint:** `POST /api/auth/refresh/`  
**Authentication:** Not required  
**Description:** Get new access token using refresh token

**Request Body:**
```json
{
  "refresh": "eyJhbGc..."
}
```

**Success Response (200 OK):**
```json
{
  "access": "eyJhbGc..."
}
```

### 1.4 Register New Account
**Endpoint:** `POST /api/auth/register/`  
**Authentication:** Not required  
**Description:** Check if registration number exists and get student details

**Request Body:**
```json
{
  "registration_number": "REG-001"
}
```

**Success Response (200 OK):**
```json
{
  "registration_number": "REG-001",
  "first_name": "Paul",
  "last_name": "Mbise",
  "email": null,
  "course": {
    "id": 1,
    "code": "BsChem",
    "name": "Bachelor of Science in Chemistry"
  }
}
```

### 1.5 Complete Registration
**Endpoint:** `POST /api/auth/complete-registration/`  
**Authentication:** Not required  
**Description:** Complete user registration with email and password

**Request Body:**
```json
{
  "registration_number": "REG-001",
  "email": "paul.mbise@university.edu",
  "password": "@2025",
  "password_confirm": "@2025",
  "state": 1,
  "course": 1
}
```

**Success Response (201 Created):**
```json
{
  "status": "success",
  "message": "Registration completed",
  "user": { ... },
  "tokens": {
    "refresh": "...",
    "access": "..."
  }
}
```

### 1.6 Forgot Password
**Endpoint:** `POST /api/auth/forgot-password/`  
**Authentication:** Not required  
**Description:** Request password reset (sends email)

**Request Body:**
```json
{
  "registration_number": "REG-001"
}
```

**Success Response (200 OK):**
```json
{
  "message": "Password reset email sent"
}
```

### 1.7 Verification Status
**Endpoint:** `GET /api/auth/verify/status/`  
**Authentication:** Required  
**Description:** Check if current user is verified

**Success Response (200 OK):**
```json
{
  "is_verified": true,
  "email": "user@example.com"
}
```

### 1.8 User Dashboard
**Endpoint:** `GET /api/auth/dashboard/`  
**Authentication:** Required  
**Description:** Get user dashboard data with active elections

**Success Response (200 OK):**
```json
{
  "user": {
    "id": "2",
    "registration_number": "REG-001",
    "email": "paul.mbise@university.edu",
    "first_name": "Paul",
    "last_name": "Mbise",
    "voter_id": "V1234567890",
    "is_verified": true,
    "role": "voter"
  },
  "active_elections": [ ... ]
}
```

### 1.9 Contact Commissioner
**Endpoint:** `POST /api/auth/contact-commissioner/`  
**Authentication:** Required  
**Description:** Send message to all commissioners

**Request Body:**
```json
{
  "message": "I need help with my voter token"
}
```

**Success Response (200 OK):**
```json
{
  "status": "success",
  "message": "Message sent to commissioners"
}
```

---

## 2. REFERENCE DATA ENDPOINTS

### 2.1 Get All States
**Endpoint:** `GET /api/states/`  
**Authentication:** Not required  
**Description:** Get list of all states/hostels

**Success Response (200 OK):**
```json
[
  {
    "id": 8,
    "name": "KIFUMBU"
  },
  {
    "id": 7,
    "name": "KWACHANGE"
  }
]
```

### 2.2 Get All Courses
**Endpoint:** `GET /api/courses/`  
**Authentication:** Not required  
**Description:** Get list of all available courses

**Success Response (200 OK):**
```json
[
  {
    "id": 51,
    "code": "BABusAdmin",
    "name": "Bachelor of Arts in Business Administration Management"
  },
  {
    "id": 52,
    "code": "BsCS",
    "name": "Bachelor of Science in Computer Science"
  }
]
```

---

## 3. ELECTION ENDPOINTS

### 3.1 List Active Elections
**Endpoint:** `GET /api/election/list/`  
**Authentication:** Required  
**Description:** Get all active elections with their levels

**Success Response (200 OK):**
```json
[
  {
    "id": 1,
    "title": "University Elections 2025",
    "description": "Annual university elections...",
    "start_date": "2025-10-22 08:40:15",
    "end_date": "2025-10-29 08:40:15",
    "is_active": true,
    "has_ended": false,
    "levels": [
      {
        "id": 1,
        "name": "University President",
        "code": "PRES-2025",
        "type": "president",
        "description": "University-wide presidential election",
        "course": null,
        "state": null
      },
      {
        "id": 2,
        "name": "KIFUMBU State Leader",
        "code": "STATE-KIFUMBU-2025",
        "type": "state",
        "description": "State leader election for KIFUMBU",
        "state": 8,
        "state_details": {
          "id": 8,
          "name": "KIFUMBU"
        }
      }
    ]
  }
]
```

### 3.2 Cast a Vote
**Endpoint:** `POST /api/election/vote/`  
**Authentication:** Required  
**Description:** Cast a vote using voter token

**Request Body:**
```json
{
  "voter_token": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": 5
}
```

**Success Response (201 Created):**
```json
{
  "message": "Vote successfully cast."
}
```

**Error Responses:**
```json
{
  "voter_token": ["Invalid or expired token"]
}

{
  "non_field_errors": ["Token already used"]
}

{
  "non_field_errors": ["Candidate not eligible for this election level"]
}
```

### 3.3 Get Election Results
**Endpoint:** `GET /api/election/results/<election_id>/`  
**Authentication:** Required  
**Description:** Get results for a specific election (only available to commissioners or after election ends)

**Success Response (200 OK):**
```json
[
  {
    "position_id": 1,
    "position_title": "University President",
    "total_votes_cast": 150,
    "candidates": [
      {
        "candidate_id": 1,
        "candidate_name": "John Doe",
        "candidate_image_url": "https://...",
        "vote_count": 85,
        "vote_percentage": 56.67
      },
      {
        "candidate_id": 2,
        "candidate_name": "Jane Smith",
        "candidate_image_url": null,
        "vote_count": 65,
        "vote_percentage": 43.33
      }
    ]
  }
]
```

**Error Response (403 Forbidden):**
```json
{
  "error": "Results are not available yet."
}
```

---

## 4. ADMIN ENDPOINTS (Commissioners Only)

### 4.1 User Management
**Endpoint:** `GET /api/users/`  
**Authentication:** Required (Commissioner role)  
**Description:** Get list of all users

**Query Parameters:**
- `role`: Filter by role (voter, candidate, class_leader, commissioner)
- `state`: Filter by state ID
- `course`: Filter by course ID
- `is_verified`: Filter by verification status (true/false)
- `search`: Search by email, registration_number, first_name, last_name

**Success Response (200 OK):**
```json
{
  "count": 77,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "1",
      "registration_number": "REG-001",
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "voter_id": "V1234567890",
      "role": "voter",
      "is_verified": true,
      "state": 1,
      "course": 1
    }
  ]
}
```

### 4.2 Get Current User Profile
**Endpoint:** `GET /api/users/me/`  
**Authentication:** Required  
**Description:** Get current logged-in user's profile

### 4.3 Update Profile
**Endpoint:** `PUT/PATCH /api/users/update-profile/`  
**Authentication:** Required  
**Description:** Update current user's profile

### 4.4 College Data Management
**Endpoint:** `GET/POST/PUT/PATCH/DELETE /api/college-data/`  
**Authentication:** Required (Class Leader or Commissioner)  
**Description:** Manage college data entries

### 4.5 Bulk Upload College Data
**Endpoint:** `POST /api/college-data/bulk-upload/`  
**Authentication:** Required (Class Leader or Commissioner)  
**Description:** Upload CSV file with student data

**Request:**
- Content-Type: multipart/form-data
- Field name: `file`
- CSV Format:
  ```
  registration_number,full_name,course_code,course_name
  REG-001,John Doe,BsCS,Bachelor of Science in Computer Science
  ```

**Success Response (201 Created):**
```json
{
  "status": "success",
  "message": "Upload completed",
  "students_added": 50,
  "students_updated": 10,
  "errors": []
}
```

---

## 5. EMAIL NOTIFICATIONS

The system automatically sends emails for the following events:

### 5.1 Account Verification
Sent when user account is verified by admin. Includes:
- Welcome message
- Account details (registration number, email, course, state, voter ID)
- Active election voter tokens (if any elections are active)

### 5.2 Election Activation
Sent when new election is activated. Includes:
- Election title and description
- Start and end dates
- Voter tokens for all eligible election levels

### 5.3 Vote Confirmation
Sent after successfully casting a vote. Includes:
- Election title
- Election level
- Vote timestamp

### 5.4 Password Reset
Sent when user requests password reset. Includes:
- Registration number
- New temporary password

### 5.5 Commissioner Contact
Sent to all commissioners when a user sends a contact message. Includes:
- Sender details
- Message content
- Reply-to email

**Note:** Email backend is currently configured for development (console output). For production, configure SMTP settings in `mw_es/settings.py`:

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
```

---

## 6. API TESTING WITH CURL

### Example: Complete Authentication Flow

1. **Get States and Courses**
```bash
curl -X GET http://localhost:5000/api/states/
curl -X GET http://localhost:5000/api/courses/
```

2. **Register New Account**
```bash
curl -X POST http://localhost:5000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"registration_number":"REG-001"}'
```

3. **Complete Registration**
```bash
curl -X POST http://localhost:5000/api/auth/complete-registration/ \
  -H "Content-Type: application/json" \
  -d '{
    "registration_number":"REG-001",
    "email":"user@example.com",
    "password":"SecurePass123",
    "password_confirm":"SecurePass123",
    "state":1,
    "course":1
  }'
```

4. **Login**
```bash
curl -X POST http://localhost:5000/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"registration_number":"REG-001","password":"@2025"}'
```

5. **Access Protected Endpoint**
```bash
curl -X GET http://localhost:5000/api/election/list/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

6. **Cast a Vote**
```bash
curl -X POST http://localhost:5000/api/election/vote/ \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "voter_token":"550e8400-e29b-41d4-a716-446655440000",
    "candidate_id":5
  }'
```

---

## 7. ERROR CODES

| Code | Description |
|------|-------------|
| 200 | OK - Request successful |
| 201 | Created - Resource created successfully |
| 204 | No Content - Successful deletion |
| 205 | Reset Content - Successful logout |
| 400 | Bad Request - Invalid data |
| 401 | Unauthorized - Authentication required or invalid credentials |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 500 | Internal Server Error - Server-side error |

---

## 8. API DOCUMENTATION TOOLS

### Swagger UI
Interactive API documentation available at:
```
http://localhost:5000/swagger/
```

### ReDoc
Alternative documentation interface:
```
http://localhost:5000/redoc/
```

### Django Admin Panel
Administrative interface for managing data:
```
http://localhost:5000/admin/
```

Default admin credentials (see TESTING_GUIDE.md):
- Email: admin@university.edu
- Password: @12345678

---

## 9. RATE LIMITING & BEST PRACTICES

1. **Token Expiry:**
   - Access tokens: 24 hours
   - Refresh tokens: 7 days

2. **Security Best Practices:**
   - Always use HTTPS in production
   - Store tokens securely (e.g., httpOnly cookies)
   - Never share voter tokens
   - Implement rate limiting on client side
   - Validate all user inputs

3. **Performance Tips:**
   - Use pagination for large datasets
   - Cache reference data (states, courses)
   - Batch requests when possible

---

## 10. SUPPORT

For technical issues or questions:
- Use the `/api/auth/contact-commissioner/` endpoint
- Check the TESTING_GUIDE.md for examples
- Review the ELECTION_BUSINESS_LOGIC.md for system behavior

**Developed by MWECAU ICT Department**
