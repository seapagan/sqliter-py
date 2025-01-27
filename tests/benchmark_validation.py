"""Benchmark tests for validation performance."""

# ruff: noqa: T201
import timeit
from datetime import datetime, timezone
from typing import Any

from pydantic import ConfigDict

from sqliter.model import BaseDBModel


class ValidatedModel(BaseDBModel):
    """Model with validation enabled."""

    str_field: str
    int_field: int
    list_field: list[str]
    dict_field: dict[str, Any]
    date_field: datetime


class UnvalidatedModel(BaseDBModel):
    """Model with validation disabled."""

    str_field: str
    int_field: int
    list_field: list[str]
    dict_field: dict[str, Any]
    date_field: datetime

    model_config = ConfigDict(
        validate_assignment=False,
    )


def run_benchmarks(num_iterations: int = 10000) -> None:
    """Run performance benchmarks.

    Args:
        num_iterations: Number of iterations for each test.
    """
    # Test data
    test_data = {
        "str_field": "test",
        "int_field": 42,
        "list_field": ["a", "b", "c"],
        "dict_field": {"key": "value"},
        "date_field": datetime.now(timezone.utc),
        "pk": 1,
    }

    # Initialize models
    validated = ValidatedModel(**test_data)
    unvalidated = UnvalidatedModel(**test_data)

    # Benchmark 1: Model Creation
    create_validated = timeit.timeit(
        lambda: ValidatedModel(**test_data),
        number=num_iterations,
    )
    create_unvalidated = timeit.timeit(
        lambda: UnvalidatedModel(**test_data),
        number=num_iterations,
    )

    # Benchmark 2: Single Field Assignment
    assign_validated = timeit.timeit(
        lambda: setattr(validated, "str_field", "new value"),
        number=num_iterations,
    )
    assign_unvalidated = timeit.timeit(
        lambda: setattr(unvalidated, "str_field", "new value"),
        number=num_iterations,
    )

    # Benchmark 3: Complex Field Assignment
    complex_data = ["item1", "item2", "item3"]
    assign_complex_validated = timeit.timeit(
        lambda: setattr(validated, "list_field", complex_data),
        number=num_iterations,
    )
    assign_complex_unvalidated = timeit.timeit(
        lambda: setattr(unvalidated, "list_field", complex_data),
        number=num_iterations,
    )

    # Print results
    print(f"\nBenchmark Results ({num_iterations:,} iterations each):")
    print("-" * 60)
    print("1. Model Creation:")
    print(f"   With validation:    {create_validated:.4f} seconds")
    print(f"   Without validation: {create_unvalidated:.4f} seconds")
    overhead = (create_validated / create_unvalidated) - 1
    print(f"   Overhead: {overhead * 100:.1f}%")
    print("\n2. Simple Field Assignment (str):")
    print(f"   With validation:    {assign_validated:.4f} seconds")
    print(f"   Without validation: {assign_unvalidated:.4f} seconds")
    overhead = (assign_validated / assign_unvalidated) - 1
    print(f"   Overhead: {overhead * 100:.1f}%")
    print("\n3. Complex Field Assignment (list):")
    print(f"   With validation:    {assign_complex_validated:.4f} seconds")
    print(f"   Without validation: {assign_complex_unvalidated:.4f} seconds")
    overhead = (assign_complex_validated / assign_complex_unvalidated) - 1
    print(f"   Overhead: {overhead * 100:.1f}%")


if __name__ == "__main__":
    run_benchmarks()
