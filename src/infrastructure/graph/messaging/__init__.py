"""消息传递模块

提供消息处理、可靠性保证和多种传递模式。
"""

from .message_processor import (
    Message,
    MessageFilter,
    MessageTypeFilter,
    SenderFilter,
    RecipientFilter,
    MetadataFilter,
    MessageTransformer,
    ContentTransformer,
    MetadataAdder,
    MessageValidator,
    RequiredFieldsValidator,
    MessageTypeValidator,
    MessageProcessor,
)

from .message_reliability import (
    DeliveryMode,
    RetryPolicy,
    DeliveryTracker,
    MessageReliability,
)

from .passing_modes import (
    MessagePassingMode,
    BaseMessagePassingMode,
    ChannelBasedMode,
    DirectMessagingMode,
    PublishSubscribeMode,
    RequestResponseMode,
    MessagePassingManager,
)

__all__ = [
    # 消息处理器
    "Message",
    "MessageFilter",
    "MessageTypeFilter",
    "SenderFilter",
    "RecipientFilter",
    "MetadataFilter",
    "MessageTransformer",
    "ContentTransformer",
    "MetadataAdder",
    "MessageValidator",
    "RequiredFieldsValidator",
    "MessageTypeValidator",
    "MessageProcessor",
    
    # 消息可靠性
    "DeliveryMode",
    "RetryPolicy",
    "DeliveryTracker",
    "MessageReliability",
    
    # 消息传递模式
    "MessagePassingMode",
    "BaseMessagePassingMode",
    "ChannelBasedMode",
    "DirectMessagingMode",
    "PublishSubscribeMode",
    "RequestResponseMode",
    "MessagePassingManager",
]