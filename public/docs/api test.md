# MWECAU Election Platform: Core App API Testing Plan

## Base URL
`http://localhost:8000`

## Endpoints
### 1. Register (`POST /api/auth/register/`)
- **Description**: Validates a student's registration number against `CollegeData`.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/register/`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003"
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "first_name": "Neema",
      "last_name": "John",
      "course": 1
    }
    ```
- **Error Cases**:
  - Invalid registration number:
    ```json
    {
      "registration_number": "T/DEG/2020/9999"
    }
    ```
    - Status: 404 Not Found
    - Body: `{"error": "Registration number not found"}`
  - Already registered:
    ```json
    {
      "registration_number": "T/ADMIN/2020/0002"
    }
    ```
    - Status: 400 Bad Request
    - Body: `{"error": "Registration number already registered"}`
- **Verification**:
  - Check response matches `CollegeData` for `T/DEG/2020/0003`.

### 2. Complete Registration (`POST /api/auth/complete-registration/`)
- **Description**: Completes user registration with email, password, state, and course.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/complete-registration/`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "state": 1,
      "email": "neema.john@example.com",
      "password": "securepass123",
      "course_id": 1
    }
    ```
- **Expected Response**:
  - Status: 201 Created
  - Body:
    ```json
    {
      "message": "Registration successful, verification email sent",
      "voter_id": "<generated-voter-id>",
      "voter_tokens": [
        {
          "election_title": "Student Election 2025",
          "token": "<generated-token>"
        }
      ]
    }
    ```
- **Error Cases**:
  - Missing fields:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "email": "neema.john@example.com"
    }
    ```
    - Status: 400 Bad Request
    - Body: `{"error": "All fields are required"}`
  - Email already used:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "state": 1,
      "email": "admin@mail.com",
      "password": "securepass123",
      "course_id": 1
    }
    ```
    - Status: 400 Bad Request
    - Body: `{"error": "Email already registered"}`
- **Verification**:
  - Check Celery logs for `send_verification_email` task.
  - Verify email sent to `neema.john@example.com` with voter token.
  - Check `User` created in MySQL (`SELECT * from apps.core _user WHERE registration_number='T/DEG/2020/0003';`).

### 3. Login (`POST /api/auth/login/`)
- **Description**: Authenticates user and returns JWT tokens.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/login/`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "password": "securepass123"
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "refresh": "<refresh-token>",
      "access": "<access-token>"
    }
    ```
- **Error Cases**:
  - Invalid credentials:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "password": "wrongpass"
    }
    ```
    - Status: 401 Unauthorized
    - Body: `{"error": "Invalid registration number or password"}`
- **Verification**:
  - Save `access` and `refresh` tokens for authenticated requests.
  - Test with commissioner: `{"registration_number": "T/ADMIN/2020/0002", "password": "adminpass"}`.

