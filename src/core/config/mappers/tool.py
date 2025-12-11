"""Tool配置模型转换器

提供基础设施层Tool配置数据和核心层Tool领域模型之间的转换功能。
"""

from typing import Any, Dict, TYPE_CHECKING
from src.infrastructure.config.models import ConfigData
from src.infrastructure.config.models.tool import ToolClientConfig, ToolSetClientConfig
from ..models.tool_config import ToolConfig, ToolSetConfig

if TYPE_CHECKING:
    from src.infrastructure.config.models import ConfigData


class ToolConfigMapper:
    """Tool配置模型转换器
    
    负责在基础设施层的基础数据模型和核心层的领域模型之间进行转换。
    """
    
    @staticmethod
    def config_data_to_tool_config(config_data: ConfigData) -> ToolConfig:
        """将基础配置数据转换为Tool领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Tool领域模型
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建ToolConfig实例
        return ToolConfig(
            name=data.get('name', ''),
            description=data.get('description'),
            tool_type=data.get('tool_type', ''),
            parameters_schema=data.get('parameters_schema', {}),
            enabled=data.get('enabled', True),
            function_path=data.get('function_path'),
            api_url=data.get('api_url'),
            mcp_server_url=data.get('mcp_server_url'),
            category=data.get('category'),
            tags=data.get('tags', []),
            version=data.get('version'),
            group=data.get('group'),
            timeout=data.get('timeout'),
            retry_config=data.get('retry_config', {}),
            metadata=data.get('metadata', {})
        )
    
    @staticmethod
    def tool_config_to_config_data(tool_config: ToolConfig) -> ConfigData:
        """将Tool领域模型转换为基础配置数据
        
        Args:
            tool_config: Tool领域模型
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = tool_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if tool_config.metadata:
            config_data.metadata = tool_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def tool_client_config_to_config_data(tool_client_config: ToolClientConfig) -> ConfigData:
        """将Tool客户端配置转换为基础配置数据
        
        Args:
            tool_client_config: Tool客户端配置
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = tool_client_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if tool_client_config.metadata:
            config_data.metadata = tool_client_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def config_data_to_tool_client_config(config_data: ConfigData) -> ToolClientConfig:
        """将基础配置数据转换为Tool客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Tool客户端配置
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建ToolClientConfig实例
        return ToolClientConfig(**data)
    
    @staticmethod
    def config_data_to_tool_set_config(config_data: ConfigData) -> ToolSetConfig:
        """将基础配置数据转换为ToolSet领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            ToolSet领域模型
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建ToolSetConfig实例
        return ToolSetConfig(
            name=data.get('name', ''),
            description=data.get('description'),
            tools=data.get('tools', []),
            enabled=data.get('enabled', True),
            version=data.get('version'),
            auto_discover=data.get('auto_discover', False),
            discovery_paths=data.get('discovery_paths', []),
            metadata=data.get('metadata', {})
        )
    
    @staticmethod
    def tool_set_config_to_config_data(tool_set_config: ToolSetConfig) -> ConfigData:
        """将ToolSet领域模型转换为基础配置数据
        
        Args:
            tool_set_config: ToolSet领域模型
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = tool_set_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if tool_set_config.metadata:
            config_data.metadata = tool_set_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def tool_set_client_config_to_config_data(tool_set_client_config: ToolSetClientConfig) -> ConfigData:
        """将ToolSet客户端配置转换为基础配置数据
        
        Args:
            tool_set_client_config: ToolSet客户端配置
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = tool_set_client_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if tool_set_client_config.metadata:
            config_data.metadata = tool_set_client_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def config_data_to_tool_set_client_config(config_data: ConfigData) -> ToolSetClientConfig:
        """将基础配置数据转换为ToolSet客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            ToolSet客户端配置
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建ToolSetClientConfig实例
        return ToolSetClientConfig(**data)


def _deep_merge(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """深度合并两个字典
    
    Args:
        dict1: 第一个字典
        dict2: 第二个字典
        
    Returns:
        合并后的字典
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    
    return result


__all__ = [
    "ToolConfigMapper"
]