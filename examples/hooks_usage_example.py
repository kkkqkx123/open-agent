"""Hook机制使用示例

展示如何在代码中使用Graph Hook机制。
"""

import logging
from pathlib import Path

from src.infrastructure.config_loader import YamlConfigLoader
from src.infrastructure.graph.hooks import (
    NodeHookManager,
    HookAwareGraphBuilder,
    create_hook_aware_builder,
    DeadLoopDetectionHook,
    PerformanceMonitoringHook,
    ErrorRecoveryHook,
    LoggingHook,
    MetricsCollectionHook
)
from src.infrastructure.graph.state import create_react_state
from src.infrastructure.graph.registry import get_global_registry

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_basic_hook_usage():
    """基础Hook使用示例"""
    logger.info("=== 基础Hook使用示例 ===")
    
    # 1. 创建配置加载器
    config_loader = YamlConfigLoader()
    
    # 2. 创建Hook管理器
    hook_manager = NodeHookManager(config_loader)
    
    # 3. 加载全局Hook配置
    hook_manager.load_hooks_from_config()
    
    # 4. 创建Hook感知的Graph构建器
    builder = create_hook_aware_builder(
        node_registry=get_global_registry(),
        hook_manager=hook_manager,
        config_loader=config_loader
    )
    
    # 5. 从配置文件构建图
    graph_config_path = "configs/graphs/react_with_hooks_example.yaml"
    graph = builder.build_from_yaml(graph_config_path)
    
    # 6. 创建初始状态
    initial_state = create_react_state(
        workflow_id="react_example",
        input_text="请计算 123 + 456 并解释结果",
        max_iterations=10
    )
    
    # 7. 执行图
    logger.info("开始执行带Hook的图...")
    try:
        result = graph.invoke(initial_state)
        logger.info(f"图执行完成，结果: {result}")
    except Exception as e:
        logger.error(f"图执行失败: {e}")
    
    # 8. 获取Hook统计信息
    stats = builder.get_hook_statistics()
    logger.info(f"Hook统计信息: {stats}")


def example_manual_hook_configuration():
    """手动配置Hook示例"""
    logger.info("=== 手动配置Hook示例 ===")
    
    # 1. 创建配置加载器
    config_loader = YamlConfigLoader()
    
    # 2. 创建Hook管理器
    hook_manager = NodeHookManager(config_loader)
    
    # 3. 手动创建和注册Hook
    # 死循环检测Hook
    dead_loop_hook = DeadLoopDetectionHook({
        "max_iterations": 5,
        "fallback_node": "dead_loop_handler",
        "log_level": "WARNING"
    })
    hook_manager.register_hook(dead_loop_hook, ["llm_node", "analysis_node"])
    
    # 性能监控Hook
    performance_hook = PerformanceMonitoringHook({
        "timeout_threshold": 30.0,
        "log_slow_executions": True,
        "metrics_collection": True
    })
    hook_manager.register_hook(performance_hook)  # 全局Hook
    
    # 错误恢复Hook
    error_recovery_hook = ErrorRecoveryHook({
        "max_retries": 2,
        "fallback_node": "error_handler",
        "retry_delay": 1.0
    })
    hook_manager.register_hook(error_recovery_hook, ["tool_node"])
    
    # 日志Hook
    logging_hook = LoggingHook({
        "log_level": "INFO",
        "structured_logging": True
    })
    hook_manager.register_hook(logging_hook)  # 全局Hook
    
    # 4. 创建Hook感知的Graph构建器
    builder = HookAwareGraphBuilder(
        node_registry=get_global_registry(),
        hook_manager=hook_manager,
        config_loader=config_loader
    )
    
    # 5. 构建简单的图
    from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType, GraphStateConfig, StateFieldConfig
    
    config = GraphConfig(
        name="简单Hook示例",
        description="展示手动配置Hook的简单图",
        state_schema=GraphStateConfig(
            name="ReActState",
            fields={
                "messages": StateFieldConfig(type="List[str]"),
                "input": StateFieldConfig(type="str"),
                "agent_outcome": StateFieldConfig(type="str", default=""),
                "intermediate_steps": StateFieldConfig(type="List[dict]", default=[])
            }
        ),
        entry_point="start"
    )
    
    # 添加节点
    config.nodes["start"] = NodeConfig(
        name="start",
        function_name="analysis_node",
        description="开始节点"
    )
    
    config.nodes["process"] = NodeConfig(
        name="process",
        function_name="llm_node",
        description="处理节点"
    )
    
    config.nodes["end"] = NodeConfig(
        name="end",
        function_name="condition_node",
        description="结束节点"
    )
    
    # 添加边
    config.edges.append(EdgeConfig(
        from_node="start",
        to_node="process",
        type=EdgeType.SIMPLE
    ))
    
    config.edges.append(EdgeConfig(
        from_node="process",
        to_node="end",
        type=EdgeType.SIMPLE
    ))
    
    # 6. 构建图
    graph = builder.build_graph(config)
    
    # 7. 创建初始状态并执行
    initial_state = create_react_state(
        workflow_id="manual_hook_example",
        input_text="测试手动配置的Hook",
        max_iterations=5
    )
    
    logger.info("开始执行手动配置Hook的图...")
    try:
        result = graph.invoke(initial_state)
        logger.info(f"图执行完成，结果: {result}")
    except Exception as e:
        logger.error(f"图执行失败: {e}")


