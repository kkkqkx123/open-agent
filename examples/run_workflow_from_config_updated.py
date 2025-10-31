"""从配置文件运行工作流示例 - 更新版本

演示如何使用通用工作流加载器来简化工作流的加载和执行。
这个版本展示了如何用更少的代码实现相同的功能。
"""

from src.application.workflow.universal_loader import UniversalWorkflowLoader, FunctionType
from src.application.workflow.runner import WorkflowRunner


def plan_execute_router(state) -> str:
    """Plan-Execute Agent路由函数"""
    # 首先检查是否有错误
    if state.get("workflow_errors"):
        return "error_handler"
    
    # 检查计划状态
    context = state.get("context", {})
    current_plan = context.get("current_plan", [])
    current_step_index = context.get("current_step_index", 0)
    
    # 如果还没有计划，继续执行当前节点来生成计划
    if not current_plan:
        return "continue"
    
    # 如果计划需要审查，进入审查节点
    if context.get("needs_review", False):
        return "plan_review"
    
    # 如果计划已完成，进入总结
    if current_step_index >= len(current_plan) and current_plan:
        return "final_summary"
    
    # 否则继续执行当前节点
    return "continue"


def run_workflow_from_config_old_way(config_path: str):
    """旧版本的工作流运行方式（复杂）"""
    print("=" * 60)
    print("旧版本实现方式（复杂）")
    print("=" * 60)
    
    # 需要创建自定义图构建器
    class CustomGraphBuilder:
        def __init__(self):
            self.condition_functions = {}
        
        def register_condition(self, name: str, function):
            self.condition_functions[name] = function
        
        def get_condition(self, name: str):
            return self.condition_functions.get(name)
        
        def build_from_yaml(self, config_path: str):
            # 这里需要复杂的图构建逻辑
            print("  - 手动创建自定义图构建器")
            print("  - 手动注册条件函数")
            print("  - 手动解析YAML配置")
            print("  - 手动创建图结构")
            print("  - 手动处理节点和边")
            return Mock()  # 简化示例
    
    # 创建自定义图构建器
    builder = CustomGraphBuilder()
    builder.register_condition("plan_execute_router", plan_execute_router)
    
    # 从YAML文件构建图
    print(f"从配置文件加载工作流: {config_path}")
    graph = builder.build_from_yaml(config_path)
    
    # 手动创建复杂的初始状态
    initial_state = {
        "workflow_messages": [],
        "workflow_tool_calls": [],
        "workflow_tool_results": [],
        "workflow_iteration_count": 0,
        "workflow_max_iterations": 15,
        "task_history": [],
        "workflow_errors": [],
        "context": {
            "current_plan": [],
            "current_step_index": 0,
            "plan_completed": False
        },
        "current_task": "分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议"
    }
    
    print("  - 手动创建包含10+字段的初始状态")
    print("  - 手动设置默认值和嵌套结构")
    
    # 执行工作流
    print("开始执行工作流...")
    print(f"初始任务: {initial_state['current_task']}")
    
    try:
        # 模拟执行
        result = {"status": "completed", "workflow_messages": ["消息1", "消息2"]}
        print("工作流执行完成!")
        print(f"最终状态: {result}")
        
    except Exception as e:
        print(f"工作流执行失败: {e}")


def run_workflow_from_config_new_way(config_path: str):
    """新版本的工作流运行方式（简化）"""
    print("\n" + "=" * 60)
    print("新版本实现方式（简化）")
    print("=" * 60)
    
    # 创建通用加载器
    loader = UniversalWorkflowLoader()
    
    # 注册自定义条件函数（一行代码）
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    print("  - 使用通用加载器自动处理图构建")
    print("  - 一行代码注册自定义函数")
    
    # 加载工作流（一行代码）
    workflow = loader.load_from_file(config_path)
    print(f"  - 自动加载和解析配置: {config_path}")
    print("  - 自动验证配置完整性")
    print("  - 自动创建图结构")
    
    # 运行工作流（一行代码）
    result = workflow.run({
        "current_task": "分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议"
    })
    print("  - 自动状态初始化")
    print("  - 自动错误处理")
    print("  - 自动执行管理")
    
    print("工作流执行完成!")
    print(f"最终状态: {result}")


