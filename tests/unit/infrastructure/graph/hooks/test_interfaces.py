"""Hook接口单元测试"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional

from src.infrastructure.graph.hooks.interfaces import (
    INodeHook, IHookManager, IHookConfigLoader,
    HookContext, HookPoint, HookExecutionResult
)
from src.infrastructure.graph.hooks.config import HookType
from src.domain.agent.state import AgentState
from src.infrastructure.graph.registry import NodeExecutionResult


class MockHook(INodeHook):
    """测试用的Mock Hook"""
    
    def __init__(self, hook_config):
        super().__init__(hook_config)
        self.before_execute_called = False
        self.after_execute_called = False
        self.on_error_called = False
    
    @property
    def hook_type(self) -> str:
        return "mock_hook"
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        self.before_execute_called = True
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        self.after_execute_called = True
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        self.on_error_called = True
        return HookExecutionResult(should_continue=True)


class MockHookManager(IHookManager):
    """测试用的Mock Hook管理器"""
    
    def __init__(self):
        self.hooks = {}
        self.registered_hooks = []
    
    def register_hook(self, hook: INodeHook, node_types=None):
        self.registered_hooks.append((hook, node_types))
        for node_type in (node_types or ["global"]):
            if node_type not in self.hooks:
                self.hooks[node_type] = []
            self.hooks[node_type].append(hook)
    
    def get_hooks_for_node(self, node_type: str):
        hooks = self.hooks.get("global", []).copy()
        hooks.extend(self.hooks.get(node_type, []))
        return hooks
    
    def execute_hooks(self, hook_point: HookPoint, context: HookContext) -> HookExecutionResult:
        hooks = self.get_hooks_for_node(context.node_type)
        for hook in hooks:
            if hook_point == HookPoint.BEFORE_EXECUTE:
                result = hook.before_execute(context)
            elif hook_point == HookPoint.AFTER_EXECUTE:
                result = hook.after_execute(context)
            elif hook_point == HookPoint.ON_ERROR:
                result = hook.on_error(context)
            else:
                continue
            
            if not result.should_continue:
                return result
        
        return HookExecutionResult(should_continue=True)
    
    def load_hooks_from_config(self, config_path: Optional[str] = None):
        pass

    def load_node_hooks_from_config(self, node_type: str):
        pass

    def get_global_hooks_count(self) -> int:
        return len(self.hooks.get("global", []))

    def get_node_hooks_count(self, node_type: str) -> int:
        return len(self.hooks.get(node_type, []))

    def get_all_node_hooks_counts(self) -> Dict[str, int]:
        return {node_type: len(hooks) for node_type, hooks in self.hooks.items()}

    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        return {}

    def clear_hooks(self):
        self.hooks.clear()
        self.registered_hooks.clear()


class TestHookExecutionResult:
    """HookExecutionResult测试"""
    
    def test_default_creation(self):
        """测试默认创建"""
        result = HookExecutionResult()
        assert result.should_continue is True
        assert result.modified_state is None
        assert result.modified_result is None
        assert result.force_next_node is None
        assert result.metadata == {}
    
    def test_custom_creation(self):
        """测试自定义创建"""
        state = Mock(spec=AgentState)
        result = NodeExecutionResult(state=state, next_node="test_node")
        
        hook_result = HookExecutionResult(
            should_continue=False,
            modified_state=state,
            modified_result=result,
            force_next_node="forced_node",
            metadata={"test": "value"}
        )
        
        assert hook_result.should_continue is False
        assert hook_result.modified_state is state
        assert hook_result.modified_result is result
        assert hook_result.force_next_node == "forced_node"
        assert hook_result.metadata["test"] == "value"
    
    def test_boolean_conversion(self):
        """测试布尔值转换"""
        result_true = HookExecutionResult(should_continue=True)
        result_false = HookExecutionResult(should_continue=False)
        
        assert bool(result_true) is True
        assert bool(result_false) is False


class TestHookContext:
    """HookContext测试"""
    
    def test_creation(self):
        """测试创建"""
        state = Mock(spec=AgentState)
        config = {"test": "config"}
        result = NodeExecutionResult(state=state, next_node="test_node")
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE,
            execution_result=result,
            
        )
        
        assert context.node_type == "test_node"
        assert context.state is state
        assert context.config == config
        assert context.hook_point == HookPoint.BEFORE_EXECUTE
        assert context.execution_result is result
        assert context.error is None
        assert context.metadata is None
    
    def test_creation_with_error(self):
        """测试带错误的创建"""
        state = Mock(spec=AgentState)
        config = {"test": "config"}
        error = Exception("test error")
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.ON_ERROR,
            error=error,
            
        )
        
        assert context.error is error


class TestMockHook:
    """Mock Hook测试"""
    
    def test_hook_creation(self):
        """测试Hook创建"""
        hook = MockHook({"enabled": True})
        assert hook.hook_type == "mock_hook"
        assert hook.enabled is True
        assert hook.is_enabled() is True
    
    def test_hook_disabled(self):
        """测试Hook禁用"""
        hook = MockHook({"enabled": False})
        assert hook.enabled is False
        assert hook.is_enabled() is False
    
    def test_hook_execution(self):
        """测试Hook执行"""
        hook = MockHook({"enabled": True})
        state = Mock(spec=AgentState)
        config = {"test": "config"}
        
        context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE,
            
        )
        
        # 测试before_execute
        result = hook.before_execute(context)
        assert result.should_continue is True
        assert hook.before_execute_called is True
        
        # 测试after_execute
        result = hook.after_execute(context)
        assert result.should_continue is True
        assert hook.after_execute_called is True
        
        # 测试on_error
        error_context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.ON_ERROR,
            error=Exception("test"),
            
        )
        result = hook.on_error(error_context)
        assert result.should_continue is True
        assert hook.on_error_called is True


class TestMockHookManager:
    """Mock Hook管理器测试"""
    
    def test_hook_registration(self):
        """测试Hook注册"""
        manager = MockHookManager()
        hook = MockHook({"enabled": True})
        
        # 注册全局Hook
        manager.register_hook(hook)
        assert len(manager.registered_hooks) == 1
        assert manager.registered_hooks[0] == (hook, None)
        
        # 注册节点特定Hook
        hook2 = MockHook({"enabled": True})
        manager.register_hook(hook2, ["test_node"])
        assert len(manager.registered_hooks) == 2
        assert manager.registered_hooks[1] == (hook2, ["test_node"])
    
    def test_get_hooks_for_node(self):
        """测试获取节点Hook"""
        manager = MockHookManager()
        global_hook = MockHook({"enabled": True})
        node_hook = MockHook({"enabled": True})
        
        manager.register_hook(global_hook)
        manager.register_hook(node_hook, ["test_node"])
        
        # 获取全局Hook
        hooks = manager.get_hooks_for_node("other_node")
        assert len(hooks) == 1
        assert hooks[0] is global_hook
        
        # 获取节点特定Hook（包含全局Hook）
        hooks = manager.get_hooks_for_node("test_node")
        assert len(hooks) == 2
        assert global_hook in hooks
        assert node_hook in hooks
    
    def test_execute_hooks(self):
        """测试执行Hook"""
        manager = MockHookManager()
        hook = MockHook({"enabled": True})
        
        manager.register_hook(hook)
        
        state = Mock(spec=AgentState)
        config = {"test": "config"}
        context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE,
            
        )
        
        result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        assert result.should_continue is True
        assert hook.before_execute_called is True
    
    def test_execute_hooks_interrupt(self):
        """测试Hook中断执行"""
        manager = MockHookManager()
        
        # 创建会中断的Hook
        class InterruptHook(MockHook):
            def before_execute(self, context: HookContext) -> HookExecutionResult:
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node="interrupt_node"
                )
        
        interrupt_hook = InterruptHook({"enabled": True})
        normal_hook = MockHook({"enabled": True})
        
        manager.register_hook(interrupt_hook)
        manager.register_hook(normal_hook)
        
        state = Mock(spec=AgentState)
        config = {"test": "config"}
        context = HookContext(
            node_type="test_node",
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE,
            
        )
        
        result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
        assert result.should_continue is False
        assert result.force_next_node == "interrupt_node"
        # 正常Hook不应该被执行
        assert normal_hook.before_execute_called is False
    
    def test_clear_hooks(self):
        """测试清除Hook"""
        manager = MockHookManager()
        hook = MockHook({"enabled": True})
        
        manager.register_hook(hook)
        assert len(manager.registered_hooks) == 1
        
        manager.clear_hooks()
        assert len(manager.registered_hooks) == 0
        assert len(manager.hooks) == 0


if __name__ == "__main__":
    pytest.main([__file__])