### 4. Logout (`POST /api/auth/logout/`)
- **Description**: Blacklists refresh token to log out user.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/logout/`
  - Headers: `Authorization: Bearer <access-token>`, `Content-Type: application/json`
  - Body:
    ```json
    {
      "refresh": "<refresh-token>"
    }
    ```
- **Expected Response**:
  - Status: 205 Reset Content
  - Body:
    ```json
    {
      "message": "Successfully logged out"
    }
    ```
- **Error Cases**:
  - Missing refresh token:
    ```json
    {}
    ```
    - Status: 400 Bad Request
    - Body: `{"error": "Refresh token is required"}`
- **Verification**:
  - Check `rest_framework_simplejwt_tokenblacklist_blacklistedtoken` table in MySQL for blacklisted token.

### 5. Refresh Token (`POST /api/auth/refresh/`)
- **Description**: Refreshes access token using refresh token.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/refresh/`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "refresh": "<refresh-token>"
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "access": "<new-access-token>",
      "refresh": "<new-refresh-token>"
    }
    ```
- **Error Cases**:
  - Invalid refresh token:
    ```json
    {
      "refresh": "invalid-token"
    }
    ```
    - Status: 401 Unauthorized
    - Body: `{"detail": "Token is invalid or expired"}`
- **Verification**:
  - Use refresh token from `/api/auth/login/`.

### 6. Verification Request (`POST /api/auth/verify/request/`)
- **Description**: Requests verification for an authenticated user.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/verify/request/`
  - Headers: `Authorization: Bearer <access-token>`, `Content-Type: application/json`
  - Body: Empty
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "message": "Verification request submitted"
    }
    ```
- **Error Cases**:
  - Already verified user:
    - Status: 400 Bad Request
    - Body: `{"message": "User already verified"}`
- **Verification**:
  - Check Celery logs for `send_commissioner_contact_email`.
  - Verify email sent to `admin@mail.com`.

### 7. Verify User (`POST /api/auth/verify/`)
- **Description**: Commissioner verifies a user.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/verify/`
  - Headers: `Authorization: Bearer <commissioner-access-token>`, `Content-Type: application/json`
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003"
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "message": "User verified, email sent"
    }
    ```
- **Error Cases**:
  - Non-commissioner user:
    - Status: 403 Forbidden
    - Body: `{"error": "Permission denied"}`
  - User not found:
    ```json
    {
      "registration_number": "T/DEG/2020/9999"
    }
    ```
    - Status: 404 Not Found
    - Body: `{"error": "User not found"}`
- **Verification**:
  - Login as commissioner (`T/ADMIN/2020/0002`) to get access token.
  - Check Celery logs for `send_verification_email`.

### 8. Verification Status (`GET /api/auth/verify/status/`)
- **Description**: Checks user verification status.
- **Request**:
  - Method: GET
  - URL: `http://localhost:8000/api/auth/verify/status/`
  - Headers: `Authorization: Bearer <access-token>`
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "is_verified": true,
      "date_verified": "2025-08-26T11:52:00+03:00"
    }
    ```
- **Verification**:
  - Verify `is_verified` matches user’s status in MySQL.

### 9. Forgot Password (`POST /api/auth/forgot-password/`)
- **Description**: Resets password with security questions.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/forgot-password/`
  - Headers: `Content-Type: application/json`
  - Body:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "email": "neema.john@example.com",
      "state": 1,
      "course": 1,
      "first_name": "Neema",
      "last_name": "John"
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "message": "Password reset email sent"
    }
    ```
- **Error Cases**:
  - Incorrect details:
    ```json
    {
      "registration_number": "T/DEG/2020/0003",
      "email": "wrong@example.com",
      "state": 1,
      "course": 1
    }
    ```
    - Status: 404 Not Found
    - Body: `{"error": "User not found or details do not match"}`
- **Verification**:
  - Check Celery logs for `send_password_reset_email`.
  - Verify email sent to `neema.john@example.com` with new password.

### 10. Dashboard (`GET /api/auth/dashboard/`)
- **Description**: Retrieves user dashboard data.
- **Request**:
  - Method: GET
  - URL: `http://localhost:8000/api/auth/dashboard/`
  - Headers: `Authorization: Bearer <access-token>`
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "ongoing_elections": [
        {
          "id": 1,
          "title": "Student Election 2025",
          "start_date": "2025-08-01",
          "end_date": "2025-08-30"
        }
      ],
      "upcoming_elections": [],
      "past_elections": [],
      "election_levels": [],
      "user": {
        "registration_number": "T/DEG/2020/0003",
        "first_name": "Neema",
        "last_name": "John",
        "email": "neema.john@example.com",
        "is_verified": true,
        "role": "voter"
      }
    }
    ```
- **Verification**:
  - Confirm `ongoing_elections` includes `Student Election 2025`.

### 11. Contact Commissioner (`POST /api/auth/contact-commissioner/`)
- **Description**: Sends message to commissioners.
- **Request**:
  - Method: POST
  - URL: `http://localhost:8000/api/auth/contact-commissioner/`
  - Headers: `Authorization: Bearer <access-token>`, `Content-Type: application/json`
  - Body:
    ```json
    {
      "message": "I have an issue with voting."
    }
    ```