def run_workflow_with_runner(config_path: str):
    """使用工作流运行器（更加简化）"""
    print("\n" + "=" * 60)
    print("使用工作流运行器（更加简化）")
    print("=" * 60)
    
    # 创建运行器
    runner = WorkflowRunner()
    
    # 注册函数
    runner.loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 运行工作流（一行代码，包含所有功能）
    result = runner.run_workflow(
        config_path,
        {"current_task": "分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议"}
    )
    
    print("  - 一行代码完成所有操作")
    print("  - 自动重试机制")
    print("  - 自动统计收集")
    print("  - 自动错误处理")
    
    if result.success:
        print(f"工作流执行成功!")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"结果: {result.result}")
    else:
        print(f"工作流执行失败: {result.error}")


def run_workflow_convenience_function(config_path: str):
    """使用便捷函数（最简化）"""
    print("\n" + "=" * 60)
    print("使用便捷函数（最简化）")
    print("=" * 60)
    
    from src.application.workflow.runner import run_workflow
    
    # 注册全局函数（只需要一次）
    loader = UniversalWorkflowLoader()
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 一行代码运行工作流
    result = run_workflow(
        config_path,
        {"current_task": "分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议"}
    )
    
    print("  - 仅仅一行代码！")
    print("  - 所有复杂性都被隐藏")
    
    if result.success:
        print(f"工作流执行成功!")
        print(f"执行时间: {result.execution_time:.2f} 秒")
    else:
        print(f"工作流执行失败: {result.error}")


def demonstrate_advanced_features(config_path: str):
    """演示高级功能"""
    print("\n" + "=" * 60)
    print("演示高级功能")
    print("=" * 60)
    
    loader = UniversalWorkflowLoader()
    runner = WorkflowRunner()
    
    # 注册函数
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 1. 配置验证
    print("1. 配置验证:")
    validation_result = loader.validate_config(config_path)
    print(f"   验证结果: {validation_result.get_summary()}")
    if validation_result.has_warnings:
        print(f"   警告数量: {len(validation_result.warnings)}")
    
    # 2. 函数管理
    print("\n2. 函数管理:")
    functions = loader.list_registered_functions()
    print(f"   已注册节点函数: {len(functions['nodes'])} 个")
    print(f"   已注册条件函数: {len(functions['conditions'])} 个")
    
    # 3. 批量执行
    print("\n3. 批量执行:")
    config_paths = [config_path, config_path]  # 重复使用相同配置进行演示
    initial_data_list = [
        {"current_task": "任务1：分析数据"},
        {"current_task": "任务2：生成报告"}
    ]
    
    results = runner.batch_run_workflows(config_paths, initial_data_list, max_workers=2)
    print(f"   批量执行完成: {len(results)} 个工作流")
    successful = sum(1 for r in results if r.success)
    print(f"   成功: {successful}, 失败: {len(results) - successful}")
    
    # 4. 执行统计
    print("\n4. 执行统计:")
    stats = runner.get_execution_statistics()
    print(f"   总执行次数: {stats['total_executions']}")
    print(f"   成功率: {stats['success_rate']:.2%}")
    print(f"   平均执行时间: {stats['average_execution_time']:.2f} 秒")
    
    # 5. 工作流信息
    print("\n5. 工作流信息:")
    workflow_info = runner.get_workflow_info(config_path)
    if workflow_info:
        print(f"   工作流名称: {workflow_info['name']}")
        print(f"   节点数量: {len(workflow_info['nodes'])}")
        print(f"   边数量: {len(workflow_info['edges'])}")


