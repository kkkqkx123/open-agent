"""消息系统测试

测试基础设施层消息系统的基本功能。
"""

import pytest
from datetime import datetime
from typing import Dict, Any

from src.infrastructure.messages import (
    BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage,
    MessageConverter, MessageFactory, LangChainCompatibilityAdapter
)
from src.core.llm.models import LLMMessage, MessageRole


class TestBaseMessage:
    """测试基础消息类"""
    
    def test_human_message_creation(self):
        """测试人类消息创建"""
        msg = HumanMessage(content="Hello, world!")
        assert msg.content == "Hello, world!"
        assert msg.type == "human"
        assert msg.additional_kwargs == {}
        assert msg.response_metadata == {}
    
    def test_ai_message_creation(self):
        """测试AI消息创建"""
        tool_calls = [{"id": "1", "name": "test_tool", "args": {}}]
        msg = AIMessage(content="I can help you!", tool_calls=tool_calls)
        assert msg.content == "I can help you!"
        assert msg.type == "ai"
        assert msg.tool_calls == tool_calls
    
    def test_system_message_creation(self):
        """测试系统消息创建"""
        msg = SystemMessage(content="You are a helpful assistant.")
        assert msg.content == "You are a helpful assistant."
        assert msg.type == "system"
    
    def test_tool_message_creation(self):
        """测试工具消息创建"""
        msg = ToolMessage(content="Result: 42", tool_call_id="call_123")
        assert msg.content == "Result: 42"
        assert msg.type == "tool"
        assert msg.tool_call_id == "call_123"
    
    def test_message_serialization(self):
        """测试消息序列化"""
        msg = HumanMessage(content="Test", name="user", id="msg_1")
        data = msg.to_dict()
        
        assert data["content"] == "Test"
        assert data["type"] == "human"
        assert data["name"] == "user"
        assert data["id"] == "msg_1"
        assert "timestamp" in data
    
    def test_message_deserialization(self):
        """测试消息反序列化"""
        data = {
            "content": "Test",
            "type": "human",
            "name": "user",
            "id": "msg_1",
            "additional_kwargs": {},
            "response_metadata": {}
        }
        
        msg = HumanMessage.from_dict(data)
        assert msg.content == "Test"
        assert msg.type == "human"
        assert msg.name == "user"
        assert msg.id == "msg_1"


class TestMessageConverter:
    """测试消息转换器"""
    
    def test_llm_message_to_base(self):
        """测试LLMMessage到基础消息的转换"""
        llm_msg = LLMMessage(
            role=MessageRole.USER,
            content="Hello",
            name="user"
        )
        
        converter = MessageConverter()
        base_msg = converter.to_base_message(llm_msg)
        
        assert isinstance(base_msg, HumanMessage)
        assert base_msg.content == "Hello"
        assert base_msg.name == "user"
    
    def test_base_message_to_llm(self):
        """测试基础消息到LLMMessage的转换"""
        base_msg = HumanMessage(content="Hello", name="user")
        
        converter = MessageConverter()
        llm_msg = converter.from_base_message(base_msg)
        
        assert isinstance(llm_msg, LLMMessage)
        assert llm_msg.role == MessageRole.USER
        assert llm_msg.content == "Hello"
        assert llm_msg.name == "user"
    
    def test_dict_to_base_message(self):
        """测试字典到基础消息的转换"""
        data = {
            "content": "Hello",
            "type": "human",
            "name": "user"
        }
        
        converter = MessageConverter()
        base_msg = converter.to_base_message(data)
        
        assert isinstance(base_msg, HumanMessage)
        assert base_msg.content == "Hello"
        assert base_msg.name == "user"
    
    def test_batch_conversion(self):
        """测试批量转换"""
        messages = [
            {"content": "Hello", "type": "human"},
            {"content": "Hi there!", "type": "ai"}
        ]
        
        converter = MessageConverter()
        base_messages = converter.convert_message_list(messages)
        
        assert len(base_messages) == 2
        assert isinstance(base_messages[0], HumanMessage)
        assert isinstance(base_messages[1], AIMessage)


