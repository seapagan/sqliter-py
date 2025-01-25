"""Test suite for the 'sqliter' library."""

import pytest

from sqliter import SqliterDB
from sqliter.exceptions import (
    RecordFetchError,
    RecordNotFoundError,
    TableCreationError,
)
from sqliter.model import BaseDBModel
from tests.conftest import ComplexModel, DetailedPersonModel, ExampleModel


class ExistOkModel(BaseDBModel):
    """Just used to test table creation with an existing table."""

    name: str
    age: int

    class Meta:
        """Meta class for the model."""

        table_name = "exist_ok_table"


class TestSqliterDB:
    """Test class to test the SqliterDB class."""

    def test_auto_commit_default(self) -> None:
        """Test that auto_commit is enabled by default."""
        db = SqliterDB(":memory:")
        assert db.auto_commit

    def test_auto_commit_disabled(self) -> None:
        """Test that auto_commit can be disabled."""
        db = SqliterDB(":memory:", auto_commit=False)
        assert not db.auto_commit

    @pytest.mark.skip(reason="This does not test the behavour correctly.")
    def test_data_lost_when_auto_commit_disabled(self) -> None:
        """Test that data is lost when auto_commit is disabled.

        The other cases when auto_commit is enabled are tested in all the other
        tests.
        """
        db = SqliterDB(":memory:", auto_commit=False)
        db.create_table(ExampleModel)

        # Insert a record
        test_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )
        result = db.insert(test_model)

        # Ensure the record exists
        fetched_license = db.get(ExampleModel, result.pk)
        assert fetched_license is not None

        # Close the connection
        db.close()

        # Re-open the connection
        db.connect()

        # Ensure the data is lost
        with pytest.raises(RecordFetchError):
            db.get(ExampleModel, result.pk)

    def test_create_table(self, db_mock) -> None:
        """Test table creation."""
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            assert len(tables) == 2
            assert ("test_table",) in tables

    def test_close_connection(self, db_mock) -> None:
        """Test closing the connection."""
        db_mock.close()
        assert db_mock.conn is None

    def test_commit_changes(self, mocker) -> None:
        """Test committing changes to the database."""
        db = SqliterDB(":memory:", auto_commit=False)
        db.create_table(ExampleModel)
        db.insert(
            ExampleModel(slug="test", name="Test License", content="Content")
        )
        mock_conn = mocker.Mock()
        mocker.patch.object(db, "conn", mock_conn)

        db.commit()

        assert mock_conn.commit.called

    def test_create_table_with_default_auto_increment(self, db_mock) -> None:
        """Test table creation with auto-incrementing primary key."""

        class AutoIncrementModel(BaseDBModel):
            name: str

            class Meta:
                table_name: str = "auto_increment_table"

        # Create the table
        db_mock.create_table(AutoIncrementModel)

        # Verify that the table was created with an auto-incrementing PK
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(auto_increment_table);")
            table_info = cursor.fetchall()

        # Check that the first column is 'id' and it's an auto-incrementing int
        assert table_info[0][1] == "pk"  # Column name
        assert table_info[0][2] == "INTEGER"  # Column type
        assert table_info[0][5] == 1  # Primary key flag

    def test_default_table_name(self, db_mock) -> None:
        """Test the default table name generation.

        It should default to the class name in lowercase, plural form.
        """

        class DefaultNameModel(BaseDBModel):
            name: str

            class Meta:
                table_name = None  # Explicitly set to None to test the default

        # Verify that get_table_name defaults to class name in lowercase
        assert DefaultNameModel.get_table_name() == "default_names"

    def test_get_table_name_fallback_without_inflect(self, mocker) -> None:
        """Test get_table_name falls back to manual plural without 'inflect."""
        # Mock the inflect import to raise ImportError for `inflect`
        mocker.patch.dict("sys.modules", {"inflect": None})

        class UserModel(BaseDBModel):
            pass

        table_name = UserModel.get_table_name()
        assert table_name == "users"  # Fallback logic should add 's'

    def test_get_table_name_no_double_s_without_inflect(self, mocker) -> None:
        """Test get_table_name doesn't add extra 's' if already there."""
        # Mock the sys.modules to simulate 'inflect' being unavailable
        mocker.patch.dict("sys.modules", {"inflect": None})

        class UsersModel(BaseDBModel):
            pass

        table_name = UsersModel.get_table_name()
        assert table_name == "users"  # Should not add an extra 's'

    def test_get_table_name_with_inflect(self) -> None:
        """Test get_table_name uses 'inflect' for pluralization if available."""

        class PersonModel(BaseDBModel):
            pass

        table_name = PersonModel.get_table_name()

        # Here, we assume that inflect will pluralize 'person' to 'people'
        assert table_name == "people"

    def test_insert_license(self, db_mock) -> None:
        """Test inserting a license into the database."""
        test_model = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        db_mock.insert(test_model)

        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM test_table WHERE slug = ?", ("mit",))
            result = cursor.fetchone()
            assert result[0] == 1
            assert result[3] == "mit"
            assert result[4] == "MIT License"
            assert result[5] == "MIT License Content"

    def test_fetch_license(self, db_mock) -> None:
        """Test fetching a license by primary key."""
        test_model = ExampleModel(
            slug="gpl", name="GPL License", content="GPL License Content"
        )
        result = db_mock.insert(test_model)

        fetched_license = db_mock.get(ExampleModel, result.pk)
        assert fetched_license is not None
        assert fetched_license.slug == "gpl"
        assert fetched_license.name == "GPL License"
        assert fetched_license.content == "GPL License Content"

    def test_update(self, db_mock) -> None:
        """Test updating an existing license."""
        test_model = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        result = db_mock.insert(test_model)

        # Update license content
        result.content = "Updated MIT License Content"
        db_mock.update(result)

        # Fetch and check if updated
        fetched_license = db_mock.get(ExampleModel, result.pk)
        assert fetched_license.content == "Updated MIT License Content"

    def test_delete(self, db_mock) -> None:
        """Test deleting a license."""
        test_model = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        result = db_mock.insert(test_model)

        # Delete the record
        db_mock.delete(ExampleModel, result.pk)

        # Ensure it no longer exists
        fetched_license = db_mock.get(ExampleModel, result.pk)
        assert fetched_license is None

    def test_select_filter(self, db_mock) -> None:
        """Test filtering licenses using the QueryBuilder."""
        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        license2 = ExampleModel(
            slug="gpl", name="GPL License", content="GPL License Content"
        )
        db_mock.insert(license1)
        db_mock.insert(license2)

        # Query and filter licenses
        filtered = (
            db_mock.select(ExampleModel).filter(name="GPL License").fetch_all()
        )
        assert len(filtered) == 1
        assert filtered[0].slug == "gpl"

    def test_query_fetch_first(self, db_mock) -> None:
        """Test fetching the first record."""
        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        license2 = ExampleModel(
            slug="gpl", name="GPL License", content="GPL License Content"
        )
        db_mock.insert(license1)
        db_mock.insert(license2)

        first_record = db_mock.select(ExampleModel).fetch_first()
        assert first_record.slug == "mit"

    def test_query_fetch_last(self, db_mock) -> None:
        """Test fetching the last record."""
        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        license2 = ExampleModel(
            slug="gpl", name="GPL License", content="GPL License Content"
        )
        db_mock.insert(license1)
        db_mock.insert(license2)

        last_record = db_mock.select(ExampleModel).fetch_last()
        assert last_record.slug == "gpl"

    def test_count_records(self, db_mock) -> None:
        """Test counting records in the database."""
        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        license2 = ExampleModel(
            slug="gpl", name="GPL License", content="GPL License Content"
        )
        db_mock.insert(license1)
        db_mock.insert(license2)

        count = db_mock.select(ExampleModel).count()
        assert count == 2

    def test_exists_record(self, db_mock) -> None:
        """Test checking if a record exists."""
        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )
        db_mock.insert(license1)

        exists = db_mock.select(ExampleModel).filter(slug="mit").exists()
        assert exists

    def test_transaction_commit(self, db_mock, mocker) -> None:
        """Test if auto_commit works correctly when enabled."""
        # Mock the commit method on the connection
        mock_conn = mocker.MagicMock()

        # Manually reset the connection to ensure our mock is used
        db_mock.conn = mock_conn

        # Patch connect method to return the mock connection
        mocker.patch.object(db_mock, "connect", return_value=mock_conn)

        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )

        with db_mock:
            db_mock.create_table(ExampleModel)
            db_mock.insert(license1)

        # Ensure commit was called only once, when the context manager exited.
        assert mock_conn.commit.call_count == 1

    def test_transaction_manual_commit(self, mocker) -> None:
        """Test context-manager commit when auto_commit is set to False.

        Regardless of the auto_commit setting, the context manager should commit
        changes when exiting the context.
        """
        db_manual = SqliterDB(":memory:", auto_commit=True)

        # Mock the connection and commit
        mock_conn = mocker.MagicMock()
        mocker.patch.object(db_manual, "connect", return_value=mock_conn)
        db_manual.conn = (
            mock_conn  # Ensure the db_manual uses the mock connection
        )

        license1 = ExampleModel(
            slug="mit", name="MIT License", content="MIT License Content"
        )

        with db_manual:
            db_manual.create_table(ExampleModel)
            db_manual.insert(license1)
            # Ensure commit hasn't been called yet
            mock_conn.commit.assert_not_called()

        # After leaving the context, commit should now be called
        mock_conn.commit.assert_called_once()

    def test_update_existing_record(self, db_mock) -> None:
        """Test that updating an existing record works correctly."""
        # Insert an example record
        example_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )
        result = db_mock.insert(example_model)

        # Update the record's content
        result.content = "Updated Content"
        db_mock.update(result)

        # Fetch the updated record and verify the changes
        updated_record = db_mock.get(ExampleModel, result.pk)
        assert updated_record is not None
        assert updated_record.content == "Updated Content"

    def test_update_non_existing_record(self, db_mock) -> None:
        """Test updating a non-existing record raises RecordNotFoundError."""
        # Create an example record that is not inserted into the DB
        example_model = ExampleModel(
            slug="nonexistent",
            name="Nonexistent License",
            content="Nonexistent Content",
        )

        # Try updating the non-existent record
        with pytest.raises(RecordNotFoundError) as exc_info:
            db_mock.update(example_model)

        # Check that the correct error message is raised
        assert "Failed to find that record in the table (key '0')" in str(
            exc_info.value
        )

    def test_get_non_existent_table(self, db_mock) -> None:
        """Test fetching from a non-existent table raises RecordFetchError."""

        class NonExistentModel(ExampleModel):
            class Meta:
                table_name = "non_existent_table"  # A table that doesn't exist

        with pytest.raises(RecordFetchError):
            db_mock.get(NonExistentModel, "non_existent_key")

    def test_get_record_no_result(self, db_mock) -> None:
        """Test fetching a non-existent record returns None."""
        result = db_mock.get(ExampleModel, "non_existent_key")
        assert result is None

    def test_delete_non_existent_record(self, db_mock) -> None:
        """Test that trying to delete a non-existent record raises exception."""
        with pytest.raises(RecordNotFoundError):
            db_mock.delete(ExampleModel, "non_existent_key")

    def test_delete_existing_record(self, db_mock) -> None:
        """Test that a record is deleted successfully."""
        # Insert a record first
        test_model = ExampleModel(
            slug="test", name="Test License", content="Test Content"
        )
        result = db_mock.insert(test_model)

        # Now delete the record
        db_mock.delete(ExampleModel, result.pk)

        # Fetch the deleted record to confirm it's gone
        result = db_mock.get(ExampleModel, result.pk)
        assert result is None

    def test_select_with_exclude_single_field(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test selecting with exclude parameter to remove a single field."""
        results = db_mock_detailed.select(
            DetailedPersonModel, exclude=["email"]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")

    def test_select_with_exclude_multiple_fields(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test selecting with exclude parameter to remove multiple fields."""
        results = db_mock_detailed.select(
            DetailedPersonModel, exclude=["email", "phone"]
        ).fetch_all()
        assert len(results) == 3
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "age")
            assert not hasattr(result, "email")
            assert not hasattr(result, "phone")

    def test_select_with_exclude_all_fields_error(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test select with excluding all fields raises error."""
        with pytest.raises(
            ValueError, match="Exclusion results in no fields being selected."
        ):
            db_mock_detailed.select(
                DetailedPersonModel,
                exclude=[
                    "created_at",
                    "updated_at",
                    "name",
                    "age",
                    "email",
                    "address",
                    "phone",
                    "occupation",
                ],
            ).fetch_all()

    def test_select_with_exclude_and_filter(
        self,
        db_mock_detailed: SqliterDB,
    ) -> None:
        """Test selecting with exclude and filter combined."""
        results = (
            db_mock_detailed.select(DetailedPersonModel, exclude=["phone"])
            .filter(age__gte=30)
            .fetch_all()
        )
        assert len(results) == 2
        for result in results:
            assert hasattr(result, "name")
            assert hasattr(result, "email")
            assert not hasattr(result, "phone")

    def test_in_memory_db_initialization(self) -> None:
        """Test that an in-memory database is initialized correctly."""
        db = SqliterDB(memory=True)
        assert db.db_filename == ":memory:"

    def test_file_based_db_initialization(self) -> None:
        """Test that a file-based database is initialized correctly."""
        db = SqliterDB(db_filename="test.db")
        assert db.db_filename == "test.db"

    def test_error_when_no_db_name_and_not_memory(self) -> None:
        """Error is raised when no db_filename is provided and memory=False."""
        with pytest.raises(ValueError, match="Database name must be provided"):
            SqliterDB(memory=False)

    def test_file_is_created_when_filename_is_provided(self, mocker) -> None:
        """Test that sqlite3.connect is called with the correct file path."""
        mock_connect = mocker.patch("sqlite3.connect")

        db_filename = "/fakepath/test.db"
        db = SqliterDB(db_filename=db_filename)
        db.connect()

        # Check if sqlite3.connect was called with the correct filename
        mock_connect.assert_called_with(db_filename)

    def test_memory_database_no_file_created(self, mocker) -> None:
        """Test sqlite3.connect is called with ':memory:' when memory=True."""
        mock_connect = mocker.patch("sqlite3.connect")

        db = SqliterDB(memory=True)
        db.connect()

        # Check if sqlite3.connect was called with ':memory:' for the in-memory
        # DB
        mock_connect.assert_called_with(":memory:")

    def test_memory_db_ignores_filename(self, mocker) -> None:
        """Test memory=True igores any filename, creating an in-memory DB."""
        mock_connect = mocker.patch("sqlite3.connect")

        db_filename = "/fakepath/test.db"
        db = SqliterDB(db_filename=db_filename, memory=True)
        db.connect()

        # Check that sqlite3.connect was called with ':memory:', ignoring the
        # filename
        mock_connect.assert_called_with(":memory:")

    def test_complex_model_field_types(self, db_mock) -> None:
        """Test that the table is created with the correct field types."""
        # Create table based on ComplexModel
        db_mock.create_table(ComplexModel)

        # Get table info for ComplexModel
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(complex_model);")
            table_info = cursor.fetchall()

        # Expected types in SQLite (INTEGER, REAL, TEXT, etc.)
        expected_types = {
            "pk": "INTEGER",
            "created_at": "INTEGER",
            "updated_at": "INTEGER",
            "name": "TEXT",
            "age": "REAL",
            "price": "REAL",
            "is_active": "INTEGER",  # Boolean stored as INTEGER
            "nullable_field": "TEXT",  # Optional fields default to TEXT
            "score": "TEXT",
        }

        # Assert each field has the correct SQLite type
        for column in table_info:
            column_name = column[
                1
            ]  # Column name is the second element in table_info
            column_type = column[2]  # Column type is the third element
            assert expected_types[column_name] == column_type, (
                f"Field {column_name} expected {expected_types[column_name]} "
                f"but got {column_type}"
            )

    def test_complex_model_primary_key(self, db_mock) -> None:
        """Test that the primary key is correctly created for ComplexModel."""
        # Create table based on ComplexModel
        db_mock.create_table(ComplexModel)

        # Get table info for ComplexModel
        with db_mock.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(complex_model);")
            table_info = cursor.fetchall()

        # Find the primary key column
        primary_key_column = None
        for column in table_info:
            if (
                column[5] == 1
            ):  # The 6th element in table_info is '1' if column is the pk
                primary_key_column = column

        # Assert that the primary key is the 'id' field and is an INTEGER
        assert primary_key_column is not None, "Primary key not found"
        assert primary_key_column[1] == "pk", (
            f"Expected 'id' as primary key, but got {primary_key_column[1]}"
        )
        assert primary_key_column[2] == "INTEGER", (
            f"Expected 'INTEGER' type for primary key, but got "
            f"{primary_key_column[2]}"
        )

    def test_reset_database_on_init(self, temp_db_path) -> None:
        """Test that the database is reset when reset=True is passed."""

        class TestModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "test_reset_table"

        # Create a database and add some data
        db = SqliterDB(temp_db_path)
        db.create_table(TestModel)
        db.insert(TestModel(name="Test Data"))
        db.close()

        # Create a new connection with reset=True
        db_reset = SqliterDB(temp_db_path, reset=True)

        # Verify the table no longer exists
        with pytest.raises(RecordFetchError):
            db_reset.select(TestModel).fetch_all()

    def test_reset_database_preserves_connection(self, temp_db_path) -> None:
        """Test that resetting the database doesn't break the connection."""

        class TestModel(BaseDBModel):
            name: str

            class Meta:
                table_name = "test_reset_table"

        db = SqliterDB(temp_db_path, reset=True)

        # Create a table after reset
        db.create_table(TestModel)
        db.insert(TestModel(name="New Data"))

        # Verify data exists
        result = db.select(TestModel).fetch_all()
        assert len(result) == 1

    def test_reset_database_with_multiple_tables(self, temp_db_path) -> None:
        """Test that reset drops all tables in the database."""

        class TestModel1(BaseDBModel):
            name: str

            class Meta:
                table_name = "test_reset_table1"

        class TestModel2(BaseDBModel):
            age: int

            class Meta:
                table_name = "test_reset_table2"

        # Create a database and add some data
        db = SqliterDB(temp_db_path)
        db.create_table(TestModel1)
        db.create_table(TestModel2)
        db.insert(TestModel1(name="Test Data"))
        db.insert(TestModel2(age=25))
        db.close()

        # Reset the database
        db_reset = SqliterDB(temp_db_path, reset=True)

        # Verify both tables no longer exist
        with pytest.raises(RecordFetchError):
            db_reset.select(TestModel1).fetch_all()
        with pytest.raises(RecordFetchError):
            db_reset.select(TestModel2).fetch_all()

    def test_create_table_exists_ok_true(self, db_mock) -> None:
        """Test creating a table with exists_ok=True (default behavior)."""
        # First creation should succeed
        db_mock.create_table(ExistOkModel)

        # Second creation should not raise an error
        try:
            db_mock.create_table(ExistOkModel)
        except TableCreationError as e:
            pytest.fail(f"create_table raised {type(e).__name__} unexpectedly!")

    def test_create_table_exists_ok_false(self, db_mock) -> None:
        """Test creating a table with exists_ok=False."""
        # First creation should succeed
        db_mock.create_table(ExistOkModel)

        # Second creation should raise an error
        with pytest.raises(TableCreationError):
            db_mock.create_table(ExistOkModel, exists_ok=False)

    def test_create_table_exists_ok_false_new_table(self) -> None:
        """Test creating a new table with exists_ok=False."""
        # Create a new database connection
        new_db = SqliterDB(":memory:")

        # Define a new model class specifically for this test
        class UniqueTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name = "unique_test_table"

        # Creation of a new table should succeed with exists_ok=False
        try:
            new_db.create_table(UniqueTestModel, exists_ok=False)
        except TableCreationError as e:
            pytest.fail(f"create_table raised {type(e).__name__} unexpectedly!")

        # Clean up
        new_db.close()

    def test_create_table_sql_generation(self, db_mock, mocker) -> None:
        """Test SQL generation for table creation based on exists_ok value."""
        mock_cursor = mocker.MagicMock()
        mocker.patch.object(
            db_mock, "connect"
        ).return_value.__enter__.return_value.cursor.return_value = mock_cursor

        # Test with exists_ok=True
        db_mock.create_table(ExistOkModel, exists_ok=True)
        mock_cursor.execute.assert_called()
        sql = mock_cursor.execute.call_args[0][0]
        assert "CREATE TABLE IF NOT EXISTS" in sql

        # Reset the mock
        mock_cursor.reset_mock()

        # Test with exists_ok=False
        db_mock.create_table(ExistOkModel, exists_ok=False)
        mock_cursor.execute.assert_called()
        sql = mock_cursor.execute.call_args[0][0]
        assert "CREATE TABLE" in sql
        assert "IF NOT EXISTS" not in sql

    def test_create_table_force(self) -> None:
        """Test creating a table with force=True."""
        # Create a new database
        db = SqliterDB(":memory:")

        # Define initial model
        class InitialTestModel(BaseDBModel):
            name: str
            age: int

            class Meta:
                table_name = "force_test_table"

        # First creation
        db.create_table(InitialTestModel)

        # Insert a record
        initial_record = InitialTestModel(name="Alice", age=30)
        db.insert(initial_record)

        # Define modified model
        class ModifiedTestModel(BaseDBModel):
            name: str
            email: str  # New field instead of age

            class Meta:
                table_name = "force_test_table"

        # Recreate with force=True
        db.create_table(ModifiedTestModel, force=True)

        # Try to insert a record with the new structure
        new_record = ModifiedTestModel(name="Bob", email="bob@example.com")
        db.insert(new_record)

        # Fetch and check if the new structure is in place
        result = db.select(ModifiedTestModel).fetch_one()
        assert result is not None
        assert hasattr(result, "email")
        assert not hasattr(result, "age")

        # Verify that the old structure is gone by checking table info
        with db.connect() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(force_test_table)")
            columns = [column[1] for column in cursor.fetchall()]

        assert "name" in columns
        assert "email" in columns
        assert "age" not in columns

        # Verify that old data is gone
        old_data = db.select(ModifiedTestModel).filter(name="Alice").fetch_one()
        assert old_data is None

        # Clean up
        db.close()

    def test_create_table_force_and_exists_ok(self, db_mock) -> None:
        """Test interaction between force and exists_ok parameters."""
        # force=True should take precedence over exists_ok=False
        db_mock.create_table(ExistOkModel)
        db_mock.create_table(ExistOkModel, exists_ok=False, force=True)
        # This should not raise an error

    def test_create_table_sql_generation_force(self, db_mock, mocker) -> None:
        """Test SQL generation for table creation with force=True."""
        mock_cursor = mocker.MagicMock()
        mocker.patch.object(
            db_mock, "connect"
        ).return_value.__enter__.return_value.cursor.return_value = mock_cursor

        db_mock.create_table(ExistOkModel, force=True)

        # Check for DROP TABLE
        drop_call = mock_cursor.execute.call_args_list[0]
        assert "DROP TABLE IF EXISTS" in drop_call[0][0]

        # Check for CREATE TABLE
        create_call = mock_cursor.execute.call_args_list[1]
        assert "CREATE TABLE" in create_call[0][0]
