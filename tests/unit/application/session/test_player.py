"""播放器单元测试"""

import pytest
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.sessions.player import Player, IPlayer
from src.sessions.event_collector import IEventCollector, EventType


class TestPlayer:
    """播放器测试类"""

    @pytest.fixture
    def mock_event_collector(self):
        """创建模拟事件收集器"""
        collector = Mock(spec=IEventCollector)
        return collector

    @pytest.fixture
    def player(self, mock_event_collector):
        """创建播放器实例"""
        return Player(mock_event_collector)

    @pytest.fixture
    def sample_events(self):
        """示例事件列表"""
        base_time = datetime(2023, 1, 1, 0, 0, 0)
        return [
            {
                "type": EventType.WORKFLOW_START.value,
                "timestamp": (base_time + timedelta(seconds=0)).isoformat(),
                "data": {"workflow_name": "test_workflow"}
            },
            {
                "type": EventType.NODE_START.value,
                "timestamp": (base_time + timedelta(seconds=1)).isoformat(),
                "data": {"node_name": "node1", "node_type": "test"}
            },
            {
                "type": EventType.NODE_END.value,
                "timestamp": (base_time + timedelta(seconds=2)).isoformat(),
                "data": {"node_name": "node1"}
            },
            {
                "type": EventType.WORKFLOW_END.value,
                "timestamp": (base_time + timedelta(seconds=3)).isoformat(),
                "data": {"workflow_name": "test_workflow"}
            }
        ]

    def test_init(self, mock_event_collector):
        """测试初始化"""
        player = Player(mock_event_collector)
        assert player.event_collector == mock_event_collector

    def test_replay_session(self, player, mock_event_collector, sample_events):
        """测试回放会话"""
        session_id = "test-session"
        mock_event_collector.get_events.return_value = sample_events
        
        with patch.object(player, '_replay_events_with_timing') as mock_replay:
            mock_replay.return_value = iter(sample_events)
            
            result = list(player.replay_session(session_id))
            
            assert result == sample_events
            mock_event_collector.get_events.assert_called_once_with(session_id)
            mock_replay.assert_called_once_with(sample_events, 1.0)

    def test_replay_session_with_speed(self, player, mock_event_collector, sample_events):
        """测试带速度的回放会话"""
        session_id = "test-session"
        speed = 2.0
        mock_event_collector.get_events.return_value = sample_events
        
        with patch.object(player, '_replay_events_with_timing') as mock_replay:
            mock_replay.return_value = iter(sample_events)
            
            list(player.replay_session(session_id, speed))
            
            mock_replay.assert_called_once_with(sample_events, speed)

    def test_replay_from_timestamp(self, player, mock_event_collector, sample_events):
        """测试从指定时间点回放会话"""
        session_id = "test-session"
        start_time = datetime(2023, 1, 1, 0, 0, 1)
        filtered_events = sample_events[1:]  # 从第二个事件开始
        
        mock_event_collector.get_events_by_time_range.return_value = filtered_events
        
        with patch.object(player, '_replay_events_with_timing') as mock_replay:
            mock_replay.return_value = iter(filtered_events)
            
            result = list(player.replay_from_timestamp(session_id, start_time))
            
            assert result == filtered_events
            mock_event_collector.get_events_by_time_range.assert_called_once_with(
                session_id, start_time=start_time
            )
            mock_replay.assert_called_once_with(filtered_events, 1.0)

    def test_replay_events(self, player, sample_events):
        """测试回放指定事件列表"""
        with patch.object(player, '_replay_events_with_timing') as mock_replay:
            mock_replay.return_value = iter(sample_events)
            
            result = list(player.replay_events(sample_events))
            
            assert result == sample_events
            mock_replay.assert_called_once_with(sample_events, 1.0)

    def test_replay_events_with_speed(self, player, sample_events):
        """测试带速度回放指定事件列表"""
        speed = 0.5
        
        with patch.object(player, '_replay_events_with_timing') as mock_replay:
            mock_replay.return_value = iter(sample_events)
            
            list(player.replay_events(sample_events, speed))
            
            mock_replay.assert_called_once_with(sample_events, speed)

    def test_replay_events_with_timing_empty(self, player):
        """测试回放空事件列表"""
        result = list(player._replay_events_with_timing([], 1.0))
        assert result == []

    def test_replay_events_with_timing_normal_speed(self, player, sample_events):
        """测试正常速度回放事件"""
        with patch('time.sleep') as mock_sleep:
            result = list(player._replay_events_with_timing(sample_events, 1.0))
            
            assert result == sample_events
            # 验证sleep调用
            assert mock_sleep.call_count == 3  # 3个时间间隔
            mock_sleep.assert_any_call(1.0)  # 第一个间隔
            mock_sleep.assert_any_call(1.0)  # 第二个间隔
            mock_sleep.assert_any_call(1.0)  # 第三个间隔

    def test_replay_events_with_timing_double_speed(self, player, sample_events):
        """测试双倍速度回放事件"""
        with patch('time.sleep') as mock_sleep:
            result = list(player._replay_events_with_timing(sample_events, 2.0))
            
            assert result == sample_events
            # 验证sleep调用时间减半
            mock_sleep.assert_any_call(0.5)  # 第一个间隔
            mock_sleep.assert_any_call(0.5)  # 第二个间隔
            mock_sleep.assert_any_call(0.5)  # 第三个间隔

    def test_replay_events_with_timing_zero_speed(self, player, sample_events):
        """测试零速度回放事件（不等待）"""
        with patch('time.sleep') as mock_sleep:
            result = list(player._replay_events_with_timing(sample_events, 0.0))
            
            assert result == sample_events
            mock_sleep.assert_not_called()

    def test_replay_events_with_timing_unsorted(self, player):
        """测试回放未排序的事件列表"""
        base_time = datetime(2023, 1, 1, 0, 0, 0)
        unsorted_events = [
            {
                "type": EventType.WORKFLOW_END.value,
                "timestamp": (base_time + timedelta(seconds=3)).isoformat(),
                "data": {"workflow_name": "test_workflow"}
            },
            {
                "type": EventType.WORKFLOW_START.value,
                "timestamp": (base_time + timedelta(seconds=0)).isoformat(),
                "data": {"workflow_name": "test_workflow"}
            },
            {
                "type": EventType.NODE_START.value,
                "timestamp": (base_time + timedelta(seconds=1)).isoformat(),
                "data": {"node_name": "node1", "node_type": "test"}
            }
        ]
        
        with patch('time.sleep'):
            result = list(player._replay_events_with_timing(unsorted_events, 1.0))
            
            # 验证事件已按时间排序
            assert result[0]["type"] == EventType.WORKFLOW_START.value
            assert result[1]["type"] == EventType.NODE_START.value
            assert result[2]["type"] == EventType.WORKFLOW_END.value

    def test_print_event_summary_workflow_start(self, player, capsys):
        """测试打印工作流开始事件摘要"""
        event = {
            "type": EventType.WORKFLOW_START.value,
            "data": {"workflow_name": "test_workflow"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "工作流开始: test_workflow" in captured.out

    def test_print_event_summary_workflow_end(self, player, capsys):
        """测试打印工作流结束事件摘要"""
        event = {
            "type": EventType.WORKFLOW_END.value,
            "data": {"workflow_name": "test_workflow"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "工作流结束: test_workflow" in captured.out

    def test_print_event_summary_node_start(self, player, capsys):
        """测试打印节点开始事件摘要"""
        event = {
            "type": EventType.NODE_START.value,
            "data": {"node_name": "node1", "node_type": "test"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "节点开始: node1 (test)" in captured.out

    def test_print_event_summary_node_end(self, player, capsys):
        """测试打印节点结束事件摘要"""
        event = {
            "type": EventType.NODE_END.value,
            "data": {"node_name": "node1"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "节点结束: node1" in captured.out

    def test_print_event_summary_tool_call(self, player, capsys):
        """测试打印工具调用事件摘要"""
        event = {
            "type": EventType.TOOL_CALL.value,
            "data": {"tool_name": "calculator"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "工具调用: calculator" in captured.out

    def test_print_event_summary_tool_result_success(self, player, capsys):
        """测试打印工具结果事件摘要（成功）"""
        event = {
            "type": EventType.TOOL_RESULT.value,
            "data": {"tool_name": "calculator", "success": True}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "工具结果: calculator - 成功" in captured.out

    def test_print_event_summary_tool_result_failure(self, player, capsys):
        """测试打印工具结果事件摘要（失败）"""
        event = {
            "type": EventType.TOOL_RESULT.value,
            "data": {"tool_name": "calculator", "success": False}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "工具结果: calculator - 失败" in captured.out

    def test_print_event_summary_llm_call(self, player, capsys):
        """测试打印LLM调用事件摘要"""
        event = {
            "type": EventType.LLM_CALL.value,
            "data": {"model": "gpt-4"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "LLM调用: gpt-4" in captured.out

    def test_print_event_summary_llm_response(self, player, capsys):
        """测试打印LLM响应事件摘要"""
        event = {
            "type": EventType.LLM_RESPONSE.value,
            "data": {"model": "gpt-4"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "LLM响应: gpt-4" in captured.out

    def test_print_event_summary_error(self, player, capsys):
        """测试打印错误事件摘要"""
        event = {
            "type": EventType.ERROR.value,
            "data": {"error_type": "ValueError", "error_message": "测试错误"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "错误: ValueError - 测试错误" in captured.out

    def test_print_event_summary_other(self, player, capsys):
        """测试打印其他类型事件摘要"""
        event = {
            "type": EventType.INFO.value,
            "data": {"message": "测试信息"}
        }
        
        player._print_event_summary(event)
        
        captured = capsys.readouterr()
        assert "数据:" in captured.out

    def test_analyze_session_no_events(self, player, mock_event_collector):
        """测试分析没有事件的会话"""
        session_id = "test-session"
        mock_event_collector.get_events.return_value = []
        
        result = player.analyze_session(session_id)
        
        assert "error" in result
        assert result["error"] == "会话没有事件记录"

    def test_analyze_session_with_events(self, player, mock_event_collector, sample_events):
        """测试分析有事件的会话"""
        session_id = "test-session"
        mock_event_collector.get_events.return_value = sample_events
        
        result = player.analyze_session(session_id)
        
        # 验证基本统计
        assert result["session_id"] == session_id
        assert result["total_events"] == 4
        assert EventType.WORKFLOW_START.value in result["event_types"]
        assert EventType.NODE_START.value in result["event_types"]
        assert EventType.NODE_END.value in result["event_types"]
        assert EventType.WORKFLOW_END.value in result["event_types"]
        
        # 验证工作流信息
        assert "workflow_info" in result
        assert result["workflow_info"]["start_time"] == sample_events[0]["timestamp"]
        assert result["workflow_info"]["end_time"] == sample_events[3]["timestamp"]
        assert result["workflow_info"]["workflow_name"] == "test_workflow"
        assert result["workflow_info"]["duration_seconds"] == 3.0
        
        # 验证节点信息
        assert "node_info" in result
        assert result["node_info"]["total_nodes"] == 1
        assert result["node_info"]["executed_nodes"] == 1
        assert "node1" in result["node_info"]["average_execution_times"]
        assert result["node_info"]["average_execution_times"]["node1"] == 1.0
        
        # 验证工具信息
        assert "tool_info" in result
        assert result["tool_info"]["total_calls"] == 0
        assert result["tool_info"]["successful_calls"] == 0
        assert result["tool_info"]["failed_calls"] == 0
        
        # 验证错误信息
        assert "error_info" in result
        assert result["error_info"]["total_errors"] == 0
        assert result["error_info"]["error_types"] == {}
        
        # 验证时间线
        assert "timeline" in result
        assert len(result["timeline"]) == 4

    def test_analyze_session_with_tool_events(self, player, mock_event_collector):
        """测试分析包含工具事件的会话"""
        base_time = datetime(2023, 1, 1, 0, 0, 0)
        events_with_tools = [
            {
                "type": EventType.TOOL_CALL.value,
                "timestamp": (base_time + timedelta(seconds=0)).isoformat(),
                "data": {"tool_name": "calculator"}
            },
            {
                "type": EventType.TOOL_RESULT.value,
                "timestamp": (base_time + timedelta(seconds=1)).isoformat(),
                "data": {"tool_name": "calculator", "success": True}
            },
            {
                "type": EventType.TOOL_CALL.value,
                "timestamp": (base_time + timedelta(seconds=2)).isoformat(),
                "data": {"tool_name": "database"}
            },
            {
                "type": EventType.TOOL_RESULT.value,
                "timestamp": (base_time + timedelta(seconds=3)).isoformat(),
                "data": {"tool_name": "database", "success": False}
            }
        ]
        
        mock_event_collector.get_events.return_value = events_with_tools
        
        result = player.analyze_session("test-session")
        
        # 验证工具信息
        assert result["tool_info"]["total_calls"] == 2
        assert result["tool_info"]["successful_calls"] == 1
        assert result["tool_info"]["failed_calls"] == 1

    def test_analyze_session_with_error_events(self, player, mock_event_collector):
        """测试分析包含错误事件的会话"""
        base_time = datetime(2023, 1, 1, 0, 0, 0)
        events_with_errors = [
            {
                "type": EventType.ERROR.value,
                "timestamp": (base_time + timedelta(seconds=0)).isoformat(),
                "data": {"error_type": "ValueError", "error_message": "测试错误1"}
            },
            {
                "type": EventType.ERROR.value,
                "timestamp": (base_time + timedelta(seconds=1)).isoformat(),
                "data": {"error_type": "ValueError", "error_message": "测试错误2"}
            },
            {
                "type": EventType.ERROR.value,
                "timestamp": (base_time + timedelta(seconds=2)).isoformat(),
                "data": {"error_type": "TypeError", "error_message": "测试错误3"}
            }
        ]
        
        mock_event_collector.get_events.return_value = events_with_errors
        
        result = player.analyze_session("test-session")
        
        # 验证错误信息
        assert result["error_info"]["total_errors"] == 3
        assert result["error_info"]["error_types"]["ValueError"] == 2
        assert result["error_info"]["error_types"]["TypeError"] == 1

    def test_get_event_summary_workflow_start(self, player):
        """测试获取工作流开始事件摘要"""
        event = {
            "type": EventType.WORKFLOW_START.value,
            "data": {"workflow_name": "test_workflow"}
        }
        
        result = player._get_event_summary(event)
        
        assert result == "工作流开始: test_workflow"

    def test_get_event_summary_node_start(self, player):
        """测试获取节点开始事件摘要"""
        event = {
            "type": EventType.NODE_START.value,
            "data": {"node_name": "node1"}
        }
        
        result = player._get_event_summary(event)
        
        assert result == "节点开始: node1"

    def test_get_event_summary_tool_call(self, player):
        """测试获取工具调用事件摘要"""
        event = {
            "type": EventType.TOOL_CALL.value,
            "data": {"tool_name": "calculator"}
        }
        
        result = player._get_event_summary(event)
        
        assert result == "工具调用: calculator"

    def test_get_event_summary_error(self, player):
        """测试获取错误事件摘要"""
        event = {
            "type": EventType.ERROR.value,
            "data": {"error_type": "ValueError"}
        }
        
        result = player._get_event_summary(event)
        
        assert result == "错误: ValueError"

    def test_get_event_summary_other(self, player):
        """测试获取其他类型事件摘要"""
        event = {
            "type": EventType.INFO.value,
            "data": {"message": "测试信息"}
        }
        
        result = player._get_event_summary(event)
        
        assert result == "事件: info"

    def test_replay_session_interactive_no_events(self, player, mock_event_collector, capsys):
        """测试交互式回放没有事件的会话"""
        session_id = "test-session"
        mock_event_collector.get_events.return_value = []
        
        player.replay_session_interactive(session_id)
        
        captured = capsys.readouterr()
        assert f"会话 {session_id} 没有事件记录" in captured.out

    def test_replay_session_interactive_with_events(self, player, mock_event_collector, sample_events):
        """测试交互式回放有事件的会话"""
        session_id = "test-session"
        mock_event_collector.get_events.return_value = sample_events
        
        with patch('builtins.input', side_effect=["", "q"]):  # 第一个事件播放，然后退出
            player.replay_session_interactive(session_id)
        
        # 验证调用了get_events
        mock_event_collector.get_events.assert_called_once_with(session_id)


class TestIPlayer:
    """播放器接口测试类"""

    def test_interface_methods(self):
        """测试接口方法定义"""
        # 验证接口定义了所有必需的方法
        assert hasattr(IPlayer, 'replay_session')
        assert hasattr(IPlayer, 'replay_from_timestamp')
        assert hasattr(IPlayer, 'replay_events')
        
        # 验证方法是抽象方法
        assert getattr(IPlayer.replay_session, '__isabstractmethod__', False)
        assert getattr(IPlayer.replay_from_timestamp, '__isabstractmethod__', False)
        assert getattr(IPlayer.replay_events, '__isabstractmethod__', False)
