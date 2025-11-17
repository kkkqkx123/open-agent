"""Token计算器入口文件

此文件作为向后兼容的入口，重新导出新的token计数模块的功能。
实际的实现已经迁移到 token_calculators 和 token_parsers 模块中。
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING, Sequence

from langchain_core.messages import BaseMessage  # type: ignore

# 导入新的模块
from .token_parsers import TokenUsage
from .token_calculators import (
    ITokenCalculator as ITokenCounter,
    LocalTokenCalculator,
    ApiTokenCalculator,
    HybridTokenCalculator
)
from .utils.encoding_protocol import EncodingProtocol, extract_content_as_string

# 重新导出以保持向后兼容
__all__ = [
    "TokenUsage",
    "ITokenCounter",
    "LocalTokenCalculator",
    "ApiTokenCalculator", 
    "HybridTokenCalculator",
    "OpenAITokenCounter",
    "GeminiTokenCounter",
    "AnthropicTokenCounter",
    "MockTokenCounter",
    "EnhancedOpenAITokenCounter",
    "EnhancedGeminiTokenCounter",
    "EnhancedAnthropicTokenCounter",
    "TokenCounterFactory",
    "EncodingProtocol",
    "_extract_content_as_string"
]

# 为了向后兼容，保留原有的函数名
_extract_content_as_string = extract_content_as_string


# 向后兼容的计数器实现类
class OpenAITokenCounter(ITokenCounter):
    """OpenAI Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "gpt-3.5-turbo") -> None:
        self._calculator = LocalTokenCalculator(model_name, "openai")

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return None

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str) -> int:
        return self._calculator.count_tokens(text) or 0

    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages)) or 0

    def get_model_info(self) -> Dict[str, Any]:
        return self._calculator.get_model_info()

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()


class GeminiTokenCounter(ITokenCounter):
    """Gemini Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "gemini-pro") -> None:
        self._calculator = LocalTokenCalculator(model_name, "gemini")

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return None

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str) -> int:
        return self._calculator.count_tokens(text) or 0

    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages)) or 0

    def get_model_info(self) -> Dict[str, Any]:
        return self._calculator.get_model_info()

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()


class AnthropicTokenCounter(ITokenCounter):
    """Anthropic Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "claude-3-sonnet-20240229") -> None:
        self._calculator = LocalTokenCalculator(model_name, "anthropic")

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return None

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str) -> int:
        return self._calculator.count_tokens(text) or 0

    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages)) or 0

    def get_model_info(self) -> Dict[str, Any]:
        return self._calculator.get_model_info()

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()


