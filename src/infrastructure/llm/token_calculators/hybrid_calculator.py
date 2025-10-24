"""混合Token计算器"""

import logging
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage  # type: ignore

from .base import ITokenCalculator
from ..token_parsers.base import TokenUsage
from .local_calculator import LocalTokenCalculator
from .api_calculator import ApiTokenCalculator
from .conversation_tracker import ConversationTokenTracker

logger = logging.getLogger(__name__)


class HybridTokenCalculator(ITokenCalculator):
    """混合Token计算器，实现降级策略"""
    
    def __init__(self, model_name: str = "gpt-3.5-turbo", provider: str = "openai", 
                 prefer_api: bool = True, enable_degradation: bool = True, 
                 supports_token_caching: bool = True, track_conversation: bool = False):
        """
        初始化混合Token计算器
        
        Args:
            model_name: 模型名称
            provider: 提供商名称
            prefer_api: 是否优先使用API计算器
            enable_degradation: 是否启用降级策略
            supports_token_caching: 是否支持token缓存
            track_conversation: 是否跟踪对话历史
        """
        self.model_name = model_name
        self.provider = provider
        self.prefer_api = prefer_api
        self.enable_degradation = enable_degradation
        self.supports_token_caching = supports_token_caching
        self.track_conversation = track_conversation
        
        # 初始化本地和API计算器
        self._local_calculator = LocalTokenCalculator(model_name, provider)
        self._api_calculator = ApiTokenCalculator(
            model_name, 
            provider, 
            supports_caching=supports_token_caching
        )
        
        # 初始化对话跟踪器
        self._conversation_tracker: Optional[ConversationTokenTracker] = None
        if track_conversation:
            self._conversation_tracker = ConversationTokenTracker(self)
        
        # 统计信息
        self._stats = {
            "local_count": 0,
            "api_count": 0,
            "fallback_count": 0,
            "degradation_count": 0
        }
    
    def count_tokens(self, text: str, api_response: Optional[Dict[str, Any]] = None) -> int:
        """
        计算文本的token数量，实现降级策略
        
        Args:
            text: 输入文本
            api_response: API响应数据（可选）
            
        Returns:
            int: token数量
        """
        if not self.prefer_api:
            # 优先使用本地计算器
            self._stats["local_count"] += 1
            
            # 如果启用了对话跟踪，添加消息到历史
            if self._conversation_tracker:
                from langchain_core.messages import HumanMessage
                message = HumanMessage(content=text)
                self._conversation_tracker.add_message(message, token_count=self._local_calculator.count_tokens(text))
            
            return self._local_calculator.count_tokens(text)
        
        # 优先使用API计算器
        if api_response and self.supports_token_caching:
            # 尝试从API响应解析token数
            api_usage = self._api_calculator.get_last_api_usage()
            if not api_usage:
                # 如果没有缓存的API使用数据，尝试从响应中解析
                self._api_calculator.update_from_api_response(api_response, text)
                api_usage = self._api_calculator.get_last_api_usage()
            
            if api_usage:
                # 计算本地估算值
                local_count = self._local_calculator.count_tokens(text)
                
                # 降级策略：如果API token数少于本地估算的1/4，使用本地计算
                if self.enable_degradation and api_usage.total_tokens < local_count / 4:
                    logger.warning(
                        f"API token count ({api_usage.total_tokens}) is less than 1/4 of "
                        f"local estimate ({local_count}), using local calculation"
                    )
                    self._stats["degradation_count"] += 1
                    self._stats["local_count"] += 1
                    
                    # 如果启用了对话跟踪，添加消息到历史
                    if self._conversation_tracker:
                        from langchain_core.messages import HumanMessage
                        message = HumanMessage(content=text)
                        self._conversation_tracker.add_message(message, token_count=local_count)
                    
                    return local_count
                
                # 使用API返回的token数
                self._stats["api_count"] += 1
                
                # 如果启用了对话跟踪，添加消息到历史
                if self._conversation_tracker:
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(content=text)
                    self._conversation_tracker.add_message(message, token_count=api_usage.total_tokens)
                
                return api_usage.total_tokens
        
        # 没有API响应或API解析失败，检查是否有缓存的API使用数据
        if self.supports_token_caching and self._api_calculator.is_api_usage_available():
            # 使用缓存的API数据
            api_usage = self._api_calculator.get_last_api_usage()
            if api_usage:
                # 计算本地估算值
                local_count = self._local_calculator.count_tokens(text)
                
                # 降级策略：如果API token数少于本地估算的1/4，使用本地计算
                if self.enable_degradation and api_usage.total_tokens < local_count / 4:
                    logger.warning(
                        f"API token count ({api_usage.total_tokens}) is less than 1/4 of "
                        f"local estimate ({local_count}), using local calculation"
                    )
                    self._stats["degradation_count"] += 1
                    self._stats["local_count"] += 1
                    
                    # 如果启用了对话跟踪，添加消息到历史
                    if self._conversation_tracker:
                        from langchain_core.messages import HumanMessage
                        message = HumanMessage(content=text)
                        self._conversation_tracker.add_message(message, token_count=local_count)
                    
                    return local_count
                
                # 使用API返回的token数
                self._stats["api_count"] += 1
                
                # 如果启用了对话跟踪，添加消息到历史
                if self._conversation_tracker:
                    from langchain_core.messages import HumanMessage
                    message = HumanMessage(content=text)
                    self._conversation_tracker.add_message(message, token_count=api_usage.total_tokens)
                
                return api_usage.total_tokens
        
        # 降级到本地计算器
        self._stats["fallback_count"] += 1
        self._stats["local_count"] += 1
        
        # 计算本地token数
        local_count = self._local_calculator.count_tokens(text)
        
        # 如果启用了对话跟踪，添加消息到历史
        if self._conversation_tracker:
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=text)
            self._conversation_tracker.add_message(message, token_count=local_count)
        
        return local_count
    
    def count_messages_tokens(self, messages: List[BaseMessage], 
                             api_response: Optional[Dict[str, Any]] = None) -> int:
        """
        计算消息列表的token数量，实现降级策略
        
        Args:
            messages: 消息列表
            api_response: API响应数据（可选）
            
        Returns:
            int: token数量
        """
        if not self.prefer_api:
            # 优先使用本地计算器
            self._stats["local_count"] += 1
            
            # 计算本地token数
            local_count = self._local_calculator.count_messages_tokens(messages)
            
            # 如果启用了对话跟踪，添加消息到历史
            if self._conversation_tracker:
                self._conversation_tracker.add_messages(messages, token_count=local_count)
            
            return local_count
        
        # 优先使用API计算器
        if api_response and self.supports_token_caching:
            # 尝试从API响应解析token数
            api_usage = self._api_calculator.get_last_api_usage()
            if not api_usage:
                # 如果没有缓存的API使用数据，尝试从响应中解析
                # 将消息列表转换为文本作为上下文
                context = self._messages_to_text(messages)
                self._api_calculator.update_from_api_response(api_response, context)
                api_usage = self._api_calculator.get_last_api_usage()
            
            if api_usage:
                # 计算本地估算值
                local_count = self._local_calculator.count_messages_tokens(messages)
                
                # 降级策略：如果API token数少于本地估算的1/4，使用本地计算
                if self.enable_degradation and api_usage.total_tokens < local_count / 4:
                    logger.warning(
                        f"API token count ({api_usage.total_tokens}) is less than 1/4 of "
                        f"local estimate ({local_count}), using local calculation"
                    )
                    self._stats["degradation_count"] += 1
                    self._stats["local_count"] += 1
                    
                    # 如果启用了对话跟踪，添加消息到历史
                    if self._conversation_tracker:
                        self._conversation_tracker.add_messages(messages, token_count=local_count)
                    
                    return local_count
                
                # 使用API返回的token数
                self._stats["api_count"] += 1
                
                # 如果启用了对话跟踪，添加消息到历史
                if self._conversation_tracker:
                    self._conversation_tracker.add_messages(messages, token_count=api_usage.total_tokens)
                
                return api_usage.total_tokens
        
        # 没有API响应或API解析失败，检查是否有缓存的API使用数据
        if self.supports_token_caching and self._api_calculator.is_api_usage_available():
            # 使用缓存的API数据
            api_usage = self._api_calculator.get_last_api_usage()
            if api_usage:
                # 计算本地估算值
                local_count = self._local_calculator.count_messages_tokens(messages)
                
                # 降级策略：如果API token数少于本地估算的1/4，使用本地计算
                if self.enable_degradation and api_usage.total_tokens < local_count / 4:
                    logger.warning(
                        f"API token count ({api_usage.total_tokens}) is less than 1/4 of "
                        f"local estimate ({local_count}), using local calculation"
                    )
                    self._stats["degradation_count"] += 1
                    self._stats["local_count"] += 1
                    
                    # 如果启用了对话跟踪，添加消息到历史
                    if self._conversation_tracker:
                        self._conversation_tracker.add_messages(messages, token_count=local_count)
                    
                    return local_count
                
                # 使用API返回的token数
                self._stats["api_count"] += 1
                
                # 如果启用了对话跟踪，添加消息到历史
                if self._conversation_tracker:
                    self._conversation_tracker.add_messages(messages, token_count=api_usage.total_tokens)
                
                return api_usage.total_tokens
        
        # 降级到本地计算器
        self._stats["fallback_count"] += 1
        self._stats["local_count"] += 1
        
        # 计算本地token数
        local_count = self._local_calculator.count_messages_tokens(messages)
        
        # 如果启用了对话跟踪，添加消息到历史
        if self._conversation_tracker:
            self._conversation_tracker.add_messages(messages, token_count=local_count)
        
        return local_count
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        local_info = self._local_calculator.get_model_info()
        api_info = self._api_calculator.get_model_info()
        
        info = {
            "model_name": self.model_name,
            "provider": self.provider,
            "calculator_type": "hybrid",
            "prefer_api": self.prefer_api,
            "enable_degradation": self.enable_degradation,
            "supports_token_caching": self.supports_token_caching,
            "track_conversation": self.track_conversation,
            "local_calculator": local_info,
            "api_calculator": api_info,
            "stats": self._stats,
            "api_available": self._api_calculator.is_api_usage_available()
        }
        
        # 如果启用了对话跟踪，添加对话统计信息
        if self._conversation_tracker:
            info["conversation_stats"] = self._conversation_tracker.get_stats()
        
        return info
    
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
        return self._api_calculator.update_from_api_response(response, context)
    
    def get_last_api_usage(self) -> Optional[TokenUsage]:
        """
        获取最近的API使用情况
        
        Returns:
            TokenUsage: 最近的API使用情况，如果没有则返回None
        """
        return self._api_calculator.get_last_api_usage()
    
    def is_api_usage_available(self) -> bool:
        """
        检查是否有可用的API使用数据
        
        Returns:
            bool: 是否有可用的API使用数据
        """
        return self._api_calculator.is_api_usage_available()
    
    def set_prefer_api(self, prefer_api: bool) -> None:
        """
        设置是否优先使用API计算器
        
        Args:
            prefer_api: 是否优先使用API计算器
        """
        self.prefer_api = prefer_api
        logger.debug(f"设置优先使用API计算器: {prefer_api}")
    
    def set_enable_degradation(self, enable_degradation: bool) -> None:
        """
        设置是否启用降级策略
        
        Args:
            enable_degradation: 是否启用降级策略
        """
        self.enable_degradation = enable_degradation
        logger.debug(f"设置启用降级策略: {enable_degradation}")
    
    def set_supports_token_caching(self, supports_token_caching: bool) -> None:
        """
        设置是否支持token缓存
        
        Args:
            supports_token_caching: 是否支持token缓存
        """
        self.supports_token_caching = supports_token_caching
        self._api_calculator.supports_caching = supports_token_caching
        logger.debug(f"设置支持token缓存: {supports_token_caching}")
    
    def set_track_conversation(self, track_conversation: bool) -> None:
        """
        设置是否跟踪对话历史
        
        Args:
            track_conversation: 是否跟踪对话历史
        """
        self.track_conversation = track_conversation
        if track_conversation and not self._conversation_tracker:
            self._conversation_tracker = ConversationTokenTracker(self)
            logger.debug("已启用对话跟踪")
        elif not track_conversation and self._conversation_tracker:
            self._conversation_tracker = None
            logger.debug("已禁用对话跟踪")
    
    def get_conversation_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取对话统计信息
        
        Returns:
            Optional[Dict[str, Any]]: 对话统计信息，如果未启用对话跟踪则返回None
        """
        if self._conversation_tracker:
            return self._conversation_tracker.get_stats()
        return None
    
    def get_conversation_tokens(self) -> Optional[int]:
        """
        获取对话的token总数
        
        Returns:
            Optional[int]]: 对话的token总数，如果未启用对话跟踪则返回None
        """
        if self._conversation_tracker:
            return self._conversation_tracker.get_conversation_tokens()
        return None
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        if self._conversation_tracker:
            self._conversation_tracker.clear_history()
            logger.debug("已清空对话历史")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        total = self._stats["local_count"] + self._stats["api_count"]
        fallback_rate = (
            float(self._stats["fallback_count"]) / total * 100
            if total > 0 else 0.0
        )
        degradation_rate = (
            float(self._stats["degradation_count"]) / total * 100
            if total > 0 else 0.0
        )
        
        stats = {
            **self._stats,
            "total_requests": total,
            "fallback_rate_percent": fallback_rate,
            "degradation_rate_percent": degradation_rate,
            "api_available": self.is_api_usage_available(),
            "supports_token_caching": self.supports_token_caching,
            "track_conversation": self.track_conversation
        }
        
        # 如果启用了对话跟踪，添加对话统计信息
        if self._conversation_tracker:
            conversation_stats = self._conversation_tracker.get_stats()
            stats["conversation_stats"] = conversation_stats  # type: ignore
        
        return stats
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "local_count": 0,
            "api_count": 0,
            "fallback_count": 0,
            "degradation_count": 0
        }
        self._api_calculator.reset_stats()
        
        # 重置对话统计信息
        if self._conversation_tracker:
            self._conversation_tracker.clear_history()
        
        logger.debug("已重置混合计算器统计信息")
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._api_calculator.clear_cache()
        logger.debug("已清空混合计算器缓存")
    
    def force_local_calculation(self, text: str) -> int:
        """
        强制使用本地计算器计算token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        self._stats["local_count"] += 1
        
        # 计算本地token数
        local_count = self._local_calculator.count_tokens(text)
        
        # 如果启用了对话跟踪，添加消息到历史
        if self._conversation_tracker:
            from langchain_core.messages import HumanMessage
            message = HumanMessage(content=text)
            self._conversation_tracker.add_message(message, token_count=local_count)
        
        return local_count
    
    def force_api_calculation(self, text: str) -> int:
        """
        强制使用API计算器计算token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        if self._api_calculator.is_api_usage_available():
            self._stats["api_count"] += 1
            
            # 使用API返回的token数
            api_count = self._api_calculator.count_tokens(text)
            
            # 如果启用了对话跟踪，添加消息到历史
            if self._conversation_tracker:
                from langchain_core.messages import HumanMessage
                message = HumanMessage(content=text)
                self._conversation_tracker.add_message(message, token_count=api_count)
            
            return api_count
        else:
            logger.warning("API计算器不可用，降级到本地计算器")
            self._stats["fallback_count"] += 1
            self._stats["local_count"] += 1
            
            # 计算本地token数
            local_count = self._local_calculator.count_tokens(text)
            
            # 如果启用了对话跟踪，添加消息到历史
            if self._conversation_tracker:
                from langchain_core.messages import HumanMessage
                message = HumanMessage(content=text)
                self._conversation_tracker.add_message(message, token_count=local_count)
            
            return local_count
    
    def _messages_to_text(self, messages: List[BaseMessage]) -> str:
        """
        将消息列表转换为文本
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 转换后的文本
        """
        from ..utils.encoding_protocol import extract_content_as_string
        
        texts = []
        for message in messages:
            content = extract_content_as_string(message.content)
            texts.append(f"{message.type}:{content}")
        return "\n".join(texts)