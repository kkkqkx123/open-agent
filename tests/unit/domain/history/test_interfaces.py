"""History接口单元测试"""

import pytest
from abc import ABC
from typing import TYPE_CHECKING, Dict, Any
from src.domain.history.interfaces import IHistoryManager

if TYPE_CHECKING:
    from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, HistoryResult
    from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord


class TestIHistoryManager:
    """IHistoryManager接口测试"""

    def test_interface_is_abstract(self) -> None:
        """测试接口是抽象基类"""
        assert issubclass(IHistoryManager, ABC)
        assert hasattr(IHistoryManager, '__abstractmethods__')

    def test_abstract_methods(self) -> None:
        """测试抽象方法"""
        abstract_methods = IHistoryManager.__abstractmethods__
        expected_methods = {
            'record_message', 'record_tool_call', 'query_history',
            'record_llm_request', 'record_llm_response', 'record_token_usage',
            'record_cost', 'get_token_statistics', 'get_cost_statistics',
            'get_llm_statistics'
        }
        
        assert abstract_methods == expected_methods

    def test_cannot_instantiate_interface(self) -> None:
        """测试不能直接实例化接口"""
        with pytest.raises(TypeError) as exc_info:
            IHistoryManager()  # type: ignore
        # 验证错误消息包含抽象方法信息
        assert "abstract" in str(exc_info.value).lower()

    def test_concrete_implementation(self) -> None:
        """测试具体实现必须实现所有抽象方法"""
        class ConcreteHistoryManager(IHistoryManager):
            def record_message(self, record: 'MessageRecord') -> None:
                pass
            
            def record_tool_call(self, record: 'ToolCallRecord') -> None:
                pass
            
            def query_history(self, query: 'HistoryQuery') -> 'HistoryResult':
                return None  # type: ignore
            
            def record_llm_request(self, record: 'LLMRequestRecord') -> None:
                pass
            
            def record_llm_response(self, record: 'LLMResponseRecord') -> None:
                pass
            
            def record_token_usage(self, record: 'TokenUsageRecord') -> None:
                pass
            
            def record_cost(self, record: 'CostRecord') -> None:
                pass
            
            def get_token_statistics(self, session_id: str) -> Dict[str, Any]:
                return {}
            
            def get_cost_statistics(self, session_id: str) -> Dict[str, Any]:
                return {}
            
            def get_llm_statistics(self, session_id: str) -> Dict[str, Any]:
                return {}

        # 应该能够实例化具体实现
        manager = ConcreteHistoryManager()
        assert isinstance(manager, IHistoryManager)

    def test_partial_implementation_fails(self) -> None:
        """测试部分实现会失败"""
        class PartialHistoryManager(IHistoryManager):
            def record_message(self, record: 'MessageRecord') -> None:
                pass
            # 缺少其他两个方法

        with pytest.raises(TypeError) as exc_info:
            PartialHistoryManager()  # type: ignore
        # 验证错误消息包含抽象方法信息
        assert "abstract" in str(exc_info.value).lower()