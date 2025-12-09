"""UI消息实现

实现具体的UI消息类型，专注于UI展示和用户交互。
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import json

from ...interfaces.ui.messages import IUIMessage


class BaseUIMessage(IUIMessage):
    """基础UI消息"""
    
    def __init__(
        self,
        message_id: Optional[str] = None,
        message_type: str = "base",
        display_content: str = "",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ):
        self._message_id = message_id or str(uuid4())
        self._message_type = message_type
        self._display_content = display_content
        self._metadata = metadata or {}
        self._timestamp = timestamp or datetime.now()
    
    @property
    def message_id(self) -> str:
        return self._message_id
    
    @property
    def message_type(self) -> str:
        return self._message_type
    
    @property
    def display_content(self) -> str:
        return self._display_content
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._metadata,
            "timestamp": self._timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "message_id": self.message_id,
            "message_type": self.message_type,
            "display_content": self.display_content,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseUIMessage":
        """从字典创建实例"""
        metadata = data.get("metadata", {})
        timestamp_str = metadata.pop("timestamp", None)
        timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else None
        
        return cls(
            message_id=data.get("message_id"),
            message_type=data.get("message_type", "base"),
            display_content=data.get("display_content", ""),
            metadata=metadata,
            timestamp=timestamp
        )


class UserUIMessage(BaseUIMessage):
    """用户UI消息"""
    
    def __init__(
        self,
        content: str,
        user_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message_type="user",
            display_content=content,
            **kwargs
        )
        self._content = content
        self._user_name = user_name or "用户"
    
    @property
    def user_name(self) -> str:
        return self._user_name
    
    @property
    def content(self) -> str:
        return self._content
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "user_name": self.user_name,
            "content": self.content
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserUIMessage":
        """从字典创建实例"""
        base_data = {
            "message_id": data.get("message_id"),
            "metadata": data.get("metadata", {})
        }

        # 提取时间戳
        metadata = base_data["metadata"]
        timestamp_str = metadata.pop("timestamp", None)
        if timestamp_str:
            base_data["timestamp"] = datetime.fromisoformat(timestamp_str)

        # Remove message_type and display_content from base_data since they're set by constructor
        message_type = data.get("message_type")
        display_content = data.get("display_content")

        return cls(
            content=data.get("content", ""),
            user_name=data.get("user_name"),
            **base_data
        )


class AssistantUIMessage(BaseUIMessage):
    """助手UI消息"""
    
    def __init__(
        self,
        content: str,
        assistant_name: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        super().__init__(
            message_type="assistant",
            display_content=content,
            **kwargs
        )
        self._content = content
        self._assistant_name = assistant_name or "助手"
        self._tool_calls = tool_calls or []
    
    @property
    def assistant_name(self) -> str:
        return self._assistant_name
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def tool_calls(self) -> List[Dict[str, Any]]:
        return self._tool_calls
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "assistant_name": self.assistant_name,
            "content": self.content,
            "tool_calls": self.tool_calls
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistantUIMessage":
        """从字典创建实例"""
        base_data = {
            "message_id": data.get("message_id"),
            "metadata": data.get("metadata", {})
        }

        # 提取时间戳
        metadata = base_data["metadata"]
        timestamp_str = metadata.pop("timestamp", None)
        if timestamp_str:
            base_data["timestamp"] = datetime.fromisoformat(timestamp_str)

        # Remove message_type and display_content from base_data since they're set by constructor
        message_type = data.get("message_type")
        display_content = data.get("display_content")

        return cls(
            content=data.get("content", ""),
            assistant_name=data.get("assistant_name"),
            tool_calls=data.get("tool_calls", []),
            **base_data
        )


class SystemUIMessage(BaseUIMessage):
    """系统UI消息"""
    
    def __init__(
        self,
        content: str,
        level: str = "info",  # info, warning, error
        **kwargs
    ):
        super().__init__(
            message_type="system",
            display_content=content,
            **kwargs
        )
        self._content = content
        self._level = level
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def level(self) -> str:
        return self._level
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "content": self.content,
            "level": self.level
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SystemUIMessage":
        """从字典创建实例"""
        base_data = {
            "message_id": data.get("message_id"),
            "metadata": data.get("metadata", {})
        }

        # 提取时间戳
        metadata = base_data["metadata"]
        timestamp_str = metadata.pop("timestamp", None)
        if timestamp_str:
            base_data["timestamp"] = datetime.fromisoformat(timestamp_str)

        # Remove message_type and display_content from base_data since they're set by constructor
        message_type = data.get("message_type")
        display_content = data.get("display_content")

        return cls(
            content=data.get("content", ""),
            level=data.get("level", "info"),
            **base_data
        )


class ToolUIMessage(BaseUIMessage):
    """工具UI消息"""
    
    def __init__(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool = True,
        **kwargs
    ):
        content = f"工具调用: {tool_name}"
        if not success:
            content += " (失败)"
        
        super().__init__(
            message_type="tool",
            display_content=content,
            **kwargs
        )
        self._tool_name = tool_name
        self._tool_input = tool_input
        self._tool_output = tool_output
        self._success = success
    
    @property
    def tool_name(self) -> str:
        return self._tool_name
    
    @property
    def tool_input(self) -> Dict[str, Any]:
        return self._tool_input
    
    @property
    def tool_output(self) -> Any:
        return self._tool_output
    
    @property
    def success(self) -> bool:
        return self._success
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "tool_output": self.tool_output,
            "success": self.success
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolUIMessage":
        """从字典创建实例"""
        base_data = {
            "message_id": data.get("message_id"),
            "metadata": data.get("metadata", {})
        }

        # 提取时间戳
        metadata = base_data["metadata"]
        timestamp_str = metadata.pop("timestamp", None)
        if timestamp_str:
            base_data["timestamp"] = datetime.fromisoformat(timestamp_str)

        # Remove message_type and display_content from base_data since they're set by constructor
        message_type = data.get("message_type")
        display_content = data.get("display_content")

        return cls(
            tool_name=data.get("tool_name", ""),
            tool_input=data.get("tool_input", {}),
            tool_output=data.get("tool_output"),
            success=data.get("success", True),
            **base_data
        )


class WorkflowUIMessage(BaseUIMessage):
    """工作流UI消息"""
    
    def __init__(
        self,
        content: str,
        workflow_name: Optional[str] = None,
        node_name: Optional[str] = None,
        status: str = "info",  # info, running, success, error
        **kwargs
    ):
        super().__init__(
            message_type="workflow",
            display_content=content,
            **kwargs
        )
        self._content = content
        self._workflow_name = workflow_name
        self._node_name = node_name
        self._status = status
    
    @property
    def content(self) -> str:
        return self._content
    
    @property
    def workflow_name(self) -> Optional[str]:
        return self._workflow_name
    
    @property
    def node_name(self) -> Optional[str]:
        return self._node_name
    
    @property
    def status(self) -> str:
        return self._status
    
    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "content": self.content,
            "workflow_name": self.workflow_name,
            "node_name": self.node_name,
            "status": self.status
        })
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkflowUIMessage":
        """从字典创建实例"""
        base_data = {
            "message_id": data.get("message_id"),
            "metadata": data.get("metadata", {})
        }

        # 提取时间戳
        metadata = base_data["metadata"]
        timestamp_str = metadata.pop("timestamp", None)
        if timestamp_str:
            base_data["timestamp"] = datetime.fromisoformat(timestamp_str)

        # Remove message_type and display_content from base_data since they're set by constructor
        message_type = data.get("message_type")
        display_content = data.get("display_content")

        return cls(
            content=data.get("content", ""),
            workflow_name=data.get("workflow_name"),
            node_name=data.get("node_name"),
            status=data.get("status", "info"),
            **base_data
        )