"""UI消息管理器实现

实现UI消息的管理功能，包括适配器注册、消息转换、消息存储等。
"""

from typing import Dict, Any, List, Optional, Type
import logging

from ...interfaces.ui.messages import (
    IUIMessage, 
    IUIMessageAdapter, 
    IUIMessageRenderer,
    IUIMessageManager
)
from .message_adapters import LLMMessageAdapter, GraphMessageAdapter, WorkflowMessageAdapter


logger = logging.getLogger(__name__)


class UIMessageManager(IUIMessageManager):
    """UI消息管理器
    
    负责管理UI消息的生命周期，包括消息转换、存储、渲染等。
    """
    
    def __init__(self):
        self._adapters: List[IUIMessageAdapter] = []
        self._renderers: Dict[str, IUIMessageRenderer] = {}
        self._messages: Dict[str, IUIMessage] = {}
        
        # 注册默认适配器
        self.register_adapter(LLMMessageAdapter())
        self.register_adapter(GraphMessageAdapter())
        self.register_adapter(WorkflowMessageAdapter())
        
        logger.info("UI消息管理器初始化完成")
    
    def register_adapter(self, adapter: IUIMessageAdapter) -> None:
        """注册消息适配器"""
        self._adapters.append(adapter)
        logger.debug(f"注册消息适配器: {type(adapter).__name__}")
    
    def register_renderer(self, message_type: str, renderer: IUIMessageRenderer) -> None:
        """注册消息渲染器"""
        self._renderers[message_type] = renderer
        logger.debug(f"注册消息渲染器: {message_type} -> {type(renderer).__name__}")
    
    def convert_to_ui_message(self, internal_message: Any) -> Optional[IUIMessage]:
        """将内部消息转换为UI消息"""
        for adapter in self._adapters:
            try:
                # 根据消息类型选择适配器
                message_type = self._extract_message_type(internal_message)
                if adapter.can_adapt(message_type):
                    ui_message = adapter.to_ui_message(internal_message)
                    logger.debug(f"成功转换消息: {message_type} -> {ui_message.message_type}")
                    return ui_message
            except Exception as e:
                logger.warning(f"适配器 {type(adapter).__name__} 转换消息失败: {e}")
                continue
        
        logger.warning(f"无法转换内部消息: {type(internal_message)}")
        return None
    
    def convert_from_ui_message(self, ui_message: IUIMessage, target_type: str) -> Optional[Any]:
        """将UI消息转换为内部消息"""
        for adapter in self._adapters:
            if adapter.can_adapt(target_type):
                try:
                    internal_message = adapter.from_ui_message(ui_message)
                    logger.debug(f"成功转换UI消息: {ui_message.message_type} -> {target_type}")
                    return internal_message
                except Exception as e:
                    logger.warning(f"适配器 {type(adapter).__name__} 转换UI消息失败: {e}")
                    continue
        
        logger.warning(f"无法转换UI消息: {ui_message.message_type} -> {target_type}")
        return None
    
    def add_message(self, ui_message: IUIMessage) -> None:
        """添加UI消息"""
        self._messages[ui_message.message_id] = ui_message
        logger.debug(f"添加UI消息: {ui_message.message_id} ({ui_message.message_type})")
    
    def remove_message(self, message_id: str) -> bool:
        """移除UI消息"""
        if message_id in self._messages:
            del self._messages[message_id]
            logger.debug(f"移除UI消息: {message_id}")
            return True
        return False
    
    def get_message(self, message_id: str) -> Optional[IUIMessage]:
        """获取UI消息"""
        return self._messages.get(message_id)
    
    def get_all_messages(self) -> List[IUIMessage]:
        """获取所有UI消息"""
        return list(self._messages.values())
    
    def get_messages_by_type(self, message_type: str) -> List[IUIMessage]:
        """根据类型获取UI消息"""
        return [
            msg for msg in self._messages.values()
            if msg.message_type == message_type
        ]
    
    def render_message(self, ui_message: IUIMessage) -> str:
        """渲染UI消息"""
        renderer = self._renderers.get(ui_message.message_type)
        if renderer:
            try:
                return renderer.render(ui_message)
            except Exception as e:
                logger.warning(f"渲染消息失败: {e}")
                return ui_message.display_content
        else:
            # 默认渲染
            return ui_message.display_content
    
    def clear_messages(self) -> None:
        """清空所有消息"""
        message_count = len(self._messages)
        self._messages.clear()
        logger.info(f"清空所有UI消息: {message_count} 条")
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return len(self._messages)
    
    def get_message_types(self) -> List[str]:
        """获取所有消息类型"""
        return list(set(msg.message_type for msg in self._messages.values()))
    
    def get_messages_by_source(self, source: str) -> List[IUIMessage]:
        """根据来源获取UI消息"""
        return [
            msg for msg in self._messages.values()
            if msg.metadata.get("source") == source
        ]
    
    def get_latest_message(self, message_type: Optional[str] = None) -> Optional[IUIMessage]:
        """获取最新消息"""
        messages = self.get_all_messages()
        if message_type:
            messages = [msg for msg in messages if msg.message_type == message_type]
        
        if not messages:
            return None
        
        # 按时间戳排序
        messages.sort(key=lambda msg: msg.metadata.get("timestamp", ""), reverse=True)
        return messages[0]
    
    def _extract_message_type(self, internal_message: Any) -> str:
        """提取内部消息类型"""
        # 尝试从不同属性获取消息类型
        for attr_name in ['type', 'message_type', '__class__.__name__']:
            if hasattr(internal_message, attr_name):
                value = getattr(internal_message, attr_name)
                if isinstance(value, str):
                    return value.lower()
        
        # 尝试从类名推断
        class_name = type(internal_message).__name__.lower()
        if 'human' in class_name or 'user' in class_name:
            return 'human'
        elif 'ai' in class_name or 'assistant' in class_name:
            return 'ai'
        elif 'system' in class_name:
            return 'system'
        elif 'tool' in class_name:
            return 'tool'
        elif 'workflow' in class_name:
            return 'workflow'
        
        return 'unknown'


