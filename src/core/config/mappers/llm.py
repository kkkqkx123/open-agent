"""LLM配置模型转换器

提供基础设施层LLM配置数据和核心层LLM领域模型之间的转换功能。
"""

from typing import Any, Dict, Optional, List, TYPE_CHECKING
from src.infrastructure.config.models import ConfigData
from src.infrastructure.config.models.llm import LLMClientConfig
from ..models.llm_config import LLMConfig

if TYPE_CHECKING:
    from src.infrastructure.config.models import ConfigData


class LLMConfigMapper:
    """LLM配置模型转换器
    
    负责在基础设施层的基础数据模型和核心层的领域模型之间进行转换。
    """
    
    @staticmethod
    def config_data_to_llm_config(config_data: ConfigData) -> LLMConfig:
        """将基础配置数据转换为LLM领域模型
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            LLM领域模型
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建LLMConfig实例
        return LLMConfig(
            model_type=data.get('model_type', ''),
            model_name=data.get('model_name', ''),
            provider=data.get('provider'),
            base_url=data.get('base_url'),
            api_key=data.get('api_key'),
            headers=data.get('headers', {}),
            parameters=data.get('parameters', {}),
            group=data.get('group'),
            token_counter=data.get('token_counter'),
            metadata=data.get('metadata', {})
        )
    
    @staticmethod
    def llm_config_to_config_data(llm_config: LLMConfig) -> ConfigData:
        """将LLM领域模型转换为基础配置数据
        
        Args:
            llm_config: LLM领域模型
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = llm_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if llm_config.metadata:
            config_data.metadata = llm_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def llm_client_config_to_config_data(llm_client_config: LLMClientConfig) -> ConfigData:
        """将LLM客户端配置转换为基础配置数据
        
        Args:
            llm_client_config: LLM客户端配置
            
        Returns:
            基础配置数据
        """
        # 转换为字典
        data = llm_client_config.to_dict()
        
        # 创建ConfigData实例
        config_data = ConfigData(data)
        
        # 设置元数据
        if llm_client_config.metadata:
            config_data.metadata = llm_client_config.metadata.copy()
        
        return config_data
    
    @staticmethod
    def config_data_to_llm_client_config(config_data: ConfigData) -> LLMClientConfig:
        """将基础配置数据转换为LLM客户端配置
        
        Args:
            config_data: 基础配置数据
            
        Returns:
            LLM客户端配置
        """
        # 提取基础配置
        data = config_data.to_dict()
        
        # 创建LLMClientConfig实例
        return LLMClientConfig(**data)
    
    @staticmethod
    def merge_config_data_with_llm_config(
        config_data: ConfigData, 
        llm_config: LLMConfig
    ) -> ConfigData:
        """合并配置数据和LLM配置
        
        Args:
            config_data: 基础配置数据
            llm_config: LLM领域模型
            
        Returns:
            合并后的配置数据
        """
        # 获取两者的字典表示
        config_dict = config_data.to_dict()
        llm_dict = llm_config.to_dict()
        
        # 深度合并
        merged_dict = _deep_merge(config_dict, llm_dict)
        
        # 创建新的ConfigData
        return ConfigData(merged_dict)
    
    @staticmethod
    def llm_config_to_client_config(llm_config: LLMConfig) -> LLMClientConfig:
        """将LLM领域模型转换为客户端配置
        
        Args:
            llm_config: LLM领域模型
            
        Returns:
            LLM客户端配置
        """
        # 获取客户端配置字典
        client_config_dict = llm_config.get_client_config()
        
        # 添加生成参数
        generation_params = llm_config.get_generation_params()
        client_config_dict.update(generation_params)
        
        # 创建LLMClientConfig实例
        return LLMClientConfig(**client_config_dict)


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
    "LLMConfigMapper"
]