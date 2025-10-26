"""Agent状态定义

提供Agent执行过程中的状态管理。
"""

from typing import Dict, Any, List, Annotated, Optional
import operator
from typing_extensions import TypedDict

from .base import BaseGraphState, create_base_state, create_message


class AgentState(BaseGraphState, total=False):
    """Agent状态
    
    扩展基础状态，添加Agent特定的字段。
    """
    # Agent特定的状态字段
    input: str
    output: Optional[str]
    
    # 工具相关状态
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]
    tool_results: Annotated[List[Dict[str, Any]], operator.add]
    
    # 迭代控制
    iteration_count: Annotated[int, operator.add]
    max_iterations: int
    
    # 错误处理
    errors: Annotated[List[str], operator.add]
    
    # 完成标志
    complete: bool
    
    # Agent配置
    agent_id: str
    agent_config: Dict[str, Any]
    
    # 执行结果
    execution_result: Optional[Dict[str, Any]]


def create_agent_state(
    input_text: str,
    agent_id: str,
    agent_config: Optional[Dict[str, Any]] = None,
    max_iterations: int = 10,
    messages: Optional[List] = None
) -> AgentState:
    """创建Agent状态
    
    Args:
        input_text: 输入文本
        agent_id: Agent ID
        agent_config: Agent配置
        max_iterations: 最大迭代次数
        messages: 初始消息列表
        
    Returns:
        AgentState实例
    """
    if messages is None:
        from .base import HumanMessage
        messages = [HumanMessage(content=input_text)]
    
    base_state = create_base_state(messages=messages)
    
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
        "agent_id": agent_id,
        "agent_config": agent_config or {},
        "execution_result": None
    }


def update_agent_state_with_tool_call(
    state: AgentState,
    tool_call: Dict[str, Any]
) -> AgentState:
    """用工具调用更新Agent状态
    
    Args:
        state: 当前Agent状态
        tool_call: 工具调用信息
        
    Returns:
        更新后的Agent状态
    """
    return {
        **state,
        "tool_calls": state.get("tool_calls", []) + [tool_call]
    }


def update_agent_state_with_tool_result(
    state: AgentState,
    tool_result: Dict[str, Any]
) -> AgentState:
    """用工具结果更新Agent状态
    
    Args:
        state: 当前Agent状态
        tool_result: 工具执行结果
        
    Returns:
        更新后的Agent状态
    """
    return {
        **state,
        "tool_results": state.get("tool_results", []) + [tool_result]
    }


def update_agent_state_with_output(
    state: AgentState,
    output: str
) -> AgentState:
    """用输出更新Agent状态
    
    Args:
        state: 当前Agent状态
        output: 输出内容
        
    Returns:
        更新后的Agent状态
    """
    from .base import AIMessage
    
    new_messages = state.get("messages", []) + [AIMessage(content=output)]
    
    return {
        **state,
        "output": output,
        "messages": new_messages,
        "complete": True
    }


def update_agent_state_with_error(
    state: AgentState,
    error: str
) -> AgentState:
    """用错误更新Agent状态
    
    Args:
        state: 当前Agent状态
        error: 错误信息
        
    Returns:
        更新后的Agent状态
    """
    return {
        **state,
        "errors": state.get("errors", []) + [error]
    }


def increment_agent_iteration(state: AgentState) -> AgentState:
    """增加Agent迭代次数
    
    Args:
        state: 当前Agent状态
        
    Returns:
        更新后的Agent状态
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


def is_agent_complete(state: AgentState) -> bool:
    """检查Agent是否完成
    
    Args:
        state: Agent状态
        
    Returns:
        是否完成
    """
    return state.get("complete", False)


def has_agent_reached_max_iterations(state: AgentState) -> bool:
    """检查Agent是否达到最大迭代次数
    
    Args:
        state: Agent状态
        
    Returns:
        是否达到最大迭代次数
    """
    current_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 10)
    
    return current_count >= max_iterations