class TestMessageFactory:
    """测试消息工厂"""
    
    def test_create_human_message(self):
        """测试创建人类消息"""
        factory = MessageFactory()
        msg = factory.create_human_message("Hello")
        
        assert isinstance(msg, HumanMessage)
        assert msg.content == "Hello"
        assert msg.id is not None
    
    def test_create_ai_message(self):
        """测试创建AI消息"""
        factory = MessageFactory()
        msg = factory.create_ai_message("Hi there!")
        
        assert isinstance(msg, AIMessage)
        assert msg.content == "Hi there!"
        assert msg.id is not None
    
    def test_create_system_message(self):
        """测试创建系统消息"""
        factory = MessageFactory()
        msg = factory.create_system_message("You are helpful")
        
        assert isinstance(msg, SystemMessage)
        assert msg.content == "You are helpful"
        assert msg.id is not None
    
    def test_create_tool_message(self):
        """测试创建工具消息"""
        factory = MessageFactory()
        msg = factory.create_tool_message("Result: 42", "call_123")
        
        assert isinstance(msg, ToolMessage)
        assert msg.content == "Result: 42"
        assert msg.tool_call_id == "call_123"
        assert msg.id is not None
    
    def test_create_conversation_pair(self):
        """测试创建对话对"""
        factory = MessageFactory()
        human_msg, ai_msg = factory.create_conversation_pair("Hello", "Hi there!")
        
        assert isinstance(human_msg, HumanMessage)
        assert isinstance(ai_msg, AIMessage)
        assert human_msg.content == "Hello"
        assert ai_msg.content == "Hi there!"
    
    def test_default_metadata(self):
        """测试默认元数据"""
        default_meta = {"session_id": "test_session"}
        factory = MessageFactory(default_metadata=default_meta)
        
        msg = factory.create_human_message("Hello")
        assert msg.additional_kwargs["session_id"] == "test_session"


class TestMessageUtils:
    """测试消息工具函数"""
    
    def test_extract_text_from_messages(self):
        """测试从消息列表提取文本"""
        from src.infrastructure.messages.utils import MessageUtils
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            SystemMessage(content="You are helpful")
        ]
        
        text = MessageUtils.extract_text_from_messages(messages)
        assert "Hello" in text
        assert "Hi there!" in text
        assert "You are helpful" in text
    
    def test_filter_messages_by_type(self):
        """测试按类型过滤消息"""
        from src.infrastructure.messages.utils import MessageUtils
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?"),
            SystemMessage(content="You are helpful")
        ]
        
        human_messages = MessageUtils.filter_messages_by_type(messages, "human")
        assert len(human_messages) == 2
        assert all(msg.type == "human" for msg in human_messages)
    
    def test_count_messages_by_type(self):
        """测试统计消息类型"""
        from src.infrastructure.messages.utils import MessageUtils
        
        messages = [
            HumanMessage(content="Hello"),
            AIMessage(content="Hi there!"),
            HumanMessage(content="How are you?"),
            SystemMessage(content="You are helpful")
        ]
        
        counts = MessageUtils.count_messages_by_type(messages)
        assert counts["human"] == 2
        assert counts["ai"] == 1
        assert counts["system"] == 1
        assert counts["tool"] == 0


class TestCompatibilityAdapter:
    """测试兼容性适配器"""
    
    def test_is_langchain_available(self):
        """测试LangChain可用性检查"""
        result = LangChainCompatibilityAdapter.is_langchain_available()
        # 这个测试的结果取决于环境，我们只确保函数能正常调用
        assert isinstance(result, bool)
    
    def test_is_base_message(self):
        """测试基础消息检查"""
        msg = HumanMessage(content="Hello")
        assert LangChainCompatibilityAdapter.is_base_message(msg)
        
        not_msg = "not a message"
        assert not LangChainCompatibilityAdapter.is_base_message(not_msg)
    
    def test_auto_convert_base_message(self):
        """测试自动转换基础消息"""
        msg = HumanMessage(content="Hello")
        result = LangChainCompatibilityAdapter.auto_convert(msg)
        
        # 基础消息应该直接返回
        assert result is msg
    
    def test_auto_convert_non_message(self):
        """测试自动转换非消息对象"""
        not_msg = "not a message"
        result = LangChainCompatibilityAdapter.auto_convert(not_msg)
        
        # 非消息对象应该直接返回
        assert result is not_msg


if __name__ == "__main__":
    pytest.main([__file__])