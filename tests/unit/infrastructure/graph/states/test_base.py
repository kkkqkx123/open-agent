"""基础状态单元测试"""

import pytest
from typing import Any, List, Dict, Optional
from dataclasses import dataclass

from src.infrastructure.graph.states.base import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
    ToolMessage,
    MessageRole,
    BaseGraphState,
    create_base_state,
    create_message,
    adapt_langchain_message
)


class TestMessageClasses:
    """消息类测试"""

    def test_base_message(self) -> None:
        """测试基础消息"""
        message = BaseMessage(content="测试内容", type="test")
        assert message.content == "测试内容"
        assert message.type == "test"

    def test_base_message_with_kwargs(self) -> None:
        """测试基础消息（带额外参数）"""
        message = BaseMessage(content="测试内容", type="test", extra="额外参数")
        assert message.content == "测试内容"
        assert message.type == "test"
        assert getattr(message, "extra") == "额外参数"

    def test_human_message(self) -> None:
        """测试人类消息"""
        message = HumanMessage(content="人类消息")
        assert message.content == "人类消息"
        assert message.type == "human"

    def test_ai_message(self) -> None:
        """测试AI消息"""
        message = AIMessage(content="AI消息")
        assert message.content == "AI消息"
        assert message.type == "ai"

    def test_system_message(self) -> None:
        """测试系统消息"""
        message = SystemMessage(content="系统消息")
        assert message.content == "系统消息"
        assert message.type == "system"

    def test_tool_message(self) -> None:
        """测试工具消息"""
        message = ToolMessage(content="工具消息", tool_call_id="tool_123")
        assert message.content == "工具消息"
        assert message.type == "tool"
        assert message.tool_call_id == "tool_123"

    def test_message_role_constants(self) -> None:
        """测试消息角色常量"""
        assert MessageRole.HUMAN == "human"
        assert MessageRole.AI == "ai"
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.TOOL == "tool"


class TestStateFunctions:
    """状态函数测试"""

    def test_create_base_state_with_defaults(self) -> None:
        """测试创建基础状态（使用默认值）"""
        state = create_base_state()
        
        # 验证基本字段
        assert isinstance(state, dict)
        assert state["messages"] == []
        assert state["metadata"] == {}
        assert state["execution_context"] == {}
        assert state["current_step"] == "start"

    def test_create_base_state_with_custom_params(self) -> None:
        """测试创建基础状态（使用自定义参数）"""
        messages = [HumanMessage(content="测试消息")]
        metadata = {"key": "value"}
        execution_context = {"context_key": "context_value"}
        current_step = "test_step"
        
        state = create_base_state(
            messages=messages,
            metadata=metadata,
            execution_context=execution_context,
            current_step=current_step
        )
        
        # 验证自定义字段
        assert state["messages"] == messages
        assert state["metadata"] == metadata
        assert state["execution_context"] == execution_context
        assert state["current_step"] == current_step

    def test_create_message_human(self) -> None:
        """测试创建人类消息"""
        message = create_message(content="人类消息", role=MessageRole.HUMAN)
        assert isinstance(message, HumanMessage)
        assert message.content == "人类消息"

    def test_create_message_ai(self) -> None:
        """测试创建AI消息"""
        message = create_message(content="AI消息", role=MessageRole.AI)
        assert isinstance(message, AIMessage)
        assert message.content == "AI消息"

    def test_create_message_system(self) -> None:
        """测试创建系统消息"""
        message = create_message(content="系统消息", role=MessageRole.SYSTEM)
        assert isinstance(message, SystemMessage)
        assert message.content == "系统消息"

    def test_create_message_tool(self) -> None:
        """测试创建工具消息"""
        message = create_message(
            content="工具消息",
            role=MessageRole.TOOL,
            tool_call_id="tool_123"
        )
        assert isinstance(message, ToolMessage)
        assert message.content == "工具消息"
        assert message.tool_call_id == "tool_123"

    def test_create_message_custom_role(self) -> None:
        """测试创建自定义角色消息"""
        message = create_message(content="自定义消息", role="custom")
        assert isinstance(message, BaseMessage)
        assert message.content == "自定义消息"
        assert message.type == "custom"

    def test_adapt_langchain_message_with_content_and_type(self) -> None:
        """测试适配LangChain消息（有内容和类型）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {
            'content': '测试内容',
            'type': 'human'
        })()
        
        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, HumanMessage)
        assert adapted_message.content == "测试内容"

    def test_adapt_langchain_message_ai(self) -> None:
        """测试适配LangChain消息（AI消息）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {
            'content': 'AI响应',
            'type': 'ai'
        })()

        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, AIMessage)
        assert adapted_message.content == "AI响应"

    def test_adapt_langchain_message_system(self) -> None:
        """测试适配LangChain消息（系统消息）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {
            'content': '系统指令',
            'type': 'system'
        })()

        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, SystemMessage)
        assert adapted_message.content == "系统指令"

    def test_adapt_langchain_message_tool(self) -> None:
        """测试适配LangChain消息（工具消息）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {
            'content': '工具结果',
            'type': 'tool',
            'tool_call_id': 'tool_123'
        })()

        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, ToolMessage)
        assert adapted_message.content == "工具结果"
        assert adapted_message.tool_call_id == "tool_123"

    def test_adapt_langchain_message_custom_type(self) -> None:
        """测试适配LangChain消息（自定义类型）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {
            'content': '自定义内容',
            'type': 'custom'
        })()

        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, BaseMessage)
        assert adapted_message.content == "自定义内容"
        assert adapted_message.type == "custom"

    def test_adapt_langchain_message_without_attributes(self) -> None:
        """测试适配LangChain消息（无属性）"""
        # 创建模拟LangChain消息
        langchain_message = type('MockMessage', (), {})()

        adapted_message = adapt_langchain_message(langchain_message)
        assert isinstance(adapted_message, BaseMessage)
        assert adapted_message.content == str(langchain_message)
        assert adapted_message.type == "base"