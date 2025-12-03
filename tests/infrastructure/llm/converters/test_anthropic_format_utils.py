"""Anthropic格式转换工具测试

测试AnthropicFormatUtils类的各种功能。
"""

import pytest
from typing import Dict, Any, List, Sequence
from unittest.mock import Mock, patch

from src.infrastructure.llm.converters.anthropic_format_utils import AnthropicFormatUtils
from src.infrastructure.llm.converters.anthropic_validation_utils import AnthropicValidationError, AnthropicFormatError
from src.infrastructure.messages import HumanMessage, AIMessage, SystemMessage, ToolMessage


class TestAnthropicFormatUtils:
    """Anthropic格式转换工具测试类"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.format_utils = AnthropicFormatUtils()
    
    def test_get_provider_name(self) -> None:
        """测试获取提供商名称"""
        assert self.format_utils.get_provider_name() == "anthropic"
    
    def test_convert_request_basic(self) -> None:
        """测试基本请求转换"""
        messages = [
            HumanMessage(content="Hello, Claude!")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert result["model"] == "claude-sonnet-4-5"
        assert result["max_tokens"] == 1024
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"] == [{"type": "text", "text": "Hello, Claude!"}]
    
    def test_convert_request_with_system_message(self) -> None:
        """测试带系统消息的请求转换"""
        messages = [
            SystemMessage(content="You are a helpful assistant."),
            HumanMessage(content="Hello!")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert result["system"] == "You are a helpful assistant."
        assert len(result["messages"]) == 1  # 系统消息不包含在messages中
        assert result["messages"][0]["role"] == "user"
    
    def test_convert_request_with_tools(self) -> None:
        """测试带工具的请求转换"""
        messages = [
            HumanMessage(content="What's the weather?")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {"type": "string"}
                        },
                        "required": ["location"]
                    }
                }
            ]
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert "tools" in result
        assert len(result["tools"]) == 1
        assert result["tools"][0]["name"] == "get_weather"
        assert "input_schema" in result["tools"][0]
    
    def test_convert_request_with_tool_choice(self) -> None:
        """测试带工具选择的请求转换"""
        messages = [
            HumanMessage(content="Use the tool")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "tools": [
                {
                    "name": "test_tool",
                    "description": "Test tool",
                    "parameters": {"type": "object", "properties": {}}
                }
            ],
            "tool_choice": {"type": "tool", "name": "test_tool"}
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert "tool_choice" in result
        assert result["tool_choice"]["type"] == "tool"
        assert result["tool_choice"]["name"] == "test_tool"
    
    def test_convert_request_with_multimodal_content(self) -> None:
        """测试多模态内容转换"""
        messages = [
            HumanMessage(content=[
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": "base64_encoded_data"
                    }
                }
            ])
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert len(result["messages"][0]["content"]) == 2
        assert result["messages"][0]["content"][0]["type"] == "text"
        assert result["messages"][0]["content"][1]["type"] == "image"
    
    def test_convert_request_with_optional_params(self) -> None:
        """测试带可选参数的请求转换"""
        messages = [
            HumanMessage(content="Hello")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024,
            "temperature": 0.7,
            "top_p": 0.9,
            "top_k": 40,
            "stop_sequences": ["STOP", "END"],
            "metadata": {"user_id": "test_user"}
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert result["temperature"] == 0.7
        assert result["top_p"] == 0.9
        assert result["top_k"] == 40
        assert result["stop_sequences"] == ["STOP", "END"]
        assert result["metadata"]["user_id"] == "test_user"
    
    def test_convert_response_basic(self) -> None:
        """测试基本响应转换"""
        response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "Hello! How can I help you?"}
            ],
            "model": "claude-sonnet-4-5",
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": 10,
                "output_tokens": 25
            }
        }
        
        result = self.format_utils.convert_response(response)
        
        assert isinstance(result, AIMessage)
        assert result.content == "Hello! How can I help you?"
        assert result.additional_kwargs["stop_reason"] == "end_turn"
        assert result.additional_kwargs["usage"]["input_tokens"] == 10
    
    def test_convert_response_with_tool_calls(self) -> None:
        """测试带工具调用的响应转换"""
        response = {
            "id": "msg_123",
            "type": "message",
            "role": "assistant",
            "content": [
                {"type": "text", "text": "I'll check the weather for you."},
                {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "get_weather",
                    "input": {"location": "San Francisco"}
                }
            ],
            "model": "claude-sonnet-4-5",
            "stop_reason": "tool_use",
            "usage": {"input_tokens": 15, "output_tokens": 30}
        }
        
        result = self.format_utils.convert_response(response)
        
        assert isinstance(result, AIMessage)
        assert result.content == "I'll check the weather for you."
        assert result.tool_calls is not None
        assert len(result.tool_calls) == 1
        assert result.tool_calls[0]["function"]["name"] == "get_weather"
        assert result.tool_calls[0]["function"]["arguments"]["location"] == "San Francisco"
    
    def test_convert_stream_response(self) -> None:
        """测试流式响应转换"""
        events = [
            {
                "type": "message_start",
                "message": {
                    "id": "msg_123",
                    "type": "message",
                    "role": "assistant",
                    "content": [],
                    "model": "claude-sonnet-4-5",
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {"input_tokens": 10, "output_tokens": 0}
                }
            },
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "text", "text": ""}
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "text_delta", "text": "Hello"}
            },
            {
                "type": "content_block_stop",
                "index": 0
            },
            {
                "type": "message_delta",
                "delta": {"stop_reason": "end_turn"},
                "usage": {"output_tokens": 5}
            },
            {
                "type": "message_stop"
            }
        ]
        
        result = self.format_utils.convert_stream_response(events)
        
        assert isinstance(result, AIMessage)
        assert result.content == "Hello"
        assert result.additional_kwargs["stop_reason"] == "end_turn"
    
    def test_validate_request_valid(self) -> None:
        """测试有效请求验证"""
        messages = [
            HumanMessage(content="Hello")
        ]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        errors = self.format_utils.validate_request(messages, parameters)
        assert len(errors) == 0
    
    def test_validate_request_invalid(self) -> None:
        """测试无效请求验证"""
        messages = []
        parameters = {
            "max_tokens": -1,
            "temperature": 2.0
        }
        
        errors = self.format_utils.validate_request(messages, parameters)
        assert len(errors) > 0
        assert any("消息列表不能为空" in error for error in errors)
        assert any("max_tokens" in error for error in errors)
        assert any("temperature" in error for error in errors)
    
    def test_handle_api_error(self) -> None:
        """测试API错误处理"""
        error_response = {
            "error": {
                "type": "authentication_error",
                "message": "Invalid API key"
            }
        }
        
        result = self.format_utils.handle_api_error(error_response)
        
        assert "认证失败" in result
        assert "Invalid API key" in result
    
    def test_convert_request_validation_error(self) -> None:
        """测试请求转换验证错误"""
        messages = [HumanMessage(content="Hello")]
        parameters = {"max_tokens": -1}  # 无效参数
        
        with pytest.raises(AnthropicValidationError):
            self.format_utils.convert_request(messages, parameters)
    
    def test_convert_tool_message(self) -> None:
        """测试工具消息转换"""
        tool_message = ToolMessage(
            content="Weather is sunny",
            tool_call_id="toolu_123"
        )
        messages = [tool_message]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "user"
        assert result["messages"][0]["content"][0]["type"] == "tool_result"
        assert result["messages"][0]["content"][0]["tool_use_id"] == "toolu_123"
    
    def test_convert_ai_message_with_tool_calls(self) -> None:
        """测试带工具调用的AI消息转换"""
        ai_message = AIMessage(
            content="I'll use the tool",
            tool_calls=[
                {
                    "id": "toolu_123",
                    "type": "function",
                    "function": {
                        "name": "test_tool",
                        "arguments": {"param": "value"}
                    }
                }
            ]
        )
        messages = [ai_message]
        parameters = {
            "model": "claude-sonnet-4-5",
            "max_tokens": 1024
        }
        
        result = self.format_utils.convert_request(messages, parameters)
        
        assert len(result["messages"]) == 1
        assert result["messages"][0]["role"] == "assistant"
        assert len(result["messages"][0]["content"]) == 2
        assert result["messages"][0]["content"][0]["type"] == "text"
        assert result["messages"][0]["content"][1]["type"] == "tool_use"


class TestAnthropicMultimodalUtils:
    """Anthropic多模态工具测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.format_utils = AnthropicFormatUtils()
        self.multimodal_utils = self.format_utils.multimodal_utils
    
    def test_process_text_content(self) -> None:
        """测试文本内容处理"""
        content = "Hello, world!"
        result = self.multimodal_utils.process_content_to_anthropic_format(content)
        
        assert len(result) == 1
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "Hello, world!"
    
    def test_process_list_content(self) -> None:
        """测试列表内容处理"""
        content = [
            {"type": "text", "text": "Hello"},
            "world"
        ]
        result = self.multimodal_utils.process_content_to_anthropic_format(content)
        
        assert len(result) == 2
        assert result[0]["type"] == "text"
        assert result[0]["text"] == "Hello"
        assert result[1]["type"] == "text"
        assert result[1]["text"] == "world"
    
    def test_validate_image_content(self) -> None:
        """测试图像内容验证"""
        valid_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/jpeg",
                    "data": "base64_data"
                }
            }
        ]
        
        errors = self.multimodal_utils.validate_anthropic_content(valid_content)
        assert len(errors) == 0
    
    def test_validate_invalid_image_content(self) -> None:
        """测试无效图像内容验证"""
        invalid_content = [
            {
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/invalid",  # 不支持的格式
                    "data": "base64_data"
                }
            }
        ]
        
        errors = self.multimodal_utils.validate_anthropic_content(invalid_content)
        assert len(errors) > 0


