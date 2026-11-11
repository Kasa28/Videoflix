# Videoflix Backend

Videoflix is a Django REST API for a video-on-demand application. It provides account registration and activation, cookie-based JWT authentication, password recovery, video metadata, automatically generated thumbnails, and HLS streaming in multiple resolutions.

The frontend is maintained as a separate project and communicates with this backend through the REST API.

## Features

- User registration with email activation
- Login and logout with HttpOnly JWT cookies
- Access-token refresh and refresh-token blacklisting
- Password reset by email
- Protected video catalogue ordered by creation date
- Automatic thumbnail generation with FFmpeg
- HLS conversion in 480p, 720p, and 1080p
- Background video processing with Django RQ and Redis
- PostgreSQL database
- Django Admin for video management
- Docker-based local environment
- Automated authentication and video API tests

## Technology Stack

- Python 3.12
- Django and Django REST Framework
- Simple JWT
- PostgreSQL
- Redis and Django RQ
- FFmpeg
- Gunicorn
- Docker Compose

## Project Structure

```text
Videoflix/
├── auth_app/              Authentication API, emails, cookies, and tests
├── video_app/             Video model, API, FFmpeg tasks, signals, and tests
├── core/                  Django settings and root URL configuration
├── backend.Dockerfile
├── backend.entrypoint.sh
├── docker-compose.yml
├── manage.py
└── requirements.txt
```

## Requirements

- Docker Desktop with Docker Compose
- A separately served Videoflix frontend
- SMTP credentials for real activation and password-reset emails

Python, PostgreSQL, Redis, and FFmpeg are provided by the Docker setup.

## Installation

1. Clone the repository and enter the project directory:

   ```bash
   git clone <repository-url>
   cd Videoflix
   ```

2. Create the local environment file.

   PowerShell:

   ```powershell
   Copy-Item .env.template .env
   ```

   Linux or macOS:

   ```bash
   cp .env.template .env
   ```

3. Replace all placeholder values in `.env`, especially the secret key, database credentials, superuser password, and SMTP credentials.

4. Start the application:

   ```bash
   docker compose up -d --build
   ```

The entrypoint waits for PostgreSQL, collects static files, applies migrations, creates the configured superuser if necessary, starts the RQ worker, and launches Gunicorn.

The backend is then available at:

```text
http://127.0.0.1:8000/
```

The Django Admin is available at:

```text
http://127.0.0.1:8000/admin/
```

## Environment Variables

Important variables are documented in `.env.template`.

```env
SECRET_KEY=replace-with-a-secure-random-value
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500
CORS_ALLOWED_ORIGINS=http://127.0.0.1:5500
FRONTEND_URL=http://127.0.0.1:5500

DB_NAME=videoflix
DB_USER=videoflix
DB_PASSWORD=replace-with-a-secure-password
DB_HOST=db
DB_PORT=5432

REDIS_HOST=redis
REDIS_LOCATION=redis://redis:6379/1
REDIS_PORT=6379
REDIS_DB=0
```

Use `DEBUG=True` only during local development, for example to enable the Django Debug Toolbar. Keep `DEBUG=False` in production. Thumbnails and HLS files are delivered through authenticated API endpoints and do not depend on debug-mode media serving.

Never commit `.env`. The file is excluded by `.gitignore`; only `.env.template` belongs in the repository.

## Email Configuration

Registration and password recovery require an SMTP server. Add the provider's credentials to `.env`:

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.example.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=your-smtp-password
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
DEFAULT_FROM_EMAIL=noreply@example.com
```

Use either TLS or SSL, never both at the same time. Port `587` commonly uses TLS, while port `465` commonly uses SSL. Confirm the values with the selected email provider.

After changing `.env`, recreate the web container so Docker reloads the environment:

```bash
docker compose up -d --force-recreate web
```

For development without a real SMTP server, use:

```env
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Emails are then printed in the container logs:

```bash
docker compose logs -f web
```

## Video Management

Videos are uploaded through Django Admin. Open `/admin/`, select **Videos**, and create a new entry with a title, description, category, and video file.

After the database transaction is committed, a Django signal queues a background job. The RQ worker then:

1. extracts a thumbnail from the video;
2. stores the thumbnail path on the video record;
3. creates HLS playlists and segments in 480p, 720p, and 1080p.

Generated files use the following structure:

```text
video_app/media/videos/<video-name>/
├── thumbnail.jpg
├── 480p/
│   ├── index.m3u8
│   └── segment_000.ts
├── 720p/
│   ├── index.m3u8
│   └── segment_000.ts
└── 1080p/
    ├── index.m3u8
    └── segment_000.ts
```

Deleting a video through Django also removes its original file and generated output directory.

## API Endpoints

All endpoints are prefixed with `/api/`.

Detailed request and response examples are available in [docs/API.md](docs/API.md).

### Authentication

| Method | Endpoint | Description | Authentication |
| --- | --- | --- | --- |
| POST | `/api/register/` | Register an inactive account and send an activation email | Public |
| GET | `/api/activate/<uidb64>/<token>/` | Activate an account | Public |
| POST | `/api/login/` | Authenticate and set JWT cookies | Public |
| POST | `/api/logout/` | Blacklist the refresh token and clear cookies | Refresh cookie |
| POST | `/api/token/refresh/` | Create and set a new access token | Refresh cookie |
| POST | `/api/password_reset/` | Send a password-reset email | Public |
| POST | `/api/password_confirm/<uidb64>/<token>/` | Store a new password | Public |

### Videos

| Method | Endpoint | Description | Authentication |
| --- | --- | --- | --- |
| GET | `/api/video/` | Return video metadata ordered by newest first | Access cookie |
| GET | `/api/video/<movie_id>/thumbnail/` | Return a generated thumbnail | Access cookie |
| GET | `/api/video/<movie_id>/<resolution>/index.m3u8` | Return an HLS playlist | Access cookie |
| GET | `/api/video/<movie_id>/<resolution>/<segment>/` | Return an HLS transport-stream segment | Access cookie |

Supported resolution values are `480p`, `720p`, and `1080p`.

JWT values are stored in HttpOnly cookies named `access_token` and `refresh_token`. Frontend requests must include credentials.

## Running Tests

Run the complete authentication and video test suite inside Docker:

```bash
docker compose exec web python manage.py test auth_app.tests video_app.tests
```

Run Django's system check:

```bash
docker compose exec web python manage.py check
```

Verify that no model changes are missing migrations:

```bash
docker compose exec web python manage.py makemigrations --check --dry-run
```

## Useful Commands

```bash
# Start all services
docker compose up -d

# Rebuild after changing Python dependencies
docker compose up -d --build

# Follow backend and worker output
docker compose logs -f web

# Apply migrations manually
docker compose exec web python manage.py migrate

# Stop the services
docker compose down
```

## Security Notes

- Keep `.env` and all real credentials out of version control.
- Use a new random `SECRET_KEY` outside development.
- Set `DEBUG=False` in production.
- Use HTTPS in production so secure authentication cookies can be enabled.
- Serve static and media files through an appropriate production service.
- Use strong SMTP, database, and administrator passwords.

## Frontend

The frontend must be served separately and configured to use:

```text
http://127.0.0.1:8000/api/
```

The default local CORS and frontend settings expect the frontend at `http://127.0.0.1:5500`.
