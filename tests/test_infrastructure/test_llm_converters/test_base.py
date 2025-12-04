"""基础组件测试

测试LLM转换器的基础组件功能。
"""

import pytest
from typing import Dict, Any, Sequence, TYPE_CHECKING
from src.infrastructure.llm.converters.base.base_provider_utils import BaseProviderUtils
from src.infrastructure.llm.converters.base.base_multimodal_utils import BaseMultimodalUtils
from src.infrastructure.llm.converters.base.base_tools_utils import BaseToolsUtils
from src.infrastructure.llm.converters.base.base_stream_utils import BaseStreamUtils
from src.infrastructure.llm.converters.base.base_validation_utils import BaseValidationUtils

if TYPE_CHECKING:
    from src.interfaces.messages import IBaseMessage


class TestBaseProviderUtils:
    """测试基础提供商工具类"""
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseProviderUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        from src.infrastructure.messages import AIMessage
        
        class ConcreteProviderUtils(BaseProviderUtils):
            def get_provider_name(self) -> str:
                return "test"
            
            def convert_request(self, messages: Sequence["IBaseMessage"], parameters: Dict[str, Any]) -> Dict[str, Any]:
                return {}
            
            def convert_response(self, response: Dict[str, Any]) -> "IBaseMessage":
                return AIMessage(content="test response")
        
        provider = ConcreteProviderUtils()
        assert provider.get_provider_name() == "test"
        assert provider.convert_request([], {}) == {}
        result = provider.convert_response({})
        assert result.content == "test response"


class TestBaseMultimodalUtils:
    """测试基础多模态工具类"""
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseMultimodalUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteMultimodalUtils(BaseMultimodalUtils):
            def process_content_to_provider_format(self, content):
                return [{"type": "text", "text": str(content)}]
            
            def extract_text_from_provider_content(self, content):
                return "extracted"
            
            def validate_provider_content(self, content):
                return []
        
        utils = ConcreteMultimodalUtils()
        result = utils.process_content_to_provider_format("test")
        assert result == [{"type": "text", "text": "test"}]
        assert utils.extract_text_from_provider_content([]) == "extracted"
        assert utils.validate_provider_content([]) == []


class TestBaseToolsUtils:
    """测试基础工具使用工具类"""
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseToolsUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteToolsUtils(BaseToolsUtils):
            def convert_tools_to_provider_format(self, tools):
                return tools
            
            def process_tool_choice(self, tool_choice):
                return tool_choice
            
            def extract_tool_calls_from_response(self, response):
                return []
        
        utils = ConcreteToolsUtils()
        tools = [{"name": "test", "description": "test tool"}]
        result = utils.convert_tools_to_provider_format(tools)
        assert result == tools
        assert utils.process_tool_choice("auto") == "auto"
        assert utils.extract_tool_calls_from_response({}) == []


class TestBaseStreamUtils:
    """测试基础流式工具类"""
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseStreamUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteStreamUtils(BaseStreamUtils):
            def parse_stream_event(self, event_line):
                return {"type": "test"}
            
            def process_stream_events(self, events):
                return {"merged": True}
            
            def extract_text_from_stream_events(self, events):
                return "extracted text"
        
        utils = ConcreteStreamUtils()
        result = utils.parse_stream_event("test event")
        assert result == {"type": "test"}
        assert utils.process_stream_events([{}]) == {"merged": True}
        assert utils.extract_text_from_stream_events([{}]) == "extracted text"


class TestBaseValidationUtils:
    """测试基础验证工具类"""
    
    def test_abstract_methods(self):
        """测试抽象方法不能直接实例化"""
        with pytest.raises(TypeError):
            BaseValidationUtils()  # type: ignore
    
    def test_concrete_implementation(self):
        """测试具体实现类"""
        
        class ConcreteValidationUtils(BaseValidationUtils):
            def validate_request_parameters(self, parameters):
                return []
            
            def validate_response(self, response):
                return []
            
            def handle_api_error(self, error_response):
                return "error"
        
        utils = ConcreteValidationUtils()
        assert utils.validate_request_parameters({}) == []
        assert utils.validate_response({}) == []
        assert utils.handle_api_error({}) == "error"
    
    def test_common_validation_methods(self):
        """测试通用验证方法"""
        
        class ConcreteValidationUtils(BaseValidationUtils):
            def validate_request_parameters(self, parameters):
                return []
            
            def validate_response(self, response):
                return []
            
            def handle_api_error(self, error_response):
                return "error"
        
        utils = ConcreteValidationUtils()
        
        # 测试参数验证
        errors = utils._validate_required_parameters({}, ["required_param"])
        assert len(errors) == 1
        assert "required_param" in errors[0]
        
        # 测试类型验证
        errors = utils._validate_parameter_type("string", int, "test_param")
        assert len(errors) == 1
        assert "int" in errors[0]
        
        # 测试范围验证
        errors = utils._validate_parameter_range(10, 0, 5, "test_param")
        assert len(errors) == 1
        assert "不能大于5" in errors[0]
        
        # 测试枚举验证
        errors = utils._validate_enum_value("invalid", ["valid1", "valid2"], "test_param")
        assert len(errors) == 1
        assert "valid1" in errors[0] and "valid2" in errors[0]