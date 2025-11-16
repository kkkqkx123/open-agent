"""
存储注册表

提供存储类型的注册和管理功能，支持动态注册和发现机制。
"""

from typing import Dict, Type, Any, List, Optional
import inspect
import logging

from ...domain.storage.exceptions import StorageError, StorageConfigurationError


logger = logging.getLogger(__name__)


class StorageRegistry:
    """存储注册表
    
    负责管理存储类型的注册和发现。
    """
    
    def __init__(self):
        """初始化存储注册表"""
        self._storage_classes: Dict[str, Type] = {}
        self._storage_metadata: Dict[str, Dict[str, Any]] = {}
        self._builtin_loaded = False
    
    def register(self, storage_type: str, storage_class: Type, metadata: Optional[Dict[str, Any]] = None) -> None:
        """注册存储类型
        
        Args:
            storage_type: 存储类型名称
            storage_class: 存储类
            metadata: 存储元数据
            
        Raises:
            StorageError: 注册失败时抛出
        """
        try:
            # 验证存储类
            self._validate_storage_class(storage_class)
            
            # 注册存储类
            self._storage_classes[storage_type] = storage_class
            
            # 注册元数据
            self._storage_metadata[storage_type] = metadata or {}
            
            logger.info(f"Registered storage type '{storage_type}' with class '{storage_class.__name__}'")
            
        except Exception as e:
            raise StorageError(f"Failed to register storage type '{storage_type}': {e}")
    
    def unregister(self, storage_type: str) -> bool:
        """注销存储类型
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否成功注销
        """
        if storage_type in self._storage_classes:
            del self._storage_classes[storage_type]
            if storage_type in self._storage_metadata:
                del self._storage_metadata[storage_type]
            logger.info(f"Unregistered storage type '{storage_type}'")
            return True
        return False
    
    def get_storage_class(self, storage_type: str) -> Type:
        """获取存储类
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            存储类
            
        Raises:
            StorageConfigurationError: 存储类型未注册时抛出
        """
        if storage_type not in self._storage_classes:
            # 尝试加载内置存储类型
            self._load_builtin_storages()
            
            if storage_type not in self._storage_classes:
                raise StorageConfigurationError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_classes[storage_type]
    
    def get_storage_metadata(self, storage_type: str) -> Dict[str, Any]:
        """获取存储元数据
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            存储元数据
            
        Raises:
            StorageConfigurationError: 存储类型未注册时抛出
        """
        if storage_type not in self._storage_metadata:
            raise StorageConfigurationError(f"Storage type '{storage_type}' is not registered")
        
        return self._storage_metadata[storage_type].copy()
    
    def get_registered_types(self) -> List[str]:
        """获取已注册的存储类型列表
        
        Returns:
            存储类型名称列表
        """
        # 确保内置存储类型已加载
        self._load_builtin_storages()
        return list(self._storage_classes.keys())
    
    def is_registered(self, storage_type: str) -> bool:
        """检查存储类型是否已注册
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            是否已注册
        """
        # 确保内置存储类型已加载
        self._load_builtin_storages()
        return storage_type in self._storage_classes
    
    def get_storage_info(self, storage_type: str) -> Dict[str, Any]:
        """获取存储类型信息
        
        Args:
            storage_type: 存储类型名称
            
        Returns:
            存储类型信息
            
        Raises:
            StorageConfigurationError: 存储类型未注册时抛出
        """
        if not self.is_registered(storage_type):
            raise StorageConfigurationError(f"Storage type '{storage_type}' is not registered")
        
        storage_class = self._storage_classes[storage_type]
        metadata = self._storage_metadata[storage_type]
        
        # 获取类信息
        class_info = {
            "name": storage_type,
            "class_name": storage_class.__name__,
            "module": storage_class.__module__,
            "doc": storage_class.__doc__,
            "metadata": metadata
        }
        
        # 获取构造函数参数
        try:
            sig = inspect.signature(storage_class.__init__)
            parameters = []
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                
                param_info = {
                    "name": param_name,
                    "default": param.default if param.default != inspect.Parameter.empty else None,
                    "annotation": param.annotation if param.annotation != inspect.Parameter.empty else None,
                    "kind": param.kind.name
                }
                parameters.append(param_info)
            
            class_info["parameters"] = parameters
        except Exception as e:
            logger.warning(f"Failed to get parameters for storage type '{storage_type}': {e}")
            class_info["parameters"] = []
        
        return class_info
    
    def list_storage_info(self) -> List[Dict[str, Any]]:
        """列出所有存储类型信息
        
        Returns:
            存储类型信息列表
        """
        return [self.get_storage_info(storage_type) for storage_type in self.get_registered_types()]
    
    def register_from_module(self, module_path: str, storage_type: Optional[str] = None) -> None:
        """从模块注册存储类型
        
        Args:
            module_path: 模块路径
            storage_type: 存储类型名称，如果为None则从模块推断
            
        Raises:
            StorageError: 注册失败时抛出
        """
        try:
            # 动态导入模块
            import importlib
            module = importlib.import_module(module_path)
            
            # 查找存储类
            storage_class = None
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # 检查是否是存储类
                if self._is_storage_class(obj):
                    storage_class = obj
                    break
            
            if storage_class is None:
                raise StorageError(f"No storage class found in module '{module_path}'")
            
            # 确定存储类型名称
            if storage_type is None:
                storage_type = module_path.split(".")[-1].replace("_storage", "").lower()
            
            # 注册存储类型
            self.register(storage_type, storage_class)
            
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to register storage from module '{module_path}': {e}")
    
    def register_from_config(self, config: Dict[str, Any]) -> None:
        """从配置注册存储类型
        
        Args:
            config: 配置字典
            
        Raises:
            StorageError: 注册失败时抛出
        """
        try:
            for storage_type, storage_config in config.items():
                if "module" in storage_config:
                    self.register_from_module(storage_config["module"], storage_type)
                elif "class" in storage_config:
                    # 从类路径注册
                    class_path = storage_config["class"]
                    module_path, class_name = class_path.rsplit(".", 1)
                    
                    import importlib
                    module = importlib.import_module(module_path)
                    storage_class = getattr(module, class_name)
                    
                    metadata = storage_config.get("metadata", {})
                    self.register(storage_type, storage_class, metadata)
                else:
                    raise StorageError(f"Invalid storage config for type '{storage_type}'")
                    
        except Exception as e:
            if isinstance(e, StorageError):
                raise
            raise StorageError(f"Failed to register storages from config: {e}")
    
    def _validate_storage_class(self, storage_class: Type) -> None:
        """验证存储类
        
        Args:
            storage_class: 存储类
            
        Raises:
            StorageError: 验证失败时抛出
        """
        if not inspect.isclass(storage_class):
            raise StorageError("Storage class must be a class")
        
        # 检查是否实现了必要的接口
        if not self._is_storage_class(storage_class):
            raise StorageError("Storage class must implement IStorageBackend interface")
    
    def _is_storage_class(self, cls: Type) -> bool:
        """检查是否是存储类
        
        Args:
            cls: 类
            
        Returns:
            是否是存储类
        """
        # 检查是否继承自IStorageBackend
        from .interfaces import IStorageBackend
        return issubclass(cls, IStorageBackend)
    
    def _load_builtin_storages(self) -> None:
        """加载内置存储类型"""
        if self._builtin_loaded:
            return
        
        try:
            # 注册内存存储
            self.register_from_module("src.infrastructure.storage.memory.memory_storage", "memory")
            
            # 注册SQLite存储
            self.register_from_module("src.infrastructure.storage.sqlite.sqlite_storage", "sqlite")
            
            # 注册文件存储
            self.register_from_module("src.infrastructure.storage.file.file_storage", "file")
            
            self._builtin_loaded = True
            logger.info("Loaded builtin storage types")
            
        except Exception as e:
            logger.warning(f"Failed to load builtin storage types: {e}")
    
    def clear(self) -> None:
        """清空注册表"""
        self._storage_classes.clear()
        self._storage_metadata.clear()
        self._builtin_loaded = False
        logger.info("Cleared storage registry")
    
    def __len__(self) -> int:
        """返回已注册的存储类型数量"""
        return len(self._storage_classes)
    
    def __contains__(self, storage_type: str) -> bool:
        """检查存储类型是否已注册"""
        return self.is_registered(storage_type)
    
    def __iter__(self):
        """迭代已注册的存储类型"""
        return iter(self._storage_classes.keys())