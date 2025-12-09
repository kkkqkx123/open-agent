"""
测试工具格式化器功能
"""

import pytest
from typing import Dict, Any, List, Optional, Union, AsyncGenerator, Sequence
from unittest.mock import Mock

from src.infrastructure.tools.formatters import (
    FunctionCallingFormatter,
    JsonlFormatter,
    ToolFormatter,
)
from src.interfaces.tool.base import ITool
from src.interfaces.messages import IBaseMessage
from src.interfaces.llm import ILLMClient


class MockTool(ITool):
    """模拟工具类"""
    
    def __init__(self, name: str, description: str, schema: Dict[str, Any]):
        self._name = name
        self._description = description
        self._schema = schema
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters_schema(self) -> Dict[str, Any]:
        return self._schema
    
    def get_schema(self) -> Dict[str, Any]:
        return self._schema
    
    def execute(self, **kwargs: Any) -> Any:
        return {"result": "success"}
    
    async def execute_async(self, **kwargs: Any) -> Any:
        return {"result": "success"}
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return True
    
    def initialize_context(self, session_id: Optional[str] = None) -> Optional[str]:
        return None
    
    def cleanup_context(self) -> bool:
        return True
    
    def get_context_info(self) -> Optional[Dict[str, Any]]:
        return None


