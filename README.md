# FastAPI Calculator

A full-stack calculator application built with **FastAPI**, **PostgreSQL**, **JWT authentication**, and a browser-based UI. Includes a complete CI/CD pipeline via GitHub Actions and Docker Hub.

---

## Features

- **Login-gated UI** — landing page is the login form; the calculator is only accessible after authentication
- **JWT Authentication** — register, login, and receive a signed access token stored in `localStorage`
- **10 Calculator Operations** — add, subtract, multiply, divide, power, root, modulus, integer division, percent, absolute difference
- **Calculation CRUD** — full Browse / Read / Add / Edit / Delete API for persisted calculations
- **Secure User Model** — bcrypt-hashed passwords, never exposed in responses
- **Factory Pattern** — `OperationFactory` and `CalculationFactory` map names/enums to arithmetic logic
- **Logging** — all requests and errors written to `data/logs/fastapi_calculator.log`
- **Tests** — unit, integration (Postgres), and end-to-end (Playwright)
- **CI/CD** — GitHub Actions runs all tests on every push and publishes a Docker image to Docker Hub on success

---

## Page Flow

```
http://localhost:8000/
        │
        ▼ (redirect)
http://localhost:8000/login
        │
        │  valid credentials → JWT stored in localStorage
        ▼
http://localhost:8000/calculator
        │
        │  Logout button → clears token
        ▼
http://localhost:8000/login
```

- Visiting `/` redirects to `/login`
- Visiting `/calculator` without a token redirects to `/login`
- After login, the browser navigates to `/calculator`

---

## Project Structure

```
├── fastapi_app.py                      # FastAPI routes and logging
├── app/
│   ├── database.py                     # SQLAlchemy engine, session, Base
│   ├── models.py                       # User + Calculation ORM models
│   ├── schemas.py                      # Pydantic schemas
│   ├── security.py                     # hash_password / verify_password (bcrypt) + JWT
│   ├── operations.py                   # Math operation classes + OperationFactory
│   ├── calculation_factory.py          # CalculationFactory (factory pattern)
│   ├── calculation.py                  # Calculator facade
│   └── ...                             # Config, history, commands, observers, exceptions
├── templates/
│   ├── login.html                      # Login page (landing)
│   ├── register.html                   # Registration page
│   └── index.html                      # Calculator UI (auth-gated)
├── tests/
│   ├── test_user_unit.py               # Unit: hashing, UserCreate/UserRead schemas
│   ├── test_user_integration.py        # Integration: User DB model + /users API
│   ├── test_calculation_unit.py        # Unit: CalculationCreate schema, CalculationFactory
│   ├── test_calculation_integration.py # Integration: Calculation DB model
│   ├── test_unit_operations.py         # Unit: math operation classes
│   ├── test_integration_api.py         # Integration: calculator API endpoints
│   ├── test_e2e_playwright.py          # End-to-end: browser flows
│   ├── test_e2e_auth.py                # End-to-end: auth flows
│   └── ...                             # Additional branch/edge-case tests
├── .github/workflows/ci.yml            # GitHub Actions CI + Docker Hub push
├── docker-compose.yml                  # Postgres + pgAdmin + app
├── Dockerfile
├── requirements.txt
└── pytest.ini
```

---

## Data Models

### User (`app/models.py`)

| Column          | Type        | Constraints               |
|-----------------|-------------|---------------------------|
| `id`            | Integer     | Primary key, auto-increment |
| `username`      | String(50)  | Unique, not null          |
| `email`         | String(100) | Unique, not null          |
| `password_hash` | String(255) | Not null (bcrypt)         |
| `created_at`    | DateTime    | Default: `utcnow`         |

### Calculation (`app/models.py`)

| Column     | Type       | Constraints                          |
|------------|------------|--------------------------------------|
| `id`       | Integer    | Primary key, auto-increment          |
| `user_id`  | Integer    | Foreign key → `users.id`, nullable   |
| `a`        | Float      | Not null — left operand              |
| `b`        | Float      | Not null — right operand             |
| `type`     | String(20) | Not null — operation name            |
| `result`   | Float      | Not null — computed and stored       |
| `created_at` | DateTime | Default: `utcnow`                    |

---

## API Endpoints

### Auth & Pages

| Method | Endpoint    | Description                         |
|--------|-------------|-------------------------------------|
| `GET`  | `/`         | Redirects to `/login`               |
| `GET`  | `/login`    | Login page (HTML)                   |
| `GET`  | `/register` | Registration page (HTML)            |
| `GET`  | `/calculator` | Calculator UI — auth-gated (HTML) |
| `POST` | `/login`    | Verify credentials, return JWT      |
| `POST` | `/register` | Register a new user                 |
| `GET`  | `/users/{id}` | Retrieve user by ID               |

### Calculator

| Method   | Endpoint    | Description                          |
|----------|-------------|--------------------------------------|
| `POST`   | `/calculate`  | Perform a calculation (form data)  |
| `GET`    | `/history`    | In-memory calculation history      |
| `DELETE` | `/history`    | Clear in-memory history            |
| `GET`    | `/operations` | List all supported operation names |
| `GET`    | `/health`     | Health check                       |

### Calculation CRUD

