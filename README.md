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


