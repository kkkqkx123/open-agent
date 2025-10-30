"""Hook配置系统单元测试"""

import pytest
from pydantic import ValidationError

from src.infrastructure.graph.hooks.config import (
    HookConfig, NodeHookConfig, GlobalHookConfig,
    HookType, DeadLoopDetectionConfig, PerformanceMonitoringConfig,
    ErrorRecoveryConfig, LoggingConfig, MetricsCollectionConfig,
    create_hook_config, validate_hook_config, merge_hook_configs
)


class TestHookConfig:
    """HookConfig测试"""
    
    def test_valid_creation(self):
        """测试有效创建"""
        config = HookConfig(
            type=HookType.DEAD_LOOP_DETECTION,
            enabled=True,
            config={"max_iterations": 10},
            node_types=["test_node"],
            priority=5
        )
        
        assert config.type == HookType.DEAD_LOOP_DETECTION
        assert config.enabled is True
        assert config.config["max_iterations"] == 10
        assert config.node_types == ["test_node"]
        assert config.priority == 5
    
    def test_default_values(self):
        """测试默认值"""
        config = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        
        assert config.type == HookType.LOGGING
        assert config.enabled is True
        assert config.config == {}
        assert config.node_types is None
        assert config.priority == 0
    
    def test_invalid_priority(self):
        """测试无效优先级"""
        with pytest.raises(ValidationError):
            HookConfig(
                type=HookType.LOGGING,
                enabled=True,
                config={},
                node_types=None,
                priority=-1
            )
    
    def test_enum_conversion(self):
        """测试枚举转换"""
        config = HookConfig(
            type=HookType.DEAD_LOOP_DETECTION,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        assert config.type == HookType.DEAD_LOOP_DETECTION
        
        # 测试字符串值
        config_dict = config.dict()
        assert config_dict["type"] == "dead_loop_detection"


class TestNodeHookConfig:
    """NodeHookConfig测试"""

    def test_valid_creation(self):
        """测试有效创建"""
        hook1 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        hook2 = HookConfig(
            type=HookType.PERFORMANCE_MONITORING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        
        node_config = NodeHookConfig(
            node_type="test_node",
            hooks=[hook1, hook2],
            inherit_global=True
        )
        
        assert node_config.node_type == "test_node"
        assert len(node_config.hooks) == 2
        assert node_config.inherit_global is True
    
    def test_duplicate_hook_types(self):
        """测试重复Hook类型"""
        hook1 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        hook2 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )

        with pytest.raises(ValidationError):
            NodeHookConfig(
                node_type="test_node",
                hooks=[hook1, hook2],
                inherit_global=True
            )


class TestGlobalHookConfig:
    """GlobalHookConfig测试"""
    
    def test_valid_creation(self):
        """测试有效创建"""
        hook1 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        hook2 = HookConfig(
            type=HookType.PERFORMANCE_MONITORING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )

        global_config = GlobalHookConfig(hooks=[hook1, hook2])
        
        assert len(global_config.hooks) == 2
    
    def test_duplicate_hook_types(self):
        """测试重复Hook类型"""
        hook1 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        hook2 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )

        with pytest.raises(ValidationError):
            GlobalHookConfig(hooks=[hook1, hook2])


class TestHookGroupConfigs:
    """Hook组配置测试"""
    
    def test_dead_loop_detection_config(self):
        """测试死循环检测配置"""
        config = DeadLoopDetectionConfig(enabled=True)
        
        assert config.enabled is True
        assert config.config["max_iterations"] == 20
        assert config.config["fallback_node"] == "dead_loop_check"
        assert config.config["log_level"] == "WARNING"
    
    def test_performance_monitoring_config(self):
        """测试性能监控配置"""
        config = PerformanceMonitoringConfig(enabled=True)
        
        assert config.enabled is True
        assert config.config["timeout_threshold"] == 10.0
        assert config.config["log_slow_executions"] is True
        assert config.config["metrics_collection"] is True
    
    def test_error_recovery_config(self):
        """测试错误恢复配置"""
        config = ErrorRecoveryConfig(enabled=True)
        
        assert config.enabled is True
        assert config.config["max_retries"] == 3
        assert config.config["fallback_node"] == "error_handler"
        assert config.config["retry_delay"] == 1.0
    
    def test_logging_config(self):
        """测试日志配置"""
        config = LoggingConfig(enabled=True)
        
        assert config.enabled is True
        assert config.config["log_level"] == "INFO"
        assert config.config["structured_logging"] is True
    
    def test_metrics_collection_config(self):
        """测试指标收集配置"""
        config = MetricsCollectionConfig(enabled=True)
        
        assert config.enabled is True
        assert config.config["enable_performance_metrics"] is True
        assert config.config["enable_business_metrics"] is True


