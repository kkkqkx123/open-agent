"""History模块集成测试"""

import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.infrastructure.container import DependencyContainer
from src.infrastructure.history.storage.file_storage import FileHistoryStorage
from src.infrastructure.history.storage.memory_storage import MemoryHistoryStorage
from src.infrastructure.llm.token_calculators.api_calculator import ApiTokenCalculator
from src.domain.history.models import MessageRecord, ToolCallRecord, HistoryQuery, MessageType
from src.domain.history.llm_models import (
    LLMRequestRecord, LLMResponseRecord, TokenUsageRecord, CostRecord
)
from src.domain.history.interfaces import IHistoryManager
from src.application.history.manager import HistoryManager
from src.application.history.service_integration import HistoryServiceIntegration
from src.application.history.session_context import session_context, generate_session_id
from src.application.history.token_tracker import TokenUsageTracker
from src.application.history.di_config import register_history_services_with_dependencies, register_test_history_services
from src.application.history.adapters.tui_adapter import TUIHistoryAdapter
from src.presentation.tui.state_manager import StateManager


class TestHistoryModuleIntegration:
    """History模块集成测试"""

    @pytest.fixture
    def temp_dir(self):
        """临时目录fixture"""
        temp_dir = tempfile.mkdtemp()
        yield Path(temp_dir)
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def container(self, temp_dir):
        """依赖注入容器fixture"""
        container = DependencyContainer()
        
        # 注册历史服务
        config = {
            "history": {
                "enabled": True,
                "storage_path": str(temp_dir),
                "pricing": {
                    "openai:gpt-4": {
                        "prompt_price_per_1k": 0.01,
                        "completion_price_per_1k": 0.03
                    }
                }
            }
        }
        
        token_calculator = ApiTokenCalculator()
        register_history_services_with_dependencies(container, config, token_calculator)
        
        return container

    def test_end_to_end_history_flow(self, container):
        """测试端到端历史记录流程"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        token_tracker = container.get(TokenUsageTracker)
        
        # 生成会话ID
        session_id = generate_session_id()
        
        # 记录会话开始
        service_integration.record_session_start(session_id, "test_workflow", "test_agent")
        
        # 记录用户消息
        service_integration.record_message(
            session_id, 
            MessageType.USER, 
            "你好，请帮我分析一下数据"
        )
        
        # 记录LLM请求
        with session_context(session_id):
            from langchain_core.messages import HumanMessage
            messages = [HumanMessage(content="你好，请帮我分析一下数据")]
            token_record = token_tracker.track_request(
                messages, 
                "gpt-4", 
                "openai", 
                session_id
            )
        
        # 模拟API响应
        api_response = {
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "total_tokens": 40
            }
        }
        token_tracker.update_from_response(token_record, api_response)
        
        # 记录助手消息
        service_integration.record_message(
            session_id, 
            MessageType.ASSISTANT, 
            "我会帮您分析数据，请提供具体的数据集"
        )
        
        # 记录工具调用
        service_integration.record_tool_call(
            session_id, 
            "data_analyzer", 
            {"dataset": "sales_data.csv"}, 
            {"result": "分析完成", "insights": ["趋势上升", "季节性明显"]}
        )
        
        # 记录会话结束
        service_integration.record_session_end(session_id, "completed")
        
        # 验证历史记录
        query = HistoryQuery(session_id=session_id)
        result = history_manager.query_history(query)
        
        assert result.total == 7  # 开始、用户消息、token使用(本地)、token使用(API)、助手消息、工具调用、结束
        assert len(result.records) == 7
        
        # 验证记录类型
        record_types = [record.record_type for record in result.records]
        assert "message" in record_types
        assert "token_usage" in record_types
        assert "tool_call" in record_types
        
        # 验证Token统计
        token_stats = history_manager.get_token_statistics(session_id)
        assert token_stats["total_tokens"] == 40
        assert token_stats["prompt_tokens"] == 15
        assert token_stats["completion_tokens"] == 25
        
        # 验证会话摘要
        summary = service_integration.get_session_summary(session_id)
        assert summary["session_id"] == session_id
        assert summary["message_count"] == 4  # 开始、用户、助手、结束
        assert summary["tool_call_count"] == 1
        assert summary["token_usage_count"] == 2  # 本地估算和API更新
        assert summary["duration"] is not None

    def test_tui_adapter_integration(self, container):
        """测试TUI适配器集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        state_manager = Mock(spec=StateManager)
        state_manager.session_id = "test-session"
        
        # 创建适配器
        adapter = TUIHistoryAdapter(history_manager, state_manager)
        
        # 记录用户消息
        adapter.on_user_message("用户输入测试")
        
        # 记录助手消息
        adapter.on_assistant_message("助手回复测试")
        
        # 记录工具调用
        adapter.on_tool_call(
            "test_tool", 
            {"param": "value"}, 
            {"result": "success"}
        )
        
        # 验证记录
        query = HistoryQuery(session_id="test-session")
        result = history_manager.query_history(query)
        
        assert result.total == 3
        assert len(result.records) == 3
        
        # 验证记录内容
        records = result.records
        user_message = next(r for r in records if r.record_type == "message" and r.message_type == MessageType.USER)
        assistant_message = next(r for r in records if r.record_type == "message" and r.message_type == MessageType.ASSISTANT)
        tool_call = next(r for r in records if r.record_type == "tool_call")
        
        assert user_message.content == "用户输入测试"
        assert assistant_message.content == "助手回复测试"
        assert tool_call.tool_name == "test_tool"

    def test_token_tracker_integration(self, container):
        """测试Token追踪器集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        token_tracker = container.get(TokenUsageTracker)
        
        session_id = generate_session_id()
        
        # 模拟多个LLM请求
        with session_context(session_id):
            from langchain_core.messages import HumanMessage, AIMessage
            
            # 第一个请求
            messages1 = [HumanMessage(content="第一个问题")]
            token_record1 = token_tracker.track_request(messages1, "gpt-4", "openai", session_id)
            
            api_response1 = {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 20,
                    "total_tokens": 30
                }
            }
            token_tracker.update_from_response(token_record1, api_response1)
            
            # 第二个请求
            messages2 = [HumanMessage(content="第二个问题")]
            token_record2 = token_tracker.track_request(messages2, "gpt-4", "openai", session_id)
            
            api_response2 = {
                "usage": {
                    "prompt_tokens": 15,
                    "completion_tokens": 25,
                    "total_tokens": 40
                }
            }
            token_tracker.update_from_response(token_record2, api_response2)
        
        # 验证Token统计
        token_stats = history_manager.get_token_statistics(session_id)
        assert token_stats["total_tokens"] == 70  # 30 + 40
        assert token_stats["prompt_tokens"] == 25  # 10 + 15
        assert token_stats["completion_tokens"] == 45  # 20 + 25
        assert token_stats["record_count"] == 4  # 每个请求记录两次（本地+API）

    def test_session_context_integration(self, container):
        """测试会话上下文集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        
        # 测试嵌套会话上下文
        outer_session = generate_session_id()
        inner_session = generate_session_id()
        
        # 外层会话
        with session_context(outer_session):
            service_integration.record_message(
                outer_session, 
                MessageType.USER, 
                "外层会话消息"
            )
            
            # 内层会话
            with session_context(inner_session):
                service_integration.record_message(
                    inner_session, 
                    MessageType.USER, 
                    "内层会话消息"
                )
            
            # 回到外层会话
            service_integration.record_message(
                outer_session, 
                MessageType.ASSISTANT, 
                "外层会话回复"
            )
        
        # 验证两个会话的记录
        outer_query = HistoryQuery(session_id=outer_session)
        outer_result = history_manager.query_history(outer_query)
        assert outer_result.total == 2
        
        inner_query = HistoryQuery(session_id=inner_session)
        inner_result = history_manager.query_history(inner_query)
        assert inner_result.total == 1

    def test_cost_tracking_integration(self, container):
        """测试成本追踪集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        
        session_id = generate_session_id()
        
        # 手动创建成本记录
        cost_record1 = CostRecord(
            record_id="cost-1",
            session_id=session_id,
            timestamp=datetime.now(),
            model="gpt-4",
            provider="openai",
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            prompt_cost=0.001,
            completion_cost=0.006,
            total_cost=0.007
        )
        
        cost_record2 = CostRecord(
            record_id="cost-2",
            session_id=session_id,
            timestamp=datetime.now(),
            model="gpt-3.5-turbo",
            provider="openai",
            prompt_tokens=50,
            completion_tokens=100,
            total_tokens=150,
            prompt_cost=0.00005,
            completion_cost=0.0002,
            total_cost=0.00025
        )
        
        # 记录成本
        history_manager.record_cost(cost_record1)
        history_manager.record_cost(cost_record2)
        
        # 验证成本统计
        cost_stats = history_manager.get_cost_statistics(session_id)
        assert cost_stats["total_cost"] == 0.00725  # 0.007 + 0.00025
        assert cost_stats["prompt_cost"] == 0.00105  # 0.001 + 0.00005
        assert cost_stats["completion_cost"] == 0.0062  # 0.006 + 0.0002
        assert len(cost_stats["models_used"]) == 2
        assert "gpt-4" in cost_stats["models_used"]
        assert "gpt-3.5-turbo" in cost_stats["models_used"]

    def test_history_export_integration(self, container):
        """测试历史导出集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        
        session_id = generate_session_id()
        
        # 创建一些记录
        service_integration.record_session_start(session_id, "test_workflow")
        service_integration.record_message(session_id, MessageType.USER, "测试消息")
        service_integration.record_tool_call(session_id, "test_tool", {"param": "value"})
        service_integration.record_session_end(session_id)
        
        # 导出数据
        exported_data = service_integration.export_session_data(session_id, "json")
        
        # 验证导出数据结构
        assert "summary" in exported_data
        assert "records" in exported_data
        assert "export_format" in exported_data
        assert "exported_at" in exported_data
        
        # 验证摘要
        summary = exported_data["summary"]
        assert summary["session_id"] == session_id
        assert summary["message_count"] == 3  # 开始、用户消息、结束
        assert summary["tool_call_count"] == 1
        
        # 验证记录
        records = exported_data["records"]
        assert len(records) == 4  # 开始、用户消息、工具调用、结束
        
        # 验证记录可序列化
        for record in records:
            assert isinstance(record, dict)
            assert "record_id" in record
            assert "session_id" in record
            assert "timestamp" in record

    def test_error_handling_integration(self, container):
        """测试错误处理集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        
        session_id = generate_session_id()
        
        # 记录正常操作
        service_integration.record_session_start(session_id, "test_workflow")
        
        # 记录错误
        test_error = ValueError("测试错误")
        service_integration.record_error(session_id, test_error, {"context": "test"})
        
        # 记录会话结束
        service_integration.record_session_end(session_id, "error")
        
        # 验证错误记录
        query = HistoryQuery(session_id=session_id)
        result = history_manager.query_history(query)
        
        # 查找错误记录
        error_record = None
        for record in result.records:
            if (record.record_type == "message" and 
                record.message_type == MessageType.SYSTEM and
                "错误" in record.content):
                error_record = record
                break
        
        assert error_record is not None
        assert "测试错误" in error_record.content
        assert error_record.metadata["error_type"] == "ValueError"
        assert error_record.metadata["context"]["context"] == "test"

    def test_concurrent_sessions_integration(self, container):
        """测试并发会话集成"""
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        
        # 创建多个会话
        session_ids = [generate_session_id() for _ in range(3)]
        
        # 为每个会话添加记录
        for i, session_id in enumerate(session_ids):
            service_integration.record_session_start(session_id, f"workflow_{i}")
            service_integration.record_message(
                session_id, 
                MessageType.USER, 
                f"会话{i}的消息"
            )
            service_integration.record_session_end(session_id)
        
        # 验证每个会话的记录
        for i, session_id in enumerate(session_ids):
            query = HistoryQuery(session_id=session_id)
            result = history_manager.query_history(query)
            
            assert result.total == 3  # 开始、消息、结束
            
            # 验证消息内容
            message_record = next(
                r for r in result.records 
                if (r.record_type == "message" and 
                    r.message_type == MessageType.USER)
            )
            assert f"会话{i}的消息" == message_record.content

    def test_memory_storage_integration(self):
        """测试内存存储集成"""
        # 使用内存存储的容器
        container = DependencyContainer()
        register_test_history_services(container)
        
        # 获取服务
        history_manager = container.get(IHistoryManager)
        service_integration = HistoryServiceIntegration(history_manager)
        
        session_id = generate_session_id()
        
        # 记录一些数据
        service_integration.record_session_start(session_id, "test_workflow")
        service_integration.record_message(session_id, MessageType.USER, "内存存储测试")
        
        # 验证记录
        query = HistoryQuery(session_id=session_id)
        result = history_manager.query_history(query)
        
        assert result.total == 2
        assert len(result.records) == 2
        
        # 验证内存存储特性
        storage = container.get(FileHistoryStorage)  # 实际上是MemoryHistoryStorage
        assert isinstance(storage, MemoryHistoryStorage)