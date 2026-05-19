# Ground Control Station — CMP9134 Software Engineering

A web-based Robot Management System that connects to a Virtual Robot simulation,
providing real-time telemetry, navigation control, and mission auditing through
a secure, role-based dashboard.

## Features

- **Real-time Dashboard**: 21×21 grid map with live robot position, battery monitoring, and sensor readings
- **WebSocket Telemetry**: Sub-second live updates with automatic reconnection and exponential backoff
- **JWT Authentication**: Secure registration and login with bcrypt password hashing
- **Role-Based Access Control (RBAC)**: Viewer (read-only telemetry) and Commander (full robot control) roles
- **Mission Audit Trail**: Every command logged to PostgreSQL with timestamp, user, payload, and robot response
- **Resilient Communication**: Automatic retry with exponential backoff for robot API 503 outages
- **Containerised Deployment**: Full Docker Compose stack with health checks and startup ordering
- **CI/CD Pipeline**: GitHub Actions for testing, linting, Docker builds, and integration smoke tests

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR-USERNAME/YOUR-REPO.git
cd YOUR-REPO

# Start all services (robot API, backend, database, frontend)
docker compose up --build

# Open the dashboard
open http://localhost:8080
```

Register an account, then login. Commanders can move the robot; Viewers can only observe.

## Architecture

```
Browser → Nginx (frontend + reverse proxy) → FastAPI (backend) → Robot API
                                                  ↓
                                             PostgreSQL (audit log + users)
```

## Project Structure

```
├── .github/workflows/ci.yml   # CI/CD pipeline (test, lint, build, integration)
├── backend/
│   ├── Dockerfile              # Multi-stage: base / development / production
│   ├── main.py                 # FastAPI routes with RBAC and audit logging
│   ├── auth.py                 # JWT authentication and role-based guards
│   ├── database.py             # SQLAlchemy models (User, MissionLog)
│   ├── robot_client.py         # Async HTTP client with retry logic
│   ├── legacy_stats.py         # Mission statistics module
│   └── tests/                  # pytest unit and integration tests
├── frontend/
│   ├── Dockerfile              # Nginx serving static files
│   ├── nginx.conf              # Reverse proxy for /api/ and /ws/
│   └── public/index.html       # Dashboard with auth, RBAC UI, audit log
├── documentation/
│   ├── ARCHITECTURE.md         # System architecture and design patterns
│   └── doc.md                  # License audit and component interfaces
└── docker-compose.yml          # Full stack orchestration
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla JS, HTML5, CSS3 |
| Web Server | Nginx 1.27-alpine |
| Backend | Python 3.12, FastAPI, httpx |
| Auth | python-jose (JWT), passlib (bcrypt) |
| Database | PostgreSQL 16, SQLAlchemy |
| Containerisation | Docker, Docker Compose |
| CI/CD | GitHub Actions |
| Testing | pytest, pytest-asyncio, pytest-cov |

## Running Tests

```bash
cd backend
pip install -r requirements.txt
pytest -v --tb=short --cov=. --cov-report=term-missing
```
