"""基础存储提供者抽象类

提供存储提供者的基础实现。
"""

import asyncio
import time
from abc import abstractmethod
from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from src.interfaces.storage import IStorageProvider
from ..core.exceptions import ProviderError, ConnectionError


logger = get_logger(__name__)


class BaseStorageProvider(IStorageProvider):
    """基础存储提供者抽象类
    
    提供存储提供者的基础功能实现。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化存储提供者
        
        Args:
            **config: 配置参数
        """
        self._config = config
        self._connected = False
        self._transaction_stack = []
        
        # 线程安全锁
        self._lock = asyncio.Lock()
        
        # 错误统计
        self._error_stats = {
            "total_errors": 0,
            "connection_errors": 0,
            "operation_errors": 0,
            "last_error": None,
            "last_error_time": None
        }
        
        # 操作统计
        self._operation_stats = {
            "total_operations": 0,
            "successful_operations": 0,
            "failed_operations": 0,
            "operations_by_type": {}
        }
        
        logger.debug(f"{self.__class__.__name__} initialized with config: {config}")
    
    async def connect(self) -> None:
        """连接到存储"""
        async with self._lock:
            if self._connected:
                return
            
            try:
                await self._connect_impl()
                self._connected = True
                logger.info(f"{self.__class__.__name__} connected")
                
            except Exception as e:
                self._record_error("connection", str(e))
                raise ConnectionError(
                    f"Failed to connect {self.__class__.__name__}: {e}",
                    backend_type=self.__class__.__name__
                )
    
    async def disconnect(self) -> None:
        """断开连接"""
        async with self._lock:
            if not self._connected:
                return
            
            try:
                await self._disconnect_impl()
                self._connected = False
                logger.info(f"{self.__class__.__name__} disconnected")
                
            except Exception as e:
                self._record_error("connection", str(e))
                raise ConnectionError(
                    f"Failed to disconnect {self.__class__.__name__}: {e}",
                    backend_type=self.__class__.__name__
                )
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查
        
        Returns:
            健康状态信息
        """
        try:
            # 基础健康检查
            provider_health = await self._health_check_impl()
            
            # 添加提供者特定信息
            health_info = {
                "provider_type": self.__class__.__name__,
                "connected": self._connected,
                "error_stats": self._error_stats,
                "operation_stats": self._operation_stats,
                "timestamp": time.time(),
                "transaction_stack_size": len(self._transaction_stack),
                **provider_health
            }
            
            return health_info
            
        except Exception as e:
            self._record_error("health_check", str(e))
            return {
                "provider_type": self.__class__.__name__,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    async def begin_transaction(self) -> str:
        """开始事务
        
        Returns:
            事务ID
        """
        if not self._connected:
            raise ConnectionError("Provider not connected")
        
        try:
            transaction_id = await self._begin_transaction_impl()
            self._transaction_stack.append(transaction_id)
            logger.debug(f"Transaction started: {transaction_id}")
            return transaction_id
            
        except Exception as e:
            self._record_error("transaction", str(e))
            raise ProviderError(f"Failed to begin transaction: {e}", operation="begin_transaction")
    
    async def commit_transaction(self, transaction_id: str) -> None:
        """提交事务
        
        Args:
            transaction_id: 事务ID
        """
        if not self._connected:
            raise ConnectionError("Provider not connected")
        
        try:
            await self._commit_transaction_impl(transaction_id)
            
            # 从事务栈中移除
            if transaction_id in self._transaction_stack:
                self._transaction_stack.remove(transaction_id)
            
            logger.debug(f"Transaction committed: {transaction_id}")
            
        except Exception as e:
            self._record_error("transaction", str(e))
            raise ProviderError(f"Failed to commit transaction: {e}", operation="commit_transaction")
    
    async def rollback_transaction(self, transaction_id: str) -> None:
        """回滚事务
        
        Args:
            transaction_id: 事务ID
        """
        if not self._connected:
            raise ConnectionError("Provider not connected")
        
        try:
            await self._rollback_transaction_impl(transaction_id)
            
            # 从事务栈中移除
            if transaction_id in self._transaction_stack:
                self._transaction_stack.remove(transaction_id)
            
            logger.debug(f"Transaction rolled back: {transaction_id}")
            
        except Exception as e:
            self._record_error("transaction", str(e))
            raise ProviderError(f"Failed to rollback transaction: {e}", operation="rollback_transaction")
    
    def _record_error(self, error_type: str, error_message: str) -> None:
        """记录错误
        
        Args:
            error_type: 错误类型
            error_message: 错误消息
        """
        self._error_stats["total_errors"] += 1
        self._error_stats["last_error"] = error_message
        self._error_stats["last_error_time"] = time.time()
        
        if error_type == "connection":
            self._error_stats["connection_errors"] += 1
        else:
            self._error_stats["operation_errors"] += 1
        
        logger.error(f"{self.__class__.__name__} {error_type} error: {error_message}")
    
    def _record_operation(self, operation_type: str, success: bool) -> None:
        """记录操作
        
        Args:
            operation_type: 操作类型
            success: 是否成功
        """
        self._operation_stats["total_operations"] += 1
        
        if success:
            self._operation_stats["successful_operations"] += 1
        else:
            self._operation_stats["failed_operations"] += 1
        
        if operation_type not in self._operation_stats["operations_by_type"]:
            self._operation_stats["operations_by_type"][operation_type] = {
                "total": 0,
                "successful": 0,
                "failed": 0
            }
        
        self._operation_stats["operations_by_type"][operation_type]["total"] += 1
        if success:
            self._operation_stats["operations_by_type"][operation_type]["successful"] += 1
        else:
            self._operation_stats["operations_by_type"][operation_type]["failed"] += 1
    
    # 抽象方法 - 必须由子类实现
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        raise NotImplementedError("Subclasses must implement _connect_impl")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        raise NotImplementedError("Subclasses must implement _disconnect_impl")
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现
        
        Returns:
            健康检查结果
        """
        # 默认实现：返回基本健康状态
        return {
            "status": "healthy" if self._connected else "disconnected"
        }
    
    async def _begin_transaction_impl(self) -> str:
        """实际开始事务实现
        
        Returns:
            事务ID
        """
        # 默认实现：不支持事务
        raise NotImplementedError("Transaction support not implemented")
    
    async def _commit_transaction_impl(self, transaction_id: str) -> None:
        """实际提交事务实现"""
        # 默认实现：不支持事务
        raise NotImplementedError("Transaction support not implemented")
    
    async def _rollback_transaction_impl(self, transaction_id: str) -> None:
        """实际回滚事务实现"""
        # 默认实现：不支持事务
        raise NotImplementedError("Transaction support not implemented")