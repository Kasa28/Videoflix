# Videoflix API Documentation

## Overview

The Videoflix backend exposes authentication and video-streaming endpoints through a REST API.

```text
Base URL: http://127.0.0.1:8000/api/
Content type: application/json
Authentication: HttpOnly JWT cookies
```

Authenticated frontend requests must include browser credentials:

```javascript
fetch(url, {
  credentials: "include"
});
```

The backend uses these cookies:

| Cookie | Purpose | Default lifetime |
| --- | --- | --- |
| `access_token` | Authenticates protected API requests | 15 minutes |
| `refresh_token` | Creates a new access token | 7 days |

## Error Responses

Validation errors use the standard Django REST Framework JSON format. Authentication messages intentionally avoid revealing whether an email address or password was incorrect.

Common status codes:

| Status | Meaning |
| --- | --- |
| `200 OK` | Request completed successfully |
| `201 Created` | Resource created successfully |
| `400 Bad Request` | Missing or invalid request data |
| `401 Unauthorized` | Authentication is missing or invalid |
| `404 Not Found` | Video, playlist, segment, or token target was not found |

---

## Authentication

### Register an account

```http
POST /api/register/
```

Creates an inactive user and sends an activation email. Authentication is not required.

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!",
  "confirmed_password": "StrongPassword123!"
}
```

Successful response — `201 Created`:

```json
{
  "user": {
    "id": 1,
    "email": "user@example.com"
  },
  "token": "activation-token"
}
```

The token in the JSON response is informational. Account activation normally happens through the link sent by email.

Possible errors:

- `400 Bad Request` when fields are missing, passwords do not match, the password fails validation, or the email is already registered.

### Activate an account

```http
GET /api/activate/<uidb64>/<token>/
```

Activates the user represented by the encoded user ID and activation token. Authentication is not required.

Successful response — `200 OK`:

```json
{
  "message": "Account successfully activated."
}
```

Invalid or expired token — `400 Bad Request`:

```json
{
  "detail": "Activation failed."
}
```

### Log in

```http
POST /api/login/
```

Authenticates an active user and sets `access_token` and `refresh_token` as HttpOnly cookies.

Request:

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123!"
}
```

Successful response — `200 OK`:

```json
{
  "detail": "Login successful",
  "user": {
    "id": 1,
    "username": "user@example.com"
  }
}
```

Invalid credentials — `401 Unauthorized`:

```json
{
  "detail": "Email or password is incorrect."
}
```

### Refresh the access token

```http
POST /api/token/refresh/
```

Uses the `refresh_token` cookie to create and set a new `access_token` cookie. No request body is required.

Successful response — `200 OK`:

```json
{
  "detail": "Token refreshed",
  "access": "new-access-token"
}
```

Missing cookie — `400 Bad Request`:

```json
{
  "detail": "Refresh token is missing."
}
```

Invalid or blacklisted token — `401 Unauthorized`:

```json
{
  "detail": "Refresh token is invalid."
}
```

### Log out

```http
POST /api/logout/
```

Blacklists the refresh token and deletes both authentication cookies. The `refresh_token` cookie is required; no request body is required.

Successful response — `200 OK`:

```json
{
  "detail": "Logout successful! All tokens were deleted."
}
```

Missing cookie returns `400 Bad Request`. An invalid or already blacklisted token returns `401 Unauthorized`.

### Request a password reset

```http
POST /api/password_reset/
```

Sends a password-reset email when the account exists. The response is deliberately identical for known and unknown email addresses. Authentication is not required.

Request:

```json
{
  "email": "user@example.com"
}
```

Successful response — `200 OK`:

```json
{
  "detail": "An email has been sent to reset your password."
}
```

### Confirm a password reset

```http
POST /api/password_confirm/<uidb64>/<token>/
```

Validates the reset token and stores a new hashed password. Authentication is not required.

Request:

```json
{
  "new_password": "NewStrongPassword123!",
  "confirm_password": "NewStrongPassword123!"
}
```

Successful response — `200 OK`:

```json
{
  "detail": "Your Password has been successfully reset."
}
```

Invalid or expired token — `400 Bad Request`:

```json
{
  "detail": "Password reset failed."
}
```

---

## Videos

All video endpoints require a valid `access_token` cookie.

### List videos

```http
GET /api/video/
```

Returns all videos ordered by `created_at` in descending order.

Successful response — `200 OK`:

```json
[
  {
    "id": 3,
    "created_at": "2026-11-10T21:14:33Z",
    "title": "Water see",
    "description": "beautiful",
    "thumbnail_url": "http://127.0.0.1:8000/media/videos/365704/thumbnail.jpg",
    "category": "See"
  }
]
```

Without a valid access cookie, the endpoint returns `401 Unauthorized`.

### Get an HLS playlist

```http
GET /api/video/<movie_id>/<resolution>/index.m3u8
```

Returns the HLS playlist for one video and resolution.

Path parameters:

| Parameter | Description |
| --- | --- |
| `movie_id` | Numeric video ID |
| `resolution` | `480p`, `720p`, or `1080p` |

Successful response:

```text
Status: 200 OK
Content-Type: application/vnd.apple.mpegurl
Body: HLS M3U8 playlist
```

The endpoint returns `404 Not Found` when the video, resolution, or generated playlist does not exist.

### Get an HLS segment

```http
GET /api/video/<movie_id>/<resolution>/<segment>/
```

Returns one transport-stream segment referenced by the playlist.

Example:

```http
GET /api/video/3/480p/segment_000.ts/
```

Path parameters:

| Parameter | Description |
| --- | --- |
| `movie_id` | Numeric video ID |
| `resolution` | `480p`, `720p`, or `1080p` |
| `segment` | Safe segment filename such as `segment_000.ts` |

Successful response:

```text
Status: 200 OK
Content-Type: video/mp2t
Body: Binary MPEG transport-stream data
```

The endpoint returns `404 Not Found` for missing files, unsupported resolutions, or unsafe segment names.

---

## Media Processing

Video uploads are managed through Django Admin rather than through a public upload endpoint. Saving a new video queues an RQ background job that:

1. creates `thumbnail.jpg`;
2. creates HLS playlists and segments in 480p, 720p, and 1080p;
3. stores the generated thumbnail path on the video record.

Until processing is complete, a playlist endpoint can temporarily return `404 Not Found`.
