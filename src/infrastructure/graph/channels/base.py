"""基础通道类

提供所有通道类型的抽象基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from typing_extensions import Self

from ..types.errors import EmptyChannelError

Value = TypeVar("Value")
Update = TypeVar("Update")
Checkpoint = TypeVar("Checkpoint")

__all__ = ("BaseChannel",)


class BaseChannel(Generic[Value, Update, Checkpoint], ABC):
    """所有通道的基类。"""

    __slots__ = ("key", "typ")

    def __init__(self, typ: Any, key: str = "") -> None:
        self.typ = typ
        self.key = key

    @property
    @abstractmethod
    def ValueType(self) -> Any:
        """通道中存储的值的类型。"""

    @property
    @abstractmethod
    def UpdateType(self) -> Any:
        """通道接收的更新的类型。"""

    # 序列化/反序列化方法

    def copy(self) -> Self:
        """返回通道的副本。
        默认情况下，委托给`checkpoint()`和`from_checkpoint()`。
        子类可以使用更高效的实现覆盖此方法。"""
        return self.from_checkpoint(self.checkpoint())

    def checkpoint(self) -> Checkpoint | Any:
        """返回通道当前状态的可序列化表示。
        如果通道为空（尚未更新），则引发`EmptyChannelError`，
        或不支持检查点。"""
        try:
            return self.get()
        except EmptyChannelError:
            from ..types import MISSING
            return MISSING

    @abstractmethod
    def from_checkpoint(self, checkpoint: Checkpoint | Any) -> Self:
        """返回一个新的相同通道，可选择从检查点初始化。
        如果检查点包含复杂的数据结构，则应复制它们。"""

    # 读取方法

    @abstractmethod
    def get(self) -> Value:
        """返回通道的当前值。

        如果通道为空（尚未更新），则引发`EmptyChannelError`。"""

    def is_available(self) -> bool:
        """如果通道可用（非空），则返回`True`，否则返回`False`。
        子类应覆盖此方法以提供比调用`get()`并捕获`EmptyChannelError`更高效的实现。
        """
        try:
            self.get()
            return True
        except EmptyChannelError:
            return False

    # 写入方法

    @abstractmethod
    def update(self, values: Sequence[Update]) -> bool:
        """使用给定的更新序列更新通道的值。
        序列中更新的顺序是任意的。
        此方法在每一步结束时由Pregel为所有通道调用。
        如果没有更新，则使用空序列调用。
        如果更新序列无效，则引发`InvalidUpdateError`。
        如果通道已更新，则返回`True`，否则返回`False`。"""

    def consume(self) -> bool:
        """通知通道订阅的任务已运行。默认情况下，无操作。
        通道可以使用此方法修改其状态，防止值再次被消耗。

        如果通道已更新，则返回`True`，否则返回`False`。
        """
        return False

    def finish(self) -> bool:
        """通知通道Pregel运行正在完成。默认情况下，无操作。
        通道可以使用此方法修改其状态，防止完成。

        如果通道已更新，则返回`True`，否则返回`False`。
        """
        return False