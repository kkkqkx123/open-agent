"""存储注册表

提供存储类型的注册和管理功能，支持插件化架构。
"""

from typing import Dict, Type, Any, List, Optional, Callable
import importlib
import inspect
from src.services.logger.injection import get_logger
from pathlib import Path

logger = get_logger(__name__)


class StorageRegistry:
    """轻量级存储注册表
    
    提供存储类型的注册、发现和管理功能，支持插件化架构。
    """
    
    def __init__(self):
        """初始化存储注册表"""
        self._storage_classes: Dict[str, Type] = {}
        self._storage_metadata: Dict[str, Dict[str, Any]] = {}
        self._storage_factories: Dict[str, Callable] = {}
        self._auto_loaded = False
    
    def register(
        self, 
        storage_type: str, 
        storage_class: Type, 
        metadata: Optional[Dict[str, Any]] = None,
        factory: Optional[Callable] = None
    ) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            metadata: 存储元数据
            factory: 工厂函数（可选）
        """
        try:
            # 验证存储类
            self._validate_storage_class(storage_class)
            
            # 注册存储类
            self._storage_classes[storage_type] = storage_class
            
            # 注册元数据
            self._storage_metadata[storage_type] = metadata or {}
            
            # 注册工厂函数
            if factory:
                self._storage_factories[storage_type] = factory
            
            logger.info(f"Registered storage type '{storage_type}'")
            
        except Exception as e:
            logger.error(f"Failed to register storage type '{storage_type}': {e}")
            raise
    
    def unregister(self, storage_type: str) -> bool:
        """注销存储类型"""
        if storage_type in self._storage_classes:
            del self._storage_classes[storage_type]
            if storage_type in self._storage_metadata:
                del self._storage_metadata[storage_type]
            if storage_type in self._storage_factories:
                del self._storage_factories[storage_type]
            logger.info(f"Unregistered storage type '{storage_type}'")
            return True
        return False
    
    def get_storage_class(self, storage_type: str) -> Type:
        """获取存储类"""
        if storage_type not in self._storage_classes:
            self._load_builtin_types()
            
        if storage_type not in self._storage_classes:
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_classes[storage_type]
    
    def get_storage_metadata(self, storage_type: str) -> Dict[str, Any]:
        """获取存储元数据"""
        if storage_type not in self._storage_metadata:
            raise ValueError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_metadata[storage_type].copy()
    
    def get_storage_factory(self, storage_type: str) -> Optional[Callable]:
        """获取存储工厂函数"""
        return self._storage_factories.get(storage_type)
    
    def get_registered_types(self) -> List[str]:
        """获取已注册的存储类型列表"""
        self._load_builtin_types()
        return list(self._storage_classes.keys())
    
    def is_registered(self, storage_type: str) -> bool:
        """检查存储类型是否已注册"""
        self._load_builtin_types()
        return storage_type in self._storage_classes
    
    def load_from_config(self, config_path: str) -> None:
        """从配置文件加载存储类型
        
        Args:
            config_path: 配置文件路径
        """
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                logger.warning(f"Config file not found: {config_path}")
                return
            
            import yaml
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            for storage_type, storage_config in config.get('storage_types', {}).items():
                if 'module' in storage_config:
                    self._register_from_module(
                        storage_type, 
                        storage_config['module'],
                        storage_config.get('metadata'),
                        storage_config.get('factory')
                    )
                elif 'class' in storage_config:
                    self._register_from_class_path(
                        storage_type,
                        storage_config['class'],
                        storage_config.get('metadata'),
                        storage_config.get('factory')
                    )
            
            logger.info(f"Loaded storage types from config: {config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load storage types from config: {e}")
    
    def _register_from_module(
        self, 
        storage_type: str, 
        module_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        factory_path: Optional[str] = None
    ) -> None:
        """从模块注册存储类型"""
        try:
            module = importlib.import_module(module_path)
            
            # 查找存储类
            storage_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                if self._is_storage_class(obj):
                    storage_class = obj
                    break
            
            if storage_class is None:
                raise ValueError(f"No storage class found in module '{module_path}'")
            
            # 获取工厂函数
            factory = None
            if factory_path:
                factory_module_path, factory_name = factory_path.rsplit(".", 1)
                factory_module = importlib.import_module(factory_module_path)
                factory = getattr(factory_module, factory_name)
            
            self.register(storage_type, storage_class, metadata, factory)
            
        except Exception as e:
            logger.error(f"Failed to register storage from module '{module_path}': {e}")
            raise
    
    def _register_from_class_path(
        self,
        storage_type: str,
        class_path: str,
        metadata: Optional[Dict[str, Any]] = None,
        factory_path: Optional[str] = None
    ) -> None:
        """从类路径注册存储类型"""
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            storage_class = getattr(module, class_name)
            
            # 获取工厂函数
            factory = None
            if factory_path:
                factory_module_path, factory_name = factory_path.rsplit(".", 1)
                factory_module = importlib.import_module(factory_module_path)
                factory = getattr(factory_module, factory_name)
            
            self.register(storage_type, storage_class, metadata, factory)
            
        except Exception as e:
            logger.error(f"Failed to register storage from class path '{class_path}': {e}")
            raise
    
    def _validate_storage_class(self, storage_class: Type) -> None:
        """验证存储类"""
        if not inspect.isclass(storage_class):
            raise ValueError("Storage class must be a class")
        
        # 检查是否实现了必要的接口
        if not self._is_storage_class(storage_class):
            raise ValueError("Storage class must implement required interface")
    
    def _is_storage_class(self, cls: Type) -> bool:
        """检查是否是存储类"""
        # 检查是否继承自基础存储类
        from .adapters.base import StorageBackend
        return issubclass(cls, StorageBackend)
    
    def _load_builtin_types(self) -> None:
        """加载内置存储类型"""
        if self._auto_loaded:
            return
        
        try:
            # 注册内存存储
            self._register_from_module(
                'memory',
                'src.adapters.storage.backends.memory_backend',
                {'description': 'In-memory storage backend'}
            )
            
            # 注册SQLite存储
            self._register_from_module(
                'sqlite',
                'src.adapters.storage.backends.sqlite_backend',
                {'description': 'SQLite storage backend'}
            )
            
            # 注册文件存储
            self._register_from_module(
                'file',
                'src.adapters.storage.backends.file_backend',
                {'description': 'File-based storage backend'}
            )
            
            # 注册checkpoint内存存储
            self._register_from_module(
                'checkpoint_memory',
                'src.adapters.storage.backends.checkpoint.memory',
                {'description': 'Checkpoint in-memory storage backend'}
            )
            
            # 注册checkpoint SQLite存储
            self._register_from_module(
                'checkpoint_sqlite',
                'src.adapters.storage.backends.checkpoint.sqlite',
                {'description': 'Checkpoint SQLite storage backend'}
            )
            
            # 注册LangGraph checkpoint适配器
            self._register_from_module(
                'langgraph',
                'src.adapters.storage.backends.checkpoint.langgraph',
                {'description': 'LangGraph checkpoint adapter'}
            )
            
            self._auto_loaded = True
            logger.info("Loaded builtin storage types")
            
        except Exception as e:
            logger.warning(f"Failed to load builtin storage types: {e}")


# 全局注册表实例
storage_registry = StorageRegistry()