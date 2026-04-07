# VibeCheck Backend

Python backend for the VibeCheck social platform — content curation, aura profiles, social discovery, gamification, and more.

## Tech Stack

- **Flask** - Web framework
- **Flasgger** - Auto-generated Swagger docs
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database (Docker) / SQLite (local dev)
- **JWT** (Flask-JWT-Extended) - Authentication
- **bcrypt** - Password hashing
- **httpx** - Async HTTP client for external APIs
- **python-dotenv** - Environment variable loading

## Setup

### Option 1: Docker (Recommended)

1. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env if needed (optional for Docker — defaults work out of the box)
   ```

2. **Start all services**
   ```bash
   docker compose up -d --build
   ```

3. **Check services are running**
   ```bash
   docker compose ps
   ```

   The API will be available at `http://localhost:3000`

### Option 2: Local Development

1. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```
   `python-dotenv` is installed, so the app automatically loads `.env`.

4. **Start PostgreSQL in Docker**
   ```bash
   docker compose up -d db
   ```

5. **Run the application locally**
   ```bash
   python main.py
   ```

   The server will start on `http://localhost:3000`

## API Endpoints

### Live Documentation

The backend generates its own API documentation from the actual implementation:

- **Swagger UI**: http://localhost:3000/docs/
- **OpenAPI JSON Spec**: http://localhost:3000/apispec_1.json
- **Compatibility alias**: http://localhost:3000/apispec.json

This allows you to:
1. See what the backend **actually implements** (not just what the spec says)
2. Compare the generated docs with [openapi-mvp.yaml](../openapi-mvp.yaml) to verify they match
3. Test endpoints interactively in your browser

### Endpoint Summary

| Group | Prefix | Endpoints |
|-------|--------|----------|
| **Auth** | `/api/v1/auth` | `POST /register`, `POST /login` |
| **Users** | `/api/v1/users` | `GET /profile`, `PUT /profile`, `GET /{userId}` |
| **Content** | `/api/v1/content` | `GET /{category}`, `GET /{category}/{id}` — movies, albums, games, books, locations |
| **Search** | `/api/v1/search` | `GET /` with `query` and `categories` params |
| **Aura** | `/api/v1/aura` | `GET/PUT /profile`, `GET /profile/{userId}`, `GET/POST /shares` |
| **Social** | `/api/v1/social` | Rooms CRUD, join/leave, posts, trending |
| **Discovery** | `/api/v1/discovery` | `GET /feed` |
| **Gamification** | `/api/v1/` | Badges, curator levels, XP, streaks |
| **Health** | `/api/v1/health` | `GET /` |

For full request/response details, see the **Swagger UI** at http://localhost:3000/docs

## Project Structure

```
backend/
├── main.py                        # Entry point (loads .env, creates app)
├── requirements.txt               # Python dependencies
├── Dockerfile                     # Container build
├── docker-compose.yml             # Backend + PostgreSQL services
├── .env.example                   # Environment variable template
├── app/
│   ├── __init__.py                # Flask app factory + blueprint registration
│   ├── config.py                  # Configuration from env vars
│   ├── database.py                # SQLAlchemy engine & session setup
│   ├── seed_rooms.py              # Seed aesthetic rooms
│   ├── seed_gamification.py       # Seed badges & levels
│   ├── models/
│   │   ├── user.py                # User model
│   │   ├── content.py             # Content / curation models
│   │   ├── room.py                # Aesthetic room model
│   │   ├── post.py                # Room post model
│   │   ├── share.py               # Aura share model
│   │   ├── badge.py               # Badge model
│   │   └── gamification.py        # Levels, XP, streaks
│   ├── routes/
│   │   ├── auth.py                # /auth — register, login
│   │   ├── user_profile.py        # /users — profile CRUD
│   │   ├── content.py             # /content — movies, albums, games, books, locations
│   │   ├── search.py              # /search — global search
│   │   ├── aura.py                # /aura — aura profile & shares
│   │   ├── social.py              # /social — rooms, posts
│   │   ├── discovery.py           # /discovery — feed
│   │   ├── gamification.py        # badges, levels, XP
│   │   └── badges.py              # (unused, replaced by gamification)
│   └── services/
│       ├── aura_inference.py       # Auto-generate aesthetic tags & colors
│       ├── badge_service.py        # Badge award logic
│       └── external_apis/          # Third-party API clients
│           ├── movies.py           # TMDB
│           ├── albums.py           # MusicBrainz / Spotify
│           ├── games.py            # RAWG
│           ├── books.py            # Open Library
│           └── locations.py        # Location / weather APIs
└── tests/                         # See tests/TEST_README.md
    ├── unit/                      # Fast tests (SQLite, no Docker)
    └── integration/               # Full API tests (PostgreSQL + Docker)
```

## Database Schema

### Users Table
- `user_id` (PK) - String, format: "u_{12-char-hex}"
- `email` - String(255), unique, indexed
- `username` - String(20), unique, indexed
- `password_hash` - String(255)
- `avatar` - Text, nullable
- `bio` - String(500), nullable
- `created_at` - DateTime
- `updated_at` - DateTime

## Development

The application automatically creates database tables on startup using SQLAlchemy's `create_all()`.

## Environment Variables

See `.env.example` for all variables:

| Variable | Purpose | Required |
|----------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | Yes (local dev) |
| `JWT_SECRET_KEY` | Secret for JWT tokens | Yes |
| `FLASK_ENV` | `development` or `production` | No (defaults to dev) |
| `PORT` | Server port | No (defaults to 3000) |
| `TMDB_API_KEY` | The Movie Database API key | Yes (for movies) |
| `RAWG_API_KEY` | RAWG video games API key | Yes (for games) |
| `UNSPLASH_ACCESS_KEY` | Unsplash API key | Yes (for locations) |
| `POSTGRES_DB` | PostgreSQL database name | Docker only |
| `POSTGRES_USER` | PostgreSQL username | Docker only |
| `POSTGRES_PASSWORD` | PostgreSQL password | Docker only |

**Note:** Docker Compose uses the same `.env` file. `python-dotenv` loads it automatically for local runs too.

## Docker Commands

```bash
# Start all services (backend + database)
docker compose up -d

# Start only database
docker compose up -d db

# View logs
docker compose logs -f

# View backend logs only
docker compose logs -f backend

# Rebuild after code changes
docker compose up -d --build

# Stop all services
docker compose down

# Stop and remove data (⚠️ destroys all data)
docker compose down -v

# Access PostgreSQL shell
docker compose exec db psql -U postgres -d vibecheck
```

## Testing

Comprehensive test suite with **270+ test cases** split into unit and integration tests.

### Quick Start

```bash
# Install test dependencies
pip install -r tests/test_requirements.txt

# Run unit tests (fast, no Docker needed)
pytest tests/unit/

# Run integration tests (requires Docker + PostgreSQL)
docker compose up -d db
pytest tests/integration/

# Run everything
pytest tests/
```

### Test Documentation

- **[tests/TESTING_QUICKREF.md](tests/TESTING_QUICKREF.md)** — Quick reference
- **[tests/TEST_README.md](tests/TEST_README.md)** — Complete guide
