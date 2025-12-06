"""
基础检查点存储后端

提供检查点存储的基础抽象类。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict

from src.core.checkpoint.interfaces import ICheckpointRepository
from src.core.checkpoint.models import Checkpoint


class BaseCheckpointBackend(ICheckpointRepository):
    """基础检查点存储后端"""
    
    def __init__(self, **config: Any) -> None:
        """初始化后端
        
        Args:
            config: 配置参数
        """
        self._config = config
        self._connected = False
    
    async def connect(self) -> None:
        """连接到存储后端"""
        if not self._connected:
            await self._do_connect()
            self._connected = True
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        if self._connected:
            await self._do_disconnect()
            self._connected = False
    
    @abstractmethod
    async def _do_connect(self) -> None:
        """执行连接操作"""
        pass
    
    @abstractmethod
    async def _do_disconnect(self) -> None:
        """执行断开连接操作"""
        pass
    
    def _check_connection(self) -> None:
        """检查连接状态"""
        if not self._connected:
            raise RuntimeError("Storage backend is not connected")