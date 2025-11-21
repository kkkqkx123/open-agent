"""会话存储接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class ISessionStore(ABC):
    """会话存储接口 - 负责会话数据的持久化"""

    @abstractmethod
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话唯一标识
            session_data: 会话数据字典
            
        Returns:
            保存成功返回True，失败返回False
            
        Raises:
            SessionStoreException: 存储操作失败时抛出
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            会话数据字典，不存在时返回None
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            删除成功返回True，失败返回False
        """
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Returns:
            会话列表，每个元素是会话基本信息的字典
        """
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话唯一标识
            
        Returns:
            存在返回True，不存在返回False
        """
        pass