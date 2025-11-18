"""适配器工厂

提供适配器的创建和管理功能。
"""

from typing import Optional

from .state_adapter import StateAdapter
from .message_adapter import MessageAdapter


class AdapterFactory:
    """适配器工厂
    
    负责创建和管理各种适配器实例。
    """
    
    def __init__(self) -> None:
        """初始化适配器工厂"""
        self._state_adapter: Optional[StateAdapter] = None
        self._message_adapter: Optional[MessageAdapter] = None
    
    def get_state_adapter(self) -> StateAdapter:
        """获取状态适配器实例
        
        Returns:
            状态适配器实例
        """
        if self._state_adapter is None:
            self._state_adapter = StateAdapter()
        return self._state_adapter
    
    def get_message_adapter(self) -> MessageAdapter:
        """获取消息适配器实例
        
        Returns:
            消息适配器实例
        """
        if self._message_adapter is None:
            self._message_adapter = MessageAdapter()
        return self._message_adapter
    
    def create_state_adapter(self) -> StateAdapter:
        """创建新的状态适配器实例
        
        Returns:
            新的状态适配器实例
        """
        return StateAdapter()
    
    def create_message_adapter(self) -> MessageAdapter:
        """创建新的消息适配器实例
        
        Returns:
            新的消息适配器实例
        """
        return MessageAdapter()


# 全局适配器工厂实例
_global_adapter_factory: Optional[AdapterFactory] = None


def get_adapter_factory() -> AdapterFactory:
    """获取全局适配器工厂实例
    
    Returns:
        全局适配器工厂实例
    """
    global _global_adapter_factory
    if _global_adapter_factory is None:
        _global_adapter_factory = AdapterFactory()
    return _global_adapter_factory


def get_state_adapter() -> StateAdapter:
    """获取全局状态适配器实例
    
    Returns:
        全局状态适配器实例
    """
    return get_adapter_factory().get_state_adapter()


def get_message_adapter() -> MessageAdapter:
    """获取全局消息适配器实例
    
    Returns:
        全局消息适配器实例
    """
    return get_adapter_factory().get_message_adapter()


def create_state_adapter() -> StateAdapter:
    """创建新的状态适配器实例
    
    Returns:
        新的状态适配器实例
    """
    return get_adapter_factory().create_state_adapter()


def create_message_adapter() -> MessageAdapter:
    """创建新的消息适配器实例
    
    Returns:
        新的消息适配器实例
    """
    return get_adapter_factory().create_message_adapter()