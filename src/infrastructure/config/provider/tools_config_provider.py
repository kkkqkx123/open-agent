"""
工具配置提供者

提供工具模块的配置服务，遵循基础设施层的职责。
"""

from typing import Dict, Any, Optional, List
import logging

from .base_provider import BaseConfigProvider
from ..impl.tools_config_impl import ToolsConfigImpl
from ..impl.base_impl import IConfigImpl
from src.interfaces.config.exceptions import ConfigError

logger = logging.getLogger(__name__)


class ToolsConfigProvider(BaseConfigProvider):
    """工具配置提供者
    
    提供工具模块的高级配置服务，包括工具加载、验证和管理。
    """
    
    def __init__(self, 
                 module_type: str,
                 config_impl: Optional[IConfigImpl] = None,
                 cache_enabled: bool = True,
                 cache_ttl: int = 300):
        """初始化工具配置提供者
        
        Args:
            module_type: 模块类型
            config_impl: 配置实现
            cache_enabled: 是否启用缓存
            cache_ttl: 缓存生存时间（秒）
        """
        super().__init__(module_type, config_impl, cache_enabled, cache_ttl)
        
        # 确保使用ToolsConfigImpl
        if not isinstance(self.config_impl, ToolsConfigImpl):
            if config_impl is None:
                from ..config_factory import ConfigFactory
                factory = ConfigFactory()
                self.config_impl = factory.create_config_implementation("tools")
            else:
                raise ConfigError("ToolsConfigProvider需要ToolsConfigImpl实例")
        
        # 工具配置缓存
        self._tool_cache: Dict[str, Dict[str, Any]] = {}
        self._registry_cache: Optional[Dict[str, Any]] = None
        
        logger.debug("初始化工具配置提供者")
    
    def get_tool_config(self, tool_name: str, tool_type: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """获取工具配置
        
        Args:
            tool_name: 工具名称
            tool_type: 工具类型（可选）
            use_cache: 是否使用缓存
            
        Returns:
            工具配置数据
            
        Raises:
            ConfigError: 配置获取失败
        """
        try:
            cache_key = f"{tool_name}:{tool_type or 'auto'}"
            
            # 检查缓存
            if use_cache and cache_key in self._tool_cache:
                logger.debug(f"从缓存获取工具配置: {cache_key}")
                return self._tool_cache[cache_key].copy()
            
            # 从实现层加载配置
            if isinstance(self.config_impl, ToolsConfigImpl):
                tool_config = self.config_impl.load_tool_config(tool_name, tool_type)
            else:
                raise ConfigError("配置实现不是ToolsConfigImpl实例")
            
            # 验证配置
            if isinstance(self.config_impl, ToolsConfigImpl):
                if not self.config_impl.validate_tool_config(tool_config):
                    raise ConfigError(f"工具配置验证失败: {tool_name}")
            
            # 缓存配置
            if use_cache:
                self._tool_cache[cache_key] = tool_config.copy()
            
            logger.debug(f"获取工具配置成功: {tool_name}")
            return tool_config
            
        except Exception as e:
            logger.error(f"获取工具配置失败 {tool_name}: {e}")
            raise ConfigError(f"获取工具配置失败 {tool_name}: {e}")
    
    def get_tools_by_type(self, tool_type: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """按类型获取工具配置列表
        
        Args:
            tool_type: 工具类型
            use_cache: 是否使用缓存
            
        Returns:
            工具配置列表
            
        Raises:
            ConfigError: 配置获取失败
        """
        try:
            # 检查工具类型是否支持
            if isinstance(self.config_impl, ToolsConfigImpl):
                if not self.config_impl.is_tool_type_supported(tool_type):
                    raise ConfigError(f"不支持的工具类型: {tool_type}")
            
            # 从实现层加载配置
            if isinstance(self.config_impl, ToolsConfigImpl):
                tools = self.config_impl.load_tools_by_type(tool_type)
            else:
                raise ConfigError("配置实现不是ToolsConfigImpl实例")
            
            logger.debug(f"获取了 {len(tools)} 个 {tool_type} 类型工具配置")
            return tools
            
        except Exception as e:
            logger.error(f"按类型获取工具配置失败 {tool_type}: {e}")
            raise ConfigError(f"按类型获取工具配置失败 {tool_type}: {e}")
    
    def get_all_tools(self, use_cache: bool = True) -> Dict[str, List[Dict[str, Any]]]:
        """获取所有工具配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            按类型分组的工具配置字典
            
        Raises:
            ConfigError: 配置获取失败
        """
        try:
            # 从实现层加载配置
            if isinstance(self.config_impl, ToolsConfigImpl):
                all_tools = self.config_impl.load_all_tools()
            else:
                raise ConfigError("配置实现不是ToolsConfigImpl实例")
            
            total_count = sum(len(tools) for tools in all_tools.values())
            logger.debug(f"获取了所有工具配置，共 {total_count} 个工具")
            return all_tools
            
        except Exception as e:
            logger.error(f"获取所有工具配置失败: {e}")
            raise ConfigError(f"获取所有工具配置失败: {e}")
    
    def get_tool_registry_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取工具注册表配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            工具注册表配置数据
            
        Raises:
            ConfigError: 配置获取失败
        """
        try:
            # 检查缓存
            if use_cache and self._registry_cache is not None:
                logger.debug("从缓存获取工具注册表配置")
                return self._registry_cache.copy()
            
            # 从实现层加载配置
            if isinstance(self.config_impl, ToolsConfigImpl):
                registry_config = self.config_impl.load_tool_registry_config()
            else:
                raise ConfigError("配置实现不是ToolsConfigImpl实例")
            
            # 缓存配置
            if use_cache:
                self._registry_cache = registry_config.copy()
            
            logger.debug("获取工具注册表配置成功")
            return registry_config
            
        except Exception as e:
            logger.error(f"获取工具注册表配置失败: {e}")
            raise ConfigError(f"获取工具注册表配置失败: {e}")
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表
        
        Returns:
            工具类型列表
        """
        if isinstance(self.config_impl, ToolsConfigImpl):
            return self.config_impl.get_supported_tool_types()
        return []
    
    def is_tool_type_supported(self, tool_type: str) -> bool:
        """检查是否支持指定的工具类型
        
        Args:
            tool_type: 工具类型
            
        Returns:
            是否支持
        """
        if isinstance(self.config_impl, ToolsConfigImpl):
            return self.config_impl.is_tool_type_supported(tool_type)
        return False
    
    def validate_tool_config(self, tool_config: Dict[str, Any]) -> bool:
        """验证工具配置
        
        Args:
            tool_config: 工具配置数据
            
        Returns:
            是否有效
        """
        if isinstance(self.config_impl, ToolsConfigImpl):
            return self.config_impl.validate_tool_config(tool_config)
        return False
    
    def clear_tool_cache(self, tool_name: Optional[str] = None) -> None:
        """清除工具配置缓存
        
        Args:
            tool_name: 工具名称，如果为None则清除所有缓存
        """
        if tool_name:
            # 清除特定工具的缓存
            keys_to_remove = [key for key in self._tool_cache.keys() if key.startswith(f"{tool_name}:")]
            for key in keys_to_remove:
                del self._tool_cache[key]
            logger.debug(f"清除工具 {tool_name} 的缓存")
        else:
            # 清除所有工具缓存
            self._tool_cache.clear()
            self._registry_cache = None
            logger.debug("清除所有工具配置缓存")
    
    def reload_tool_config(self, tool_name: str, tool_type: Optional[str] = None) -> Dict[str, Any]:
        """重新加载工具配置
        
        Args:
            tool_name: 工具名称
            tool_type: 工具类型（可选）
            
        Returns:
            重新加载的工具配置数据
        """
        # 清除缓存
        self.clear_tool_cache(tool_name)
        
        # 重新加载配置
        return self.get_tool_config(tool_name, tool_type, use_cache=False)
    
    def reload_tool_registry_config(self) -> Dict[str, Any]:
        """重新加载工具注册表配置
        
        Returns:
            重新加载的工具注册表配置数据
        """
        # 清除缓存
        self._registry_cache = None
        
        # 重新加载配置
        return self.get_tool_registry_config(use_cache=False)
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            统计信息
        """
        stats = super().get_provider_stats()
        
        # 添加工具特定统计
        stats.update({
            "tool_cache_size": len(self._tool_cache),
            "registry_cached": self._registry_cache is not None,
            "supported_tool_types": self.get_supported_tool_types()
        })
        
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于工具配置，直接返回配置数据
        # 在实际应用中，这里可以转换为特定的配置模型类
        return config_data
    
    def _preload_common_configs(self) -> None:
        """预加载常用配置"""
        try:
            # 预加载工具注册表配置
            self.get_config("registry")
        except Exception as e:
            logger.warning(f"预加载工具注册表配置失败: {e}")