"""配置回调管理器单元测试"""

from datetime import datetime
import pytest
from unittest.mock import Mock

from src.config.config_callback_manager import (
    ConfigCallbackManager,
    ConfigChangeContext,
    ConfigCallback,
    CallbackPriority,
    register_config_callback,
    unregister_config_callback,
    trigger_config_callbacks,
    get_global_callback_manager,
)


class TestConfigChangeContext:
    """配置变更上下文测试类"""

    def test_context_creation(self):
        """测试上下文创建"""
        old_config = {"key": "old_value"}
        new_config = {"key": "new_value"}

        context = ConfigChangeContext(
            config_path="test.yaml",
            old_config=old_config,
            new_config=new_config,
            source="test",
            timestamp=datetime.now(),
        )

        assert context.config_path == "test.yaml"
        assert context.old_config == old_config
        assert context.new_config == new_config
        assert context.source == "test"
        assert context.timestamp is not None

    def test_context_to_dict(self):
        """测试上下文转换为字典"""
        old_config = {"key": "old_value"}
        new_config = {"key": "new_value"}

        context = ConfigChangeContext(
            config_path="test.yaml",
            old_config=old_config,
            new_config=new_config,
            timestamp=datetime.now(),
        )

        context_dict = context.to_dict()

        assert context_dict["config_path"] == "test.yaml"
        assert context_dict["old_config"] == old_config
        assert context_dict["new_config"] == new_config
        assert context_dict["source"] == "file_watcher"
        assert "timestamp" in context_dict


class TestConfigCallback:
    """配置回调测试类"""

    def test_callback_creation(self):
        """测试回调创建"""

        def test_callback(context):
            pass

        callback = ConfigCallback(
            id="test_callback",
            callback=test_callback,
            priority=CallbackPriority.HIGH,
            once=True,
            filter_paths=["*.yaml"],
        )

        assert callback.id == "test_callback"
        assert callback.callback == test_callback
        assert callback.priority == CallbackPriority.HIGH
        assert callback.once is True
        assert callback.filter_paths == ["*.yaml"]
        assert callback.enabled is True

    def test_should_execute_with_filter(self):
        """测试过滤器执行检查"""

        def test_callback(context):
            pass

        callback = ConfigCallback(
            id="test_callback",
            callback=test_callback,
            filter_paths=["*.yaml", "config/*.yml"],
        )

        # 匹配的路径
        assert callback.should_execute("test.yaml") is True
        assert callback.should_execute("config/test.yml") is True

        # 不匹配的路径
        assert callback.should_execute("test.json") is False
        assert callback.should_execute("other/test.yaml") is False

    def test_should_execute_disabled(self):
        """测试禁用状态执行检查"""

        def test_callback(context):
            pass

        callback = ConfigCallback(
            id="test_callback", callback=test_callback, enabled=False
        )

        # 禁用的回调不应该执行
        assert callback.should_execute("test.yaml") is False

    def test_should_execute_no_filter(self):
        """测试无过滤器执行检查"""

        def test_callback(context):
            pass

        callback = ConfigCallback(id="test_callback", callback=test_callback)

        # 无过滤器应该执行所有路径
        assert callback.should_execute("test.yaml") is True
        assert callback.should_execute("test.json") is True


