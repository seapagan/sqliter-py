# Changelog

This is an auto-generated log of all the changes that have been made to the
project since the first release, with the latest changes at the top.

This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


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
