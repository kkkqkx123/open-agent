"""Token处理器基础接口和抽象类

整合了Token计算和解析功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Sequence
from datetime import datetime

from langchain_core.messages import BaseMessage

from .token_types import TokenUsage
from ..utils.encoding_protocol import TiktokenEncoding
from src.interfaces.llm.encoding import EncodingProtocol
from src.services.logger import get_logger

logger = get_logger(__name__)


class ITokenProcessor(ABC):
    """统一的Token处理器接口
    
    整合了Token计算和解析功能。
    """
    
    @abstractmethod
    def count_tokens(self, text: str) -> Optional[int]:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            api_response: API响应（可选，用于更准确的计算）
            
        Returns:
            Optional[int]: token数量，如果无法计算则返回None
        """
        pass
    
    @abstractmethod
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息，如果解析失败返回None
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        获取提供商名称
        
        Returns:
            str: 提供商名称
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        pass
    
    @abstractmethod
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        pass
    
    
    # 降级策略相关方法
    def supports_degradation(self) -> bool:
        """
        检查是否支持降级策略
        
        Returns:
            bool: 是否支持降级策略
        """
        return False
    
    def set_degradation_enabled(self, enabled: bool) -> None:
        """
        设置是否启用降级策略
        
        Args:
            enabled: 是否启用降级策略
        """
        pass
    
    def is_degradation_enabled(self) -> bool:
        """
        检查降级策略是否启用
        
        Returns:
            bool: 降级策略是否启用
        """
        return False
    
    # 统计功能
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {}
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass
    
    # 对话跟踪功能
    def supports_conversation_tracking(self) -> bool:
        """
        检查是否支持对话跟踪
        
        Returns:
            bool: 是否支持对话跟踪
        """
        return False
    
    def set_conversation_tracking_enabled(self, enabled: bool) -> None:
        """
        设置是否启用对话跟踪
        
        Args:
            enabled: 是否启用对话跟踪
        """
        pass
    
    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 对话统计信息，如果未启用则返回None
        """
        return None
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        pass
    
    # 通用方法
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
            Optional[TokenUsage]: 最近的API使用情况，如果没有则返回None
        """
        return getattr(self, '_last_usage', None)
    
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        return self.get_last_api_usage() is not None
    
    def calculate_usage_cost(self, usage: TokenUsage, model_pricing: Optional[Dict[str, float]] = None) -> Optional[float]:
        """
        计算Token使用成本
        
        Args:
            usage: Token使用情况
            model_pricing: 模型定价信息，格式为 {"prompt": 0.001, "completion": 0.002}
            
        Returns:
            Optional[float]: 成本，如果无法计算则返回None
        """
        if not model_pricing:
            return None
        
        try:
            prompt_cost = usage.prompt_tokens * model_pricing.get("prompt", 0)
            completion_cost = usage.completion_tokens * model_pricing.get("completion", 0)
            total_cost = prompt_cost + completion_cost
            return total_cost
        except Exception:
            return None
    
    def format_usage_summary(self, usage: TokenUsage) -> str:
        """
        格式化Token使用情况摘要
        
        Args:
            usage: Token使用情况
            
        Returns:
            str: 格式化的摘要字符串
        """
        return (
            f"Token使用情况 - "
            f"提示: {usage.prompt_tokens}, "
            f"完成: {usage.completion_tokens}, "
            f"总计: {usage.total_tokens} "
            f"(来源: {usage.source})"
        )


