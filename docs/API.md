# API Documentation Notes

## Authentication
- **Base Path**: `/api/v1/auth/`
- **Method**: Session/Cookie based with CSRF tokens.
- **Endpoints**:
  - `GET /csrf/`: Fetches the CSRF token. Required before `POST` actions if not already set.
  - `POST /request-otp/`: Requests a 6-digit OTP for a given E.164 formatted phone number.
  - `POST /verify-otp/`: Submits phone and OTP to establish an authenticated session.
  - `GET /me/`: Returns current logged-in user profile and role.
  - `POST /logout/`: Destroys the session.

## Attendance & Sessions
- **Base Path**: `/api/v1/attendance/`
- **Endpoints**:
  - `GET /sessions/`: Lists active sessions scoped to the user (e.g., today's classes for a teacher).
  - `GET /sessions/{id}/roster/`: Returns the enrolled student list and their current attendance status.
  - `POST /sessions/{id}/bulk_mark/`: Teacher endpoint to save the roster. Requires `attendances` list payload.
  - `POST /sessions/{id}/join/`: Student endpoint to join a live online class. Returns the `meeting_url`.
  - `GET /summary/?student_id=UUID`: Returns percentage, present, late, absent, and excused counts.
  
## Leave Requests
- **Base Path**: `/api/v1/attendance/leaves/`
- **Endpoints**:
  - `GET /`, `POST /`: List or create leave requests.
  - `POST /{id}/approve/`: Staff/Admin approval action. Auto-marks overlapping sessions as `EXCUSED`.
  - `POST /{id}/reject/`: Rejects a request.

## Scoping & Error Handling
All API endpoints rely on robust queryset scoping. Accessing an ID that exists but belongs to a different tenant will safely return `404 Not Found` to prevent enumeration attacks. Missing or expired OTPs return `400 Bad Request` with descriptive `detail` keys.
