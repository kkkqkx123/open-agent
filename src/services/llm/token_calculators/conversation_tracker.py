"""对话token跟踪器"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from langchain_core.messages import BaseMessage  # type: ignore

from .base import ITokenCalculator
from ..token_parsers.base import TokenUsage

logger = logging.getLogger(__name__)


class ConversationTokenTracker:
    """对话token跟踪器"""
    
    def __init__(self, token_counter: ITokenCalculator):
        """
        初始化对话token跟踪器
        
        Args:
            token_counter: Token计算器实例
        """
        self.token_counter = token_counter
        self.conversation_history: List[Dict[str, Any]] = []
        self.total_tokens_used = 0
        
        # 统计信息
        self._stats = {
            "total_messages": 0,
            "total_api_updates": 0,
            "total_local_calculations": 0
        }
    
    def add_message(self, message: BaseMessage, api_response: Optional[Dict[str, Any]] = None, 
                  token_count: Optional[int] = None) -> None:
        """
        添加消息到对话历史
        
        Args:
            message: 消息内容
            api_response: API响应数据（可选）
            token_count: 预先计算的token数（可选）
        """
        # 计算当前消息的token数
        if token_count is not None:
            # 使用预先计算的token数
            actual_token_count = token_count
            source = "precomputed"
        elif api_response:
            # 使用API返回的token数
            actual_token_count = self.token_counter.count_messages_tokens([message]) or 0
            source = "api"
            self._stats["total_api_updates"] += 1
        else:
            # 使用本地估算
            actual_token_count = self.token_counter.count_messages_tokens([message]) or 0
            source = "local"
            self._stats["total_local_calculations"] += 1
        
        # 记录消息和token数
        self.conversation_history.append({
            "message": message,
            "token_count": actual_token_count,
            "timestamp": datetime.now(),
            "source": source
        })
        
        self.total_tokens_used += actual_token_count
        self._stats["total_messages"] += 1
        
        logger.debug(f"添加消息到对话历史，token数: {actual_token_count}, 来源: {source}")
    
    def add_messages(self, messages: List[BaseMessage], api_response: Optional[Dict[str, Any]] = None,
                   token_count: Optional[int] = None) -> None:
        """
        添加多条消息到对话历史
        
        Args:
            messages: 消息列表
            api_response: API响应数据（可选）
            token_count: 预先计算的token数（可选）
        """
        if token_count is not None:
            # 如果有总的token数，平均分配给每条消息
            avg_token_count = token_count / len(messages) if messages else 0
            for message in messages:
                self.add_message(message, api_response, int(avg_token_count))
        else:
            # 逐条添加消息
            for message in messages:
                self.add_message(message, api_response)
    
    def get_conversation_tokens(self) -> int:
        """
        获取整个对话的token总数
        
        Returns:
            int: 对话的token总数
        """
        return self.total_tokens_used
    
    def get_recent_tokens(self, last_n: int = 10) -> int:
        """
        获取最近N条消息的token数
        
        Args:
            last_n: 最近的消息数量
            
        Returns:
            int: 最近N条消息的token数
        """
        recent_messages = self.conversation_history[-last_n:]
        return sum(msg["token_count"] for msg in recent_messages)
    
    def get_average_tokens_per_message(self) -> float:
        """
        获取平均每条消息的token数
        
        Returns:
            float: 平均每条消息的token数
        """
        if not self.conversation_history:
            return 0.0
        return self.total_tokens_used / len(self.conversation_history)
    
    def get_message_token_distribution(self) -> Dict[str, int]:
        """
        获取消息类型的token分布
        
        Returns:
            Dict[str, int]: 消息类型的token分布
        """
        distribution = {}
        for entry in self.conversation_history:
            message_type = entry["message"].type
            if message_type not in distribution:
                distribution[message_type] = 0
            distribution[message_type] += entry["token_count"]
        return distribution
    
    def get_source_distribution(self) -> Dict[str, int]:
        """
        获取token来源的分布
        
        Returns:
            Dict[str, int]: token来源的分布（api/local/precomputed）
        """
        distribution = {"api": 0, "local": 0, "precomputed": 0}
        for entry in self.conversation_history:
            source = entry["source"]
            if source in distribution:
                distribution[source] += entry["token_count"]
            else:
                distribution[source] = entry["token_count"]
        return distribution
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        获取对话历史
        
        Returns:
            List[Dict[str, Any]]: 对话历史记录
        """
        return self.conversation_history.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        source_distribution = self.get_source_distribution()
        total = sum(source_distribution.values())
        api_percentage = (
            source_distribution["api"] / total * 100 
            if total > 0 else 0
        )
        
        return {
            **self._stats,
            "total_tokens_used": self.total_tokens_used,
            "message_count": len(self.conversation_history),
            "average_tokens_per_message": self.get_average_tokens_per_message(),
            "source_distribution": source_distribution,
            "api_percentage": api_percentage
        }
    
    def clear_history(self) -> None:
        """清空对话历史"""
        self.conversation_history.clear()
        self.total_tokens_used = 0
        self._stats = {
            "total_messages": 0,
            "total_api_updates": 0,
            "total_local_calculations": 0
        }
        logger.debug("已清空对话历史")
    
    def trim_history(self, max_messages: int) -> None:
        """
        截断对话历史，保留最近的消息
        
        Args:
            max_messages: 保留的最大消息数量
        """
        if len(self.conversation_history) > max_messages:
            # 计算要删除的消息的token数
            removed_messages = self.conversation_history[:-max_messages]
            removed_tokens = sum(msg["token_count"] for msg in removed_messages)
            
            # 保留最近的消息
            self.conversation_history = self.conversation_history[-max_messages:]
            self.total_tokens_used -= removed_tokens
            
            # 更新统计信息
            self._stats["total_messages"] = len(self.conversation_history)
            
            logger.debug(f"已截断对话历史，保留最近 {max_messages} 条消息")
    
    def export_conversation_data(self) -> Dict[str, Any]:
        """
        导出对话数据
        
        Returns:
            Dict[str, Any]: 对话数据
        """
        return {
            "conversation_history": [
                {
                    "message_type": entry["message"].type,
                    "content": entry["message"].content,
                    "token_count": entry["token_count"],
                    "timestamp": entry["timestamp"].isoformat(),
                    "source": entry["source"]
                }
                for entry in self.conversation_history
            ],
            "total_tokens_used": self.total_tokens_used,
            "stats": self.get_stats()
        }