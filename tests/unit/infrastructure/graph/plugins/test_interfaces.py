"""插件系统接口测试"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, Any, Optional, List

from src.infrastructure.graph.plugins.interfaces import (
    PluginType, PluginStatus, HookPoint,
    PluginMetadata, PluginContext, HookContext, HookExecutionResult,
    IPlugin, IHookPlugin, IStartPlugin, IEndPlugin,
    PluginError, PluginInitializationError, PluginExecutionError, PluginConfigurationError
)


class TestPluginType:
    """测试PluginType枚举"""
    
    def test_plugin_type_values(self):
        """测试插件类型枚举值"""
        assert PluginType.START.value == "start"
        assert PluginType.END.value == "end"
        assert PluginType.GENERIC.value == "generic"
        assert PluginType.HOOK.value == "hook"


class TestPluginStatus:
    """测试PluginStatus枚举"""
    
    def test_plugin_status_values(self):
        """测试插件状态枚举值"""
        assert PluginStatus.ENABLED.value == "enabled"
        assert PluginStatus.DISABLED.value == "disabled"
        assert PluginStatus.ERROR.value == "error"


class TestHookPoint:
    """测试HookPoint枚举"""
    
    def test_hook_point_values(self):
        """测试Hook点枚举值"""
        assert HookPoint.BEFORE_EXECUTE.value == "before_execute"
        assert HookPoint.AFTER_EXECUTE.value == "after_execute"
        assert HookPoint.ON_ERROR.value == "on_error"


class TestPluginMetadata:
    """测试PluginMetadata类"""
    
    def test_plugin_metadata_creation(self):
        """测试插件元数据创建"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="测试插件",
            author="测试作者",
            plugin_type=PluginType.GENERIC,
            dependencies=["dep1", "dep2"],
            config_schema={"type": "object"},
            supported_hook_points=[HookPoint.BEFORE_EXECUTE]
        )
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.description == "测试插件"
        assert metadata.author == "测试作者"
        assert metadata.plugin_type == PluginType.GENERIC
        assert metadata.dependencies == ["dep1", "dep2"]
        assert metadata.config_schema == {"type": "object"}
        assert metadata.supported_hook_points == [HookPoint.BEFORE_EXECUTE]
    
    def test_plugin_metadata_defaults(self):
        """测试插件元数据默认值"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="测试插件",
            author="测试作者",
            plugin_type=PluginType.GENERIC
        )
        
        assert metadata.dependencies == []
        assert metadata.config_schema == {}
        assert metadata.supported_hook_points == []
    
    def test_plugin_metadata_post_init_with_none(self):
        """测试插件元数据初始化后处理（None值）"""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            description="测试插件",
            author="测试作者",
            plugin_type=PluginType.GENERIC,
            dependencies=None,
            config_schema=None,
            supported_hook_points=None
        )
        
        assert metadata.dependencies == []
        assert metadata.config_schema == {}
        assert metadata.supported_hook_points == []


class TestPluginContext:
    """测试PluginContext类"""
    
    def test_plugin_context_creation(self):
        """测试插件上下文创建"""
        context = PluginContext(
            workflow_id="test_workflow",
            thread_id="test_thread",
            session_id="test_session",
            execution_start_time=1234567890.0,
            metadata={"key": "value"}
        )
        
        assert context.workflow_id == "test_workflow"
        assert context.thread_id == "test_thread"
        assert context.session_id == "test_session"
        assert context.execution_start_time == 1234567890.0
        assert context.metadata == {"key": "value"}
    
    def test_plugin_context_defaults(self):
        """测试插件上下文默认值"""
        context = PluginContext(workflow_id="test_workflow")
        
        assert context.workflow_id == "test_workflow"
        assert context.thread_id is None
        assert context.session_id is None
        assert context.execution_start_time is None
        assert context.metadata == {}
    
    def test_plugin_context_post_init_with_none(self):
        """测试插件上下文初始化后处理（None值）"""
        context = PluginContext(
            workflow_id="test_workflow",
            metadata=None
        )
        
        assert context.metadata == {}


class TestHookContext:
    """测试HookContext类"""
    
    def test_hook_context_creation(self):
        """测试Hook上下文创建"""
        mock_state = Mock()
        mock_result = Mock()
        error = Exception("测试错误")
        
        context = HookContext(
            node_type="test_node",
            state=mock_state,
            config={"key": "value"},
            hook_point=HookPoint.BEFORE_EXECUTE,
            error=error,
            execution_result=mock_result,
            metadata={"meta": "data"}
        )
        
        assert context.node_type == "test_node"
        assert context.state is mock_state
        assert context.config == {"key": "value"}
        assert context.hook_point == HookPoint.BEFORE_EXECUTE
        assert context.error is error
        assert context.execution_result is mock_result
        assert context.metadata == {"meta": "data"}
    
    def test_hook_context_defaults(self):
        """测试Hook上下文默认值"""
        mock_state = Mock()
        
        context = HookContext(
            node_type="test_node",
            state=mock_state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        assert context.error is None
        assert context.execution_result is None
        assert context.metadata is None


class TestHookExecutionResult:
    """测试HookExecutionResult类"""
    
    def test_hook_execution_result_creation(self):
        """测试Hook执行结果创建"""
        mock_state = Mock()
        mock_result = Mock()
        
        result = HookExecutionResult(
            should_continue=False,
            modified_state=mock_state,
            modified_result=mock_result,
            force_next_node="next_node",
            metadata={"key": "value"}
        )
        
        assert result.should_continue is False
        assert result.modified_state is mock_state
        assert result.modified_result is mock_result
        assert result.force_next_node == "next_node"
        assert result.metadata == {"key": "value"}
    
    def test_hook_execution_result_defaults(self):
        """测试Hook执行结果默认值"""
        result = HookExecutionResult()
        
        assert result.should_continue is True
        assert result.modified_state is None
        assert result.modified_result is None
        assert result.force_next_node is None
        assert result.metadata == {}
    
    def test_hook_execution_result_bool_conversion(self):
        """测试Hook执行结果布尔值转换"""
        result_true = HookExecutionResult(should_continue=True)
        result_false = HookExecutionResult(should_continue=False)
        
        assert bool(result_true) is True
        assert bool(result_false) is False


class TestPluginExceptions:
    """测试插件异常类"""
    
    def test_plugin_error(self):
        """测试插件异常基类"""
        error = PluginError("测试错误")
        assert str(error) == "测试错误"
        assert isinstance(error, Exception)
    
    def test_plugin_initialization_error(self):
        """测试插件初始化异常"""
        error = PluginInitializationError("初始化错误")
        assert str(error) == "初始化错误"
        assert isinstance(error, PluginError)
    
    def test_plugin_execution_error(self):
        """测试插件执行异常"""
        error = PluginExecutionError("执行错误")
        assert str(error) == "执行错误"
        assert isinstance(error, PluginError)
    
    def test_plugin_configuration_error(self):
        """测试插件配置异常"""
        error = PluginConfigurationError("配置错误")
        assert str(error) == "配置错误"
        assert isinstance(error, PluginError)


class MockPlugin(IPlugin):
    """用于测试的模拟插件"""
    
    def __init__(self, name="test_plugin", plugin_type=PluginType.GENERIC):
        self._metadata = PluginMetadata(
            name=name,
            version="1.0.0",
            description="测试插件",
            author="测试作者",
            plugin_type=plugin_type
        )
        self._initialized = False
        self._config = {}
    
    @property
    def metadata(self) -> PluginMetadata:
        return self._metadata
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        self._config = config
        self._initialized = True
        return True
    
    def execute(self, state: Dict[str, Any], context: PluginContext) -> Dict[str, Any]:
        if not self._initialized:
            raise PluginExecutionError("插件未初始化")
        return {"executed": True, "plugin": self._metadata.name}
    
    def cleanup(self) -> bool:
        self._initialized = False
        return True


class MockHookPlugin(MockPlugin, IHookPlugin):
    """用于测试的模拟Hook插件"""
    
    def __init__(self, name="test_hook_plugin"):
        super().__init__(name, PluginType.HOOK)
        self._metadata.supported_hook_points = [HookPoint.BEFORE_EXECUTE, HookPoint.AFTER_EXECUTE]
        self.execution_service = None
    
    def before_execute(self, context: HookContext) -> HookExecutionResult:
        return HookExecutionResult(should_continue=True)
    
    def after_execute(self, context: HookContext) -> HookExecutionResult:
        return HookExecutionResult(should_continue=True)
    
    def on_error(self, context: HookContext) -> HookExecutionResult:
        return HookExecutionResult(should_continue=True)
    
    def set_execution_service(self, service: Any) -> None:
        self.execution_service = service


class MockStartPlugin(MockPlugin, IStartPlugin):
    """用于测试的模拟START插件"""
    
    def __init__(self, name="test_start_plugin"):
        super().__init__(name, PluginType.START)


class MockEndPlugin(MockPlugin, IEndPlugin):
    """用于测试的模拟END插件"""
    
    def __init__(self, name="test_end_plugin"):
        super().__init__(name, PluginType.END)


class TestIPlugin:
    """测试IPlugin接口"""
    
    def test_plugin_interface_methods(self):
        """测试插件接口方法"""
        plugin = MockPlugin()
        
        # 测试属性
        assert plugin.metadata.name == "test_plugin"
        assert plugin.metadata.plugin_type == PluginType.GENERIC
        
        # 测试初始化
        config = {"key": "value"}
        assert plugin.initialize(config) is True
        
        # 测试执行
        state = {"test": "state"}
        context = PluginContext(workflow_id="test")
        result = plugin.execute(state, context)
        assert result["executed"] is True
        assert result["plugin"] == "test_plugin"
        
        # 测试清理
        assert plugin.cleanup() is True
    
    def test_plugin_validate_config(self):
        """测试插件配置验证"""
        plugin = MockPlugin()
        
        # 测试非字典配置
        errors = plugin.validate_config("invalid")  # type: ignore
        assert "配置必须是字典类型" in errors
        
        # 测试空配置
        errors = plugin.validate_config({})
        assert errors == []
        
        # 测试带模式的配置验证
        plugin._metadata.config_schema = {
            "required": ["required_field"],
            "properties": {
                "required_field": {"type": "string"},
                "optional_field": {"type": "integer"}
            }
        }
        
        # 测试缺少必需字段
        errors = plugin.validate_config({})
        assert "缺少必需字段: required_field" in errors
        
        # 测试字段类型错误
        errors = plugin.validate_config({
            "required_field": 123,  # 应该是字符串
            "optional_field": "not_integer"  # 应该是整数
        })
        assert "字段 required_field 应为字符串类型" in errors
        assert "字段 optional_field 应为整数类型" in errors
        
        # 测试正确配置
        errors = plugin.validate_config({
            "required_field": "test",
            "optional_field": 42
        })
        assert errors == []
    
    def test_plugin_get_status(self):
        """测试获取插件状态"""
        plugin = MockPlugin()
        assert plugin.get_status() == PluginStatus.ENABLED


class TestIHookPlugin:
    """测试IHookPlugin接口"""
    
    def test_hook_plugin_metadata(self):
        """测试Hook插件元数据"""
        plugin = MockHookPlugin()
        assert plugin.metadata.plugin_type == PluginType.HOOK
        assert HookPoint.BEFORE_EXECUTE in (plugin.metadata.supported_hook_points or [])
        assert HookPoint.AFTER_EXECUTE in (plugin.metadata.supported_hook_points or [])
    
    def test_hook_plugin_methods(self):
        """测试Hook插件方法"""
        plugin = MockHookPlugin()
        mock_state = Mock()
        context = HookContext(
            node_type="test_node",
            state=mock_state,
            config={},
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 测试Hook方法
        result = plugin.before_execute(context)
        assert isinstance(result, HookExecutionResult)
        assert result.should_continue is True
        
        result = plugin.after_execute(context)
        assert isinstance(result, HookExecutionResult)
        assert result.should_continue is True
        
        result = plugin.on_error(context)
        assert isinstance(result, HookExecutionResult)
        assert result.should_continue is True
    
    def test_hook_plugin_set_execution_service(self):
        """测试设置执行服务"""
        plugin = MockHookPlugin()
        mock_service = Mock()
        
        plugin.set_execution_service(mock_service)
        assert plugin.execution_service is mock_service
    
    def test_hook_plugin_get_supported_hook_points(self):
        """测试获取支持的Hook点"""
        plugin = MockHookPlugin()
        supported_points = plugin.get_supported_hook_points()
        assert HookPoint.BEFORE_EXECUTE in supported_points
        assert HookPoint.AFTER_EXECUTE in supported_points


class TestIStartPlugin:
    """测试IStartPlugin接口"""
    
    def test_start_plugin_metadata(self):
        """测试START插件元数据"""
        plugin = MockStartPlugin()
        assert plugin.metadata.plugin_type == PluginType.START


class TestIEndPlugin:
    """测试IEndPlugin接口"""
    
    def test_end_plugin_metadata(self):
        """测试END插件元数据"""
        plugin = MockEndPlugin()
        assert plugin.metadata.plugin_type == PluginType.END