"""存储服务依赖注入注册

提供存储相关服务的依赖注入注册功能。
"""

import logging
from typing import Dict, Any, Optional

from src.services.container import container, ServiceLifetime
from src.services.storage import StorageManager, StorageConfigManager, StorageMigrationService
from src.adapters.storage import (
    get_factory_registry,
    create_storage_adapter,
    register_storage_factory,
    register_custom_storage_factory
)


logger = logging.getLogger(__name__)


def register_storage_services() -> None:
    """注册存储相关服务到依赖注入容器"""
    try:
        # 注册存储配置管理器（单例）
        container.register(
            "storage_config_manager",
            StorageConfigManager,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册存储管理器（单例）
        container.register(
            "storage_manager",
            StorageManager,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册存储迁移服务（单例）
        container.register(
            "storage_migration_service",
            StorageMigrationService,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册存储适配器工厂注册表（单例）
        container.register(
            "storage_factory_registry",
            get_factory_registry,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("Storage services registered to dependency injection container")
        
    except Exception as e:
        logger.error(f"Failed to register storage services: {e}")
        raise


def register_storage_adapter(
    name: str,
    adapter_type: str,
    config: Dict[str, Any],
    set_as_default: bool = False
) -> None:
    """注册存储适配器到存储管理器
    
    Args:
        name: 适配器名称
        adapter_type: 适配器类型
        config: 配置参数
        set_as_default: 是否设为默认适配器
    """
    try:
        # 获取存储管理器
        storage_manager = container.resolve("storage_manager")
        
        # 创建并注册适配器
        import asyncio
        
        async def register_adapter():
            adapter = create_storage_adapter(adapter_type, config)
            await storage_manager.register_adapter(name, adapter_type, config, set_as_default)
        
        # 运行异步注册
        asyncio.run(register_adapter())
        
        logger.info(f"Registered storage adapter: {name} ({adapter_type})")
        
    except Exception as e:
        logger.error(f"Failed to register storage adapter {name}: {e}")
        raise


def get_storage_manager() -> StorageManager:
    """获取存储管理器实例
    
    Returns:
        存储管理器实例
    """
    return container.resolve("storage_manager")


def get_storage_config_manager() -> StorageConfigManager:
    """获取存储配置管理器实例
    
    Returns:
        存储配置管理器实例
    """
    return container.resolve("storage_config_manager")


def get_storage_migration_service() -> StorageMigrationService:
    """获取存储迁移服务实例
    
    Returns:
        存储迁移服务实例
    """
    return container.resolve("storage_migration_service")


def get_storage_factory_registry():
    """获取存储适配器工厂注册表实例
    
    Returns:
        存储适配器工厂注册表实例
    """
    return container.resolve("storage_factory_registry")


# 便捷函数：注册默认存储适配器
def register_default_storage_adapters() -> None:
    """注册默认存储适配器"""
    try:
        # 注册内存存储适配器
        register_storage_adapter(
            name="memory",
            adapter_type="memory",
            config={
                "max_size": 10000,
                "max_memory_mb": 100,
                "enable_ttl": False,
                "enable_compression": False,
                "enable_metrics": True
            }
        )
        
        # 注册SQLite存储适配器
        register_storage_adapter(
            name="sqlite",
            adapter_type="sqlite",
            config={
                "db_path": "storage.db",
                "timeout": 30.0,
                "enable_wal_mode": True,
                "connection_pool_size": 5,
                "enable_backup": True,
                "backup_interval_hours": 24
            },
            set_as_default=True
        )
        
        # 注册文件存储适配器
        register_storage_adapter(
            name="file",
            adapter_type="file",
            config={
                "base_path": "file_storage",
                "enable_compression": False,
                "enable_ttl": False,
                "directory_structure": "flat",
                "enable_backup": True,
                "backup_interval_hours": 24
            }
        )
        
        logger.info("Default storage adapters registered")
        
    except Exception as e:
        logger.error(f"Failed to register default storage adapters: {e}")
        raise


# 便捷函数：从配置注册存储适配器
def register_storage_adapter_from_config(config_name: str) -> None:
    """从配置注册存储适配器
    
    Args:
        config_name: 配置名称
    """
    try:
        # 获取存储配置管理器
        config_manager = get_storage_config_manager()
        
        # 获取配置
        config = config_manager.get_config(config_name)
        if config is None:
            raise ValueError(f"Storage config not found: {config_name}")
        
        # 注册适配器
        register_storage_adapter(
            name=config.name,
            adapter_type=config.storage_type.value,
            config=config.config,
            set_as_default=config.is_default
        )
        
        logger.info(f"Registered storage adapter from config: {config_name}")
        
    except Exception as e:
        logger.error(f"Failed to register storage adapter from config {config_name}: {e}")
        raise


# 便捷函数：注册所有配置中的存储适配器
def register_storage_adapters_from_configs() -> None:
    """从所有配置注册存储适配器"""
    try:
        # 获取存储配置管理器
        config_manager = get_storage_config_manager()
        
        # 获取所有配置
        configs = config_manager.list_configs()
        
        # 注册每个配置
        for config in configs:
            if config.enabled:
                register_storage_adapter(
                    name=config.name,
                    adapter_type=config.storage_type.value,
                    config=config.config,
                    set_as_default=config.is_default
                )
        
        logger.info(f"Registered {len(configs)} storage adapters from configs")
        
    except Exception as e:
        logger.error(f"Failed to register storage adapters from configs: {e}")
        raise


# 初始化函数
def initialize_storage_services() -> None:
    """初始化存储服务"""
    try:
        # 注册存储服务
        register_storage_services()
        
        # 注册默认存储适配器
        register_default_storage_adapters()
        
        logger.info("Storage services initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize storage services: {e}")
        raise