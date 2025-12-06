"""二元操作符聚合通道实现

存储将二元操作符应用于当前值和每个新值的结果。
"""

import collections.abc
from collections.abc import Callable, Sequence
from typing import Generic, cast

from typing_extensions import NotRequired, Required, Self

from ..types.errors import EmptyChannelError
from .base import BaseChannel, Value

__all__ = ("BinaryOperatorAggregate",)


# 从typing_extensions适配
def _strip_extras(t):  # type: ignore[no-untyped-def]
    """从给定类型中剥离Annotated、Required和NotRequired。"""
    if hasattr(t, "__origin__"):
        return _strip_extras(t.__origin__)
    if hasattr(t, "__origin__") and t.__origin__ in (Required, NotRequired):
        return _strip_extras(t.__args__[0])

    return t


class BinaryOperatorAggregate(Generic[Value], BaseChannel[Value, Value, Value]):
    """存储将二元操作符应用于当前值和每个新值的结果。

    ```python
    import operator

    total = Channels.BinaryOperatorAggregate(int, operator.add)
    ```
    """

    __slots__ = ("value", "operator")

    def __init__(self, typ: type[Value], operator: Callable[[Value, Value], Value]):
        super().__init__(typ)
        self.operator = operator
        # 来自typing或collections.abc的特殊形式不可实例化
        # 所以我们需要将它们替换为具体的对应项
        concrete_typ: type[Value] = cast(type[Value], _strip_extras(typ))
        if concrete_typ in (collections.abc.Sequence, collections.abc.MutableSequence):
            concrete_typ = cast(type[Value], list)
        if concrete_typ in (collections.abc.Set, collections.abc.MutableSet):
            concrete_typ = cast(type[Value], set)
        if concrete_typ in (collections.abc.Mapping, collections.abc.MutableMapping):
            concrete_typ = cast(type[Value], dict)
        try:
            self.value = concrete_typ()
        except Exception:
            from ..types import MISSING
            self.value = MISSING

    def __eq__(self, value: object) -> bool:
        return isinstance(value, BinaryOperatorAggregate) and (
            value.operator is self.operator
            if value.operator.__name__ != "<lambda>"
            and self.operator.__name__ != "<lambda>"
            else True
        )

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
        empty = self.__class__(self.typ, self.operator)
        empty.key = self.key
        empty.value = self.value
        return empty

    def from_checkpoint(self, checkpoint: Value) -> Self:
        empty = self.__class__(self.typ, self.operator)
        empty.key = self.key
        from ..types import MISSING
        if checkpoint is not MISSING:
            empty.value = checkpoint
        return empty

    def update(self, values: Sequence[Value]) -> bool:
        if not values:
            return False
        from ..types import MISSING
        if self.value is MISSING:
            self.value = values[0]
            values = values[1:]
        for value in values:
            self.value = self.operator(cast(Value, self.value), value)
        return True

    def get(self) -> Value:
        from ..types import MISSING
        if self.value is MISSING:
            raise EmptyChannelError()
        return cast(Value, self.value)

    def is_available(self) -> bool:
        from ..types import MISSING
        return self.value is not MISSING

    def checkpoint(self) -> Value:
        from ..types import MISSING
        if self.value is MISSING:
            raise EmptyChannelError()
        return cast(Value, self.value)