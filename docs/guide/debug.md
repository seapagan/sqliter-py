# Debug Logging

You can enable debug logging to see the SQL queries being executed by SQLiter.
This can be useful for debugging and understanding the behavior of your
application. It is disabled by default, and can be set on the `SqliterDB` class:

```python
db = SqliterDB("your_database.db", debug=True)
```

This will print the SQL queries to the console as they are executed. If there is
an existing logger in your application then SQLiter will use that logger,
otherwise it will create and use a new logger named `sqliter`.
