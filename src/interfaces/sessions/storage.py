"""会话仓储接口"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.core.sessions.entities import Session, SessionStatus


class ISessionRepository(ABC):
    """会话仓储接口 - 协调所有会话存储操作"""
    
    @abstractmethod
    async def create(self, session: 'Session') -> bool:
        """创建会话
        
        Args:
            session: 会话实体
            
        Returns:
            是否创建成功
        """
        pass
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional['Session']:
        """获取会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话实体，不存在返回None
        """
        pass
    
    @abstractmethod
    async def update(self, session: 'Session') -> bool:
        """更新会话
        
        Args:
            session: 会话实体
            
        Returns:
            是否更新成功
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def list_by_status(self, status: 'SessionStatus') -> List['Session']:
        """按状态列会话
        
        Args:
            status: 会话状态
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def list_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List['Session']:
        """按日期范围列会话
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        limit: int = 10
    ) -> List['Session']:
        """搜索会话
        
        Args:
            query: 查询字符串
            limit: 返回数量限制
            
        Returns:
            会话列表
        """
        pass
    
    @abstractmethod
    async def get_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量
        
        Returns:
            状态到数量的映射字典
        """
        pass
    
    @abstractmethod
    async def cleanup_old(self, max_age_days: int = 30) -> int:
        """清理旧会话
        
        Args:
            max_age_days: 最大保留天数
            
        Returns:
            清理的会话数量
        """
        pass
    
    @abstractmethod
    async def add_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """添加用户交互
        
        Args:
            session_id: 会话ID
            interaction: 交互数据字典
            
        Returns:
            是否添加成功
        """
        pass
    
    @abstractmethod
    async def get_interactions(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取交互历史
        
        Args:
            session_id: 会话ID
            limit: 返回数量限制
            
        Returns:
            交互列表
        """
        pass
    
    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        pass