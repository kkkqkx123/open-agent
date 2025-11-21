"""会话业务逻辑接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISessionService(ABC):
    """会话业务服务接口 - 定义会话相关的业务逻辑"""
    
    @abstractmethod
    async def create_session_with_thread(
        self, 
        session_config: Dict[str, Any],
        thread_config: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建会话并关联线程
        
        Args:
            session_config: 会话配置
            thread_config: 线程配置（可选）
            
        Returns:
            会话ID
        """
        pass
    
    @abstractmethod
    async def update_session_metadata(self, session_id: str, metadata: Dict[str, Any]) -> bool:
        """更新会话元数据
        
        Args:
            session_id: 会话ID
            metadata: 新的元数据
            
        Returns:
            更新成功返回True
        """
        pass
    
    @abstractmethod
    async def increment_message_count(self, session_id: str) -> int:
        """增加消息计数
        
        Args:
            session_id: 会话ID
            
        Returns:
            更新后的消息数量
        """
        pass
    
    @abstractmethod
    async def increment_checkpoint_count(self, session_id: str) -> int:
        """增加检查点计数
        
        Args:
            session_id: 会话ID
            
        Returns:
            更新后的检查点数量
        """
        pass
    
    @abstractmethod
    async def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话摘要信息
        """
        pass
    
    @abstractmethod
    async def list_sessions_by_status(self, status: str) -> List[Dict[str, Any]]:
        """按状态列会话
        
        Args:
            status: 会话状态
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def cleanup_inactive_sessions(self, max_age_hours: int = 24) -> int:
        """清理不活动的会话
        
        Args:
            max_age_hours: 最大存活时间（小时）
            
        Returns:
            清理的会话数量
        """
        pass