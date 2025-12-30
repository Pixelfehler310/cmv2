# Login Enhancement Plan

This document outlines the plan to enhance the login functionality for the Civic VTT application, covering both frontend and backend aspects, including OAuth support.

## 1. Login Window (Frontend)

The login page will be redesigned to provide a premium, immersive experience suitable for a VTT.

### UI Design

- **Layout**: Centered card on a thematic background (already present, but will be refined).
- **Styling**: Use Shadcn UI components for a polished look.
- **Elements**:
  - **Branding**: Civic VTT logo/header.
  - **OAuth Buttons**: Prominent buttons for "Sign in with Google" and "Sign in with Discord".
  - **Divider**: "Or continue with" divider.
  - **Credentials Form**: Username/Password inputs for legacy/local auth.
  - **Action Links**: "Forgot Password?", "Don't have an account? Sign up".
  - **Dev Login**: Hidden or less prominent in production, but accessible for dev (keep existing functionality).

### UX Flow

1.  User lands on `/login`.
2.  **Scenario A (OAuth)**:
    - User clicks "Sign in with Google".
    - Redirects to Backend `/auth/google/authorize`.
    - Backend redirects to Google.
    - User authenticates with Google.
    - Google redirects to Backend `/auth/google/callback`.
    - Backend processes login/registration and redirects to Frontend `/auth/callback?token=...` or sets a secure cookie.
    - Frontend stores token and redirects to `/campaigns`.
3.  **Scenario B (Credentials)**:
    - User enters username/password.
    - Frontend calls `POST /auth/login`.
    - On success, store token and redirect.

## 2. Communication Interfaces (API)

We will extend the existing `src/identity` module.

### Existing Endpoints

- `POST /auth/register`: Register with username/password.
- `POST /auth/login`: Login with username/password (returns JWT).
- `GET /auth/me`: Get current user.

### New Endpoints (OAuth)

- `GET /auth/{provider}/authorize`: Initiates OAuth flow.
  - `provider`: `google`, `discord`.
  - Returns: 302 Redirect to provider's consent page.
- `GET /auth/{provider}/callback`: Handles provider callback.
  - Query Params: `code`, `state`.
  - Logic: Exchange code for profile, find/create user, generate JWT.
  - Returns: 302 Redirect to Frontend with JWT (e.g., `https://app.civicvtt.com/auth/callback?token=xyz`).

## 3. Necessary Libraries

### Backend (Python/FastAPI)

- **`authlib`**: Comprehensive OAuth client support for FastAPI.
- **`httpx`**: For making async HTTP requests to providers (used by Authlib).
- **`itsdangerous`**: For signing state parameters (security against CSRF).

### Frontend (React)

- **`lucide-react`**: For provider icons (Google, Discord).
- **`zod`**: For form validation (if not already used).
- **`react-hook-form`**: For form handling (if not already used).

## 4. Data Model Changes

We need to support linking multiple authentication providers to a single user account.

### New Model: `UserSocialAuth`

Instead of cluttering the `User` table, we'll create a related table.

```python
class UserSocialAuth(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "user_social_auths"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"))
    provider: Mapped[str] = mapped_column(String) # 'google', 'discord'
    provider_user_id: Mapped[str] = mapped_column(String) # Unique ID from provider
    email: Mapped[str] = mapped_column(String, nullable=True)
    extra_data: Mapped[dict] = mapped_column(JSON, default={})

    user: Mapped["User"] = relationship("User", back_populates="social_auths")
```

### Updates to `User` Model

- Add relationship: `social_auths = relationship("UserSocialAuth", back_populates="user")`.
- Make `hashed_password` nullable (if a user only uses OAuth).

## 5. Implementation Steps

1.  **Backend Dependencies**: Install `authlib`, `httpx`.
2.  **Database Migration**: Create `UserSocialAuth` model and update `User`.
3.  **OAuth Configuration**: Add `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, etc., to `config.py`.
4.  **Backend Logic**: Implement `authorize` and `callback` endpoints in `src/identity`.
5.  **Frontend UI**: Update `LoginRoute.tsx` with new design and OAuth buttons.
6.  **Frontend Logic**: Handle the redirect callback to extract and store the token.
