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
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint
        
        Args:
            session_id: 会话ID
            
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
    async def get_latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint
        
        Args:
            session_id: 会话ID
            
        Returns:
            Optional[Dict[str, Any]]: 最新的checkpoint数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个
        
        Args:
            session_id: 会话ID
            max_count: 保留的最大数量
            
        Returns:
            int: 删除的checkpoint数量
        """
        pass
    
    @abstractmethod
    async def get_checkpoints_by_workflow(self, session_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint
        
        Args:
            session_id: 会话ID
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