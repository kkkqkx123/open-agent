"""Checkpoint领域接口定义

定义checkpoint存储和管理的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ICheckpointStore(ABC):
    """Checkpoint存储接口
    
    负责checkpoint数据的持久化存储和检索。
    """
    
    @abstractmethod
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据
        
        Args:
            checkpoint_data: checkpoint数据字典
            
        Returns:
            bool: 是否保存成功
        """
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_by_thread(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_latest(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        pass
    
    @abstractmethod
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        pass


class ICheckpointSerializer(ABC):
    """Checkpoint序列化接口
    
    负责工作流状态的序列化和反序列化。
    """
    
    @abstractmethod
    def serialize(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态
        
        Args:
            state: 工作流状态对象
            
        Returns:
            Dict[str, Any]: 序列化后的状态数据
        """
        pass
    
    @abstractmethod
    def deserialize(self, state_data: Dict[str, Any]) -> Any:
        """反序列化工作流状态
        
        Args:
            state_data: 序列化的状态数据
            
        Returns:
            Any: 反序列化后的工作流状态对象
        """
        pass


class ICheckpointManager(ABC):
    """Checkpoint管理器接口
    
    负责checkpoint的创建、保存、恢复和管理。
    """
    
    @abstractmethod
    async def create_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            metadata: 可选的元数据
            
        Returns:
            str: checkpoint ID
        """
        pass
    
    @abstractmethod
    async def get_checkpoint(self, thread_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Dict[str, Any]]: checkpoint数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出thread的所有checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            List[Dict[str, Any]]: checkpoint列表，按创建时间倒序排列
        """
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, thread_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            bool: 是否删除成功
        """
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint
        
        Args:
            thread_id: thread ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(
        self, 
        thread_id: str, 
        checkpoint_id: str
    ) -> Optional[Any]:
        """从checkpoint恢复状态
        
        Args:
            thread_id: thread ID
            checkpoint_id: checkpoint ID
            
        Returns:
            Optional[Any]: 恢复的工作流状态，如果失败则返回None
        """
        pass
    
    @abstractmethod
    async def auto_save_checkpoint(
        self, 
        thread_id: str, 
        workflow_id: str, 
        state: Any,
        trigger_reason: str
    ) -> Optional[str]:
        """自动保存checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            trigger_reason: 触发原因
            
        Returns:
            Optional[str]: checkpoint ID，如果保存失败则返回None
        """
        pass
    
    @abstractmethod
    async def cleanup_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint
        
        Args:
            thread_id: thread ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        pass

    @abstractmethod
    async def copy_checkpoint(
        self,
        source_thread_id: str,
        source_checkpoint_id: str,
        target_thread_id: str
    ) -> str:
        """复制checkpoint到另一个thread"""
        pass

    @abstractmethod
    async def export_checkpoint(
        self,
        thread_id: str,
        checkpoint_id: str
    ) -> Dict[str, Any]:
        """导出checkpoint数据"""
        pass

    @abstractmethod
    async def import_checkpoint(
        self,
        thread_id: str,
        checkpoint_data: Dict[str, Any]
    ) -> str:
        """导入checkpoint数据"""
        pass


class ICheckpointPolicy(ABC):
    """Checkpoint策略接口
    
    定义何时以及如何保存checkpoint的策略。
    """
    
    @abstractmethod
    def should_save_checkpoint(self, thread_id: str, workflow_id: str, 
                              state: Any, context: Dict[str, Any]) -> bool:
        """判断是否应该保存checkpoint
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            bool: 是否应该保存checkpoint
        """
        pass
    
    @abstractmethod
    def get_checkpoint_metadata(self, thread_id: str, workflow_id: str,
                               state: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """获取checkpoint元数据
        
        Args:
            thread_id: thread ID
            workflow_id: 工作流ID
            state: 工作流状态
            context: 上下文信息
            
        Returns:
            Dict[str, Any]: checkpoint元数据
        """
        pass