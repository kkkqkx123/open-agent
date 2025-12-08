"""提供商格式转换工具类

提供各种LLM提供商的格式转换工具，采用新的核心架构。
"""

from typing import Dict, Any, List, Optional, Union, Sequence
from src.services.logger.injection import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

# 导入核心架构
from .core.provider_base import BaseProvider

# 导入具体的供应商格式转换器
from src.infrastructure.llm.converters.openai.openai_format_utils import OpenAIFormatUtils
from src.infrastructure.llm.converters.openai_response.openai_responses_format_utils import OpenAIResponsesFormatUtils
from src.infrastructure.llm.converters.gemini.gemini_format_utils import GeminiFormatUtils
from src.infrastructure.llm.converters.anthropic.anthropic_format_utils import AnthropicFormatUtils


class ProviderFormatUtils:
    """提供商格式工具类
    
    使用新的核心架构，提供统一的格式转换接口。
    """
    
    def __init__(self) -> None:
        """初始化提供商格式工具"""
        self.logger = get_logger(__name__)
        self._providers_cache: Dict[str, BaseProvider] = {}
    
    def get_provider(self, provider_name: str) -> BaseProvider:
        """获取提供商实例
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            BaseProvider: 提供商实例
        """
        if provider_name not in self._providers_cache:
            if provider_name == "openai":
                self._providers_cache[provider_name] = OpenAIFormatUtils()
            elif provider_name == "openai-responses":
                self._providers_cache[provider_name] = OpenAIResponsesFormatUtils()
            elif provider_name == "gemini":
                self._providers_cache[provider_name] = GeminiFormatUtils()
            elif provider_name == "anthropic":
                self._providers_cache[provider_name] = AnthropicFormatUtils()
            else:
                raise ValueError(f"不支持的提供商: {provider_name}")
        
        return self._providers_cache[provider_name]
    
    def convert_request(self, provider_name: str, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式
        
        Args:
            provider_name: 提供商名称
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            Dict[str, Any]: 提供商API请求格式
        """
        provider = self.get_provider(provider_name)
        return provider.convert_request(list(messages), parameters)
    
    def convert_response(self, provider_name: str, response: Dict[str, Any]) -> "IBaseMessage":
        """转换响应格式
        
        Args:
            provider_name: 提供商名称
            response: 提供商API响应
            
        Returns:
            IBaseMessage: 基础消息
        """
        provider = self.get_provider(provider_name)
        return provider.convert_response(response)
    
    def convert_stream_response(self, provider_name: str, events: List[Dict[str, Any]]) -> "IBaseMessage":
        """转换流式响应格式
        
        Args:
            provider_name: 提供商名称
            events: 流式事件列表
            
        Returns:
            IBaseMessage: 基础消息
        """
        provider = self.get_provider(provider_name)
        return provider.convert_stream_response(events)
    
    def validate_request(self, provider_name: str, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> List[str]:
        """验证请求参数
        
        Args:
            provider_name: 提供商名称
            messages: 基础消息列表
            parameters: 请求参数
            
        Returns:
            List[str]: 验证错误列表
        """
        provider = self.get_provider(provider_name)
        return provider.validate_request(list(messages), parameters)
    
    def handle_api_error(self, provider_name: str, error_response: Dict[str, Any]) -> str:
        """处理API错误响应
        
        Args:
            provider_name: 提供商名称
            error_response: 错误响应
            
        Returns:
            str: 用户友好的错误消息
        """
        provider = self.get_provider(provider_name)
        return provider.handle_error(error_response)
    
    def get_supported_providers(self) -> List[str]:
        """获取支持的提供商列表
        
        Returns:
            List[str]: 支持的提供商名称列表
        """
        return ["openai", "openai-responses", "gemini", "anthropic"]
    
    def get_provider_models(self, provider_name: str) -> List[str]:
        """获取提供商支持的模型列表
        
        Args:
            provider_name: 提供商名称
            
        Returns:
            List[str]: 支持的模型列表
        """
        provider = self.get_provider(provider_name)
        return provider.get_supported_models()
    
    def validate_provider_model(self, provider_name: str, model: str) -> List[str]:
        """验证提供商模型
        
        Args:
            provider_name: 提供商名称
            model: 模型名称
            
        Returns:
            List[str]: 验证错误列表
        """
        provider = self.get_provider(provider_name)
        return provider.validate_model(model)
    
    def validate_provider_api_key(self, provider_name: str, api_key: str) -> List[str]:
        """验证提供商API密钥
        
        Args:
            provider_name: 提供商名称
            api_key: API密钥
            
        Returns:
            List[str]: 验证错误列表
        """
        provider = self.get_provider(provider_name)
        return provider.validate_api_key(api_key)


class ProviderFormatUtilsFactory:
    """提供商格式工具工厂
    
    负责创建和管理各种提供商的格式转换工具。
    """
    
    def __init__(self) -> None:
        """初始化工厂"""
        self.logger = get_logger(__name__)
        self._utils_cache: Dict[str, BaseProvider] = {}
    
    def get_format_utils(self, provider: str) -> BaseProvider:
        """获取提供商格式转换工具
        
        Args:
            provider: 提供商名称
            
        Returns:
            BaseProvider: 格式转换工具实例
        """
        if provider not in self._utils_cache:
            if provider == "openai":
                self._utils_cache[provider] = OpenAIFormatUtils()
            elif provider == "openai-responses":
                self._utils_cache[provider] = OpenAIResponsesFormatUtils()
            elif provider == "gemini":
                self._utils_cache[provider] = GeminiFormatUtils()
            elif provider == "anthropic":
                self._utils_cache[provider] = AnthropicFormatUtils()
            else:
                raise ValueError(f"不支持的提供商: {provider}")
        
        return self._utils_cache[provider]
    
    def get_supported_providers(self) -> List[str]:
        """获取支持的提供商列表
        
        Returns:
            List[str]: 支持的提供商名称列表
        """
        return ["openai", "openai-responses", "gemini", "anthropic"]
    
    def register_provider(self, provider: str, provider_class: type) -> None:
        """注册新的提供商格式转换工具
        
        Args:
            provider: 提供商名称
            provider_class: 提供商类
        """
        if not issubclass(provider_class, BaseProvider):
            raise ValueError("提供商类必须继承自BaseProvider")
        
        self._utils_cache[provider] = provider_class(name=provider)
        self.logger.info(f"已注册提供商格式转换工具: {provider}")


# 全局工厂实例
_global_format_utils_factory: Optional[ProviderFormatUtilsFactory] = None


def get_provider_format_utils_factory() -> ProviderFormatUtilsFactory:
    """获取全局提供商格式工具工厂实例
    
    Returns:
        ProviderFormatUtilsFactory: 工厂实例
    """
    global _global_format_utils_factory
    if _global_format_utils_factory is None:
        _global_format_utils_factory = ProviderFormatUtilsFactory()
    return _global_format_utils_factory

