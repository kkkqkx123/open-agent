"""
检查点保存器接口定义

定义检查点保存器的抽象接口，兼容LangGraph的检查点保存器规范。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from collections.abc import AsyncIterator, Iterator, Sequence

V = TypeVar("V", int, float, str)


class ICheckpointSaver(Generic[V], ABC):
    """检查点保存器接口
    
    兼容LangGraph的检查点保存器规范，提供检查点存储的抽象接口。
    """
    
    @abstractmethod
    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        pass
    
    @abstractmethod
    def get_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """使用给定配置获取检查点元组
        
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
    ) -> Iterator[Dict[str, Any]]:
        """列出匹配给定条件的检查点
        
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
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """存储带有其配置和元数据的检查点
        
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
        """存储与检查点关联的中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        pass
    
    async def aget(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点
        
        Args:
            config: 指定要检索的检查点的配置
            
        Returns:
            请求的检查点，如果未找到则为None
        """
        return self.get(config)
    
    async def aget_tuple(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """异步获取检查点元组
        
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
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步列出匹配给定条件的检查点
        
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
        checkpoint: Dict[str, Any],
        metadata: Dict[str, Any],
        new_versions: Dict[str, V],
    ) -> Dict[str, Any]:
        """异步存储检查点
        
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
        """异步存储中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
        """
        self.put_writes(config, writes, task_id, task_path)
    
    def get_next_version(self, current: Optional[V], channel: None) -> V:
        """生成通道的下一个版本ID
        
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