class DefaultUIMessageRenderer(IUIMessageRenderer):
    """默认UI消息渲染器

    提供基本的消息渲染功能。
    """

    def render(self, message: IUIMessage) -> str:
        """渲染消息"""
        timestamp = message.metadata.get("timestamp", "")
        message_type = message.message_type.upper()

        # 根据消息类型添加前缀
        if message_type == "USER":
            user_name = getattr(message, 'user_name', '用户')
            prefix = f"[{user_name}]"
        elif message_type == "ASSISTANT":
            assistant_name = getattr(message, 'assistant_name', '助手')
            prefix = f"[{assistant_name}]"
        elif message_type == "SYSTEM":
            level = getattr(message, 'level', 'info').upper()
            prefix = f"[系统-{level}]"
        elif message_type == "TOOL":
            tool_name = getattr(message, 'tool_name', 'unknown')
            status = "成功" if getattr(message, 'success', True) else "失败"
            prefix = f"[工具-{tool_name}-{status}]"
        elif message_type == "WORKFLOW":
            workflow_name = getattr(message, 'workflow_name', 'unknown')
            node_name = getattr(message, 'node_name', '')
            status = getattr(message, 'status', 'info').upper()
            prefix = f"[工作流-{workflow_name}-{node_name}-{status}]" if node_name else f"[工作流-{workflow_name}-{status}]"
        else:
            prefix = f"[{message_type}]"

        return f"{timestamp} {prefix} {message.display_content}"

    def can_render(self, message_type: str) -> bool:
        """检查是否可以渲染指定类型的消息"""
        return True  # 默认渲染器可以渲染所有类型