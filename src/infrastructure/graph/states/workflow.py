"""工作流状态定义

提供工作流执行过程中的状态管理。
"""

from typing import Any, List, Annotated, Optional, cast, Union
import operator
from datetime import datetime
from typing_extensions import TypedDict

from .base import BaseMessage, LCBaseMessage
# AgentState已移除，统一使用WorkflowState

def create_agent_state(
    input_text: str,
    max_iterations: int = 10,
    messages: Optional[List[LCBaseMessage]] = None
) -> WorkflowState:
    """创建Agent状态
    
    Args:
        input_text: 输入文本
        max_iterations: 最大迭代次数
        messages: 初始消息列表
        
    Returns:
        WorkflowState实例
    """
    if messages is None:
        from .base import LCHumanMessage
        messages = [LCHumanMessage(content=input_text)]
    
    return {
        "messages": messages,
        "input": input_text,
        "output": None,
        "tool_calls": [],
        "tool_results": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "errors": [],
        "complete": False,
        "metadata": {},
        "execution_context": {},
        "current_step": "start",
        "agent_id": "",
        "agent_config": {},
        "execution_result": None,
        "workflow_id": "",
        "workflow_name": "",
        "workflow_config": {},
        "current_graph": "",
        "analysis": None,
        "decision": None,
        "context": {},
        "start_time": None,
        "end_time": None,
        "graph_states": {},
        "custom_fields": {}
    }


# 工作流状态类型定义
WorkflowState = dict[str, Any]

# 类型注解
class _WorkflowState(TypedDict, total=False):
    """工作流状态类型注解

    统一状态模型，包含工作流特定的字段。
    """
    # 基础字段
    messages: Annotated[List[LCBaseMessage], operator.add]
    metadata: dict[str, Any]
    execution_context: dict[str, Any]
    current_step: str
    input: str
    output: Optional[str]

    # 工具相关状态
    tool_calls: Annotated[List[dict[str, Any]], operator.add]
    tool_results: Annotated[List[dict[str, Any]], operator.add]

    # 迭代控制
    iteration_count: Annotated[int, operator.add]
    max_iterations: int

    # 错误处理
    errors: Annotated[List[str], operator.add]

    # 完成标志
    complete: bool

    # Agent配置
    agent_id: str
    agent_config: dict[str, Any]
    
    # 执行结果
    execution_result: Optional[dict[str, Any]]

    # 工作流特定的状态字段
    workflow_id: str
    workflow_name: str
    workflow_config: dict[str, Any]
    
    # 工作流执行信息
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    
    # 多图状态管理
    graph_states: dict[str, dict[str, Any]]
    
    # 自定义字段
    custom_fields: dict[str, Any]


def create_workflow_state(
workflow_id: str,
workflow_name: str,
input_text: str,
workflow_config: Optional[dict[str, Any]] = None,
max_iterations: int = 10,
messages: Optional[List[Union[BaseMessage, LCBaseMessage]]] = None
) -> WorkflowState:
    """创建工作流状态
    
    Args:
        workflow_id: 工作流ID
        workflow_name: 工作流名称
        input_text: 输入文本
        workflow_config: 工作流配置
        max_iterations: 最大迭代次数
        messages: 初始消息列表
        
    Returns:
        WorkflowState实例
    """
    if messages is None:
        from .base import LCHumanMessage
        messages = [LCHumanMessage(content=input_text)]
    
    # 创建基础状态
    base_state = {
        "messages": messages,
        "metadata": {},
        "execution_context": {},
        "current_step": "start"
    }
    
    return {
        **base_state,
        "input": input_text,
        "output": None,
        "tool_calls": [],
        "tool_results": [],
        "iteration_count": 0,
        "max_iterations": max_iterations,
        "errors": [],
        "complete": False,
        "agent_id": workflow_id,
        "agent_config": workflow_config or {},
        "execution_result": None,
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "workflow_config": workflow_config or {},
        "current_graph": "",
        "analysis": None,
        "decision": None,
        "context": {},
        "start_time": datetime.now(),
        "end_time": None,
        "graph_states": {},
        "custom_fields": {}
    }


