# VibeCheck Backend

Python backend for VibeCheck MVP - Authentication endpoints.

## Tech Stack

- **Flask** - Web framework
- **SQLAlchemy** - ORM
- **PostgreSQL** - Database
- **JWT** - Authentication
- **bcrypt** - Password hashing

## Setup

### Option 1: Docker (Recommended)

1. **Configure environment**
   ```powershell
   cp .env.example .env
   # Edit .env if needed (optional for Docker)
   ```

2. **Start all services**
   ```powershell
   docker-compose up -d
   ```

3. **Check services are running**
   ```powershell
   docker-compose ps
   ```

   The API will be available at `http://localhost:3000`

### Option 2: Local Development

1. **Create virtual environment**
   ```powershell
   python -m venv venv
   .venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```powershell
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Start PostgreSQL in Docker**
   ```powershell
   docker-compose up -d postgres
   ```

5. **Run the application locally**
   ```powershell
   python main.py
   ```

   The server will start on `http://localhost:3000`

## API Endpoints

### Live Documentation

The backend generates its own API documentation from the actual implementation:

- **Swagger UI**: http://localhost:3000/docs
- **OpenAPI JSON Spec**: http://localhost:3000/apispec.json

This allows you to:
1. See what the backend **actually implements** (not just what the spec says)
2. Compare the generated docs with [openapi-mvp.yaml](../openapi-mvp.yaml) to verify they match
3. Test endpoints interactively in your browser

### Authentication

#### POST /api/v1/auth/register
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "username": "aesthetic_anna"
}
```

**Response (201):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "userId": "u_123abc456def",
    "email": "user@example.com",
    "username": "aesthetic_anna",
    "avatar": null,
    "bio": null,
    "createdAt": "2026-02-11T12:00:00",
    "updatedAt": "2026-02-11T12:00:00"
  }
}
```

#### POST /api/v1/auth/login
Login with existing credentials.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200):**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "userId": "u_123abc456def",
    "email": "user@example.com",
    "username": "aesthetic_anna",
    "avatar": null,
    "bio": null,
    "createdAt": "2026-02-11T12:00:00",
    "updatedAt": "2026-02-11T12:00:00"
  }
}
```

## Project Structure

```
backend/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── config.py             # Configuration
│   ├── database.py           # Database setup
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py           # User model
│   └── routes/
│       ├── __init__.py
│       └── auth.py           # Auth endpoints
├── main.py                   # Application entry point
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
└── README.md                # This file
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

See `.env.example` for required environment variables:
- `DATABASE_URL` - PostgreSQL connection string (for local Python app)
- `JWT_SECRET_KEY` - Secret key for JWT tokens (change in production!)
- `FLASK_ENV` - Environment (development/production)
- `PORT` - Server port (default: 3000)
- `POSTGRES_DB` - PostgreSQL database name (Docker only)
- `POSTGRES_USER` - PostgreSQL username (Docker only)
- `POSTGRES_PASSWORD` - PostgreSQL password (Docker only, change in production!)

**Note:** Docker Compose uses the same `.env` file for PostgreSQL credentials. Defaults are set for development convenience.

## Docker Commands

```powershell
# Start all services (backend + database)
docker-compose up -d

# Start only database
docker-compose up -d postgres

# View logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# Rebuild after code changes
docker-compose up -d --build

# Stop all services
docker-compose down

# Stop and remove data (⚠️ destroys all data)
docker-compose down -v

# Access PostgreSQL shell
docker-compose exec postgres psql -U postgres -d vibecheck
```
