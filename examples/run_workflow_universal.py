"""通用工作流加载器使用示例

演示如何使用通用工作流加载器来简化工作流的加载和执行。
"""

from src.application.workflow.universal_loader import UniversalWorkflowLoader, FunctionType
from src.application.workflow.runner import WorkflowRunner, run_workflow


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


def example_1_basic_usage():
    """示例1：基础用法"""
    print("=" * 60)
    print("示例1：基础用法")
    print("=" * 60)
    
    # 创建加载器
    loader = UniversalWorkflowLoader()
    
    # 注册自定义条件函数
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 加载工作流
    workflow = loader.load_from_file("configs/workflows/plan_execute_agent_workflow.yaml")
    
    # 运行工作流
    result = workflow.run({
        "current_task": "分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议"
    })
    
    print(f"工作流执行完成!")
    print(f"最终状态: {result}")
    
    # 打印执行历史
    if result.get("task_history"):
        print("\n执行历史:")
        for i, task in enumerate(result["task_history"], 1):
            print(f"{i}. {task}")
    
    # 打印计划信息
    context = result.get("context", {})
    if context.get("current_plan"):
        print("\n执行计划:")
        plan = context["current_plan"]
        current_step = context.get("current_step_index", 0)
        for i, step in enumerate(plan, 1):
            status = "✓" if i <= current_step else "○"
            print(f"{status} {i}. {step}")


def example_2_with_runner():
    """示例2：使用工作流运行器"""
    print("\n" + "=" * 60)
    print("示例2：使用工作流运行器")
    print("=" * 60)
    
    # 创建运行器
    runner = WorkflowRunner()
    
    # 注册自定义函数
    runner.loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 运行工作流
    result = runner.run_workflow(
        "configs/workflows/plan_execute_agent_workflow.yaml",
        {"current_task": "分析市场趋势并制定营销策略"}
    )
    
    if result.success:
        print(f"工作流执行成功!")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"结果: {result.result}")
    else:
        print(f"工作流执行失败: {result.error}")
    
    # 获取执行统计
    stats = runner.get_execution_statistics()
    print(f"\n执行统计: {stats}")


def example_3_batch_execution():
    """示例3：批量执行"""
    print("\n" + "=" * 60)
    print("示例3：批量执行")
    print("=" * 60)
    
    # 创建运行器
    runner = WorkflowRunner()
    
    # 注册自定义函数
    runner.loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 批量运行工作流
    config_paths = [
        "configs/workflows/plan_execute_agent_workflow.yaml",
        "configs/workflows/react_workflow.yaml"
    ]
    
    initial_data_list = [
        {"current_task": "分析用户行为数据"},
        {"input": "分析市场趋势"}
    ]
    
    results = runner.batch_run_workflows(config_paths, initial_data_list, max_workers=2)
    
    print(f"批量执行完成，共 {len(results)} 个工作流")
    
    for i, result in enumerate(results, 1):
        print(f"\n工作流 {i}:")
        print(f"  成功: {result.success}")
        print(f"  执行时间: {result.execution_time:.2f} 秒" if result.execution_time else "  执行时间: N/A")
        if result.error:
            print(f"  错误: {result.error}")


def example_4_config_validation():
    """示例4：配置验证"""
    print("\n" + "=" * 60)
    print("示例4：配置验证")
    print("=" * 60)
    
    # 创建加载器
    loader = UniversalWorkflowLoader()
    
    # 验证配置
    validation_result = loader.validate_config("configs/workflows/plan_execute_agent_workflow.yaml")
    
    print(f"验证结果: {validation_result.get_summary()}")
    
    if validation_result.has_errors():
        print("\n错误:")
        for error in validation_result.errors:
            print(f"  - {error}")
    
    if validation_result.has_warnings():
        print("\n警告:")
        for warning in validation_result.warnings:
            print(f"  - {warning}")
    
    if validation_result.suggestions:
        print("\n建议:")
        for suggestion in validation_result.suggestions:
            print(f"  - {suggestion}")


def example_5_function_management():
    """示例5：函数管理"""
    print("\n" + "=" * 60)
    print("示例5：函数管理")
    print("=" * 60)
    
    # 创建加载器
    loader = UniversalWorkflowLoader()
    
    # 注册自定义函数
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 列出已注册的函数
    functions = loader.list_registered_functions()
    print("已注册的函数:")
    print(f"  节点函数: {functions['nodes']}")
    print(f"  条件函数: {functions['conditions']}")
    
    # 获取函数信息
    if "plan_execute_router" in functions['conditions']:
        func_info = loader.get_function_info("plan_execute_router", FunctionType.CONDITION_FUNCTION)
        if func_info:
            print(f"\nplan_execute_router 信息:")
            print(f"  模块: {func_info.get('module')}")
            print(f"  签名: {func_info.get('signature')}")
            print(f"  文档: {func_info.get('doc', '无文档')}")
        else:
            print(f"\nplan_execute_router 信息: 未找到函数信息")
    
    # 获取函数统计
    stats = loader.get_function_statistics()
    print(f"\n函数统计: {stats}")


def example_6_streaming_execution():
    """示例6：流式执行"""
    print("\n" + "=" * 60)
    print("示例6：流式执行")
    print("=" * 60)
    
    # 创建加载器
    loader = UniversalWorkflowLoader()
    
    # 注册自定义函数
    loader.register_function("plan_execute_router", plan_execute_router, FunctionType.CONDITION_FUNCTION)
    
    # 加载工作流
    workflow = loader.load_from_file("configs/workflows/plan_execute_agent_workflow.yaml")
    
    # 流式执行
    print("开始流式执行...")
    for i, chunk in enumerate(workflow.stream({"current_task": "流式执行示例"}), 1):
        print(f"步骤 {i}: {chunk}")
        if i >= 5:  # 限制输出数量
            print("...")
            break


def example_7_convenience_function():
    """示例7：便捷函数"""
    print("\n" + "=" * 60)
    print("示例7：便捷函数")
    print("=" * 60)
    
    # 使用便捷函数运行工作流
    result = run_workflow(
        "configs/workflows/plan_execute_agent_workflow.yaml",
        {"current_task": "使用便捷函数的示例"}
    )
    
    if result.success:
        print(f"工作流执行成功!")
        print(f"执行时间: {result.execution_time:.2f} 秒")
        print(f"工作流名称: {result.workflow_name}")
    else:
        print(f"工作流执行失败: {result.error}")


def main():
    """主函数"""
    print("通用工作流加载器示例")
    print("=" * 60)
    
    try:
        # 运行各种示例
        example_1_basic_usage()
        example_2_with_runner()
        example_3_batch_execution()
        example_4_config_validation()
        example_5_function_management()
        example_6_streaming_execution()
        example_7_convenience_function()
        
        print("\n" + "=" * 60)
        print("所有示例执行完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n示例执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()