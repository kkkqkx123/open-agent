"""pytest配置文件

为Anthropic转换器测试提供共享配置和fixture。
"""

import pytest
from unittest.mock import Mock
from src.services.logger import get_logger


@pytest.fixture
def mock_logger():
    """模拟日志器"""
    logger = Mock(spec=get_logger(__name__))
    return logger


@pytest.fixture
def sample_anthropic_response():
    """示例Anthropic响应"""
    return {
        "id": "msg_01A09qVqPDqAmAmaFmC5Vx3E",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll help you with that."
            }
        ],
        "model": "claude-sonnet-4-5",
        "stop_reason": "end_turn",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 20,
            "output_tokens": 15
        }
    }


@pytest.fixture
def sample_anthropic_tool_response():
    """示例Anthropic工具响应"""
    return {
        "id": "msg_01A09qVqPDqAmAmaFmC5Vx3E",
        "type": "message",
        "role": "assistant",
        "content": [
            {
                "type": "text",
                "text": "I'll check the weather for you."
            },
            {
                "type": "tool_use",
                "id": "toolu_01A09qVqPDqAmAmaFmC5Vx3E",
                "name": "get_weather",
                "input": {
                    "location": "San Francisco, CA"
                }
            }
        ],
        "model": "claude-sonnet-4-5",
        "stop_reason": "tool_use",
        "stop_sequence": None,
        "usage": {
            "input_tokens": 25,
            "output_tokens": 20
        }
    }


@pytest.fixture
def sample_anthropic_stream_events():
    """示例Anthropic流式事件"""
    return [
        {
            "type": "message_start",
            "message": {
                "id": "msg_01A09qVqPDqAmAmaFmC5Vx3E",
                "type": "message",
                "role": "assistant",
                "content": [],
                "model": "claude-sonnet-4-5",
                "stop_reason": None,
                "stop_sequence": None,
                "usage": {
                    "input_tokens": 20,
                    "output_tokens": 0
                }
            }
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {
                "type": "text",
                "text": ""
            }
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "text_delta",
                "text": "I'll"
            }
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "text_delta",
                "text": " help"
            }
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {
                "type": "text_delta",
                "text": " you."
            }
        },
        {
            "type": "content_block_stop",
            "index": 0
        },
        {
            "type": "message_delta",
            "delta": {
                "stop_reason": "end_turn"
            },
            "usage": {
                "output_tokens": 4
            }
        },
        {
            "type": "message_stop"
        }
    ]


@pytest.fixture
def sample_tools():
    """示例工具定义"""
    return [
        {
            "name": "get_weather",
            "description": "Get current weather information for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "The city and state, e.g. San Francisco, CA"
                    },
                    "unit": {
                        "type": "string",
                        "enum": ["celsius", "fahrenheit"],
                        "description": "Temperature unit"
                    }
                },
                "required": ["location"]
            }
        },
        {
            "name": "calculate",
            "description": "Perform mathematical calculations",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"]
            }
        }
    ]


@pytest.fixture
def sample_multimodal_content():
    """示例多模态内容"""
    return [
        {
            "type": "text",
            "text": "What's in this image?"
        },
        {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": "image/jpeg",
                "data": "/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCdABmX/9k="
            }
        }
    ]


@pytest.fixture
def sample_error_response():
    """示例错误响应"""
    return {
        "error": {
            "type": "invalid_request_error",
            "message": "Invalid request: missing required parameter 'max_tokens'"
        }
    }