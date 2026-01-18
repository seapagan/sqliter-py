"""Test the advanced filter capabilities of the library."""

import pytest

from .conftest import PersonModel


class TestAdvancedFilters:
    """Test class containing methods to test advanced filter capabilities."""

    def test_filter_with_gt_condition(self, db_mock_adv) -> None:
        """Test filter with greater than condition."""
        # Filter where age > 25
        results = db_mock_adv.select(PersonModel).filter(age__gt=25).fetch_all()

        assert len(results) == 2
        assert all(result.age > 25 for result in results)
        assert {result.name for result in results} == {"Bob", "Charlie"}

    def test_filter_with_lt_condition(self, db_mock_adv) -> None:
        """Test filter with less than condition."""
        # Filter where age < 35
        results = db_mock_adv.select(PersonModel).filter(age__lt=35).fetch_all()

        assert len(results) == 2
        assert all(result.age < 35 for result in results)
        assert {result.name for result in results} == {"Alice", "Bob"}

    def test_filter_with_gte_condition(self, db_mock_adv) -> None:
        """Test filter with greater than or equal to condition."""
        # Filter where age >= 30
        results = (
            db_mock_adv.select(PersonModel).filter(age__gte=30).fetch_all()
        )

        assert len(results) == 2
        assert all(result.age >= 30 for result in results)
        assert {result.name for result in results} == {"Bob", "Charlie"}

    def test_filter_with_lte_condition(self, db_mock_adv) -> None:
        """Test filter with less than or equal to condition."""
        # Filter where age <= 30
        results = (
            db_mock_adv.select(PersonModel).filter(age__lte=30).fetch_all()
        )

        assert len(results) == 2
        assert all(result.age <= 30 for result in results)
        assert {result.name for result in results} == {"Alice", "Bob"}

    def test_filter_with_eq_condition(self, db_mock_adv) -> None:
        """Test filter with equal to condition."""
        # Filter where age == 30
        results = db_mock_adv.select(PersonModel).filter(age__eq=30).fetch_all()

        assert len(results) == 1
        assert results[0].age == 30
        assert results[0].name == "Bob"

    def test_filter_with_ne_condition(self, db_mock_adv) -> None:
        """Test filter with not equal to condition."""
        # Filter where age != 30
        results = db_mock_adv.select(PersonModel).filter(age__ne=30).fetch_all()

        assert len(results) == 2
        assert all(result.age != 30 for result in results)
        assert {result.name for result in results} == {"Alice", "Charlie"}

    def test_filter_with_gt_and_lt_combined(self, db_mock_adv) -> None:
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

    def test_filter_with_gt_and_lte_combined(self, db_mock_adv) -> None:
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

    def test_filter_with_is_null_condition(self, db_mock_adv) -> None:
        """Test filter with IS NULL condition."""
        db_mock_adv.insert(PersonModel(name="David", age=None))
        # Filter where age is NULL
        results = (
            db_mock_adv.select(PersonModel).filter(age__isnull=True).fetch_all()
        )

        assert len(results) == 1
        assert results[0].age is None
        assert results[0].name == "David"

    def test_filter_with_is_not_null_condition(self, db_mock_adv) -> None:
        """Test filter with IS NOT NULL condition."""
        db_mock_adv.insert(PersonModel(name="David", age=None))
        # Filter where age is NOT NULL
        results = (
            db_mock_adv.select(PersonModel)
            .filter(age__notnull=True)
            .fetch_all()
        )

        assert len(results) == 3
        assert all(result.age is not None for result in results)
        assert {result.name for result in results} == {
            "Alice",
            "Bob",
            "Charlie",
        }

    def test_filter_with_in_condition(self, db_mock_adv) -> None:
        """Test filter with IN condition."""
        # Filter where age IN (25, 35)
        results = (
            db_mock_adv.select(PersonModel).filter(age__in=[25, 35]).fetch_all()
        )

        assert len(results) == 2
        assert all(result.age in [25, 35] for result in results)
        assert {result.name for result in results} == {"Alice", "Charlie"}

    def test_filter_with_not_in_condition(self, db_mock_adv) -> None:
        """Test filter with NOT IN condition."""
        # Filter where age NOT IN (25, 35)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(age__not_in=[25, 35])
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].age == 30
        assert results[0].name == "Bob"

    def test_filter_with_bad_in_condition(self, db_mock_adv) -> None:
        """Test filter with bad IN condition."""
        with pytest.raises(TypeError, match="age requires a list") as exc_info:
            db_mock_adv.select(PersonModel).filter(age__in=25).fetch_all()

        assert str(exc_info.value) == "age requires a list for '__in'"

    def test_filter_with_bad_not_in_condition(self, db_mock_adv) -> None:
        """Test filter with bad NOT IN condition."""
        with pytest.raises(TypeError, match="age requires a list") as exc_info:
            db_mock_adv.select(PersonModel).filter(age__not_in=25).fetch_all()

        assert str(exc_info.value) == "age requires a list for '__not_in'"

    def test_filter_with_starts_with_condition(self, db_mock_adv) -> None:
        """Test filter with starts with condition (default case-sensitive)."""
        db_mock_adv.insert(PersonModel(name="alison", age=50))
        # Filter where name starts with 'A' case-sensitive
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__startswith="A")
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].name == "Alice"

    def test_filter_with_starts_with_condition_case_insensitive(
        self,
        db_mock_adv,
    ) -> None:
        """Test filter with starts with condition (case insensitive)."""
        db_mock_adv.insert(PersonModel(name="alison", age=50))
        # Filter where name starts with 'a' (case insensitive)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__istartswith="a")
            .fetch_all()
        )

        assert len(results) == 2
        assert results[0].name == "Alice"

    def test_filter_with_bad_starts_with_condition(self, db_mock_adv) -> None:
        """Test filter with bad starts with condition."""
        with pytest.raises(
            TypeError, match="name requires a string"
        ) as exc_info:
            db_mock_adv.select(PersonModel).filter(
                name__startswith=25
            ).fetch_all()

        assert (
            str(exc_info.value)
            == "name requires a string value for '__startswith'"
        )

    def test_filter_with_ends_with_condition(self, db_mock_adv) -> None:
        """Test filter with ends with condition (case sensitive)."""
        db_mock_adv.insert(PersonModel(name="DALE", age=2))

        # Filter where name ends with 'e'
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__endswith="e")
            .fetch_all()
        )

        assert len(results) == 2
        assert all(result.name.endswith("e") for result in results)

    def test_filter_with_ends_with_condition_case_insensitive(
        self,
        db_mock_adv,
    ) -> None:
        """Test filter with ends with condition (case insensitive)."""
        # Filter where name ends with 'e' (case insensitive)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__iendswith="E")
            .fetch_all()
        )

        assert len(results) == 2
        assert all(result.name.endswith("e") for result in results)

    def test_filter_with_bad_ends_with_condition(self, db_mock_adv) -> None:
        """Test filter with bad ends with condition."""
        with pytest.raises(
            TypeError, match="name requires a string"
        ) as exc_info:
            db_mock_adv.select(PersonModel).filter(
                name__endswith=25
            ).fetch_all()

        assert (
            str(exc_info.value)
            == "name requires a string value for '__endswith'"
        )

    def test_filter_with_contains_condition(self, db_mock_adv) -> None:
        """Test filter with contains condition (case-sensitive)."""
        # Add one more record for our test
        db_mock_adv.insert(PersonModel(name="Lianne", age=40))

        # Case-sensitive contains "lie" (should match Charlie)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__contains="lie")
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Charlie"

        # Case-sensitive contains "ia" (should match Lianne)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__contains="ia")
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Lianne"

        # Case-sensitive contains "i" (should match Alice, Charlie, Lianne)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__contains="i")
            .fetch_all()
        )
        assert len(results) == 3
        assert {r.name for r in results} == {"Alice", "Charlie", "Lianne"}

        # Case-sensitive contains "I" (should match none)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__contains="I")
            .fetch_all()
        )
        assert len(results) == 0

    def test_filter_with_icontains_condition(self, db_mock_adv) -> None:
        """Test filter with case-insensitive contains condition."""
        # No need to insert new records, we'll use existing ones

        # Case-insensitive contains "LI"
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__icontains="LI")
            .fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Alice", "Charlie"}

        # Case-insensitive contains "BOB"
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__icontains="BOB")
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Bob"

        # Case-insensitive contains "i"
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__icontains="i")
            .fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Alice", "Charlie"}

    def test_filter_with_bad_contains_condition(self, db_mock_adv) -> None:
        """Test filter with bad contains condition."""
        with pytest.raises(
            TypeError, match="name requires a string"
        ) as exc_info:
            db_mock_adv.select(PersonModel).filter(
                name__contains=25
            ).fetch_all()

        assert (
            str(exc_info.value)
            == "name requires a string value for '__contains'"
        )

    def test_multiple_chained_filters(self, db_mock_adv) -> None:
        """Test multiple chained filters."""
        # Insert an additional record
        db_mock_adv.insert(PersonModel(name="Alex", age=28))

        results = (
            db_mock_adv.select(PersonModel)
            .filter(age__gt=25)
            .filter(name__startswith="A")
            .fetch_all()
        )

        assert len(results) == 1
        assert results[0].name == "Alex"
        assert results[0].age == 28

    def test_all_records_with_multiple_inclusive_filters(
        self, db_mock_adv
    ) -> None:
        """Test using multiple filters in same filter() call."""
        results = (
            db_mock_adv.select(PersonModel)
            .filter(age__gte=25, name__isnull=False)
            .fetch_all()
        )

        assert len(results) == 3  # Original assertion
        assert {result.name for result in results} == {
            "Alice",
            "Bob",
            "Charlie",
        }

    def test_name_isnull_and_notnull_filters(self, db_mock_adv) -> None:
        """Test various filters with __isnull and __notnull."""
        # Test __isnull=False
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__isnull=False)
            .fetch_all()
        )
        assert len(results) == 3
        assert all(result.name is not None for result in results)

        # Test __isnull=True (should return no results as all names are set)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__isnull=True)
            .fetch_all()
        )
        assert len(results) == 0

        # Test __notnull=True
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__notnull=True)
            .fetch_all()
        )
        assert len(results) == 3
        assert all(result.name is not None for result in results)

        # Test __notnull=False (should return no results as all names are set)
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__notnull=False)
            .fetch_all()
        )
        assert len(results) == 0

        # Add a record with null name to test opposite cases
        db_mock_adv.insert(PersonModel(name=None, age=40))

        # Now test __isnull=True and __notnull=False with the new record
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__isnull=True)
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name is None

        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__notnull=False)
            .fetch_all()
        )
        assert len(results) == 1
        assert results[0].name is None

    def test_filter_with_like_condition(self, db_mock_adv) -> None:
        """Test filter with LIKE condition using wildcards."""
        # Filter where name matches 'A%' (starts with A)
        results = (
            db_mock_adv.select(PersonModel).filter(name__like="A%").fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Alice"

    def test_filter_with_like_ends_with(self, db_mock_adv) -> None:
        """Test filter with LIKE condition for ends with pattern."""
        # Filter where name matches '%e' (ends with e)
        results = (
            db_mock_adv.select(PersonModel).filter(name__like="%e").fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Alice", "Charlie"}

    def test_filter_with_like_contains(self, db_mock_adv) -> None:
        """Test filter with LIKE condition for contains pattern."""
        # Filter where name matches '%li%' (contains 'li')
        results = (
            db_mock_adv.select(PersonModel)
            .filter(name__like="%li%")
            .fetch_all()
        )
        assert len(results) == 2
        assert {r.name for r in results} == {"Alice", "Charlie"}

    def test_filter_with_like_single_char_wildcard(self, db_mock_adv) -> None:
        """Test filter with LIKE condition using single character wildcard."""
        # Filter where name matches '_ob' (3 chars ending in 'ob')
        results = (
            db_mock_adv.select(PersonModel).filter(name__like="_ob").fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Bob"

    def test_filter_with_like_case_insensitive(self, db_mock_adv) -> None:
        """Test that LIKE is case-insensitive in SQLite by default."""
        # SQLite LIKE is case-insensitive for ASCII characters
        results = (
            db_mock_adv.select(PersonModel).filter(name__like="a%").fetch_all()
        )
        assert len(results) == 1
        assert results[0].name == "Alice"

    def test_filter_with_like_no_match(self, db_mock_adv) -> None:
        """Test filter with LIKE condition that matches nothing."""
        results = (
            db_mock_adv.select(PersonModel).filter(name__like="Z%").fetch_all()
        )
        assert len(results) == 0

    def test_filter_with_bad_like_condition(self, db_mock_adv) -> None:
        """Test filter with bad LIKE condition (non-string value)."""
        with pytest.raises(
            TypeError, match="name requires a string"
        ) as exc_info:
            db_mock_adv.select(PersonModel).filter(name__like=25).fetch_all()

        assert (
            str(exc_info.value) == "name requires a string value for '__like'"
        )
