# Track 07: Authentication & ACL - Plan

## Step 1: Database Models
- Add `User` model to `tascam_app/models.py`.
- Fields: `id`, `email` (unique), `name`, `role` (default: 'user'), `status` (default: 'pending').
- Create database migration/update script if necessary.

## Step 2: Google OAuth Integration
- Install necessary libraries (e.g., `authlib` or `fastapi-sso`, `itsdangerous` for sessions).
- Configure OAuth client with Google Client ID and Secret (loaded from environment variables).
- Implement `/login` endpoint to redirect to Google.
- Implement `/auth/callback` endpoint to handle the Google response, create/update the user in the database, and set a session cookie.
- Implement `/logout` endpoint.

## Step 3: Authorization Middleware/Dependencies
- Create a `get_current_user` dependency that reads the session cookie and fetches the user from the database.
- Create a `require_approved_user` dependency that ensures the user is logged in and has `status == 'approved'`.
- Create a `require_admin` dependency that ensures the user is logged in and has `role == 'admin'`.
- Apply these dependencies to existing routes.

## Step 4: Admin Interface
- Create an HTML template for the admin dashboard.
- Implement a route (`/admin/users`) protected by `require_admin` to list all users.
- Implement API endpoints to update user status (approve/reject) and roles.

## Step 5: Super User Bootstrap
- Add logic in the auth callback: if the logging-in user's email matches a configured `SUPER_USER_EMAIL` environment variable, automatically set their role to `admin` and status to `approved`.

## Step 6: Verification
- Verify login flow with a Google account.
- Verify that a new user is created as `pending` and cannot access the main app.
- Verify that the super user can access the admin page and approve the pending user.
- Verify that the approved user can now access the main app.
