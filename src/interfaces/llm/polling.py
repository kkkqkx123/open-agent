"""LLM轮询池管理接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List


class IPollingPoolManager(ABC):
    """轮询池管理器接口"""
    
    @abstractmethod
    def get_pool(self, name: str) -> Optional[Any]:
        """获取轮询池"""
        pass
    
    @abstractmethod
    def list_all_status(self) -> Dict[str, Any]:
        """获取所有轮询池状态"""
        pass
    
    @abstractmethod
    async def shutdown_all(self) -> None:
        """关闭所有轮询池"""
        pass