# Product Requirements Document: Support for Python Structures in SQLiter Models

## **TODO**

Enable SQLiter models to support Python structures like `list`, `dict`, `set`,
and `tuple`. These structures should be transparently serialized (pickled) into
`BLOB` fields for database storage and automatically deserialized when
retrieved, without requiring a dedicated field type like `PickleField`.
Serialization should be handled in a way similar to how `datetime` is currently
converted to integers in SQLiter.

---

## **Implementation Steps**

### **1. Extend Serialization Logic in `BaseDBModel`**

Update the `serialize_field` and `deserialize_field` methods in `BaseDBModel` to
handle the following Python structures:

- `list`
- `dict`
- `set`
- `tuple`

#### **Serialization**

- Serialize supported Python structures into a binary format using
  `pickle.dumps()`.
- Store the serialized data as a `BLOB` in SQLite.
- Ensure that serialization logic aligns with the mappings defined in
  `SQLITE_TYPE_MAPPING` to avoid discrepancies.

#### **Deserialization**

- Deserialize `BLOB` data back into the original Python structure using
  `pickle.loads()` when retrieving from the database.

---

### **2. Update Field Handling in `SqliterDB`**

Ensure `SqliterDB` handles the following during CRUD operations:

- **Insertion/Update**: Serialize Python structures before executing SQL
  commands.
- **Retrieval**: Deserialize `BLOB` data back into Python structures after
  fetching results.

### **3. Modify Table Creation Logic**

Ensure fields typed as `list`, `dict`, `set`, or `tuple` in models are created
as `BLOB` columns in the SQLite table schema.

---

## **Detailed Implementation Plan**

### **1. Extend `BaseDBModel`

#### Modify `serialize_field` Method

Add logic to serialize supported Python structures into `BLOB` format:

```python
@classmethod
def serialize_field(cls, value: Any) -> Any:
    if isinstance(value, (list, dict, set, tuple)):
        return pickle.dumps(value)
    return super().serialize_field(value)
```

#### Modify `deserialize_field` Method

Add logic to deserialize `BLOB` data back into Python structures:

```python
@classmethod
def deserialize_field(cls, field_name: str, value: Any, *, return_local_time: bool = False) -> Any:
    if cls.__annotations__.get(field_name) in (list, dict, set, tuple) and isinstance(value, bytes):
        return pickle.loads(value)
    return super().deserialize_field(field_name, value, return_local_time=return_local_time)
```

### **2. Update `SqliterDB` CRUD Operations**

#### Ensure Serialization During Insertion and Updates

Update logic in `SqliterDB.insert` and `SqliterDB.update` to serialize Python
structures:

- Use `BaseDBModel.serialize_field` for all fields before constructing SQL
  commands.

#### Ensure Deserialization During Retrieval

Update logic in `SqliterDB.get` and `QueryBuilder` to deserialize Python
structures:

- Use `BaseDBModel.deserialize_field` to transform `BLOB` data into Python
  objects.

#### Reminder to Test Interaction with `SQLITE_TYPE_MAPPING`

Ensure CRUD operations are tested with the updated `SQLITE_TYPE_MAPPING` to
verify correct behavior when handling the new types.

### **3. Test Cases**

#### **Unit Tests**

Write tests to verify the serialization and deserialization of supported structures:

1. Insert and retrieve models containing:
   - Lists (`list[int]`, `list[str]`)
   - Dictionaries (`dict[str, str]`)
   - Sets (`set[int]`, `set[str]`)
   - Tuples (`tuple[int, str]`)
2. Test nested structures (e.g., `list[dict[str, list[int]]]`).
3. Verify behavior with empty structures (e.g., `[]`, `{}`).
4. Confirm that non-supported types raise appropriate exceptions.

#### **Performance Tests**

Evaluate performance with large datasets and deeply nested structures to ensure
acceptable serialization/deserialization times.

### **4. Documentation**

Update the following documentation:

1. **User Guide**: Explain how Python structures are supported transparently.
2. **Examples**: Provide examples of models with supported fields and
   corresponding CRUD operations.

---

## **Potential Issues and Mitigation**

### **1. Security Risks with Pickle**

- **Risk**: `pickle.loads` can execute arbitrary code if untrusted data is
  deserialized.
- **Mitigation**:
  - Since all database data originates from the user, this risk is minimal.
  - Clearly document that this feature assumes trusted data sources.

### **2. Querying Serialized Fields**

- **Issue**: SQLite does not support querying pickled data.
- **Mitigation**:
  - Limit operations on these fields to storage and retrieval.
  - For advanced querying, users can store additional metadata in separate
    fields.

### **3. Backward Compatibility**

- **Issue**: Adding `list`, `dict`, `set`, and `tuple` support could conflict
  with existing database schemas.
- **Mitigation**:
  - Clearly document migration requirements for affected fields.
  - Provide tools or scripts to assist with schema migrations if needed.

---

## **Roadmap**

### **Phase 1: Core Implementation**

- Extend `BaseDBModel` for serialization/deserialization.
- Update `SqliterDB` CRUD operations.
- Modify table creation logic.

### **Phase 2: Testing**

- Write unit tests for all supported types.
- Conduct performance testing with large and nested datasets.

### **Phase 3: Documentation**

- Update user guides and examples.
- Document limitations and potential risks.

---

## **Success Criteria**

- Python structures (`list`, `dict`, `set`, `tuple`) are seamlessly
  serialized/deserialized.
- No changes to user-facing APIs (fields remain strongly typed).
- CRUD operations work as expected with minimal performance overhead.
- Comprehensive documentation and test coverage are provided.
