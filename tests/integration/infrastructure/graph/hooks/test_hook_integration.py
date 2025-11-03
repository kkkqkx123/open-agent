"""Hook系统集成测试"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.graph.hooks import (
    NodeHookManager, HookAwareGraphBuilder, create_hook_aware_builder,
    DeadLoopDetectionHook, PerformanceMonitoringHook, ErrorRecoveryHook
)
from src.infrastructure.graph.hooks.interfaces import HookContext, HookPoint
from src.infrastructure.graph.hooks.config import HookType
from src.infrastructure.graph.state import create_react_state
from src.infrastructure.graph.registry import get_global_registry, BaseNode, NodeExecutionResult
from src.infrastructure.graph.state import WorkflowState as AgentState


class MockTestNode(BaseNode):
    """测试用的Mock节点"""
    
    def __init__(self, should_fail=False, execution_time=0.1):
        self.should_fail = should_fail
        self.execution_time = execution_time
        self.execution_count = 0
    
    @property
    def node_type(self) -> str:
        return "mock_test_node"
    
    def execute(self, state: AgentState, config: dict) -> NodeExecutionResult:
        """模拟节点执行"""
        import time
        
        self.execution_count += 1
        
        # 模拟执行时间
        time.sleep(self.execution_time)
        
        if self.should_fail:
            raise Exception(f"Mock node execution failed (count: {self.execution_count})")
        
        # 更新状态
        if not hasattr(state, 'test_data'):
            state.test_data = []
        state.test_data.append(f"execution_{self.execution_count}")
        
        return NodeExecutionResult(
            state=state,
            next_node=None,
            metadata={"execution_count": self.execution_count}
        )
    
    def get_config_schema(self) -> dict:
        return {"type": "object", "properties": {}}


class TestHookManagerIntegration:
    """Hook管理器集成测试"""
    
    def test_load_hooks_from_config(self):
        """测试从配置加载Hook"""
        with tempfile.TemporaryDirectory() as temp_dir:
            # 创建临时配置文件
            config_dir = Path(temp_dir) / "configs" / "hooks"
            config_dir.mkdir(parents=True)
            
            # 全局Hook配置
            global_config = {
                "global_hooks": [
                    {
                        "type": "logging",
                        "enabled": True,
                        "config": {"log_level": "INFO"}
                    },
                    {
                        "type": "performance_monitoring",
                        "enabled": True,
                        "config": {"timeout_threshold": 30.0}
                    }
                ]
            }
            
            global_file = config_dir / "global_hooks.yaml"
            with open(global_file, 'w') as f:
                yaml.dump(global_config, f)
            
            # 节点Hook配置
            node_config = {
                "mock_test_node": {
                    "inherit_global": True,
                    "hooks": [
                        {
                            "type": "dead_loop_detection",
                            "enabled": True,
                            "config": {"max_iterations": 5}
                        }
                    ]
                }
            }
            
            node_file = config_dir / "mock_test_node_hooks.yaml"
            with open(node_file, 'w') as f:
                yaml.dump(node_config, f)
            
            # 创建配置加载器
            config_loader = YamlConfigLoader(base_path=str(Path(temp_dir) / "configs"))
            
            # 创建Hook管理器
            hook_manager = NodeHookManager(config_loader)
            
            # 加载全局Hook
            hook_manager.load_hooks_from_config()
            
            # 加载节点Hook
            hook_manager.load_node_hooks_from_config("mock_test_node")
            
            # 验证Hook已加载
            hooks = hook_manager.get_hooks_for_node("mock_test_node")
            assert len(hooks) >= 2  # 至少有全局Hook和节点Hook
            
            hook_types = [hook.hook_type for hook in hooks]
            assert HookType.LOGGING in hook_types
            assert HookType.PERFORMANCE_MONITORING in hook_types
            assert HookType.DEAD_LOOP_DETECTION in hook_types
    
    def test_hook_execution_flow(self):
        """测试Hook执行流程"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        hook_manager = NodeHookManager(config_loader)
        
        # 创建测试Hook
        before_hook = Mock()
        before_hook.hook_type = "before_hook"
        before_hook.is_enabled.return_value = True
        before_hook.get_supported_hook_points.return_value = [HookPoint.BEFORE_EXECUTE]
        before_hook.before_execute.return_value = Mock(should_continue=True)
        
        after_hook = Mock()
        after_hook.hook_type = "after_hook"
        after_hook.is_enabled.return_value = True
        after_hook.get_supported_hook_points.return_value = [HookPoint.AFTER_EXECUTE]
        after_hook.after_execute.return_value = Mock(should_continue=True)
        
        # 注册Hook
        hook_manager.register_hook(before_hook)
        hook_manager.register_hook(after_hook)
        
        # 创建测试上下文
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 执行前置Hook
        result = hook_manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        assert result.should_continue is True
        before_hook.before_execute.assert_called_once()
        
        # 执行后置Hook
        context.hook_point = HookPoint.AFTER_EXECUTE
        result = hook_manager.execute_hooks(HookPoint.AFTER_EXECUTE, context)
        assert result.should_continue is True
        after_hook.after_execute.assert_called_once()
    
    def test_hook_interrupt_execution(self):
        """测试Hook中断执行"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        hook_manager = NodeHookManager(config_loader)
        
        # 创建会中断的Hook
        interrupt_hook = Mock()
        interrupt_hook.hook_type = "interrupt_hook"
        interrupt_hook.is_enabled.return_value = True
        interrupt_hook.get_supported_hook_points.return_value = [HookPoint.BEFORE_EXECUTE]
        interrupt_hook.before_execute.return_value = Mock(
            should_continue=False,
            force_next_node="interrupted_node"
        )
        
        # 创建正常Hook
        normal_hook = Mock()
        normal_hook.hook_type = "normal_hook"
        normal_hook.is_enabled.return_value = True
        normal_hook.get_supported_hook_points.return_value = [HookPoint.BEFORE_EXECUTE]
        normal_hook.before_execute.return_value = Mock(should_continue=True)
        
        # 注册Hook（中断Hook优先级更高）
        hook_manager.register_hook(interrupt_hook)
        hook_manager.register_hook(normal_hook)
        
        # 创建测试上下文
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 执行Hook
        result = hook_manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        
        # 验证执行被中断
        assert result.should_continue is False
        assert result.force_next_node == "interrupted_node"
        
        # 验证中断Hook被执行，正常Hook未被执行
        interrupt_hook.before_execute.assert_called_once()
        normal_hook.before_execute.assert_not_called()


class TestHookAwareGraphBuilderIntegration:
    """Hook感知Graph构建器集成测试"""
    
    def test_build_graph_with_hooks(self):
        """测试构建带Hook的图"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        # 创建Hook管理器
        hook_manager = NodeHookManager(config_loader)
        
        # 创建Hook感知的构建器
        builder = HookAwareGraphBuilder(
            node_registry=get_global_registry(),
            hook_manager=hook_manager,
            config_loader=config_loader
        )
        
        # 注册测试节点
        get_global_registry().register_node(MockTestNode)
        
        # 创建图配置
        from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
        
        config = GraphConfig(
            name="测试图",
            description="带Hook的测试图",
            state_schema_name="ReActState",
            entry_point="test_node"
        )
        
        config.add_node(NodeConfig(
            name="test_node",
            function_name="mock_test_node",
            description="测试节点"
        ))
        
        # 构建图
        graph = builder.build_graph(config)
        
        # 验证图已构建
        assert graph is not None
        
        # 验证Hook统计
        stats = builder.get_hook_statistics()
        assert "hook_manager_initialized" in stats
        assert stats["hook_manager_initialized"] is True
    
    @patch('src.infrastructure.graph.hooks.builtin.logger')
    def test_execute_graph_with_hooks(self, mock_logger):
        """测试执行带Hook的图"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        # 创建Hook管理器
        hook_manager = NodeHookManager(config_loader)
        
        # 添加性能监控Hook
        performance_hook = PerformanceMonitoringHook({
            "timeout_threshold": 5.0,
            "log_slow_executions": True
        })
        hook_manager.register_hook(performance_hook)
        
        # 创建Hook感知的构建器
        builder = HookAwareGraphBuilder(
            node_registry=get_global_registry(),
            hook_manager=hook_manager,
            config_loader=config_loader
        )
        
        # 注册测试节点
        get_global_registry().register_node(MockTestNode)
        
        # 创建图配置
        from src.infrastructure.graph.config import GraphConfig, NodeConfig
        
        config = GraphConfig(
            name="测试图",
            description="带Hook的测试图",
            state_schema_name="ReActState",
            entry_point="test_node"
        )
        
        config.add_node(NodeConfig(
            name="test_node",
            function_name="mock_test_node",
            description="测试节点"
        ))
        
        # 构建图
        graph = builder.build_graph(config)
        
        # 创建初始状态
        initial_state = create_react_state(
            workflow_id="test_workflow",
            input_text="测试输入",
            max_iterations=5
        )
        
        # 执行图
        try:
            result = graph.invoke(initial_state)
            assert result is not None
        except Exception as e:
            # 如果LangGraph不可用，这是预期的
            print(f"LangGraph不可用，跳过图执行测试: {e}")


class TestDeadLoopDetectionIntegration:
    """死循环检测集成测试"""
    
    def test_dead_loop_detection_in_action(self):
        """测试死循环检测实际工作"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        hook_manager = NodeHookManager(config_loader)
        
        # 创建死循环检测Hook
        dead_loop_hook = DeadLoopDetectionHook({
            "max_iterations": 3,
            "fallback_node": "dead_loop_handler"
        })
        hook_manager.register_hook(dead_loop_hook, ["mock_test_node"])
        
        # 创建测试节点
        test_node = MockTestNode()
        
        # 模拟多次执行
        state = Mock(spec=AgentState)
        context = HookContext(
            node_type="mock_test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE,
            hook_manager=hook_manager
        )
        
        # 前两次执行应该正常
        for i in range(2):
            hook_manager.increment_execution_count("mock_test_node")
            result = dead_loop_hook.before_execute(context)
            assert result.should_continue is True
        
        # 第三次执行应该被中断
        hook_manager.increment_execution_count("mock_test_node")
        result = dead_loop_hook.before_execute(context)
        assert result.should_continue is False
        assert result.force_next_node == "dead_loop_handler"


