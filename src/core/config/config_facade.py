"""配置门面（优化版）

为Service层提供统一的配置访问接口，直接使用基础设施层的ConfigFactory。
"""

from typing import Dict, Any, Optional
from src.interfaces.dependency_injection import get_logger
from src.infrastructure.config import ConfigFactory

logger = get_logger(__name__)


class ConfigFacade:
    """配置门面
    
    直接使用ConfigFactory，提供缓存和业务逻辑协调
    """
    
    def __init__(self, config_factory: ConfigFactory):
        """初始化配置门面
        
        Args:
            config_factory: 配置工厂实例
        """
        self.factory = config_factory
        
        # 简单的内存缓存
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl: Dict[str, float] = {}
        
        logger.info("配置门面初始化完成")
    
    def get_config(self, module_type: str, config_name: Optional[str] = None, 
                 use_cache: bool = True) -> Dict[str, Any]:
        """获取配置的统一接口
        
        Args:
            module_type: 模块类型
            config_name: 配置名称
            use_cache: 是否使用缓存
            
        Returns:
            配置数据字典
        """
        cache_key = f"{module_type}:{config_name or 'default'}"
        
        # 检查缓存
        if use_cache and cache_key in self._cache:
            cache_time = self._cache_ttl.get(cache_key, 0)
            if cache_time > 0:
                logger.debug(f"从缓存获取配置: {cache_key}")
                return self._cache[cache_key]
        
        # 直接使用工厂获取配置
        try:
            impl = self.factory.get_config_implementation(module_type)
            
            # 检查 impl 是否为 None
            if impl is None:
                raise ValueError(f"无法获取 {module_type} 模块的配置实现")
            
            if config_name:
                config_path = impl.get_config_path(config_name)
                config = impl.load_config(config_path)
            else:
                config = impl.get_config()
                
        except Exception as e:
            logger.error(f"获取{module_type}模块配置失败: {e}")
            raise
        
        # 缓存配置
        if use_cache:
            self._cache[cache_key] = config
            self._cache_ttl[cache_key] = 300  # 5分钟缓存
        
        return config
    
    def invalidate_cache(self, module_type: Optional[str] = None, 
                      config_name: Optional[str] = None) -> None:
        """清除缓存"""
        if module_type and config_name:
            cache_key = f"{module_type}:{config_name}"
            if cache_key in self._cache:
                del self._cache[cache_key]
                del self._cache_ttl[cache_key]
        elif module_type:
            # 清除模块相关的所有缓存
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(f"{module_type}:")]
            for key in keys_to_remove:
                if key in self._cache:
                    del self._cache[key]
                if key in self._cache_ttl:
                    del self._cache_ttl[key]
        else:
            # 清除所有缓存
            self._cache.clear()
            self._cache_ttl.clear()
        
        logger.info("配置缓存已清除")
    
    def get_facade_status(self) -> Dict[str, Any]:
        """获取门面状态"""
        return {
            "cached_configs": list(self._cache.keys()),
            "cache_ttl": self._cache_ttl.copy(),
            "factory_stats": self.factory.get_factory_stats()
        }
    
    # 兼容性方法 - 保持与旧接口的兼容性
    def get_llm_config(self) -> Dict[str, Any]:
        """获取LLM配置"""
        return self.get_config("llm")
    
    def get_storage_config(self) -> Dict[str, Any]:
        """获取存储配置"""
        return self.get_config("storage")
    
    def get_state_config(self) -> Dict[str, Any]:
        """获取状态配置"""
        return self.get_config("state")
    
    def get_workflow_config(self) -> Dict[str, Any]:
        """获取工作流配置"""
        return self.get_config("workflow")
    
    def reload_config(self, module_type: str) -> None:
        """重新加载配置"""
        self.invalidate_cache(module_type)
        logger.info(f"已重新加载{module_type}模块配置")


def initialize_config_facade(config_loader: Any) -> ConfigFacade:
    """初始化配置门面
    
    Args:
        config_loader: 配置加载器
        
    Returns:
        ConfigFacade: 配置门面实例
    """
    from src.infrastructure.config import ConfigFactory
    
    factory = ConfigFactory()
    return ConfigFacade(factory)