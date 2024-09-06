import sqlite3
from pydantic import BaseModel

# Pydantic model for licenses
class LicenseModel(BaseModel):
    slug: str
    name: str
    content: str

    # Pydantic v2 uses 'model_config' instead of 'Config'
    model_config = {
        "table_name": "licenses",  # Specify the table name here
        "primary_key": "slug",     # Specify the primary key field if no id field is used
        "create_id": True          # Whether to create an auto-increment id field
    }

class QueryBuilder:
    def __init__(self, db, model_class):
        self.db = db
        self.model_class = model_class
        self.table_name = db._get_table_name(model_class)
        self.filters = []

    def filter(self, **conditions):
        """Add filter conditions to the query."""
        for field, value in conditions.items():
            self.filters.append((field, value))
        return self

    def _execute_query(self, limit=None, offset=None, order_by=None, fetch_one=False):
        """Helper function to execute the query with filters."""
        fields = ", ".join(self.model_class.__fields__.keys())
        where_clause = " AND ".join([f"{field} = ?" for field, _ in self.filters])
        sql = f"SELECT {fields} FROM {self.table_name}"

        if self.filters:
            sql += f" WHERE {where_clause}"

        if order_by:
            sql += f" ORDER BY {order_by}"

        if limit is not None:
            sql += f" LIMIT {limit}"

        if offset is not None:
            sql += f" OFFSET {offset}"

        values = [value for _, value in self.filters]

        with self.db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return cursor.fetchall() if not fetch_one else cursor.fetchone()

    def fetch_all(self):
        """Fetch all results matching the filters."""
        results = self._execute_query()
        return [self.model_class(**{field: row[idx] for idx, field in enumerate(self.model_class.__fields__.keys())}) for row in results]

    def fetch_one(self):
        """Fetch exactly one result."""
        result = self._execute_query(fetch_one=True)
        if not result:
            return None
        return self.model_class(**{field: result[idx] for idx, field in enumerate(self.model_class.__fields__.keys())})

    def fetch_first(self):
        """Fetch the first result of the query."""
        result = self._execute_query(limit=1)
        if not result:
            return None
        return self.model_class(**{field: result[0][idx] for idx, field in enumerate(self.model_class.__fields__.keys())})

    def fetch_last(self):
        """Fetch the last result of the query (based on the primary key)."""
        primary_key = self.db._get_primary_key(self.model_class)
        result = self._execute_query(limit=1, order_by=f"{primary_key} DESC")
        if not result:
            return None
        return self.model_class(**{field: result[0][idx] for idx, field in enumerate(self.model_class.__fields__.keys())})

    def count(self):
        """Return the count of records matching the filters."""
        where_clause = " AND ".join([f"{field} = ?" for field, _ in self.filters])
        sql = f"SELECT COUNT(*) FROM {self.table_name}"

        if self.filters:
            sql += f" WHERE {where_clause}"

        values = [value for _, value in self.filters]

        with self.db._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(sql, values)
            return cursor.fetchone()[0]

    def exists(self):
        """Return True if any record matches the filters."""
        return self.count() > 0