class BaseTokenProcessor(ITokenProcessor):
    """Token处理器基础实现类
    
    提供通用功能的默认实现。
    """
    
    def __init__(self, model_name: str, provider: str):
        """
        初始化基础Token处理器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
        """
        self.model_name = model_name
        self.provider = provider
        self._last_usage: Optional[TokenUsage] = None
        self._encoding: Optional[EncodingProtocol] = None
        self._load_fallback_encoding()
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "degradation_events": 0
        }
        
        # 降级功能
        self._degradation_enabled = False
        
        # 对话跟踪功能
        self._conversation_history: list[Dict[str, Any]] = []
        self._conversation_tracking_enabled = False
    
    def _load_fallback_encoding(self) -> None:
        """加载统一的tiktoken编码器"""
        try:
            import tiktoken
            
            # 使用cl100k_base作为统一的编码器
            encoding = tiktoken.get_encoding("cl100k_base")
            self._encoding = TiktokenEncoding(encoding)
                
        except ImportError:
            # 如果没有安装tiktoken，抛出异常而不是降级到除4估算
            raise ImportError("tiktoken is required for token processing. Please install it with: pip install tiktoken")

    
    # 降级策略相关方法
    def supports_degradation(self) -> bool:
        """支持降级策略"""
        return True
    
    def set_degradation_enabled(self, enabled: bool) -> None:
        """设置是否启用降级策略"""
        self._degradation_enabled = enabled
    
    def is_degradation_enabled(self) -> bool:
        """检查降级策略是否启用"""
        return self._degradation_enabled
    
    def _should_degrade(self, api_count: int, local_count: int, threshold: float = 0.25) -> bool:
        """
        判断是否应该降级
        
        Args:
            api_count: API计算的token数
            local_count: 本地计算的token数
            threshold: 降级阈值（API token数与本地token数的比例）
            
        Returns:
            bool: 是否应该降级
        """
        if not self._degradation_enabled:
            return False
        
        if api_count < local_count * threshold:
            self._stats["degradation_events"] += 1
            return True
        
        return False
    
    # 统计功能的默认实现
    def get_stats(self) -> Dict[str, Any]:
        """获取基础统计信息"""
        total = self._stats["total_requests"]
        success_rate = (
            self._stats["successful_calculations"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "success_rate_percent": success_rate,
            "model_name": self.model_name,
            "provider": self.provider,
            "supports_degradation": self.supports_degradation(),
            "supports_conversation_tracking": self.supports_conversation_tracking()
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_calculations": 0,
            "failed_calculations": 0,
            "degradation_events": 0
        }
    
    # 对话跟踪相关方法
    def supports_conversation_tracking(self) -> bool:
        """支持对话跟踪"""
        return True
    
    def set_conversation_tracking_enabled(self, enabled: bool) -> None:
        """设置是否启用对话跟踪"""
        self._conversation_tracking_enabled = enabled
        if not enabled:
            self._conversation_history.clear()
    
    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """获取对话统计信息"""
        if not self._conversation_tracking_enabled:
            return None
        
        total_tokens = sum(msg.get("token_count", 0) for msg in self._conversation_history)
        
        return {
            "total_messages": len(self._conversation_history),
            "total_tokens": total_tokens,
            "average_tokens_per_message": total_tokens / len(self._conversation_history) if self._conversation_history else 0,
        }
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._conversation_history.clear()
    
    def _add_message_to_history(self, message_type: str, content: str, token_count: Optional[int]) -> None:
        """添加消息到对话历史"""
        if not self._conversation_tracking_enabled:
            return
        
        self._conversation_history.append({
            "type": message_type,
            "content": content[:100] + "..." if len(content) > 100 else content,  # 只保存前100个字符
            "token_count": token_count,
            "timestamp": datetime.now().isoformat()
        })
    
    # 辅助方法
    def _update_stats_on_success(self) -> None:
        """更新成功统计"""
        self._stats["total_requests"] += 1
        self._stats["successful_calculations"] += 1
    
    def _update_stats_on_failure(self) -> None:
        """更新失败统计"""
        self._stats["total_requests"] += 1
        self._stats["failed_calculations"] += 1
    
    def get_provider_name(self) -> str:
        """获取提供商名称"""
        return self.provider
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取基础模型信息"""
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "processor_type": self.__class__.__name__,
            "supports_degradation": self.supports_degradation(),
            "supports_conversation_tracking": self.supports_conversation_tracking(),
            "stats": self.get_stats()
        }
    
    # 核心方法的默认实现
    def count_tokens(self, text: str) -> Optional[int]:
        """使用统一的tiktoken编码器"""
        if self._encoding:
            return len(self._encoding.encode(text))
        else:
            # 如果编码器不可用，返回None而不是使用除4估算
            logger.warning("Encoding not available, cannot count tokens")
            return None
    
    def count_messages_tokens(self, messages: Sequence[BaseMessage], api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """使用统一的tiktoken编码器"""
        # 如果有API响应，优先使用API响应中的token数量
        if api_response:
            usage = self.parse_response(api_response)
            if usage and usage.total_tokens > 0:
                return usage.total_tokens
        
        # 否则使用本地计算
        if self._encoding:
            return self._count_messages_tokens_with_encoding(list(messages))
        else:
            # 如果编码器不可用，返回None而不是使用除4估算
            logger.warning("Encoding not available, cannot count message tokens")
            return None
    
    def _count_messages_tokens_with_encoding(self, messages: list[BaseMessage]) -> int:
        """使用编码器计算消息格式的token数量。这是在计算格式信息，而非硬编码的消息计算"""
        if not self._encoding:
            return 0
            
        total_tokens = 0
        
        # 每条消息的开销
        tokens_per_message = 3
        tokens_per_name = 1
        
        for message in messages:
            # 计算消息内容的token
            total_tokens += tokens_per_message
            total_tokens += len(
                self._encoding.encode(self._extract_message_content(message))
            )
            
            # 如果有名称，添加名称的token
            if hasattr(message, "name") and message.name:
                total_tokens += tokens_per_name + len(
                    self._encoding.encode(message.name)
                )
        
        # 添加回复的token
        total_tokens += 3
        
        return total_tokens
    
    def _extract_message_content(self, message: BaseMessage) -> str:
        """提取消息内容"""
        from ..utils.encoding_protocol import extract_content_as_string
        return extract_content_as_string(message.content)
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """默认不支持解析响应"""
        return None
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """默认不支持任何响应"""
        return False