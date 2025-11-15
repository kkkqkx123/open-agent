import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from src.infrastructure.history.history_hook import HistoryRecordingHook
from src.domain.history import (
    LLMRequestRecord,
    LLMResponseRecord,
    TokenUsageRecord,
    CostRecord,
    IHistoryManager
)
from src.domain.history.cost_calculator import CostCalculator
from infrastructure.history.token_tracker import TokenUsageTracker


class MockHistoryManager(IHistoryManager):
    """模拟历史管理器用于测试"""
    
    def __init__(self):
        self.records = []
    
    def record_message(self, record) -> None:
        self.records.append(record)
    
    def record_tool_call(self, record) -> None:
        self.records.append(record)
    
    def query_history(self, query):
        # 简单实现
        pass
    
    def record_llm_request(self, record) -> None:
        self.records.append(record)
    
    def record_llm_response(self, record) -> None:
        self.records.append(record)
    
    def record_token_usage(self, record) -> None:
        self.records.append(record)
    
    def record_cost(self, record) -> None:
        self.records.append(record)
    
    def get_token_statistics(self, session_id: str):
        # 简单实现
        pass
    
    def get_cost_statistics(self, session_id: str):
        # 简单实现
        pass
    
    def get_llm_statistics(self, session_id: str):
        # 简单实现
        pass


