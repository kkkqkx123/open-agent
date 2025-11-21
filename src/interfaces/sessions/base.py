"""会话管理基础接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISessionManager(ABC):
    """会话管理器接口 - 负责会话的生命周期管理"""

    @abstractmethod
    async def create_session(self, workflow_config_path: str, metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建新会话
        
        Args:
            workflow_config_path: 工作流配置文件路径
            metadata: 可选的会话元数据
            
        Returns:
            新创建的会话ID
            
        Raises:
            SessionCreationException: 创建失败时抛出
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话详细信息
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            会话详细信息字典，不存在时返回None
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            删除成功返回True，失败返回False
            
        Raises:
            SessionDeletionException: 删除失败时抛出
        """
        pass

    @abstractmethod
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 可选的过滤条件
            
        Returns:
            会话列表
        """
        pass

    @abstractmethod
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态
        
        Args:
            session_id: 会话唯一标识
            status: 新状态
            
        Returns:
            更新成功返回True，失败返回False
        """
        pass

    @abstractmethod
    async def get_session_threads(self, session_id: str) -> List[str]:
        """获取会话关联的线程列表
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            线程ID列表
        """
        pass