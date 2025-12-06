"""
检查点服务接口定义

定义检查点服务的核心操作接口，提供统一的检查点管理抽象。
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from collections.abc import AsyncIterator

from src.core.checkpoint.models import Checkpoint, CheckpointTuple


class ICheckpointService(ABC):
    """检查点服务接口
    
    定义检查点管理的核心操作，包括保存、加载、列表和清理等。
    """
    
    @abstractmethod
    async def save_checkpoint(
        self, 
        config: Dict[str, Any], 
        checkpoint: Checkpoint,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """保存检查点
        
        Args:
            config: 可运行配置
            checkpoint: 检查点对象
            metadata: 检查点元数据（可选）
            
        Returns:
            检查点ID
            
        Raises:
            CheckpointError: 保存失败时抛出
        """
        pass
    
    @abstractmethod
    async def load_checkpoint(self, config: Dict[str, Any]) -> Optional[Checkpoint]:
        """加载检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点对象，如果不存在则返回None
            
        Raises:
            CheckpointError: 加载失败时抛出
        """
        pass
    
    @abstractmethod
    async def load_checkpoint_tuple(self, config: Dict[str, Any]) -> Optional[CheckpointTuple]:
        """加载检查点元组
        
        Args:
            config: 可运行配置
            
        Returns:
            检查点元组，如果不存在则返回None
            
        Raises:
            CheckpointError: 加载失败时抛出
        """
        pass
    
    @abstractmethod
    def list_checkpoints(
        self, 
        config: Optional[Dict[str, Any]] = None,
        *,
        filter: Optional[Dict[str, Any]] = None,
        before: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> AsyncIterator[CheckpointTuple]:
        """列出检查点
        
        Args:
            config: 用于过滤检查点的基本配置
            filter: 额外的过滤条件
            before: 列出在此配置之前创建的检查点
            limit: 要返回的最大检查点数
            
        Yields:
            检查点元组的异步迭代器
            
        Raises:
            CheckpointError: 列出失败时抛出
        """
        pass
    
    @abstractmethod
    async def put_writes(
        self,
        config: Dict[str, Any],
        writes: List[tuple[str, Any]],
        task_id: str,
        task_path: str = ""
    ) -> None:
        """存储与检查点关联的中间写入
        
        Args:
            config: 相关检查点的配置
            writes: 要存储的写入列表，每个为(通道, 值)对
            task_id: 创建写入的任务的标识符
            task_path: 创建写入的任务的路径
            
        Raises:
            CheckpointError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, config: Dict[str, Any]) -> bool:
        """删除检查点
        
        Args:
            config: 可运行配置
            
        Returns:
            是否删除成功
            
        Raises:
            CheckpointError: 删除失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, max_age_days: int = 30) -> int:
        """清理旧检查点
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的检查点数量
            
        Raises:
            CheckpointError: 清理失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_stats(self) -> Dict[str, Any]:
        """获取检查点统计信息
        
        Returns:
            统计信息字典
            
        Raises:
            CheckpointError: 获取失败时抛出
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
            
        Raises:
            CheckpointError: 健康检查失败时抛出
        """
        pass