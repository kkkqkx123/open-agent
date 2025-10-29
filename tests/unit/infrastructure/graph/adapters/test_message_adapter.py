"""消息适配器测试用例"""

import pytest
from datetime import datetime

from src.domain.agent.state import AgentMessage as DomainAgentMessage
from src.infrastructure.graph.state import HumanMessage, AIMessage, SystemMessage, ToolMessage, BaseMessage, LCHumanMessage, LCAIMessage, LCSystemMessage, LCToolMessage
from src.infrastructure.graph.adapters.message_adapter import MessageAdapter


class TestMessageAdapter:
    """消息适配器测试类"""
    
    def test_to_graph_message_user(self):
        """测试用户消息转换"""
        adapter = MessageAdapter()
        
        # 创建域层用户消息
        domain_message = DomainAgentMessage(
            content="用户消息内容",
            role="user",
            timestamp=datetime.now(),
            metadata={"key": "value"}
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            assert isinstance(graph_message, (LCHumanMessage, HumanMessage))
        else:
            assert isinstance(graph_message, HumanMessage)
        assert graph_message.content == "用户消息内容"
        assert graph_message.type == "human"
    
    def test_to_graph_message_assistant(self):
        """测试助手消息转换"""
        adapter = MessageAdapter()
        
        # 创建域层助手消息
        domain_message = DomainAgentMessage(
            content="助手消息内容",
            role="assistant",
            timestamp=datetime.now()
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            assert isinstance(graph_message, (LCAIMessage, AIMessage))
        else:
            assert isinstance(graph_message, AIMessage)
        assert graph_message.content == "助手消息内容"
        assert graph_message.type == "ai"
    
    def test_to_graph_message_system(self):
        """测试系统消息转换"""
        adapter = MessageAdapter()
        
        # 创建域层系统消息
        domain_message = DomainAgentMessage(
            content="系统消息内容",
            role="system",
            timestamp=datetime.now()
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            assert isinstance(graph_message, (LCSystemMessage, SystemMessage))
        else:
            assert isinstance(graph_message, SystemMessage)
        assert graph_message.content == "系统消息内容"
        assert graph_message.type == "system"
    
    def test_to_graph_message_tool(self):
        """测试工具消息转换"""
        adapter = MessageAdapter()
        
        # 创建域层工具消息
        domain_message = DomainAgentMessage(
            content="工具消息内容",
            role="tool",
            timestamp=datetime.now(),
            metadata={"tool_call_id": "test-123"}
        )
        
        # 转换为图消息
        graph_message = adapter.to_graph_message(domain_message)
        
        # 验证转换结果
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            assert isinstance(graph_message, (LCToolMessage, ToolMessage))
        else:
            assert isinstance(graph_message, ToolMessage)
        assert graph_message.content == "工具消息内容"
        assert graph_message.type == "tool"
        if hasattr(graph_message, 'tool_call_id'):
            assert graph_message.tool_call_id == "test-123"
    
    def test_from_graph_message_human(self):
        """测试从图消息转换回域消息 - 人类消息"""
        adapter = MessageAdapter()
        
        # 创建图人类消息
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            graph_message = LCHumanMessage(content="用户消息内容")
        else:
            graph_message = HumanMessage(content="用户消息内容")
        
        # 转换为域消息
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, DomainAgentMessage)
        assert domain_message.content == "用户消息内容"
        assert domain_message.role == "user"
        assert domain_message.metadata == {}
    
    def test_from_graph_message_ai(self):
        """测试从图消息转换回域消息 - AI消息"""
        adapter = MessageAdapter()
        
        # 创建图AI消息
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            graph_message = LCAIMessage(content="助手消息内容")
        else:
            graph_message = AIMessage(content="助手消息内容")
        
        # 转换为域消息
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, DomainAgentMessage)
        assert domain_message.content == "助手消息内容"
        assert domain_message.role == "assistant"
        assert domain_message.metadata == {}
    
    def test_from_graph_message_system(self):
        """测试从图消息转换回域消息 - 系统消息"""
        adapter = MessageAdapter()
        
        # 创建图系统消息
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            graph_message = LCSystemMessage(content="系统消息内容")
        else:
            graph_message = SystemMessage(content="系统消息内容")
        
        # 转换为域消息
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, DomainAgentMessage)
        assert domain_message.content == "系统消息内容"
        assert domain_message.role == "system"
        assert domain_message.metadata == {}
    
    def test_from_graph_message_tool(self):
        """测试从图消息转换回域消息 - 工具消息"""
        adapter = MessageAdapter()
        
        # 创建图工具消息
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            graph_message = LCToolMessage(content="工具消息内容", tool_call_id="test-456")
        else:
            graph_message = ToolMessage(content="工具消息内容", tool_call_id="test-456")
        
        # 转换为域消息
        domain_message = adapter.from_graph_message(graph_message)
        
        # 验证转换结果
        assert isinstance(domain_message, DomainAgentMessage)
        assert domain_message.content == "工具消息内容"
        assert domain_message.role == "tool"
        assert domain_message.metadata == {"tool_call_id": "test-456"}
    
    def test_batch_message_conversion(self):
        """测试批量消息转换"""
        adapter = MessageAdapter()
        
        # 创建域层消息列表
        domain_messages = [
            DomainAgentMessage(content="消息1", role="user"),
            DomainAgentMessage(content="消息2", role="assistant"),
            DomainAgentMessage(content="消息3", role="system"),
            DomainAgentMessage(content="消息4", role="tool", metadata={"tool_call_id": "123"})
        ]
        
        # 批量转换为图消息
        graph_messages = adapter.to_graph_messages(domain_messages)
        
        # 验证转换结果
        assert len(graph_messages) == 4
        from src.infrastructure.graph.state import LANGCHAIN_AVAILABLE
        if LANGCHAIN_AVAILABLE:
            assert isinstance(graph_messages[0], (LCHumanMessage, HumanMessage))
            assert isinstance(graph_messages[1], (LCAIMessage, AIMessage))
            assert isinstance(graph_messages[2], (LCSystemMessage, SystemMessage))
            assert isinstance(graph_messages[3], (LCToolMessage, ToolMessage))
        else:
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
        domain_message = DomainAgentMessage(
            content="调用工具",
            role="assistant",
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
        domain_message = DomainAgentMessage(
            content="调用工具",
            role="assistant"
        )
        
        # 添加工具调用
        tool_calls = [
            {"name": "calculator", "args": {"expression": "2+2"}}
        ]
        updated_message = adapter.add_tool_calls_to_message(domain_message, tool_calls)
        
        # 验证结果
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


if __name__ == "__main__":
    pytest.main([__file__])