def update_workflow_state_with_tool_call(
state: WorkflowState,
tool_call: dict[str, Any]
) -> WorkflowState:
    """用工具调用更新工作流状态
    
    Args:
        state: 当前工作流状态
        tool_call: 工具调用信息
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "tool_calls": state.get("tool_calls", []) + [tool_call]
    }


def update_workflow_state_with_tool_result(
state: WorkflowState,
tool_result: dict[str, Any]
) -> WorkflowState:
    """用工具结果更新工作流状态
    
    Args:
        state: 当前工作流状态
        tool_result: 工具执行结果
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "tool_results": state.get("tool_results", []) + [tool_result]
    }

def update_workflow_state_with_output(
    state: WorkflowState,
    output: str
) -> WorkflowState:
    """用输出更新工作流状态
    
    Args:
        state: 当前工作流状态
        output: 输出内容
        
    Returns:
        更新后的工作流状态
    """
    from .base import LCAIMessage
    
    # 获取当前消息列表
    current_messages = state.get("messages", [])
    
    # 创建新的AI消息
    new_ai_message = LCAIMessage(content=output)
    
    # 添加新消息到列表
    new_messages = current_messages + [new_ai_message]
    
    return {
        **state,
        "output": output,
        "messages": new_messages,
        "complete": True
    }


def update_workflow_state_with_error(
    state: WorkflowState,
    error: str
) -> WorkflowState:
    """用错误更新工作流状态
    
    Args:
        state: 当前工作流状态
        error: 错误信息
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "errors": state.get("errors", []) + [error]
    }


def increment_workflow_iteration(state: WorkflowState) -> WorkflowState:
    """增加工作流迭代次数
    
    Args:
        state: 当前工作流状态
        
    Returns:
        更新后的工作流状态
    """
    current_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    
    new_count = current_count + 1
    is_complete = new_count >= max_iterations
    
    return {
        **state,
        "iteration_count": new_count,
        "complete": is_complete
    }


def is_workflow_complete(state: WorkflowState) -> bool:
    """检查工作流是否完成
    
    Args:
        state: 工作流状态
        
    Returns:
        是否完成
    """
    return cast(bool, state.get("complete", False))


def has_workflow_reached_max_iterations(state: WorkflowState) -> bool:
    """检查工作流是否达到最大迭代次数
    
    Args:
        state: 工作流状态
        
    Returns:
        是否达到最大迭代次数
    """
    current_count = cast(int, state.get("iteration_count", 0))
    max_iterations = cast(int, state.get("max_iterations", 10))

    return current_count >= max_iterations


def add_graph_state(state: WorkflowState, graph_id: str, graph_state: dict[str, Any]) -> WorkflowState:
    """添加图状态到工作流状态
    
    Args:
        state: 工作流状态
        graph_id: 图ID
        graph_state: 图状态
        
    Returns:
        更新后的工作流状态
    """
    graph_states = state.get("graph_states", {})
    graph_states[graph_id] = graph_state
    
    return {
        **state,
        "graph_states": graph_states
    }


def get_graph_state(state: WorkflowState, graph_id: str) -> Optional[dict[str, Any]]:
    """获取指定图的状态
    
    Args:
        state: 工作流状态
        graph_id: 图ID
        
    Returns:
        图状态或None
    """
    graph_states = cast(dict[str, dict[str, Any]], state.get("graph_states", {}))
    return graph_states.get(graph_id)


def update_graph_state(state: WorkflowState, graph_id: str, graph_state: dict[str, Any]) -> WorkflowState:
    """更新指定图的状态
    
    Args:
        state: 工作流状态
        graph_id: 图ID
        graph_state: 图状态
        
    Returns:
        更新后的工作流状态
    """
    graph_states = state.get("graph_states", {})
    graph_states[graph_id] = graph_state
    
    return {
        **state,
        "graph_states": graph_states
    }


def update_workflow_state_with_analysis(
    state: WorkflowState,
    analysis: str
) -> WorkflowState:
    """用分析结果更新工作流状态
    
    Args:
        state: 当前工作流状态
        analysis: 分析结果
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "analysis": analysis
    }


