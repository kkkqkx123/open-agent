"""动态导入工具

实现安全的类动态导入功能，处理导入错误并提供友好的错误信息。
"""

from typing import Type, Any, Optional, Dict, Callable
import importlib
import inspect
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DynamicImportError(Exception):
    """动态导入错误"""
    pass


class DynamicImporter:
    """动态导入器
    
    实现安全的类动态导入功能。
    """
    
    def __init__(self):
        """初始化动态导入器"""
        self.logger = logging.getLogger(f"{__name__}.DynamicImporter")
        
        # 导入缓存
        self._module_cache: Dict[str, Any] = {}
        self._class_cache: Dict[str, Type] = {}
        
        # 重试配置
        self.max_retries = 3
        self.retry_delay = 0.1  # 秒
    
    def import_class(self, class_path: str, retry: bool = True) -> Type:
        """导入类
        
        Args:
            class_path: 类路径，格式为 "module.submodule:ClassName"
            retry: 是否在失败时重试
            
        Returns:
            Type: 导入的类
            
        Raises:
            DynamicImportError: 导入失败
        """
        # 检查缓存
        if class_path in self._class_cache:
            self.logger.debug(f"从缓存获取类: {class_path}")
            return self._class_cache[class_path]
        
        # 解析类路径
        try:
            module_path, class_name = class_path.split(":")
        except ValueError:
            raise DynamicImportError(f"类路径格式不正确: {class_path}，应为 'module.submodule:ClassName'")
        
        # 导入模块和类
        attempts = 0
        last_error = None
        
        while attempts < (self.max_retries if retry else 1):
            attempts += 1
            
            try:
                # 导入模块
                module = self._import_module(module_path)
                
                # 获取类
                cls = self._get_class_from_module(module, class_name)
                
                # 验证类
                self._validate_class(cls)
                
                # 缓存结果
                self._class_cache[class_path] = cls
                
                self.logger.debug(f"成功导入类: {class_path}")
                return cls
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"导入类失败 (尝试 {attempts}/{self.max_retries}): {class_path}, 错误: {e}")
                
                if attempts < self.max_retries and retry:
                    # 清除缓存并重试
                    if module_path in self._module_cache:
                        del self._module_cache[module_path]
                    
                    # 简单的延迟
                    import time
                    time.sleep(self.retry_delay)
        
        # 所有尝试都失败
        error_msg = f"导入类失败: {class_path}"
        if last_error:
            error_msg += f", 错误: {last_error}"
        raise DynamicImportError(error_msg)
    
    def import_function(self, function_path: str, retry: bool = True) -> Callable:
        """导入函数
        
        Args:
            function_path: 函数路径，格式为 "module.submodule:function_name"
            retry: 是否在失败时重试
            
        Returns:
            Callable: 导入的函数
            
        Raises:
            DynamicImportError: 导入失败
        """
        # 解析函数路径
        try:
            module_path, function_name = function_path.split(":")
        except ValueError:
            raise DynamicImportError(f"函数路径格式不正确: {function_path}，应为 'module.submodule:function_name'")
        
        # 导入模块
        module = self._import_module(module_path)
        
        # 获取函数
        try:
            func = getattr(module, function_name)
        except AttributeError:
            raise DynamicImportError(f"模块中不存在函数: {function_name}")
        
        # 验证函数
        if not inspect.isfunction(func) and not inspect.ismethod(func):
            raise DynamicImportError(f"对象不是函数: {function_name}")
        
        self.logger.debug(f"成功导入函数: {function_path}")
        return func
    
    def import_module(self, module_path: str, retry: bool = True) -> Any:
        """导入模块
        
        Args:
            module_path: 模块路径
            retry: 是否在失败时重试
            
        Returns:
            Any: 导入的模块
            
        Raises:
            DynamicImportError: 导入失败
        """
        return self._import_module(module_path, retry)
    
    def is_class_available(self, class_path: str) -> bool:
        """检查类是否可用
        
        Args:
            class_path: 类路径
            
        Returns:
            bool: 是否可用
        """
        try:
            self.import_class(class_path, retry=False)
            return True
        except DynamicImportError:
            return False
    
    def is_function_available(self, function_path: str) -> bool:
        """检查函数是否可用
        
        Args:
            function_path: 函数路径
            
        Returns:
            bool: 是否可用
        """
        try:
            self.import_function(function_path, retry=False)
            return True
        except DynamicImportError:
            return False
    
    def get_class_info(self, class_path: str) -> Optional[Dict[str, Any]]:
        """获取类信息
        
        Args:
            class_path: 类路径
            
        Returns:
            Optional[Dict[str, Any]]: 类信息，如果导入失败则返回None
        """
        try:
            cls = self.import_class(class_path, retry=False)
            
            # 获取类信息
            info = {
                "name": cls.__name__,
                "module": cls.__module__,
                "doc": cls.__doc__,
                "file": inspect.getfile(cls) if hasattr(cls, '__file__') else None,
                "methods": [],
                "properties": [],
                "base_classes": [base.__name__ for base in cls.__bases__]
            }
            
            # 获取方法
            for name, member in inspect.getmembers(cls):
                if inspect.isfunction(member) or inspect.ismethod(member):
                    if not name.startswith("_"):
                        info["methods"].append({
                            "name": name,
                            "doc": member.__doc__,
                            "signature": str(inspect.signature(member))
                        })
            
            # 获取属性
            for name, member in inspect.getmembers(cls):
                if not name.startswith("_") and not inspect.ismethod(member) and not inspect.isfunction(member):
                    if not callable(member):
                        info["properties"].append({
                            "name": name,
                            "type": type(member).__name__,
                            "value": str(member) if len(str(member)) < 100 else str(member)[:100] + "..."
                        })
            
            return info
            
        except DynamicImportError:
            return None
    
    def clear_cache(self) -> None:
        """清除缓存"""
        self._module_cache.clear()
        self._class_cache.clear()
        self.logger.info("已清除导入缓存")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息
        
        Returns:
            Dict[str, Any]: 缓存信息
        """
        return {
            "module_cache_size": len(self._module_cache),
            "class_cache_size": len(self._class_cache),
            "cached_modules": list(self._module_cache.keys()),
            "cached_classes": list(self._class_cache.keys())
        }
    
    def _import_module(self, module_path: str, retry: bool = True) -> Any:
        """导入模块
        
        Args:
            module_path: 模块路径
            retry: 是否在失败时重试
            
        Returns:
            Any: 导入的模块
            
        Raises:
            DynamicImportError: 导入失败
        """
        # 检查缓存
        if module_path in self._module_cache:
            self.logger.debug(f"从缓存获取模块: {module_path}")
            return self._module_cache[module_path]
        
        attempts = 0
        last_error = None
        
        while attempts < (self.max_retries if retry else 1):
            attempts += 1
            
            try:
                # 导入模块
                module = importlib.import_module(module_path)
                
                # 缓存结果
                self._module_cache[module_path] = module
                
                self.logger.debug(f"成功导入模块: {module_path}")
                return module
                
            except Exception as e:
                last_error = e
                self.logger.warning(f"导入模块失败 (尝试 {attempts}/{self.max_retries}): {module_path}, 错误: {e}")
                
                if attempts < self.max_retries and retry:
                    # 简单的延迟
                    import time
                    time.sleep(self.retry_delay)
        
        # 所有尝试都失败
        error_msg = f"导入模块失败: {module_path}"
        if last_error:
            error_msg += f", 错误: {last_error}"
        raise DynamicImportError(error_msg)
    
    def _get_class_from_module(self, module: Any, class_name: str) -> Type:
        """从模块中获取类
        
        Args:
            module: 模块对象
            class_name: 类名
            
        Returns:
            Type: 类对象
            
        Raises:
            DynamicImportError: 获取失败
        """
        try:
            cls = getattr(module, class_name)
        except AttributeError:
            raise DynamicImportError(f"模块中不存在类: {class_name}")
        
        if not inspect.isclass(cls):
            raise DynamicImportError(f"对象不是类: {class_name}")
        
        return cls
    
    def _validate_class(self, cls: Type) -> None:
        """验证类
        
        Args:
            cls: 类对象
            
        Raises:
            DynamicImportError: 验证失败
        """
        # 检查类是否可以实例化
        try:
            # 尝试获取构造函数签名
            inspect.signature(cls.__init__)
        except Exception as e:
            raise DynamicImportError(f"类构造函数不可用: {e}")
        
        # 检查类是否在有效的模块中
        if not hasattr(cls, '__module__') or not cls.__module__:
            raise DynamicImportError("类没有有效的模块信息")
        
        # 检查模块是否可以访问
        try:
            module = inspect.getmodule(cls)
            if module is None:
                raise DynamicImportError("无法获取类的模块信息")
        except Exception as e:
            raise DynamicImportError(f"无法访问类的模块: {e}")


# 全局动态导入器实例
_global_importer: Optional[DynamicImporter] = None


def get_global_importer() -> DynamicImporter:
    """获取全局动态导入器实例
    
    Returns:
        DynamicImporter: 全局动态导入器实例
    """
    global _global_importer
    if _global_importer is None:
        _global_importer = DynamicImporter()
    return _global_importer


def import_class(class_path: str, retry: bool = True) -> Type:
    """使用全局导入器导入类的便捷函数
    
    Args:
        class_path: 类路径
        retry: 是否在失败时重试
        
    Returns:
        Type: 导入的类
    """
    return get_global_importer().import_class(class_path, retry)


def import_function(function_path: str, retry: bool = True) -> Callable:
    """使用全局导入器导入函数的便捷函数
    
    Args:
        function_path: 函数路径
        retry: 是否在失败时重试
        
    Returns:
        Callable: 导入的函数
    """
    return get_global_importer().import_function(function_path, retry)