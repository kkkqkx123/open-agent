"""缓存键生成器测试"""

import pytest
from unittest.mock import Mock
from typing import Any, Dict, Optional, Sequence
from langchain_core.messages import BaseMessage

from src.infrastructure.llm.cache.key_generator import (
    DefaultCacheKeyGenerator,
    LLMCacheKeyGenerator,
    AnthropicCacheKeyGenerator
)


class MockBaseMessage(BaseMessage):
    """模拟BaseMessage用于测试"""
    
    def __init__(self, msg_type: str, content: str, additional_kwargs: Optional[Dict] = None):
        super().__init__(content=content, type=msg_type)
        self.type = msg_type
        self.additional_kwargs = additional_kwargs or {}


class TestDefaultCacheKeyGenerator:
    """测试默认缓存键生成器"""
    
    def test_generate_key_with_strings(self):
        """测试字符串参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key("arg1", "arg2")
        key2 = generator.generate_key("arg1", "arg2")
        key3 = generator.generate_key("arg2", "arg1")
        
        assert key1 == key2  # 相同参数应该生成相同键
        assert key1 != key3  # 不同参数应该生成不同键
        assert isinstance(key1, str)
        assert len(key1) == 32  # MD5哈希长度
    
    def test_generate_key_with_numbers(self):
        """测试数字参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key(1, 2.5)
        key2 = generator.generate_key(1, 2.5)
        key3 = generator.generate_key(2, 2.5)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_boolean(self):
        """测试布尔参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key(True, False)
        key2 = generator.generate_key(True, False)
        key3 = generator.generate_key(False, True)
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_kwargs(self):
        """测试关键字参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key(a="value1", b="value2")
        key2 = generator.generate_key(a="value1", b="value2")
        key3 = generator.generate_key(b="value2", a="value1")  # 顺序不同
        
        assert key1 == key2
        assert key1 == key3 # 关键字参数顺序应该不影响结果
    
    def test_generate_key_with_list(self):
        """测试列表参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key([1, 2, 3])
        key2 = generator.generate_key([1, 2, 3])
        key3 = generator.generate_key([3, 2, 1])
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_tuple(self):
        """测试元组参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key((1, 2, 3))
        key2 = generator.generate_key((1, 2, 3))
        key3 = generator.generate_key((3, 2, 1))
        
        assert key1 == key2
        assert key1 != key3
    
    def test_generate_key_with_dict(self):
        """测试字典参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key({"a": 1, "b": 2})
        key2 = generator.generate_key({"a": 1, "b": 2})
        key3 = generator.generate_key({"b": 2, "a": 1})  # 顺序不同
        
        assert key1 == key2
        assert key1 == key3  # 字典键顺序应该不影响结果
    
    def test_generate_key_with_mixed_types(self):
        """测试混合类型参数键生成"""
        generator = DefaultCacheKeyGenerator()
        
        key1 = generator.generate_key("string", 123, True, [1, 2], {"a": 1})
        key2 = generator.generate_key("string", 123, True, [1, 2], {"a": 1})
        
        assert key1 == key2
    
    def test_serialize_value_with_string(self):
        """测试字符串序列化"""
        generator = DefaultCacheKeyGenerator()
        
        result = generator._serialize_value("test_string")
        assert result == "test_string"
    
    def test_serialize_value_with_numbers(self):
        """测试数字序列化"""
        generator = DefaultCacheKeyGenerator()
        
        assert generator._serialize_value(123) == "123"
        assert generator._serialize_value(45.67) == "45.67"
    
    def test_serialize_value_with_boolean(self):
        """测试布尔值序列化"""
        generator = DefaultCacheKeyGenerator()
        
        assert generator._serialize_value(True) == "True"
        assert generator._serialize_value(False) == "False"
    
    def test_serialize_value_with_list(self):
        """测试列表序列化"""
        generator = DefaultCacheKeyGenerator()
        
        result = generator._serialize_value([1, "a", True])
        assert "1" in result
        assert "a" in result
        assert "True" in result
    
    def test_serialize_value_with_dict(self):
        """测试字典序列化"""
        generator = DefaultCacheKeyGenerator()
        
        result = generator._serialize_value({"a": 1, "b": "test"})
        assert "a:1" in result
        assert "b:test" in result
    
    def test_serialize_value_with_complex_object(self):
        """测试复杂对象序列化"""
        generator = DefaultCacheKeyGenerator()
        
        class ComplexObject:
            def __init__(self, value):
                self.value = value
        
        obj = ComplexObject("test")
        result = generator._serialize_value(obj)
        # 复杂对象应该被转换为字符串
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_serialize_value_with_json_serializable(self):
        """测试JSON可序列化对象"""
        generator = DefaultCacheKeyGenerator()
        
        class JSONSerializableObject:
            def __init__(self, data):
                self.data = data
            
            def __str__(self):
                return str(self.data)
        
        obj = JSONSerializableObject({"key": "value"})
        result = generator._serialize_value(obj)
        # 应该使用JSON序列化
        assert isinstance(result, str)
        assert "key" in result
        assert "value" in result


class TestLLMCacheKeyGenerator:
    """测试LLM缓存键生成器"""
    
    def test_init_default(self):
        """测试默认初始化"""
        generator = LLMCacheKeyGenerator()
        
        assert generator.include_model is True
        assert generator.include_parameters is True
        assert isinstance(generator._default_generator, DefaultCacheKeyGenerator)
    
    def test_init_with_options(self):
        """测试带选项初始化"""
        generator = LLMCacheKeyGenerator(include_model=False, include_parameters=False)
        
        assert generator.include_model is False
        assert generator.include_parameters is False
    
    def test_generate_key_basic(self):
        """测试基本键生成"""
        generator = LLMCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "gpt-4", {"temperature": 0.7})
        
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_generate_key_without_model(self):
        """测试不带模型的键生成"""
        generator = LLMCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "", {"temperature": 0.7})
        
        # 应该生成有效的哈希
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_generate_key_without_parameters(self):
        """测试不带参数的键生成"""
        generator = LLMCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "gpt-4")
        
        # 应该生成有效的哈希
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_generate_key_with_include_model_false(self):
        """测试include_model为False的键生成"""
        generator = LLMCacheKeyGenerator(include_model=False)
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "gpt-4", {"temperature": 0.7})
        
        # 应该生成有效的哈希
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_generate_key_with_include_parameters_false(self):
        """测试include_parameters为False的键生成"""
        generator = LLMCacheKeyGenerator(include_parameters=False)
        messages = [MockBaseMessage("user", "Hello")]
        
        key = generator.generate_key(messages, "gpt-4", {"temperature": 0.7})
        
        # 应该生成有效的哈希
        assert isinstance(key, str)
        assert len(key) == 32  # MD5哈希长度
    
    def test_serialize_messages(self):
        """测试消息序列化"""
        generator = LLMCacheKeyGenerator()
        messages = [
            MockBaseMessage("system", "You are helpful", {"role": "system"}),
            MockBaseMessage("user", "Hello", {"role": "user"})
        ]
        
        result = generator._serialize_messages(messages)
        
        assert isinstance(result, str)
        assert "type" in result  # JSON序列化后应包含类型信息
        assert "You are helpful" in result
        assert "Hello" in result
    
    def test_serialize_messages_with_additional_kwargs(self):
        """测试带额外属性的消息序列化"""
        generator = LLMCacheKeyGenerator()
        message = MockBaseMessage("user", "Hello", {"role": "user", "custom": "value"})
        
        result = generator._serialize_messages([message])
        
        assert "role" in result
        assert "custom" in result
    
    def test_serialize_parameters(self):
        """测试参数序列化"""
        generator = LLMCacheKeyGenerator()
        parameters = {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9,
            "stop": None,
            "empty_string": ""
        }
        
        result = generator._serialize_parameters(parameters)
        
        # 应该过滤掉None值和空字符串
        assert "temperature" in result
        assert "max_tokens" in result
        assert "top_p" in result
        assert "stop" not in result  # None值被过滤
        assert "empty_string" not in result  # 空字符串被过滤


class TestAnthropicCacheKeyGenerator:
    """测试Anthropic缓存键生成器"""
    
    def test_init(self):
        """测试初始化"""
        generator = AnthropicCacheKeyGenerator()
        
        assert generator.include_model is True
        assert generator.include_parameters is True
        assert isinstance(generator._default_generator, DefaultCacheKeyGenerator)
    
    def test_generate_key_has_different_result_than_base(self):
        """测试Anthropic键与基础键不同"""
        base_generator = LLMCacheKeyGenerator()
        anthropic_generator = AnthropicCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        
        base_key = base_generator.generate_key(messages, "claude-3", {"temperature": 0.7})
        anthropic_key = anthropic_generator.generate_key(messages, "claude-3", {"temperature": 0.7})
        
        assert isinstance(anthropic_key, str)
        assert len(anthropic_key) == 32
        assert anthropic_key != base_key  # Anthropic生成器应该生成不同的键
    
    def test_serialize_messages_anthropic(self):
        """测试Anthropic消息序列化"""
        generator = AnthropicCacheKeyGenerator()
        messages = [
            MockBaseMessage("system", "You are helpful", {"role": "system"}),
            MockBaseMessage("user", "Hello", {"role": "user"})
        ]
        
        result = generator._serialize_messages_anthropic(messages)
        
        assert isinstance(result, str)
        assert "type" in result # JSON序列化后应包含类型信息
        assert "You are helpful" in result
        assert "Hello" in result
    
    def test_serialize_parameters_anthropic(self):
        """测试Anthropic参数序列化"""
        generator = AnthropicCacheKeyGenerator()
        parameters = {
            "temperature": 0.7,
            "max_tokens": 100,
            "top_p": 0.9,
            "top_k": 40,
            "stop_sequences": ["END"],
            "tool_choice": "auto",
            "tools": [{"name": "tool1"}],
            "system": "You are helpful",
            "custom_param": "should_be_filtered",
            "none_value": None,
            "empty_string": ""
        }
        
        result = generator._serialize_parameters_anthropic(parameters)
        
        # 应该只包含Anthropic特定的参数
        assert "temperature" in result
        assert "max_tokens" in result
        assert "top_p" in result
        assert "top_k" in result
        assert "stop_sequences" in result
        assert "tool_choice" in result
        assert "tools" in result
        assert "system" in result
        
        # 非特定参数应该被过滤掉
        assert "custom_param" not in result
        assert "none_value" not in result
        assert "empty_string" not in result
    
    def test_generate_key_with_filtered_params(self):
        """测试过滤参数后的键生成"""
        generator = AnthropicCacheKeyGenerator()
        messages = [MockBaseMessage("user", "Hello")]
        parameters = {
            "temperature": 0.7,
            "max_tokens": 100,
            "custom_param": "should_be_filtered"  # 应该被过滤
        }
        
        key = generator.generate_key(messages, "claude-3", parameters)
        
        assert isinstance(key, str)
        assert len(key) == 32


class TestKeyGeneratorEdgeCases:
    """测试键生成器边界情况"""
    
    def test_empty_arguments(self):
        """测试空参数"""
        generator = DefaultCacheKeyGenerator()
        
        key = generator.generate_key()
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_none_values(self):
        """测试None值"""
        generator = DefaultCacheKeyGenerator()
        
        key = generator.generate_key(None)
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_very_long_string(self):
        """测试非常长的字符串"""
        generator = DefaultCacheKeyGenerator()
        long_string = "x" * 10000
        
        key = generator.generate_key(long_string)
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_special_characters(self):
        """测试特殊字符"""
        generator = DefaultCacheKeyGenerator()
        
        key = generator.generate_key("测试中文", "émojis🚀", "special\nchars\t")
        assert isinstance(key, str)
        assert len(key) == 32
    
    def test_nested_structures(self):
        """测试嵌套结构"""
        generator = DefaultCacheKeyGenerator()
        
        nested_dict = {
            "level1": {
                "level2": {
                    "data": [1, 2, 3]
                }
            }
        }
        
        key = generator.generate_key(nested_dict)
        assert isinstance(key, str)
        assert len(key) == 32