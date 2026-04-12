"""Unit tests for CalculationCreate/CalculationRead schemas and CalculationFactory.

No database connection required — runs entirely in-memory.

Run:
    pytest tests/test_calculation_unit.py -v
"""
import pytest
from pydantic import ValidationError

from app.schemas import CalculationCreate, CalculationRead, CalculationType
from app.calculation_factory import CalculationFactory
from app.exceptions import DivisionByZeroError, OperationError
from datetime import datetime


# ── CalculationType Enum ───────────────────────────────────────────────────────

class TestCalculationType:
    def test_add_value(self):
        assert CalculationType.add == "add"

    def test_sub_value(self):
        assert CalculationType.sub == "sub"

    def test_multiply_value(self):
        assert CalculationType.multiply == "multiply"

    def test_divide_value(self):
        assert CalculationType.divide == "divide"

    def test_invalid_type_raises(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=1, b=2, type="modulus")


# ── CalculationCreate Schema ───────────────────────────────────────────────────

class TestCalculationCreateSchema:
    def test_valid_add(self):
        calc = CalculationCreate(a=3.0, b=4.0, type="add")
        assert calc.a == 3.0
        assert calc.b == 4.0
        assert calc.type == CalculationType.add

    def test_valid_sub(self):
        calc = CalculationCreate(a=10.0, b=3.0, type="sub")
        assert calc.type == CalculationType.sub

    def test_valid_multiply(self):
        calc = CalculationCreate(a=2.0, b=5.0, type="multiply")
        assert calc.type == CalculationType.multiply

    def test_valid_divide(self):
        calc = CalculationCreate(a=8.0, b=2.0, type="divide")
        assert calc.type == CalculationType.divide

    def test_divide_by_zero_raises(self):
        with pytest.raises(ValidationError) as exc_info:
            CalculationCreate(a=5.0, b=0.0, type="divide")
        assert "zero" in str(exc_info.value).lower()

    def test_add_with_zero_b_is_valid(self):
        """b=0 is only forbidden for divide, not other operations."""
        calc = CalculationCreate(a=5.0, b=0.0, type="add")
        assert calc.b == 0.0

    def test_sub_with_zero_b_is_valid(self):
        calc = CalculationCreate(a=5.0, b=0.0, type="sub")
        assert calc.b == 0.0

    def test_multiply_with_zero_b_is_valid(self):
        calc = CalculationCreate(a=5.0, b=0.0, type="multiply")
        assert calc.b == 0.0

    def test_missing_a_raises(self):
        with pytest.raises(ValidationError):
            CalculationCreate(b=2.0, type="add")

    def test_missing_b_raises(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=2.0, type="add")

    def test_missing_type_raises(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=1.0, b=2.0)

    def test_invalid_type_string_raises(self):
        with pytest.raises(ValidationError):
            CalculationCreate(a=1.0, b=2.0, type="power")

    def test_optional_user_id_defaults_to_none(self):
        calc = CalculationCreate(a=1.0, b=2.0, type="add")
        assert calc.user_id is None

    def test_user_id_can_be_set(self):
        calc = CalculationCreate(a=1.0, b=2.0, type="add", user_id=42)
        assert calc.user_id == 42

    def test_negative_operands_allowed(self):
        calc = CalculationCreate(a=-5.0, b=-3.0, type="multiply")
        assert calc.a == -5.0
        assert calc.b == -3.0

    def test_float_operands_allowed(self):
        calc = CalculationCreate(a=1.5, b=2.5, type="add")
        assert calc.a == 1.5


# ── CalculationRead Schema ─────────────────────────────────────────────────────

class TestCalculationReadSchema:
    def _base(self, **overrides):
        data = {
            "id": 1,
            "a": 3.0,
            "b": 4.0,
            "type": "add",
            "result": 7.0,
            "user_id": None,
            "created_at": datetime(2024, 6, 1, 12, 0, 0),
        }
        data.update(overrides)
        return data

    def test_valid_data_parses(self):
        calc = CalculationRead(**self._base())
        assert calc.id == 1
        assert calc.result == 7.0

    def test_user_id_can_be_none(self):
        calc = CalculationRead(**self._base(user_id=None))
        assert calc.user_id is None

    def test_user_id_can_be_set(self):
        calc = CalculationRead(**self._base(user_id=5))
        assert calc.user_id == 5

    def test_missing_id_raises(self):
        data = self._base()
        del data["id"]
        with pytest.raises(ValidationError):
            CalculationRead(**data)

    def test_missing_result_raises(self):
        data = self._base()
        del data["result"]
        with pytest.raises(ValidationError):
            CalculationRead(**data)

    def test_type_is_string(self):
        calc = CalculationRead(**self._base(type="divide"))
        assert isinstance(calc.type, str)
        assert calc.type == "divide"


# ── CalculationFactory ─────────────────────────────────────────────────────────

class TestCalculationFactory:
    def test_add(self):
        result = CalculationFactory.compute(CalculationType.add, 3, 4)
        assert result == 7

    def test_sub(self):
        result = CalculationFactory.compute(CalculationType.sub, 10, 3)
        assert result == 7

    def test_multiply(self):
        result = CalculationFactory.compute(CalculationType.multiply, 3, 4)
        assert result == 12

    def test_divide(self):
        result = CalculationFactory.compute(CalculationType.divide, 10, 2)
        assert result == 5.0

    def test_divide_by_zero_raises(self):
        with pytest.raises(DivisionByZeroError):
            CalculationFactory.compute(CalculationType.divide, 5, 0)

    def test_add_negative_numbers(self):
        result = CalculationFactory.compute(CalculationType.add, -5, -3)
        assert result == -8

    def test_sub_negative_result(self):
        result = CalculationFactory.compute(CalculationType.sub, 3, 10)
        assert result == -7

    def test_multiply_by_zero(self):
        result = CalculationFactory.compute(CalculationType.multiply, 999, 0)
        assert result == 0

    def test_divide_float_result(self):
        result = CalculationFactory.compute(CalculationType.divide, 7, 2)
        assert result == 3.5

    def test_add_floats(self):
        result = CalculationFactory.compute(CalculationType.add, 1.1, 2.2)
        assert abs(result - 3.3) < 1e-9

    def test_multiply_floats(self):
        result = CalculationFactory.compute(CalculationType.multiply, 2.5, 4.0)
        assert result == 10.0
