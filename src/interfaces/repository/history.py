"""历史Repository接口

定义历史记录数据的存储和检索接口，实现数据访问层的抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IHistoryRepository(ABC):
    """历史记录仓库接口
    
    专注于历史记录数据的存储和检索，不包含业务逻辑。
    """
    
    @abstractmethod
    async def save_history(self, entry: Dict[str, Any]) -> str:
        """保存历史记录
        
        Args:
            entry: 历史记录条目，包含agent_id、timestamp、action等字段
            
        Returns:
            保存的历史记录ID
        """
        pass
    
    @abstractmethod
    async def get_history(self, agent_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """获取历史记录
        
        Args:
            agent_id: 代理ID
            limit: 返回记录数限制
            
        Returns:
            历史记录列表，按时间倒序排列
        """
        pass
    
    @abstractmethod
    async def get_history_by_timerange(
        self, 
        agent_id: str, 
        start_time: datetime, 
        end_time: datetime,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """按时间范围获取历史记录
        
        Args:
            agent_id: 代理ID
            start_time: 开始时间
            end_time: 结束时间
            limit: 返回记录数限制
            
        Returns:
            历史记录列表
        """
        pass
    
    @abstractmethod
    async def delete_history(self, history_id: str) -> bool:
        """删除历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def clear_agent_history(self, agent_id: str) -> bool:
        """清空代理的历史记录
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否清空成功
        """
        pass
    
    @abstractmethod
    async def get_history_statistics(self) -> Dict[str, Any]:
        """获取历史记录统计信息
        
        Returns:
            统计信息字典，包含总记录数、代理数量等
        """
        pass
    
    @abstractmethod
    async def get_history_by_id(self, history_id: str) -> Optional[Dict[str, Any]]:
        """根据ID获取历史记录
        
        Args:
            history_id: 历史记录ID
            
        Returns:
            历史记录，如果不存在则返回None
        """
        pass