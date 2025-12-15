# Changelog

This is an auto-generated log of all the changes that have been made to the
project since the first release, with the latest changes at the top.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [v0.10.0](https://github.com/seapagan/sqliter-py/releases/tag/v0.10.0) (December 15, 2025)

**Bug Fixes**

- Ensure python 3.14 compatability ([#87](https://github.com/seapagan/sqliter-py/pull/87)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.9.1...v0.10.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.9.1...v0.10.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.9.1...v0.10.0.patch)

## [0.9.1](https://github.com/seapagan/sqliter-py/releases/tag/0.9.1) (December 09, 2025)

**Dependency Updates**

- Bump requests from 2.32.3 to 2.32.4 ([#85](https://github.com/seapagan/sqliter-py/pull/85)) by [dependabot[bot]](https://github.com/apps/dependabot)
- Bump urllib3 from 2.4.0 to 2.6.0 ([#83](https://github.com/seapagan/sqliter-py/pull/83)) by [dependabot[bot]](https://github.com/apps/dependabot)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.9.0...0.9.1) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.9.0...0.9.1.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.9.0...0.9.1.patch)

## [0.9.0](https://github.com/seapagan/sqliter-py/releases/tag/0.9.0) (December 09, 2025)

> [!CAUTION]
>
> This library is currently NOT compatible with Python 3.14. I am working on
> fixing this.

**New Features**

- Mark as typed library and update deps ([#81](https://github.com/seapagan/sqliter-py/pull/81)) by [seapagan](https://github.com/seapagan)
- Update ruff and fix linting issues; improve logging in demo ([#70](https://github.com/seapagan/sqliter-py/pull/70)) by [seapagan](https://github.com/seapagan)

**Dependency Updates**

- Bump urllib3 from 2.4.0 to 2.6.0 ([#80](https://github.com/seapagan/sqliter-py/pull/80)) by [dependabot[bot]](https://github.com/apps/dependabot)
- Chore(deps): update actions/checkout action to v6 ([#79](https://github.com/seapagan/sqliter-py/pull/79)) by [renovate[bot]](https://github.com/apps/renovate)
- Chore(deps): update astral-sh/setup-uv action to v7 ([#78](https://github.com/seapagan/sqliter-py/pull/78)) by [renovate[bot]](https://github.com/apps/renovate)
- Bump requests from 2.32.3 to 2.32.4 ([#75](https://github.com/seapagan/sqliter-py/pull/75)) by [dependabot[bot]](https://github.com/apps/dependabot)
- Chore(deps): update astral-sh/setup-uv action to v6 ([#72](https://github.com/seapagan/sqliter-py/pull/72)) by [renovate[bot]](https://github.com/apps/renovate)
- Bump jinja2 from 3.1.5 to 3.1.6 ([#68](https://github.com/seapagan/sqliter-py/pull/68)) by [dependabot[bot]](https://github.com/apps/dependabot)
- Bump cryptography from 44.0.0 to 44.0.1 ([#66](https://github.com/seapagan/sqliter-py/pull/66)) by [dependabot[bot]](https://github.com/apps/dependabot)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.8.0...0.9.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.8.0...0.9.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.8.0...0.9.0.patch)

## [0.8.0](https://github.com/seapagan/sqliter-py/releases/tag/0.8.0) (January 28, 2025)

**New Features**

- Implement list, dict, tuple and set as valid field types ([#63](https://github.com/seapagan/sqliter-py/pull/63)) by [seapagan](https://github.com/seapagan)
- Add delete() method to QueryBuilder with comprehensive test coverage ([#61](https://github.com/seapagan/sqliter-py/pull/61)) by [seapagan](https://github.com/seapagan)

**Dependency Updates**

- Update astral-sh/setup-uv action to v5 ([#59](https://github.com/seapagan/sqliter-py/pull/59)) by [renovate[bot]](https://github.com/apps/renovate)
- Update astral-sh/setup-uv action to v4 ([#57](https://github.com/seapagan/sqliter-py/pull/57)) by [renovate[bot]](https://github.com/apps/renovate)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.7.0...0.8.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.7.0...0.8.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.7.0...0.8.0.patch)

## [0.7.0](https://github.com/seapagan/sqliter-py/releases/tag/0.7.0) (October 31, 2024)

**New Features**

- Support the `date` and `datetime` types ([#52](https://github.com/seapagan/sqliter-py/pull/52)) by [seapagan](https://github.com/seapagan)
- Add `created_at` and `updated_at` timestamps to the BaseDBModel ([#49](https://github.com/seapagan/sqliter-py/pull/49)) by [seapagan](https://github.com/seapagan)
- Add some useful properties to the SqliterDB class instance ([#48](https://github.com/seapagan/sqliter-py/pull/48)) by [seapagan](https://github.com/seapagan)

**Bug Fixes**

- Fix missing commits from the previous PR (#49) ([#50](https://github.com/seapagan/sqliter-py/pull/50)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.6.0...0.7.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.6.0...0.7.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.6.0...0.7.0.patch)

## [0.6.0](https://github.com/seapagan/sqliter-py/releases/tag/0.6.0) (October 12, 2024)

**New Features**

- Add ability to mark a field as UNIQUE ([#46](https://github.com/seapagan/sqliter-py/pull/46)) by [seapagan](https://github.com/seapagan)
- Implement user-defined indexes ([#45](https://github.com/seapagan/sqliter-py/pull/45)) by [seapagan](https://github.com/seapagan)

**Bug Fixes**

- Ensure context-manager ignores the `auto_commit` setting. ([#43](https://github.com/seapagan/sqliter-py/pull/43)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.5.0...0.6.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.5.0...0.6.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.5.0...0.6.0.patch)

## [0.5.0](https://github.com/seapagan/sqliter-py/releases/tag/0.5.0) (September 30, 2024)

**Breaking Change!**

This release removes the `create_pk` and `primary_key` attributes from the Model
`Meta` Class. Now, an auto-incrementing primary key is created by default and
the name of the primary key is always `pk`.

**Closed Issues**

- Auto-generated primary key not returned by the Model ([#37](https://github.com/seapagan/sqliter-py/issues/37)) by [seapagan](https://github.com/seapagan)

**Breaking Changes**

- Always create a `pk` primary auto-incrementing key ([#39](https://github.com/seapagan/sqliter-py/pull/39)) by [seapagan](https://github.com/seapagan)

**Bug Fixes**

- Fix `null` filter when combined with others and add tests ([#40](https://github.com/seapagan/sqliter-py/pull/40)) by [seapagan](https://github.com/seapagan)

**Documentation**

- Refactor web docs layout and improve content ([#36](https://github.com/seapagan/sqliter-py/pull/36)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.4.0...0.5.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.4.0...0.5.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.4.0...0.5.0.patch)

## [0.4.0](https://github.com/seapagan/sqliter-py/releases/tag/0.4.0) (September 27, 2024)

**New Features**

- Add `exists_ok` and `force` flags to `create_table` ([#34](https://github.com/seapagan/sqliter-py/pull/34)) by [seapagan](https://github.com/seapagan)
- Add `reset=` to SqliterDB(), to drop all existing tables ([#33](https://github.com/seapagan/sqliter-py/pull/33)) by [seapagan](https://github.com/seapagan)
- Order by primary key if no field specified to `order()` ([#32](https://github.com/seapagan/sqliter-py/pull/32)) by [seapagan](https://github.com/seapagan)
- Add `drop_table` method ([#31](https://github.com/seapagan/sqliter-py/pull/31)) by [seapagan](https://github.com/seapagan)
- Add debug logging option ([#29](https://github.com/seapagan/sqliter-py/pull/29)) by [seapagan](https://github.com/seapagan)
- Create relevant database fields depending on the Model types ([#27](https://github.com/seapagan/sqliter-py/pull/27)) by [seapagan](https://github.com/seapagan)

**Testing**

- Add test coverage where missing ([#28](https://github.com/seapagan/sqliter-py/pull/28)) by [seapagan](https://github.com/seapagan)

**Refactoring**

- Perform some internal refactoring, mostly arranging the tests. ([#30](https://github.com/seapagan/sqliter-py/pull/30)) by [seapagan](https://github.com/seapagan)

**Documentation**

- Add a documentation website and trim down the README ([#25](https://github.com/seapagan/sqliter-py/pull/25)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.3.0...0.4.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.3.0...0.4.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.3.0...0.4.0.patch)

## [0.3.0](https://github.com/seapagan/sqliter-py/releases/tag/0.3.0) (September 23, 2024)

**Breaking Changes**

- Rename 'create_id' to 'create_pk' ([#23](https://github.com/seapagan/sqliter-py/pull/23)) by [seapagan](https://github.com/seapagan)

**New Features**

- Deprecate 'direction=' for 'reverse=' in `order()` method. ([#24](https://github.com/seapagan/sqliter-py/pull/24)) by [seapagan](https://github.com/seapagan)
- Add improved table name generation ([#21](https://github.com/seapagan/sqliter-py/pull/21)) by [seapagan](https://github.com/seapagan)
- Implement an in-memory database option ([#15](https://github.com/seapagan/sqliter-py/pull/15)) by [seapagan](https://github.com/seapagan)
- Allow selecting a subset of the database fields instead of all them ([#12](https://github.com/seapagan/sqliter-py/pull/12)) by [seapagan](https://github.com/seapagan)
- Improve dev tooling and contributor documentation ([#11](https://github.com/seapagan/sqliter-py/pull/11)) by [seapagan](https://github.com/seapagan)

**Dependency Updates**

- Update dependency ruff to v0.6.7 ([#19](https://github.com/seapagan/sqliter-py/pull/19)) by [renovate[bot]](https://github.com/apps/renovate)
- Update dependency pydantic to v2.9.2 ([#18](https://github.com/seapagan/sqliter-py/pull/18)) by [renovate[bot]](https://github.com/apps/renovate)
- Update dependency idna to v3.10 ([#17](https://github.com/seapagan/sqliter-py/pull/17)) by [renovate[bot]](https://github.com/apps/renovate)
- Update dependency zipp to v3.20.2 ([#16](https://github.com/seapagan/sqliter-py/pull/16)) by [renovate[bot]](https://github.com/apps/renovate)
- Update astral-sh/setup-uv action to v3 ([#10](https://github.com/seapagan/sqliter-py/pull/10)) by [renovate[bot]](https://github.com/apps/renovate)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.2.0...0.3.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.2.0...0.3.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.2.0...0.3.0.patch)

## [0.2.0](https://github.com/seapagan/sqliter-py/releases/tag/0.2.0) (September 14, 2024)

**New Features**

- Default to auto_create=True, and add 'commit()' & 'close()' methods ([#9](https://github.com/seapagan/sqliter-py/pull/9)) by [seapagan](https://github.com/seapagan)
- Add more advanced filtering options ([#7](https://github.com/seapagan/sqliter-py/pull/7)) by [seapagan](https://github.com/seapagan)

**Bug Fixes**

- Ensure context manager commits on exit ([#8](https://github.com/seapagan/sqliter-py/pull/8)) by [seapagan](https://github.com/seapagan)

[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.1.1...0.2.0) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.1.1...0.2.0.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.1.1...0.2.0.patch)

## [0.1.1](https://github.com/seapagan/sqliter-py/releases/tag/0.1.1) (September 12, 2024)

Just a documentation fix - README was old version
[`Full Changelog`](https://github.com/seapagan/sqliter-py/compare/0.1.0...0.1.1) | [`Diff`](https://github.com/seapagan/sqliter-py/compare/0.1.0...0.1.1.diff) | [`Patch`](https://github.com/seapagan/sqliter-py/compare/0.1.0...0.1.1.patch)

## [0.1.0](https://github.com/seapagan/sqliter-py/releases/tag/0.1.0) (September 12, 2024)

**New Features**

- Remove transaction exception (TransactionError) ([#4](https://github.com/seapagan/sqliter-py/pull/4)) by [seapagan](https://github.com/seapagan)
- Improve error handling across the library ([#3](https://github.com/seapagan/sqliter-py/pull/3)) by [seapagan](https://github.com/seapagan)
- Add 'limit', 'offset' and 'order' methods ([#2](https://github.com/seapagan/sqliter-py/pull/2)) by [seapagan](https://github.com/seapagan)

**Testing**

- Add a full test suite to the existing code. ([#1](https://github.com/seapagan/sqliter-py/pull/1)) by [seapagan](https://github.com/seapagan)

**Dependency Updates**

- Configure Renovate ([#5](https://github.com/seapagan/sqliter-py/pull/5)) by [renovate[bot]](https://github.com/apps/renovate)

---
*This changelog was generated using [github-changelog-md](http://changelog.seapagan.net/) by [Seapagan](https://github.com/seapagan)*