class TestConfigCallbackManager:
    """配置回调管理器测试类"""

    def test_manager_creation(self):
        """测试管理器创建"""
        manager = ConfigCallbackManager()

        assert len(manager._callbacks) == 0
        assert len(manager._execution_order) == 0
        assert len(manager._execution_history) == 0

    def test_register_callback(self):
        """测试注册回调"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册回调
        manager.register_callback(
            "test_callback", test_callback, priority=CallbackPriority.HIGH
        )

        assert "test_callback" in manager._callbacks
        assert len(manager._execution_order) == 1
        assert manager._execution_order[0] == "test_callback"

    def test_register_duplicate_callback(self):
        """测试注册重复回调"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册第一个回调
        manager.register_callback("test_callback", test_callback)

        # 尝试注册重复回调
        with pytest.raises(Exception):  # 应该抛出ConfigurationError
            manager.register_callback("test_callback", test_callback)

    def test_unregister_callback(self):
        """测试注销回调"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册回调
        manager.register_callback("test_callback", test_callback)
        assert "test_callback" in manager._callbacks

        # 注销回调
        success = manager.unregister_callback("test_callback")
        assert success is True
        assert "test_callback" not in manager._callbacks
        assert len(manager._execution_order) == 0

        # 尝试注销不存在的回调
        success = manager.unregister_callback("nonexistent")
        assert success is False

    def test_enable_disable_callback(self):
        """测试启用/禁用回调"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册回调
        manager.register_callback("test_callback", test_callback)

        # 禁用回调
        success = manager.enable_callback("test_callback")
        assert success is True
        assert manager._callbacks["test_callback"].enabled is True

        success = manager.disable_callback("test_callback")
        assert success is True
        assert manager._callbacks["test_callback"].enabled is False

        # 尝试操作不存在的回调
        success = manager.enable_callback("nonexistent")
        assert success is False

    def test_trigger_callbacks(self):
        """测试触发回调"""
        manager = ConfigCallbackManager()

        # 创建模拟回调
        callback1 = Mock()
        callback2 = Mock()

        # 注册回调
        manager.register_callback(
            "callback1", callback1, priority=CallbackPriority.HIGH
        )
        manager.register_callback("callback2", callback2, priority=CallbackPriority.LOW)

        # 触发回调
        old_config = {"key": "old_value"}
        new_config = {"key": "new_value"}
        manager.trigger_callbacks("test.yaml", old_config, new_config)

        # 验证回调被调用
        callback1.assert_called_once()
        callback2.assert_called_once()

        # 验证调用参数
        context1 = callback1.call_args[0][0]
        context2 = callback2.call_args[0][0]

        assert context1.config_path == "test.yaml"
        assert context1.old_config == old_config
        assert context1.new_config == new_config

        assert context2.config_path == "test.yaml"
        assert context2.old_config == old_config
        assert context2.new_config == new_config

    def test_trigger_callbacks_with_filter(self):
        """测试带过滤器的回调触发"""
        manager = ConfigCallbackManager()

        # 创建模拟回调
        callback1 = Mock()
        callback2 = Mock()

        # 注册回调（带过滤器）
        manager.register_callback("callback1", callback1, filter_paths=["*.yaml"])
        manager.register_callback("callback2", callback2, filter_paths=["*.json"])

        # 触发回调
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})

        # 验证只有匹配的回调被调用
        callback1.assert_called_once()
        callback2.assert_not_called()

    def test_trigger_callbacks_once(self):
        """测试一次性回调"""
        manager = ConfigCallbackManager()

        # 创建模拟回调
        callback = Mock()

        # 注册一次性回调
        manager.register_callback("callback", callback, once=True)

        # 第一次触发
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})
        assert callback.call_count == 1
        assert "callback" in manager._callbacks

        # 第二次触发
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})
        assert callback.call_count == 1  # 不应该再次调用
        assert "callback" not in manager._callbacks  # 应该被移除

    def test_execution_order_by_priority(self):
        """测试按优先级排序执行"""
        manager = ConfigCallbackManager()

        # 创建模拟回调
        callback1 = Mock()
        callback2 = Mock()
        callback3 = Mock()

        # 注册不同优先级的回调
        manager.register_callback("callback1", callback1, priority=CallbackPriority.LOW)
        manager.register_callback(
            "callback2", callback2, priority=CallbackPriority.HIGHEST
        )
        manager.register_callback(
            "callback3", callback3, priority=CallbackPriority.NORMAL
        )

        # 验证执行顺序
        assert manager._execution_order == ["callback2", "callback3", "callback1"]

    def test_callback_error_handling(self):
        """测试回调错误处理"""
        manager = ConfigCallbackManager()

        # 创建会抛出异常的回调
        def error_callback(context):
            raise ValueError("Test error")

        # 创建正常回调
        def normal_callback(context):
            pass

        normal_mock = Mock(side_effect=normal_callback)

        # 注册回调
        manager.register_callback("error_callback", error_callback)
        manager.register_callback("normal_callback", normal_mock)

        # 触发回调（不应该因为错误而中断）
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})

        # 验证正常回调仍然被调用
        normal_mock.assert_called_once()

    def test_get_callback_info(self):
        """测试获取回调信息"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册回调
        manager.register_callback(
            "test_callback",
            test_callback,
            priority=CallbackPriority.HIGH,
            once=True,
            filter_paths=["*.yaml"],
        )

        # 获取回调信息
        info = manager.get_callback_info("test_callback")

        assert info is not None
        assert info["id"] == "test_callback"
        assert info["priority"] == "HIGH"
        assert info["once"] is True
        assert info["filter_paths"] == ["*.yaml"]
        assert info["enabled"] is True

        # 获取不存在的回调信息
        info = manager.get_callback_info("nonexistent")
        assert info is None

    def test_list_callbacks(self):
        """测试列出所有回调"""
        manager = ConfigCallbackManager()

        def test_callback1(context):
            pass

        def test_callback2(context):
            pass

        # 注册回调
        manager.register_callback("callback1", test_callback1)
        manager.register_callback(
            "callback2", test_callback2, priority=CallbackPriority.HIGH
        )

        # 列出回调
        callbacks = manager.list_callbacks()

        assert len(callbacks) == 2

        # 验证回调信息
        callback_ids = [c["id"] for c in callbacks]
        assert "callback1" in callback_ids
        assert "callback2" in callback_ids

    def test_execution_history(self):
        """测试执行历史"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册回调
        manager.register_callback("callback", test_callback)

        # 触发回调
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})

        # 获取执行历史
        history = manager.get_execution_history()

        assert len(history) == 1
        assert history[0]["config_path"] == "test.yaml"
        assert history[0]["status"] == "started"
        assert len(history[0]["callbacks"]) == 1
        assert history[0]["callbacks"][0]["callback_id"] == "callback"
        assert history[0]["callbacks"][0]["status"] == "success"

    def test_clear_execution_history(self):
        """测试清除执行历史"""
        manager = ConfigCallbackManager()

        def test_callback(context):
            pass

        # 注册并触发回调
        manager.register_callback("callback", test_callback)
        manager.trigger_callbacks("test.yaml", {}, {"key": "value"})

        # 验证历史存在
        history = manager.get_execution_history()
        assert len(history) == 1

        # 清除历史
        manager.clear_execution_history()

        # 验证历史已清除
        history = manager.get_execution_history()
        assert len(history) == 0


