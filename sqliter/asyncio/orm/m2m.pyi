from typing import Any, Generic, Protocol, TypeVar, overload

from sqliter.asyncio.db import AsyncSqliterDB
from sqliter.asyncio.query import AsyncQueryBuilder
from sqliter.orm.m2m import M2MSQLMetadata, ManyToManyOptions
from sqliter.query.query import FilterValue

_T = TypeVar("_T")

class HasPKAndContext(Protocol):
    pk: int | None
    db_context: Any | None

class AsyncManyToManyManager(Generic[_T]):
    _instance: HasPKAndContext
    _to_model: type[_T]
    _from_model: type[Any]
    _junction_table: str
    _db: AsyncSqliterDB | None
    _current_cache_key: str | None
    _reverse_cache_key: str | None

    def __init__(
        self,
        instance: HasPKAndContext,
        to_model: type[_T],
        from_model: type[Any],
        junction_table: str,
        db_context: AsyncSqliterDB | None,
        options: ManyToManyOptions | None = ...,
    ) -> None: ...
    @property
    def sql_metadata(self) -> M2MSQLMetadata: ...
    def configure_cache_keys(
        self,
        *,
        current_cache_key: str | None,
        reverse_cache_key: str | None,
    ) -> None: ...
    def _select_related_ids_sql(self) -> str: ...
    def _clear_sql(self) -> tuple[str, tuple[int, ...]]: ...
    def _count_sql(self) -> str: ...
    def _get_instance_pk(self) -> int: ...
    async def add(self, *instances: _T) -> None: ...
    async def remove(self, *instances: _T) -> None: ...
    async def clear(self) -> None: ...
    async def set(self, *instances: _T) -> None: ...
    async def fetch_all(self) -> list[_T]: ...
    async def fetch_one(self) -> _T | None: ...
    async def count(self) -> int: ...
    async def exists(self) -> bool: ...
    async def filter(
        self,
        **kwargs: FilterValue,
    ) -> AsyncQueryBuilder[Any]: ...

class AsyncPrefetchedM2MResult(Generic[_T]):
    _items: list[_T]
    _manager: AsyncManyToManyManager[_T]

    def __init__(
        self,
        cached_items: list[_T],
        manager: AsyncManyToManyManager[_T],
    ) -> None: ...
    @property
    def sql_metadata(self) -> M2MSQLMetadata: ...
    async def fetch_all(self) -> list[_T]: ...
    async def fetch_one(self) -> _T | None: ...
    async def count(self) -> int: ...
    async def exists(self) -> bool: ...
    async def filter(
        self,
        **kwargs: FilterValue,
    ) -> AsyncQueryBuilder[Any]: ...
    async def add(self, *instances: _T) -> None: ...
    async def remove(self, *instances: _T) -> None: ...
    async def clear(self) -> None: ...
    async def set(self, *instances: _T) -> None: ...

class AsyncManyToMany(Generic[_T]):
    to_model: type[_T] | str
    related_name: str | None
    name: str | None
    owner: type | None
    _junction_table: str | None

    def __init__(
        self,
        to_model: type[_T] | str,
        *,
        through: str | None = ...,
        related_name: str | None = ...,
        symmetrical: bool = ...,
    ) -> None: ...
    def __set_name__(self, owner: type, name: str) -> None: ...
    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> AsyncManyToMany[_T]: ...
    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object],
    ) -> AsyncManyToManyManager[_T] | AsyncPrefetchedM2MResult[_T]: ...
    def __set__(self, instance: object, value: object) -> None: ...

class AsyncReverseManyToMany:
    _from_model: type[Any]
    _to_model: type[Any]
    _junction_table: str
    _related_name: str
    _symmetrical: bool
    _forward_name: str | None

    def __init__(
        self,
        from_model: type[Any],
        to_model: type[Any],
        junction_table: str,
        related_name: str,
        *,
        symmetrical: bool = ...,
        forward_name: str | None = ...,
    ) -> None: ...
    @property
    def sql_metadata(self) -> M2MSQLMetadata: ...
    @property
    def _swap_columns(self) -> bool: ...
    @overload
    def __get__(
        self,
        instance: None,
        owner: type[object],
    ) -> AsyncReverseManyToMany: ...
    @overload
    def __get__(
        self,
        instance: object,
        owner: type[object],
    ) -> AsyncManyToManyManager[Any] | AsyncPrefetchedM2MResult[Any]: ...
    def __set__(self, instance: object, value: object) -> None: ...
