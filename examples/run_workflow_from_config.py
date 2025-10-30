"""从配置文件运行工作流示例

演示如何使用YAML配置文件来创建和执行工作流。
"""

from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.config import GraphConfig
from src.domain.agent.state import AgentState


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


class CustomGraphBuilder(GraphBuilder):
    """自定义图构建器，支持我们的条件函数"""
    
    def _get_builtin_condition(self, condition_name: str):
        """获取内置条件函数，包括我们的自定义条件"""
        if condition_name == "plan_execute_router":
            return plan_execute_router
        # 调用父类方法获取其他内置条件
        return super()._get_builtin_condition(condition_name)


def run_workflow_from_config(config_path: str):
    """从配置文件运行工作流"""
    
    # 创建自定义图构建器
    builder = CustomGraphBuilder()
    
    # 从YAML文件构建图
    print(f"从配置文件加载工作流: {config_path}")
    
    # 先加载配置以获取额外设置
    with open(config_path, 'r', encoding='utf-8') as f:
        import yaml
        config_data = yaml.safe_load(f)
    workflow_config = GraphConfig.from_dict(config_data)
    
    graph = builder.build_from_yaml(config_path)
    
    if graph is None:
        print("无法构建图，请检查配置文件")
        return
    
    # 创建初始状态
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
    
    # 执行工作流
    print("开始执行工作流...")
    print(f"初始任务: {initial_state['current_task']}")
    print("-" * 50)
    
    try:
        # 从配置中获取递归限制
        recursion_limit = workflow_config.additional_config.get("recursion_limit", 10)
        
        # 执行图，设置递归限制
        result = graph.invoke(initial_state, config={"recursion_limit": recursion_limit})
        
        print("工作流执行完成!")
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
        
        # 打印消息历史
        if result.get("workflow_messages"):
            print("\n消息历史:")
            for i, msg in enumerate(result["workflow_messages"], 1):
                print(f"{i}. {msg}")
                
    except Exception as e:
        print(f"工作流执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行配置文件中的工作流
    config_path = "configs/workflows/plan_execute_agent_workflow.yaml"
    run_workflow_from_config(config_path)