| Method   | Endpoint               | Description                    |
|----------|------------------------|--------------------------------|
| `POST`   | `/calculations`        | Create and persist calculation |
| `GET`    | `/calculations`        | List all calculations          |
| `GET`    | `/calculations/{id}`   | Get a single calculation       |
| `PUT`    | `/calculations/{id}`   | Update a calculation           |
| `DELETE` | `/calculations/{id}`   | Delete a calculation           |

---

## Supported Operations

| Operation        | API name     | Example               |
|------------------|--------------|-----------------------|
| Addition         | `add`        | `5 + 3 = 8`           |
| Subtraction      | `sub`        | `10 − 4 = 6`          |
| Multiplication   | `mul`        | `6 × 7 = 42`          |
| Division         | `div`        | `20 ÷ 4 = 5`          |
| Power            | `pow`        | `2 ^ 10 = 1024`       |
| Root             | `root`       | `∛27 = 3`             |
| Modulus          | `mod`        | `10 % 3 = 1`          |
| Integer Division | `int_divide` | `10 // 3 = 3`         |
| Percentage       | `percent`    | `(50/200)×100 = 25%`  |
| Absolute Diff    | `abs_diff`   | `\|3 − 10\| = 7`      |

---

## Running the App

### Option 1 — Docker Compose (recommended)

Starts the FastAPI app, PostgreSQL, and pgAdmin in one command.

```bash
docker-compose up --build
```

| Service   | URL                        | Credentials             |
|-----------|----------------------------|-------------------------|
| App       | http://localhost:8000/login | —                      |
| pgAdmin   | http://localhost:5050       | admin@admin.com / admin |

To stop:

```bash
docker-compose down
```

### Option 2 — Local (requires Python + PostgreSQL)

```bash
# 1. Clone and enter the repo
git clone <your-repository-url>
cd Isha_Jagtap_module_13

# 2. Create and activate a virtual environment
python -m venv .venv
# Windows
.venv\Scripts\activate
# Mac/Linux
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set the database URL and start the server
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
uvicorn fastapi_app:app --reload

# Mac/Linux
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db uvicorn fastapi_app:app --reload
```

Open http://localhost:8000 — you will land on the login page.

---

## Running Tests

### Start the database (required for integration tests)

```bash
docker-compose up db -d
```

### Unit tests — no database required

```bash
pytest tests/test_unit_operations.py tests/test_user_unit.py tests/test_calculation_unit.py -v
```

### Integration tests — calculator API

```bash
pytest tests/test_integration_api.py -v
```

### Integration tests — user and calculation models (requires Postgres)

```bash
# Windows CMD
set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db
pytest tests/test_user_integration.py tests/test_calculation_integration.py tests/test_calculation_api_integration.py -v

# Mac/Linux
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/fastapi_db \
  pytest tests/test_user_integration.py tests/test_calculation_integration.py tests/test_calculation_api_integration.py -v
```

### End-to-end tests with Playwright

Install the browser once:

```bash
playwright install chromium
```

Run the E2E suite (app must be running):

```bash
pytest tests/test_e2e_playwright.py tests/test_e2e_auth.py -v --browser chromium
```

### All tests with coverage (via Docker — recommended)

```bash
docker-compose up --build -d
docker-compose exec web pytest tests/ -v --browser chromium --cov=app --cov-report=term-missing
docker-compose down
```

---

## CI/CD Pipeline

The workflow at `.github/workflows/ci.yml` runs on every push and pull request to `main`:

1. Spin up a Postgres 15 service container
2. Install Python 3.11 and all dependencies
3. Install Playwright Chromium
4. Run unit tests
5. Run calculator and user/calculation integration tests
6. Run end-to-end Playwright tests
7. Build and push Docker image to Docker Hub *(push to `main` only, after all tests pass)*

### Required GitHub Secrets

Add these in **Settings → Secrets and variables → Actions**:

| Secret               | Value                        |
|----------------------|------------------------------|
| `DOCKERHUB_USERNAME` | Your Docker Hub username     |
| `DOCKERHUB_TOKEN`    | A Docker Hub access token    |

Generate a token at: **Docker Hub → Account Settings → Security → New Access Token**

---

## Docker Hub

Image: [`ishaj2000/fastapi-calculator`](https://hub.docker.com/r/ishaj2000/fastapi-calculator)

```bash
docker pull ishajagtap/fastapi-calculator:latest
docker run -p 8000:8000 \
  -e DATABASE_URL=postgresql://postgres:postgres@host.docker.internal:5432/fastapi_db \
  ishajagtap/fastapi-calculator:latest
```

---

## Design Patterns

| Pattern      | Where used                                                          |
|--------------|---------------------------------------------------------------------|
| **Factory**  | `OperationFactory` — creates operation instances by name            |
| **Factory**  | `CalculationFactory` — maps `CalculationType` enum to arithmetic logic |
| **Facade**   | `CalculatorFacade` — unified interface over history, memento, observers |
| **Command**  | `commands.py` — each REPL action is an encapsulated command object  |
| **Observer** | `observers.py` — logging and auto-save observers                    |
| **Memento**  | `calculator_memento.py` — undo/redo state management                |

---

## Author

Isha Jagtap — Master's in Computer Science, NJIT
