"""Plan-Execute Agent工作流示例

演示如何使用PlanExecuteAgentNode构建工作流。
"""

from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.nodes import LLMNode
from src.infrastructure.graph.states import create_agent_state
from src.infrastructure.llm.clients.mock import MockLLMClient
from src.infrastructure.llm.config import MockConfig
from src.infrastructure.tools.executor import AsyncToolExecutor as ToolExecutor


def plan_generated(state) -> str:
    """检查是否已生成计划"""
    return "plan_review" if state.get("current_plan") else "continue"


def plan_completed(state) -> str:
    """检查计划是否已完成"""
    plan = state.get("current_plan", [])
    current_step = state.get("current_step_index", 0)
    return "__end__" if current_step >= len(plan) else "continue"


def has_error(state) -> str:
    """检查是否有错误"""
    return "error_handler" if state.get("errors") else "continue"


def create_plan_execute_workflow() -> GraphConfig:
    """创建Plan-Execute工作流配置"""
    
    # 定义节点
    nodes = {
        "plan_execute_agent": NodeConfig(
            name="plan_execute_agent",
            function_name="plan_execute_agent_node",
            config={
                "name": "plan_execute_agent",
                "system_prompt": "你是一个使用Plan-Execute算法的智能助手，先制定计划然后逐步执行。",
                "max_iterations": 10,
                "max_steps": 5,
                "tools": ["calculator", "search", "database"],
                "llm_client": "mock",
                "next_node_on_complete": "final_summary",
                "next_node_on_error": "error_handler",
                "continue_on_plan_generated": True
            },
            description="Plan-Execute Agent节点，制定和执行计划"
        ),
        
        "plan_review": NodeConfig(
            name="plan_review",
            function_name="llm_node",
            config={
                "llm_client": "mock",
                "system_prompt": "审查生成的计划是否合理，并提供改进建议。",
                "max_tokens": 800,
                "temperature": 0.2
            },
            description="计划审查节点"
        ),
        
        "final_summary": NodeConfig(
            name="final_summary",
            function_name="llm_node",
            config={
                "llm_client": "mock",
                "system_prompt": "总结整个计划执行过程，包括计划步骤、执行结果和最终结论。",
                "max_tokens": 1500,
                "temperature": 0.3
            },
            description="生成最终总结"
        ),
        
        "error_handler": NodeConfig(
            name="error_handler",
            function_name="llm_node",
            config={
                "llm_client": "mock",
                "system_prompt": "处理计划执行过程中发生的错误，并提供恢复建议。",
                "max_tokens": 500,
                "temperature": 0.1
            },
            description="错误处理节点"
        )
    }
    
    # 定义边
    edges = [
        EdgeConfig(
            from_node="plan_execute_agent",
            to_node="plan_review",
            type=EdgeType.CONDITIONAL,
            condition="plan_generated",
            description="计划生成后进行审查"
        ),
        
        EdgeConfig(
            from_node="plan_execute_agent",
            to_node="final_summary",
            type=EdgeType.CONDITIONAL,
            condition="plan_completed",
            description="计划执行完成后生成总结"
        ),
        
        EdgeConfig(
            from_node="plan_execute_agent",
            to_node="error_handler",
            type=EdgeType.CONDITIONAL,
            condition="has_error",
            description="发生错误时进行错误处理"
        ),
        
        EdgeConfig(
            from_node="plan_review",
            to_node="plan_execute_agent",
            type=EdgeType.SIMPLE,
            description="计划审查后继续执行"
        ),
        
        EdgeConfig(
            from_node="final_summary",
            to_node="__end__",
            type=EdgeType.SIMPLE,
            description="工作流结束"
        ),
        
        EdgeConfig(
            from_node="error_handler",
            to_node="__end__",
            type=EdgeType.SIMPLE,
            description="错误处理后结束工作流"
        )
    ]
    
    # 创建状态模式配置
    from src.infrastructure.graph.config import GraphStateConfig, StateFieldConfig
    
    state_schema = GraphStateConfig(
        name="PlanExecuteWorkflowState",
        fields={
            "workflow_messages": StateFieldConfig(
                type="List[dict]",
                default=[],
                description="工作流消息历史"
            ),
            "current_task": StateFieldConfig(
                type="str",
                default="",
                description="当前任务"
            ),
            "current_plan": StateFieldConfig(
                type="List[str]",
                default=[],
                description="当前计划"
            ),
            "current_step_index": StateFieldConfig(
                type="int",
                default=0,
                description="当前步骤索引"
            ),
            "workflow_iteration_count": StateFieldConfig(
                type="int",
                default=0,
                description="工作流迭代计数"
            ),
            "workflow_max_iterations": StateFieldConfig(
                type="int",
                default=10,
                description="工作流最大迭代次数"
            ),
            "task_history": StateFieldConfig(
                type="List[dict]",
                default=[],
                description="任务历史"
            ),
            "workflow_context": StateFieldConfig(
                type="Dict[str, Any]",
                default={},
                description="工作流上下文信息"
            )
        }
    )
    
    # 创建图配置
    graph_config = GraphConfig(
        name="plan_execute_agent_workflow",
        description="基于Plan-Execute Agent的工作流示例",
        version="1.0",
        state_schema=state_schema,
        nodes=nodes,
        edges=edges,
        entry_point="plan_execute_agent",
        additional_config={
            "max_execution_time": 600,
            "enable_logging": True,
            "plan_max_steps": 5
        }
    )
    
    return graph_config


def run_plan_execute_workflow_example():
    """运行Plan-Execute工作流示例"""
    
    # 创建工作流配置
    workflow_config = create_plan_execute_workflow()
    
    # 创建自定义图构建器，添加我们的条件函数
    class CustomGraphBuilder(GraphBuilder):
        def _get_builtin_condition(self, condition_name: str):
            """获取内置条件函数，包括我们的自定义条件"""
            if condition_name == "plan_generated":
                return plan_generated
            elif condition_name == "plan_completed":
                return plan_completed
            elif condition_name == "has_error":
                return has_error
            # 调用父类方法获取其他内置条件
            return super()._get_builtin_condition(condition_name)
    
    # 创建图构建器
    builder = CustomGraphBuilder()
    
    # 构建图
    graph = builder.build_graph(workflow_config)
    
    if graph is None:
        print("无法构建图，请检查配置")
        return
    
    # 创建初始状态
    initial_state = create_agent_state(
        input_text="分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议",
        max_iterations=15
    )
    
    # 执行工作流
    print("开始执行Plan-Execute工作流...")
    print(f"初始任务: {initial_state.get('input', '')}")
    print("-" * 50)
    
    try:
        # 执行图
        result = graph.invoke(initial_state)
        
        print("工作流执行完成!")
        print(f"最终状态: {result}")
        
        # 打印消息历史
        if result.get('messages'):
            print("\n消息历史:")
            for i, msg in enumerate(result.get('messages', []), 1):
                role = msg.get('role') if isinstance(msg, dict) else getattr(msg, 'role', 'unknown')
                content = msg.get('content') if isinstance(msg, dict) else getattr(msg, 'content', '')
                print(f"{i}. [{role}]: {content}")
                
    except Exception as e:
        print(f"工作流执行失败: {e}")


if __name__ == "__main__":
    run_plan_execute_workflow_example()