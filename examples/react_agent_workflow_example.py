"""ReAct Agent工作流示例

演示如何使用ReActAgentNode构建工作流。
"""

from src.infrastructure.graph.config import GraphConfig, NodeConfig, EdgeConfig, EdgeType
from src.infrastructure.graph.builder import GraphBuilder
from src.infrastructure.graph.nodes import ReActAgentNode, LLMNode
from src.infrastructure.llm.clients.mock import MockLLMClient
from src.infrastructure.llm.config import MockConfig
from src.infrastructure.tools.executor import AsyncToolExecutor as ToolExecutor
from src.domain.agent.state import AgentState


def create_react_workflow() -> GraphConfig:
    """创建ReAct工作流配置"""
    
    # 定义节点
    nodes = {
        "react_agent": NodeConfig(
            name="react_agent",
            function_name="react_agent_node",
            config={
                "name": "react_agent",
                "system_prompt": "你是一个使用ReAct算法的智能助手，通过推理和行动来解决问题。",
                "max_iterations": 5,
                "tools": ["calculator", "search"],
                "llm_client": "mock",
                "next_node_on_complete": "final_response",
                "next_node_on_error": "error_handler"
            },
            description="ReAct Agent节点，执行推理和行动"
        ),
        
        "final_response": NodeConfig(
            name="final_response",
            function_name="llm_node",
            config={
                "llm_client": "mock",
                "system_prompt": "请总结ReAct Agent的执行结果，并提供最终答案。",
                "max_tokens": 1000,
                "temperature": 0.3
            },
            description="生成最终响应"
        ),
        
        "error_handler": NodeConfig(
            name="error_handler",
            function_name="llm_node",
            config={
                "llm_client": "mock",
                "system_prompt": "处理执行过程中发生的错误，并提供有用的错误信息。",
                "max_tokens": 500,
                "temperature": 0.1
            },
            description="错误处理节点"
        )
    }
    
    # 定义边
    edges = [
        EdgeConfig(
            from_node="react_agent",
            to_node="final_response",
            type=EdgeType.CONDITIONAL,
            condition="task_completed",
            description="任务完成后生成最终响应"
        ),
        
        EdgeConfig(
            from_node="react_agent",
            to_node="error_handler",
            type=EdgeType.CONDITIONAL,
            condition="has_error",
            description="发生错误时进行错误处理"
        ),
        
        EdgeConfig(
            from_node="final_response",
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
        name="react_agent_workflow",
        description="基于ReAct Agent的工作流示例",
        version="1.0",
        nodes=nodes,
        edges=edges,
        entry_point="react_agent",
        additional_config={
            "max_execution_time": 300,
            "enable_logging": True
        }
    )
    
    return graph_config


def run_react_workflow_example():
    """运行ReAct工作流示例"""
    
    # 创建工作流配置
    workflow_config = create_react_workflow()
    
    # 创建图构建器
    builder = GraphBuilder()
    
    # 构建图
    graph = builder.build_graph(workflow_config)
    
    if graph is None:
        print("无法构建图，请检查配置")
        return
    
    # 创建初始状态
    initial_state = AgentState(
        current_task="计算 15 * 23 + 42 的结果",
        max_iterations=10,
        iteration_count=0
    )
    
    # 执行工作流
    print("开始执行ReAct工作流...")
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
        
        # 打印消息历史
        if hasattr(result, 'messages') and result.messages:
            print("\n消息历史:")
            for i, msg in enumerate(result.messages, 1):
                print(f"{i}. [{msg.role}]: {msg.content}")
                
    except Exception as e:
        print(f"工作流执行失败: {e}")


if __name__ == "__main__":
    run_react_workflow_example()