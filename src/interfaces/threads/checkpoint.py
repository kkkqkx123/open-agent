"""Thread检查点接口定义

定义Thread检查点的核心接口，提供类型安全的操作。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...core.threads.checkpoints.storage.models import (
    ThreadCheckpoint,
    CheckpointStatus,
    CheckpointType,
    CheckpointMetadata,
    CheckpointStatistics
)


class IThreadCheckpointStorage(ABC):
    """Thread检查点存储接口
    
    负责Thread检查点数据的持久化存储和检索。
    """
    
    @abstractmethod
    async def save_checkpoint(self, thread_id: str, checkpoint: ThreadCheckpoint) -> str:
        """保存Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint: 检查点对象
            
        Returns:
            str: 保存的检查点ID
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def load_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """加载Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            Optional[ThreadCheckpoint]: 检查点对象，如果不存在则返回None
            
        Raises:
            CheckpointNotFoundError: 检查点不存在时抛出
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str, status: Optional[CheckpointStatus] = None) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点
        
        Args:
            thread_id: Thread ID
            status: 可选的状态过滤
            
        Returns:
            List[ThreadCheckpoint]: 检查点列表，按创建时间倒序排列
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Optional[ThreadCheckpoint]: 最新的检查点对象，如果不存在则返回None
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点，保留最新的max_count个
        
        Args:
            thread_id: Thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的检查点数量
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_checkpoint_statistics(self, thread_id: str) -> CheckpointStatistics:
        """获取Thread检查点统计信息
        
        Args:
            thread_id: Thread ID
            
        Returns:
            CheckpointStatistics: 统计信息
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass


class IThreadCheckpointManager(ABC):
    """Thread检查点管理器接口
    
    负责Thread检查点的创建、保存、恢复和管理。
    """
    
    @abstractmethod
    async def create_checkpoint(
        self, 
        thread_id: str, 
        state: Dict[str, Any],
        checkpoint_type: CheckpointType = CheckpointType.AUTO,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建Thread检查点
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            checkpoint_type: 检查点类型
            metadata: 可选的元数据
            
        Returns:
            str: 检查点ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            Optional[ThreadCheckpoint]: 检查点对象，如果不存在则返回None
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[ThreadCheckpoint]:
        """列出Thread的所有检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            List[ThreadCheckpoint]: 检查点列表，按创建时间倒序排列
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除Thread检查点
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[ThreadCheckpoint]:
        """获取Thread的最新检查点
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Optional[ThreadCheckpoint]: 最新的检查点对象，如果不存在则返回None
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复状态
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            Optional[Dict[str, Any]]: 恢复的工作流状态，如果失败则返回None
            
        Raises:
            CheckpointNotFoundError: 检查点不存在时抛出
            CheckpointRestoreError: 恢复失败时抛出
        """
        pass
    
    @abstractmethod
    async def auto_save_checkpoint(
        self, 
        thread_id: str, 
        state: Dict[str, Any],
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存检查点
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            trigger_reason: 触发原因
            
        Returns:
            Optional[str]: 检查点ID，如果保存失败则返回None
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def cleanup_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点
        
        Args:
            thread_id: Thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的检查点数量
            
        Raises:
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制检查点到另一个Thread
        
        Args:
            source_thread_id: 源Thread ID
            source_checkpoint_id: 源检查点ID
            target_thread_id: 目标Thread ID
            
        Returns:
            str: 新检查点的ID
            
        Raises:
            CheckpointNotFoundError: 检查点不存在时抛出
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def export_checkpoint(self, thread_id: str, checkpoint_id: str) -> Dict[str, Any]:
        """导出检查点数据
        
        Args:
            thread_id: Thread ID
            checkpoint_id: 检查点ID
            
        Returns:
            Dict[str, Any]: 导出的检查点数据
            
        Raises:
            CheckpointNotFoundError: 检查点不存在时抛出
            CheckpointStorageError: 存储失败时抛出
        """
        pass
    
    @abstractmethod
    async def import_checkpoint(self, thread_id: str, checkpoint_data: Dict[str, Any]) -> str:
        """导入检查点数据
        
        Args:
            thread_id: Thread ID
            checkpoint_data: 检查点数据
            
        Returns:
            str: 导入的检查点ID
            
        Raises:
            CheckpointValidationError: 验证失败时抛出
            CheckpointStorageError: 存储失败时抛出
        """
        pass


class IThreadCheckpointSerializer(ABC):
    """Thread检查点序列化接口
    
    负责Thread检查点状态的序列化和反序列化。
    """
    
    @abstractmethod
    def serialize_checkpoint(self, checkpoint: ThreadCheckpoint) -> str:
        """序列化检查点到字符串格式
        
        Args:
            checkpoint: 检查点对象
            
        Returns:
            str: 序列化后的检查点字符串
            
        Raises:
            CheckpointValidationError: 序列化失败时抛出
        """
        pass
    
    @abstractmethod
    def deserialize_checkpoint(self, data: str) -> ThreadCheckpoint:
        """从字符串格式反序列化检查点
        
        Args:
            data: 序列化的检查点字符串
            
        Returns:
            ThreadCheckpoint: 反序列化后的检查点对象
            
        Raises:
            CheckpointValidationError: 反序列化失败时抛出
        """
        pass
    
    @abstractmethod
    def serialize_state(self, state: Dict[str, Any]) -> str:
        """序列化状态到字符串格式
        
        Args:
            state: 状态字典
            
        Returns:
            str: 序列化后的状态字符串
            
        Raises:
            CheckpointValidationError: 序列化失败时抛出
        """
        pass
    
    @abstractmethod
    def deserialize_state(self, data: str) -> Dict[str, Any]:
        """从字符串格式反序列化状态
        
        Args:
            data: 序列化的状态字符串
            
        Returns:
            Dict[str, Any]: 反序列化后的状态字典
            
        Raises:
            CheckpointValidationError: 反序列化失败时抛出
        """
        pass


class IThreadCheckpointPolicy(ABC):
    """Thread检查点策略接口
    
    定义何时以及如何保存检查点的策略。
    """
    
    @abstractmethod
    def should_save_checkpoint(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """判断是否应该保存检查点
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该保存检查点
        """
        pass
    
    @abstractmethod
    def get_checkpoint_metadata(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """获取检查点元数据
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: 检查点元数据
        """
        pass
    
    @abstractmethod
    def get_checkpoint_type(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> CheckpointType:
        """获取检查点类型
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            CheckpointType: 检查点类型
        """
        pass
    
    @abstractmethod
    def get_expiration_hours(self, thread_id: str, state: Dict[str, Any], context: Dict[str, Any]) -> Optional[int]:
        """获取检查点过期时间（小时）
        
        Args:
            thread_id: Thread ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Optional[int]: 过期小时数，None表示永不过期
        """
        pass