"""Factory pattern for executing Calculation operations.

Maps a CalculationType enum value to the correct arithmetic logic and
computes the result.  This separates the "which operation" decision from
both the HTTP layer and the persistence layer.
"""
from app.schemas import CalculationType
from app.exceptions import DivisionByZeroError, OperationError


class CalculationFactory:
    """Selects and executes the correct arithmetic operation for a Calculation."""

    @staticmethod
    def compute(calc_type: CalculationType, a: float, b: float) -> float:
        """Execute the arithmetic operation and return the result.

        Args:
            calc_type: One of the CalculationType enum values.
            a: Left-hand operand.
            b: Right-hand operand.

        Returns:
            The numeric result of the operation.

        Raises:
            DivisionByZeroError: When dividing by zero.
            OperationError: When an unknown type is supplied.
        """
        if calc_type == CalculationType.add:
            return a + b
        if calc_type == CalculationType.sub:
            return a - b
        if calc_type == CalculationType.multiply:
            return a * b
        if calc_type == CalculationType.divide:
            if b == 0:
                raise DivisionByZeroError("Division by zero is not allowed.")
            return a / b
        raise OperationError(f"Unknown calculation type: {calc_type}")
