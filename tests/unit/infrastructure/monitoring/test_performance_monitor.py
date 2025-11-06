"""性能监控系统测试

测试新创建的统一性能监控系统。
"""

import pytest
from typing import Dict, Any

from src.infrastructure.monitoring import (
    IPerformanceMonitor,
    BasePerformanceMonitor,
    CheckpointPerformanceMonitor,
    LLMPerformanceMonitor,
    PerformanceMonitorFactory
)


class TestPerformanceMonitorInterface:
    """性能监控接口测试"""
    
    def test_interface_methods(self):
        """测试接口方法定义"""
        # 这是一个接口测试，确保接口定义正确
        # 实际实现会在具体类中测试
        pass


class TestBasePerformanceMonitor:
    """基础性能监控器测试"""
    
    def test_initialization(self):
        """测试初始化"""
        monitor = BasePerformanceMonitor(max_history_size=500)
        assert monitor is not None
        
        # 检查默认配置
        metrics = monitor.get_all_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "timers" in metrics
        
    def test_counter_operations(self):
        """测试计数器操作"""
        monitor = BasePerformanceMonitor()
        
        # 增加计数器
        monitor.increment_counter("test_counter", 1.0)
        monitor.increment_counter("test_counter", 2.0)
        
        # 获取计数器值
        from src.infrastructure.monitoring.interfaces import MetricType
        value = monitor.get_metric("test_counter", MetricType.COUNTER)
        assert value == 3.0
        
    def test_gauge_operations(self):
        """测试仪表值操作"""
        monitor = BasePerformanceMonitor()
        
        # 设置仪表值
        monitor.set_gauge("test_gauge", 42.0)
        
        # 获取仪表值
        from src.infrastructure.monitoring.interfaces import MetricType
        value = monitor.get_metric("test_gauge", MetricType.GAUGE)
        assert value == 42.0
        
    def test_timer_operations(self):
        """测试计时器操作"""
        monitor = BasePerformanceMonitor()
        
        # 记录时间
        monitor.record_timer("test_timer", 1.5)
        monitor.record_timer("test_timer", 2.5)
        
        # 获取计时器统计
        from src.infrastructure.monitoring.interfaces import MetricType
        stats = monitor.get_metric("test_timer", MetricType.TIMER)
        assert stats is not None
        assert stats["count"] == 2
        assert stats["average"] == 2.0
        
    def test_reset_metrics(self):
        """测试重置指标"""
        monitor = BasePerformanceMonitor()
        
        # 添加一些指标
        monitor.increment_counter("test_counter", 1.0)
        monitor.set_gauge("test_gauge", 42.0)
        
        # 重置指标
        monitor.reset_metrics()
        
        # 检查指标是否被重置
        metrics = monitor.get_all_metrics()
        assert len(metrics["counters"]) == 0
        assert len(metrics["gauges"]) == 0


class TestSpecificMonitors:
    """具体监控器测试"""
    
    def test_checkpoint_monitor(self):
        """测试检查点监控器"""
        monitor = CheckpointPerformanceMonitor()
        
        # 测试检查点保存记录
        monitor.record_checkpoint_save(duration=0.5, size=1024, success=True)
        
        # 检查指标是否被记录
        metrics = monitor.get_all_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        
    def test_llm_monitor(self):
        """测试LLM监控器"""
        monitor = LLMPerformanceMonitor()
        
        # 测试LLM调用记录
        monitor.record_llm_call(
            model="gpt-4",
            provider="openai",
            response_time=2.1,
            prompt_tokens=100,
            completion_tokens=200,
            total_tokens=300,
            success=True
        )
        
        # 检查指标是否被记录
        metrics = monitor.get_all_metrics()
        assert "counters" in metrics
        assert "gauges" in metrics
        assert "timers" in metrics


class TestPerformanceMonitorFactory:
    """性能监控器工厂测试"""
    
    def test_factory_singleton(self):
        """测试工厂单例"""
        factory1 = PerformanceMonitorFactory.get_instance()
        factory2 = PerformanceMonitorFactory.get_instance()
        
        assert factory1 is factory2
        
    def test_create_monitor(self):
        """测试创建监控器"""
        factory = PerformanceMonitorFactory.get_instance()
        
        # 创建基础监控器
        base_monitor = factory.create_monitor("base")
        assert isinstance(base_monitor, BasePerformanceMonitor)
        
        # 创建检查点监控器
        checkpoint_monitor = factory.create_monitor("checkpoint")
        assert isinstance(checkpoint_monitor, CheckpointPerformanceMonitor)
        
        # 创建LLM监控器
        llm_monitor = factory.create_monitor("llm")
        assert isinstance(llm_monitor, LLMPerformanceMonitor)
        
    def test_get_monitor(self):
        """测试获取监控器"""
        factory = PerformanceMonitorFactory.get_instance()
        
        # 获取已创建的监控器
        checkpoint_monitor = factory.get_monitor("checkpoint")
        assert checkpoint_monitor is not None
        assert isinstance(checkpoint_monitor, CheckpointPerformanceMonitor)
        
    def test_get_all_monitors(self):
        """测试获取所有监控器"""
        factory = PerformanceMonitorFactory.get_instance()
        
        # 获取所有监控器
        monitors = factory.get_all_monitors()
        assert isinstance(monitors, dict)
        assert len(monitors) >= 3  # 至少有base, checkpoint, llm监控器