def update_workflow_state_with_decision(
    state: WorkflowState,
    decision: str
) -> WorkflowState:
    """用决策结果更新工作流状态
    
    Args:
        state: 当前工作流状态
        decision: 决策结果
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "decision": decision
    }


def update_workflow_state_with_context(
    state: WorkflowState,
    context_key: str,
    context_value: Any
) -> WorkflowState:
    """用上下文信息更新工作流状态
    
    Args:
        state: 当前工作流状态
        context_key: 上下文键
        context_value: 上下文值
        
    Returns:
        更新后的工作流状态
    """
    context = state.get("context", {})
    context[context_key] = context_value
    
    return {
        **state,
        "context": context
    }


def update_workflow_state_with_custom_field(
    state: WorkflowState,
    field_key: str,
    field_value: Any
) -> WorkflowState:
    """用自定义字段更新工作流状态
    
    Args:
        state: 当前工作流状态
        field_key: 字段键
        field_value: 字段值
        
    Returns:
        更新后的工作流状态
    """
    custom_fields = state.get("custom_fields", {})
    custom_fields[field_key] = field_value
    
    return {
        **state,
        "custom_fields": custom_fields
    }


def complete_workflow(state: WorkflowState) -> WorkflowState:
    """完成工作流
    
    Args:
        state: 当前工作流状态
        
    Returns:
        更新后的工作流状态
    """
    return {
        **state,
        "end_time": datetime.now(),
        "complete": True
    }


def get_workflow_duration(state: WorkflowState) -> Optional[float]:
    """获取工作流执行时长
    
    Args:
        state: 工作流状态
        
    Returns:
        执行时长（秒）或None
    """
    start_time = state.get("start_time")
    end_time = state.get("end_time")
    
    if start_time and end_time:
        return (end_time - start_time).total_seconds()
    return None


def has_all_graphs_completed(state: WorkflowState, graph_ids: List[str]) -> bool:
    """检查所有图是否完成
    
    Args:
        state: 工作流状态
        graph_ids: 图ID列表
        
    Returns:
        是否所有图都已完成
    """
    graph_states = state.get("graph_states", {})
    
    for graph_id in graph_ids:
        graph_state = graph_states.get(graph_id)
        if not graph_state or not graph_state.get("complete", False):
            return False
    
    return True


# 状态更新函数 - 从旧的state.py迁移
def update_state_with_message(state: dict[str, Any], message: LCBaseMessage) -> dict[str, Any]:
    """用消息更新状态
    
    Args:
        state: 当前状态
        message: 新消息
        
    Returns:
        更新后的状态
    """
    return {"messages": [message]}


def update_state_with_tool_result(
state: dict[str, Any],
tool_call: dict[str, Any],
result: Any
) -> dict[str, Any]:
    """用工具结果更新状态
    
    Args:
        state: 当前状态
        tool_call: 工具调用信息
        result: 工具执行结果
        
    Returns:
        更新后的状态
    """
    return {
        "tool_results": [{"tool_call": tool_call, "result": result}]
    }


def update_state_with_error(state: dict[str, Any], error: str) -> dict[str, Any]:
    """用错误信息更新状态
    
    Args:
        state: 当前状态
        error: 错误信息
        
    Returns:
        更新后的状态
    """
    return {"errors": [error]}


# 状态验证函数 - 从旧的state.py迁移
def validate_state(state: dict[str, Any], state_type: type) -> List[str]:
    """验证状态
    
    Args:
        state: 要验证的状态
        state_type: 状态类型
        
    Returns:
        验证错误列表
    """
    errors = []
    
    # 检查必需字段
    if "messages" not in state:
        errors.append("缺少messages字段")
    
    if state_type == WorkflowState:
        required_fields = ["workflow_id", "input", "max_iterations"]
        for field in required_fields:
            if field not in state:
                errors.append(f"缺少必需字段: {field}")
    
    return errors


# 状态序列化函数 - 从旧的state.py迁移
def serialize_state(state: dict[str, Any]) -> dict[str, Any]:
    """序列化状态
    
    Args:
        state: 要序列化的状态
        
    Returns:
        序列化后的状态
    """
    serialized = state.copy()
    
    # 序列化消息
    if "messages" in serialized and serialized["messages"]:
        from .base import LCBaseMessage
        serialized["messages"] = [
            {
                "content": msg.content,
                "type": getattr(msg, 'type', getattr(msg, '__class__', type(msg)).__name__.lower()),
                "tool_call_id": getattr(msg, "tool_call_id", "")
            }
            for msg in serialized["messages"]
        ]
    
    return serialized


def deserialize_state(serialized_state: dict[str, Any]) -> dict[str, Any]:
    """反序列化状态
    
    Args:
        serialized_state: 序列化的状态
        
    Returns:
        反序列化后的状态
    """
    state = serialized_state.copy()
    
    # 反序列化消息
    if "messages" in state:
        messages = []
        for msg_data in state["messages"]:
            from .base import create_message
            message = create_message(
                content=msg_data["content"],
                role=msg_data["type"],
                tool_call_id=msg_data.get("tool_call_id", "")
            )
            messages.append(message)
        state["messages"] = messages
    
    return state


def create_react_state(
workflow_id: str,
input_text: str,
max_iterations: int = 10
) -> dict[str, Any]:
    """创建ReAct状态
    
    Args:
        workflow_id: 工作流ID
        input_text: 输入文本
        max_iterations: 最大迭代次数
        
    Returns:
        ReActState实例
    """
    base_workflow_state = create_workflow_state(workflow_id, f"react_{workflow_id}", input_text, max_iterations=max_iterations)
    
    # 创建完整的ReAct状态
    react_state = {
        **base_workflow_state,
        "thought": None,
        "action": None,
        "observation": None,
        "steps": []
    }
    return react_state


def create_plan_execute_state(
workflow_id: str,
input_text: str,
max_iterations: int = 10
) -> dict[str, Any]:
    """创建计划执行状态
    
    Args:
        workflow_id: 工作流ID
        input_text: 输入文本
        max_iterations: 最大迭代次数
        
    Returns:
        PlanExecuteState实例
    """
    base_workflow_state = create_workflow_state(workflow_id, f"plan_execute_{workflow_id}", input_text, max_iterations=max_iterations)
    
    # 创建完整的计划执行状态
    plan_execute_state = {
        **base_workflow_state,
        "plan": None,
        "steps": [],
        "current_step": None,
        "step_results": []
    }
    return plan_execute_state


def create_message(content: str, role: str, **kwargs: Any) -> "LCBaseMessage":
    """创建消息
    
    Args:
        content: 消息内容
        role: 消息角色
        **kwargs: 其他参数
        
    Returns:
        LangChain BaseMessage实例
    """
    from .base import MessageRole, LCHumanMessage, LCAIMessage, LCSystemMessage, LCToolMessage, LCBaseMessage
    if role == MessageRole.HUMAN:
        return LCHumanMessage(content=content)
    elif role == MessageRole.AI:
        return LCAIMessage(content=content)
    elif role == MessageRole.SYSTEM:
        return LCSystemMessage(content=content)
    elif role == MessageRole.TOOL:
        return LCToolMessage(content=content, tool_call_id=kwargs.get("tool_call_id", ""))
    else:
        return LCBaseMessage(content=content, type=role)