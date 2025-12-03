"""消息工具函数

提供消息处理的实用工具函数。
"""

from typing import Dict, Any, List, Optional, Union, Iterator, Callable
from datetime import datetime
import json
import hashlib

from ...interfaces.messages import IBaseMessage
from .types import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    is_human_message, is_ai_message, is_system_message, is_tool_message
)


class MessageUtils:
    """消息工具类
    
    提供各种消息处理的实用方法。
    """
    
    @staticmethod
    def extract_text_from_messages(messages: List[IBaseMessage]) -> str:
        """从消息列表中提取纯文本内容
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 合并的文本内容
        """
        text_parts = []
        for message in messages:
            if hasattr(message, 'get_text_content'):
                text_parts.append(message.get_text_content())
            else:
                text_parts.append(str(message.content))
        
        return "\n".join(text_parts)
    
    @staticmethod
    def filter_messages_by_type(messages: List[IBaseMessage], message_type: str) -> List[IBaseMessage]:
        """按类型过滤消息
        
        Args:
            messages: 消息列表
            message_type: 消息类型 ("human", "ai", "system", "tool")
            
        Returns:
            List[IBaseMessage]: 过滤后的消息列表
        """
        filtered = []
        for message in messages:
            if message.type == message_type:
                filtered.append(message)
        return filtered
    
    @staticmethod
    def filter_human_messages(messages: List[IBaseMessage]) -> List[IBaseMessage]:
        """过滤人类消息"""
        return [msg for msg in messages if is_human_message(msg)]
    
    @staticmethod
    def filter_ai_messages(messages: List[IBaseMessage]) -> List[IBaseMessage]:
        """过滤AI消息"""
        return [msg for msg in messages if is_ai_message(msg)]
    
    @staticmethod
    def filter_system_messages(messages: List[IBaseMessage]) -> List[IBaseMessage]:
        """过滤系统消息"""
        return [msg for msg in messages if is_system_message(msg)]
    
    @staticmethod
    def filter_tool_messages(messages: List[IBaseMessage]) -> List[IBaseMessage]:
        """过滤工具消息"""
        return [msg for msg in messages if is_tool_message(msg)]
    
    @staticmethod
    def get_last_message_of_type(messages: List[IBaseMessage], message_type: str) -> Optional[IBaseMessage]:
        """获取指定类型的最后一条消息
        
        Args:
            messages: 消息列表
            message_type: 消息类型
            
        Returns:
            Optional[IBaseMessage]: 最后一条消息，如果不存在则返回None
        """
        for message in reversed(messages):
            if message.type == message_type:
                return message
        return None
    
    @staticmethod
    def get_last_human_message(messages: List[IBaseMessage]) -> Optional[IBaseMessage]:
        """获取最后一条人类消息"""
        return MessageUtils.get_last_message_of_type(messages, "human")
    
    @staticmethod
    def get_last_ai_message(messages: List[IBaseMessage]) -> Optional[IBaseMessage]:
        """获取最后一条AI消息"""
        return MessageUtils.get_last_message_of_type(messages, "ai")
    
    @staticmethod
    def count_messages_by_type(messages: List[IBaseMessage]) -> Dict[str, int]:
        """统计各类型消息数量
        
        Args:
            messages: 消息列表
            
        Returns:
            Dict[str, int]: 类型到数量的映射
        """
        counts = {"human": 0, "ai": 0, "system": 0, "tool": 0}
        for message in messages:
            msg_type = message.type
            if msg_type in counts:
                counts[msg_type] += 1
        return counts
    
    @staticmethod
    def get_conversation_pairs(messages: List[IBaseMessage]) -> List[tuple[IBaseMessage, IBaseMessage]]:
        """获取对话对（人类消息和AI消息的配对）
        
        Args:
            messages: 消息列表
            
        Returns:
            List[tuple[IBaseMessage, IBaseMessage]]: 对话对列表
        """
        pairs = []
        i = 0
        n = len(messages)
        
        while i < n:
            # 查找人类消息
            human_msg = None
            while i < n and not is_human_message(messages[i]):
                i += 1
            
            if i >= n:
                break
            
            human_msg = messages[i]
            i += 1
            
            # 查找下一条AI消息
            ai_msg = None
            while i < n and not is_ai_message(messages[i]):
                i += 1
            
            if i < n:
                ai_msg = messages[i]
                i += 1
            
            if human_msg and ai_msg:
                pairs.append((human_msg, ai_msg))
        
        return pairs
    
    @staticmethod
    def truncate_messages(messages: List[IBaseMessage], max_tokens: int, 
                         tokenizer: Optional[Callable[[str], int]] = None) -> List[IBaseMessage]:
        """截断消息列表以适应token限制
        
        Args:
            messages: 消息列表
            max_tokens: 最大token数
            tokenizer: token计数函数，默认按字符计算
            
        Returns:
            List[IBaseMessage]: 截断后的消息列表
        """
        if tokenizer is None:
            # 默认按字符数计算token
            tokenizer = lambda text: len(text)
        
        # 保留系统消息
        system_messages = MessageUtils.filter_system_messages(messages)
        other_messages = [msg for msg in messages if not is_system_message(msg)]
        
        # 从最新消息开始倒序添加
        truncated = []
        current_tokens = 0
        
        # 添加系统消息的token数
        for msg in system_messages:
            current_tokens += tokenizer(msg.get_text_content())
        
        # 倒序添加其他消息
        for msg in reversed(other_messages):
            msg_tokens = tokenizer(msg.get_text_content())
            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, msg)
                current_tokens += msg_tokens
            else:
                break
        
        # 系统消息放在最前面
        return system_messages + truncated
    
    @staticmethod
    def merge_messages(messages: List[IBaseMessage], 
                      merge_strategy: str = "sequential") -> List[IBaseMessage]:
        """合并消息
        
        Args:
            messages: 消息列表
            merge_strategy: 合并策略 ("sequential", "by_type", "consecutive")
            
        Returns:
            List[IBaseMessage]: 合并后的消息列表
        """
        if merge_strategy == "sequential":
            return messages  # 保持原顺序
        
        elif merge_strategy == "by_type":
            # 按类型分组
            grouped = {
                "system": MessageUtils.filter_system_messages(messages),
                "human": MessageUtils.filter_human_messages(messages),
                "ai": MessageUtils.filter_ai_messages(messages),
                "tool": MessageUtils.filter_tool_messages(messages)
            }
            return grouped["system"] + grouped["human"] + grouped["ai"] + grouped["tool"]
        
        elif merge_strategy == "consecutive":
            # 合并连续的同类型消息
            merged = []
            if not messages:
                return merged
            
            current_type = messages[0].type
            current_content = [messages[0].get_text_content()]
            
            for msg in messages[1:]:
                if msg.type == current_type:
                    current_content.append(msg.get_text_content())
                else:
                    # 创建合并消息
                    if current_type == "human":
                        merged.append(HumanMessage(content=" ".join(current_content)))
                    elif current_type == "ai":
                        merged.append(AIMessage(content=" ".join(current_content)))
                    elif current_type == "system":
                        merged.append(SystemMessage(content=" ".join(current_content)))
                    elif current_type == "tool":
                        # 工具消息不合并，保持原样
                        for original_msg in messages:
                            if is_tool_message(original_msg):
                                merged.append(original_msg)
                        return merged
                    
                    # 开始新类型
                    current_type = msg.type
                    current_content = [msg.get_text_content()]
            
            # 添加最后一组
            if current_type == "human":
                merged.append(HumanMessage(content=" ".join(current_content)))
            elif current_type == "ai":
                merged.append(AIMessage(content=" ".join(current_content)))
            elif current_type == "system":
                merged.append(SystemMessage(content=" ".join(current_content)))
            
            return merged
        
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")
    
    @staticmethod
    def calculate_message_hash(message: IBaseMessage) -> str:
        """计算消息的哈希值
        
        Args:
            message: 消息对象
            
        Returns:
            str: 消息的哈希值
        """
        content = message.get_text_content()
        hash_input = f"{message.type}:{content}:{message.name or ''}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    @staticmethod
    def calculate_conversation_hash(messages: List[IBaseMessage]) -> str:
        """计算对话的哈希值
        
        Args:
            messages: 消息列表
            
        Returns:
            str: 对话的哈希值
        """
        content_parts = []
        for msg in messages:
            content_parts.append(f"{msg.type}:{msg.get_text_content()}")
        
        conversation_text = "|".join(content_parts)
        return hashlib.md5(conversation_text.encode()).hexdigest()
    
    @staticmethod
    def validate_message(message: IBaseMessage) -> List[str]:
        """验证消息
        
        Args:
            message: 消息对象
            
        Returns:
            List[str]: 验证错误列表，空列表表示验证通过
        """
        errors = []
        
        # 检查基本属性
        if not hasattr(message, 'content') or message.content is None:
            errors.append("Message must have content")
        
        if not hasattr(message, 'type') or not message.type:
            errors.append("Message must have type")
        
        # 检查工具消息的特殊要求
        if is_tool_message(message) and not hasattr(message, 'tool_call_id'):
            errors.append("Tool message must have tool_call_id")
        
        # 检查内容格式
        if hasattr(message, 'content'):
            if isinstance(message.content, list):
                for i, item in enumerate(message.content):
                    if not isinstance(item, (str, dict)):
                        errors.append(f"Content item {i} must be string or dict")
        
        return errors
    
    @staticmethod
    def format_message_for_display(message: IBaseMessage, 
                                 max_length: int = 100) -> str:
        """格式化消息用于显示
        
        Args:
            message: 消息对象
            max_length: 最大显示长度
            
        Returns:
            str: 格式化后的消息字符串
        """
        content = message.get_text_content()
        if len(content) > max_length:
            content = content[:max_length] + "..."
        
        type_emoji = {
            "human": "👤",
            "ai": "🤖", 
            "system": "⚙️",
            "tool": "🔧"
        }
        
        emoji = type_emoji.get(message.type, "📝")
        name_part = f" ({message.name})" if message.name else ""
        
        return f"{emoji} {message.type.upper()}{name_part}: {content}"


# 便捷函数
def extract_text_from_messages(messages: List[IBaseMessage]) -> str:
    """便捷函数：从消息列表中提取纯文本内容"""
    return MessageUtils.extract_text_from_messages(messages)


def filter_messages_by_type(messages: List[IBaseMessage], message_type: str) -> List[IBaseMessage]:
    """便捷函数：按类型过滤消息"""
    return MessageUtils.filter_messages_by_type(messages, message_type)


def get_conversation_pairs(messages: List[IBaseMessage]) -> List[tuple[IBaseMessage, IBaseMessage]]:
    """便捷函数：获取对话对"""
    return MessageUtils.get_conversation_pairs(messages)


def calculate_conversation_hash(messages: List[IBaseMessage]) -> str:
    """便捷函数：计算对话的哈希值"""
    return MessageUtils.calculate_conversation_hash(messages)


def format_message_for_display(message: IBaseMessage, max_length: int = 100) -> str:
    """便捷函数：格式化消息用于显示"""
    return MessageUtils.format_message_for_display(message, max_length)