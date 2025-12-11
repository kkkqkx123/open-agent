"""
工具配置实现

提供工具模块的配置实现，遵循基础设施层的职责。
"""

from typing import Dict, Any, Optional, List
from pathlib import Path
import logging

from .base_impl import BaseConfigImpl, ConfigProcessorChain
from src.interfaces.config import IConfigLoader, IConfigProcessor
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
    
    def load_tool_config(self, tool_name: str, tool_type: Optional[str] = None) -> Dict[str, Any]:
        """加载特定工具的配置
        
        Args:
            tool_name: 工具名称
            tool_type: 工具类型（可选）
            
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
            
            logger.debug(f"加载工具配置: {config_path}")
            return self.load_config(config_path)
            
        except Exception as e:
            logger.error(f"加载工具配置失败 {tool_name}: {e}")
            raise ConfigError(f"加载工具配置失败 {tool_name}: {e}")
    
    def load_tools_by_type(self, tool_type: str) -> List[Dict[str, Any]]:
        """按类型加载所有工具配置
        
        Args:
            tool_type: 工具类型
            
        Returns:
            工具配置列表
            
        Raises:
            ConfigError: 配置加载失败
        """
        try:
            if tool_type not in self._supported_tool_types:
                raise ConfigError(f"不支持的工具类型: {tool_type}")
            
            # 获取指定类型的所有配置文件
            config_files = self._get_tool_config_files(tool_type)
            
            tools = []
            for config_file in config_files:
                try:
                    config_path = f"tools/{tool_type}/{config_file}"
                    tool_config = self.load_config(config_path)
                    
                    # 确保工具类型正确
                    tool_config["tool_type"] = tool_type
                    tools.append(tool_config)
                    
                except Exception as e:
                    logger.warning(f"加载工具配置失败 {config_file}: {e}")
                    continue
            
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
    
    def load_tool_registry_config(self) -> Dict[str, Any]:
        """加载工具注册表配置
        
        Returns:
            工具注册表配置数据
            
        Raises:
            ConfigError: 配置加载失败
        """
        try:
            return self.load_config("tools/registry")
            
        except Exception as e:
            logger.warning(f"加载工具注册表配置失败，使用默认配置: {e}")
            # 返回默认配置
            return {
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
    
    def validate_tool_config(self, tool_config: Dict[str, Any]) -> bool:
        """验证工具配置
        
        Args:
            tool_config: 工具配置数据
            
        Returns:
            是否有效
        """
        try:
            # 基础字段验证
            required_fields = ["name", "description", "parameters_schema"]
            for field in required_fields:
                if field not in tool_config:
                    logger.error(f"工具配置缺少必需字段: {field}")
                    return False
            
            # 工具类型验证
            tool_type = tool_config.get("tool_type")
            if tool_type and tool_type not in self._supported_tool_types:
                logger.error(f"不支持的工具类型: {tool_type}")
                return False
            
            # 类型特定验证
            if tool_type == "rest":
                if "api_url" not in tool_config:
                    logger.error("REST工具缺少api_url字段")
                    return False
            elif tool_type == "mcp":
                if "mcp_server_url" not in tool_config:
                    logger.error("MCP工具缺少mcp_server_url字段")
                    return False
            elif tool_type in ["builtin", "native"]:
                if "function_path" not in tool_config:
                    logger.error(f"{tool_type}工具缺少function_path字段")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"验证工具配置失败: {e}")
            return False
    
    def _find_tool_config(self, tool_name: str) -> str:
        """查找工具配置文件
        
        Args:
            tool_name: 工具名称
            
        Returns:
            配置文件路径
        """
        # 在不同类型目录中查找
        for tool_type in self._supported_tool_types:
            config_path = f"tools/{tool_type}/{tool_name}"
            try:
                # 尝试加载配置来检查是否存在
                self.config_loader.load(config_path)
                return config_path
            except Exception:
                continue
        
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
            # 使用list_configs方法获取配置文件列表
            config_files = self.config_loader.list_configs(f"tools/{tool_type}")
            
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