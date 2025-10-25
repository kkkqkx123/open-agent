import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime
from pathlib import Path

from src.application.history.manager import HistoryManager
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.domain.history.models import MessageRecord, ToolCallRecord
from src.domain.history.llm_models import LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
from src.domain.history import HistoryQuery


class TestHistoryManager(unittest.TestCase):
    def setUp(self):
        """设置测试环境"""
        self.storage_path = Path("./test_history_storage")
        self.storage = FileHistoryStorage(self.storage_path)
        self.history_manager = HistoryManager(self.storage)
    
    def tearDown(self):
        """清理测试环境"""
        import shutil
        if self.storage_path.exists():
            shutil.rmtree(self.storage_path)
    
    def test_record_message(self):
        """测试记录消息"""
        record = MessageRecord(
            record_id="test_msg_1",
            session_id="session_1",
            timestamp=datetime.now(),
            content="Hello, world!"
        )
        
        # 记录消息
        self.history_manager.record_message(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['content'], "Hello, world!")
    
    def test_record_tool_call(self):
        """测试记录工具调用"""
        record = ToolCallRecord(
            record_id="test_tool_1",
            session_id="session_1",
            timestamp=datetime.now(),
            tool_name="test_tool",
            tool_input={"param": "value"}
        )
        
        # 记录工具调用
        self.history_manager.record_tool_call(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['tool_name'], "test_tool")
    
    def test_record_llm_request(self):
        """测试记录LLM请求"""
        record = LLMRequestRecord(
            record_id="test_llm_req_1",
            session_id="session_1",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            messages=[{"role": "user", "content": "Hello"}],
            parameters={"temperature": 0.7}
        )
        
        # 记录LLM请求
        self.history_manager.record_llm_request(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['model'], "gpt-4")
    
    def test_record_llm_response(self):
        """测试记录LLM响应"""
        record = LLMResponseRecord(
            record_id="test_llm_resp_1",
            session_id="session_1",
            timestamp=datetime.now(),
            request_id="test_llm_req_1",
            content="Response content",
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            response_time=1.5,
            model="gpt-4"
        )
        
        # 记录LLM响应
        self.history_manager.record_llm_response(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['content'], "Response content")
    
    def test_record_token_usage(self):
        """测试记录Token使用"""
        record = TokenUsageRecord(
            record_id="test_token_1",
            session_id="session_1",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api"
        )
        
        # 记录Token使用
        self.history_manager.record_token_usage(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['total_tokens'], 30)
    
    def test_record_cost(self):
        """测试记录成本"""
        record = CostRecord(
            record_id="test_cost_1",
            session_id="session_1",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            prompt_cost=0.001,
            completion_cost=0.002,
            total_cost=0.003
        )
        
        # 记录成本
        self.history_manager.record_cost(record)
        
        # 验证记录已存储
        records = self.storage.get_all_records("session_1")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['total_cost'], 0.003)
    
    def test_get_token_statistics(self):
        """测试获取Token统计"""
        # 添加一些Token使用记录
        token_record1 = TokenUsageRecord(
            record_id="token_1",
            session_id="session_stats",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            source="api"
        )
        
        token_record2 = TokenUsageRecord(
            record_id="token_2",
            session_id="session_stats",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=15,
            completion_tokens=25,
            total_tokens=40,
            source="api"
        )
        
        self.history_manager.record_token_usage(token_record1)
        self.history_manager.record_token_usage(token_record2)
        
        # 获取统计信息
        stats = self.history_manager.get_token_statistics("session_stats")
        
        self.assertEqual(stats["total_tokens"], 70)  # 30 + 40
        self.assertEqual(stats["prompt_tokens"], 25)  # 10 + 15
        self.assertEqual(stats["completion_tokens"], 45)  # 20 + 25
        self.assertEqual(stats["record_count"], 2)
    
    def test_get_cost_statistics(self):
        """测试获取成本统计"""
        # 添加一些成本记录
        cost_record1 = CostRecord(
            record_id="cost_1",
            session_id="session_cost_stats",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            prompt_cost=0.001,
            completion_cost=0.002,
            total_cost=0.003
        )
        
        cost_record2 = CostRecord(
            record_id="cost_2",
            session_id="session_cost_stats",
            timestamp=datetime.now(),
            model="gpt-3.5-turbo",
            provider="openai",
            prompt_tokens=5,
            completion_tokens=10,
            total_tokens=15,
            prompt_cost=0.0005,
            completion_cost=0.001,
            total_cost=0.0015
        )
        
        self.history_manager.record_cost(cost_record1)
        self.history_manager.record_cost(cost_record2)
        
        # 获取统计信息
        stats = self.history_manager.get_cost_statistics("session_cost_stats")
        
        # 使用assertAlmostEqual处理浮点数精度问题
        self.assertAlmostEqual(stats["total_cost"], 0.0045, places=10)  # 0.003 + 0.0015
        self.assertAlmostEqual(stats["prompt_cost"], 0.0015, places=10)  # 0.001 + 0.0005
        self.assertAlmostEqual(stats["completion_cost"], 0.003, places=10)  # 0.002 + 0.001
        self.assertEqual(len(stats["models_used"]), 2)  # gpt-4 and gpt-3.5-turbo
        self.assertEqual(stats["record_count"], 2)
    
    def test_get_llm_statistics(self):
        """测试获取LLM统计"""
        # 添加一些LLM请求和响应记录
        llm_request = LLMRequestRecord(
            record_id="llm_req_1",
            session_id="session_llm_stats",
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            messages=[{"role": "user", "content": "Hello"}],
            parameters={"temperature": 0.7}
        )
        
        llm_response = LLMResponseRecord(
            record_id="llm_resp_1",
            session_id="session_llm_stats",
            timestamp=datetime.now(),
            request_id="llm_req_1",
            content="Response content",
            finish_reason="stop",
            token_usage={"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
            response_time=1.5,
            model="gpt-4"
        )
        
        self.history_manager.record_llm_request(llm_request)
        self.history_manager.record_llm_response(llm_response)
        
        # 获取统计信息
        stats = self.history_manager.get_llm_statistics("session_llm_stats")
        
        self.assertEqual(stats["llm_requests"], 1)
        self.assertEqual(stats["llm_responses"], 1)
        self.assertEqual(len(stats["models_used"]), 1)  # gpt-4
        self.assertEqual(stats["request_record_count"], 1)
        self.assertEqual(stats["response_record_count"], 1)
    
    def test_query_history(self):
        """测试查询历史"""
        # 添加一些记录
        msg_record = MessageRecord(
            record_id="msg_query_1",
            session_id="session_query",
            timestamp=datetime.now(),
            content="Message content"
        )
        
        tool_record = ToolCallRecord(
            record_id="tool_query_1",
            session_id="session_query",
            timestamp=datetime.now(),
            tool_name="test_tool",
            tool_input={"param": "value"}
        )
        
        self.history_manager.record_message(msg_record)
        self.history_manager.record_tool_call(tool_record)
        
        # 查询历史
        query = HistoryQuery(session_id="session_query")
        result = self.history_manager.query_history(query)
        
        self.assertEqual(result.total, 2)
        self.assertEqual(len(result.records), 2)
        
        # 验证记录类型
        record_types = [record.record_type for record in result.records]
        self.assertIn("message", record_types)
        self.assertIn("tool_call", record_types)


if __name__ == "__main__":
    unittest.main()