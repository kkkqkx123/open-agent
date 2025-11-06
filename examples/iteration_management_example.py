"""
迭代管理器使用示例

演示如何使用新的迭代管理器系统创建一个具有高级迭代控制的工作流。
"""

from datetime import datetime
from src.infrastructure.graph import (
    IterationAwareGraphBuilder,
    GraphConfig,
    NodeConfig,
    EdgeConfig,
    EdgeType,
    create_workflow_state
)
from src.infrastructure.graph.registry import BaseNode, NodeExecutionResult, node


# 定义示例节点
@node("example_think_node")
class ExampleThinkNode(BaseNode):
    """示例思考节点"""
    
    def execute(self, state, config):
        """执行思考逻辑"""
        print(f"思考节点执行，当前迭代: {state.get('iteration_count', 0)}")
        
        # 更新消息
        from src.infrastructure.graph.states import LCAIMessage
        new_message = LCAIMessage(content=f"思考结果 {state.get('iteration_count', 0) + 1}")
        
        updated_messages = state.get("messages", []) + [new_message]
        
        return NodeExecutionResult(
            state={
                **state,
                "messages": updated_messages,
                "thought": f"这是第 {state.get('iteration_count', 0) + 1} 次思考"
            },
            next_node="example_act_node"
        )


@node("example_act_node")
class ExampleActNode(BaseNode):
    """示例行动节点"""
    
    def execute(self, state, config):
        """执行行动逻辑"""
        print(f"行动节点执行，当前迭代: {state.get('iteration_count', 0)}")
        
        # 更新状态
        return NodeExecutionResult(
            state={
                **state,
                "action": f"执行行动 {state.get('iteration_count', 0) + 1}"
            },
            next_node="example_observe_node"
        )


@node("example_observe_node")
class ExampleObserveNode(BaseNode):
    """示例观察节点"""
    
    def execute(self, state, config):
        """执行观察逻辑"""
        print(f"观察节点执行，当前迭代: {state.get('iteration_count', 0)}")
        
        # 更新状态
        return NodeExecutionResult(
            state={
                **state,
                "observation": f"观察结果 {state.get('iteration_count', 0) + 1}"
            },
            next_node="example_condition_node"  # 回到条件节点，完成一次循环
        )


@node("example_condition_node")
class ExampleConditionNode(BaseNode):
    """示例条件节点"""
    
    def execute(self, state, config):
        """执行条件判断"""
        # 这里简单地总是继续循环，实际使用中可以根据条件决定是否继续
        print(f"条件节点执行，检查是否继续迭代...")
        
        # 返回继续下一个节点
        return NodeExecutionResult(
            state=state,
            next_node="example_think_node"
        )


def create_example_workflow():
    """创建示例工作流配置"""
    config = GraphConfig(
        name="example_react_workflow",
        description="示例ReAct工作流，展示迭代管理功能",
        additional_config={
            "max_iterations": 5,              # 全局最大迭代5次
            "cycle_completer_node": "example_observe_node"  # observe_node完成一个循环
        }
    )
    
    # 添加节点
    config.nodes = {
        "example_think_node": NodeConfig(
            name="example_think_node",
            function_name="example_think_node",
            config={"max_iterations": 10}  # think_node最多执行10次
        ),
        "example_act_node": NodeConfig(
            name="example_act_node", 
            function_name="example_act_node",
            config={"max_iterations": 8}   # act_node最多执行8次
        ),
        "example_observe_node": NodeConfig(
            name="example_observe_node",
            function_name="example_observe_node", 
            config={}  # observe_node不受节点级限制，只受全局限制
        ),
        "example_condition_node": NodeConfig(
            name="example_condition_node",
            function_name="example_condition_node",
            config={}
        )
    }
    
    # 添加边
    config.edges = [
        EdgeConfig(
            from_node="example_think_node",
            to_node="example_act_node", 
            type=EdgeType.SIMPLE
        ),
        EdgeConfig(
            from_node="example_act_node",
            to_node="example_observe_node",
            type=EdgeType.SIMPLE
        ),
        EdgeConfig(
            from_node="example_observe_node", 
            to_node="example_condition_node",
            type=EdgeType.SIMPLE
        ),
        EdgeConfig(
            from_node="example_condition_node",
            to_node="example_think_node",
            type=EdgeType.SIMPLE
        )
    ]
    
    # 设置入口点
    config.entry_point = "example_think_node"
    
    return config


def run_example():
    """运行示例"""
    print("开始运行迭代管理器示例...")
    
    # 创建工作流配置
    config = create_example_workflow()
    
    # 使用迭代感知构建器创建图
    builder = IterationAwareGraphBuilder()
    graph = builder.build_graph(config)
    
    # 创建初始状态
    initial_state = create_workflow_state(
        workflow_id="example_workflow",
        workflow_name="Example Workflow",
        input_text="这是一个示例输入",
        max_iterations=5  # 工作流级别的最大迭代次数
    )
    
    print(f"初始状态: workflow_iteration_count={initial_state.get('workflow_iteration_count')}")
    print(f"初始状态: node_iterations={initial_state.get('node_iterations')}")
    
    # 注意：在实际使用中，您需要使用LangGraph的接口来执行图
    # 这里仅演示配置和初始化
    
    print("\n工作流配置完成，迭代管理器已集成:")
    print(f"- 全局最大迭代次数: {config.additional_config['max_iterations']}")
    print(f"- 循环完成节点: {config.additional_config['cycle_completer_node']}")
    print(f"- think_node最大迭代次数: {config.nodes['example_think_node'].config['max_iterations']}")
    print(f"- act_node最大迭代次数: {config.nodes['example_act_node'].config['max_iterations']}")
    
    print("\n迭代管理器功能:")
    print("- 自动记录每次迭代的详细信息")
    print("- 检查全局和节点级别的迭代限制")
    print("- 在达到限制时自动终止工作流")
    print("- 提供详细的迭代统计信息用于分析")


if __name__ == "__main__":
    run_example()