def example_custom_hook_creation():
    """自定义Hook创建示例"""
    logger.info("=== 自定义Hook创建示例 ===")
    
    from src.infrastructure.graph.hooks.interfaces import INodeHook, HookContext, HookExecutionResult, HookPoint
    
    class CustomValidationHook(INodeHook):
        """自定义验证Hook"""
        
        def __init__(self, hook_config):
            super().__init__(hook_config)
            self.validation_rules = hook_config.get("validation_rules", {})
        
        @property
        def hook_type(self) -> str:
            return "custom_validation"
        
        def before_execute(self, context: HookContext) -> HookExecutionResult:
            """执行前验证"""
            # 检查状态中是否有必需字段
            required_fields = self.validation_rules.get("required_fields", [])
            missing_fields = []
            
            for field in required_fields:
                if not hasattr(context.state, field) or getattr(context.state, field) is None:
                    missing_fields.append(field)
            
            if missing_fields:
                logger.error(f"缺少必需字段: {missing_fields}")
                return HookExecutionResult(
                    should_continue=False,
                    force_next_node="validation_error_handler",
                    metadata={
                        "validation_failed": True,
                        "missing_fields": missing_fields
                    }
                )
            
            return HookExecutionResult(should_continue=True)
        
        def after_execute(self, context: HookContext) -> HookExecutionResult:
            """执行后验证"""
            # 检查执行结果是否符合预期
            expected_result_type = self.validation_rules.get("expected_result_type")
            if expected_result_type and context.execution_result:
                result_type = type(context.execution_result.state).__name__
                if result_type != expected_result_type:
                    logger.warning(f"结果类型不匹配: 期望 {expected_result_type}, 实际 {result_type}")
            
            return HookExecutionResult(should_continue=True)
        
        def on_error(self, context: HookContext) -> HookExecutionResult:
            """错误处理"""
            logger.error(f"自定义验证Hook捕获错误: {context.error}")
            return HookExecutionResult(should_continue=True)
    
    # 使用自定义Hook
    config_loader = YamlConfigLoader()
    hook_manager = NodeHookManager(config_loader)
    
    # 创建并注册自定义Hook
    custom_hook = CustomValidationHook({
        "validation_rules": {
            "required_fields": ["input", "messages"],
            "expected_result_type": "ReActState"
        }
    })
    
    hook_manager.register_hook(custom_hook, ["analysis_node", "llm_node"])
    
    logger.info("自定义Hook已注册")


def example_hook_performance_monitoring():
    """Hook性能监控示例"""
    logger.info("=== Hook性能监控示例 ===")
    
    config_loader = YamlConfigLoader()
    hook_manager = NodeHookManager(config_loader)
    
    # 创建性能监控Hook
    performance_hook = PerformanceMonitoringHook({
        "timeout_threshold": 10.0,
        "log_slow_executions": True,
        "metrics_collection": True,
        "enable_profiling": True
    })
    
    hook_manager.register_hook(performance_hook)
    
    # 创建指标收集Hook
    metrics_hook = MetricsCollectionHook({
        "enable_performance_metrics": True,
        "enable_business_metrics": True,
        "enable_system_metrics": True
    })
    
    hook_manager.register_hook(metrics_hook)
    
    # 模拟节点执行
    logger.info("模拟节点执行以收集性能数据...")
    
    # 更新性能统计
    hook_manager.update_performance_stats("test_node", 2.5, success=True)
    hook_manager.update_performance_stats("test_node", 3.1, success=True)
    hook_manager.update_performance_stats("test_node", 15.2, success=False)  # 慢执行
    
    # 获取性能统计
    stats = hook_manager.get_node_performance_stats("test_node")
    logger.info(f"性能统计: {stats}")
    
    # 获取指标收集数据
    if hasattr(metrics_hook, 'get_metrics'):
        metrics = metrics_hook.get_metrics()
        logger.info(f"收集的指标: {metrics}")


if __name__ == "__main__":
    """运行所有示例"""
    logger.info("开始运行Hook机制使用示例")
    
    try:
        # 基础Hook使用示例
        example_basic_hook_usage()
        
        # 手动配置Hook示例
        example_manual_hook_configuration()
        
        # 自定义Hook创建示例
        example_custom_hook_creation()
        
        # Hook性能监控示例
        example_hook_performance_monitoring()
        
        logger.info("所有示例运行完成")
        
    except Exception as e:
        logger.error(f"示例运行失败: {e}")
        import traceback
        traceback.print_exc()