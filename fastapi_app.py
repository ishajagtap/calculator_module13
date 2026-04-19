"""FastAPI Calculator Application."""
import logging
import os
from pathlib import Path
from fastapi import FastAPI, Request, Form, Depends, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.operations import OperationFactory
from app.exceptions import DivisionByZeroError, OperationError
from app.database import engine, get_db
from app.models import User, Calculation, Base
from app.schemas import (
    UserCreate,
    UserRead,
    UserLogin,
    CalculationCreate,
    CalculationRead,
    CalculationUpdate,
)
from app.security import hash_password, verify_password

# ── Logging Setup ──────────────────────────────────────────────────────────────
log_dir = Path("data/logs")
log_dir.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "fastapi_calculator.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

# ── App Setup ──────────────────────────────────────────────────────────────────
app = FastAPI(title="FastAPI Calculator", description="A calculator API built with FastAPI")
templates = Jinja2Templates(directory="templates")

# Create database tables on startup
Base.metadata.create_all(bind=engine)

# In-memory history (list of dicts)
calculation_history: list[dict] = []

# ── Routes ─────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Serve the calculator web UI."""
    logger.info("Serving calculator home page")
    return templates.TemplateResponse(
        request, "index.html", {"history": calculation_history}
    )


@app.post("/calculate")
async def calculate(
    operation: str = Form(...),
    a: float = Form(...),
    b: float = Form(...),
):
    """Perform a calculation and return the result."""
    logger.info("Calculation request: %s %s %s", a, operation, b)
    try:
        op = OperationFactory.create(operation)
        result = op.execute(a, b)
        entry = {"operation": operation, "a": a, "b": b, "result": result}
        calculation_history.append(entry)
        logger.info("Result: %s %s %s = %s", a, operation, b, result)
        return JSONResponse({"result": result, "operation": operation, "a": a, "b": b})
    except DivisionByZeroError as exc:
        logger.error("Division by zero: %s %s %s — %s", a, operation, b, exc)
        return JSONResponse({"error": str(exc)}, status_code=400)
    except OperationError as exc:
        logger.error("Operation error: %s %s %s — %s", a, operation, b, exc)
        return JSONResponse({"error": str(exc)}, status_code=400)
    except Exception as exc:  # pragma: no cover
        logger.error("Unexpected error: %s", exc)
        return JSONResponse({"error": f"Unexpected error: {exc}"}, status_code=500)


@app.get("/history")
async def get_history():
    """Return the full calculation history."""
    logger.info("History requested (%d entries)", len(calculation_history))
    return {"history": calculation_history}


@app.delete("/history")
async def clear_history():
    """Clear all calculation history."""
    calculation_history.clear()
    logger.info("History cleared")
    return {"message": "History cleared"}


@app.get("/health")
async def health_check():
    """Health-check endpoint used by tests and CI."""
    return {"status": "ok"}


# ── User Routes ────────────────────────────────────────────────────────────────

@app.post("/users/register", response_model=UserRead, status_code=201)
def register_user(user_in: UserCreate, db: Session = Depends(get_db)):
    """Register a new user with a hashed password."""
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hash_password(user_in.password),
    )
    db.add(db_user)
    try:
        db.commit()
        db.refresh(db_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username or email already registered")
    logger.info("New user registered: %s", db_user.username)
    return db_user


@app.post("/users/login")
def login(user_in: UserLogin, db: Session = Depends(get_db)):
    """Verify user credentials."""
    user = db.query(User).filter(User.username == user_in.username).first()
    if not user or not verify_password(user_in.password, user.password_hash):
        logger.warning("Failed login attempt for user: %s", user_in.username)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    logger.info("User logged in: %s", user.username)
    return {"message": "Login successful", "user_id": user.id, "username": user.username}


@app.get("/users/{user_id}", response_model=UserRead)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Retrieve a user by their ID (password_hash is never returned)."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@app.get("/operations")
async def list_operations():
    """List all supported operation names."""
    ops = sorted(OperationFactory._operations.keys())
    return {"operations": ops}


# ── Calculation CRUD (BREAD) ──────────────────────────────────────────────────

@app.post("/calculations", response_model=CalculationRead, status_code=201)
def add_calculation(calc_in: CalculationCreate, db: Session = Depends(get_db)):
    """Add a new calculation (Create)."""
    try:
        # Use CalculationFactory to ensure consistent results
        op = OperationFactory.create(calc_in.type.value)
        result = op.execute(calc_in.a, calc_in.b)
        
        db_calc = Calculation(
            a=calc_in.a,
            b=calc_in.b,
            type=calc_in.type.value,
            result=result,
            user_id=calc_in.user_id
        )
        db.add(db_calc)
        db.commit()
        db.refresh(db_calc)
        logger.info("Calculation added: %s", db_calc.id)
        return db_calc
    except (DivisionByZeroError, OperationError) as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.get("/calculations", response_model=list[CalculationRead])
def browse_calculations(db: Session = Depends(get_db)):
    """List all calculations (Browse)."""
    return db.query(Calculation).all()


@app.get("/calculations/{calc_id}", response_model=CalculationRead)
def read_calculation(calc_id: int, db: Session = Depends(get_db)):
    """Retrieve a single calculation (Read)."""
    db_calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    return db_calc


@app.put("/calculations/{calc_id}", response_model=CalculationRead)
def edit_calculation(calc_id: int, calc_update: CalculationUpdate, db: Session = Depends(get_db)):
    """Update an existing calculation (Edit)."""
    db_calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    
    # Update fields if provided
    if calc_update.a is not None:
        db_calc.a = calc_update.a
    if calc_update.b is not None:
        db_calc.b = calc_update.b
    if calc_update.type is not None:
        db_calc.type = calc_update.type.value
    if calc_update.user_id is not None:
        db_calc.user_id = calc_update.user_id
        
    # Re-calculate result
    try:
        op = OperationFactory.create(db_calc.type)
        db_calc.result = op.execute(db_calc.a, db_calc.b)
        db.commit()
        db.refresh(db_calc)
        logger.info("Calculation updated: %s", db_calc.id)
        return db_calc
    except (DivisionByZeroError, OperationError) as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))


@app.delete("/calculations/{calc_id}", status_code=204)
def delete_calculation(calc_id: int, db: Session = Depends(get_db)):
    """Delete a calculation (Delete)."""
    db_calc = db.query(Calculation).filter(Calculation.id == calc_id).first()
    if not db_calc:
        raise HTTPException(status_code=404, detail="Calculation not found")
    db.delete(db_calc)
    db.commit()
    logger.info("Calculation deleted: %s", calc_id)
    return None
