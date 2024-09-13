"""Test the advanced filter capabilities of the library."""

import pytest

from .conftest import PersonModel


def test_filter_with_gt_condition(db_mock_adv) -> None:
    """Test filter with greater than condition."""
    # Filter where age > 25
    results = db_mock_adv.select(PersonModel).filter(age__gt=25).fetch_all()

    assert len(results) == 2
    assert all(result.age > 25 for result in results)
    assert {result.name for result in results} == {"Bob", "Charlie"}


def test_filter_with_lt_condition(db_mock_adv) -> None:
    """Test filter with less than condition."""
    # Filter where age < 35
    results = db_mock_adv.select(PersonModel).filter(age__lt=35).fetch_all()

    assert len(results) == 2
    assert all(result.age < 35 for result in results)
    assert {result.name for result in results} == {"Alice", "Bob"}


def test_filter_with_gte_condition(db_mock_adv) -> None:
    """Test filter with greater than or equal to condition."""
    # Filter where age >= 30
    results = db_mock_adv.select(PersonModel).filter(age__gte=30).fetch_all()

    assert len(results) == 2
    assert all(result.age >= 30 for result in results)
    assert {result.name for result in results} == {"Bob", "Charlie"}


def test_filter_with_lte_condition(db_mock_adv) -> None:
    """Test filter with less than or equal to condition."""
    # Filter where age <= 30
    results = db_mock_adv.select(PersonModel).filter(age__lte=30).fetch_all()

    assert len(results) == 2
    assert all(result.age <= 30 for result in results)
    assert {result.name for result in results} == {"Alice", "Bob"}


def test_filter_with_eq_condition(db_mock_adv) -> None:
    """Test filter with equal to condition."""
    # Filter where age == 30
    results = db_mock_adv.select(PersonModel).filter(age__eq=30).fetch_all()

    assert len(results) == 1
    assert results[0].age == 30
    assert results[0].name == "Bob"


def test_filter_with_ne_condition(db_mock_adv) -> None:
    """Test filter with not equal to condition."""
    # Filter where age != 30
    results = db_mock_adv.select(PersonModel).filter(age__ne=30).fetch_all()

    assert len(results) == 2
    assert all(result.age != 30 for result in results)
    assert {result.name for result in results} == {"Alice", "Charlie"}


def test_filter_with_gt_and_lt_combined(db_mock_adv) -> None:
    """Test filter with combined greater than and less than conditions."""
    db_mock_adv.insert(PersonModel(name="David", age=40))

    # Filter where age > 25 and age < 40
    results = (
        db_mock_adv.select(PersonModel)
        .filter(age__gt=25, age__lt=40)
        .fetch_all()
    )

    assert len(results) == 2
    assert all(25 < result.age < 40 for result in results)
    assert {result.name for result in results} == {"Bob", "Charlie"}


def test_filter_with_gt_and_lte_combined(db_mock_adv) -> None:
    """Test with combined greater than and less than or equal conditions."""
    db_mock_adv.insert(PersonModel(name="David", age=40))

    # Filter where age > 25 and age <= 35
    results = (
        db_mock_adv.select(PersonModel)
        .filter(age__gt=25, age__lte=35)
        .fetch_all()
    )

    assert len(results) == 2
    assert all(25 < result.age <= 35 for result in results)
    assert {result.name for result in results} == {"Bob", "Charlie"}


def test_filter_with_is_null_condition(db_mock_adv) -> None:
    """Test filter with IS NULL condition."""
    db_mock_adv.insert(PersonModel(name="David", age=None))
    # Filter where age is NULL
    results = (
        db_mock_adv.select(PersonModel).filter(age__isnull=True).fetch_all()
    )

    assert len(results) == 1
    assert results[0].age is None
    assert results[0].name == "David"


@pytest.mark.skip(reason="fails and needs investigation")
def test_filter_with_is_not_null_condition(db_mock_adv) -> None:
    """Test filter with IS NOT NULL condition."""
    db_mock_adv.insert(PersonModel(name="David", age=None))
    # Filter where age is NOT NULL
    results = (
        db_mock_adv.select(PersonModel).filter(age__notnull=True).fetch_all()
    )

    assert len(results) == 3
    assert all(result.age is not None for result in results)
    assert {result.name for result in results} == {"Alice", "Bob", "Charlie"}


def test_filter_with_in_condition(db_mock_adv) -> None:
    """Test filter with IN condition."""
    # Filter where age IN (25, 35)
    results = (
        db_mock_adv.select(PersonModel).filter(age__in=[25, 35]).fetch_all()
    )

    assert len(results) == 2
    assert all(result.age in [25, 35] for result in results)
    assert {result.name for result in results} == {"Alice", "Charlie"}


def test_filter_with_not_in_condition(db_mock_adv) -> None:
    """Test filter with NOT IN condition."""
    # Filter where age NOT IN (25, 35)
    results = (
        db_mock_adv.select(PersonModel).filter(age__not_in=[25, 35]).fetch_all()
    )

    assert len(results) == 1
    assert results[0].age == 30
    assert results[0].name == "Bob"


def test_filter_with_bad_in_condition(db_mock_adv) -> None:
    """Test filter with bad IN condition."""
    with pytest.raises(ValueError, match="age requires a list") as exc_info:
        db_mock_adv.select(PersonModel).filter(age__in=25).fetch_all()

    assert str(exc_info.value) == "age requires a list for '__in'"


def test_filter_with_bad_not_in_condition(db_mock_adv) -> None:
    """Test filter with bad NOT IN condition."""
    with pytest.raises(ValueError, match="age requires a list") as exc_info:
        db_mock_adv.select(PersonModel).filter(age__not_in=25).fetch_all()

    assert str(exc_info.value) == "age requires a list for '__not_in'"


@pytest.mark.skip(reason="fails and needs investigation")
def test_filter_with_starts_with_condition(db_mock_adv) -> None:
    """Test filter with starts with condition."""
    # Filter where name starts with 'A'
    results = (
        db_mock_adv.select(PersonModel).filter(name__startswith="A").fetch_all()
    )

    assert len(results) == 1
    assert results[0].name == "Alice"
