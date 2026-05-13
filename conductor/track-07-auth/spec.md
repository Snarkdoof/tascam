# Track 07: Authentication & ACL - Specification

## Objective
Implement Google Login for authentication and a database-backed Access Control List (ACL) for authorization, including an admin interface for user management.

## Requirements
1. **Google Login:** Integrate Google OAuth2 so users can log in with their Google accounts.
2. **User Model:** Create a `User` model in SQLModel to store user information (email, name, role, status).
3. **Roles & Status:**
   - Roles: `admin` (super user), `user`.
   - Status: `pending` (awaiting approval), `approved`, `rejected`.
4. **Authorization (ACL):**
   - Only `approved` users can access the main application.
   - `pending` users see a "waiting for approval" page.
   - Unauthenticated users are redirected to the login page.
5. **Admin Interface:** A dedicated page (accessible only to `admin` users) to view all users and change their status/roles.
6. **Super User:** The user "Njaal" (identified by a specific email) should be automatically granted `admin` status upon first login or via a setup script.

## Deliverables
- Updated `models.py` with the `User` model.
- Authentication endpoints (`/login`, `/auth/callback`, `/logout`).
- Dependency injection for FastAPI to protect routes (`get_current_user`).
- Admin UI templates and endpoints for user management.
