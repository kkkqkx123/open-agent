"""测试JSONL和Structured Output格式化器的差异"""

import pytest
from unittest.mock import Mock

from src.infrastructure.tools.formatters.formatter import (
    JsonlFormatter, 
    StructuredOutputFormatter,
    FunctionCallingFormatter,
    ToolFormatter
)
from src.interfaces.tool.base import ToolCall
from src.infrastructure.messages import AIMessage


class TestJsonlVsStructuredOutput:
    """测试JSONL和Structured Output的差异"""

    @pytest.fixture
    def mock_tools(self):
        """模拟工具列表"""
        tools = []
        for i in range(3):
            tool = Mock()
            tool.name = f"tool_{i+1}"
            tool.description = f"测试工具{i+1}"
            tool.get_schema.return_value = {
                "type": "object",
                "properties": {
                    f"param_{i+1}": {"type": "string"}
                },
                "required": [f"param_{i+1}"]
            }
            tools.append(tool)
        return tools

    def test_structured_output_format(self, mock_tools):
        """测试Structured Output格式化"""
        formatter = StructuredOutputFormatter()
        result = formatter.format_for_llm(mock_tools)
        
        # 验证返回格式
        assert "prompt" in result
        prompt = result["prompt"]
        
        # 验证提示词包含单JSON格式
        assert "请按以下JSON格式调用工具" in prompt
        assert '"name": "工具名称"' in prompt
        assert '"parameters": {' in prompt
        
        # 验证不包含JSONL相关内容
        assert "JSONL" not in prompt
        assert "每行一个JSON对象" not in prompt

    def test_jsonl_format(self, mock_tools):
        """测试JSONL格式化"""
        formatter = JsonlFormatter()
        result = formatter.format_for_llm(mock_tools)
        
        # 验证返回格式
        assert "prompt" in result
        assert "tools" in result
        prompt = result["prompt"]
        
        # 验证提示词包含JSONL格式
        assert "JSONL格式调用工具" in prompt
        assert "每行一个JSON对象" in prompt
        assert '{"name": "工具名称", "parameters": {"参数1": "值1", "参数2": "值2"}}' in prompt
        
        # 验证包含工具schema
        assert len(result["tools"]) == 3
        assert result["tools"][0]["name"] == "tool_1"

    def test_structured_output_single_parsing(self):
        """测试Structured Output单工具调用解析"""
        formatter = StructuredOutputFormatter()
        
        # 创建单工具调用响应
        response = AIMessage(content='{"name": "tool_1", "parameters": {"param_1": "value1"}}')
        
        tool_call = formatter.parse_llm_response(response)
        
        assert tool_call.name == "tool_1"
        assert tool_call.arguments == {"param_1": "value1"}

    def test_jsonl_single_parsing(self):
        """测试JSONL单工具调用解析"""
        formatter = JsonlFormatter()
        
        # 创建单行JSONL响应
        response = AIMessage(content='{"name": "tool_1", "parameters": {"param_1": "value1"}}')
        
        tool_call = formatter.parse_llm_response(response)
        
        assert tool_call.name == "tool_1"
        assert tool_call.arguments == {"param_1": "value1"}

    def test_jsonl_batch_parsing(self):
        """测试JSONL批量工具调用解析"""
        formatter = JsonlFormatter()
        
        # 创建多行JSONL响应
        jsonl_content = '''{"name": "tool_1", "parameters": {"param_1": "value1"}}
{"name": "tool_2", "parameters": {"param_2": "value2"}}
{"name": "tool_3", "parameters": {"param_3": "value3"}}'''
        
        response = AIMessage(content=jsonl_content)
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        assert len(tool_calls) == 3
        assert tool_calls[0].name == "tool_1"
        assert tool_calls[1].name == "tool_2"
        assert tool_calls[2].name == "tool_3"
        assert tool_calls[0].arguments == {"param_1": "value1"}
        assert tool_calls[1].arguments == {"param_2": "value2"}
        assert tool_calls[2].arguments == {"param_3": "value3"}

    def test_jsonl_batch_parsing_with_empty_lines(self):
        """测试JSONL批量解析包含空行"""
        formatter = JsonlFormatter()
        
        # 创建包含空行的JSONL响应
        jsonl_content = '''{"name": "tool_1", "parameters": {"param_1": "value1"}}

{"name": "tool_2", "parameters": {"param_2": "value2"}}

'''
        
        response = AIMessage(content=jsonl_content)
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "tool_1"
        assert tool_calls[1].name == "tool_2"

    def test_jsonl_fallback_to_single_json(self):
        """测试JSONL回退到单JSON解析"""
        formatter = JsonlFormatter()
        
        # 创建单JSON响应（不是JSONL格式）
        response = AIMessage(content='{"name": "tool_1", "parameters": {"param_1": "value1"}}')
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "tool_1"

    def test_structured_output_batch_parsing(self):
        """测试Structured Output批量解析（只返回单工具）"""
        formatter = StructuredOutputFormatter()
        
        # 创建单工具调用响应
        response = AIMessage(content='{"name": "tool_1", "parameters": {"param_1": "value1"}}')
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        # StructuredOutput只支持单工具调用
        assert len(tool_calls) == 1
        assert tool_calls[0].name == "tool_1"

    def test_tool_formatter_batch_parsing(self):
        """测试ToolFormatter批量解析"""
        formatter = ToolFormatter()
        
        # 创建多行JSONL响应
        jsonl_content = '''{"name": "tool_1", "parameters": {"param_1": "value1"}}
{"name": "tool_2", "parameters": {"param_2": "value2"}}'''
        
        response = AIMessage(content=jsonl_content)
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "tool_1"
        assert tool_calls[1].name == "tool_2"

    def test_function_calling_batch_parsing(self):
        """测试Function Calling批量解析"""
        formatter = FunctionCallingFormatter()
        
        # 创建多工具调用响应
        response = AIMessage(content="dummy content")
        response.additional_kwargs = {
            "tool_calls": [
                {
                    "id": "call_1",
                    "function": {
                        "name": "tool_1",
                        "arguments": '{"param_1": "value1"}'
                    }
                },
                {
                    "id": "call_2", 
                    "function": {
                        "name": "tool_2",
                        "arguments": '{"param_2": "value2"}'
                    }
                }
            ]
        }
        
        tool_calls = formatter.parse_llm_response_batch(response)
        
        assert len(tool_calls) == 2
        assert tool_calls[0].name == "tool_1"
        assert tool_calls[1].name == "tool_2"
        assert tool_calls[0].call_id == "call_1"
        assert tool_calls[1].call_id == "call_2"

    def test_jsonl_vs_structured_output_key_differences(self, mock_tools):
        """测试JSONL和Structured Output的关键差异"""
        jsonl_formatter = JsonlFormatter()
        structured_formatter = StructuredOutputFormatter()
        
        jsonl_result = jsonl_formatter.format_for_llm(mock_tools)
        structured_result = structured_formatter.format_for_llm(mock_tools)
        
        # 差异1：JSONL包含tools schema，Structured Output不包含
        assert "tools" in jsonl_result
        assert "tools" not in structured_result
        
        # 差异2：提示词格式不同
        jsonl_prompt = jsonl_result["prompt"]
        structured_prompt = structured_result["prompt"]
        
        # JSONL强调多行格式
        assert "每行一个JSON对象" in jsonl_prompt
        assert "每行一个JSON对象" not in structured_prompt
        
        # Structured Output强调单JSON格式
        assert "请按以下JSON格式调用工具" in structured_prompt
        assert "JSONL格式" not in structured_prompt
        
        # 差异3：批量解析能力
        jsonl_content = '''{"name": "tool_1", "parameters": {"param_1": "value1"}}
{"name": "tool_2", "parameters": {"param_2": "value2"}}'''
        
        jsonl_response = AIMessage(content=jsonl_content)
        structured_response = AIMessage(content=jsonl_content)
        
        jsonl_tool_calls = jsonl_formatter.parse_llm_response_batch(jsonl_response)
        structured_tool_calls = structured_formatter.parse_llm_response_batch(structured_response)
        
        # JSONL能解析多个工具调用
        assert len(jsonl_tool_calls) == 2
        
        # Structured Output只能解析第一个工具调用
        assert len(structured_tool_calls) <= 1


if __name__ == "__main__":
    pytest.main([__file__])