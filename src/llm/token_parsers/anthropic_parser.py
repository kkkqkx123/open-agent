"""Anthropic API响应解析器"""

import logging
from typing import Dict, Any, Optional

from .base import ITokenParser, TokenUsage

logger = logging.getLogger(__name__)


class AnthropicParser(ITokenParser):
    """Anthropic API响应解析器"""
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Anthropic API响应中的token使用信息
        
        Args:
            response: Anthropic API响应数据
            
        Returns:
            TokenUsage: 解析出的token使用信息，如果解析失败返回None
        """
        try:
            usage = response.get("usage", {})
            if not usage:
                logger.warning("Anthropic响应中未找到usage信息")
                return None
                
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            
            return TokenUsage(
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
        except Exception as e:
            logger.error(f"解析Anthropic响应失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "anthropic"
    
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