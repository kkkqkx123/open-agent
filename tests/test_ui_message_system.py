"""UI消息系统测试

测试UI消息系统的基本功能，包括消息创建、转换、管理等。
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.interfaces.ui.messages import IUIMessage
from src.adapters.ui.messages import (
    BaseUIMessage,
    UserUIMessage,
    AssistantUIMessage,
    SystemUIMessage,
    ToolUIMessage,
    WorkflowUIMessage
)
from src.adapters.ui.message_adapters import LLMMessageAdapter, GraphMessageAdapter
from src.adapters.ui.message_manager import UIMessageManager, DefaultUIMessageRenderer
from src.infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage, ToolMessage


class TestUIMessages:
    """测试UI消息类"""
    
    def test_base_ui_message(self):
        """测试基础UI消息"""
        message = BaseUIMessage(
            message_type="test",
            display_content="测试内容",
            metadata={"key": "value"}
        )
        
        assert message.message_id is not None
        assert message.message_type == "test"
        assert message.display_content == "测试内容"
        assert "key" in message.metadata
        assert "timestamp" in message.metadata
        
        # 测试序列化
        data = message.to_dict()
        assert data["message_type"] == "test"
        assert data["display_content"] == "测试内容"
        
        # 测试反序列化
        restored = BaseUIMessage.from_dict(data)
        assert restored.message_type == "test"
        assert restored.display_content == "测试内容"
    
    def test_user_ui_message(self):
        """测试用户UI消息"""
        message = UserUIMessage(
            content="用户输入",
            user_name="测试用户"
        )
        
        assert message.message_type == "user"
        assert message.content == "用户输入"
        assert message.user_name == "测试用户"
        assert message.display_content == "用户输入"
        
        # 测试序列化
        data = message.to_dict()
        assert data["user_name"] == "测试用户"
        assert data["content"] == "用户输入"
        
        # 测试反序列化
        restored = UserUIMessage.from_dict(data)
        assert restored.user_name == "测试用户"
        assert restored.content == "用户输入"
    
    def test_assistant_ui_message(self):
        """测试助手UI消息"""
        tool_calls = [
            {"name": "test_tool", "args": {"param": "value"}}
        ]
        message = AssistantUIMessage(
            content="助手回复",
            assistant_name="测试助手",
            tool_calls=tool_calls
        )
        
        assert message.message_type == "assistant"
        assert message.content == "助手回复"
        assert message.assistant_name == "测试助手"
        assert message.tool_calls == tool_calls
        
        # 测试序列化
        data = message.to_dict()
        assert data["assistant_name"] == "测试助手"
        assert data["tool_calls"] == tool_calls
        
        # 测试反序列化
        restored = AssistantUIMessage.from_dict(data)
        assert restored.assistant_name == "测试助手"
        assert restored.tool_calls == tool_calls
    
    def test_system_ui_message(self):
        """测试系统UI消息"""
        message = SystemUIMessage(
            content="系统通知",
            level="warning"
        )
        
        assert message.message_type == "system"
        assert message.content == "系统通知"
        assert message.level == "warning"
        
        # 测试序列化
        data = message.to_dict()
        assert data["level"] == "warning"
        
        # 测试反序列化
        restored = SystemUIMessage.from_dict(data)
        assert restored.level == "warning"
    
    def test_tool_ui_message(self):
        """测试工具UI消息"""
        tool_input = {"param": "value"}
        message = ToolUIMessage(
            tool_name="测试工具",
            tool_input=tool_input,
            tool_output="执行结果",
            success=True
        )
        
        assert message.message_type == "tool"
        assert message.tool_name == "测试工具"
        assert message.tool_input == tool_input
        assert message.tool_output == "执行结果"
        assert message.success is True
        
        # 测试序列化
        data = message.to_dict()
        assert data["tool_name"] == "测试工具"
        assert data["success"] is True
        
        # 测试反序列化
        restored = ToolUIMessage.from_dict(data)
        assert restored.tool_name == "测试工具"
        assert restored.success is True
    
    def test_workflow_ui_message(self):
        """测试工作流UI消息"""
        message = WorkflowUIMessage(
            content="工作流执行",
            workflow_name="测试工作流",
            node_name="测试节点",
            status="running"
        )
        
        assert message.message_type == "workflow"
        assert message.content == "工作流执行"
        assert message.workflow_name == "测试工作流"
        assert message.node_name == "测试节点"
        assert message.status == "running"
        
        # 测试序列化
        data = message.to_dict()
        assert data["workflow_name"] == "测试工作流"
        assert data["status"] == "running"
        
        # 测试反序列化
        restored = WorkflowUIMessage.from_dict(data)
        assert restored.workflow_name == "测试工作流"
        assert restored.status == "running"


class TestMessageAdapters:
    """测试消息适配器"""
    
    def test_llm_message_adapter_to_ui(self):
        """测试LLM消息适配器转换为UI消息"""
        adapter = LLMMessageAdapter()
        
        # 测试HumanMessage转换
        human_msg = HumanMessage(content="用户消息")
        ui_msg = adapter.to_ui_message(human_msg)
        assert isinstance(ui_msg, UserUIMessage)
        assert ui_msg.content == "用户消息"
        
        # 测试AIMessage转换（带工具调用）
        tool_calls = [
            {"name": "test_tool", "args": {"param": "value"}, "id": "call_123"}
        ]
        ai_msg = AIMessage(content="AI回复", tool_calls=tool_calls)
        ui_msg = adapter.to_ui_message(ai_msg)
        assert isinstance(ui_msg, AssistantUIMessage)
        assert ui_msg.content == "AI回复"
        assert ui_msg.tool_calls == tool_calls
        
        # 测试AIMessage转换（不带工具调用）
        ai_msg_no_tools = AIMessage(content="AI回复，无工具调用")
        ui_msg_no_tools = adapter.to_ui_message(ai_msg_no_tools)
        assert isinstance(ui_msg_no_tools, AssistantUIMessage)
        assert ui_msg_no_tools.content == "AI回复，无工具调用"
        assert ui_msg_no_tools.tool_calls == []
        
        # 测试SystemMessage转换
        sys_msg = SystemMessage(content="系统消息")
        ui_msg = adapter.to_ui_message(sys_msg)
        assert isinstance(ui_msg, SystemUIMessage)
        assert ui_msg.content == "系统消息"
        
        # 测试ToolMessage转换
        tool_msg = ToolMessage(
            content="工具结果",
            tool_call_id="call_123"
        )
        ui_msg = adapter.to_ui_message(tool_msg)
        assert isinstance(ui_msg, ToolUIMessage)
        # ToolMessage 现在需要通过 tool_call_id 来识别工具
    
    def test_llm_message_adapter_from_ui(self):
        """测试LLM消息适配器从UI消息转换"""
        adapter = LLMMessageAdapter()
        
        # 测试UserUIMessage转换
        user_ui = UserUIMessage(content="用户输入")
        internal_msg = adapter.from_ui_message(user_ui)
        assert isinstance(internal_msg, HumanMessage)
        assert internal_msg.get_text_content() == "用户输入"
        
        # 测试AssistantUIMessage转换（带工具调用）
        tool_calls = [
            {"name": "test_tool", "args": {"param": "value"}}
        ]
        assistant_ui = AssistantUIMessage(content="助手回复", tool_calls=tool_calls)
        internal_msg = adapter.from_ui_message(assistant_ui)
        assert isinstance(internal_msg, AIMessage)
        assert internal_msg.get_text_content() == "助手回复"
        assert internal_msg.has_tool_calls() == True
        assert len(internal_msg.get_tool_calls()) == 1
        
        # 测试AssistantUIMessage转换（不带工具调用）
        assistant_ui_no_tools = AssistantUIMessage(content="助手回复，无工具调用")
        internal_msg_no_tools = adapter.from_ui_message(assistant_ui_no_tools)
        assert isinstance(internal_msg_no_tools, AIMessage)
        assert internal_msg_no_tools.get_text_content() == "助手回复，无工具调用"
        assert internal_msg_no_tools.has_tool_calls() == False
        
        # 测试SystemUIMessage转换
        system_ui = SystemUIMessage(content="系统通知")
        internal_msg = adapter.from_ui_message(system_ui)
        assert isinstance(internal_msg, SystemMessage)
        assert internal_msg.get_text_content() == "系统通知"
    
    def test_graph_message_adapter(self):
        """测试图消息适配器"""
        adapter = GraphMessageAdapter()
        
        # 创建模拟图消息
        class MockGraphMessage:
            def __init__(self, message_type, content, metadata=None):
                self.message_type = message_type
                self.content = content
                self.metadata = metadata or {}
        
        # 测试系统消息转换
        graph_msg = MockGraphMessage("system", "系统通知")
        ui_msg = adapter.to_ui_message(graph_msg)
        assert isinstance(ui_msg, SystemUIMessage)
        assert ui_msg.content == "系统通知"
        
        # 测试错误消息转换
        error_msg = MockGraphMessage("error", "错误信息")
        ui_msg = adapter.to_ui_message(error_msg)
        assert isinstance(ui_msg, SystemUIMessage)
        assert ui_msg.level == "error"
        
        # 测试UI消息转换回图消息
        ui_msg = SystemUIMessage(content="测试内容")
        graph_msg = adapter.from_ui_message(ui_msg)
        assert graph_msg.message_type == "ui_event"
        assert graph_msg.content["action"] == "system"


class TestUIMessageManager:
    """测试UI消息管理器"""
    
    def test_message_manager_basic_operations(self):
        """测试消息管理器基本操作"""
        manager = UIMessageManager()
        
        # 测试添加消息
        message = UserUIMessage(content="测试消息")
        manager.add_message(message)
        
        # 测试获取消息
        retrieved = manager.get_message(message.message_id)
        assert retrieved is not None
        assert retrieved.display_content == "测试消息"
        
        # 测试获取所有消息
        all_messages = manager.get_all_messages()
        assert len(all_messages) == 1
        assert all_messages[0].message_id == message.message_id
        
        # 测试按类型获取消息
        user_messages = manager.get_messages_by_type("user")
        assert len(user_messages) == 1
        assert user_messages[0].message_type == "user"
        
        # 测试移除消息
        removed = manager.remove_message(message.message_id)
        assert removed is True
        
        # 验证消息已移除
        retrieved = manager.get_message(message.message_id)
        assert retrieved is None
    
    def test_message_manager_conversion(self):
        """测试消息管理器转换功能"""
        manager = UIMessageManager()
        
        # 测试LLM消息转换
        human_msg = HumanMessage(content="用户消息")
        ui_msg = manager.convert_to_ui_message(human_msg)
        assert ui_msg is not None
        assert isinstance(ui_msg, UserUIMessage)
        assert ui_msg.content == "用户消息"
        
        # 测试UI消息转换回LLM消息
        internal_msg = manager.convert_from_ui_message(ui_msg, "human")
        assert internal_msg is not None
        assert isinstance(internal_msg, HumanMessage)
        assert internal_msg.get_text_content() == "用户消息"
    
    def test_message_manager_rendering(self):
        """测试消息管理器渲染功能"""
        manager = UIMessageManager()
        renderer = DefaultUIMessageRenderer()
        
        # 注册渲染器
        manager.register_renderer("user", renderer)
        
        # 测试渲染
        message = UserUIMessage(content="测试消息")
        rendered = manager.render_message(message)
        assert "测试消息" in rendered
        assert "[用户]" in rendered


class TestDefaultRenderer:
    """测试默认渲染器"""
    
    def test_renderer_user_message(self):
        """测试渲染用户消息"""
        renderer = DefaultUIMessageRenderer()
        message = UserUIMessage(content="用户输入", user_name="测试用户")
        
        rendered = renderer.render(message)
        assert "[测试用户]" in rendered
        assert "用户输入" in rendered
    
    def test_renderer_assistant_message(self):
        """测试渲染助手消息"""
        renderer = DefaultUIMessageRenderer()
        message = AssistantUIMessage(content="助手回复", assistant_name="测试助手")
        
        rendered = renderer.render(message)
        assert "[测试助手]" in rendered
        assert "助手回复" in rendered
    
    def test_renderer_system_message(self):
        """测试渲染系统消息"""
        renderer = DefaultUIMessageRenderer()
        message = SystemUIMessage(content="系统通知", level="warning")
        
        rendered = renderer.render(message)
        assert "[系统-WARNING]" in rendered
        assert "系统通知" in rendered
    
    def test_renderer_tool_message(self):
        """测试渲染工具消息"""
        renderer = DefaultUIMessageRenderer()
        message = ToolUIMessage(
            tool_name="测试工具",
            tool_input={"param": "value"},
            tool_output="结果",
            success=True
        )
        
        rendered = renderer.render(message)
        assert "[工具-测试工具-成功]" in rendered
    
    def test_renderer_workflow_message(self):
        """测试渲染工作流消息"""
        renderer = DefaultUIMessageRenderer()
        message = WorkflowUIMessage(
            content="工作流执行",
            workflow_name="测试工作流",
            node_name="测试节点",
            status="running"
        )
        
        rendered = renderer.render(message)
        assert "[工作流-测试工作流-测试节点-RUNNING]" in rendered


if __name__ == "__main__":
    pytest.main([__file__])