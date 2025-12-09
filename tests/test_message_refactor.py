"""测试消息处理重构

验证新的消息处理接口是否正常工作。
"""

import pytest
from src.interfaces.messages import IBaseMessage
from src.infrastructure.messages.types import AIMessage, HumanMessage, SystemMessage, ToolMessage


class TestMessageRefactor:
    """测试消息处理重构"""
    
    def test_ai_message_tool_calls(self):
        """测试 AI 消息的工具调用功能"""
        # 创建包含工具调用的 AI 消息
        tool_calls = [
            {"name": "search", "args": {"query": "test"}, "id": "call_1"},
            {"name": "calculate", "args": {"expression": "1+1"}, "id": "call_2"}
        ]
        
        ai_message = AIMessage(
            content="I will search and calculate for you.",
            tool_calls=tool_calls
        )
        
        # 测试接口方法
        assert ai_message.has_tool_calls() == True
        assert len(ai_message.get_tool_calls()) == 2
        assert len(ai_message.get_valid_tool_calls()) == 2
        assert len(ai_message.get_invalid_tool_calls()) == 0
        
        # 测试添加工具调用
        new_tool_call = {"name": "weather", "args": {"city": "Beijing"}, "id": "call_3"}
        ai_message.add_tool_call(new_tool_call)
        assert len(ai_message.get_tool_calls()) == 3
    
    def test_ai_message_with_invalid_tool_calls(self):
        """测试包含无效工具调用的 AI 消息"""
        tool_calls = [{"name": "search", "args": {"query": "test"}, "id": "call_1"}]
        invalid_tool_calls = [{"name": "invalid_tool", "args": {}, "id": "call_invalid"}]
        
        ai_message = AIMessage(
            content="I have both valid and invalid tool calls.",
            tool_calls=tool_calls,
            invalid_tool_calls=invalid_tool_calls
        )
        
        # 测试接口方法
        assert ai_message.has_tool_calls() == True
        assert len(ai_message.get_tool_calls()) == 2  # 总数
        assert len(ai_message.get_valid_tool_calls()) == 1  # 有效
        assert len(ai_message.get_invalid_tool_calls()) == 1  # 无效
    
    def test_human_message_no_tool_calls(self):
        """测试人类消息不包含工具调用"""
        human_message = HumanMessage(content="Please search for information.")
        
        # 测试接口方法
        assert human_message.has_tool_calls() == False
        assert len(human_message.get_tool_calls()) == 0
        assert len(human_message.get_valid_tool_calls()) == 0
        assert len(human_message.get_invalid_tool_calls()) == 0
        
        # 测试添加工具调用应该抛出异常
        with pytest.raises(NotImplementedError):
            human_message.add_tool_call({"name": "test", "args": {}})
    
    def test_system_message_no_tool_calls(self):
        """测试系统消息不包含工具调用"""
        system_message = SystemMessage(content="You are a helpful assistant.")
        
        # 测试接口方法
        assert system_message.has_tool_calls() == False
        assert len(system_message.get_tool_calls()) == 0
        assert len(system_message.get_valid_tool_calls()) == 0
        assert len(system_message.get_invalid_tool_calls()) == 0
        
        # 测试添加工具调用应该抛出异常
        with pytest.raises(NotImplementedError):
            system_message.add_tool_call({"name": "test", "args": {}})
    
    def test_tool_message_no_tool_calls(self):
        """测试工具消息不包含工具调用"""
        tool_message = ToolMessage(
            content="Search results: ...",
            tool_call_id="call_1"
        )
        
        # 测试接口方法
        assert tool_message.has_tool_calls() == False
        assert len(tool_message.get_tool_calls()) == 0
        assert len(tool_message.get_valid_tool_calls()) == 0
        assert len(tool_message.get_invalid_tool_calls()) == 0
        
        # 测试添加工具调用应该抛出异常
        with pytest.raises(NotImplementedError):
            tool_message.add_tool_call({"name": "test", "args": {}})
    
    def test_message_tool_accessor(self):
        """测试消息工具访问器"""
        from src.infrastructure.messages.accessor import MessageToolAccessor
        
        # 创建 AI 消息
        tool_calls = [
            {"name": "search", "args": {"query": "test"}, "id": "call_1"},
            {"name": "calculate", "args": {"expression": "1+1"}, "id": "call_2"}
        ]
        ai_message = AIMessage(content="I will search and calculate.", tool_calls=tool_calls)
        
        # 测试访问器方法
        assert MessageToolAccessor.has_tool_calls(ai_message) == True
        assert len(MessageToolAccessor.extract_tool_calls(ai_message)) == 2
        assert len(MessageToolAccessor.extract_valid_tool_calls(ai_message)) == 2
        assert len(MessageToolAccessor.extract_invalid_tool_calls(ai_message)) == 0
        assert MessageToolAccessor.get_tool_call_count(ai_message) == 2
        assert MessageToolAccessor.get_valid_tool_call_count(ai_message) == 2
        assert MessageToolAccessor.get_invalid_tool_call_count(ai_message) == 0
        
        # 测试工具名称提取
        tool_names = MessageToolAccessor.extract_tool_names(ai_message)
        assert "search" in tool_names
        assert "calculate" in tool_names
        
        # 测试按名称查找工具调用
        search_calls = MessageToolAccessor.get_tool_calls_with_name(ai_message, "search")
        assert len(search_calls) == 1
        assert search_calls[0]["name"] == "search"
        
        # 测试是否包含指定名称的工具调用
        assert MessageToolAccessor.has_tool_call_with_name(ai_message, "search") == True
        assert MessageToolAccessor.has_tool_call_with_name(ai_message, "nonexistent") == False
    
    def test_message_from_dict(self):
        """测试从字典创建消息"""
        # 测试 AI 消息
        ai_data = {
            "content": "I will search for you.",
            "type": "ai",
            "tool_calls": [{"name": "search", "args": {"query": "test"}, "id": "call_1"}],
            "additional_kwargs": {"key": "value"}
        }
        ai_message = AIMessage.from_dict(ai_data)
        assert ai_message.has_tool_calls() == True
        assert len(ai_message.get_tool_calls()) == 1
        
        # 测试人类消息
        human_data = {
            "content": "Hello",
            "type": "human",
            "additional_kwargs": {"key": "value"}
        }
        human_message = HumanMessage.from_dict(human_data)
        assert human_message.has_tool_calls() == False
        
        # 测试工具消息
        tool_data = {
            "content": "Result: ...",
            "type": "tool",
            "tool_call_id": "call_1",
            "additional_kwargs": {"key": "value"}
        }
        tool_message = ToolMessage.from_dict(tool_data)
        assert tool_message.has_tool_calls() == False
        assert tool_message.tool_call_id == "call_1"


if __name__ == "__main__":
    pytest.main([__file__])