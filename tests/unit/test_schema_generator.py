"""测试Schema生成器

验证从配置文件生成Schema的功能。
"""

import pytest
from unittest.mock import Mock, patch
from src.core.workflow.config.schema_generator import SchemaGenerator, generate_node_schema


class TestSchemaGenerator:
    """测试Schema生成器"""
    
    def setup_method(self) -> None:
        """设置测试环境"""
        self.generator = SchemaGenerator()
    
    def test_generate_schema_from_config_llm_node(self) -> None:
        """测试从配置生成LLM节点Schema"""
        # 模拟配置加载器
        mock_config = {
            "max_tokens": 2000,
            "temperature": 0.7,
            "top_p": 1.0,
            "frequency_penalty": 0.0,
            "presence_penalty": 0.0,
            "context_window_size": 4000,
            "max_message_history": 10,
            "system_prompt": "你是一个智能助手",
            "include_tool_results": True,
            "follow_up_indicators": ["需要更多信息", "无法确定"]
        }
        
        with patch.object(self.generator._config_loader, 'get_config', return_value=mock_config):
            schema = self.generator.generate_schema_from_config("llm_node")
            
            # 验证Schema结构
            assert schema["type"] == "object"
            assert "properties" in schema
            assert "required" in schema
            assert schema["description"] == "llm_node 节点配置Schema"
            
            # 验证属性
            properties = schema["properties"]
            assert "max_tokens" in properties
            assert "temperature" in properties
            assert "system_prompt" in properties
            
            # 验证类型推断
            assert properties["max_tokens"]["type"] == "integer"
            assert properties["temperature"]["type"] == "number"
            assert properties["system_prompt"]["type"] == "string"
            assert properties["include_tool_results"]["type"] == "boolean"
            assert properties["follow_up_indicators"]["type"] == "array"
    
    def test_generate_schema_from_config_tool_node(self) -> None:
        """测试从配置生成工具节点Schema"""
        mock_config = {
            "timeout": 30,
            "max_parallel_calls": 1,
            "retry_on_failure": False,
            "max_retries": 3,
            "continue_on_error": True,
            "parse_tool_calls_from_text": True,
            "key_value_pattern": "(\\w+)\\s*[:=]\\s*[\"']?([^\"'\\s,]+)[\"']?"
        }
        
        with patch.object(self.generator._config_loader, 'get_config', return_value=mock_config):
            schema = self.generator.generate_schema_from_config("tool_node")
            
            # 验证必需字段
            assert "tool_manager" in schema["required"]
            
            # 验证属性类型
            properties = schema["properties"]
            assert properties["timeout"]["type"] == "integer"
            assert properties["max_parallel_calls"]["type"] == "integer"
            assert properties["retry_on_failure"]["type"] == "boolean"
    
    def test_generate_schema_with_nested_objects(self) -> None:
        """测试生成包含嵌套对象的Schema"""
        mock_config = {
            "simple_field": "value",
            "nested_object": {
                "field1": "string_value",
                "field2": 42,
                "field3": True
            },
            "array_field": ["item1", "item2", "item3"]
        }
        
        with patch.object(self.generator._config_loader, 'get_config', return_value=mock_config):
            schema = self.generator.generate_schema_from_config("test_node")
            
            properties = schema["properties"]
            
            # 验证嵌套对象
            assert properties["nested_object"]["type"] == "object"
            assert "field1" in properties["nested_object"]["properties"]
            assert properties["nested_object"]["properties"]["field1"]["type"] == "string"
            assert properties["nested_object"]["properties"]["field2"]["type"] == "integer"
            assert properties["nested_object"]["properties"]["field3"]["type"] == "boolean"
            
            # 验证数组
            assert properties["array_field"]["type"] == "array"
    
    def test_generate_schema_no_config(self) -> None:
        """测试当配置不存在时返回默认Schema"""
        with patch.object(self.generator._config_loader, 'get_config', return_value={}):
            schema = self.generator.generate_schema_from_config("nonexistent_node")
            
            # 应该返回默认Schema
            assert schema["type"] == "object"
            assert schema["properties"] == {}
            assert schema["required"] == []
    
    def test_schema_caching(self) -> None:
        """测试Schema缓存功能"""
        mock_config = {"test_field": "test_value"}
        
        with patch.object(self.generator._config_loader, 'get_config', return_value=mock_config) as mock_get_config:
            # 第一次调用
            schema1 = self.generator.generate_schema_from_config("test_node")
            
            # 第二次调用应该使用缓存
            schema2 = self.generator.generate_schema_from_config("test_node")
            
            # 验证结果相同
            assert schema1 == schema2
            
            # 验证配置加载器只被调用一次
            mock_get_config.assert_called_once()
    
    def test_clear_cache(self) -> None:
        """测试清除缓存功能"""
        mock_config = {"test_field": "test_value"}
        
        with patch.object(self.generator._config_loader, 'get_config', return_value=mock_config) as mock_get_config:
            # 生成Schema并缓存
            self.generator.generate_schema_from_config("test_node")
            
            # 清除缓存
            self.generator.clear_cache()
            
            # 再次生成应该重新调用配置加载器
            self.generator.generate_schema_from_config("test_node")
            
            # 验证配置加载器被调用了两次
            assert mock_get_config.call_count == 2
    
    def test_is_required_field_tool_node(self) -> None:
        """测试工具节点必需字段判断"""
        # tool_manager应该是必需的
        assert self.generator._is_required_field("tool_manager", "some_value", "tool_node")
        # 其他字段不是必需的
        assert not self.generator._is_required_field("timeout", 30, "tool_node")
        assert not self.generator._is_required_field("max_retries", 3, "tool_node")
    
    def test_is_required_field_llm_node(self) -> None:
        """测试LLM节点必需字段判断"""
        # LLM节点没有必需字段
        assert not self.generator._is_required_field("temperature", 0.7, "llm_node")
        assert not self.generator._is_required_field("max_tokens", 2000, "llm_node")
    
    def test_is_required_field_start_end_nodes(self) -> None:
        """测试START和END节点必需字段判断"""
        # START和END节点没有必需字段
        assert not self.generator._is_required_field("plugin_config_path", "path", "start_node")
        assert not self.generator._is_required_field("next_node", "node", "start_node")
        assert not self.generator._is_required_field("output_directory", "dir", "end_node")
    
    def test_is_required_field_condition_node(self) -> None:
        """测试条件节点必需字段判断"""
        # conditions应该是必需的
        assert self.generator._is_required_field("conditions", [], "condition_node")
        # 其他字段不是必需的
        assert not self.generator._is_required_field("default_next_node", "node", "condition_node")


class TestGenerateNodeSchema:
    """测试全局函数"""
    
    def test_generate_node_schema_function(self) -> None:
        """测试全局generate_node_schema函数"""
        mock_config = {"test_field": "test_value"}
        
        with patch('src.core.workflow.config.schema_generator.get_schema_generator') as mock_get_generator:
            mock_generator = Mock()
            mock_generator.generate_schema_from_config.return_value = {"test": "schema"}
            mock_get_generator.return_value = mock_generator
            
            result = generate_node_schema("test_node")
            
            assert result == {"test": "schema"}
            mock_generator.generate_schema_from_config.assert_called_once_with("test_node")


if __name__ == "__main__":
    pytest.main([__file__])