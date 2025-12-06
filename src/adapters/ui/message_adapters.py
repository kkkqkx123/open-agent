"""UI消息适配器实现

实现内部消息与UI消息之间的转换适配器。
"""

from typing import Any, Dict, List, Optional
from datetime import datetime

from ...interfaces.ui.messages import IUIMessage, IUIMessageAdapter
from ...interfaces.messages import IBaseMessage
from .messages import UserUIMessage, AssistantUIMessage, SystemUIMessage, ToolUIMessage, WorkflowUIMessage

# 避免循环导入，使用TYPE_CHECKING
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ...infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage, ToolMessage


class LLMMessageAdapter(IUIMessageAdapter):
    """LLM消息适配器
    
    负责将LLM消息转换为UI消息，以及将UI消息转换为LLM消息。
    """
    
    def to_ui_message(self, internal_message: IBaseMessage) -> IUIMessage:
        """将LLM消息转换为UI消息"""
        # 动态导入以避免循环导入
        from ...infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage, ToolMessage
        
        if isinstance(internal_message, HumanMessage):
            return UserUIMessage(
                content=internal_message.get_text_content(),
                message_id=internal_message.id,
                timestamp=internal_message.timestamp,
                metadata={
                    "source": "llm",
                    "original_type": "human",
                    "additional_kwargs": internal_message.additional_kwargs
                }
            )
        elif isinstance(internal_message, AIMessage):
            return AssistantUIMessage(
                content=internal_message.get_text_content(),
                message_id=internal_message.id,
                timestamp=internal_message.timestamp,
                tool_calls=internal_message.get_tool_calls(),
                metadata={
                    "source": "llm",
                    "original_type": "ai",
                    "additional_kwargs": internal_message.additional_kwargs,
                    "response_metadata": internal_message.response_metadata
                }
            )
        elif isinstance(internal_message, SystemMessage):
            return SystemUIMessage(
                content=internal_message.get_text_content(),
                message_id=internal_message.id,
                timestamp=internal_message.timestamp,
                metadata={
                    "source": "llm",
                    "original_type": "system",
                    "additional_kwargs": internal_message.additional_kwargs
                }
            )
        elif isinstance(internal_message, ToolMessage):
            return ToolUIMessage(
                tool_name=internal_message.additional_kwargs.get("tool_name", "unknown"),
                tool_input=internal_message.additional_kwargs.get("tool_input", {}),
                tool_output=internal_message.get_text_content(),
                success=True,
                message_id=internal_message.id,
                timestamp=internal_message.timestamp,
                metadata={
                    "source": "llm",
                    "original_type": "tool",
                    "tool_call_id": internal_message.additional_kwargs.get("tool_call_id"),
                    "additional_kwargs": internal_message.additional_kwargs
                }
            )
        else:
            # 默认处理为系统消息
            return SystemUIMessage(
                content=internal_message.get_text_content(),
                message_id=internal_message.id,
                timestamp=internal_message.timestamp,
                metadata={
                    "source": "llm",
                    "original_type": "unknown",
                    "additional_kwargs": internal_message.additional_kwargs
                }
            )
    
    def from_ui_message(self, ui_message: IUIMessage) -> IBaseMessage:
        """将UI消息转换为LLM消息"""
        # 动态导入以避免循环导入
        from ...infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage, ToolMessage
        
        if isinstance(ui_message, UserUIMessage):
            return HumanMessage(
                content=ui_message.content,
                id=ui_message.message_id,
                timestamp=datetime.fromisoformat(ui_message.metadata["timestamp"]),
                additional_kwargs=ui_message.metadata.get("additional_kwargs", {})
            )
        elif isinstance(ui_message, AssistantUIMessage):
            return AIMessage(
                content=ui_message.content,
                id=ui_message.message_id,
                timestamp=datetime.fromisoformat(ui_message.metadata["timestamp"]),
                tool_calls=ui_message.tool_calls,
                additional_kwargs=ui_message.metadata.get("additional_kwargs", {}),
                response_metadata=ui_message.metadata.get("response_metadata", {})
            )
        elif isinstance(ui_message, SystemUIMessage):
            return SystemMessage(
                content=ui_message.content,
                id=ui_message.message_id,
                timestamp=datetime.fromisoformat(ui_message.metadata["timestamp"]),
                additional_kwargs=ui_message.metadata.get("additional_kwargs", {})
            )
        elif isinstance(ui_message, ToolUIMessage):
            additional_kwargs = {
                "tool_name": ui_message.tool_name,
                "tool_input": ui_message.tool_input,
                "tool_call_id": ui_message.metadata.get("tool_call_id")
            }
            # 过滤掉None值
            additional_kwargs = {k: v for k, v in additional_kwargs.items() if v is not None}
            
            return ToolMessage(
                content=str(ui_message.tool_output),
                tool_call_id=additional_kwargs.get("tool_call_id", "unknown"),
                id=ui_message.message_id,
                timestamp=datetime.fromisoformat(ui_message.metadata["timestamp"]),
                additional_kwargs=additional_kwargs
            )
        else:
            # 默认转换为系统消息
            return SystemMessage(
                content=ui_message.display_content,
                id=ui_message.message_id,
                timestamp=datetime.fromisoformat(ui_message.metadata["timestamp"]),
                additional_kwargs={}
            )
    
    def can_adapt(self, message_type: str) -> bool:
        """检查是否可以适配指定类型的消息"""
        return message_type in ["human", "ai", "system", "tool", "unknown"]


