"""图引擎策略类型定义

提供重试、缓存等策略相关的类型定义。
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, Union

KeyFuncT = TypeVar("KeyFuncT", bound=Callable[..., Union[str, bytes]])


class RetryPolicy:
    """重试节点的配置。"""

    def __init__(
        self,
        initial_interval: float = 0.5,
        backoff_factor: float = 2.0,
        max_interval: float = 128.0,
        max_attempts: int = 3,
        jitter: bool = True,
        retry_on: Union[
            type[Exception], Sequence[type[Exception]], Callable[[Exception], bool]
        ] = lambda exc: False,
    ):
        """初始化重试策略。

        Args:
            initial_interval: 第一次重试发生前必须经过的时间量（秒）。
            backoff_factor: 每次重试后间隔增加的倍数。
            max_interval: 重试之间可能经过的最长时间（秒）。
            max_attempts: 放弃前的最大尝试次数，包括第一次。
            jitter: 是否在重试之间的间隔中添加随机抖动。
            retry_on: 应触发重试的异常类列表，或应为应触发重试的异常返回True的可调用对象。
        """
        self.initial_interval = initial_interval
        self.backoff_factor = backoff_factor
        self.max_interval = max_interval
        self.max_attempts = max_attempts
        self.jitter = jitter
        self.retry_on = retry_on


@dataclass(frozen=True, slots=True, kw_only=True)
class CachePolicy(Generic[KeyFuncT]):
    """节点的缓存配置。"""

    key_func: KeyFuncT = field(default_factory=lambda: (lambda *args, **kwargs: ""))  # type: ignore[assignment]
    """从节点输入生成缓存键的函数。
    默认为使用pickle对输入进行哈希处理。"""

    ttl: Union[int, None] = None
    """缓存条目的生存时间（秒）。如果为None，则条目永不过期。"""


__all__ = [
    "RetryPolicy",
    "CachePolicy",
]