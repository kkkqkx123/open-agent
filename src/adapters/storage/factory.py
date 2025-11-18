"""存储适配器工厂实现

提供存储适配器的创建和管理功能。
"""

import logging
from typing import Dict, Any, List, Optional

from src.core.state.interfaces import IStateStorageAdapter, IStorageAdapterFactory
from .memory import MemoryStateStorageAdapter
from .sqlite import SQLiteStateStorageAdapter

# 确保可以导出
__all__ = ['StorageAdapterFactory', 'StorageAdapterManager', 'get_storage_factory', 'get_storage_manager', 'create_storage_adapter']


logger = logging.getLogger(__name__)


class StorageAdapterFactory(IStorageAdapterFactory):
    """存储适配器工厂
    
    负责创建和管理不同类型的存储适配器。
    """
    
    def __init__(self):
        """初始化工厂"""
        self._adapter_registry = {
            "memory": MemoryStateStorageAdapter,
            "sqlite": SQLiteStateStorageAdapter
        }
        
        self._default_configs = {
            "memory": {},
            "sqlite": {
                "db_path": "data/state_storage.db"
            }
        }
        
        logger.debug("存储适配器工厂初始化完成")
    
    def create_adapter(self, storage_type: str, config: Dict[str, Any]) -> IStateStorageAdapter:
        """创建存储适配器
        
        Args:
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            存储适配器实例
        """
        try:
            # 验证存储类型
            if storage_type not in self._adapter_registry:
                raise ValueError(f"不支持的存储类型: {storage_type}")
            
            # 合并默认配置
            default_config = self._default_configs.get(storage_type, {}).copy()
            merged_config = {**default_config, **config}
            
            # 验证配置
            validation_errors = self.validate_config(storage_type, merged_config)
            if validation_errors:
                raise ValueError(f"配置验证失败: {validation_errors}")
            
            # 创建适配器
            adapter_class = self._adapter_registry[storage_type]
            
            if storage_type == "memory":
                adapter = adapter_class()
            elif storage_type == "sqlite":
                adapter = adapter_class(merged_config.get("db_path"))
            else:
                adapter = adapter_class(**merged_config)
            
            logger.info(f"存储适配器创建成功: {storage_type}")
            return adapter
            
        except Exception as e:
            logger.error(f"创建存储适配器失败: {e}")
            raise
    
    def get_supported_types(self) -> List[str]:
        """获取支持的存储类型"""
        return list(self._adapter_registry.keys())
    
    def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置参数"""
        errors = []
        
        try:
            if storage_type == "memory":
                # 内存存储不需要特殊配置
                pass
            elif storage_type == "sqlite":
                # 验证SQLite配置
                db_path = config.get("db_path")
                if not db_path:
                    errors.append("SQLite存储需要指定db_path参数")
                elif not isinstance(db_path, str):
                    errors.append("db_path必须是字符串类型")
            else:
                errors.append(f"未知的存储类型: {storage_type}")
                
        except Exception as e:
            errors.append(f"配置验证异常: {e}")
        
        return errors
    
    def register_adapter(self, storage_type: str, adapter_class: type, 
                        default_config: Optional[Dict[str, Any]] = None) -> None:
        """注册新的存储适配器
        
        Args:
            storage_type: 存储类型名称
            adapter_class: 适配器类
            default_config: 默认配置
        """
        try:
            # 验证适配器类
            if not issubclass(adapter_class, IStateStorageAdapter):
                raise ValueError(f"适配器类必须实现IStateStorageAdapter接口")
            
            self._adapter_registry[storage_type] = adapter_class
            if default_config:
                self._default_configs[storage_type] = default_config
            
            logger.info(f"存储适配器注册成功: {storage_type}")
            
        except Exception as e:
            logger.error(f"注册存储适配器失败: {e}")
            raise
    
    def unregister_adapter(self, storage_type: str) -> bool:
        """注销存储适配器
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否成功注销
        """
        if storage_type in self._adapter_registry:
            del self._adapter_registry[storage_type]
            if storage_type in self._default_configs:
                del self._default_configs[storage_type]
            
            logger.info(f"存储适配器注销成功: {storage_type}")
            return True
        
        return False
    
    def get_adapter_info(self, storage_type: str) -> Optional[Dict[str, Any]]:
        """获取适配器信息
        
        Args:
            storage_type: 存储类型
            
        Returns:
            适配器信息，如果不存在则返回None
        """
        if storage_type not in self._adapter_registry:
            return None
        
        return {
            "type": storage_type,
            "class": self._adapter_registry[storage_type].__name__,
            "default_config": self._default_configs.get(storage_type, {})
        }
    
    def get_all_adapter_info(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """获取所有适配器信息
        
        Returns:
            所有适配器信息
        """
        result: Dict[str, Optional[Dict[str, Any]]] = {}
        for storage_type in self._adapter_registry.keys():
            result[storage_type] = self.get_adapter_info(storage_type)
        return result


class StorageAdapterManager:
    """存储适配器管理器
    
    管理多个存储适配器的生命周期。
    """
    
    def __init__(self, factory: Optional[StorageAdapterFactory] = None):
        """初始化管理器
        
        Args:
            factory: 存储适配器工厂
        """
        self._factory = factory or StorageAdapterFactory()
        self._adapters: Dict[str, IStateStorageAdapter] = {}
        self._adapter_configs: Dict[str, Dict[str, Any]] = {}
        
        logger.debug("存储适配器管理器初始化完成")
    
    def create_adapter(self, name: str, storage_type: str, 
                      config: Optional[Dict[str, Any]] = None) -> IStateStorageAdapter:
        """创建并注册存储适配器
        
        Args:
            name: 适配器名称
            storage_type: 存储类型
            config: 配置参数
            
        Returns:
            存储适配器实例
        """
        try:
            if name in self._adapters:
                logger.warning(f"适配器已存在，将替换: {name}")
                self.remove_adapter(name)
            
            adapter = self._factory.create_adapter(storage_type, config or {})
            self._adapters[name] = adapter
            self._adapter_configs[name] = {
                "storage_type": storage_type,
                "config": config or {}
            }
            
            logger.info(f"存储适配器创建并注册成功: {name}")
            return adapter
            
        except Exception as e:
            logger.error(f"创建存储适配器失败: {e}")
            raise
    
    def get_adapter(self, name: str) -> Optional[IStateStorageAdapter]:
        """获取存储适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            存储适配器实例，如果不存在则返回None
        """
        return self._adapters.get(name)
    
    def remove_adapter(self, name: str) -> bool:
        """移除存储适配器
        
        Args:
            name: 适配器名称
            
        Returns:
            是否成功移除
        """
        if name not in self._adapters:
            return False
        
        try:
            adapter = self._adapters[name]
            adapter.close()
            del self._adapters[name]
            del self._adapter_configs[name]
            
            logger.info(f"存储适配器移除成功: {name}")
            return True
            
        except Exception as e:
            logger.error(f"移除存储适配器失败: {e}")
            return False
    
    def list_adapters(self) -> List[str]:
        """列出所有适配器名称
        
        Returns:
            适配器名称列表
        """
        return list(self._adapters.keys())
    
    def get_adapter_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取适配器配置
        
        Args:
            name: 适配器名称
            
        Returns:
            适配器配置，如果不存在则返回None
        """
        return self._adapter_configs.get(name)
    
    def health_check_all(self) -> Dict[str, bool]:
        """检查所有适配器的健康状态
        
        Returns:
            适配器健康状态字典
        """
        results = {}
        for name, adapter in self._adapters.items():
            try:
                results[name] = adapter.health_check()
            except Exception as e:
                logger.error(f"适配器健康检查失败 {name}: {e}")
                results[name] = False
        
        return results
    
    def close_all(self) -> None:
        """关闭所有适配器"""
        for name, adapter in self._adapters.items():
            try:
                adapter.close()
                logger.debug(f"适配器已关闭: {name}")
            except Exception as e:
                logger.error(f"关闭适配器失败 {name}: {e}")
        
        self._adapters.clear()
        self._adapter_configs.clear()
        logger.debug("所有存储适配器已关闭")
    
    def get_factory(self) -> StorageAdapterFactory:
        """获取工厂实例
        
        Returns:
            存储适配器工厂
        """
        return self._factory
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取管理器统计信息
        
        Returns:
            统计信息字典
        """
        stats = {
            "total_adapters": len(self._adapters),
            "adapter_types": {},
            "health_status": self.health_check_all()
        }
        
        # 统计各类型适配器数量
        for config in self._adapter_configs.values():
            storage_type = config["storage_type"]
            stats["adapter_types"][storage_type] = stats["adapter_types"].get(storage_type, 0) + 1
        
        return stats


# 全局工厂实例
_global_factory = StorageAdapterFactory()
_global_manager = StorageAdapterManager(_global_factory)


def get_storage_factory() -> StorageAdapterFactory:
    """获取全局存储适配器工厂
    
    Returns:
        全局存储适配器工厂实例
    """
    return _global_factory


def get_storage_manager() -> StorageAdapterManager:
    """获取全局存储适配器管理器
    
    Returns:
        全局存储适配器管理器实例
    """
    return _global_manager


def create_storage_adapter(storage_type: str, config: Optional[Dict[str, Any]] = None) -> IStateStorageAdapter:
    """便捷函数：创建存储适配器
    
    Args:
        storage_type: 存储类型
        config: 配置参数
        
    Returns:
        存储适配器实例
    """
    return _global_factory.create_adapter(storage_type, config or {})