class LicenseDB:
    def __init__(self, db_filename, auto_commit=False):
        self.db_filename = db_filename
        self.auto_commit = auto_commit
        self.conn = None

    def _connect(self):
        """Create or return a connection to the SQLite database."""
        if not self.conn:
            self.conn = sqlite3.connect(self.db_filename)
        return self.conn

    def _get_table_name(self, model_class):
        """Get the table name from the model or default to class name."""
        return model_class.model_config.get('table_name', model_class.__name__.lower())

    def _get_primary_key(self, model_class):
        """Get the primary key from the model's config or raise an error if not defined."""
        return model_class.model_config.get('primary_key', 'id')  # Default to 'id' if not specified

    def _should_create_id(self, model_class):
        """Check if the table should include an auto-increment id field."""
        return model_class.model_config.get('create_id', True)  # Default to True

    def create_table(self, model_class):
        """Create a table based on the Pydantic model."""
        table_name = self._get_table_name(model_class)
        primary_key = self._get_primary_key(model_class)
        create_id = self._should_create_id(model_class)

        # Extract field names and types from the Pydantic model to create the SQL query
        fields = ", ".join(f"{field_name} TEXT" for field_name in model_class.__fields__.keys())

        # Add auto-increment id field if needed
        if create_id:
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {fields}
                )
            '''
        else:
            # Use the specified primary key if create_id is False
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {fields},
                    PRIMARY KEY ({primary_key})
                )
            '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(create_table_sql)
            conn.commit()

    def _maybe_commit(self, conn):
        """Commit changes if auto_commit is True."""
        if self.auto_commit:
            conn.commit()

    def insert(self, model_instance):
        """Insert a new record into the table defined by the Pydantic model."""
        model_class = type(model_instance)
        table_name = self._get_table_name(model_class)
        create_id = self._should_create_id(model_class)

        # Dynamically extract field names and values from the Pydantic model instance
        fields = ", ".join(model_class.__fields__.keys())
        placeholders = ", ".join(["?"] * len(model_class.__fields__))
        values = tuple(getattr(model_instance, field) for field in model_class.__fields__)

        # If there's an auto-increment id, skip specifying the id field
        if create_id:
            insert_sql = f'''
                INSERT OR REPLACE INTO {table_name} ({fields})
                VALUES ({placeholders})
            '''
        else:
            # Include the primary key explicitly if create_id is False
            insert_sql = f'''
                INSERT OR REPLACE INTO {table_name} ({fields})
                VALUES ({placeholders})
            '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(insert_sql, values)
            self._maybe_commit(conn)

    def get(self, model_class, primary_key_value):
        """Retrieve a record by its primary key and return a Pydantic model instance."""
        table_name = self._get_table_name(model_class)
        primary_key = self._get_primary_key(model_class)

        # Select only the fields defined in the Pydantic model, excluding the auto-increment id
        fields = ", ".join(model_class.__fields__.keys())

        select_sql = f'''
            SELECT {fields} FROM {table_name} WHERE {primary_key} = ?
        '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(select_sql, (primary_key_value,))
            result = cursor.fetchone()

        if result:
            # Dynamically map the result to the Pydantic model fields
            result_dict = {field: result[idx] for idx, field in enumerate(model_class.__fields__)}
            return model_class(**result_dict)
        return None


    def update(self, model_instance):
        """Update an existing record using the Pydantic model."""
        model_class = type(model_instance)
        table_name = self._get_table_name(model_class)
        primary_key = self._get_primary_key(model_class)

        # Dynamically build the update SQL with the model fields
        fields = ", ".join(f"{field} = ?" for field in model_class.__fields__ if field != primary_key)
        values = tuple(getattr(model_instance, field) for field in model_class.__fields__ if field != primary_key)
        primary_key_value = getattr(model_instance, primary_key)

        update_sql = f'''
            UPDATE {table_name} SET {fields} WHERE {primary_key} = ?
        '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(update_sql, (*values, primary_key_value))
            self._maybe_commit(conn)

    def delete(self, model_class, primary_key_value):
        """Delete a record by its primary key."""
        table_name = self._get_table_name(model_class)
        primary_key = self._get_primary_key(model_class)

        delete_sql = f'''
            DELETE FROM {table_name} WHERE {primary_key} = ?
        '''

        with self._connect() as conn:
            cursor = conn.cursor()
            cursor.execute(delete_sql, (primary_key_value,))
            self._maybe_commit(conn)

    def select(self, model_class):
        """Select the model (table) for querying."""
        return QueryBuilder(self, model_class)


    # --- Context manager methods ---
    def __enter__(self):
        """Enter the runtime context for the 'with' statement."""
        self._connect()  # Ensure the connection is opened
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exit the runtime context and close the connection."""
        if self.conn:
            if not self.auto_commit:  # Commit only if auto_commit is off
                self.conn.commit()
            self.conn.close()
            self.conn = None


# Example usage:
db = LicenseDB('lice.db', auto_commit=True)
with db:
    db.create_table(LicenseModel)  # Create the licenses table
    license = LicenseModel(slug='mit', name='MIT License', content='This is the MIT license content.')
    db.insert(license)
    fetched_license = db.get(LicenseModel, 'mit')
    print(fetched_license)
