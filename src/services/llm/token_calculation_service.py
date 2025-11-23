"""统一的Token计算服务
"""

from typing import Dict, Any, Optional, Sequence
from langchain_core.messages import BaseMessage

from .token_processing.base_processor import ITokenProcessor
from .token_processing.openai_processor import OpenAITokenProcessor
from .token_processing.gemini_processor import GeminiTokenProcessor
from .token_processing.anthropic_processor import AnthropicTokenProcessor
from .token_processing.hybrid_processor import HybridTokenProcessor
from .token_processing.token_types import TokenUsage


class TokenCalculationService:
    """统一的Token计算服务"""
    
    def __init__(self, default_provider: str = "openai"):
        """
        初始化Token计算服务
        
        Args:
            default_provider: 默认提供商名称
        """
        self._default_provider = default_provider
        self._processors: Dict[str, ITokenProcessor] = {}
        
    def _get_processor_for_model(self, model_type: str, model_name: str) -> ITokenProcessor:
        """
        获取指定模型的处理器
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            ITokenProcessor: 对应的处理器
        """
        # 创建唯一的处理器键
        processor_key = f"{model_type}:{model_name}"
        
        # 如果处理器已存在，直接返回
        if processor_key in self._processors:
            return self._processors[processor_key]
        
        # 根据模型类型创建处理器
        if model_type.lower() == "openai":
            processor = OpenAITokenProcessor(model_name)
        elif model_type.lower() == "gemini":
            # Gemini处理器需要特定的实现
            processor = GeminiTokenProcessor(model_name)
        elif model_type.lower() == "anthropic":
            processor = AnthropicTokenProcessor(model_name)
        else:
            # 使用混合处理器作为默认选项
            processor = HybridTokenProcessor(model_type, model_name)
        
        # 缓存处理器
        self._processors[processor_key] = processor
        return processor
    
    def calculate_tokens(self, text: str, model_type: str, model_name: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        processor = self._get_processor_for_model(model_type, model_name)
        result = processor.count_tokens(text)
        return result if result is not None else 0
    
    def calculate_messages_tokens(self, messages: Sequence[BaseMessage], model_type: str, model_name: str) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            int: token数量
        """
        processor = self._get_processor_for_model(model_type, model_name)
        result = processor.count_messages_tokens(messages)
        return result if result is not None else 0
    
    def parse_token_usage_from_response(self, response: Dict[str, Any], model_type: str) -> Optional[TokenUsage]:
        """
        从API响应中解析token使用情况
        
        Args:
            response: API响应
            model_type: 模型类型
            
        Returns:
            Optional[TokenUsage]: token使用情况
        """
        # 根据模型类型创建临时处理器来解析响应
        if model_type.lower() == "openai":
            processor = OpenAITokenProcessor("gpt-3.5-turbo")  # 临时使用默认模型名
        elif model_type.lower() == "gemini":
            processor = GeminiTokenProcessor("gemini-pro")  # 临时使用默认模型名
        elif model_type.lower() == "anthropic":
            processor = AnthropicTokenProcessor("claude-3")  # 临时使用默认模型名
        else:
            processor = HybridTokenProcessor(model_type, "default")
        
        return processor.parse_response(response)
    
    def get_processor_stats(self, model_type: str, model_name: str) -> Dict[str, Any]:
        """
        获取处理器统计信息
        
        Args:
            model_type: 模型类型
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        processor = self._get_processor_for_model(model_type, model_name)
        return processor.get_stats()