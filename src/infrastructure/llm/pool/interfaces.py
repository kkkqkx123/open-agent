from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from threading import Lock, RLock
import asyncio
from datetime import datetime, timedelta


class IConnectionPool(ABC):
    """连接池接口"""
    
    @abstractmethod
    async def acquire(self, base_url: str) -> Any:
        """获取连接"""
        pass
    
    @abstractmethod
    async def release(self, base_url: str, connection: Any) -> None:
        """释放连接"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取连接池统计信息"""
        pass