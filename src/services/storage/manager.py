"""存储管理服务

提供存储适配器的生命周期管理和统一入口。
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List, Union
from enum import Enum

from src.interfaces.state import IStateStorageAdapter
from core.common.exceptions.state import StorageError, StorageConnectionError
from src.adapters.storage.adapters.memory import MemoryStateStorageAdapter
from src.adapters.storage.adapters.sqlite import SQLiteStateStorageAdapter
from src.adapters.storage.adapters.file import FileStateStorageAdapter


logger = logging.getLogger(__name__)


class StorageType(Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"


class StorageManager:
    """存储管理服务
    
    提供存储适配器的生命周期管理和统一入口。
    """
    
    def __init__(self) -> None:
        """初始化存储管理服务"""
        self._adapters: Dict[str, IStateStorageAdapter] = {}
        self._adapter_configs: Dict[str, Dict[str, Any]] = {}
        self._default_adapter: Optional[str] = None
        self._lock = asyncio.Lock()
        
        logger.info("StorageManager initialized")
    
    async def register_adapter(
        self, 
        name: str, 
        storage_type: Union[str, StorageType], 
        config: Dict[str, Any],
        set_as_default: bool = False
    ) -> bool:
        """注册存储适配器
        
        Args:
            name: 适配器名称
            storage_type: 存储类型
            config: 配置参数
            set_as_default: 是否设为默认适配器
            
        Returns:
            是否注册成功
        """
        try:
            async with self._lock:
                # 检查名称是否已存在
                if name in self._adapters:
                    logger.warning(f"Adapter {name} already exists, updating...")
                    await self.unregister_adapter(name)
                
                # 创建适配器
                adapter = await self._create_adapter(storage_type, config)
                
                # 连接适配器
                await adapter._backend.connect()
                
                # 注册适配器
                self._adapters[name] = adapter
                self._adapter_configs[name] = config.copy()
                
                # 设置默认适配器
                if set_as_default or self._default_adapter is None:
                    self._default_adapter = name
                
                logger.info(f"Registered storage adapter: {name} ({storage_type})")
                return True
                
        except Exception as e:
            logger.error(f"Failed to register adapter {name}: {e}")
            return False
    
    async def unregister_adapter(self, name: str) -> bool:
        """注销存储适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            是否注销成功
        """
        try:
            async with self._lock:
                if name not in self._adapters:
                    logger.warning(f"Adapter {name} not found")
                    return False
                
                # 断开适配器连接
                adapter = self._adapters[name]
                await adapter._backend.disconnect()
                
                # 移除适配器
                del self._adapters[name]
                del self._adapter_configs[name]
                
                # 如果是默认适配器，重新选择默认适配器
                if self._default_adapter == name:
                    self._default_adapter = next(iter(self._adapters.keys()), None)
                
                logger.info(f"Unregistered storage adapter: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to unregister adapter {name}: {e}")
            return False
    
    async def get_adapter(self, name: Optional[str] = None) -> Optional[IStateStorageAdapter]:
        """获取存储适配器
        
        Args:
            name: 适配器名称，如果为None则返回默认适配器
            
        Returns:
            存储适配器或None
        """
        try:
            async with self._lock:
                # 如果未指定名称，使用默认适配器
                if name is None:
                    name = self._default_adapter
                
                if name is None:
                    logger.warning("No default adapter set")
                    return None
                
                return self._adapters.get(name)
                
        except Exception as e:
            logger.error(f"Failed to get adapter {name}: {e}")
            return None
    
    async def list_adapters(self) -> List[Dict[str, Any]]:
        """列出所有已注册的适配器
        
        Returns:
            适配器信息列表
        """
        try:
            async with self._lock:
                adapters_info = []
                
                for name, adapter in self._adapters.items():
                    # 获取适配器健康状态
                    try:
                        is_healthy = adapter.health_check()
                    except Exception as e:
                        is_healthy = False
                        logger.error(f"Health check failed for adapter {name}: {e}")
                    
                    # 获取适配器统计信息
                    try:
                        stats = adapter.get_history_statistics()
                    except Exception as e:
                        stats = {"error": str(e)}
                        logger.error(f"Failed to get statistics for adapter {name}: {e}")
                    
                    adapters_info.append({
                        "name": name,
                        "type": adapter.__class__.__name__.replace("StateStorageAdapter", "").lower(),
                        "is_default": name == self._default_adapter,
                        "is_healthy": is_healthy,
                        "statistics": stats,
                        "config": self._adapter_configs.get(name, {})
                    })
                
                return adapters_info
                
        except Exception as e:
            logger.error(f"Failed to list adapters: {e}")
            return []
    
    async def set_default_adapter(self, name: str) -> bool:
        """设置默认适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            是否设置成功
        """
        try:
            async with self._lock:
                if name not in self._adapters:
                    logger.warning(f"Adapter {name} not found")
                    return False
                
                self._default_adapter = name
                logger.info(f"Set default adapter: {name}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to set default adapter {name}: {e}")
            return False
    
    async def get_default_adapter(self) -> Optional[IStateStorageAdapter]:
        """获取默认适配器
        
        Returns:
            默认适配器或None
        """
        return await self.get_adapter(None)
    
    async def health_check(self, name: Optional[str] = None) -> Dict[str, Any]:
        """执行健康检查
        
        Args:
            name: 适配器名称，如果为None则检查所有适配器
            
        Returns:
            健康检查结果
        """
        try:
            if name is not None:
                # 检查指定适配器
                adapter = await self.get_adapter(name)
                if adapter is None:
                    return {"name": name, "status": "not_found"}
                
                try:
                    is_healthy = adapter.health_check()
                    return {"name": name, "status": "healthy" if is_healthy else "unhealthy"}
                except Exception as e:
                    return {"name": name, "status": "error", "error": str(e)}
            else:
                # 检查所有适配器
                results = {}
                adapters_info = await self.list_adapters()
                
                for adapter_info in adapters_info:
                    adapter_name = adapter_info["name"]
                    results[adapter_name] = {
                        "status": "healthy" if adapter_info["is_healthy"] else "unhealthy",
                        "type": adapter_info["type"],
                        "is_default": adapter_info["is_default"]
                    }
                
                return results
                
        except Exception as e:
            logger.error(f"Failed to perform health check: {e}")
            return {"status": "error", "error": str(e)}
    
    async def cleanup_expired_data(self, name: Optional[str] = None) -> Dict[str, int]:
        """清理过期数据
        
        Args:
            name: 适配器名称，如果为None则清理所有适配器
            
        Returns:
            清理结果
        """
        try:
            results = {}
            
            if name is not None:
                # 清理指定适配器
                adapter = await self.get_adapter(name)
                if adapter is None:
                    return {name: 0}
                
                try:
                    # 这里需要适配器支持清理方法
                    # 由于接口中没有定义，我们暂时返回0
                    results[name] = 0
                except Exception as e:
                    logger.error(f"Failed to cleanup expired data for adapter {name}: {e}")
                    results[name] = 0
            else:
                # 清理所有适配器
                adapters_info = await self.list_adapters()
                
                for adapter_info in adapters_info:
                    adapter_name = adapter_info["name"]
                    try:
                        # 这里需要适配器支持清理方法
                        # 由于接口中没有定义，我们暂时返回0
                        results[adapter_name] = 0
                    except Exception as e:
                        logger.error(f"Failed to cleanup expired data for adapter {adapter_name}: {e}")
                        results[adapter_name] = 0
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to cleanup expired data: {e}")
            return {}
    
    async def backup_all_adapters(self, backup_dir: str = "backups") -> Dict[str, Any]:
        """备份所有适配器
        
        Args:
            backup_dir: 备份目录
            
        Returns:
            备份结果
        """
        try:
            import os
            from pathlib import Path
            import time
            
            # 确保备份目录存在
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # 创建时间戳目录
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            timestamp_dir = backup_path / f"backup_{timestamp}"
            timestamp_dir.mkdir(exist_ok=True)
            
            results = {}
            adapters_info = await self.list_adapters()
            
            for adapter_info in adapters_info:
                adapter_name = adapter_info["name"]
                adapter_type = adapter_info["type"]
                
                try:
                    adapter = await self.get_adapter(adapter_name)
                    if adapter is None:
                        continue
                    
                    # 根据适配器类型执行备份
                    adapter_backup_dir = timestamp_dir / adapter_name
                    adapter_backup_dir.mkdir(exist_ok=True)
                    
                    if adapter_type == "sqlite":
                        sqlite_backup_path: str = adapter.backup_database(str(adapter_backup_dir / "database.db"))
                        if sqlite_backup_path:
                            results[adapter_name] = sqlite_backup_path
                    elif adapter_type == "file":
                        file_backup_path: str = adapter.backup_storage(str(adapter_backup_dir))
                        if file_backup_path:
                            results[adapter_name] = file_backup_path
                    elif adapter_type == "memory":
                        # 内存适配器无法备份，跳过
                        results[adapter_name] = "memory_adapter_no_backup"
                    
                except Exception as e:
                    logger.error(f"Failed to backup adapter {adapter_name}: {e}")
                    results[adapter_name] = f"error: {str(e)}"
            
            logger.info(f"Backup completed: {timestamp_dir}")
            return {"backup_dir": str(timestamp_dir), "results": results}
            
        except Exception as e:
            logger.error(f"Failed to backup adapters: {e}")
            return {"error": str(e)}
    
    async def restore_adapter(
        self, 
        name: str, 
        backup_path: str, 
        storage_type: Union[str, StorageType],
        config: Dict[str, Any]
    ) -> bool:
        """恢复适配器
        
        Args:
            name: 适配器名称
            backup_path: 备份路径
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            是否恢复成功
        """
        try:
            # 先注销现有适配器
            if name in self._adapters:
                await self.unregister_adapter(name)
            
            # 创建新适配器
            adapter = await self._create_adapter(storage_type, config)
            
            # 恢复数据
            adapter_type = storage_type.value if isinstance(storage_type, StorageType) else storage_type
            
            if adapter_type == "sqlite":
                success = adapter.restore_database(backup_path)
            elif adapter_type == "file":
                success = adapter.restore_storage(backup_path)
            else:
                logger.warning(f"Restore not supported for adapter type: {adapter_type}")
                success = False
            
            if success:
                # 连接适配器
                await adapter._backend.connect()
                
                # 注册适配器
                self._adapters[name] = adapter
                self._adapter_configs[name] = config.copy()
                
                logger.info(f"Restored adapter: {name}")
                return True
            else:
                logger.error(f"Failed to restore adapter: {name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to restore adapter {name}: {e}")
            return False
    
    async def _create_adapter(
        self, 
        storage_type: Union[str, StorageType], 
        config: Dict[str, Any]
    ) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            存储适配器
        """
        if isinstance(storage_type, str):
            storage_type = StorageType(storage_type.lower())
        
        if storage_type == StorageType.MEMORY:
            return MemoryStateStorageAdapter(**config)
        elif storage_type == StorageType.SQLITE:
            return SQLiteStateStorageAdapter(**config)
        elif storage_type == StorageType.FILE:
            return FileStateStorageAdapter(**config)
        else:
            raise StorageError(f"Unsupported storage type: {storage_type}")
    
    async def close(self) -> None:
        """关闭存储管理服务"""
        try:
            async with self._lock:
                # 断开所有适配器连接
                for name, adapter in self._adapters.items():
                    try:
                        await adapter._backend.disconnect()
                    except Exception as e:
                        logger.error(f"Failed to disconnect adapter {name}: {e}")
                
                # 清空适配器
                self._adapters.clear()
                self._adapter_configs.clear()
                self._default_adapter = None
                
                logger.info("StorageManager closed")
                
        except Exception as e:
            logger.error(f"Failed to close StorageManager: {e}")
    
    async def __aenter__(self) -> 'StorageManager':
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type: Optional[type], exc_val: Optional[Exception], exc_tb: Optional[object]) -> None:
        """异步上下文管理器出口"""
        await self.close()