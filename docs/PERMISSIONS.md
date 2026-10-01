# Permissions & Role Matrix

This document defines the access control boundaries for the Perin Devi Natyalayam platform.

## Roles

1. **ADMIN**: System administrators. Have full read and write access to all data across all branches.
2. **STAFF**: Instructors and administrative staff linked to a specific branch. Teachers are a subset of staff with `is_teacher=True`.
3. **GUARDIAN**: Parents or legal guardians of enrolled students.
4. **STUDENT**: The students themselves. Young children may not have direct login credentials; older students might.

## Access Rules

### 1. Accounts & Identity
- **Profiles**: 
  - `Admin` can view/edit all profiles.
  - `Staff` can view profiles of students enrolled in their assigned batches. They have exclusive access to `medical_notes` for safety.
  - `Guardian` can only view/edit profiles of students explicitly linked to them.
  - `Student` can only view their own profile.
- **Audit Logs**: Read-only for `Admin` to maintain a secure trail.

### 2. Academics
- **Batches**:
  - `Admin`: Full access.
  - `Staff`: Can only view batches they are designated as the `teacher` for.
  - `Guardian`: Can view batch details only if their linked child is enrolled.
  - `Student`: Can view batch details only if enrolled.
- **Sessions**: Follows Batch visibility rules.

### 3. Attendance
- **Session Roster & Marking**:
  - `Teacher`: Can mark attendance for their own sessions. Restricted by a 48-hour edit window.
  - `Admin`: Can override attendance at any time. Automatically logs an `ADMIN_OVERRIDE` event.
- **Join Session**:
  - `Student`/`Guardian`: Can only join sessions their child is actively enrolled in, strictly within the -10min to +end_time window. Auto-logs a `SessionJoin`.
- **Leave Requests**:
  - `Student`/`Guardian`: Can submit and view leaves for themselves/their children.
  - `Teacher`/`Admin`: Can approve or reject leaves for students in their batches.

## Enforcement (Queryset Scoping)
Instead of relying purely on ad-hoc view checks, the platform uses **Queryset Scoping** (`apps.accounts.scopes`) combined with central permissions (`IsAdmin`, `IsStaff`, `IsGuardian`, `IsStudent`). 

When a user requests a list of sessions, leaves, or students, the base `queryset` is passed through a scope function (e.g., `scope_sessions(qs, user)`), which guarantees that cross-tenant access returns empty sets or HTTP 404s, preventing ID guessing and data leakage.