- **Expected Response**:
  - Status: 200 OK
  - Body:
    ```json
    {
      "message": "Message sent to commissioners"
    }
    ```
- **Error Cases**:
  - Missing message:
    ```json
    {}
    ```
    - Status: 400 Bad Request
    - Body: `{"error": "Message is required"}`
- **Verification**:
  - Check Celery logs for `send_commissioner_contact_email`.
  - Verify email sent to `admin@mail.com`.

## Troubleshooting
- **Celery Email Tasks**:
  - If emails fail, verify `EMAIL_HOST_PASSWORD` in `settings.py`.
  - Test SMTP:
    ```bash
    python -m smtpd -n -c DebuggingServer localhost:1025
    ```
    - Temporarily set `EMAIL_HOST='localhost'`, `EMAIL_PORT=1025`, `EMAIL_USE_TLS=False` in `settings.py`.
- **MySQL Errors**:
  - Ensure `PASSWORD` in `settings.py` matches MySQL user `election_sys`.
  - Test: `mysql -u election_sys -p -e "SELECT 1;"`.
- **JWT Issues**:
  - Verify `access` and `refresh` tokens are valid.
- **Logs**:
  - Check Django logs (`python manage.py runserver`).
  - Check Celery logs for task errors.








  <!-- Testing 1 -->
  >>Starting Celery Broker: 
```bash
celery -A mw_es.celery_app worker --loglevel=info -Q email_queue
```
# 1. Detail Comp:
 API Endpoint : http://localhost:8000/api/auth/register
Body:
{
  "registration_number": "T/DEG/2020/0003"
}
 
# 2. Complete Reg:

  API Endpoint : http://localhost:8000/api/auth/complete-registration/

  Body:
  {
  "registration_number": "T/DEG/2020/0003",
  "state": 1,
  "email": "cleven2024@gmail.com",
  "password": "password123",
  "course": 2
}

# 3. Login
API Endpoint : http://localhost:8000/api/auth/login/
Body: 
```
{
  "registration_number": "T/DEG/2020/0003",
  "password": "password123"
}

Response : 
{
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoicmVmcmVzaCIsImV4cCI6MTc1NzA3OTM3MCwiaWF0IjoxNzU2OTkyOTcwLCJqdGkiOiJjYTU3NWNmMzFmNmE0NTY0OGY5ODQ4MzVmMWY5NmJjOCIsInVzZXJfaWQiOiIzNCJ9.qkpEXA42gHhbs8wKLC_E0aCU-KZGPoWPo32nD03rO00",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2OTk2NTcwLCJpYXQiOjE3NTY5OTI5NzAsImp0aSI6IjUwYjU2ODc2YTZjZDQ5Y2Y5YWVlZjQ0ZmQwZDMyMzg5IiwidXNlcl9pZCI6IjM0In0.dbGIunEdJnArSAi7wzIglZYsHY-jlXdZqf_6m7PTrJI"
}
```

4. LogOut
Method: POST
URL: http://localhost:8000/api/auth/logout/
Headers: Authorization: Bearer <access-token>, Content-Type: application/json
Body:
{
  "refresh": "<refresh-token>"
}






Accept: */*
User-Agent: Thunder Client (https://www.thunderclient.com)
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU2OTk2NTcwLCJpYXQiOjE3NTY5OTI5NzAsImp0aSI6IjUwYjU2ODc2YTZjZDQ5Y2Y5YWVlZjQ0ZmQwZDMyMzg5IiwidXNlcl9pZCI6IjM0In0.dbGIunEdJnArSAi7wzIglZYsHY-jlXdZqf_6m7PTrJI
Content-Type: application/json