class TestCreateHookConfig:
    """create_hook_config函数测试"""
    
    def test_create_with_defaults(self):
        """测试使用默认值创建"""
        config = create_hook_config(
            HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        
        assert config.type == HookType.LOGGING
        assert config.enabled is True
        assert "log_level" in config.config
    
    def test_create_with_custom_config(self):
        """测试使用自定义配置创建"""
        config = create_hook_config(
            HookType.DEAD_LOOP_DETECTION,
            enabled=False,
            config={"max_iterations": 5},
            priority=10
        )
        
        assert config.type == HookType.DEAD_LOOP_DETECTION
        assert config.enabled is False
        assert config.config["max_iterations"] == 5
        assert config.priority == 10
    
    def test_create_unknown_type(self):
        """测试创建未知类型"""
        config = create_hook_config(HookType.CUSTOM, config={"custom_param": "value"})
        
        assert config.type == HookType.CUSTOM
        assert config.config["custom_param"] == "value"


class TestValidateHookConfig:
    """validate_hook_config函数测试"""
    
    def test_valid_config(self):
        """测试有效配置"""
        config_dict = {
            "type": "logging",
            "enabled": True,
            "config": {"log_level": "INFO"}
        }
        
        errors = validate_hook_config(config_dict)
        assert len(errors) == 0
    
    def test_invalid_config(self):
        """测试无效配置"""
        config_dict = {
            "type": "invalid_type",
            "enabled": "not_boolean",
            "priority": -1
        }
        
        errors = validate_hook_config(config_dict)
        assert len(errors) > 0


class TestMergeHookConfigs:
    """merge_hook_configs函数测试"""
    
    def test_merge_with_inheritance(self):
        """测试带继承的合并"""
        global_hook = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=1
        )
        node_hook = HookConfig(
            type=HookType.PERFORMANCE_MONITORING,
            enabled=True,
            config={},
            node_types=None,
            priority=2
        )
        
        global_config = GlobalHookConfig(hooks=[global_hook])
        node_config = NodeHookConfig(
            node_type="test_node",
            hooks=[node_hook],
            inherit_global=True
        )
        
        merged = merge_hook_configs(global_config, node_config)
        
        assert len(merged) == 2
        assert HookType.LOGGING in [hook.type for hook in merged]
        assert HookType.PERFORMANCE_MONITORING in [hook.type for hook in merged]
    
    def test_merge_without_inheritance(self):
        """测试不带继承的合并"""
        global_hook = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        node_hook = HookConfig(
            type=HookType.PERFORMANCE_MONITORING,
            enabled=True,
            config={},
            node_types=None,
            priority=0
        )
        
        global_config = GlobalHookConfig(hooks=[global_hook])
        node_config = NodeHookConfig(
            node_type="test_node",
            hooks=[node_hook],
            inherit_global=False
        )
        
        merged = merge_hook_configs(global_config, node_config)
        
        assert len(merged) == 1
        assert merged[0].type == HookType.PERFORMANCE_MONITORING
    
    def test_merge_with_override(self):
        """测试覆盖合并"""
        global_hook = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={"log_level": "INFO"},
            node_types=None,
            priority=1
        )
        node_hook = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={"log_level": "DEBUG"},
            node_types=None,
            priority=2
        )

        global_config = GlobalHookConfig(hooks=[global_hook])
        node_config = NodeHookConfig(
            node_type="test_node",
            hooks=[node_hook],
            inherit_global=True
        )

        merged = merge_hook_configs(global_config, node_config)

        assert len(merged) == 1
        assert merged[0].type == HookType.LOGGING
        assert merged[0].priority == 2  # 节点配置优先级更高
        assert merged[0].config["log_level"] == "DEBUG"  # 节点配置覆盖全局配置
    
    def test_merge_priority_ordering(self):
        """测试优先级排序"""
        hook1 = HookConfig(
            type=HookType.LOGGING,
            enabled=True,
            config={},
            node_types=None,
            priority=1
        )
        hook2 = HookConfig(
            type=HookType.PERFORMANCE_MONITORING,
            enabled=True,
            config={},
            node_types=None,
            priority=3
        )
        hook3 = HookConfig(
            type=HookType.ERROR_RECOVERY,
            enabled=True,
            config={},
            node_types=None,
            priority=2
        )
        
        global_config = GlobalHookConfig(hooks=[hook1, hook2])
        node_config = NodeHookConfig(
            node_type="test_node",
            hooks=[hook3],
            inherit_global=True
        )
        
        merged = merge_hook_configs(global_config, node_config)
        
        # 应该按优先级降序排列
        assert merged[0].priority == 3
        assert merged[1].priority == 2
        assert merged[2].priority == 1


if __name__ == "__main__":
    pytest.main([__file__])