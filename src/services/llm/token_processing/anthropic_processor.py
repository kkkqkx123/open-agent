"""Anthropic Token处理器

整合了Anthropic的Token计算和解析功能。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage

from .base_processor import BaseTokenProcessor
from .token_types import TokenUsage
from ..utils.encoding_protocol import TiktokenEncoding
from src.interfaces.llm.encoding import EncodingProtocol

logger = get_logger(__name__)


class AnthropicTokenProcessor(BaseTokenProcessor):
    """Anthropic Token处理器
    
    整合了Anthropic的Token计算和解析功能。
    """
    
    def __init__(self, model_name: str = "claude-3-sonnet-20240229"):
        """
        初始化Anthropic Token处理器
        
        Args:
            model_name: 模型名称
        """
        super().__init__(model_name, "anthropic")
        self._encoding: Optional[EncodingProtocol] = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载tiktoken编码器"""
        try:
            import tiktoken
            
            # Anthropic模型使用cl100k_base编码器（与GPT-4相同）
            # 这是目前最接近Claude tokenization的公开编码器
            encoding = tiktoken.get_encoding("cl100k_base")
            self._encoding = TiktokenEncoding(encoding)
            
            logger.info(f"Anthropic处理器使用tiktoken编码器: {self._encoding.name}")
                
        except ImportError:
            # 如果没有安装tiktoken，抛出异常而不是降级到除4估算
            raise ImportError("tiktoken is required for Anthropic token processing. Please install it with: pip install tiktoken")
    
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量
        """
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            # 如果编码器不可用，返回None而不是使用除4估算
            logger.warning("Encoding not available, cannot count tokens")
            return None
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Anthropic API响应中的token使用信息
        
        Args:
            response: Anthropic API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            usage = response.get("usage", {})
            if not usage:
                logger.warning("Anthropic响应中未找到usage信息")
                return None
                
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            
            token_usage = TokenUsage(
                prompt_tokens=input_tokens,
                completion_tokens=output_tokens,
                total_tokens=input_tokens + output_tokens,
                source="api",
                additional_info={
                    "model": response.get("model"),
                    "id": response.get("id"),
                    "type": response.get("type"),
                    "role": response.get("role"),
                    "stop_reason": response.get("stop_reason"),
                    "stop_sequence": response.get("stop_sequence"),
                    "cache_creation_tokens": usage.get("cache_creation_input_tokens", 0),
                    "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
                    "cache_creation_input_tokens": usage.get("cache_creation_input_tokens", 0),
                    "cache_read_input_tokens": usage.get("cache_read_input_tokens", 0)
                }
            )
            
            # 保存最后一次的使用情况
            self._last_usage = token_usage
            
            return token_usage
        except Exception as e:
            logger.error(f"解析Anthropic响应失败: {e}")
            return None
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        base_info = super().get_model_info()
        encoding_name = "estimated"
        if self._encoding:
            encoding_name = getattr(self._encoding, 'name', 'tiktoken')
        
        return {
            **base_info,
            "encoding": encoding_name,
            "supports_tiktoken": self._encoding is not None,
        }
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        # 检查是否有Anthropic特有的字段
        return (
            "usage" in response and
            isinstance(response.get("usage"), dict) and
            any(key in response.get("usage", {}) for key in ["input_tokens", "output_tokens"])
        ) or (
            # 检查是否有Anthropic特有的响应结构
            "type" in response and response.get("type") == "message"
        )
    
    def get_model_pricing(self) -> Optional[Dict[str, float]]:
        """
        获取模型定价信息
        
        Returns:
            Optional[Dict[str, float]]: 定价信息，格式为 {"prompt": 0.003, "completion": 0.015}
        """
        # Anthropic模型定价
        pricing_map = {
            "claude-3-haiku-20240307": {"prompt": 0.00025, "completion": 0.00125},
            "claude-3-sonnet-20240229": {"prompt": 0.003, "completion": 0.015},
            "claude-3-opus-20240229": {"prompt": 0.015, "completion": 0.075},
            "claude-3-5-sonnet-20240620": {"prompt": 0.003, "completion": 0.015},
        }
        
        return pricing_map.get(self.model_name)