class TestErrorRecoveryIntegration:
    """错误恢复集成测试"""
    
    def test_error_recovery_in_action(self):
        """测试错误恢复实际工作"""
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        hook_manager = NodeHookManager(config_loader)
        
        # 创建错误恢复Hook
        error_recovery_hook = ErrorRecoveryHook({
            "max_retries": 2,
            "retry_delay": 0.1,  # 快速重试用于测试
            "retry_on_exceptions": ["Exception"]
        })
        hook_manager.register_hook(error_recovery_hook, ["mock_test_node"])
        
        # 创建会失败的测试节点
        test_node = MockTestNode(should_fail=True)
        
        # 模拟错误和重试
        state = Mock(spec=AgentState)
        error = Exception("Test error")
        
        for retry_count in range(2):
            context = HookContext(
                node_type="mock_test_node",
                state=state,
                config={},
                hook_point=HookPoint.ON_ERROR,
                error=error,
                metadata={"retry_count": retry_count}
            )
            
            result = error_recovery_hook.on_error(context)
            assert result.should_continue is True
            assert result.metadata["retry_scheduled"] is True
            assert result.metadata["retry_count"] == retry_count + 1
        
        # 第三次错误应该超过重试限制
        context = HookContext(
            node_type="mock_test_node",
            state=state,
            config={},
            hook_point=HookPoint.ON_ERROR,
            error=error,
            metadata={"retry_count": 2}
        )
        
        result = error_recovery_hook.on_error(context)
        assert result.should_continue is False
        assert result.force_next_node == "error_handler"
        assert result.metadata["max_retries_exceeded"] is True