class MockLLMClient(ILLMClient):
    """模拟LLM客户端"""
    
    def __init__(self, config: Any) -> None:
        self.config = config
        self._supports_jsonl = True
    
    async def generate(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        return Mock()
    
    async def stream_generate(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        async def _generator() -> AsyncGenerator[str, None]:
            yield "test"
        return _generator()
    
    def supports_function_calling(self) -> bool:
        return False
    
    def supports_jsonl(self) -> bool:
        return self._supports_jsonl
    
    def get_model_info(self) -> Dict[str, Any]:
        return {"model": "test"}


class MockMessage(IBaseMessage):
    """模拟消息类"""
    
    def __init__(self, content: str):
        self._content = content
        self._additional_kwargs: Dict[str, Any] = {}
        self._response_metadata: Dict[str, Any] = {}
        self._name = None
        self._id = "test_id"
        self._timestamp = Mock()
        self._type = "human"
    
    @property
    def content(self) -> Union[str, List[Union[str, Dict[str, Any]]]]:
        return self._content
    
    @property
    def type(self) -> str:
        return self._type
    
    @property
    def additional_kwargs(self) -> Dict[str, Any]:
        return self._additional_kwargs
    
    @property
    def response_metadata(self) -> Dict[str, Any]:
        return self._response_metadata
    
    @property
    def name(self) -> Optional[str]:
        return self._name
    
    @property
    def id(self) -> Optional[str]:
        return self._id
    
    @property
    def timestamp(self) -> Any:
        return self._timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {"content": self._content, "type": self._type}
    
    def get_text_content(self) -> str:
        return str(self._content)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "IBaseMessage":
        return cls(data.get("content", ""))
    
    def has_tool_calls(self) -> bool:
        return False
    
    def get_tool_calls(self) -> List[Dict[str, Any]]:
        return []
    
    def get_valid_tool_calls(self) -> List[Dict[str, Any]]:
        return []
    
    def get_invalid_tool_calls(self) -> List[Dict[str, Any]]:
        return []
    
    def add_tool_call(self, tool_call: Dict[str, Any]) -> None:
        pass


class TestJsonlFormatter:
    """测试JSONL格式化器"""
    
    def setup_method(self) -> None:
        """设置测试方法"""
        self.formatter = JsonlFormatter()
        self.tools = [
            MockTool("search", "搜索工具", {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"}
                },
                "required": ["query"]
            }),
            MockTool("calculate", "计算工具", {
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            })
        ]
    
    def test_format_for_llm(self) -> None:
        """测试JSONL格式化"""
        result = self.formatter.format_for_llm(self.tools)
        
        assert "prompt" in result
        assert "tools" in result
        assert len(result["tools"]) == 2
        
        # 检查提示词内容
        prompt = result["prompt"]
        assert "JSONL格式" in prompt
        assert "search" in prompt
        assert "calculate" in prompt
        
        # 检查工具模式
        tools = result["tools"]
        assert tools[0]["name"] == "search"
        assert tools[1]["name"] == "calculate"
    
    def test_detect_strategy_with_jsonl_support(self) -> None:
        """测试检测JSONL策略"""
        client = MockLLMClient({})
        strategy = self.formatter.detect_strategy(client)
        assert strategy == "jsonl"
    
    def test_detect_strategy_without_jsonl_support(self) -> None:
        """测试JSONL策略检测（总是返回jsonl）"""
        client = MockLLMClient({})
        # JSONL格式化器总是返回jsonl
        strategy = self.formatter.detect_strategy(client)
        assert strategy == "jsonl"
    
    def test_parse_single_jsonl_response(self) -> None:
        """测试解析单行JSONL响应"""
        response = MockMessage('{"name": "search", "parameters": {"query": "test"}}')
        tool_call = self.formatter.parse_llm_response(response)
        
        assert tool_call.name == "search"
        assert tool_call.arguments == {"query": "test"}
    
    def test_parse_multi_line_jsonl_response(self) -> None:
        """测试解析多行JSONL响应"""
        response = MockMessage('{"name": "search", "parameters": {"query": "test"}}\n{"name": "calculate", "parameters": {"expression": "1+1"}}')
        tool_call = self.formatter.parse_llm_response(response)
        
        # 应该返回第一个有效的工具调用
        assert tool_call.name == "search"
        assert tool_call.arguments == {"query": "test"}
    
    def test_parse_json_fallback(self) -> None:
        """测试JSON回退解析"""
        response = MockMessage('一些文本 {"name": "search", "parameters": {"query": "test"}} 更多文本')
        tool_call = self.formatter.parse_llm_response(response)
        
        assert tool_call.name == "search"
        assert tool_call.arguments == {"query": "test"}
    
    def test_parse_invalid_response(self) -> None:
        """测试解析无效响应"""
        response = MockMessage("无效的内容")
        with pytest.raises(ValueError, match="无法从响应中解析JSONL格式的工具调用"):
            self.formatter.parse_llm_response(response)


class TestToolFormatterWithJsonl:
    """测试支持JSONL的ToolFormatter"""
    
    def setup_method(self) -> None:
        """设置测试方法"""
        self.formatter = ToolFormatter()
        self.tools = [
            MockTool("search", "搜索工具", {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"}
                },
                "required": ["query"]
            })
        ]
    
    def test_detect_strategy_priority(self) -> None:
        """测试策略检测优先级"""
        # 测试Function Calling优先
        client = MockLLMClient({})
        # 使用 setattr 来设置方法属性
        object.__setattr__(client, 'supports_function_calling', lambda: True)
        strategy = self.formatter.detect_strategy(client)
        assert strategy == "function_calling"
        
        # 测试JSONL作为回退
        object.__setattr__(client, 'supports_function_calling', lambda: False)
        strategy = self.formatter.detect_strategy(client)
        assert strategy == "jsonl"
    
    def test_format_with_jsonl_strategy(self) -> None:
        """测试使用JSONL策略格式化"""
        result = self.formatter.format_for_llm_with_strategy(self.tools, "jsonl")
        
        assert "prompt" in result
        assert "tools" in result
        prompt = result["prompt"]
        assert "JSONL格式" in prompt
    
    def test_parse_with_jsonl_strategy(self) -> None:
        """测试使用JSONL策略解析"""
        response = MockMessage('{"name": "search", "parameters": {"query": "test"}}')
        tool_call = self.formatter.parse_llm_response_with_strategy(response, "jsonl")
        
        assert tool_call.name == "search"
        assert tool_call.arguments == {"query": "test"}


if __name__ == "__main__":
    pytest.main([__file__])