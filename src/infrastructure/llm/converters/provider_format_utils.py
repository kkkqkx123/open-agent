"""提供商格式转换工具类

提供各种LLM提供商的格式转换工具，采用基础类+具体实现的模式。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Sequence
from src.services.logger import get_logger
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage

# 导入具体的供应商格式转换器
from src.infrastructure.llm.converters.openai_format_utils import OpenAIFormatUtils
from src.infrastructure.llm.converters.gemini_format_utils import GeminiFormatUtils
from src.infrastructure.llm.converters.anthropic_format_utils import AnthropicFormatUtils


class BaseProviderFormatUtils(ABC):
    """提供商格式转换基础工具类
    
    定义提供商格式转换的通用接口和公共方法。
    """
    
    def __init__(self) -> None:
        """初始化基础工具类"""
        self.logger = get_logger(__name__)
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        pass
    
    @abstractmethod
    def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """转换请求格式"""
        pass
    
    @abstractmethod
    def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
        """转换响应格式"""
        pass
    
    def _convert_tools_to_openai_format(self, tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """转换工具格式为OpenAI格式（通用方法）"""
        openai_tools = []
        
        for tool in tools:
            function_dict: Dict[str, Any] = {
                "name": tool["name"],
                "description": tool.get("description", ""),
            }
            
            if "parameters" in tool:
                function_dict["parameters"] = tool["parameters"]
            
            openai_tool = {
                "type": "function",
                "function": function_dict
            }
            
            openai_tools.append(openai_tool)
        
        return openai_tools
    
    def _extract_text_from_content(self, content: Union[str, List[Union[str, Dict[str, Any]]]]) -> str:
        """从内容中提取文本（通用方法）"""
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, str):
                    text_parts.append(item)
                elif isinstance(item, dict):
                    if "text" in item:
                        text_parts.append(item["text"])
                    else:
                        # 尝试转换为字符串
                        text_parts.append(str(item))
            return " ".join(text_parts)
        else:
            return str(content)
    
    def _build_base_message(self, content: str, message_type: str, **kwargs: Any) -> "IBaseMessage":
        """构建基础消息（通用方法）"""
        from src.infrastructure.messages import (
            HumanMessage,
            AIMessage,
            SystemMessage,
            ToolMessage,
        )
        
        common_kwargs = {
            "name": kwargs.get("name"),
            "additional_kwargs": kwargs.get("additional_kwargs", {}),
            "response_metadata": kwargs.get("response_metadata", {}),
            "id": kwargs.get("id"),
            "timestamp": kwargs.get("timestamp")
        }
        
        if message_type == "human":
            return HumanMessage(content=content, **common_kwargs)
        elif message_type == "ai":
            return AIMessage(
                content=content,
                tool_calls=kwargs.get("tool_calls"),
                **common_kwargs
            )
        elif message_type == "system":
            return SystemMessage(content=content, **common_kwargs)
        elif message_type == "tool":
            return ToolMessage(
                content=content,
                tool_call_id=kwargs.get("tool_call_id", ""),
                **common_kwargs
            )
        else:
            return HumanMessage(content=content, **common_kwargs)


class ProviderFormatUtilsFactory:
    """提供商格式工具工厂
    
    负责创建和管理各种提供商的格式转换工具。
    """
    
    def __init__(self) -> None:
        """初始化工厂"""
        self.logger = get_logger(__name__)
        self._utils_cache: Dict[str, BaseProviderFormatUtils] = {}
    
    def get_format_utils(self, provider: str) -> BaseProviderFormatUtils:
        """获取提供商格式转换工具
        
        Args:
            provider: 提供商名称
            
        Returns:
            BaseProviderFormatUtils: 格式转换工具实例
        """
        if provider not in self._utils_cache:
            if provider == "openai":
                self._utils_cache[provider] = OpenAIFormatUtils()
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
        return ["openai", "gemini", "anthropic"]
    
    def register_provider(self, provider: str, utils_class: type) -> None:
        """注册新的提供商格式转换工具
        
        Args:
            provider: 提供商名称
            utils_class: 工具类
        """
        if not issubclass(utils_class, BaseProviderFormatUtils):
            raise ValueError("工具类必须继承自BaseProviderFormatUtils")
        
        self._utils_cache[provider] = utils_class()
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