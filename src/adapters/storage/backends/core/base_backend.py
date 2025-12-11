"""基础存储后端抽象类

提供轻量级的基础后端实现，专注于基础设施组件管理。
"""

import asyncio
import time
from typing import Dict, Any, Optional
from src.interfaces.dependency_injection import get_logger

from src.interfaces.storage.base import IStorage
from .exceptions import StorageBackendError, ConnectionError, ConfigurationError


logger = get_logger(__name__)


class BaseStorageBackend(IStorage):
    """基础存储后端抽象类
    
    提供基础设施组件管理，不包含具体的数据操作逻辑。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化存储后端
        
        Args:
            **config: 配置参数
        """
        self._config = config
        self._connected = False
        
        # 基础配置验证
        self._validate_config()
        
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
    
    def _validate_config(self) -> None:
        """验证配置
        
        Raises:
            ConfigurationError: 配置无效时抛出
        """
        # 基础配置验证
        required_keys = self._get_required_config_keys()
        for key in required_keys:
            if key not in self._config:
                raise ConfigurationError(
                    f"Missing required config key: {key}",
                    backend_type=self.__class__.__name__,
                    config_key=key
                )
    
    def _get_required_config_keys(self) -> list:
        """获取必需的配置键
        
        Returns:
            必需配置键列表
        """
        # 子类可以重写此方法来定义必需的配置键
        return []
    
    async def connect(self) -> None:
        """连接到存储后端"""
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
        """断开与存储后端的连接"""
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
            backend_health = await self._health_check_impl()
            
            # 添加后端特定信息
            health_info = {
                "backend_type": self.__class__.__name__,
                "connected": self._connected,
                "config": self._get_safe_config(),
                "error_stats": self._error_stats,
                "operation_stats": self._operation_stats,
                "timestamp": time.time(),
                **backend_health
            }
            
            return health_info
            
        except Exception as e:
            self._record_error("health_check", str(e))
            return {
                "backend_type": self.__class__.__name__,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": time.time()
            }
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置
        
        Returns:
            配置字典
        """
        return self._config.copy()
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置
        
        Args:
            config: 新配置
        """
        # 验证新配置
        old_config = self._config.copy()
        self._config.update(config)
        
        try:
            self._validate_config()
            logger.info(f"{self.__class__.__name__} config updated")
        except ConfigurationError as e:
            # 恢复旧配置
            self._config = old_config
            raise e
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        return {
            "error_stats": self._error_stats.copy(),
            "operation_stats": self._operation_stats.copy(),
            "uptime": time.time() - getattr(self, "_start_time", time.time()),
            "connected": self._connected
        }
    
    def get_error_stats(self) -> Dict[str, Any]:
        """获取错误统计
        
        Returns:
            错误统计信息
        """
        return self._error_stats.copy()
    
    def clear_error_stats(self) -> None:
        """清除错误统计"""
        self._error_stats = {
            "total_errors": 0,
            "connection_errors": 0,
            "operation_errors": 0,
            "last_error": None,
            "last_error_time": None
        }
        logger.info(f"{self.__class__.__name__} error stats cleared")
    
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
    
    def _get_safe_config(self) -> Dict[str, Any]:
        """获取安全的配置信息（隐藏敏感信息）
        
        Returns:
            安全的配置字典
        """
        safe_config = {}
        sensitive_keys = ["password", "token", "secret", "key"]
        
        for key, value in self._config.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_config[key] = "***"
            else:
                safe_config[key] = value
        
        return safe_config
    
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