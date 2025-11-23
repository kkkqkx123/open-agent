"""LLM配置验证器

负责验证LLM客户端配置的有效性。
"""

from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass

from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMClientConfig
from core.common.exceptions.llm import LLMError


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[str]
    client: Optional[Any] = None
    
    @classmethod
    def success(cls, client: Any) -> "ValidationResult":
        """创建成功的验证结果"""
        return cls(is_valid=True, errors=[], client=client)
    
    @classmethod
    def failure(cls, errors: List[str]) -> "ValidationResult":
        """创建失败的验证结果"""
        return cls(is_valid=False, errors=errors)


class LLMConfigValidator:
    """LLM配置验证器
    
    负责验证LLM客户端配置的有效性，并提供详细的错误信息。
    """
    
    def __init__(self, factory: LLMFactory):
        """
        初始化配置验证器
        
        Args:
            factory: LLM工厂实例
        """
        self._factory = factory
    
    def validate_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> ValidationResult:
        """
        验证配置并返回详细结果
        
        Args:
            config: LLM客户端配置（字典或LLMClientConfig对象）
            
        Returns:
            ValidationResult: 验证结果，包含是否有效、错误列表和客户端实例
        """
        errors = []
        
        try:
            # 转换为字典形式如果需要
            config_dict = config.to_dict() if isinstance(config, LLMClientConfig) else config
            
            # 基础字段验证
            validation_errors = self._validate_basic_fields(config_dict)
            errors.extend(validation_errors)
            
            if errors:
                return ValidationResult.failure(errors)
            
            # 尝试创建客户端实例来验证配置
            client = self._factory.create_client(config_dict)
            if client is None:
                errors.append("工厂无法创建客户端实例")
                return ValidationResult.failure(errors)
            
            return ValidationResult.success(client)
            
        except Exception as e:
            errors.append(f"配置验证失败: {str(e)}")
            return ValidationResult.failure(errors)
    
    def _validate_basic_fields(self, config: Dict[str, Any]) -> List[str]:
        """
        验证基础配置字段
        
        Args:
            config: 配置字典
            
        Returns:
            List[str]: 错误列表
        """
        errors = []
        
        # 检查必需字段
        required_fields = ["model_type", "model_name"]
        for field in required_fields:
            if field not in config or not config[field]:
                errors.append(f"缺少必需字段: {field}")
        
        # 验证模型类型
        if "model_type" in config:
            model_type = config["model_type"]
            supported_types = self._factory.list_supported_types()
            if model_type not in supported_types:
                errors.append(f"不支持的模型类型: {model_type}，支持的类型: {supported_types}")
        
        # 验证API密钥或基础URL
        model_type = config.get("model_type", "")
        if model_type in ["openai", "anthropic", "gemini"]:
            has_api_key = bool(config.get("api_key"))
            has_base_url = bool(config.get("base_url"))
            
            if not has_api_key and not has_base_url:
                errors.append(f"{model_type} 模型需要提供 api_key 或 base_url")
        
        return errors
    
    def validate_config_batch(self, configs: List[Union[Dict[str, Any], LLMClientConfig]]) -> Dict[str, ValidationResult]:
        """
        批量验证配置
        
        Args:
            configs: 配置列表
            
        Returns:
            Dict[str, ValidationResult]: 配置名称到验证结果的映射
        """
        results = {}
        
        for i, config in enumerate(configs):
            config_name = self._get_config_name(config, f"config_{i}")
            results[config_name] = self.validate_config(config)
        
        return results
    
    def _get_config_name(self, config: Union[Dict[str, Any], LLMClientConfig], default: str) -> str:
        """
        获取配置名称
        
        Args:
            config: 配置对象
            default: 默认名称
            
        Returns:
            str: 配置名称
        """
        if isinstance(config, LLMClientConfig):
            return config.model_name
        
        if isinstance(config, dict):
            return config.get("name", config.get("model_name", default))
        
        return default