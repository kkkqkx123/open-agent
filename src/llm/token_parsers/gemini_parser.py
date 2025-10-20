"""Gemini API响应解析器"""

import logging
from typing import Dict, Any, Optional

from .base import ITokenParser, TokenUsage

logger = logging.getLogger(__name__)


class GeminiParser(ITokenParser):
    """Gemini API响应解析器"""
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析Gemini API响应中的token使用信息
        
        Args:
            response: Gemini API响应数据
            
        Returns:
            TokenUsage: 解析出的token使用信息，如果解析失败返回None
        """
        try:
            metadata = response.get("usageMetadata", {})
            if not metadata:
                logger.warning("Gemini响应中未找到usageMetadata信息")
                return None
                
            return TokenUsage(
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
        except Exception as e:
            logger.error(f"解析Gemini响应失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "gemini"
    
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