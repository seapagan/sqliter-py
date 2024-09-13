from .conftest import PersonModel


def test_filter_with_gt_condition(db_mock_adv) -> None:
    """Test filter with greater than condition."""
    db_mock_adv.insert(PersonModel(name="Alice", age=25))
    db_mock_adv.insert(PersonModel(name="Bob", age=30))
    db_mock_adv.insert(PersonModel(name="Charlie", age=35))

    # Filter where age > 25
    results = db_mock_adv.select(PersonModel).filter(age__gt=25).fetch_all()

    assert len(results) == 2
    assert all(result.age > 25 for result in results)
    assert {result.name for result in results} == {"Bob", "Charlie"}


def test_filter_with_lt_condition(db_mock_adv) -> None:
    """Test filter with less than condition."""
    db_mock_adv.insert(PersonModel(name="Alice", age=25))
    db_mock_adv.insert(PersonModel(name="Bob", age=30))
    db_mock_adv.insert(PersonModel(name="Charlie", age=35))

    # Filter where age < 35
    results = db_mock_adv.select(PersonModel).filter(age__lt=35).fetch_all()

    assert len(results) == 2
    assert all(result.age < 35 for result in results)
    assert {result.name for result in results} == {"Alice", "Bob"}


def test_filter_with_gt_and_lt_combined(db_mock_adv) -> None:
    """Test filter with combined greater than and less than conditions."""
    db_mock_adv.insert(PersonModel(name="Alice", age=25))
    db_mock_adv.insert(PersonModel(name="Bob", age=30))
    db_mock_adv.insert(PersonModel(name="Charlie", age=35))
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
