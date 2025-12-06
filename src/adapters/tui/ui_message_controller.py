"""TUI UI消息控制器实现

实现TUI框架与UI消息系统的集成，负责协调UI消息与TUI组件的交互。
"""

from typing import Dict, Any, List, Optional, Callable
import logging

from ...interfaces.ui.messages import IUIMessage, IUIMessageController
from ...adapters.ui.message_manager import UIMessageManager, DefaultUIMessageRenderer
from ...adapters.ui.messages import (
    UserUIMessage, 
    AssistantUIMessage, 
    SystemUIMessage, 
    ToolUIMessage,
    WorkflowUIMessage
)


logger = logging.getLogger(__name__)


class TUIUIMessageController(IUIMessageController):
    """TUI UI消息控制器
    
    负责协调UI消息与TUI组件的交互，处理消息的显示和用户输入。
    """
    
    def __init__(self, state_manager=None, main_content_component=None):
        self.state_manager = state_manager
        self.main_content_component = main_content_component
        self.ui_message_manager = UIMessageManager()
        
        # 注册默认渲染器
        default_renderer = DefaultUIMessageRenderer()
        for message_type in ["user", "assistant", "system", "tool", "workflow"]:
            self.ui_message_manager.register_renderer(message_type, default_renderer)
        
        # 消息处理器
        self._message_handlers: Dict[str, Callable] = {}
        
        # 设置消息处理器
        self._setup_message_handlers()
        
        logger.info("TUI UI消息控制器初始化完成")
    
    def _setup_message_handlers(self):
        """设置消息处理器"""
        # 注册到StateManager的钩子（如果可用）
        if self.state_manager:
            if hasattr(self.state_manager, 'add_user_message_hook'):
                self.state_manager.add_user_message_hook(self._on_user_message)
            if hasattr(self.state_manager, 'add_assistant_message_hook'):
                self.state_manager.add_assistant_message_hook(self._on_assistant_message)
            if hasattr(self.state_manager, 'add_system_message_hook'):
                self.state_manager.add_system_message_hook(self._on_system_message)
            if hasattr(self.state_manager, 'add_tool_message_hook'):
                self.state_manager.add_tool_message_hook(self._on_tool_message)
            if hasattr(self.state_manager, 'add_workflow_message_hook'):
                self.state_manager.add_workflow_message_hook(self._on_workflow_message)
        
        # 注册内部消息处理器
        self._message_handlers.update({
            "user": self._on_user_message,
            "assistant": self._on_assistant_message,
            "system": self._on_system_message,
            "tool": self._on_tool_message,
            "workflow": self._on_workflow_message
        })
    
    def _on_user_message(self, content: str, **kwargs) -> None:
        """处理用户消息"""
        ui_message = UserUIMessage(
            content=content,
            user_name=kwargs.get("user_name"),
            metadata=kwargs.get("metadata", {})
        )
        self._process_ui_message(ui_message)
    
    def _on_assistant_message(self, content: str, **kwargs) -> None:
        """处理助手消息"""
        ui_message = AssistantUIMessage(
            content=content,
            assistant_name=kwargs.get("assistant_name"),
            tool_calls=kwargs.get("tool_calls", []),
            metadata=kwargs.get("metadata", {})
        )
        self._process_ui_message(ui_message)
    
    def _on_system_message(self, content: str, **kwargs) -> None:
        """处理系统消息"""
        ui_message = SystemUIMessage(
            content=content,
            level=kwargs.get("level", "info"),
            metadata=kwargs.get("metadata", {})
        )
        self._process_ui_message(ui_message)
    
    def _on_tool_message(self, tool_name: str, tool_input: Dict[str, Any], 
                        tool_output: Any, success: bool = True, **kwargs) -> None:
        """处理工具消息"""
        ui_message = ToolUIMessage(
            tool_name=tool_name,
            tool_input=tool_input,
            tool_output=tool_output,
            success=success,
            metadata=kwargs.get("metadata", {})
        )
        self._process_ui_message(ui_message)
    
    def _on_workflow_message(self, content: str, workflow_name: Optional[str] = None,
                           node_name: Optional[str] = None, status: str = "info", **kwargs) -> None:
        """处理工作流消息"""
        ui_message = WorkflowUIMessage(
            content=content,
            workflow_name=workflow_name,
            node_name=node_name,
            status=status,
            metadata=kwargs.get("metadata", {})
        )
        self._process_ui_message(ui_message)
    
    def _process_ui_message(self, ui_message: IUIMessage) -> None:
        """处理UI消息"""
        # 添加到消息管理器
        self.ui_message_manager.add_message(ui_message)
        
        # 显示消息
        self.display_ui_message(ui_message)
    
    def process_internal_message(self, internal_message: Any) -> None:
        """处理内部消息"""
        ui_message = self.ui_message_manager.convert_to_ui_message(internal_message)
        if ui_message:
            self._process_ui_message(ui_message)
        else:
            logger.warning(f"无法转换内部消息: {type(internal_message)}")
    
    def process_user_input(self, input_text: str) -> None:
        """处理用户输入"""
        # 创建用户UI消息
        user_message = UserUIMessage(content=input_text)
        self._process_ui_message(user_message)
        
        # 转换为内部消息并发送给StateManager
        if self.state_manager:
            internal_message = self.ui_message_manager.convert_from_ui_message(
                user_message, "human"
            )
            if internal_message:
                # 发送给StateManager处理
                if hasattr(self.state_manager, 'process_user_message'):
                    self.state_manager.process_user_message(internal_message)
                else:
                    logger.warning("StateManager没有process_user_message方法")
    
    def clear_all_messages(self) -> None:
        """清空所有消息"""
        self.ui_message_manager.clear_messages()
        
        # 清空TUI组件
        if self.main_content_component:
            if hasattr(self.main_content_component, 'clear_all'):
                self.main_content_component.clear_all()
            elif hasattr(self.main_content_component, 'clear'):
                self.main_content_component.clear()
    
    def get_message_history(self) -> List[Dict[str, Any]]:
        """获取消息历史"""
        return [
            msg.to_dict() for msg in self.ui_message_manager.get_all_messages()
        ]
    
    def display_ui_message(self, ui_message: IUIMessage) -> None:
        """显示UI消息"""
        if not self.main_content_component:
            logger.warning("没有设置主内容组件，无法显示消息")
            return
        
        # 根据消息类型调用相应的显示方法
        if ui_message.message_type == "user":
            self._display_user_message(ui_message)
        elif ui_message.message_type == "assistant":
            self._display_assistant_message(ui_message)
        elif ui_message.message_type == "system":
            self._display_system_message(ui_message)
        elif ui_message.message_type == "tool":
            self._display_tool_message(ui_message)
        elif ui_message.message_type == "workflow":
            self._display_workflow_message(ui_message)
        else:
            self._display_default_message(ui_message)
    
    def _display_user_message(self, ui_message: UserUIMessage) -> None:
        """显示用户消息"""
        if hasattr(self.main_content_component, 'add_user_message'):
            self.main_content_component.add_user_message(ui_message.display_content)
        elif hasattr(self.main_content_component, 'add_message'):
            self.main_content_component.add_message(
                f"[{ui_message.user_name}] {ui_message.display_content}",
                "user"
            )
    
    def _display_assistant_message(self, ui_message: AssistantUIMessage) -> None:
        """显示助手消息"""
        if hasattr(self.main_content_component, 'add_assistant_message'):
            self.main_content_component.add_assistant_message(ui_message.display_content)
        elif hasattr(self.main_content_component, 'add_message'):
            self.main_content_component.add_message(
                f"[{ui_message.assistant_name}] {ui_message.display_content}",
                "assistant"
            )
        
        # 显示工具调用信息
        if ui_message.tool_calls and hasattr(self.main_content_component, 'add_tool_calls'):
            self.main_content_component.add_tool_calls(ui_message.tool_calls)
    
    def _display_system_message(self, ui_message: SystemUIMessage) -> None:
        """显示系统消息"""
        if hasattr(self.main_content_component, 'add_system_message'):
            self.main_content_component.add_system_message(
                ui_message.display_content, 
                ui_message.level
            )
        elif hasattr(self.main_content_component, 'add_message'):
            self.main_content_component.add_message(
                f"[系统-{ui_message.level}] {ui_message.display_content}",
                "system"
            )
    
    def _display_tool_message(self, ui_message: ToolUIMessage) -> None:
        """显示工具消息"""
        if hasattr(self.main_content_component, 'add_tool_message'):
            self.main_content_component.add_tool_message(
                ui_message.tool_name,
                ui_message.tool_input,
                ui_message.tool_output,
                ui_message.success
            )
        elif hasattr(self.main_content_component, 'add_message'):
            status = "成功" if ui_message.success else "失败"
            self.main_content_component.add_message(
                f"[工具-{ui_message.tool_name}-{status}] {ui_message.display_content}",
                "tool"
            )
    
    def _display_workflow_message(self, ui_message: WorkflowUIMessage) -> None:
        """显示工作流消息"""
        if hasattr(self.main_content_component, 'add_workflow_message'):
            self.main_content_component.add_workflow_message(
                ui_message.content,
                ui_message.workflow_name,
                ui_message.node_name,
                ui_message.status
            )
        elif hasattr(self.main_content_component, 'add_message'):
            prefix = f"[工作流-{ui_message.workflow_name}"
            if ui_message.node_name:
                prefix += f"-{ui_message.node_name}"
            prefix += f"-{ui_message.status}]"
            self.main_content_component.add_message(
                f"{prefix} {ui_message.display_content}",
                "workflow"
            )
    
    def _display_default_message(self, ui_message: IUIMessage) -> None:
        """显示默认消息"""
        if hasattr(self.main_content_component, 'add_message'):
            self.main_content_component.add_message(
                f"[{ui_message.message_type}] {ui_message.display_content}",
                ui_message.message_type
            )
    
    def register_message_handler(self, message_type: str, handler: Callable) -> None:
        """注册消息处理器"""
        self._message_handlers[message_type] = handler
        logger.debug(f"注册消息处理器: {message_type}")
    
    def unregister_message_handler(self, message_type: str) -> None:
        """注销消息处理器"""
        if message_type in self._message_handlers:
            del self._message_handlers[message_type]
            logger.debug(f"注销消息处理器: {message_type}")
    
    def get_message_count(self) -> int:
        """获取消息数量"""
        return self.ui_message_manager.get_message_count()
    
    def get_messages_by_type(self, message_type: str) -> List[IUIMessage]:
        """根据类型获取消息"""
        return self.ui_message_manager.get_messages_by_type(message_type)
    
    def get_latest_message(self, message_type: Optional[str] = None) -> Optional[IUIMessage]:
        """获取最新消息"""
        return self.ui_message_manager.get_latest_message(message_type)
    
    def set_main_content_component(self, component) -> None:
        """设置主内容组件"""
        self.main_content_component = component
        logger.info("设置主内容组件")
    
    def set_state_manager(self, state_manager) -> None:
        """设置状态管理器"""
        self.state_manager = state_manager
        # 重新设置消息处理器
        self._setup_message_handlers()
        logger.info("设置状态管理器")