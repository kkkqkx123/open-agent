"""本地Token计算器"""

from src.services.logger import get_logger
from typing import Dict, Any, List, Optional, Sequence

from langchain_core.messages import BaseMessage  # type: ignore

from .token_types import TokenUsage
from ..utils.encoding_protocol import extract_content_as_string

logger = get_logger(__name__)


class LocalTokenCalculator:
    """本地Token计算器，有tiktoken时统一使用tiktoken计算，否则采用除4估算"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", provider: str = "openai"):
        """
        初始化本地Token计算器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
        """
        self.model_name = model_name
        self.provider = provider
        self._encoding: Optional[Any] = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载编码器"""
        try:
            import tiktoken
            
            # 尝试获取模型特定的编码器
            try:
                self._encoding = tiktoken.encoding_for_model(self.model_name)
            except KeyError:
                # 如果模型没有特定编码器，使用默认的
                self._encoding = tiktoken.get_encoding("cl100k_base")
                
            logger.info(f"使用tiktoken编码器: {self._encoding.name}")
                
        except ImportError:
            # 如果没有安装tiktoken，使用简单的估算
            self._encoding = None
            logger.warning("tiktoken not available, falling back to estimation (len(text) // 4)")
    
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量，本地计算器总是能返回结果
        """
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            # 简单估算：大约4个字符=1个token
            return len(text) // 4
    
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            Optional[int]: token数量，本地计算器总是能返回结果
        """
        if self._encoding:
            return self._count_messages_tokens_with_encoding(list(messages))
        else:
            return self._count_messages_tokens_estimation(list(messages))
    
    def _count_messages_tokens_with_encoding(self, messages: List[BaseMessage]) -> int:
        """使用编码器计算消息格式的token数量"""
        if not self._encoding:
            # 如果编码器不可用，回退到估算方法
            return self._count_messages_tokens_estimation(messages)
            
        total_tokens = 0
        
        # 每条消息的开销
        tokens_per_message = 3
        tokens_per_name = 1
        
        for message in messages:
            # 计算消息内容的token
            total_tokens += tokens_per_message
            total_tokens += len(
                self._encoding.encode(extract_content_as_string(message.content))
            )
            
            # 如果有名称，添加名称的token
            if hasattr(message, "name") and message.name:
                total_tokens += tokens_per_name + len(
                    self._encoding.encode(message.name)
                )
        
        # 添加回复的token
        total_tokens += 3
        
        return total_tokens
    
    def _count_messages_tokens_estimation(self, messages: List[BaseMessage]) -> int:
        """使用估算方法计算消息格式的token数量"""
        total_tokens = 0
        
        for message in messages:
            # 每条消息内容的token
            content_tokens = self.count_tokens(
                extract_content_as_string(message.content)
            )
            if content_tokens is not None:
                total_tokens += content_tokens
            
            # 添加格式化的token（每个消息4个token）
            total_tokens += 4
        
        # 添加回复的token（3个token）
        total_tokens += 3
        
        return total_tokens
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        encoding_name = "estimated"
        if self._encoding:
            encoding_name = getattr(self._encoding, 'name', 'tiktoken')
        
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "encoding": encoding_name,
            "supports_tiktoken": self._encoding is not None,
            "calculator_type": "local"
        }