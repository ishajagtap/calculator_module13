# FastAPI Calculator — Midterm Project

A full-stack calculator application built with **FastAPI**, featuring a **secure user model**, a **Calculation model** with factory pattern, PostgreSQL (SQLAlchemy + bcrypt hashing), Pydantic schema validation, and a full CI/CD pipeline via GitHub Actions and Docker Hub.

---

## Features

- **Web UI** — browser-based calculator with live results and history table
- **REST API** — JSON endpoints for all arithmetic operations
- **Secure User Model** — SQLAlchemy ORM model with bcrypt-hashed passwords, unique constraints on `username` and `email`
- **Calculation Model** — SQLAlchemy ORM model storing `a`, `b`, `type`, and `result` with optional `user_id` foreign key
- **Pydantic Schemas** — `UserCreate`, `UserRead`, `CalculationCreate` (with divide-by-zero validation), `CalculationRead`
- **Factory Pattern** — `CalculationFactory` selects and executes the correct arithmetic operation (Add, Sub, Multiply, Divide)
- **10 operations** — addition, subtraction, multiplication, division, power, root, modulus, integer division, percent, absolute difference
- **Logging** — all requests and errors logged to `data/logs/fastapi_calculator.log`
- **Tests** — unit tests (no DB), integration tests (Postgres), and end-to-end tests (Playwright)
- **GitHub Actions CI** — runs all tests on every push; pushes Docker image to Docker Hub on success
- **Docker Hub** — image available at: `https://hub.docker.com/r/ishajagtap/fastapi-calculator`

---

## Project Structure

```
Midterm_Project-main/
├── fastapi_app.py                      # FastAPI application (routes + logging)
├── app/
│   ├── database.py                     # SQLAlchemy engine, session, Base
│   ├── models.py                       # User + Calculation ORM models
│   ├── schemas.py                      # Pydantic: UserCreate, UserRead, CalculationCreate, CalculationRead
│   ├── calculation_factory.py          # CalculationFactory — factory pattern for arithmetic operations
│   ├── security.py                     # hash_password() and verify_password() (bcrypt)
│   ├── operations.py                   # Math operation classes + OperationFactory
│   ├── calculation.py                  # Calculator facade
│   └── ...                             # Config, history, commands, observers, exceptions
├── tests/
│   ├── test_calculation_unit.py        # Unit tests: CalculationCreate schema, CalculationFactory (no DB)
│   ├── test_calculation_integration.py # Integration tests: Calculation DB model + error cases (Postgres)
│   ├── test_user_unit.py               # Unit tests: hashing, UserCreate/UserRead schema (no DB)
│   ├── test_user_integration.py        # Integration tests: User DB model + /users API (Postgres)
│   ├── test_unit_operations.py         # Unit tests for math operations
│   ├── test_integration_api.py         # Integration tests for calculator API
│   ├── test_e2e_playwright.py          # End-to-end browser tests
│   └── ...                             # Additional CLI test suite
├── templates/
│   └── index.html                      # Web UI
├── .github/workflows/ci.yml            # GitHub Actions CI + Docker Hub push
├── docker-compose.yml                  # Local Postgres + pgAdmin + app
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

---

## Calculation Model

### SQLAlchemy Model (`app/models.py`)

| Column       | Type        | Constraints                        |
|--------------|-------------|------------------------------------|
| `id`         | Integer     | Primary key, auto-increment        |
| `user_id`    | Integer     | Foreign key → `users.id`, nullable |
| `a`          | Float       | Not null — left operand            |
| `b`          | Float       | Not null — right operand           |
| `type`       | String(20)  | Not null — `add`, `sub`, `multiply`, `divide` |
| `result`     | Float       | Not null — computed and stored     |
| `created_at` | DateTime    | Default: `utcnow`                  |

### Pydantic Schemas (`app/schemas.py`)

- **`CalculationCreate`** — accepts `a`, `b`, `type` (must be one of `add`, `sub`, `multiply`, `divide`), optional `user_id`. Raises a validation error if `type` is `divide` and `b` is `0`.
- **`CalculationRead`** — returns `id`, `a`, `b`, `type`, `result`, `user_id`, `created_at`.

### CalculationFactory (`app/calculation_factory.py`)

A factory class that maps a `CalculationType` enum to the correct arithmetic logic:

```python
from app.calculation_factory import CalculationFactory
from app.schemas import CalculationType

result = CalculationFactory.compute(CalculationType.add, 3, 4)      # 7
result = CalculationFactory.compute(CalculationType.multiply, 6, 7) # 42
result = CalculationFactory.compute(CalculationType.divide, 10, 2)  # 5.0
```

---

## Secure User Model

### SQLAlchemy Model (`app/models.py`)

| Column          | Type         | Constraints              |
|-----------------|--------------|--------------------------|
| `id`            | Integer      | Primary key, auto-increment |
| `username`      | String(50)   | Unique, not null         |
| `email`         | String(100)  | Unique, not null         |
| `password_hash` | String(255)  | Not null (bcrypt hash)   |
| `created_at`    | DateTime     | Default: `utcnow`        |

### Pydantic Schemas (`app/schemas.py`)

- **`UserCreate`** — accepts `username`, `email` (validated), `password` (min 6 chars)
- **`UserRead`** — returns `id`, `username`, `email`, `created_at`; **never** exposes `password_hash`

### Password Hashing (`app/security.py`)

```python
from app.security import hash_password, verify_password