class TestAnthropicToolsUtils:
    """Anthropic工具工具测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.format_utils = AnthropicFormatUtils()
        self.tools_utils = self.format_utils.tools_utils
    
    def test_convert_tools_to_anthropic_format(self) -> None:
        """测试工具格式转换"""
        tools = [
            {
                "name": "test_tool",
                "description": "Test tool",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"}
                    },
                    "required": ["param1"]
                }
            }
        ]
        
        result = self.tools_utils.convert_tools_to_anthropic_format(tools)
        
        assert len(result) == 1
        assert result[0]["name"] == "test_tool"
        assert result[0]["description"] == "Test tool"
        assert "input_schema" in result[0]
    
    def test_process_tool_choice_auto(self) -> None:
        """测试自动工具选择"""
        result = self.tools_utils.process_tool_choice("auto")
        assert result == "auto"
    
    def test_process_tool_choice_none(self) -> None:
        """测试不使用工具选择"""
        result = self.tools_utils.process_tool_choice("none")
        assert result == "none"
    
    def test_process_tool_choice_specific(self) -> None:
        """测试特定工具选择"""
        tool_choice = {"type": "tool", "name": "test_tool"}
        result = self.tools_utils.process_tool_choice(tool_choice)
        
        assert isinstance(result, dict)
        assert result["type"] == "tool"
        assert result["name"] == "test_tool"
    
    def test_validate_tools_valid(self) -> None:
        """测试有效工具验证"""
        tools = [
            {
                "name": "test_tool",
                "description": "Test tool",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        ]
        
        errors = self.tools_utils.validate_tools(tools)
        assert len(errors) == 0
    
    def test_validate_tools_invalid(self) -> None:
        """测试无效工具验证"""
        tools = [
            {
                "description": "Missing name",
                "parameters": "invalid"
            }
        ]
        
        errors = self.tools_utils.validate_tools(tools)
        assert len(errors) > 0


class TestAnthropicStreamUtils:
    """Anthropic流式工具测试"""
    
    def setup_method(self) -> None:
        """测试前设置"""
        self.format_utils = AnthropicFormatUtils()
        self.stream_utils = self.format_utils.stream_utils
    
    def test_parse_stream_event(self) -> None:
        """测试流式事件解析"""
        event_line = 'data: {"type": "message_start", "message": {"id": "msg_123"}}'
        
        result = self.stream_utils.parse_stream_event(event_line)
        
        assert result is not None
        assert result["type"] == "message_start"
        assert result["message"]["id"] == "msg_123"
    
    def test_parse_stream_event_done(self) -> None:
        """测试流式结束事件解析"""
        event_line = "data: [DONE]"
        
        result = self.stream_utils.parse_stream_event(event_line)
        
        assert result is not None
        assert result["type"] == "stream_end"
    
    def test_extract_text_from_stream_events(self) -> None:
        """测试从流式事件提取文本"""
        events = [
            {
                "type": "content_block_start",
                "content_block": {"type": "text", "text": ""}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": "Hello"}
            },
            {
                "type": "content_block_delta",
                "delta": {"type": "text_delta", "text": " world"}
            },
            {
                "type": "content_block_stop"
            }
        ]
        
        result = self.stream_utils.extract_text_from_stream_events(events)
        
        assert result == "Hello world"
    
    def test_extract_tool_calls_from_stream_events(self) -> None:
        """测试从流式事件提取工具调用"""
        events = [
            {
                "type": "content_block_start",
                "content_block": {
                    "type": "tool_use",
                    "id": "toolu_123",
                    "name": "test_tool",
                    "input": {}
                }
            },
            {
                "type": "content_block_delta",
                "delta": {
                    "type": "input_json_delta",
                    "partial_json": '{"param": "value"}'
                }
            },
            {
                "type": "content_block_stop"
            }
        ]
        
        result = self.stream_utils.extract_tool_calls_from_stream_events(events)
        
        assert len(result) == 1
        assert result[0]["function"]["name"] == "test_tool"


if __name__ == "__main__":
    pytest.main([__file__])