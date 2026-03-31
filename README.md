# FastAPI Calculator — Midterm Project

A full-stack calculator application built with **FastAPI** and tested with unit, integration, and end-to-end (Playwright) tests. Includes structured logging and a GitHub Actions CI pipeline.

---

## Features

- **Web UI** — browser-based calculator with live results and history table
- **REST API** — JSON endpoints for all arithmetic operations
- **10 operations** — addition, subtraction, multiplication, division, power, root, modulus, integer division, percent, absolute difference
- **Logging** — all requests and errors logged to `data/logs/fastapi_calculator.log`
- **81 tests** — unit, integration, and end-to-end
- **GitHub Actions CI** — runs all tests automatically on every push

---

## Project Structure

```
Midterm_Project-main/
├── fastapi_app.py              # FastAPI application (routes + logging)
├── templates/
│   └── index.html              # Web UI (HTML + JavaScript)
├── app/
│   ├── operations.py           # All math operation classes + factory
│   ├── calculation.py          # Calculator facade
│   ├── calculator_repl.py      # Original CLI REPL interface
│   ├── exceptions.py           # Custom exception classes
│   └── ...                     # Config, history, commands, observers
├── tests/
│   ├── test_unit_operations.py     # Unit tests for operations.py
│   ├── test_integration_api.py     # Integration tests for API endpoints
│   ├── test_e2e_playwright.py      # End-to-end browser tests
│   └── ...                         # Original CLI test suite
├── conftest.py                 # Shared pytest fixtures (live server)
├── .github/workflows/ci.yml    # GitHub Actions CI workflow
├── requirements.txt
└── pytest.ini
```

---

## Supported Operations

| Operation | API name | Example |
|---|---|---|
| Addition | `add` | `5 + 3 = 8` |
| Subtraction | `sub` | `10 − 4 = 6` |
| Multiplication | `mul` | `6 × 7 = 42` |
| Division | `div` | `20 ÷ 4 = 5` |
| Power | `pow` | `2 ^ 10 = 1024` |
| Root | `root` | `∛27 = 3` |
| Modulus | `mod` | `10 % 3 = 1` |
| Integer Division | `int_divide` | `10 // 3 = 3` |
| Percentage | `percent` | `(50/200)×100 = 25%` |
| Absolute Difference | `abs_diff` | `\|3 − 10\| = 7` |

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

## Running the Web Application

```bash
uvicorn fastapi_app:app --reload
```

Open `http://127.0.0.1:8000` in your browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Calculator web UI |
| `POST` | `/calculate` | Perform a calculation (form data: `operation`, `a`, `b`) |
| `GET` | `/history` | Retrieve calculation history (JSON) |
| `DELETE` | `/history` | Clear calculation history |
| `GET` | `/operations` | List all supported operation names |
| `GET` | `/health` | Health check |

### Example — POST /calculate

```bash
curl -X POST http://127.0.0.1:8000/calculate \
  -d "operation=add&a=5&b=3"
```

```json
{"result": 8.0, "operation": "add", "a": 5.0, "b": 3.0}
```

---

## Running Tests

### Unit + Integration tests

```bash
python -m pytest tests/test_unit_operations.py tests/test_integration_api.py -v
```

### End-to-End tests (requires the browser)

```bash
python -m pytest tests/test_e2e_playwright.py -v --browser chromium
```

### All new tests together

```bash
python -m pytest tests/test_unit_operations.py tests/test_integration_api.py tests/test_e2e_playwright.py -v --browser chromium
```

### Run with coverage

```bash
pytest --cov=app --cov-report=term-missing
```

---

## Test Summary

| Test file | Type | Tests |
|---|---|---|
| `test_unit_operations.py` | Unit | 43 |
| `test_integration_api.py` | Integration | 25 |
| `test_e2e_playwright.py` | End-to-End | 13 |
| **Total** | | **81** |

---

## Logging

All operations and errors are logged to:

```
data/logs/fastapi_calculator.log
```

Log format:
```
2025-01-01 12:00:00 | INFO | Calculation request: 5.0 add 3.0
2025-01-01 12:00:00 | INFO | Result: 5.0 add 3.0 = 8.0
```

---

## Continuous Integration

GitHub Actions runs all three test suites automatically on every push or pull request to `main`/`master`.

Workflow file: `.github/workflows/ci.yml`

Steps:
1. Checkout repository
2. Set up Python 3.11
3. Install dependencies
4. Install Playwright Chromium browser
5. Run unit tests
6. Run integration tests
7. Run end-to-end tests

---

## Design Patterns (CLI Calculator)

The underlying calculator library (`app/`) demonstrates several design patterns:

| Pattern | Where used |
|---|---|
| **Factory** | `OperationFactory` — creates operation instances by name |
| **Facade** | `CalculatorFacade` — unified interface over history, memento, observers |
| **Command** | `commands.py` — each REPL action is an encapsulated command object |
| **Observer** | `observers.py` — logging and auto-save observers |
| **Memento** | `calculator_memento.py` — undo/redo state management |
| **Decorator** | `@OperationFactory.register(...)` — registers operations at class definition |

---

## Author

Isha Jagtap  
Master's in Computer Science — NJIT
