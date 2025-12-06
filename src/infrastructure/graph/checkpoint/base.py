"""基础检查点保存器

提供检查点保存器的抽象基类。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator, Iterator, Sequence
from typing import Any, Dict, Generic, List, Optional, TypeVar

V = TypeVar("V", int, float, str)

__all__ = ("BaseCheckpointSaver", "Checkpoint", "CheckpointMetadata", "CheckpointTuple")


class CheckpointMetadata(Dict[str, Any]):
    """检查点元数据。"""
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化检查点元数据。
        
        Args:
            **kwargs: 元数据字段
        """
        super().__init__()
        self.update(kwargs)
    
    @property
    def source(self) -> Optional[str]:
        """检查点来源。"""
        return self.get("source")
    
    @property
    def step(self) -> Optional[int]:
        """检查点步数。"""
        return self.get("step")
    
    @property
    def parents(self) -> Optional[Dict[str, str]]:
        """父检查点ID映射。"""
        return self.get("parents")


class Checkpoint(Dict[str, Any]):
    """特定时间点的状态快照。"""
    
    def __init__(self, **kwargs: Any) -> None:
        """初始化检查点。
        
        Args:
            **kwargs: 检查点字段
        """
        super().__init__()
        self.update(kwargs)
    
    @property
    def id(self) -> Optional[str]:
        """检查点ID。"""
        return self.get("id")
    
    @property
    def ts(self) -> Optional[str]:
        """时间戳。"""
        return self.get("ts")
    
    @property
    def channel_values(self) -> Optional[Dict[str, Any]]:
        """通道值映射。"""
        return self.get("channel_values")
    
    @property
    def channel_versions(self) -> Optional[Dict[str, Any]]:
        """通道版本映射。"""
        return self.get("channel_versions")
    
    @property
    def versions_seen(self) -> Optional[Dict[str, Any]]:
        """每个节点看到的通道版本映射。"""
        return self.get("versions_seen")


class CheckpointTuple:
    """包含检查点及其相关数据的元组。"""
    
    def __init__(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        parent_config: Optional[Dict[str, Any]] = None,
        pending_writes: Optional[List[Any]] = None
    ):
        """初始化检查点元组。
        
        Args:
            config: 可运行配置
            checkpoint: 检查点数据
            metadata: 检查点元数据
            parent_config: 父配置
            pending_writes: 待写入数据
        """
        self.config = config
        self.checkpoint = checkpoint
        self.metadata = metadata
        self.parent_config = parent_config
        self.pending_writes = pending_writes or []


class BaseCheckpointSaver(Generic[V], ABC):
    """检查点保存器的基类。
    
    检查点保存器允许LangGraph代理在多个交互中持久化其状态。
    """
    
    def __init__(self) -> None:
        """初始化检查点保存器。"""
        pass
    
    @abstractmethod
    def get(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """使用给定配置获取检查点。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        pass
    
    @abstractmethod
    def get_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """使用给定配置获取检查点元组。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        pass
    
    @abstractmethod
    def list(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> Iterator[CheckpointTuple]:
        """列出匹配给定条件的检查点。
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            匹配的检查点元组的迭代器
        """
        pass
    
    @abstractmethod
    def put(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点。
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        pass
    
    @abstractmethod
    def put_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """存储与检查点关联的中间写入。
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        pass
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """异步获取检查点。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        return self.get(config)
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """异步获取检查点元组。
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点元组，如果未找到则为None
        """
        return self.get_tuple(config)
    
    async def alist(
        self,
        config: Optional[Dict[str, Any]],
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterator[CheckpointTuple]:
        """异步列出匹配给定条件的检查点。
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            匹配的检查点元组的异步迭代器
        """
        for item in self.list(config, filter=filter, before=before, limit=limit):
            yield item
    
    async def aput(
        self,
        config: Dict[str, Any],
        checkpoint: Checkpoint,
        metadata: CheckpointMetadata,
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """异步存储检查点。
        
        Args:
            config: 检查点的配置
            checkpoint: 要存储的检查点
            metadata: 检查点的额外元数据
            new_versions: 作为此写入的新通道版本
            
        Returns:
            存储检查点后更新的配置
        """
        return self.put(config, checkpoint, metadata, new_versions)
    
    async def aput_writes(
        self,
        config: Dict[str, Any],
        writes: Sequence[tuple[str, Any]],
        task_id: str,
        task_path: str = "",
    ) -> None:
        """异步存储中间写入。
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        self.put_writes(config, writes, task_id, task_path)
    
    def get_next_version(self, current: Optional[V], channel: None) -> V:
        """生成通道的下一个版本ID。
        
        默认使用整数版本，每次递增1。如果覆盖，可以使用str/int/float版本，
        只要它们是单调递增的。
        
        Args:
            current: 通道的当前版本标识符(int、float或str)
            channel: 已弃用的参数，为向后兼容保留
            
        Returns:
            V: 下一个版本标识符，必须是递增的
        """
        if isinstance(current, str):
            raise NotImplementedError
        elif current is None:
            return 1  # type: ignore
        else:
            return current + 1