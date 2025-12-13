"""
工具配置实现

提供工具模块的配置实现，遵循基础设施层的职责。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from .base_impl import BaseConfigImpl, ConfigProcessorChain
from src.interfaces.config import IConfigLoader
from src.interfaces.config.schema import IConfigSchema
from src.interfaces.config.exceptions import ConfigError

logger = logging.getLogger(__name__)


class ToolsConfigImpl(BaseConfigImpl):
    """工具配置实现
    
    提供工具模块的配置加载、处理和验证功能。
    """
    
    def __init__(self,
                 config_loader: IConfigLoader,
                 processor_chain: ConfigProcessorChain | None = None,
                 schema: IConfigSchema | None = None):
        """初始化工具配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        # 如果没有提供处理器链，创建一个默认的
        if processor_chain is None:
            processor_chain = ConfigProcessorChain()
        
        # 如果没有提供模式，创建一个默认的
        if schema is None:
            from ..schema.base_schema import BaseSchema
            schema = BaseSchema()
        
        super().__init__("tools", config_loader, processor_chain, schema)
        
        # 工具特定的配置目录
        self._tools_config_dir = Path("configs/tools")
        
        # 支持的工具类型
        self._supported_tool_types = ["builtin", "native", "rest", "mcp"]
        
        logger.debug("初始化工具配置实现")
    
    def load_tool_config(self, tool_name: str, tool_type: Optional[str] = None, use_cache: bool = True) -> Dict[str, Any]:
        """加载特定工具的配置
        
        Args:
            tool_name: 工具名称
            tool_type: 工具类型（可选）
            use_cache: 是否使用缓存
            
        Returns:
            工具配置数据
            
        Raises:
            ConfigError: 配置加载失败
        """
        try:
            # 构建配置文件路径
            if tool_type:
                config_path = f"tools/{tool_type}/{tool_name}"
            else:
                # 尝试在不同类型目录中查找
                config_path = self._find_tool_config(tool_name)
            
            # 检查缓存
            cache_key = f"tool_config:{config_path}"
            if use_cache:
                cached_config = self.cache_manager.get(cache_key)
                if cached_config is not None:
                    logger.debug(f"从缓存加载工具配置: {config_path}")
                    if isinstance(cached_config, dict):
                        return cached_config
                    else:
                        logger.warning(f"缓存中的工具配置不是字典类型，重新加载: {cache_key}")
            
            logger.debug(f"加载工具配置: {config_path}")
            config = self.load_config(config_path, use_cache=False)
            
            # 缓存结果
            if use_cache:
                self.cache_manager.set(cache_key, config)
            
            return config
            
        except Exception as e:
            logger.error(f"加载工具配置失败 {tool_name}: {e}")
            raise ConfigError(f"加载工具配置失败 {tool_name}: {e}")
    
    def load_tools_by_type(self, tool_type: str, use_cache: bool = True) -> List[Dict[str, Any]]:
        """按类型加载所有工具配置
        
        Args:
            tool_type: 工具类型
            use_cache: 是否使用缓存
            
        Returns:
            工具配置列表
            
        Raises:
            ConfigError: 配置加载失败
        """
        try:
            if tool_type not in self._supported_tool_types:
                raise ConfigError(f"不支持的工具类型: {tool_type}")
            
            # 检查缓存
            cache_key = f"tools_by_type:{tool_type}"
            if use_cache:
                cached_tools = self.cache_manager.get(cache_key)
                if cached_tools is not None:
                    logger.debug(f"从缓存加载 {tool_type} 类型工具配置")
                    if isinstance(cached_tools, list):
                        return cached_tools
                    else:
                        logger.warning(f"缓存中的工具列表不是列表类型，重新加载: {cache_key}")
            
            # 使用发现管理器获取配置文件
            config_files = self.discovery_manager.discover_module_configs("tools", f"{tool_type}/*")
            
            tools = []
            for config_file in config_files:
                try:
                    tool_config = self.load_config(config_file, use_cache=False)
                    
                    # 确保工具类型正确
                    tool_config["tool_type"] = tool_type
                    tools.append(tool_config)
                    
                except Exception as e:
                    logger.warning(f"加载工具配置失败 {config_file}: {e}")
                    continue
            
            # 缓存结果
            if use_cache:
                self.cache_manager.set(cache_key, tools)
            
            logger.info(f"加载了 {len(tools)} 个 {tool_type} 类型工具配置")
            return tools
            
        except Exception as e:
            logger.error(f"按类型加载工具配置失败 {tool_type}: {e}")
            raise ConfigError(f"按类型加载工具配置失败 {tool_type}: {e}")
    
    def load_all_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """加载所有工具配置
        
        Returns:
            按类型分组的工具配置字典
            
        Raises:
            ConfigError: 配置加载失败
        """
        try:
            all_tools = {}
            
            for tool_type in self._supported_tool_types:
                tools = self.load_tools_by_type(tool_type)
                if tools:
                    all_tools[tool_type] = tools
            
            logger.info(f"加载了所有工具配置，共 {sum(len(tools) for tools in all_tools.values())} 个工具")
            return all_tools
            
        except Exception as e:
            logger.error(f"加载所有工具配置失败: {e}")
            raise ConfigError(f"加载所有工具配置失败: {e}")
    
    def load_tool_registry_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """加载工具注册表配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            工具注册表配置数据
            
        Raises:
            ConfigError: 配置加载失败
        """
        # 检查缓存
        cache_key = "tool_registry_config"
        try:
            if use_cache:
                cached_config = self.cache_manager.get(cache_key)
                if cached_config is not None:
                    logger.debug("从缓存加载工具注册表配置")
                    if isinstance(cached_config, dict):
                        return cached_config
                    else:
                        logger.warning(f"缓存中的注册表配置不是字典类型，重新加载: {cache_key}")
            
            config = self.load_config("tools/registry", use_cache=False)
            
            # 缓存结果
            if use_cache:
                self.cache_manager.set(cache_key, config)
            
            return config
            
        except Exception as e:
            logger.warning(f"加载工具注册表配置失败，使用默认配置: {e}")
            # 返回默认配置
            default_config = {
                "auto_discover": True,
                "discovery_paths": [],
                "reload_on_change": False,
                "tools": [],
                "max_tools": 1000,
                "enable_caching": True,
                "cache_ttl": 300,
                "allow_dynamic_loading": True,
                "validate_schemas": True,
                "sandbox_mode": False
            }
            
            # 缓存默认配置
            if use_cache:
                self.cache_manager.set(cache_key, default_config)
            
            return default_config
    
    
    def discover_tool_configs(self, pattern: str = "*") -> List[str]:
        """发现工具配置文件
        
        Args:
            pattern: 文件模式（支持通配符）
            
        Returns:
            配置文件路径列表
        """
        return self.discovery_manager.discover_module_configs("tools", pattern)
    
    def invalidate_cache(self, config_path: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            config_path: 配置文件路径，如果为None则清除所有相关缓存
        """
        if config_path:
            cache_key = f"tool_config:{config_path}"
            self.cache_manager.delete(cache_key)
        else:
            # 清除工具相关的所有缓存
            cache_keys = [
                "tool_registry_config"
            ]
            
            # 清除按类型缓存的工具配置
            for tool_type in self._supported_tool_types:
                cache_keys.append(f"tools_by_type:{tool_type}")
            
            # 清除特定工具配置缓存（需要发现所有工具）
            try:
                all_configs = self.discover_tool_configs("**/*")
                for config in all_configs:
                    cache_keys.append(f"tool_config:{config}")
            except Exception:
                pass  # 忽略发现错误
            
            for key in cache_keys:
                self.cache_manager.delete(key)
            
            logger.debug("清除工具模块所有缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.cache_manager.get_stats()
    
    def _find_tool_config(self, tool_name: str) -> str:
        """查找工具配置文件
        
        Args:
            tool_name: 工具名称
            
        Returns:
            配置文件路径
        """
        # 使用发现管理器查找配置文件
        for tool_type in self._supported_tool_types:
            pattern = f"{tool_type}/{tool_name}"
            configs = self.discovery_manager.discover_module_configs("tools", pattern)
            
            if configs:
                return configs[0]  # 返回第一个匹配的配置
        
        # 如果找不到，返回默认路径
        return f"tools/native/{tool_name}"
    
    def _get_tool_config_files(self, tool_type: str) -> List[str]:
        """获取指定类型的工具配置文件列表
        
        Args:
            tool_type: 工具类型
            
        Returns:
            配置文件名列表
        """
        try:
            # 使用发现管理器获取配置文件列表
            config_files = self.discovery_manager.discover_module_configs("tools", f"{tool_type}/*")
            
            # 提取文件名（不含扩展名和路径）
            file_names = []
            for config_file in config_files:
                file_path = Path(config_file)
                file_names.append(file_path.stem)
            
            return file_names
            
        except Exception as e:
            logger.warning(f"获取工具配置文件列表失败 {tool_type}: {e}")
            return []
    
    def get_supported_tool_types(self) -> List[str]:
        """获取支持的工具类型列表
        
        Returns:
            工具类型列表
        """
        return self._supported_tool_types.copy()
    
    def is_tool_type_supported(self, tool_type: str) -> bool:
        """检查是否支持指定的工具类型
        
        Args:
            tool_type: 工具类型
            
        Returns:
            是否支持
        """
        return tool_type in self._supported_tool_types