"""OpenAI Token处理器

整合了OpenAI的Token计算和解析功能。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage  # type: ignore

from .base_processor import ITokenProcessor, TokenUsage
from .base_implementation import BaseTokenProcessor
from ..utils.encoding_protocol import extract_content_as_string, EncodingProtocol, TiktokenEncoding

logger = get_logger(__name__)


class OpenAITokenProcessor(BaseTokenProcessor):
    """OpenAI Token处理器
    
    整合了OpenAI的Token计算和解析功能。
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo"):
        """
        初始化OpenAI Token处理器
        
        Args:
            model_name: 模型名称
        """
        super().__init__(model_name, "openai")
        self._encoding: Optional[EncodingProtocol] = None
        self._load_encoding()
    
    def _load_encoding(self) -> None:
        """加载编码器"""
        try:
            import tiktoken
            
            # 尝试获取模型特定的编码器
            try:
                encoding = tiktoken.encoding_for_model(self.model_name)
                self._encoding = TiktokenEncoding(encoding)
            except KeyError:
                # 如果模型没有特定编码器，使用默认的
                encoding = tiktoken.get_encoding("cl100k_base")
                self._encoding = TiktokenEncoding(encoding)
                
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
            Optional[int]: token数量
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
        if self._encoding:
            return self._count_messages_tokens_with_encoding(list(messages))
        else:
            return self._count_messages_tokens_estimation(list(messages))
    
    def _count_messages_tokens_with_encoding(self, messages: list[BaseMessage]) -> int:
        """使用编码器计算消息格式的token数量"""
        if not self._encoding:
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
    
    def _count_messages_tokens_estimation(self, messages: list[BaseMessage]) -> int:
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
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析OpenAI API响应中的token使用信息
        
        Args:
            response: OpenAI API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            usage = response.get("usage", {})
            if not usage:
                logger.warning("OpenAI响应中未找到usage信息")
                return None
                
            token_usage = TokenUsage(
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
            
            # 保存最后一次的使用情况
            self._last_usage = token_usage
            
            return token_usage
        except Exception as e:
            logger.error(f"解析OpenAI响应失败: {e}")
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
        # 检查是否有OpenAI特有的字段
        return (
            "usage" in response and
            isinstance(response.get("usage"), dict) and
            any(key in response.get("usage", {}) for key in ["prompt_tokens", "completion_tokens", "total_tokens"])
        )
    
    def get_model_pricing(self) -> Optional[Dict[str, float]]:
        """
        获取模型定价信息
        
        Returns:
            Optional[Dict[str, float]]: 定价信息，格式为 {"prompt": 0.001, "completion": 0.002}
        """
        # 这里可以实现获取模型定价的逻辑
        # 可以从配置文件或API获取
        pricing_map = {
            "gpt-3.5-turbo": {"prompt": 0.0005, "completion": 0.0015},
            "gpt-4": {"prompt": 0.03, "completion": 0.06},
            "gpt-4-turbo": {"prompt": 0.01, "completion": 0.03},
            "gpt-4o": {"prompt": 0.005, "completion": 0.015},
        }
        
        return pricing_map.get(self.model_name)