"""消息适配器单元测试"""

import pytest
from datetime import datetime

from src.infrastructure.llm.models import LLMMessage, MessageRole
from src.infrastructure.graph.states import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage, GraphHumanMessage, GraphAIMessage, GraphSystemMessage, GraphToolMessage
from src.infrastructure.graph.adapters.message_adapter import MessageAdapter


class TestMessageAdapter:
    """消息适配器测试"""

    @pytest.fixture
    def adapter(self):
        """创建消息适配器实例"""
        return MessageAdapter()

    def test_to_graph_message_user(self, adapter):
        """测试转换域层用户消息为图系统消息"""
        # 创建域层用户消息
        domain_message = LLMMessage(
            role=MessageRole.USER,
            content="用户消息内容",
            timestamp=datetime.now()
        )
        
        # 转换
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证
        assert isinstance(graph_message, HumanMessage)
        assert graph_message.content == "用户消息内容"

    def test_to_graph_message_assistant(self, adapter):
        """测试转换域层助手消息为图系统消息"""
        # 创建域层助手消息
        domain_message = LLMMessage(
            role=MessageRole.ASSISTANT,
            content="助手消息内容",
            timestamp=datetime.now()
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        assert isinstance(graph_message, AIMessage)
        assert graph_message.content == "助手消息内容"

    def test_to_graph_message_system(self, adapter):
        """测试转换域层系统消息为图系统消息"""
        # 创建域层系统消息
        domain_message = LLMMessage(
            role=MessageRole.SYSTEM,
            content="系统消息内容",
            timestamp=datetime.now()
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        assert isinstance(graph_message, SystemMessage)
        assert graph_message.content == "系统消息内容"

    def test_to_graph_message_tool(self, adapter):
        """测试转换域层工具消息为图系统消息"""
        # 创建域层工具消息
        domain_message = LLMMessage(
            content="工具消息内容",
            role=MessageRole.TOOL,
            timestamp=datetime.now(),
            metadata={"tool_call_id": "123"}
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证
        assert isinstance(graph_message, ToolMessage)
        assert graph_message.content == "工具消息内容"

    def test_from_graph_message_human(self, adapter):
        """测试转换图系统用户消息为域层消息"""
        # 创建图系统用户消息
        graph_message = HumanMessage(content="用户消息")
        
        # 转换
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, LLMMessage)
        assert domain_message.content == "用户消息"
        assert domain_message.role == MessageRole.USER

    def test_from_graph_message_ai(self, adapter):
        """测试转换图系统AI消息为域层消息"""
        # 创建图系统AI消息
        graph_message = AIMessage(content="助手回复")
        
        # 转换
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, LLMMessage)
        assert domain_message.content == "助手回复"
        assert domain_message.role == MessageRole.ASSISTANT

    def test_from_graph_message_system(self, adapter):
        """测试转换图系统系统消息为域层消息"""
        # 创建图系统系统消息
        graph_message = SystemMessage(content="系统指令")
        
        # 转换
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, LLMMessage)
        assert domain_message.content == "系统指令"
        assert domain_message.role == MessageRole.SYSTEM

    def test_from_graph_message_tool(self, adapter):
        """测试转换图系统工具消息为域层消息"""
        # 创建图系统工具消息
        graph_message = ToolMessage(content="工具结果", tool_call_id="123")
        
        # 转换
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, LLMMessage)
        assert domain_message.content == "工具结果"
        assert domain_message.role == MessageRole.TOOL
        assert domain_message.metadata.get("tool_call_id") == "123"

    def test_batch_message_conversion(self, adapter):
        """测试批量消息转换"""
        # 创建域层消息列表
        domain_messages = [
            LLMMessage(content="消息1", role=MessageRole.USER),
            LLMMessage(content="消息2", role=MessageRole.ASSISTANT),
            LLMMessage(content="消息3", role=MessageRole.SYSTEM),
            LLMMessage(content="消息4", role=MessageRole.TOOL, metadata={"tool_call_id": "123"})
        ]
        
        # 批量转换为图系统消息
        graph_messages = adapter.to_graph_messages(domain_messages)
        
        # 验证转换结果
        assert len(graph_messages) == 4
        assert isinstance(graph_messages[0], HumanMessage)
        assert isinstance(graph_messages[1], AIMessage)
        assert isinstance(graph_messages[2], SystemMessage)
        assert isinstance(graph_messages[3], ToolMessage)
        
        # 批量转换回域消息
        converted_back = adapter.from_graph_messages(graph_messages)
        
        # 验证转换一致性
        assert len(converted_back) == 4
        assert converted_back[0].role == "user"
        assert converted_back[1].role == "assistant"
        assert converted_back[2].role == "system"
        assert converted_back[3].role == "tool"
        assert converted_back[3].metadata.get("tool_call_id") == "123"

    def test_extract_tool_calls(self):
        """测试提取工具调用"""
        adapter = MessageAdapter()
        
        # 创建包含工具调用的消息
        domain_message = LLMMessage(
            content="调用工具",
            role=MessageRole.ASSISTANT,
            metadata={
                "tool_calls": [
                    {"name": "calculator", "args": {"expression": "2+2"}},
                    {"name": "search", "args": {"query": "test"}}
                ]
            }
        )
        
        # 提取工具调用
        tool_calls = adapter.extract_tool_calls(domain_message)
        
        # 验证提取结果
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "calculator"
        assert tool_calls[1]["name"] == "search"

    def test_add_tool_calls_to_message(self):
        """测试添加工具调用到消息"""
        adapter = MessageAdapter()
        
        # 创建消息
        domain_message = LLMMessage(
            content="调用工具",
            role=MessageRole.ASSISTANT
        )
        
        # 添加工具调用
        tool_calls = [
            {"name": "calculator", "args": {"expression": "2+2"}}
        ]
        updated_message = adapter.add_tool_calls_to_message(domain_message, tool_calls)
        
        # 验证结果 - 应该同时更新新属性和 metadata
        assert updated_message.tool_calls == tool_calls
        assert updated_message.metadata["tool_calls"] == tool_calls

    def test_create_message_factory_methods(self):
        """测试消息创建工厂方法"""
        adapter = MessageAdapter()
        
        # 测试创建系统消息
        system_msg = adapter.create_system_message("系统消息")
        assert system_msg.role == "system"
        assert system_msg.content == "系统消息"
        
        # 测试创建用户消息
        user_msg = adapter.create_user_message("用户消息")
        assert user_msg.role == "user"
        assert user_msg.content == "用户消息"
        
        # 测试创建助手消息
        assistant_msg = adapter.create_assistant_message("助手消息")
        assert assistant_msg.role == "assistant"
        assert assistant_msg.content == "助手消息"
        
        # 测试创建工具消息
        tool_msg = adapter.create_tool_message("工具结果", "call-123")
        assert tool_msg.role == "tool"
        assert tool_msg.content == "工具结果"
        assert tool_msg.metadata["tool_call_id"] == "call-123"
    
    def test_extract_tool_calls_prefer_new_property(self):
        """测试优先使用新的 tool_calls 属性"""
        adapter = MessageAdapter()
        
        # 创建同时有新属性和 metadata 的消息
        domain_message = LLMMessage(
            content="调用工具",
            role=MessageRole.ASSISTANT,
            tool_calls=[{"name": "new_tool", "arguments": {"param": "value"}}],
            metadata={"tool_calls": [{"name": "old_tool", "arguments": {"param": "old_value"}}]}
        )
        
        # 提取工具调用
        tool_calls = adapter.extract_tool_calls(domain_message)
        
        # 验证应该使用新属性
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "new_tool"
        assert tool_calls[0]["arguments"]["param"] == "value"
    
    def test_from_graph_message_with_langchain_tool_calls(self):
        """测试从 LangChain 消息转换（带有 tool_calls 属性）"""
        adapter = MessageAdapter()
        
        # 使用真正的 LangChain 消息类型
        from langchain_core.messages import AIMessage
        
        # 创建带有 tool_calls 的 AIMessage
        graph_message = AIMessage(
            content="I'll use a tool",
            additional_kwargs={
                "tool_calls": [
                    {
                        "id": "call_123",
                        "function": {
                            "name": "test_tool",
                            "arguments": '{"param": "value"}'
                        },
                        "type": "function"
                    }
                ]
            }
        )
        
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert domain_message.role == "assistant"
        assert domain_message.content == "I'll use a tool"
        assert domain_message.tool_calls is not None
        assert len(domain_message.tool_calls) == 1
        assert domain_message.tool_calls[0]["name"] == "test_tool"
        assert domain_message.tool_calls[0]["args"]["param"] == "value"
        assert domain_message.tool_calls[0]["id"] == "call_123"
        # 验证 metadata 中也有工具调用（向后兼容）
        assert "tool_calls" in domain_message.metadata
        assert domain_message.metadata["tool_calls"] == domain_message.tool_calls

    def test_from_graph_message_with_openai_format(self):
        """测试从 OpenAI 格式消息转换"""
        adapter = MessageAdapter()
        
        # 使用真正的 LangChain 消息类型
        from langchain_core.messages import AIMessage
        
        # 创建带有 OpenAI 格式 additional_kwargs 的 AIMessage
        graph_message = AIMessage(
            content="I'll use a tool",
            additional_kwargs={
                "tool_calls": [
                    {
                        "id": "call_456",
                        "function": {
                            "name": "openai_tool",
                            "arguments": '{"param": "openai_value"}'
                        },
                        "type": "function"
                    }
                ]
            }
        )
        
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert domain_message.role == "assistant"
        assert domain_message.content == "I'll use a tool"
        assert domain_message.tool_calls is not None
        assert len(domain_message.tool_calls) == 1
        assert domain_message.tool_calls[0]["name"] == "openai_tool"
        assert domain_message.tool_calls[0]["args"]["param"] == "openai_value"
        assert domain_message.tool_calls[0]["id"] == "call_456"
        assert domain_message.metadata["tool_calls"] == graph_message.additional_kwargs["tool_calls"]


if __name__ == "__main__":
    pytest.main([__file__])