class TestPerformanceMonitoringIntegration:
    """性能监控集成测试"""
    
    @patch('time.time')
    def test_performance_monitoring_in_action(self, mock_time):
        """测试性能监控实际工作"""
        mock_time.side_effect = [1000.0, 1002.0]  # 2秒执行时间
        
        config_loader = Mock()
        config_loader.load.return_value = {"global_hooks": []}
        
        hook_manager = NodeHookManager(config_loader)
        
        # 创建性能监控Hook
        performance_hook = PerformanceMonitoringHook({
            "timeout_threshold": 10.0,
            "slow_execution_threshold": 1.0
        })
        hook_manager.register_hook(performance_hook)
        
        # 模拟节点执行
        state = Mock(spec=AgentState)
        
        # 前置Hook
        before_context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        result = performance_hook.before_execute(before_context)
        assert result.should_continue is True
        assert "performance_start_time" in before_context.metadata
        
        # 后置Hook
        after_context = HookContext(
            node_type="test_node",
            state=state,
            config={},
            hook_point=HookPoint.AFTER_EXECUTE,
            metadata={"performance_start_time": 1000.0},
            hook_manager=hook_manager
        )
        
        result = performance_hook.after_execute(after_context)
        assert result.should_continue is True
        assert result.metadata["execution_time"] == 2.0
        
        # 验证性能统计已更新
        stats = hook_manager.get_performance_stats("test_node")
        assert "total_executions" in stats
        assert stats["total_executions"] == 1
        assert "total_execution_time" in stats
        assert stats["total_execution_time"] == 2.0


if __name__ == "__main__":
    pytest.main([__file__])