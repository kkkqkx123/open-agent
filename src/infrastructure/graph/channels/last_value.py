"""最后值通道实现

存储接收到的最后一个值，每步最多只能接收一个值。
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Generic

from typing_extensions import Self

from ..types.errors import GraphErrorCode, create_error_message, InvalidUpdateError

from ..types.errors import EmptyChannelError
from .base import BaseChannel, Value

__all__ = ("LastValue", "LastValueAfterFinish")


class LastValue(Generic[Value], BaseChannel[Value, Value, Value]):
    """存储接收到的最后一个值，每步最多只能接收一个值。"""

    __slots__ = ("value",)

    value: Value | Any

    def __init__(self, typ: Any, key: str = "") -> None:
        super().__init__(typ, key)
        from ..types import MISSING
        self.value = MISSING

    def __eq__(self, value: object) -> bool:
        return isinstance(value, LastValue)

    @property
    def ValueType(self) -> type[Value]:
        """通道中存储的值的类型。"""
        return self.typ

    @property
    def UpdateType(self) -> type[Value]:
        """通道接收的更新的类型。"""
        return self.typ

    def copy(self) -> Self:
        """返回通道的副本。"""
        empty = self.__class__(self.typ, self.key)
        empty.value = self.value
        return empty

    def from_checkpoint(self, checkpoint: Value) -> Self:
        empty = self.__class__(self.typ, self.key)
        from ..types import MISSING
        if checkpoint is not MISSING:
            empty.value = checkpoint
        return empty

    def update(self, values: Sequence[Value]) -> bool:
        if len(values) == 0:
            return False
        if len(values) != 1:
            msg = create_error_message(
                message=f"At key '{self.key}': Can receive only one value per step. Use an Annotated key to handle multiple values.",
                error_code=GraphErrorCode.INVALID_CONCURRENT_GRAPH_UPDATE,
            )
            raise InvalidUpdateError(msg)

        self.value = values[-1]
        return True

    def get(self) -> Value:
        from ..types import MISSING
        if self.value is MISSING:
            raise EmptyChannelError()
        return self.value

    def is_available(self) -> bool:
        from ..types import MISSING
        return self.value is not MISSING

    def checkpoint(self) -> Value:
        return self.value


class LastValueAfterFinish(
    Generic[Value], BaseChannel[Value, Value, tuple[Value, bool]]
):
    """存储接收到的最后一个值，但只有在finish()调用后才可用。
    一旦可用，就清除值。"""

    __slots__ = ("value", "finished")

    value: Value | Any
    finished: bool

    def __init__(self, typ: Any, key: str = "") -> None:
        super().__init__(typ, key)
        from ..types import MISSING
        self.value = MISSING
        self.finished = False

    def __eq__(self, value: object) -> bool:
        return isinstance(value, LastValueAfterFinish)

    @property
    def ValueType(self) -> type[Value]:
        """通道中存储的值的类型。"""
        return self.typ

    @property
    def UpdateType(self) -> type[Value]:
        """通道接收的更新的类型。"""
        return self.typ

    def checkpoint(self) -> tuple[Value | Any, bool] | Any:
        from ..types import MISSING
        if self.value is MISSING:
            return MISSING
        return (self.value, self.finished)

    def from_checkpoint(self, checkpoint: tuple[Value | Any, bool] | Any) -> Self:
        empty = self.__class__(self.typ)
        empty.key = self.key
        from ..types import MISSING
        if checkpoint is not MISSING:
            empty.value, empty.finished = checkpoint
        return empty

    def update(self, values: Sequence[Value | Any]) -> bool:
        if len(values) == 0:
            return False

        self.finished = False
        self.value = values[-1]
        return True

    def consume(self) -> bool:
        if self.finished:
            self.finished = False
            from ..types import MISSING
            self.value = MISSING
            return True

        return False

    def finish(self) -> bool:
        from ..types import MISSING
        if not self.finished and self.value is not MISSING:
            self.finished = True
            return True
        else:
            return False

    def get(self) -> Value:
        from ..types import MISSING
        if self.value is MISSING or not self.finished:
            raise EmptyChannelError()
        return self.value

    def is_available(self) -> bool:
        from ..types import MISSING
        return self.value is not MISSING and self.finished