class TestHistoryRecordingHook(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.mock_history_manager = MockHistoryManager()
        self.mock_token_tracker = Mock(spec=TokenUsageTracker)
        self.mock_cost_calculator = Mock(spec=CostCalculator)
        
        self.hook = HistoryRecordingHook(
            history_manager=self.mock_history_manager,
            token_tracker=self.mock_token_tracker,
            cost_calculator=self.mock_cost_calculator
        )
    
    def test_before_call(self):
        """测试before_call方法"""
        # 准备测试数据
        messages = [Mock()]
        parameters = {"temperature": 0.7}
        kwargs = {
            "request_id": "req_123",
            "session_id": "session_456",
            "model": "gpt-4",
            "provider": "openai"
        }
        
        # 设置mock返回值
        self.mock_token_tracker.estimate_tokens.return_value = 100
        
        # 执行测试
        self.hook.before_call(messages, parameters, **kwargs)
        
        # 验证记录被添加到pending_requests
        self.assertIn("req_123", self.hook.pending_requests)
        
        # 验证history_manager被调用
        self.assertEqual(len(self.mock_history_manager.records), 1)
        self.assertIsInstance(self.mock_history_manager.records[0], LLMRequestRecord)
        self.assertEqual(self.mock_history_manager.records[0].model, "gpt-4")
        self.assertEqual(self.mock_history_manager.records[0].provider, "openai")
        self.assertEqual(self.mock_history_manager.records[0].session_id, "session_456")
        
        # 验证token_tracker被调用
        self.mock_token_tracker.estimate_tokens.assert_called_once_with(messages)
    
    def test_after_call_success(self):
        """测试after_call方法（成功情况）"""
        # 准备测试数据
        messages = [Mock()]
        parameters = {"temperature": 0.7}
        kwargs = {
            "request_id": "req_123",
            "session_id": "session_456",
            "model": "gpt-4",
            "provider": "openai"
        }
        
        # 先调用before_call来创建pending request
        self.mock_token_tracker.estimate_tokens.return_value = 100
        self.hook.before_call(messages, parameters, **kwargs)
        
        # 准备响应对象
        mock_response = Mock()
        mock_response.content = "Test response"
        mock_response.finish_reason = "stop"
        mock_response.model = "gpt-4"
        mock_response.metadata = {}
        mock_response.response_time = 1.5
        mock_response.token_usage = Mock()
        mock_response.token_usage.prompt_tokens = 50
        mock_response.token_usage.completion_tokens = 30
        mock_response.token_usage.total_tokens = 80
        
        # 设置cost_calculator的返回值
        mock_cost_record = CostRecord(
            record_id="cost_1",
            session_id="session_456",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=50,
            completion_tokens=30,
            total_tokens=80,
            prompt_cost=0.0015,
            completion_cost=0.0018,
            total_cost=0.0033
        )
        self.mock_cost_calculator.calculate_cost.return_value = mock_cost_record
        
        # 执行测试
        self.hook.after_call(mock_response, messages, parameters, **kwargs)
        
        # 验证pending request被移除
        self.assertNotIn("req_123", self.hook.pending_requests)
        
        # 验证所有记录都被添加
        self.assertEqual(len(self.mock_history_manager.records), 4)  # 原来的1个请求 + 1个响应 + 1个token + 1个cost
        
        # 验证响应记录
        response_records = [r for r in self.mock_history_manager.records if isinstance(r, LLMResponseRecord)]
        self.assertEqual(len(response_records), 1)
        self.assertEqual(response_records[0].content, "Test response")
        self.assertEqual(response_records[0].request_id, "req_123")
        
        # 验证Token使用记录
        token_records = [r for r in self.mock_history_manager.records if isinstance(r, TokenUsageRecord)]
        self.assertEqual(len(token_records), 1)
        self.assertEqual(token_records[0].prompt_tokens, 50)
        self.assertEqual(token_records[0].completion_tokens, 30)
        self.assertEqual(token_records[0].total_tokens, 80)
        
        # 验证成本记录
        cost_records = [r for r in self.mock_history_manager.records if isinstance(r, CostRecord)]
        self.assertEqual(len(cost_records), 1)
        self.assertEqual(cost_records[0].total_cost, 0.0033)
        
        # 验证cost_calculator被调用
        self.mock_cost_calculator.calculate_cost.assert_called_once()
    
    def test_on_error(self):
        """测试on_error方法"""
        # 准备测试数据
        messages = [Mock()]
        parameters = {"temperature": 0.7}
        kwargs = {
            "request_id": "req_error_1",
            "session_id": "session_error",
            "model": "gpt-4",
            "provider": "openai"
        }
        
        # 先调用before_call来创建pending request
        self.mock_token_tracker.estimate_tokens.return_value = 100
        self.hook.before_call(messages, parameters, **kwargs)
        
        # 验证pending request存在
        self.assertIn("req_error_1", self.hook.pending_requests)
        
        # 创建错误对象
        error = Exception("Test error")
        
        # 执行测试
        result = self.hook.on_error(error, messages, parameters, **kwargs)
        
        # 验证返回值为None（不尝试恢复）
        self.assertIsNone(result)
        
        # 验证pending request被移除
        self.assertNotIn("req_error_1", self.hook.pending_requests)
        
        # 验证错误响应记录被添加
        response_records = [r for r in self.mock_history_manager.records if isinstance(r, LLMResponseRecord)]
        self.assertEqual(len(response_records), 1)
        self.assertIn("Error: Test error", response_records[0].content)
        self.assertEqual(response_records[0].finish_reason, "error")
    
    def test_after_call_no_response(self):
        """测试after_call方法（无响应情况）"""
        # 准备测试数据
        messages = [Mock()]
        parameters = {"temperature": 0.7}
        kwargs = {
            "request_id": "req_no_resp",
            "session_id": "session_no_resp",
            "model": "gpt-4",
            "provider": "openai"
        }
        
        # 先调用before_call来创建pending request
        self.mock_token_tracker.estimate_tokens.return_value = 100
        self.hook.before_call(messages, parameters, **kwargs)
        
        # 验证pending request存在
        self.assertIn("req_no_resp", self.hook.pending_requests)
        
        # 执行测试（response为None）
        self.hook.after_call(None, messages, parameters, **kwargs)
        
        # 验证pending request仍然存在（因为没有处理响应）
        self.assertIn("req_no_resp", self.hook.pending_requests)


if __name__ == "__main__":
    unittest.main()