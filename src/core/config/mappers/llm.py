"""LLM配置模型转换器

提供基础设施层LLM配置数据和核心层LLM领域模型之间的转换功能。
"""

from typing import Any, Dict, Optional, List, TYPE_CHECKING
from src.core.config.models.llm_config import LLMConfig

if TYPE_CHECKING:
    from typing import Dict as ConfigData


class LLMConfigMapper:
    """LLM配置模型转换器
    
    负责在基础设施层的基础数据模型和核心层的领域模型之间进行转换。
    """
    
    @staticmethod
    def dict_to_llm_config(data: Dict[str, Any]) -> LLMConfig:
        """将字典数据转换为LLM领域模型
        
        Args:
            data: 字典数据
            
        Returns:
            LLM领域模型
        """
        # 创建LLMConfig实例
        return LLMConfig(**data)
    
    @staticmethod
    def llm_config_to_dict(llm_config: LLMConfig) -> Dict[str, Any]:
        """将LLM领域模型转换为字典数据
        
        Args:
            llm_config: LLM领域模型
            
        Returns:
            字典数据
        """
        # 转换为字典
        return llm_config.model_dump()
    
    
    @staticmethod
    def merge_dict_with_llm_config(
        data: Dict[str, Any],
        llm_config: LLMConfig
    ) -> Dict[str, Any]:
        """合并字典数据和LLM配置
        
        Args:
            data: 字典数据
            llm_config: LLM领域模型
            
        Returns:
            合并后的字典数据
        """
        # 获取两者的字典表示
        llm_dict = llm_config.model_dump()
        
        # 深度合并
        return _deep_merge(data, llm_dict)
    


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