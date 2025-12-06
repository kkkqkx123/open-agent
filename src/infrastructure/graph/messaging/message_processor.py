"""消息处理器

提供消息处理、过滤和转换功能。
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Sequence, Union

from ..types import errors


class Message:
    """消息基类"""
    
    def __init__(
        self,
        message_type: str,
        content: Any,
        sender: str,
        recipients: Optional[Sequence[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.message_type = message_type
        self.content = content
        self.sender = sender
        self.recipients = recipients or []
        self.metadata = metadata or {}
        self.id = id(self)  # 简单的消息ID生成
    
    def __repr__(self) -> str:
        return f"Message(type={self.message_type}, sender={self.sender}, recipients={self.recipients})"


class MessageFilter(ABC):
    """消息过滤器基类"""
    
    @abstractmethod
    def filter(self, message: Message) -> bool:
        """过滤消息
        
        Args:
            message: 消息
            
        Returns:
            True表示消息通过过滤器，False表示被过滤
        """
        pass


class MessageTypeFilter(MessageFilter):
    """消息类型过滤器"""
    
    def __init__(self, allowed_types: Union[str, Sequence[str]]) -> None:
        if isinstance(allowed_types, str):
            self.allowed_types = {allowed_types}
        else:
            self.allowed_types = set(allowed_types)
    
    def filter(self, message: Message) -> bool:
        return message.message_type in self.allowed_types


class SenderFilter(MessageFilter):
    """发送者过滤器"""
    
    def __init__(self, allowed_senders: Union[str, Sequence[str]]) -> None:
        if isinstance(allowed_senders, str):
            self.allowed_senders = {allowed_senders}
        else:
            self.allowed_senders = set(allowed_senders)
    
    def filter(self, message: Message) -> bool:
        return message.sender in self.allowed_senders


class RecipientFilter(MessageFilter):
    """接收者过滤器"""
    
    def __init__(self, recipient: str) -> None:
        self.recipient = recipient
    
    def filter(self, message: Message) -> bool:
        return not message.recipients or self.recipient in message.recipients


class MetadataFilter(MessageFilter):
    """元数据过滤器"""
    
    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value
    
    def filter(self, message: Message) -> bool:
        return message.metadata.get(self.key) == self.value


class MessageTransformer(ABC):
    """消息转换器基类"""
    
    @abstractmethod
    def transform(self, message: Message) -> Optional[Message]:
        """转换消息
        
        Args:
            message: 原始消息
            
        Returns:
            转换后的消息，如果返回None表示丢弃消息
        """
        pass


class ContentTransformer(MessageTransformer):
    """内容转换器"""
    
    def __init__(self, transform_func: Callable[[Any], Any]) -> None:
        self.transform_func = transform_func
    
    def transform(self, message: Message) -> Optional[Message]:
        try:
            new_content = self.transform_func(message.content)
            new_message = Message(
                message_type=message.message_type,
                content=new_content,
                sender=message.sender,
                recipients=message.recipients,
                metadata=message.metadata.copy(),
            )
            return new_message
        except Exception:
            return None


class MetadataAdder(MessageTransformer):
    """元数据添加器"""
    
    def __init__(self, key: str, value: Any) -> None:
        self.key = key
        self.value = value
    
    def transform(self, message: Message) -> Optional[Message]:
        new_metadata = message.metadata.copy()
        new_metadata[self.key] = self.value
        
        new_message = Message(
            message_type=message.message_type,
            content=message.content,
            sender=message.sender,
            recipients=message.recipients,
            metadata=new_metadata,
        )
        return new_message


class MessageValidator(ABC):
    """消息验证器基类"""
    
    @abstractmethod
    def validate(self, message: Message) -> bool:
        """验证消息
        
        Args:
            message: 消息
            
        Returns:
            True表示消息有效，False表示消息无效
        """
        pass


class RequiredFieldsValidator(MessageValidator):
    """必需字段验证器"""
    
    def __init__(self, required_fields: List[str]) -> None:
        self.required_fields = required_fields
    
    def validate(self, message: Message) -> bool:
        if isinstance(message.content, dict):
            return all(field in message.content for field in self.required_fields)
        return False


class MessageTypeValidator(MessageValidator):
    """消息类型验证器"""
    
    def __init__(self, valid_types: Union[str, Sequence[str]]) -> None:
        if isinstance(valid_types, str):
            self.valid_types = {valid_types}
        else:
            self.valid_types = set(valid_types)
    
    def validate(self, message: Message) -> bool:
        return message.message_type in self.valid_types


class MessageProcessor:
    """消息处理器
    
    提供消息过滤、转换和验证的流水线处理功能。
    """
    
    def __init__(self) -> None:
        self.filters: List[MessageFilter] = []
        self.transformers: List[MessageTransformer] = []
        self.validators: List[MessageValidator] = []
    
    def add_filter(self, filter_obj: MessageFilter) -> None:
        """添加过滤器
        
        Args:
            filter_obj: 过滤器对象
        """
        self.filters.append(filter_obj)
    
    def add_transformer(self, transformer: MessageTransformer) -> None:
        """添加转换器
        
        Args:
            transformer: 转换器对象
        """
        self.transformers.append(transformer)
    
    def add_validator(self, validator: MessageValidator) -> None:
        """添加验证器
        
        Args:
            validator: 验证器对象
        """
        self.validators.append(validator)
    
    def process_message(self, message: Message) -> Optional[Message]:
        """处理单个消息
        
        Args:
            message: 原始消息
            
        Returns:
            处理后的消息，如果被过滤或验证失败则返回None
        """
        # 应用过滤器
        for filter_obj in self.filters:
            if not filter_obj.filter(message):
                return None
        
        # 应用转换器
        current_message = message
        for transformer in self.transformers:
            current_message = transformer.transform(current_message)
            if current_message is None:
                return None
        
        # 应用验证器
        for validator in self.validators:
            if not validator.validate(current_message):
                return None
        
        return current_message
    
    async def process_message_async(self, message: Message) -> Optional[Message]:
        """异步处理单个消息
        
        Args:
            message: 原始消息
            
        Returns:
            处理后的消息，如果被过滤或验证失败则返回None
        """
        # 应用过滤器
        for filter_obj in self.filters:
            if not filter_obj.filter(message):
                return None
        
        # 应用转换器
        current_message = message
        for transformer in self.transformers:
            if asyncio.iscoroutinefunction(transformer.transform):
                current_message = await transformer.transform(current_message)
            else:
                current_message = transformer.transform(current_message)
            if current_message is None:
                return None
        
        # 应用验证器
        for validator in self.validators:
            if asyncio.iscoroutinefunction(validator.validate):
                if not await validator.validate(current_message):
                    return None
            else:
                if not validator.validate(current_message):
                    return None
        
        return current_message
    
    def process_messages(self, messages: Sequence[Message]) -> List[Message]:
        """批量处理消息
        
        Args:
            messages: 消息列表
            
        Returns:
            处理后的消息列表
        """
        processed_messages = []
        for message in messages:
            processed_message = self.process_message(message)
            if processed_message is not None:
                processed_messages.append(processed_message)
        return processed_messages
    
    async def process_messages_async(self, messages: Sequence[Message]) -> List[Message]:
        """异步批量处理消息
        
        Args:
            messages: 消息列表
            
        Returns:
            处理后的消息列表
        """
        tasks = [self.process_message_async(message) for message in messages]
        results = await asyncio.gather(*tasks)
        return [msg for msg in results if msg is not None]
    
    def clear_filters(self) -> None:
        """清空所有过滤器"""
        self.filters.clear()
    
    def clear_transformers(self) -> None:
        """清空所有转换器"""
        self.transformers.clear()
    
    def clear_validators(self) -> None:
        """清空所有验证器"""
        self.validators.clear()
    
    def clear_all(self) -> None:
        """清空所有处理器"""
        self.clear_filters()
        self.clear_transformers()
        self.clear_validators()