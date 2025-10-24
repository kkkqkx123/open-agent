"""OpenAI API响应解析器"""

import logging
from typing import Dict, Any, Optional

from .base import ITokenParser, TokenUsage

logger = logging.getLogger(__name__)


class OpenAIParser(ITokenParser):
    """OpenAI API响应解析器"""
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析OpenAI API响应中的token使用信息
        
        Args:
            response: OpenAI API响应数据
            
        Returns:
            TokenUsage: 解析出的token使用信息，如果解析失败返回None
        """
        try:
            usage = response.get("usage", {})
            if not usage:
                logger.warning("OpenAI响应中未找到usage信息")
                return None
                
            return TokenUsage(
                prompt_tokens=usage.get("prompt_tokens", 0),
                completion_tokens=usage.get("completion_tokens", 0),
                total_tokens=usage.get("total_tokens", 0),
                source="api",
                additional_info={
                    "model": response.get("model"),
                    "response_id": response.get("id"),
                    "object": response.get("object"),
                    "created": response.get("created"),
                    "system_fingerprint": response.get("system_fingerprint")
                }
            )
        except Exception as e:
            logger.error(f"解析OpenAI响应失败: {e}")
            return None
    
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        return "openai"
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        # 检查是否有OpenAI特有的字段
        return (
            "usage" in response and
            isinstance(response.get("usage"), dict) and
            any(key in response.get("usage", {}) for key in ["prompt_tokens", "completion_tokens", "total_tokens"])
        )