# Task API

![CI](https://github.com/rcayroc02/API-task-manager/actions/workflows/ci.yml/badge.svg)

A RESTful task management API built with **FastAPI** and **PostgreSQL**. It features JWT authentication, per-user task isolation, pagination, filtering, database migrations, automated tests and a CI pipeline.

<!-- Optional: uncomment once deployed
**Live demo:** https://your-app.onrender.com/docs
(The free tier may take ~30 seconds to wake up on the first request.)
-->

## Features

- User registration and login with **JWT** access tokens
- Passwords hashed with **Argon2**
- Full **CRUD** for tasks, protected by authentication
- **Ownership rules:** every user can only see and modify their own tasks
- Pagination, status filtering and sorting on the task list
- Partial updates with `PATCH`
- Database migrations with **Alembic**
- Automated tests with **pytest** and coverage reporting
- Linting and formatting with **Ruff**
- **CI** with GitHub Actions (lint, migrations, tests, Docker build)
- Fully containerized with **Docker Compose**
- Interactive API documentation (Swagger UI) generated automatically

## Tech stack

| Area | Technology |
|---|---|
| Language | Python 3.12 |
| Framework | FastAPI |
| Database | PostgreSQL 16 |
| ORM / Migrations | SQLAlchemy 2.0, Alembic |
| Validation / Settings | Pydantic v2, pydantic-settings |
| Auth | PyJWT, pwdlib (Argon2) |
| Testing | pytest, pytest-cov, httpx |
| Quality | Ruff |
| DevOps | Docker, Docker Compose, GitHub Actions |

## Project structure

```
.
├── app/
│   ├── main.py             # Application entry point
│   ├── config.py           # Settings loaded from environment variables
│   ├── database.py         # Engine, session and get_db dependency
│   ├── exceptions.py       # Domain exceptions
│   ├── models/             # SQLAlchemy models (User, Task)
│   ├── schemas/            # Pydantic schemas (request / response)
│   ├── routers/            # HTTP endpoints
│   ├── services/           # Business logic and database queries
│   └── auth/               # Password hashing, JWT, current-user dependency
├── alembic/                # Database migrations
├── tests/                  # Automated tests
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/ci.yml
```

The code follows a layered design: **routers** handle HTTP, **services** hold the business rules, and **models** map to the database. Services do not know about HTTP; they raise domain exceptions that are translated into responses in one central place.

## Getting started

### Option 1: Docker (recommended)

```bash
git clone https://github.com/rcayroc02/API-task-manager.git
cd API-task-manager
cp .env.example .env        # then set a real SECRET_KEY
docker compose up --build
```

The API will be available at <http://localhost:8000/docs>. Migrations are applied automatically on startup.

> The database credentials in `docker-compose.yml` are for local development only.

### Option 2: Local development

Requirements: Python 3.12+ and Docker (for PostgreSQL).

```bash
# Create and activate an environment (conda shown; venv works too)
conda create -n task-api python=3.12 -y
conda activate task-api

# Install dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env

# Start only the database
docker compose up -d db

# Apply migrations
alembic upgrade head

# Run the API
uvicorn app.main:app --reload
```

Open <http://127.0.0.1:8000/docs>.

### Environment variables

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://postgres:postgres@localhost:5432/task_api` |
| `SECRET_KEY` | Key used to sign JWT tokens | output of `python -c "import secrets; print(secrets.token_hex(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |

URLs starting with `postgres://` or `postgresql://` (as provided by many hosting platforms) are automatically converted to use the `psycopg` driver.

## API overview

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/health` | Health check | No |
| `POST` | `/auth/register` | Create an account | No |
| `POST` | `/auth/login` | Get an access token | No |
| `GET` | `/auth/me` | Current user profile | Yes |
| `POST` | `/tasks` | Create a task | Yes |
| `GET` | `/tasks` | List your tasks | Yes |
| `GET` | `/tasks/{id}` | Get one task | Yes |
| `PATCH` | `/tasks/{id}` | Update a task partially | Yes |
| `DELETE` | `/tasks/{id}` | Delete a task | Yes |

### List query parameters

| Parameter | Values | Default |
|---|---|---|
| `status` | `pending`, `in_progress`, `done` | all |
| `order_by` | `created_at`, `due_date` | `created_at` |
| `direction` | `asc`, `desc` | `asc` |
| `limit` | 1 to 100 | 20 |
| `offset` | 0 or more | 0 |

When ordering by `due_date`, tasks without a due date are placed last.

### Example requests

```bash
# Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}'

# Log in and store the token
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "password123"}' \
  | python -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Create a task
curl -X POST http://localhost:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Learn FastAPI", "due_date": "2026-12-01T12:00:00Z"}'

# List pending tasks, sorted by due date
curl "http://localhost:8000/tasks?status=pending&order_by=due_date" \
  -H "Authorization: Bearer $TOKEN"

# Mark a task as done
curl -X PATCH http://localhost:8000/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

On Windows PowerShell, the easiest way to try the API is through Swagger UI at `/docs`: log in, click **Authorize**, and paste the token.

### Error responses

| Status | Meaning |
|---|---|
| `401` | Missing, invalid or expired token; wrong credentials |
| `404` | Task not found (also returned for tasks that belong to another user) |
| `409` | Email already registered |
| `422` | Invalid input (short password, empty title, unknown status, null in a required field) |

## Running tests

```bash
pip install -r requirements.txt
pytest --cov=app --cov-report=term-missing
```

Tests use an in-memory SQLite database, so no Docker or PostgreSQL is required. Each test starts with empty tables and does not depend on the others.

Current coverage: **XX%** (the CI fails below 80%).

The suite covers authentication, password hashing and JWT handling, the full task CRUD, pagination, filtering, validation errors and, importantly, **isolation between users**.

## Code quality and CI

```bash
ruff check .
ruff format --check .
```

On every push to `main` and on every pull request, GitHub Actions:

1. Installs dependencies
2. Runs Ruff (lint and format check)
3. Applies the migrations to a real PostgreSQL service
4. Checks that the models and the migrations are in sync (`alembic check`)
5. Runs the tests with a minimum coverage threshold
6. Builds the Docker image

## Design decisions

- **Layered architecture.** Separating routers, services and models keeps each part small, testable and easy to change.
- **404 instead of 403 for other users' tasks.** Responding the same way as for a nonexistent task avoids revealing which task IDs exist.
- **Same error for unknown email and wrong password.** Login does not reveal which emails are registered.
- **Argon2 for passwords.** It is the current recommended algorithm, with automatic salting.
- **Alembic from day one.** The schema is versioned and reproducible, and CI verifies that migrations match the models.
- **Stable pagination.** The list is ordered with the task `id` as a tiebreaker, so pages never repeat or skip rows.
- **SQLite for tests, PostgreSQL for migrations in CI.** Tests stay fast and self-contained, while migrations are still validated against the real engine.
- **Configuration through environment variables.** No secrets live in the repository.

## Possible improvements

- Refresh tokens and logout
- Rate limiting on authentication endpoints
- Task categories or tags (many-to-many)
- Structured logging
- Async endpoints with SQLAlchemy async
- Separate `requirements-dev.txt` to keep the Docker image smaller
- Run the full test suite against PostgreSQL in CI

## License

This project is for learning and portfolio purposes.
