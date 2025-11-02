"""TokenUsageTracker单元测试"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import List
from langchain_core.messages import HumanMessage

from src.application.history.token_tracker import TokenUsageTracker, generate_id
from src.domain.history.llm_models import TokenUsageRecord
from src.domain.history.interfaces import IHistoryManager
from src.infrastructure.llm.token_calculators.base import ITokenCalculator


class TestTokenUsageTracker:
    """TokenUsageTracker测试"""

    def test_init(self) -> None:
        """测试初始化"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        assert tracker.token_counter == mock_token_counter
        assert tracker.history_manager == mock_history_manager
        assert tracker.usage_history == []

    def test_track_request_with_session_id(self) -> None:
        """测试追踪请求（有会话ID）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        # 模拟消息和token计数
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = 10
        
        with patch('src.application.history.token_tracker.generate_id', return_value='test-id'):
            with patch('src.application.history.token_tracker.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now
                
                result = tracker.track_request(mock_messages, "gpt-4", "openai", "session-1")
                
                # 验证token计数被调用
                mock_token_counter.count_messages_tokens.assert_called_once_with(mock_messages)
                
                # 验证历史记录被保存
                mock_history_manager.record_token_usage.assert_called_once()
                call_args = mock_history_manager.record_token_usage.call_args[0][0]
                
                assert isinstance(call_args, TokenUsageRecord)
                assert call_args.record_id == 'test-id'
                assert call_args.session_id == "session-1"
                assert call_args.timestamp == mock_now
                assert call_args.model == "gpt-4"
                assert call_args.provider == "openai"
                assert call_args.prompt_tokens == 10
                assert call_args.completion_tokens == 0
                assert call_args.total_tokens == 10
                assert call_args.source == "local"
                assert call_args.confidence == 0.7
                
                # 验证返回值
                assert result == call_args
                
                # 验证使用历史被更新
                assert len(tracker.usage_history) == 1
                assert tracker.usage_history[0] == call_args

    def test_track_request_without_session_id(self) -> None:
        """测试追踪请求（无会话ID）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)

        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = 10

        with patch('src.application.history.token_tracker.generate_id', return_value='test-id'):
            with patch('src.application.history.token_tracker.datetime') as mock_datetime:
                mock_now = datetime(2023, 10, 25, 12, 0, 0)
                mock_datetime.now.return_value = mock_now

                with patch('src.application.history.token_tracker.get_current_session_id', return_value="current-session"):
                    result = tracker.track_request(mock_messages, "gpt-4", "openai")

                    # 验证使用当前会话ID
                    call_args = mock_history_manager.record_token_usage.call_args[0][0]
                    assert call_args.session_id == "current-session"

    def test_track_request_no_current_session(self) -> None:
        """测试追踪请求（无当前会话）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = 10
        
        with patch('src.application.history.token_tracker.generate_id', return_value='test-id'):
            with patch('src.application.history.token_tracker.datetime'):
                with patch('src.application.history.token_tracker.get_current_session_id', return_value=None):
                    result = tracker.track_request(mock_messages, "gpt-4", "openai")
                    
                    # 验证使用默认会话ID
                    call_args = mock_history_manager.record_token_usage.call_args[0][0]
                    assert call_args.session_id == "default_session"

    def test_track_request_zero_tokens(self) -> None:
        """测试追踪请求（零token）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="")]
        mock_token_counter.count_messages_tokens.return_value = 0
        
        with patch('src.application.history.token_tracker.generate_id', return_value='test-id'):
            with patch('src.application.history.token_tracker.datetime'):
                result = tracker.track_request(mock_messages, "gpt-4", "openai", "session-1")
                
                # 验证零token处理
                call_args = mock_history_manager.record_token_usage.call_args[0][0]
                assert call_args.prompt_tokens == 0
                assert call_args.completion_tokens == 0
                assert call_args.total_tokens == 0

    def test_track_request_token_counter_none(self) -> None:
        """测试追踪请求（token计数器返回None）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = None
        
        with patch('src.application.history.token_tracker.generate_id', return_value='test-id'):
            with patch('src.application.history.token_tracker.datetime'):
                result = tracker.track_request(mock_messages, "gpt-4", "openai", "session-1")
                
                # 验证None处理为0
                call_args = mock_history_manager.record_token_usage.call_args[0][0]
                assert call_args.prompt_tokens == 0
                assert call_args.completion_tokens == 0
                assert call_args.total_tokens == 0

    def test_update_from_response_openai_format(self) -> None:
        """测试从API响应更新（OpenAI格式）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        # 创建原始记录
        original_record = TokenUsageRecord(
            record_id='test-id',
            session_id='session-1',
            timestamp=datetime.now(),
            model='gpt-4',
            provider='openai',
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            source='local',
            confidence=0.7
        )
        
        # OpenAI API响应
        api_response = {
            "usage": {
                "prompt_tokens": 15,
                "completion_tokens": 25,
                "total_tokens": 40
            }
        }
        
        # 更新记录
        updated_record = tracker.update_from_response(original_record, api_response)
        
        # 验证更新
        assert updated_record.prompt_tokens == 15
        assert updated_record.completion_tokens == 25
        assert updated_record.total_tokens == 40
        assert updated_record.source == "api"
        assert updated_record.confidence == 1.0
        
        # 验证历史记录被保存
        mock_history_manager.record_token_usage.assert_called_once_with(updated_record)

    def test_update_from_response_gemini_format(self) -> None:
        """测试从API响应更新（Gemini格式）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        original_record = TokenUsageRecord(
            record_id='test-id',
            session_id='session-1',
            timestamp=datetime.now(),
            model='gemini-pro',
            provider='google',
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            source='local',
            confidence=0.7
        )
        
        # Gemini API响应
        api_response = {
            "usageMetadata": {
                "promptTokenCount": 20,
                "candidatesTokenCount": 30,
                "totalTokenCount": 50
            }
        }
        
        updated_record = tracker.update_from_response(original_record, api_response)
        
        # 验证更新
        assert updated_record.prompt_tokens == 20
        assert updated_record.completion_tokens == 30
        assert updated_record.total_tokens == 50
        assert updated_record.source == "api"
        assert updated_record.confidence == 1.0

    def test_update_from_response_anthropic_format(self) -> None:
        """测试从API响应更新（Anthropic格式）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        original_record = TokenUsageRecord(
            record_id='test-id',
            session_id='session-1',
            timestamp=datetime.now(),
            model='claude-3',
            provider='anthropic',
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            source='local',
            confidence=0.7
        )
        
        # Anthropic API响应
        api_response = {
            "usage": {
                "input_tokens": 25,
                "output_tokens": 35
            }
        }
        
        updated_record = tracker.update_from_response(original_record, api_response)
        
        # 验证更新
        assert updated_record.prompt_tokens == 25
        assert updated_record.completion_tokens == 35
        assert updated_record.total_tokens == 60  # 25 + 35
        assert updated_record.source == "api"
        assert updated_record.confidence == 1.0

    def test_update_from_response_no_usage(self) -> None:
        """测试从API响应更新（无使用信息）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        original_record = TokenUsageRecord(
            record_id='test-id',
            session_id='session-1',
            timestamp=datetime.now(),
            model='gpt-4',
            provider='openai',
            prompt_tokens=10,
            completion_tokens=0,
            total_tokens=10,
            source='local',
            confidence=0.7
        )
        
        # 无使用信息的API响应
        api_response = {
            "content": "Response content"
        }
        
        updated_record = tracker.update_from_response(original_record, api_response)
        
        # 验证没有更新
        assert updated_record.prompt_tokens == 10
        assert updated_record.completion_tokens == 0
        assert updated_record.total_tokens == 10
        assert updated_record.source == "local"
        assert updated_record.confidence == 0.7

    def test_estimate_tokens(self) -> None:
        """测试估算Token数量"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = 15
        
        result = tracker.estimate_tokens(mock_messages)
        
        assert result == 15
        mock_token_counter.count_messages_tokens.assert_called_once_with(mock_messages)

    def test_estimate_tokens_none(self) -> None:
        """测试估算Token数量（返回None）"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = None
        
        result = tracker.estimate_tokens(mock_messages)
        
        assert result == 0

    def test_get_session_token_usage(self) -> None:
        """测试获取会话Token使用统计"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        expected_stats = {
            "session_id": "session-1",
            "total_tokens": 100,
            "prompt_tokens": 60,
            "completion_tokens": 40
        }
        
        mock_history_manager.get_token_statistics.return_value = expected_stats
        
        result = tracker.get_session_token_usage("session-1")
        
        assert result == expected_stats
        mock_history_manager.get_token_statistics.assert_called_once_with("session-1")

    def test_multiple_requests_tracking(self) -> None:
        """测试多个请求追踪"""
        mock_token_counter = Mock(spec=ITokenCalculator)
        mock_history_manager = Mock(spec=IHistoryManager)
        tracker = TokenUsageTracker(mock_token_counter, mock_history_manager)
        
        mock_messages = [HumanMessage(content="Hello")]
        mock_token_counter.count_messages_tokens.return_value = 10
        
        with patch('src.application.history.token_tracker.generate_id') as mock_generate_id:
            mock_generate_id.side_effect = ["id-1", "id-2"]
            
            with patch('src.application.history.token_tracker.datetime'):
                # 追踪两个请求
                tracker.track_request(mock_messages, "gpt-4", "openai", "session-1")
                tracker.track_request(mock_messages, "gpt-4", "openai", "session-1")
                
                # 验证使用历史
                assert len(tracker.usage_history) == 2
                assert tracker.usage_history[0].record_id == "id-1"
                assert tracker.usage_history[1].record_id == "id-2"
                
                # 验证历史记录被保存两次
                assert mock_history_manager.record_token_usage.call_count == 2


class TestGenerateId:
    """generate_id函数测试"""

    def test_generate_id(self) -> None:
        """测试生成ID"""
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = "test-uuid"
            
            result = generate_id()
            
            assert result == "test-uuid"
            mock_uuid.assert_called_once()