hashed = hash_password("my_secret")       # bcrypt hash
verify_password("my_secret", hashed)      # True
verify_password("wrong_password", hashed) # False
```

### User API Endpoints

| Method | Endpoint         | Description                         |
|--------|------------------|-------------------------------------|
| `POST` | `/users`         | Register a new user (returns 201)   |
| `GET`  | `/users/{id}`    | Retrieve a user by ID               |

Example — create a user:
```bash
curl -X POST http://127.0.0.1:8000/users \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","email":"alice@example.com","password":"secret123"}'
```
```json
{"id": 1, "username": "alice", "email": "alice@example.com", "created_at": "2024-01-01T12:00:00"}
```

---

## Installation

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd Midterm_Project-main
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac/Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Playwright browser

```bash
playwright install chromium
```

---

## Running the Application

### With Docker Compose (recommended — includes Postgres)

```bash
docker-compose up --build
```

Open `http://127.0.0.1:8000` in your browser.  
pgAdmin is available at `http://localhost:5050` (admin@admin.com / admin).

### Without Docker (requires local Postgres)

```bash
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db

# Mac/Linux
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db

uvicorn fastapi_app:app --reload
```

---

## Running Tests Locally

### Start the database first (for integration tests)

```bash
docker-compose up db -d
```

### Unit tests — no database required

```bash
pytest tests/test_unit_operations.py tests/test_user_unit.py tests/test_calculation_unit.py -v
```

### Integration tests — calculator API (no database required)

```bash
pytest tests/test_integration_api.py -v
```

### Integration tests — user model (requires Postgres)

```bash
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
pytest tests/test_user_integration.py -v

# Mac/Linux
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
  pytest tests/test_user_integration.py -v
```

### Integration tests — calculation model (requires Postgres)

```bash
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
pytest tests/test_calculation_integration.py -v

# Mac/Linux
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
  pytest tests/test_calculation_integration.py -v
```

### End-to-end tests (requires Playwright browser)

```bash
pytest tests/test_e2e_playwright.py -v --browser chromium
```

### All tests with coverage

```bash
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
pytest tests/ -v --browser chromium --cov=app --cov-report=term-missing

# Mac/Linux
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
  pytest tests/ -v --browser chromium --cov=app --cov-report=term-missing
```

---

## CI/CD Pipeline

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs on every push/PR to `main`:

1. **Spin up a Postgres 15 service container** — available at `localhost:5432`
2. **Install Python 3.11 and all dependencies**
3. **Install Playwright Chromium**
4. **Run unit tests** (`test_unit_operations.py`, `test_user_unit.py`, `test_calculation_unit.py`)
5. **Run calculator integration tests** (`test_integration_api.py`)
6. **Run user integration tests** (`test_user_integration.py`) — uses the Postgres container
7. **Run calculation integration tests** (`test_calculation_integration.py`) — uses the Postgres container
8. **Run end-to-end tests** (`test_e2e_playwright.py`)
9. **Build and push Docker image to Docker Hub** — only on push to `main`/`master`, only after all tests pass

### Setting up Docker Hub secrets

Add these two secrets to your GitHub repository (**Settings → Secrets and variables → Actions**):

| Secret name          | Value                            |
|----------------------|----------------------------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username         |
| `DOCKERHUB_TOKEN`    | A Docker Hub access token        |

Generate a Docker Hub token at: **Docker Hub → Account Settings → Security → New Access Token**

---

## Docker Hub

Image: `https://hub.docker.com/r/ishajagtap/fastapi-calculator`

Pull and run:
```bash
docker pull ishajagtap/fastapi-calculator:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db \
  ishajagtap/fastapi-calculator:latest
```

---

## Supported Calculator Operations

| Operation         | API name     | Example              |
|-------------------|--------------|----------------------|
| Addition          | `add`        | `5 + 3 = 8`          |
| Subtraction       | `sub`        | `10 − 4 = 6`         |
| Multiplication    | `mul`        | `6 × 7 = 42`         |
| Division          | `div`        | `20 ÷ 4 = 5`         |
| Power             | `pow`        | `2 ^ 10 = 1024`      |
| Root              | `root`       | `∛27 = 3`            |
| Modulus           | `mod`        | `10 % 3 = 1`         |
| Integer Division  | `int_divide` | `10 // 3 = 3`        |
| Percentage        | `percent`    | `(50/200)×100 = 25%` |
| Absolute Diff     | `abs_diff`   | `|3 − 10| = 7`       |

---

## API Endpoints

| Method   | Endpoint       | Description                             |
|----------|----------------|-----------------------------------------|
| `GET`    | `/`            | Calculator web UI                       |
| `POST`   | `/calculate`   | Perform a calculation                   |
| `GET`    | `/history`     | Retrieve calculation history (JSON)     |
| `DELETE` | `/history`     | Clear calculation history               |
| `GET`    | `/operations`  | List all supported operation names      |
| `GET`    | `/health`      | Health check                            |
| `POST`   | `/users`       | Register a new user                     |
| `GET`    | `/users/{id}`  | Retrieve a user by ID                   |

---

## Design Patterns

| Pattern     | Where used                                                                        |
|-------------|-----------------------------------------------------------------------------------|
| **Factory** | `CalculationFactory` — maps `CalculationType` enum to arithmetic logic            |
| **Factory** | `OperationFactory` — creates REPL/API operation instances by name                 |
| **Facade**  | `CalculatorFacade` — unified interface over history, memento, observers           |
| **Command** | `commands.py` — each REPL action is an encapsulated command object                |
| **Observer**| `observers.py` — logging and auto-save observers                                  |
| **Memento** | `calculator_memento.py` — undo/redo state management                              |

---

## Author

Isha Jagtap  
Master's in Computer Science — NJIT
