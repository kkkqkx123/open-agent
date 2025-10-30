"""内置Hook单元测试"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock

from src.infrastructure.graph.hooks.builtin import (
    DeadLoopDetectionHook, PerformanceMonitoringHook, ErrorRecoveryHook,
    LoggingHook, MetricsCollectionHook, create_builtin_hook
)
from src.infrastructure.graph.hooks.interfaces import HookContext, HookPoint
from src.infrastructure.graph.hooks.config import HookType
from src.domain.agent.state import AgentState
from src.infrastructure.graph.registry import NodeExecutionResult


class TestDeadLoopDetectionHook:
    """死循环检测Hook测试"""
    
    def test_creation(self):
        """测试创建"""
        config = {
            "max_iterations": 10,
            "fallback_node": "test_fallback",
            "log_level": "ERROR"
        }
        hook = DeadLoopDetectionHook(config)
        
        assert hook.hook_type == HookType.DEAD_LOOP_DETECTION
        assert hook.max_iterations == 10
        assert hook.fallback_node == "test_fallback"
        assert hook.log_level == "ERROR"
    
    def test_before_execute_normal(self):
        """测试正常执行前检查"""
        config = {"max_iterations": 5}
        hook = DeadLoopDetectionHook(config)
        
        # Mock Hook管理器
        mock_manager = Mock()
        mock_manager.get_execution_count.return_value = 3
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE,
            hook_manager=mock_manager
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is True
    
    def test_before_execute_dead_loop_detected(self):
        """测试检测到死循环"""
        config = {"max_iterations": 5}
        hook = DeadLoopDetectionHook(config)
        
        # Mock Hook管理器
        mock_manager = Mock()
        mock_manager.get_execution_count.return_value = 5
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE,
            hook_manager=mock_manager
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is False
        assert result.force_next_node == "dead_loop_check"
        assert result.metadata["dead_loop_detected"] is True
    
    def test_after_execute_increment_count(self):
        """测试执行后增加计数"""
        config = {"max_iterations": 5}
        hook = DeadLoopDetectionHook(config)
        
        # Mock Hook管理器
        mock_manager = Mock()
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            hook_manager=mock_manager
        )
        
        result = hook.after_execute(context)
        assert result.should_continue is True
        mock_manager.increment_execution_count.assert_called_once_with("test_node")


class TestPerformanceMonitoringHook:
    """性能监控Hook测试"""
    
    def test_creation(self):
        """测试创建"""
        config = {
            "timeout_threshold": 30.0,
            "slow_execution_threshold": 10.0
        }
        hook = PerformanceMonitoringHook(config)
        
        assert hook.hook_type == HookType.PERFORMANCE_MONITORING
        assert hook.timeout_threshold == 30.0
        assert hook.slow_execution_threshold == 10.0
    
    def test_before_execute_record_start_time(self):
        """测试执行前记录开始时间"""
        config = {"timeout_threshold": 30.0}
        hook = PerformanceMonitoringHook(config)
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is True
        assert "performance_start_time" in context.metadata
    
    @patch('time.time')
    def test_after_execute_normal(self, mock_time):
        """测试正常执行后监控"""
        mock_time.side_effect = [1000.0, 1005.0]  # 开始时间和结束时间
        
        config = {"timeout_threshold": 30.0, "slow_execution_threshold": 10.0}
        hook = PerformanceMonitoringHook(config)
        
        # Mock Hook管理器
        mock_manager = Mock()
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            hook_manager=mock_manager,
            metadata={"performance_start_time": 1000.0}
        )
        
        result = hook.after_execute(context)
        assert result.should_continue is True
        assert result.metadata["execution_time"] == 5.0
        mock_manager.update_performance_stats.assert_called_once_with("test_node", 5.0, True)
    
    @patch('time.time')
    def test_after_execute_timeout(self, mock_time):
        """测试执行超时"""
        mock_time.side_effect = [1000.0, 1040.0]  # 超过30秒阈值
        
        config = {"timeout_threshold": 30.0}
        hook = PerformanceMonitoringHook(config)
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            metadata={"performance_start_time": 1000.0}
        )
        
        result = hook.after_execute(context)
        assert result.should_continue is False
        assert result.force_next_node == "timeout_handler"
        assert result.metadata["timeout_detected"] is True


class TestErrorRecoveryHook:
    """错误恢复Hook测试"""
    
    def test_creation(self):
        """测试创建"""
        config = {
            "max_retries": 5,
            "fallback_node": "test_fallback",
            "retry_delay": 2.0
        }
        hook = ErrorRecoveryHook(config)
        
        assert hook.hook_type == HookType.ERROR_RECOVERY
        assert hook.max_retries == 5
        assert hook.fallback_node == "test_fallback"
        assert hook.retry_delay == 2.0
    
    def test_before_execute_normal(self):
        """测试正常执行前检查"""
        config = {"max_retries": 3}
        hook = ErrorRecoveryHook(config)
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE,
            metadata={"retry_count": 1}
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is True
    
    def test_before_execute_max_retries_exceeded(self):
        """测试超过最大重试次数"""
        config = {"max_retries": 3}
        hook = ErrorRecoveryHook(config)
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE,
            metadata={"retry_count": 3}
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is False
        assert result.force_next_node == "error_handler"
        assert result.metadata["max_retries_exceeded"] is True
    
    @patch('time.sleep')
    def test_on_error_retry(self, mock_sleep):
        """测试错误重试"""
        config = {"max_retries": 3, "retry_delay": 1.0}
        hook = ErrorRecoveryHook(config)
        
        state = Mock(spec=AgentState)
        error = Exception("test error")
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.ON_ERROR,
            error=error,
            metadata={"retry_count": 1}
        )
        
        result = hook.on_error(context)
        assert result.should_continue is True
        assert result.metadata["retry_scheduled"] is True
        assert result.metadata["retry_count"] == 2
        mock_sleep.assert_called_once_with(1.0)
    
    def test_on_error_unrecoverable(self):
        """测试不可恢复错误"""
        config = {"max_retries": 3, "retry_on_exceptions": ["ValueError"]}
        hook = ErrorRecoveryHook(config)
        
        state = Mock(spec=AgentState)
        error = TypeError("test error")  # 不在重试列表中
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.ON_ERROR,
            error=error
        )
        
        result = hook.on_error(context)
        assert result.should_continue is False
        assert result.force_next_node == "error_handler"
        assert result.metadata["unrecoverable_error"] is True


class TestLoggingHook:
    """日志Hook测试"""
    
    def test_creation(self):
        """测试创建"""
        config = {
            "log_level": "DEBUG",
            "structured_logging": False
        }
        hook = LoggingHook(config)
        
        assert hook.hook_type == HookType.LOGGING
        assert hook.log_level == "DEBUG"
        assert hook.structured_logging is False
    
    @patch('src.infrastructure.graph.hooks.builtin.logger')
    def test_before_execute_logging(self, mock_logger):
        """测试执行前日志"""
        config = {"log_level": "INFO"}
        hook = LoggingHook(config)
        
        state = Mock(spec=AgentState)
        state.messages = []
        state.iteration_count = 0
        state.errors = []
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is True
        mock_logger.info.assert_called()
    
    @patch('src.infrastructure.graph.hooks.builtin.logger')
    def test_after_execute_logging(self, mock_logger):
        """测试执行后日志"""
        config = {"log_level": "INFO"}
        hook = LoggingHook(config)
        
        state = Mock(spec=AgentState)
        execution_result = NodeExecutionResult(state=state, next_node="next_node")
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            execution_result=execution_result,
            metadata={"execution_time": 2.5}
        )
        
        result = hook.after_execute(context)
        assert result.should_continue is True
        mock_logger.info.assert_called()
    
    @patch('src.infrastructure.graph.hooks.builtin.logger')
    def test_on_error_logging(self, mock_logger):
        """测试错误日志"""
        config = {"log_level": "INFO"}
        hook = LoggingHook(config)
        
        state = Mock(spec=AgentState)
        error = Exception("test error")
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.ON_ERROR,
            error=error
        )
        
        result = hook.on_error(context)
        assert result.should_continue is True
        mock_logger.info.assert_called()


class TestMetricsCollectionHook:
    """指标收集Hook测试"""
    
    def test_creation(self):
        """测试创建"""
        config = {
            "enable_performance_metrics": True,
            "enable_business_metrics": False
        }
        hook = MetricsCollectionHook(config)
        
        assert hook.hook_type == HookType.METRICS_COLLECTION
        assert hook.enable_performance_metrics is True
        assert hook.enable_business_metrics is False
    
    def test_before_execute_record_start_time(self):
        """测试执行前记录开始时间"""
        config = {"enable_performance_metrics": True}
        hook = MetricsCollectionHook(config)
        
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        result = hook.before_execute(context)
        assert result.should_continue is True
        assert "metrics_start_time" in context.metadata
    
    @patch('time.time')
    def test_after_execute_collect_metrics(self, mock_time):
        """测试执行后收集指标"""
        mock_time.side_effect = [1000.0, 1003.0]
        
        config = {
            "enable_performance_metrics": True,
            "enable_business_metrics": True
        }
        hook = MetricsCollectionHook(config)
        
        state = Mock(spec=AgentState)
        state.messages = [Mock(), Mock()]
        state.iteration_count = 5
        state.tool_calls = [Mock()]
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            metadata={"metrics_start_time": 1000.0}
        )
        
        result = hook.after_execute(context)
        assert result.should_continue is True
        
        # 检查指标是否被收集
        metrics = hook.get_metrics()
        assert "performance.test_node.execution_time" in metrics
        assert "business.test_node.message_count" in metrics
        assert "business.test_node.iteration_count" in metrics
    
    def test_get_and_reset_metrics(self):
        """测试获取和重置指标"""
        config = {"enable_performance_metrics": True}
        hook = MetricsCollectionHook(config)
        
        # 添加一些指标
        hook._metrics["test_metric"] = 100
        
        # 获取指标
        metrics = hook.get_metrics()
        assert metrics["test_metric"] == 100
        
        # 重置指标
        hook.reset_metrics()
        metrics = hook.get_metrics()
        assert len(metrics) == 0


class TestCreateBuiltinHook:
    """create_builtin_hook函数测试"""
    
    def test_create_dead_loop_detection_hook(self):
        """测试创建死循环检测Hook"""
        config = {"type": "dead_loop_detection", "max_iterations": 10}
        hook = create_builtin_hook(config)
        
        assert hook is not None
        assert isinstance(hook, DeadLoopDetectionHook)
        assert hook.max_iterations == 10
    
    def test_create_performance_monitoring_hook(self):
        """测试创建性能监控Hook"""
        config = {"type": "performance_monitoring", "timeout_threshold": 30.0}
        hook = create_builtin_hook(config)
        
        assert hook is not None
        assert isinstance(hook, PerformanceMonitoringHook)
        assert hook.timeout_threshold == 30.0
    
    def test_create_error_recovery_hook(self):
        """测试创建错误恢复Hook"""
        config = {"type": "error_recovery", "max_retries": 5}
        hook = create_builtin_hook(config)
        
        assert hook is not None
        assert isinstance(hook, ErrorRecoveryHook)
        assert hook.max_retries == 5
    
    def test_create_logging_hook(self):
        """测试创建日志Hook"""
        config = {"type": "logging", "log_level": "DEBUG"}
        hook = create_builtin_hook(config)
        
        assert hook is not None
        assert isinstance(hook, LoggingHook)
        assert hook.log_level == "DEBUG"
    
    def test_create_metrics_collection_hook(self):
        """测试创建指标收集Hook"""
        config = {"type": "metrics_collection", "enable_system_metrics": True}
        hook = create_builtin_hook(config)
        
        assert hook is not None
        assert isinstance(hook, MetricsCollectionHook)
        assert hook.enable_system_metrics is True
    
    def test_create_unknown_hook(self):
        """测试创建未知Hook"""
        config = {"type": "unknown_hook"}
        hook = create_builtin_hook(config)
        
        assert hook is None
    
    def test_create_invalid_config(self):
        """测试创建无效配置"""
        config = {"invalid": "config"}
        hook = create_builtin_hook(config)
        
        assert hook is None


if __name__ == "__main__":
    pytest.main([__file__])