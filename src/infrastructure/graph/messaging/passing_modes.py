"""消息传递模式

定义不同的消息传递模式。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, TYPE_CHECKING

from .message_processor import Message
from .message_reliability import MessageReliability
from ..types import errors

if TYPE_CHECKING:
    from ..optimization.message_router import MessageRouter


class MessagePassingMode(Enum):
    """消息传递模式"""
    CHANNEL_BASED = "channel"      # 基于通道
    DIRECT_MESSAGING = "direct"    # 直接消息
    PUBLISH_SUBSCRIBE = "pubsub"   # 发布订阅
    REQUEST_RESPONSE = "reqresp"   # 请求响应


class BaseMessagePassingMode(ABC):
    """消息传递模式基类"""
    
    @abstractmethod
    async def send(self, message: Message, targets: Optional[Sequence[str]] = None) -> bool:
        """发送消息
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功发送
        """
        pass
    
    @abstractmethod
    async def receive(self, recipient: str) -> Optional[Message]:
        """接收消息
        
        Args:
            recipient: 接收者
            
        Returns:
            接收到的消息
        """
        pass


class ChannelBasedMode(BaseMessagePassingMode):
    """基于通道的消息传递模式"""
    
    def __init__(self) -> None:
        """初始化基于通道的消息传递模式"""
        self.channels: Dict[str, List[Message]] = {}
    
    async def send(self, message: Message, targets: Optional[Sequence[str]] = None) -> bool:
        """发送消息到通道
        
        Args:
            message: 消息
            targets: 目标列表（通道名称）
            
        Returns:
            是否成功发送
        """
        if not targets:
            targets = [message.message_type]
        
        try:
            for target in targets:
                if target not in self.channels:
                    self.channels[target] = []
                self.channels[target].append(message)
            return True
        except Exception:
            return False
    
    async def receive(self, recipient: str) -> Optional[Message]:
        """从通道接收消息
        
        Args:
            recipient: 接收者（通道名称）
            
        Returns:
            接收到的消息
        """
        if recipient in self.channels and self.channels[recipient]:
            return self.channels[recipient].pop(0)
        return None
    
    def get_channel_messages(self, channel: str) -> List[Message]:
        """获取通道中的所有消息
        
        Args:
            channel: 通道名称
            
        Returns:
            消息列表
        """
        return self.channels.get(channel, []).copy()
    
    def clear_channel(self, channel: str) -> None:
        """清空通道
        
        Args:
            channel: 通道名称
        """
        if channel in self.channels:
            self.channels[channel].clear()


class DirectMessagingMode(BaseMessagePassingMode):
    """直接消息传递模式"""
    
    def __init__(self) -> None:
        """初始化直接消息传递模式"""
        self.mailboxes: Dict[str, List[Message]] = {}
    
    async def send(self, message: Message, targets: Optional[Sequence[str]] = None) -> bool:
        """直接发送消息到目标
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功发送
        """
        if not targets:
            targets = message.recipients
        
        if not targets:
            return False
        
        try:
            for target in targets:
                if target not in self.mailboxes:
                    self.mailboxes[target] = []
                self.mailboxes[target].append(message)
            return True
        except Exception:
            return False
    
    async def receive(self, recipient: str) -> Optional[Message]:
        """从邮箱接收消息
        
        Args:
            recipient: 接收者
            
        Returns:
            接收到的消息
        """
        if recipient in self.mailboxes and self.mailboxes[recipient]:
            return self.mailboxes[recipient].pop(0)
        return None
    
    def get_mailbox_messages(self, recipient: str) -> List[Message]:
        """获取邮箱中的所有消息
        
        Args:
            recipient: 接收者
            
        Returns:
            消息列表
        """
        return self.mailboxes.get(recipient, []).copy()
    
    def clear_mailbox(self, recipient: str) -> None:
        """清空邮箱
        
        Args:
            recipient: 接收者
        """
        if recipient in self.mailboxes:
            self.mailboxes[recipient].clear()


class PublishSubscribeMode(BaseMessagePassingMode):
    """发布订阅消息传递模式"""
    
    def __init__(self) -> None:
        """初始化发布订阅消息传递模式"""
        self.topics: Dict[str, List[str]] = {}  # 主题到订阅者列表
        self.subscriptions: Dict[str, List[str]] = {}  # 订阅者到主题列表
        self.message_queue: Dict[str, List[Message]] = {}  # 订阅者消息队列
    
    def subscribe(self, subscriber: str, topic: str) -> None:
        """订阅主题
        
        Args:
            subscriber: 订阅者
            topic: 主题
        """
        if topic not in self.topics:
            self.topics[topic] = []
        if subscriber not in self.topics[topic]:
            self.topics[topic].append(subscriber)
        
        if subscriber not in self.subscriptions:
            self.subscriptions[subscriber] = []
        if topic not in self.subscriptions[subscriber]:
            self.subscriptions[subscriber].append(topic)
    
    def unsubscribe(self, subscriber: str, topic: str) -> None:
        """取消订阅主题
        
        Args:
            subscriber: 订阅者
            topic: 主题
        """
        if topic in self.topics and subscriber in self.topics[topic]:
            self.topics[topic].remove(subscriber)
        
        if subscriber in self.subscriptions and topic in self.subscriptions[subscriber]:
            self.subscriptions[subscriber].remove(topic)
    
    async def send(self, message: Message, targets: Optional[Sequence[str]] = None) -> bool:
        """发布消息到主题
        
        Args:
            message: 消息
            targets: 目标主题列表
            
        Returns:
            是否成功发送
        """
        if not targets:
            targets = [message.message_type]
        
        try:
            for topic in targets:
                if topic in self.topics:
                    for subscriber in self.topics[topic]:
                        if subscriber not in self.message_queue:
                            self.message_queue[subscriber] = []
                        self.message_queue[subscriber].append(message)
            return True
        except Exception:
            return False
    
    async def receive(self, recipient: str) -> Optional[Message]:
        """接收订阅的消息
        
        Args:
            recipient: 接收者
            
        Returns:
            接收到的消息
        """
        if recipient in self.message_queue and self.message_queue[recipient]:
            return self.message_queue[recipient].pop(0)
        return None
    
    def get_subscribers(self, topic: str) -> List[str]:
        """获取主题的订阅者列表
        
        Args:
            topic: 主题
            
        Returns:
            订阅者列表
        """
        return self.topics.get(topic, []).copy()
    
    def get_subscriptions(self, subscriber: str) -> List[str]:
        """获取订阅者的主题列表
        
        Args:
            subscriber: 订阅者
            
        Returns:
            主题列表
        """
        return self.subscriptions.get(subscriber, []).copy()


class RequestResponseMode(BaseMessagePassingMode):
    """请求响应消息传递模式"""
    
    def __init__(self) -> None:
        """初始化请求响应消息传递模式"""
        self.pending_requests: Dict[str, Message] = {}
        self.responses: Dict[str, Message] = {}
    
    async def send(self, message: Message, targets: Optional[Sequence[str]] = None) -> bool:
        """发送请求
        
        Args:
            message: 消息
            targets: 目标列表
            
        Returns:
            是否成功发送
        """
        if not targets:
            targets = message.recipients
        
        if not targets:
            return False
        
        try:
            # 标记为请求消息
            message.metadata["is_request"] = True
            message.metadata["targets"] = list(targets)
            
            # 存储待处理的请求
            self.pending_requests[str(message.id)] = message
            return True
        except Exception:
            return False
    
    async def receive(self, recipient: str) -> Optional[Message]:
        """接收请求
        
        Args:
            recipient: 接收者
            
        Returns:
            接收到的请求
        """
        # 查找发送给此接收者的请求
        for message_id, message in self.pending_requests.items():
            targets = message.metadata.get("targets", [])
            if recipient in targets:
                # 从待处理列表中移除
                del self.pending_requests[message_id]
                return message
        return None
    
    async def send_response(self, request: Message, response: Message) -> bool:
        """发送响应
        
        Args:
            request: 原始请求
            response: 响应消息
            
        Returns:
            是否成功发送
        """
        try:
            # 标记为响应消息
            response.metadata["is_response"] = True
            response.metadata["request_id"] = str(request.id)
            response.recipients = [request.sender]
            
            # 存储响应
            self.responses[str(request.id)] = response
            return True
        except Exception:
            return False
    
    async def receive_response(self, request_id: str) -> Optional[Message]:
        """接收响应
        
        Args:
            request_id: 请求ID
            
        Returns:
            接收到的响应
        """
        if request_id in self.responses:
            response = self.responses[request_id]
            del self.responses[request_id]
            return response
        return None
    
    def get_pending_requests(self) -> List[Message]:
        """获取所有待处理的请求
        
        Returns:
            请求列表
        """
        return list(self.pending_requests.values())
    
    def get_pending_responses(self) -> List[Message]:
        """获取所有待接收的响应
        
        Returns:
            响应列表
        """
        return list(self.responses.values())


class MessagePassingManager:
    """消息传递管理器
    
    管理不同的消息传递模式。
    """
    
    def __init__(self) -> None:
        """初始化消息传递管理器"""
        self.modes: Dict[MessagePassingMode, BaseMessagePassingMode] = {
            MessagePassingMode.CHANNEL_BASED: ChannelBasedMode(),
            MessagePassingMode.DIRECT_MESSAGING: DirectMessagingMode(),
            MessagePassingMode.PUBLISH_SUBSCRIBE: PublishSubscribeMode(),
            MessagePassingMode.REQUEST_RESPONSE: RequestResponseMode(),
        }
        self.default_mode = MessagePassingMode.CHANNEL_BASED
        self.message_reliability = MessageReliability()
        
        # 延迟导入避免循环依赖
        from ..optimization.message_router import MessageRouter
        self.message_router: MessageRouter = MessageRouter()
    
    def set_default_mode(self, mode: MessagePassingMode) -> None:
        """设置默认消息传递模式
        
        Args:
            mode: 消息传递模式
        """
        if mode not in self.modes:
            raise errors.InvalidConfigurationError(f"不支持的消息传递模式: {mode}")
        self.default_mode = mode
    
    async def send(
        self,
        message: Message,
        targets: Optional[Sequence[str]] = None,
        mode: Optional[MessagePassingMode] = None,
    ) -> bool:
        """发送消息
        
        Args:
            message: 消息
            targets: 目标列表
            mode: 消息传递模式
            
        Returns:
            是否成功发送
        """
        # 使用指定的模式或默认模式
        passing_mode = mode or self.default_mode
        
        # 路由消息
        if not targets:
            targets = self.message_router.route_message(message)
        
        # 使用可靠性保证
        if targets:
            return await self.message_reliability.ensure_delivery(message, list(targets))
        
        # 直接发送
        mode_handler = self.modes[passing_mode]
        return await mode_handler.send(message, targets)
    
    async def receive(
        self,
        recipient: str,
        mode: Optional[MessagePassingMode] = None,
    ) -> Optional[Message]:
        """接收消息
        
        Args:
            recipient: 接收者
            mode: 消息传递模式
            
        Returns:
            接收到的消息
        """
        # 使用指定的模式或默认模式
        passing_mode = mode or self.default_mode
        mode_handler = self.modes[passing_mode]
        return await mode_handler.receive(recipient)
    
    def get_mode_handler(self, mode: MessagePassingMode) -> BaseMessagePassingMode:
        """获取模式处理器
        
        Args:
            mode: 消息传递模式
            
        Returns:
            模式处理器
        """
        if mode not in self.modes:
            raise errors.InvalidConfigurationError(f"不支持的消息传递模式: {mode}")
        return self.modes[mode]