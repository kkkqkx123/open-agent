"""主题通道实现

可配置的发布/订阅主题通道，允许一个值被多个节点接收。
"""

from __future__ import annotations

from collections.abc import Iterator, Sequence
from typing import Any, Generic

from typing_extensions import Self

from ..types.errors import EmptyChannelError
from .base import BaseChannel, Value

__all__ = ("Topic",)


def _flatten(values: Sequence[Value | list[Value]]) -> Iterator[Value]:
    for value in values:
        if isinstance(value, list):
            yield from value
        else:
            yield value


class Topic(
    Generic[Value],
    BaseChannel[Sequence[Value], Value | list[Value], list[Value]],
):
    """一个可配置的PubSub主题。

    Args:
        typ: 通道中存储的值的类型。
        accumulate: 是否在步骤间累积值。如果为`False`，通道将在每一步后清空。
    """

    __slots__ = ("values", "accumulate")

    def __init__(self, typ: type[Value], accumulate: bool = False) -> None:
        super().__init__(typ)
        # 属性
        self.accumulate = accumulate
        # 状态
        self.values = list[Value]()

    def __eq__(self, value: object) -> bool:
        return isinstance(value, Topic) and value.accumulate == self.accumulate

    @property
    def ValueType(self) -> Any:
        """通道中存储的值的类型。"""
        return Sequence[self.typ]  # type: ignore[name-defined]

    @property
    def UpdateType(self) -> Any:
        """通道接收的更新的类型。"""
        return self.typ | list[self.typ]  # type: ignore[name-defined]

    def copy(self) -> Self:
        """返回通道的副本。"""
        empty = self.__class__(self.typ, self.accumulate)
        empty.key = self.key
        empty.values = self.values.copy()
        return empty

    def checkpoint(self) -> list[Value]:
        return self.values

    def from_checkpoint(self, checkpoint: list[Value]) -> Self:
        empty = self.__class__(self.typ, self.accumulate)
        empty.key = self.key
        from ..types import MISSING
        if checkpoint is not MISSING:
            if isinstance(checkpoint, tuple):
                # 向后兼容
                empty.values = checkpoint[1]
            else:
                empty.values = checkpoint
        return empty

    def update(self, values: Sequence[Value | list[Value]]) -> bool:
        updated = False
        if not self.accumulate:
            updated = bool(self.values)
            self.values = list[Value]()
        if flat_values := tuple(_flatten(values)):
            updated = True
            self.values.extend(flat_values)
        return updated

    def get(self) -> Sequence[Value]:
        if self.values:
            return list(self.values)
        else:
            raise EmptyChannelError

    def is_available(self) -> bool:
        return bool(self.values)