"""Gemini Token处理器

整合了Gemini的Token计算和解析功能。
"""

import logging
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage

from .base_processor import ITokenProcessor, TokenUsage
from .base_implementation import BaseTokenProcessor
from ..utils.encoding_protocol import extract_content_as_string

logger = logging.getLogger(__name__)


class GeminiTokenProcessor(BaseTokenProcessor):
    """Gemini Token处理器
    
    整合了Gemini的Token计算和解析功能。
    """
    
    def __init__(self, model_name: str = "gemini-pro"):
        """
        初始化Gemini Token处理器
        
        Args:
            model_name: 模型名称
        """
        super().__init__(model_name, "gemini")
    
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量
        """
        # Gemini没有公开的token计算库，使用估算
        # Gemini大约4个字符=1个token
        return len(text) // 4
    
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            api_response: API响应（可选，用于更准确的计算）
            
        Returns:
            Optional[int]: token数量
        """
        # 如果有API响应，优先使用API响应中的token数量
        if api_response:
            usage = self.parse_response(api_response)
            if usage and usage.total_tokens > 0:
                return usage.total_tokens
        
        # 否则使用本地计算
        total_tokens = 0
        
        for message in messages:
            # 计算消息内容的token
            content_tokens = self.count_tokens(
                extract_content_as_string(message.content)
            )
            if content_tokens is not None:
                total_tokens += content_tokens
            
            # 添加格式化的token（每个消息约4个token）
            total_tokens += 4
        
        # 添加回复的token（约3个token）
        total_tokens += 3
        
        return total_tokens
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Gemini API响应中的token使用信息
        
        Args:
            response: Gemini API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            metadata = response.get("usageMetadata", {})
            if not metadata:
                logger.warning("Gemini响应中未找到usageMetadata信息")
                return None
                
            token_usage = TokenUsage(
                prompt_tokens=metadata.get("promptTokenCount", 0),
                completion_tokens=metadata.get("candidatesTokenCount", 0),
                total_tokens=metadata.get("totalTokenCount", 0),
                source="api",
                additional_info={
                    "model": response.get("model"),
                    "thoughts_tokens": metadata.get("thoughtsTokenCount", 0),
                    "cached_tokens": metadata.get("cachedContentTokenCount", 0),
                    "candidates": response.get("candidates"),
                    "prompt_feedback": response.get("promptFeedback")
                }
            )
            
            # 保存最后一次的使用情况
            self._last_usage = token_usage
            
            return token_usage
        except Exception as e:
            logger.error(f"解析Gemini响应失败: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        base_info = super().get_model_info()
        return {
            **base_info,
            "encoding": "estimated",
            "supports_tiktoken": False,
        }
    
    def update_from_api_response(self, response: Dict[str, Any], 
                                context: Optional[str] = None) -> bool:
        """
        从API响应更新token信息
        
        Args:
            response: API响应数据
            context: 上下文文本（可选）
            
        Returns:
            bool: 是否成功更新
        """
        usage = self.parse_response(response)
        return usage is not None
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """
        获取最近的API使用情况
        
        Returns:
            Optional[TokenUsage]: 最近的API使用情况
        """
        return self._last_usage
    
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        return self._last_usage is not None
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        # 检查是否有Gemini特有的字段
        return (
            "usageMetadata" in response and
            isinstance(response.get("usageMetadata"), dict) and
            any(key in response.get("usageMetadata", {}) for key in [
                "promptTokenCount", "candidatesTokenCount", "totalTokenCount"
            ])
        )
    
    def get_model_pricing(self) -> Optional[Dict[str, float]]:
        """
        获取模型定价信息
        
        Returns:
            Optional[Dict[str, float]]: 定价信息，格式为 {"prompt": 0.0005, "completion": 0.0015}
        """
        # Gemini模型定价
        pricing_map = {
            "gemini-pro": {"prompt": 0.0005, "completion": 0.0015},
            "gemini-pro-vision": {"prompt": 0.00025, "completion": 0.0005},
            "gemini-1.5-pro": {"prompt": 0.0025, "completion": 0.0075},
            "gemini-1.5-flash": {"prompt": 0.000075, "completion": 0.00015},
        }
        
        return pricing_map.get(self.model_name)