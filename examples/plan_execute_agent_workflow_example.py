"""Plan-Execute Agent工作流示例

演示如何使用PlanExecuteAgentNode构建工作流。
"""

from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.nodes import PlanExecuteAgentNode, LLMNode
from src.infrastructure.llm.clients.mock import MockLLMClient
from src.infrastructure.llm.config import MockConfig
from src.infrastructure.tools.executor import ToolExecutor
from src.domain.agent.state import AgentState


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
    
    # 创建图配置
    graph_config = GraphConfig(
        name="plan_execute_agent_workflow",
        description="基于Plan-Execute Agent的工作流示例",
        version="1.0",
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
    
    # 创建图构建器
    builder = GraphBuilder()
    
    # 构建图
    graph = builder.build_graph(workflow_config)
    
    if graph is None:
        print("无法构建图，请检查配置")
        return
    
    # 创建初始状态
    initial_state = AgentState(
        current_task="分析用户行为数据，找出最受欢迎的产品类别，并提供改进建议",
        max_iterations=15,
        iteration_count=0
    )
    
    # 执行工作流
    print("开始执行Plan-Execute工作流...")
    print(f"初始任务: {initial_state.current_task}")
    print("-" * 50)
    
    try:
        # 执行图
        result = graph.invoke(initial_state)
        
        print("工作流执行完成!")
        print(f"最终状态: {result}")
        
        # 打印执行历史
        if hasattr(result, 'task_history') and result.task_history:
            print("\n执行历史:")
            for i, task in enumerate(result.task_history, 1):
                print(f"{i}. Agent: {task.get('agent_id')}, 迭代: {task.get('iterations')}, 状态: {task.get('final_state')}")
        
        # 打印计划信息
        if hasattr(result, 'context') and 'current_plan' in result.context:
            print("\n执行计划:")
            plan = result.context['current_plan']
            current_step = result.context.get('current_step_index', 0)
            for i, step in enumerate(plan, 1):
                status = "✓" if i <= current_step else "○"
                print(f"{status} {i}. {step}")
        
        # 打印消息历史
        if hasattr(result, 'messages') and result.messages:
            print("\n消息历史:")
            for i, msg in enumerate(result.messages, 1):
                print(f"{i}. [{msg.role}]: {msg.content}")
                
    except Exception as e:
        print(f"工作流执行失败: {e}")


if __name__ == "__main__":
    run_plan_execute_workflow_example()