class TestGlobalCallbackManager:
    """全局回调管理器测试类"""

    def test_get_global_callback_manager(self):
        """测试获取全局回调管理器"""
        manager1 = get_global_callback_manager()
        manager2 = get_global_callback_manager()

        # 应该返回同一实例
        assert manager1 is manager2

    def test_register_config_callback(self):
        """测试注册配置回调函数"""

        def test_callback(context):
            pass

        # 注册回调
        register_config_callback("test_callback", test_callback)

        # 验证回调已注册
        manager = get_global_callback_manager()
        assert "test_callback" in manager._callbacks

        # 清理
        unregister_config_callback("test_callback")

    def test_unregister_config_callback(self):
        """测试注销配置回调函数"""

        def test_callback(context):
            pass

        # 注册回调
        register_config_callback("test_callback", test_callback)

        # 注销回调
        success = unregister_config_callback("test_callback")
        assert success is True

        # 验证回调已注销
        manager = get_global_callback_manager()
        assert "test_callback" not in manager._callbacks

    def test_trigger_config_callbacks(self):
        """测试触发配置回调函数"""

        def test_callback(context):
            pass

        callback_mock = Mock(side_effect=test_callback)

        # 注册回调
        register_config_callback("test_callback", callback_mock)

        # 触发回调
        old_config = {"key": "old_value"}
        new_config = {"key": "new_value"}
        trigger_config_callbacks("test.yaml", old_config, new_config)

        # 验证回调被调用
        callback_mock.assert_called_once()

        # 清理
        unregister_config_callback("test_callback")
