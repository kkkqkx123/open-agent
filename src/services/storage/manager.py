"""存储管理器

提供存储后端的生命周期管理和统一技术入口。
专注于技术实现，不包含业务逻辑。
"""

import asyncio
from src.services.logger import get_logger
from typing import Dict, Any, Optional, List, Union

from src.core.storage import (
    IStorageBackend,
    IStorageManager,
    StorageConfig,
    StorageOperation,
    StorageResult,
    StorageBackendType,
    StorageOperationType,
    StorageConnectionError,
    StorageOperationError,
    StorageConfigurationError
)


logger = get_logger(__name__)


class StorageManager(IStorageManager):
    """存储管理器 - 技术实现层
    
    专注于存储后端的技术管理，包括连接、生命周期管理等。
    不包含业务逻辑，业务逻辑由上层的编排器处理。
    """
    
    def __init__(self) -> None:
        """初始化存储管理器"""
        self._backends: Dict[str, IStorageBackend] = {}
        self._backend_configs: Dict[str, StorageConfig] = {}
        self._default_backend: Optional[str] = None
        self._lock = asyncio.Lock()
        
        logger.info("StorageManager initialized")
    
    async def register_backend(
        self,
        name: str,
        backend: IStorageBackend,
        config: Optional[StorageConfig] = None,
        set_as_default: bool = False
    ) -> bool:
        """注册存储后端
        
        Args:
            name: 后端名称
            backend: 存储后端实例
            config: 存储配置
            set_as_default: 是否设为默认后端
            
        Returns:
            是否注册成功
        """
        try:
            async with self._lock:
                # 检查名称是否已存在
                if name in self._backends:
                    logger.warning(f"Backend {name} already exists, updating...")
                    await self.unregister_backend(name)
                
                # 连接后端
                if not await backend.connect():
                    raise StorageConnectionError(f"Failed to connect backend {name}")
                
                # 注册后端
                self._backends[name] = backend
                if config:
                    self._backend_configs[name] = config
                
                # 设置默认后端
                if set_as_default or self._default_backend is None:
                    self._default_backend = name
                
                logger.info(f"Registered storage backend: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register backend {name}: {e}")
            return False
    
    async def unregister_backend(self, name: str) -> bool:
        """注销存储后端
        
        Args:
            name: 后端名称
            
        Returns:
            是否注销成功
        """
        try:
            async with self._lock:
                if name not in self._backends:
                    logger.warning(f"Backend {name} not found")
                    return False
                
                # 断开后端连接
                backend = self._backends[name]
                await backend.disconnect()
                
                # 移除后端
                del self._backends[name]
                if name in self._backend_configs:
                    del self._backend_configs[name]
                
                # 如果是默认后端，重新选择默认后端
                if self._default_backend == name:
                    self._default_backend = next(iter(self._backends.keys()), None)
                
                logger.info(f"Unregistered storage backend: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unregister backend {name}: {e}")
            return False
    
    async def get_backend(self, name: Optional[str] = None) -> Optional[IStorageBackend]:
        """获取存储后端
        
        Args:
            name: 后端名称，如果为None则返回默认后端
            
        Returns:
            存储后端或None
        """
        try:
            async with self._lock:
                # 如果未指定名称，使用默认后端
                if name is None:
                    name = self._default_backend
                
                if name is None:
                    logger.warning("No default backend set")
                    return None
                
                return self._backends.get(name)
                
        except Exception as e:
            logger.error(f"Failed to get backend {name}: {e}")
            return None
    
    async def list_backends(self) -> List[Dict[str, Any]]:
        """列出所有已注册的后端
        
        Returns:
            后端信息列表
        """
        try:
            async with self._lock:
                backends_info = []
                
                for name, backend in self._backends.items():
                    # 获取后端健康状态
                    try:
                        health_info = await backend.health_check()
                        is_healthy = health_info.get("status", "unknown") == "healthy"
                    except Exception as e:
                        is_healthy = False
                        logger.error(f"Health check failed for backend {name}: {e}")
                        health_info = {"error": str(e)}
                    
                    # 获取后端统计信息
                    try:
                        stats = await backend.get_statistics()
                    except Exception as e:
                        stats = {"error": str(e)}
                        logger.error(f"Failed to get statistics for backend {name}: {e}")
                    
                    backends_info.append({
                        "name": name,
                        "type": backend.__class__.__name__,
                        "is_default": name == self._default_backend,
                        "is_healthy": is_healthy,
                        "is_connected": await backend.is_connected(),
                        "statistics": stats,
                        "health": health_info,
                        "config": self._backend_configs.get(name)
                    })
                
                return backends_info
                
        except Exception as e:
            logger.error(f"Failed to list backends: {e}")
            return []
    
    async def set_default_backend(self, name: str) -> bool:
        """设置默认后端
        
        Args:
            name: 后端名称
            
        Returns:
            是否设置成功
        """
        try:
            async with self._lock:
                if name not in self._backends:
                    logger.warning(f"Backend {name} not found")
                    return False
                
                self._default_backend = name
                logger.info(f"Set default backend: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set default backend {name}: {e}")
            return False
    
    async def execute_operation(self, operation: StorageOperation) -> StorageResult:
        """执行存储操作
        
        Args:
            operation: 存储操作
            
        Returns:
            操作结果
        """
        try:
            backend = await self.get_backend()
            if backend is None:
                return StorageResult(
                    success=False,
                    error="No backend available",
                    data=None,
                    operation_id=str(id(operation))
                )
            
            # 根据操作类型执行相应的操作
            if operation.operation_type == StorageOperationType.SAVE:
                if operation.key and operation.data:
                    success = await backend.save(operation.key, operation.data)
                    return StorageResult(
                        success=success,
                        data={"key": operation.key} if success else None,
                        error=None,
                        operation_id=str(id(operation))
                    )
                else:
                    return StorageResult(
                        success=False,
                        error="Missing key or data for save operation",
                        data=None,
                        operation_id=str(id(operation))
                    )
            
            elif operation.operation_type == StorageOperationType.LOAD:
                if operation.key:
                    data = await backend.load(operation.key)
                    return StorageResult(
                        success=data is not None,
                        data=data,
                        error=None,
                        operation_id=str(id(operation))
                    )
                else:
                    return StorageResult(
                        success=False,
                        error="Missing key for load operation",
                        data=None,
                        operation_id=str(id(operation))
                    )
            
            elif operation.operation_type == StorageOperationType.DELETE:
                if operation.key:
                    success = await backend.delete(operation.key)
                    return StorageResult(
                        success=success,
                        data={"key": operation.key} if success else None,
                        error=None,
                        operation_id=str(id(operation))
                    )
                else:
                    return StorageResult(
                        success=False,
                        error="Missing key for delete operation",
                        data=None,
                        operation_id=str(id(operation))
                    )
            
            else:
                return StorageResult(
                    success=False,
                    error=f"Unsupported operation type: {operation.operation_type}",
                    data=None,
                    operation_id=str(id(operation))
                )
                
        except Exception as e:
            logger.error(f"Failed to execute operation {operation.operation_type}: {e}")
            return StorageResult(
                success=False,
                error=str(e),
                data=None,
                operation_id=str(id(operation))
            )
    
    async def execute_batch_operations(self, operations: List[StorageOperation]) -> List[StorageResult]:
        """批量执行存储操作
        
        Args:
            operations: 存储操作列表
            
        Returns:
            操作结果列表
        """
        results = []
        for operation in operations:
            result = await self.execute_operation(operation)
            results.append(result)
        return results
    
    async def close(self) -> None:
        """关闭存储管理器"""
        try:
            async with self._lock:
                # 断开所有后端连接
                for name, backend in self._backends.items():
                    try:
                        await backend.disconnect()
                    except Exception as e:
                        logger.error(f"Failed to disconnect backend {name}: {e}")
                
                # 清空后端
                self._backends.clear()
                self._backend_configs.clear()
                self._default_backend = None
                
                logger.info("StorageManager closed")
                
        except Exception as e:
            logger.error(f"Failed to close StorageManager: {e}")
    
    async def __aenter__(self) -> 'StorageManager':
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """异步上下文管理器出口"""
        await self.close()