class GraphMessageAdapter(IUIMessageAdapter):
    """图消息适配器
    
    负责将图消息转换为UI消息，以及将UI消息转换为图消息。
    """
    
    def to_ui_message(self, internal_message: Any) -> IUIMessage:
        """将图消息转换为UI消息"""
        # 尝试获取消息类型
        message_type = getattr(internal_message, 'message_type', None)
        content = getattr(internal_message, 'content', str(internal_message))
        metadata = getattr(internal_message, 'metadata', {})
        sender = getattr(internal_message, 'sender', None)
        
        if message_type == "ui":
            # UI消息直接转换
            return SystemUIMessage(
                content=f"UI事件: {metadata.get('ui_name', 'unknown')}",
                level="info",
                metadata={
                    "source": "graph",
                    "original_type": "ui",
                    "ui_data": content,
                    "sender": sender
                }
            )
        elif message_type == "system":
            return SystemUIMessage(
                content=str(content),
                metadata={
                    "source": "graph",
                    "original_type": "system",
                    "sender": sender
                }
            )
        elif message_type == "error":
            return SystemUIMessage(
                content=str(content),
                level="error",
                metadata={
                    "source": "graph",
                    "original_type": "error",
                    "sender": sender
                }
            )
        elif message_type == "workflow":
            return WorkflowUIMessage(
                content=str(content),
                workflow_name=metadata.get("workflow_name"),
                node_name=metadata.get("node_name"),
                status=metadata.get("status", "info"),
                metadata={
                    "source": "graph",
                    "original_type": "workflow",
                    "sender": sender
                }
            )
        else:
            # 默认处理为系统消息
            return SystemUIMessage(
                content=f"系统消息: {message_type or 'unknown'} - {str(content)}",
                metadata={
                    "source": "graph",
                    "original_type": message_type or "unknown",
                    "sender": sender
                }
            )
    
    def from_ui_message(self, ui_message: IUIMessage) -> Any:
        """将UI消息转换为图消息"""
        # 创建一个简单的图消息对象
        class GraphMessage:
            def __init__(self, message_type: str, content: Any, sender: str, metadata: Dict[str, Any]):
                self.message_type = message_type
                self.content = content
                self.sender = sender
                self.metadata = metadata
        
        return GraphMessage(
            message_type="ui_event",
            content={
                "action": ui_message.message_type,
                "content": ui_message.display_content,
                "message_id": ui_message.message_id
            },
            sender="ui_adapter",
            metadata={
                "ui_message_id": ui_message.message_id,
                "original_type": ui_message.message_type,
                "timestamp": ui_message.metadata.get("timestamp")
            }
        )
    
    def can_adapt(self, message_type: str) -> bool:
        """检查是否可以适配指定类型的消息"""
        return message_type in ["ui", "system", "error", "workflow", "node", "edge", "unknown"]


class WorkflowMessageAdapter(IUIMessageAdapter):
    """工作流消息适配器
    
    负责将工作流消息转换为UI消息，以及将UI消息转换为工作流消息。
    """
    
    def to_ui_message(self, internal_message: Any) -> IUIMessage:
        """将工作流消息转换为UI消息"""
        # 尝试获取工作流相关信息
        workflow_name = getattr(internal_message, 'workflow_name', None)
        node_name = getattr(internal_message, 'node_name', None)
        status = getattr(internal_message, 'status', 'info')
        content = getattr(internal_message, 'content', str(internal_message))
        message_type = getattr(internal_message, 'message_type', 'workflow')
        
        return WorkflowUIMessage(
            content=str(content),
            workflow_name=workflow_name,
            node_name=node_name,
            status=status,
            metadata={
                "source": "workflow",
                "original_type": message_type,
                "workflow_data": getattr(internal_message, 'data', {})
            }
        )
    
    def from_ui_message(self, ui_message: IUIMessage) -> Any:
        """将UI消息转换为工作流消息"""
        # 创建一个简单的工作流消息对象
        class WorkflowMessage:
            def __init__(self, message_type: str, content: Any, metadata: Dict[str, Any]):
                self.message_type = message_type
                self.content = content
                self.metadata = metadata
        
        return WorkflowMessage(
            message_type="ui_event",
            content={
                "action": ui_message.message_type,
                "content": ui_message.display_content
            },
            metadata={
                "ui_message_id": ui_message.message_id,
                "original_type": ui_message.message_type,
                "timestamp": ui_message.metadata.get("timestamp")
            }
        )
    
    def can_adapt(self, message_type: str) -> bool:
        """检查是否可以适配指定类型的消息"""
        return message_type in ["workflow", "node", "edge", "execution", "unknown"]