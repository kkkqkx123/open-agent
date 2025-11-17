"""混合Token处理器

整合了本地计算、API计算和降级策略的统一处理器。
"""

import logging
from typing import Dict, Any, Optional, Sequence

from langchain_core.messages import BaseMessage  # type: ignore

from .base_implementation import CachedTokenProcessor, DegradationTokenProcessor
from .token_types import TokenUsage
from ..utils.encoding_protocol import extract_content_as_string

logger = logging.getLogger(__name__)


class HybridTokenProcessor(CachedTokenProcessor, DegradationTokenProcessor):
    """混合Token处理器
    
    整合了本地计算、API计算、缓存和降级策略的完整实现。
    """
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", provider: str = "openai",
                 prefer_api: bool = True, enable_degradation: bool = True,
                 cache_size: int = 1000, enable_conversation_tracking: bool = False):
        """
        初始化混合Token处理器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            prefer_api: 是否优先使用API计算
            enable_degradation: 是否启用降级策略
            cache_size: 缓存大小
            enable_conversation_tracking: 是否启用对话跟踪
        """
        # 初始化缓存功能
        CachedTokenProcessor.__init__(self, model_name, provider, cache_size)
        # 初始化降级功能
        DegradationTokenProcessor.__init__(self, model_name, provider, enable_degradation)
        
        self.prefer_api = prefer_api
        self.enable_conversation_tracking = enable_conversation_tracking
        
        # 初始化对话跟踪器
        self._conversation_history: list[Dict[str, Any]] = []
        
        # 扩展统计信息
        self._stats.update({
            "local_calculations": 0,
            "api_calculations": 0,
            "hybrid_calculations": 0,
            "conversation_messages": 0
        })
    
    def count_tokens(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算文本的token数量，实现完整的降级策略
        
        Args:
            text: 输入文本
            api_response: API响应数据（可选）
            
        Returns:
            Optional[int]: token数量
        """
        try:
            self._stats["total_requests"] += 1
            
            # 如果优先使用本地计算
            if not self.prefer_api:
                return self._count_tokens_local(text)
            
            # 优先使用API计算
            return self._count_tokens_with_api_fallback(text, api_response)
            
        except Exception as e:
            logger.error(f"计算token数量失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def count_messages_tokens(self, messages: Sequence[BaseMessage], 
                            api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """
        计算消息列表的token数量，实现完整的降级策略
        
        Args:
            messages: 消息列表
            api_response: API响应数据（可选）
            
        Returns:
            Optional[int]: token数量
        """
        try:
            self._stats["total_requests"] += 1
            
            # 如果优先使用本地计算
            if not self.prefer_api:
                return self._count_messages_tokens_local(messages)
            
            # 优先使用API计算
            return self._count_messages_tokens_with_api_fallback(messages, api_response)
            
        except Exception as e:
            logger.error(f"计算消息token数量失败: {e}")
            self._update_stats_on_failure()
            return None
    
    def _count_tokens_local(self, text: str) -> Optional[int]:
        """使用本地计算器计算token数量"""
        self._stats["local_calculations"] += 1
        self._stats["successful_calculations"] += 1
        
        # 添加到对话历史
        if self.enable_conversation_tracking:
            self._add_message_to_history("human", text, None)
        
        # 这里应该调用具体的本地计算实现
        # 暂时返回估算值
        return len(text.split()) * 2  # 简单估算
    
    def _count_messages_tokens_local(self, messages: Sequence[BaseMessage]) -> Optional[int]:
        """使用本地计算器计算消息token数量"""
        self._stats["local_calculations"] += 1
        self._stats["successful_calculations"] += 1
        
        total_tokens = 0
        for message in messages:
            content = extract_content_as_string(message.content)
            tokens = len(content.split()) * 2  # 简单估算
            total_tokens += tokens
            
            # 添加到对话历史
            if self.enable_conversation_tracking:
                self._add_message_to_history(message.type, content, tokens)
        
        return total_tokens
    
    def _count_tokens_with_api_fallback(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """使用API计算并支持降级到本地计算"""
        # 尝试从API响应解析
        if api_response:
            api_usage = self.parse_response(api_response)
            if api_usage:
                local_count = self._count_tokens_local(text) or 0
                
                # 检查是否需要降级
                if self._should_degrade(api_usage.total_tokens, local_count):
                    return local_count
                
                # 使用API结果
                self._stats["api_calculations"] += 1
                self._stats["successful_calculations"] += 1
                
                # 添加到对话历史
                if self.enable_conversation_tracking:
                    self._add_message_to_history("human", text, api_usage.total_tokens)
                
                # 缓存结果
                cache_key = self._generate_cache_key(text)
                self._add_to_cache(cache_key, api_usage)
                
                return api_usage.total_tokens
        
        # 检查缓存
        cache_key = self._generate_cache_key(text)
        cached_usage = self._get_from_cache(cache_key)
        if cached_usage:
            self._stats["api_calculations"] += 1
            self._stats["successful_calculations"] += 1
            
            # 添加到对话历史
            if self.enable_conversation_tracking:
                self._add_message_to_history("human", text, cached_usage.total_tokens)
            
            return cached_usage.total_tokens
        
        # 降级到本地计算
        return self._count_tokens_local(text)
    
    def _count_messages_tokens_with_api_fallback(self, messages: Sequence[BaseMessage], 
                                               api_response: Optional[Dict[str, Any]] = None) -> Optional[int]:
        """使用API计算消息token并支持降级到本地计算"""
        # 尝试从API响应解析
        if api_response:
            api_usage = self.parse_response(api_response)
            if api_usage:
                local_count = self._count_messages_tokens_local(messages) or 0
                
                # 检查是否需要降级
                if self._should_degrade(api_usage.total_tokens, local_count):
                    return local_count
                
                # 使用API结果
                self._stats["api_calculations"] += 1
                self._stats["successful_calculations"] += 1
                
                # 添加到对话历史
                if self.enable_conversation_tracking:
                    content = self._messages_to_text(messages)
                    self._add_message_to_history("messages", content, api_usage.total_tokens)
                
                # 缓存结果
                cache_key = self._generate_cache_key(self._messages_to_text(messages))
                self._add_to_cache(cache_key, api_usage)
                
                return api_usage.total_tokens
        
        # 检查缓存
        cache_key = self._generate_cache_key(self._messages_to_text(messages))
        cached_usage = self._get_from_cache(cache_key)
        if cached_usage:
            self._stats["api_calculations"] += 1
            self._stats["successful_calculations"] += 1
            
            # 添加到对话历史
            if self.enable_conversation_tracking:
                content = self._messages_to_text(messages)
                self._add_message_to_history("messages", content, cached_usage.total_tokens)
            
            return cached_usage.total_tokens
        
        # 降级到本地计算
        return self._count_messages_tokens_local(messages)
    
    def parse_response(self, response: Dict[str, Any]) -> Optional[TokenUsage]:
        """
        解析API响应中的token使用信息
        
        Args:
            response: API响应数据
            
        Returns:
            Optional[TokenUsage]: 解析出的token使用信息
        """
        try:
            # 这里应该根据不同的provider实现具体的解析逻辑
            # 暂时返回一个示例实现
            if "usage" in response:
                usage_data = response["usage"]
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                    source="api"
                )
                self._last_usage = usage
                return usage
            
            return None
            
        except Exception as e:
            logger.error(f"解析API响应失败: {e}")
            return None
    
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
        try:
            usage = self.parse_response(response)
            if usage and context:
                # 缓存结果
                cache_key = self._generate_cache_key(context)
                self._add_to_cache(cache_key, usage)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"更新API响应失败: {e}")
            return False
    
    def is_supported_response(self, response: Dict[str, Any]) -> bool:
        """
        检查是否支持解析该响应
        
        Args:
            response: API响应数据
            
        Returns:
            bool: 是否支持解析
        """
        return "usage" in response
    
    # 对话跟踪功能
    def supports_conversation_tracking(self) -> bool:
        """支持对话跟踪"""
        return True
    
    def set_conversation_tracking_enabled(self, enabled: bool) -> None:
        """设置是否启用对话跟踪"""
        self.enable_conversation_tracking = enabled
        if not enabled:
            self._conversation_history.clear()
        logger.debug(f"设置对话跟踪: {enabled}")
    
    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """获取对话统计信息"""
        if not self.enable_conversation_tracking:
            return None
        
        total_tokens = sum(msg.get("token_count", 0) for msg in self._conversation_history)
        
        return {
            "total_messages": len(self._conversation_history),
            "total_tokens": total_tokens,
            "average_tokens_per_message": total_tokens / len(self._conversation_history) if self._conversation_history else 0,
            "message_types": self._get_message_type_stats()
        }
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._conversation_history.clear()
        self._stats["conversation_messages"] = 0
        logger.debug("已清空对话历史")
    
    def _add_message_to_history(self, message_type: str, content: str, token_count: Optional[int]) -> None:
        """添加消息到对话历史"""
        if not self.enable_conversation_tracking:
            return
        
        self._conversation_history.append({
            "type": message_type,
            "content": content[:100] + "..." if len(content) > 100 else content,  # 只保存前100个字符
            "token_count": token_count,
            "timestamp": self._get_current_timestamp()
        })
        
        self._stats["conversation_messages"] += 1
    
    def _get_message_type_stats(self) -> Dict[str, int]:
        """获取消息类型统计"""
        type_stats = {}
        for msg in self._conversation_history:
            msg_type = msg.get("type", "unknown")
            type_stats[msg_type] = type_stats.get(msg_type, 0) + 1
        return type_stats
    
    def _messages_to_text(self, messages: Sequence[BaseMessage]) -> str:
        """将消息列表转换为文本"""
        texts = []
        for message in messages:
            content = extract_content_as_string(message.content)
            texts.append(f"{message.type}:{content}")
        return "\n".join(texts)
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取完整的模型信息"""
        base_info = super().get_model_info()
        base_info.update({
            "processor_type": "HybridTokenProcessor",
            "prefer_api": self.prefer_api,
            "enable_conversation_tracking": self.enable_conversation_tracking,
            "conversation_stats": self.get_conversation_stats(),
            "cache_stats": self.get_cache_stats()
        })
        return base_info
    
    def set_prefer_api(self, prefer_api: bool) -> None:
        """设置是否优先使用API计算"""
        self.prefer_api = prefer_api
        logger.debug(f"设置优先使用API计算: {prefer_api}")
    
    def force_local_calculation(self, text: str) -> Optional[int]:
        """强制使用本地计算"""
        return self._count_tokens_local(text)
    
    def force_api_calculation(self, text: str) -> Optional[int]:
        """强制使用API计算"""
        cache_key = self._generate_cache_key(text)
        cached_usage = self._get_from_cache(cache_key)
        if cached_usage:
            self._stats["api_calculations"] += 1
            self._stats["successful_calculations"] += 1
            return cached_usage.total_tokens
        
        # 如果没有缓存，返回None表示无法计算
        logger.warning("API计算器不可用，没有缓存数据")
        return None