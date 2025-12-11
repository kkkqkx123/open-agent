"""Global配置模型转换器

提供基础设施层Global配置数据和核心层Global领域模型之间的转换功能。
"""

from typing import Any, Dict, TYPE_CHECKING
from src.infrastructure.config.models import ConfigData
from src.infrastructure.config.models.global_config import LogOutputClientConfig, GlobalClientConfig
from ..models.global_config import GlobalConfig, LogOutputConfig

if TYPE_CHECKING:
    from src.infrastructure.config.models import ConfigData


class GlobalConfigMapper:
    """Global配置模型转换器
    
    负责在基础设施层的基础数据模型和核心层的领域模型之间进行转换。
    """
    
    @staticmethod
    def config_data_to_global_config(config_data: ConfigData) -> GlobalConfig:
        """将基础配置数据转换为Global领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Global领域模型
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 处理log_outputs字段
        log_outputs = []
        if 'log_outputs' in data:
            for output_config in data['log_outputs']:
                if isinstance(output_config, dict):
                    log_outputs.append(LogOutputConfig(**output_config))
                else:
                    log_outputs.append(output_config)
        
        # 创建GlobalConfig实例
        return GlobalConfig(
            log_level=data.get('log_level', 'INFO'),
            log_outputs=log_outputs,
            env=data.get('env', 'development'),
            debug=data.get('debug', False)
        )
    
    @staticmethod
    def global_config_to_config_data(global_config: GlobalConfig) -> ConfigData:
        """将Global领域模型转换为基础配置数据
        
        Args:
            global_config: Global领域模型
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = global_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        return config_data
    
    @staticmethod
    def global_client_config_to_config_data(global_client_config: GlobalClientConfig) -> ConfigData:
        """将Global客户端配置转换为基础配置数据
        
        Args:
            global_client_config: Global客户端配置
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = global_client_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        return config_data
    
    @staticmethod
    def config_data_to_global_client_config(config_data: ConfigData) -> GlobalClientConfig:
        """将基础配置数据转换为Global客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            Global客户端配置
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建GlobalClientConfig实例
        return GlobalClientConfig.from_dict(data)
    
    @staticmethod
    def config_data_to_log_output_config(config_data: ConfigData) -> LogOutputConfig:
        """将基础配置数据转换为LogOutput领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            LogOutput领域模型
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建LogOutputConfig实例
        return LogOutputConfig(
            type=data.get('type', 'console'),
            level=data.get('level', 'INFO'),
            format=data.get('format', 'text'),
            path=data.get('path')
        )
    
    @staticmethod
    def log_output_config_to_config_data(log_output_config: LogOutputConfig) -> ConfigData:
        """将LogOutput领域模型转换为基础配置数据
        
        Args:
            log_output_config: LogOutput领域模型
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = log_output_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        return config_data
    
    @staticmethod
    def log_output_client_config_to_config_data(log_output_client_config: LogOutputClientConfig) -> ConfigData:
        """将LogOutput客户端配置转换为基础配置数据
        
        Args:
            log_output_client_config: LogOutput客户端配置
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = log_output_client_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        return config_data
    
    @staticmethod
    def config_data_to_log_output_client_config(config_data: ConfigData) -> LogOutputClientConfig:
        """将基础配置数据转换为LogOutput客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            LogOutput客户端配置
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建LogOutputClientConfig实例
        return LogOutputClientConfig(**data)


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
    "GlobalConfigMapper"
]