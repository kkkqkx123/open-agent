"""指标收集器单元测试"""

import pytest
import json
import tempfile
from pathlib import Path

from src.logger.metrics import (
    LLMMetric, 
    ToolMetric, 
    SessionMetric, 
    MetricsCollector,
    IMetricsCollector
)


class TestLLMMetric:
    """LLM指标测试类"""
    
    def test_llm_metric_creation(self) -> None:
        """测试LLM指标创建"""
        metric = LLMMetric(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_time=2.5,
            success=True
        )
        
        assert metric.model == "gpt-4"
        assert metric.input_tokens == 100
        assert metric.output_tokens == 50
        assert metric.total_time == 2.5
        assert metric.success is True
        assert metric.error_type is None
        assert metric.timestamp is not None
    
    def test_llm_metric_with_error(self) -> None:
        """测试带错误的LLM指标"""
        metric = LLMMetric(
            model="gpt-4",
            input_tokens=100,
            output_tokens=0,
            total_time=1.0,
            success=False,
            error_type="timeout"
        )
        
        assert metric.success is False
        assert metric.error_type == "timeout"
    
    def test_llm_metric_to_dict(self) -> None:
        """测试LLM指标转换为字典"""
        metric = LLMMetric(
            model="gpt-4",
            input_tokens=100,
            output_tokens=50,
            total_time=2.5
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict['model'] == "gpt-4"
        assert metric_dict['input_tokens'] == 100
        assert metric_dict['output_tokens'] == 50
        assert metric_dict['total_time'] == 2.5
        assert 'timestamp' in metric_dict


class TestToolMetric:
    """工具指标测试类"""
    
    def test_tool_metric_creation(self) -> None:
        """测试工具指标创建"""
        metric = ToolMetric(
            tool="search_tool",
            count=10,
            success_count=8,
            total_time=5.0
        )
        
        assert metric.tool == "search_tool"
        assert metric.count == 10
        assert metric.success_count == 8
        assert metric.total_time == 5.0
    
    def test_success_rate(self) -> None:
        """测试成功率计算"""
        # 成功情况
        metric = ToolMetric("tool", count=10, success_count=8, total_time=5.0)
        assert metric.success_rate == 0.8
        
        # 全部成功
        metric = ToolMetric("tool", count=5, success_count=5, total_time=2.5)
        assert metric.success_rate == 1.0
        
        # 全部失败
        metric = ToolMetric("tool", count=5, success_count=0, total_time=2.5)
        assert metric.success_rate == 0.0
        
        # 零调用
        metric = ToolMetric("tool", count=0, success_count=0, total_time=0.0)
        assert metric.success_rate == 0.0
    
    def test_avg_time(self) -> None:
        """测试平均时间计算"""
        metric = ToolMetric("tool", count=10, success_count=8, total_time=5.0)
        assert metric.avg_time == 0.5
        
        # 零调用
        metric = ToolMetric("tool", count=0, success_count=0, total_time=0.0)
        assert metric.avg_time == 0.0
    
    def test_tool_metric_to_dict(self) -> None:
        """测试工具指标转换为字典"""
        metric = ToolMetric(
            tool="search_tool",
            count=10,
            success_count=8,
            total_time=5.0
        )
        
        metric_dict = metric.to_dict()
        
        assert metric_dict['tool'] == "search_tool"
        assert metric_dict['count'] == 10
        assert metric_dict['success_count'] == 8
        assert metric_dict['success_rate'] == 0.8
        assert metric_dict['avg_time'] == 0.5
        assert 'timestamp' in metric_dict


class TestSessionMetric:
    """会话指标测试类"""
    
    def test_session_metric_creation(self) -> None:
        """测试会话指标创建"""
        session = SessionMetric("test_session")
        
        assert session.session_id == "test_session"
        assert session.start_time is not None
        assert session.end_time is None
        assert session.total_messages == 0
        assert session.total_errors == 0
        assert len(session.llm_calls) == 0
        assert len(session.tool_calls) == 0
    
    def test_session_duration(self) -> None:
        """测试会话持续时间"""
        session = SessionMetric("test_session")
        
        # 未结束的会话
        duration = session.duration
        assert duration >= 0
        
        # 结束会话
        session.end_session()
        assert session.end_time is not None
        assert session.duration >= 0
    
    def test_total_llm_calls(self) -> None:
        """测试总LLM调用次数"""
        session = SessionMetric("test_session")
        
        # 添加LLM调用
        session.llm_calls.append(LLMMetric("gpt-4", input_tokens=10, output_tokens=50, total_time=2.0))
        session.llm_calls.append(LLMMetric("gpt-3.5", input_tokens=50, output_tokens=25, total_time=1.0, count=2))
        
        assert session.total_llm_calls == 3  # 1 + 2
    
    def test_total_tool_calls(self) -> None:
        """测试总工具调用次数"""
        session = SessionMetric("test_session")
        
        # 添加工具调用
        session.tool_calls.append(ToolMetric("search", 5, 4, 2.0))
        session.tool_calls.append(ToolMetric("calculate", 3, 3, 1.0))
        
        assert session.total_tool_calls == 8  # 5 + 3
    
    def test_total_tokens(self) -> None:
        """测试总token数"""
        session = SessionMetric("test_session")
        
        # 添加LLM调用
        session.llm_calls.append(LLMMetric("gpt-4", input_tokens=10, output_tokens=50, total_time=2.0))
        session.llm_calls.append(LLMMetric("gpt-3.5", input_tokens=50, output_tokens=25, total_time=1.0))
        
        assert session.total_tokens == 135  # (10+50) + (50+25)
    
    def test_record_message_and_error(self):
        """测试记录消息和错误"""
        session = SessionMetric("test_session")
        
        # 记录消息
        session.total_messages += 1
        session.total_messages += 1
        assert session.total_messages == 2
        
        # 记录错误
        session.total_errors += 1
        session.total_errors += 1
        assert session.total_errors == 2
    
    def test_session_to_dict(self) -> None:
        """测试会话指标转换为字典"""
        session = SessionMetric("test_session")
        
        # 添加一些数据
        session.llm_calls.append(LLMMetric("gpt-4", input_tokens=10, output_tokens=50, total_time=2.0))
        session.tool_calls.append(ToolMetric("search", count=5, success_count=4, total_time=2.0))
        session.total_messages += 1
        session.total_errors += 1
        
        session_dict = session.to_dict()
        
        assert session_dict['session_id'] == "test_session"
        assert session_dict['total_messages'] == 1
        assert session_dict['total_errors'] == 1
        assert session_dict['total_llm_calls'] == 1
        assert session_dict['total_tool_calls'] == 5
        assert session_dict['total_tokens'] == 60
        assert len(session_dict['llm_calls']) == 1
        assert len(session_dict['tool_calls']) == 1


class TestMetricsCollector:
    """指标收集器测试类"""
    
    def test_collector_creation(self) -> None:
        """测试收集器创建"""
        collector = MetricsCollector()
        
        assert isinstance(collector, IMetricsCollector)
        assert collector.max_sessions == 1000
        assert collector.max_history == 100
    
    def test_record_llm_metric(self) -> None:
        """测试记录LLM指标"""
        collector = MetricsCollector()
        
        # 记录LLM调用
        collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        collector.record_llm_metric("gpt-4", 200, 100, 3.0)
        collector.record_llm_metric("gpt-3.5", 50, 25, 1.0, success=False)
        
        # 检查全局统计
        stats = collector.export_stats()
        
        assert stats['global']['total_llm_calls'] == 3
        assert stats['global']['total_tokens'] == 525  # (100+50) + (200+100) + (50+25)
        assert stats['global']['models']['gpt-4']['calls'] == 2
        assert stats['global']['models']['gpt-4']['tokens'] == 450
        assert stats['global']['models']['gpt-3.5']['calls'] == 1
        assert stats['global']['models']['gpt-3.5']['tokens'] == 75
        assert stats['global']['total_errors'] == 1  # 一次失败调用
    
    def test_record_tool_metric(self) -> None:
        """测试记录工具指标"""
        collector = MetricsCollector()
        
        # 记录工具调用
        collector.record_tool_metric("search", True, 0.5)
        collector.record_tool_metric("search", False, 0.3)
        collector.record_tool_metric("calculate", True, 0.2)
        
        # 检查全局统计
        stats = collector.export_stats()
        
        assert stats['global']['total_tool_calls'] == 3
        assert stats['global']['tools']['search']['calls'] == 2
        assert stats['global']['tools']['search']['successes'] == 1
        assert stats['global']['tools']['search']['errors'] == 1
        assert stats['global']['tools']['calculate']['calls'] == 1
        assert stats['global']['tools']['calculate']['successes'] == 1
        assert stats['global']['tools']['calculate']['errors'] == 0
    
    def test_session_management(self) -> None:
        """测试会话管理"""
        collector = MetricsCollector()
        
        # 开始会话
        collector.record_session_start("test_session")
        
        # 记录一些指标
        collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        collector.record_tool_metric("search", True, 0.5)
        collector.record_message("test_session")
        collector.record_error("test_session", "timeout")
        
        # 结束会话
        collector.record_session_end("test_session")
        
        # 检查会话统计
        session_stats = collector.export_stats("test_session")
        
        assert session_stats['session_id'] == "test_session"
        assert session_stats['total_messages'] == 1
        assert session_stats['total_errors'] == 1
        assert session_stats['end_time'] is not None
    
    def test_clear_metrics(self) -> None:
        """测试清除指标"""
        collector = MetricsCollector()
        
        # 记录一些指标
        collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        collector.record_session_start("test_session")
        
        # 验证数据存在
        stats = collector.export_stats()
        assert stats['global']['total_llm_calls'] == 1
        assert len(stats['sessions']) == 1
        
        # 清除所有指标
        collector.clear_metrics()
        
        # 验证数据已清除
        stats = collector.export_stats()
        assert stats['global']['total_llm_calls'] == 0
        assert len(stats['sessions']) == 0
    
    def test_clear_session_metrics(self):
        """测试清除特定会话指标"""
        collector = MetricsCollector()
        
        # 创建多个会话
        collector.record_session_start("session1")
        collector.record_session_start("session2")
        
        # 记录一些指标
        collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        
        # 验证会话存在
        stats = collector.export_stats()
        assert len(stats['sessions']) == 2
        
        # 清除特定会话
        collector.clear_metrics("session1")
        
        # 验证只有特定会话被清除
        stats = collector.export_stats()
        assert len(stats['sessions']) == 1
        assert "session1" not in stats['sessions']
        assert "session2" in stats['sessions']
    
    def test_save_and_load_metrics(self) -> None:
        """测试保存和加载指标"""
        collector = MetricsCollector()
        
        # 记录一些指标
        collector.record_llm_metric("gpt-4", 100, 50, 2.0)
        collector.record_session_start("test_session")
        
        # 保存到临时文件
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            collector.save_to_file(temp_file)
            
            # 验证文件存在且包含数据
            assert Path(temp_file).exists()
            
            with open(temp_file, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['global']['total_llm_calls'] == 1
            assert len(saved_data['sessions']) == 1
            
        finally:
            # 清理临时文件
            Path(temp_file).unlink(missing_ok=True)
    
    def test_max_sessions_limit(self) -> None:
        """测试最大会话数限制"""
        collector = MetricsCollector(max_sessions=2)
        
        # 创建超过限制的会话
        collector.record_session_start("session1")
        collector.record_session_start("session2")
        collector.record_session_start("session3")
        
        # 验证只有最新的会话保留
        stats = collector.export_stats()
        assert len(stats['sessions']) == 2
        assert "session1" not in stats['sessions']
        assert "session2" in stats['sessions']
        assert "session3" in stats['sessions']