class MockTokenCounter(ITokenCounter):
    """Mock Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "mock-model") -> None:
        self._calculator = LocalTokenCalculator(model_name, "mock")

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return None

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str) -> int:
        # 保持原有的Mock计数逻辑
        if len(text) <= 4:
            return 2  # 对于短文本，至少返回2个token
        return len(text) // 4

    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> int:
        total_tokens = 0

        for message in messages:
            # 每条消息内容的token
            content_tokens = self.count_tokens(
                extract_content_as_string(message.content)
            )
            total_tokens += content_tokens

            # 添加格式化的token（每个消息4个token）
            total_tokens += 4

        # 添加回复的token（3个token）
        total_tokens += 3

        return total_tokens

    def get_model_info(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": "mock",
            "encoding": "estimated",
            "supports_tiktoken": False,
        }

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()


# 增强版本的计数器（使用混合计算器）
class EnhancedOpenAITokenCounter(ITokenCounter):
    """增强的OpenAI Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "gpt-3.5-turbo", config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        prefer_api = self.config.get("prefer_api", True)
        enable_degradation = self.config.get("enable_degradation", True)
        supports_token_caching = self.config.get("supports_token_caching", True)
        track_conversation = self.config.get("track_conversation", False)
        
        self._calculator = HybridTokenCalculator(
            model_name, 
            "openai", 
            prefer_api=prefer_api,
            enable_degradation=enable_degradation,
            supports_token_caching=supports_token_caching,
            track_conversation=track_conversation
        )

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        # 返回API计算器的缓存
        return getattr(self._calculator._api_calculator, '_usage_cache', None)

    @property
    def calibrator(self) -> Optional[Any]:
        # 混合计算器没有校准器，返回None
        return None

    def count_tokens(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_tokens(text, api_response)

    def count_messages_tokens(self, messages: Sequence[BaseMessage],
                             api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages), api_response)

    def get_model_info(self) -> Dict[str, Any]:
        info = self._calculator.get_model_info()
        # 添加增强版本特有的信息
        info.update({
            "supports_api_usage": True,
            "calibration_confidence": 0.0,  # 混合计算器没有校准器
            "api_usage_stats": self._calculator.get_stats()
        })
        return info

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()

    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 对话统计信息，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_stats()

    def get_conversation_tokens(self) -> Optional[int]:
        """
        获取对话的token总数
        
        Returns:
            Optional[int]]: 对话的token总数，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_tokens()

    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._calculator.clear_conversation_history()


class EnhancedGeminiTokenCounter(ITokenCounter):
    """增强的Gemini Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "gemini-pro", config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        prefer_api = self.config.get("prefer_api", True)
        enable_degradation = self.config.get("enable_degradation", True)
        supports_token_caching = self.config.get("supports_token_caching", False)  # Gemini 默认不支持缓存
        track_conversation = self.config.get("track_conversation", False)
        
        self._calculator = HybridTokenCalculator(
            model_name, 
            "gemini", 
            prefer_api=prefer_api,
            enable_degradation=enable_degradation,
            supports_token_caching=supports_token_caching,
            track_conversation=track_conversation
        )

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return getattr(self._calculator._api_calculator, '_usage_cache', None)

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_tokens(text, api_response)

    def count_messages_tokens(self, messages: Sequence[BaseMessage],
                             api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages), api_response)

    def get_model_info(self) -> Dict[str, Any]:
        info = self._calculator.get_model_info()
        info.update({
            "supports_api_usage": True,
            "calibration_confidence": 0.0,
            "api_usage_stats": self._calculator.get_stats()
        })
        return info

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()

    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 对话统计信息，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_stats()

    def get_conversation_tokens(self) -> Optional[int]:
        """
        获取对话的token总数
        
        Returns:
            Optional[int]]: 对话的token总数，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_tokens()

    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._calculator.clear_conversation_history()


class EnhancedAnthropicTokenCounter(ITokenCounter):
    """增强的Anthropic Token计算器（向后兼容包装器）"""

    def __init__(self, model_name: str = "claude-3-sonnet-20240229", config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        prefer_api = self.config.get("prefer_api", True)
        enable_degradation = self.config.get("enable_degradation", True)
        supports_token_caching = self.config.get("supports_token_caching", True)
        track_conversation = self.config.get("track_conversation", False)
        
        self._calculator = HybridTokenCalculator(
            model_name, 
            "anthropic", 
            prefer_api=prefer_api,
            enable_degradation=enable_degradation,
            supports_token_caching=supports_token_caching,
            track_conversation=track_conversation
        )

    @property
    def model_name(self) -> str:
        return self._calculator.model_name

    @property
    def provider(self) -> str:
        return self._calculator.provider

    @property
    def cache(self) -> Optional[Any]:
        return getattr(self._calculator._api_calculator, '_usage_cache', None)

    @property
    def calibrator(self) -> Optional[Any]:
        return None

    def count_tokens(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_tokens(text, api_response)

    def count_messages_tokens(self, messages: Sequence[BaseMessage],
                             api_response: Optional[Dict[str, Any]] = None) -> int:
        return self._calculator.count_messages_tokens(list(messages), api_response)

    def get_model_info(self) -> Dict[str, Any]:
        info = self._calculator.get_model_info()
        info.update({
            "supports_api_usage": True,
            "calibration_confidence": 0.0,
            "api_usage_stats": self._calculator.get_stats()
        })
        return info

    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        return self._calculator.update_from_api_response(response, context)

    def get_last_api_usage(self) -> Optional[TokenUsage]:
        return self._calculator.get_last_api_usage()

    def is_api_usage_available(self) -> bool:
        return self._calculator.is_api_usage_available()

    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 对话统计信息，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_stats()

    def get_conversation_tokens(self) -> Optional[int]:
        """
        获取对话的token总数
        
        Returns:
            Optional[int]]: 对话的token总数，如果未启用对话跟踪则返回None
        """
        return self._calculator.get_conversation_tokens()

    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._calculator.clear_conversation_history()


class TokenCounterFactory:
    """Token计算器工厂（向后兼容包装器）"""

    @staticmethod
    def create_counter(model_type: str, model_name: str, enhanced: bool = False, 
                      config: Optional[Dict[str, Any]] = None) -> ITokenCounter:
        """
        创建Token计算器

        Args:
            model_type: 模型类型
            model_name: 模型名称
            enhanced: 是否使用增强版本
            config: 配置信息

        Returns:
            ITokenCounter: Token计算器实例
        """
        if enhanced:
            # 创建增强版本的计数器
            if model_type == "openai":
                return EnhancedOpenAITokenCounter(model_name, config)
            elif model_type == "gemini":
                return EnhancedGeminiTokenCounter(model_name, config)
            elif model_type in ["anthropic", "claude"]:
                return EnhancedAnthropicTokenCounter(model_name, config)
            else:
                # 默认使用增强的OpenAI计数器
                return EnhancedOpenAITokenCounter(model_name, config)
        else:
            # 创建传统版本的计数器
            if model_type == "openai":
                return OpenAITokenCounter(model_name)
            elif model_type == "gemini":
                return GeminiTokenCounter(model_name)
            elif model_type in ["anthropic", "claude"]:
                return AnthropicTokenCounter(model_name)
            elif model_type == "mock":
                return MockTokenCounter(model_name)
            else:
                # 默认使用OpenAI计算器
                return OpenAITokenCounter(model_name)

    @staticmethod
    def get_supported_types() -> List[str]:
        """
        获取支持的模型类型

        Returns:
            List[str]: 支持的模型类型列表
        """
        return ["openai", "gemini", "anthropic", "claude", "mock"]
    
    @staticmethod
    def create_with_config(config: Dict[str, Any]) -> ITokenCounter:
        """根据配置创建计数器"""
        model_type = config.get("model_type", "openai")
        model_name = config.get("model_name", "gpt-3.5-turbo")
        enhanced = config.get("enhanced", False)
        
        counter = TokenCounterFactory.create_counter(model_type, model_name, enhanced, config)
        
        # 对于增强版本，应用额外配置
        if enhanced and hasattr(counter, '_calculator'):
            calculator = getattr(counter, '_calculator', None)
            if calculator and hasattr(calculator, '_api_calculator') and hasattr(calculator._api_calculator, 'clear_cache'):
                # 如果有缓存配置，可以在这里应用
                cache_config = config.get("cache", {})
                if cache_config.get("clear_on_init", False):
                    calculator._api_calculator.clear_cache()
            
            # 设置降级策略
            if calculator and hasattr(calculator, 'set_enable_degradation'):
                enable_degradation = config.get("enable_degradation", True)
                calculator.set_enable_degradation(enable_degradation)
            
            # 设置API优先级
            if calculator and hasattr(calculator, 'set_prefer_api'):
                prefer_api = config.get("prefer_api", True)
                calculator.set_prefer_api(prefer_api)
            
            # 设置token缓存支持
            if calculator and hasattr(calculator, 'set_supports_token_caching'):
                supports_token_caching = config.get("supports_token_caching", True)
                calculator.set_supports_token_caching(supports_token_caching)
            
            # 设置对话跟踪
            if calculator and hasattr(calculator, 'set_track_conversation'):
                track_conversation = config.get("track_conversation", False)
                calculator.set_track_conversation(track_conversation)
        
        return counter
    
    @staticmethod
    def create_with_model_config(model_config: Dict[str, Any]) -> ITokenCounter:
        """根据模型配置创建计数器"""
        model_type = model_config.get("model_type", "openai")
        model_name = model_config.get("model_name", "gpt-3.5-turbo")
        
        # 从新的LLM配置中提取缓存设置
        supports_caching = model_config.get("supports_caching", False)
        cache_config = model_config.get("cache_config", {})
        
        # 从配置中提取token相关设置
        token_config = {
            "supports_token_caching": supports_caching,
            "track_conversation": model_config.get("track_conversation", False),
            "max_context_tokens": model_config.get("max_tokens", 2000),
            "enhanced": True,  # 默认使用增强版本
            # 添加缓存配置
            "cache": {
                "enabled": cache_config.get("enabled", supports_caching),
                "ttl_seconds": cache_config.get("ttl_seconds", 3600),
                "max_size": cache_config.get("max_size", 1000),
                "clear_on_init": cache_config.get("clear_on_init", False)
            }
        }
        
        return TokenCounterFactory.create_counter(model_type, model_name, True, token_config)