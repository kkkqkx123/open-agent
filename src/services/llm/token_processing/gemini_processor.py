"""Gemini Token处理器

整合了Gemini的Token计算和解析功能。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage

from .base_processor import BaseTokenProcessor
from .token_types import TokenUsage
from ..utils.encoding_protocol import TiktokenEncoding
from src.interfaces.llm.encoding import EncodingProtocol

logger = get_logger(__name__)


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
        self._encoding: Optional[EncodingProtocol] = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载tiktoken编码器"""
        try:
            import tiktoken
            
            # Gemini模型使用cl100k_base编码器（与GPT-4相同）
            # 这是目前最接近Gemini tokenization的公开编码器
            encoding = tiktoken.get_encoding("cl100k_base")
            self._encoding = TiktokenEncoding(encoding)
            
            logger.info(f"Gemini处理器使用tiktoken编码器: {self._encoding.name}")
                
        except ImportError:
            # 如果没有安装tiktoken，抛出异常而不是降级到除4估算
            raise ImportError("tiktoken is required for Gemini token processing. Please install it with: pip install tiktoken")
    
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