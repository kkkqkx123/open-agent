"""状态Repository接口

定义状态数据的存储和检索接口，实现数据访问层的抽象。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IStateRepository(ABC):
    """状态存储仓库接口
    
    专注于状态数据的存储和检索，不包含业务逻辑。
    """
    
    @abstractmethod
    async def save_state(self, agent_id: str, state_data: Dict[str, Any]) -> str:
        """保存状态
        
        Args:
            agent_id: 代理ID
            state_data: 状态数据
            
        Returns:
            保存的状态ID
        """
        pass
    
    @abstractmethod
    async def load_state(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """加载状态
        
        Args:
            agent_id: 代理ID
            
        Returns:
            状态数据，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def delete_state(self, agent_id: str) -> bool:
        """删除状态
        
        Args:
            agent_id: 代理ID
            
        Returns:
            是否删除成功
        """
        pass
    
    @abstractmethod
    async def exists_state(self, agent_id: str) -> bool:
        """检查状态是否存在
        
        Args:
            agent_id: 代理ID
            
        Returns:
            状态是否存在
        """
        pass
    
    @abstractmethod
    async def list_states(self, limit: int = 100) -> List[Dict[str, Any]]:
        """列出所有状态
        
        Args:
            limit: 返回记录数限制
            
        Returns:
            状态列表
        """
        pass