def demonstrate_config_enhancements():
    """演示配置增强功能"""
    print("\n" + "=" * 60)
    print("演示配置增强功能")
    print("=" * 60)
    
    # 展示增强的配置格式
    enhanced_config = {
        "name": "enhanced_workflow",
        "description": "增强功能演示工作流",
        "version": "1.0",
        
        # 函数注册配置
        "function_registrations": {
            "nodes": {
                "custom_node": "src.custom.nodes.my_node"
            },
            "conditions": {
                "custom_router": "src.custom.conditions.my_router"
            },
            "auto_discovery": {
                "enabled": True,
                "module_paths": [
                    "src.workflow.nodes",
                    "src.workflow.conditions"
                ]
            }
        },
        
        # 状态模板配置
        "state_template": "plan_execute_state",
        "state_overrides": {
            "workflow_max_iterations": 20,
            "context": {
                "plan_max_steps": 8
            }
        },
        
        "state_schema": {
            "name": "EnhancedWorkflowState",
            "fields": {
                "workflow_messages": {
                    "type": "List[dict]",
                    "default": []
                },
                "current_task": {
                    "type": "str",
                    "default": ""
                }
            }
        },
        
        "nodes": {
            "start_node": {
                "type": "llm_node",
                "config": {
                    "system_prompt": "你是一个AI助手"
                }
            }
        },
        
        "edges": [
            {
                "from": "start_node",
                "to": "__end__",
                "type": "simple"
            }
        ],
        
        "entry_point": "start_node",
        
        "additional_config": {
            "recursion_limit": 15,
            "enable_logging": True
        }
    }
    
    print("增强的配置功能:")
    print("  1. function_registrations - 自动函数注册")
    print("  2. auto_discovery - 自动函数发现")
    print("  3. state_template - 状态模板支持")
    print("  4. state_overrides - 状态覆盖")
    print("  5. 增强的验证和错误处理")
    
    # 创建加载器并验证增强配置
    loader = UniversalWorkflowLoader()
    
    try:
        # 验证配置
        validation_result = loader.validate_config(enhanced_config)
        print(f"\n配置验证结果: {validation_result.get_summary()}")
        
        if validation_result.has_suggestions:
            print("改进建议:")
            for suggestion in validation_result.suggestions[:3]:  # 显示前3个建议
                print(f"  - {suggestion}")
    
    except Exception as e:
        print(f"配置验证失败: {e}")


class Mock:
    """模拟对象，用于演示"""
    def invoke(self, state, config=None):
        return {"status": "completed", "workflow_messages": ["模拟消息1", "模拟消息2"]}


def main():
    """主函数"""
    print("通用工作流配置加载器对比演示")
    print("=" * 60)
    
    config_path = "configs/workflows/plan_execute_agent_workflow.yaml"
    
    try:
        # 演示不同的实现方式
        run_workflow_from_config_old_way(config_path)
        run_workflow_from_config_new_way(config_path)
        run_workflow_with_runner(config_path)
        run_workflow_convenience_function(config_path)
        
        # 演示高级功能
        demonstrate_advanced_features(config_path)
        demonstrate_config_enhancements()
        
        print("\n" + "=" * 60)
        print("总结:")
        print("=" * 60)
        print("✅ 通用工作流配置加载器显著简化了工作流的使用")
        print("✅ 消除了硬编码的需求")
        print("✅ 提供了统一的函数注册机制")
        print("✅ 自动处理状态初始化")
        print("✅ 支持多种执行模式和高级功能")
        print("✅ 保持了完全的向后兼容性")
        print("✅ 提供了完善的错误处理和验证")
        
        print("\n代码行数对比:")
        print("  旧版本: ~50 行代码")
        print("  新版本: ~5 行代码")
        print("  简化程度: 90%")
        
    except Exception as e:
        print(f"\n演示执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()