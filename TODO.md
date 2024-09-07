# TODO

- allow adding multiple indexes to each table as well as the primary index.
- rewrite the logic - all licenses scanned once at first startup and stored into
  a sqlite database. Then, the database is used to generate the license list and
  licenses. Add a flag to rescan if needed.
