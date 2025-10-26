"""Workflow状态定义

提供工作流执行过程中的状态管理。
"""

from typing import Dict, Any, List, Optional, Annotated, cast
import operator
from datetime import datetime
from typing_extensions import TypedDict

from .base import BaseMessage
from .agent import AgentState, create_agent_state


# 工作流状态类型定义
WorkflowState = Dict[str, Any]

# 类型注解
class _WorkflowState(TypedDict, total=False):
    """工作流状态类型注解

    扩展Agent状态，添加工作流特定的字段。
    """
    # 基础字段 (从BaseGraphState和AgentState继承)
    messages: Annotated[List[BaseMessage], operator.add]
    metadata: Dict[str, Any]
    execution_context: Dict[str, Any]
    current_step: str
    input: str
    output: Optional[str]
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]
    tool_results: Annotated[List[Dict[str, Any]], operator.add]
    iteration_count: Annotated[int, operator.add]
    max_iterations: int
    errors: Annotated[List[str], operator.add]
    complete: bool
    agent_id: str
    agent_config: Dict[str, Any]
    execution_result: Optional[Dict[str, Any]]

    # 工作流特定字段
    workflow_id: str
    workflow_name: str
    workflow_config: Dict[str, Any]

    # 当前执行信息
    current_graph: str

    # 分析和决策结果
    analysis: Optional[str]
    decision: Optional[str]
    
    # 上下文信息
    context: Dict[str, Any]
    
    # 工作流执行信息
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    
    # 多图状态管理
    graph_states: Dict[str, AgentState]
    
    # 自定义字段
    custom_fields: Dict[str, Any]


def create_workflow_state(
    workflow_id: str,
    workflow_name: str,
    input_text: str,
    workflow_config: Optional[Dict[str, Any]] = None,
    max_iterations: int = 10
) -> WorkflowState:
    """创建工作流状态
    
    Args:
        workflow_id: 工作流ID
        workflow_name: 工作流名称
        input_text: 输入文本
        workflow_config: 工作流配置
        max_iterations: 最大迭代次数
        
    Returns:
        WorkflowState实例
    """
    agent_state = create_agent_state(
        input_text=input_text,
        agent_id=workflow_id,  # 使用workflow_id作为默认agent_id
        max_iterations=max_iterations
    )
    
    return {
        **agent_state,
        "workflow_id": workflow_id,
        "workflow_name": workflow_name,
        "workflow_config": workflow_config or {},
        "current_graph": "",
        "current_step": "",
        "analysis": None,
        "decision": None,
        "context": {},
        "start_time": datetime.now(),
        "end_time": None,
        "graph_states": {},
        "custom_fields": {}
    }


def update_workflow_state_with_graph_state(
    state: WorkflowState,
    graph_id: str,
    graph_state: AgentState
) -> WorkflowState:
    """用图状态更新工作流状态
    
    Args:
        state: 当前工作流状态
        graph_id: 图ID
        graph_state: 图状态
        
    Returns:
        更新后的工作流状态
    """
    updated_graph_states = state.get("graph_states", {}).copy()
    updated_graph_states[graph_id] = graph_state
    
    return {
        **state,
        "current_graph": graph_id,
        "graph_states": updated_graph_states
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
    updated_context = state.get("context", {}).copy()
    updated_context[context_key] = context_value
    
    return {
        **state,
        "context": updated_context
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
    updated_custom_fields = state.get("custom_fields", {}).copy()
    updated_custom_fields[field_key] = field_value
    
    return {
        **state,
        "custom_fields": updated_custom_fields
    }


def complete_workflow(state: WorkflowState) -> WorkflowState:
    """完成工作流
    
    Args:
        state: 当前工作流状态
        
    Returns:
        完成的工作流状态
    """
    return {
        **state,
        "end_time": datetime.now(),
        "complete": True
    }


def get_workflow_duration(state: WorkflowState) -> Optional[float]:
    """获取工作流执行时长（秒）
    
    Args:
        state: 工作流状态
        
    Returns:
        执行时长（秒），如果未完成则返回None
    """
    start_time = cast(datetime, state.get("start_time"))
    end_time = cast(datetime, state.get("end_time"))

    if start_time and end_time:
        return (end_time - start_time).total_seconds()

    return None


def get_graph_state(state: WorkflowState, graph_id: str) -> Optional[AgentState]:
    """获取指定图的状态
    
    Args:
        state: 工作流状态
        graph_id: 图ID
        
    Returns:
        图状态，如果不存在则返回None
    """
    graph_states = cast(Dict[str, AgentState], state.get("graph_states", {}))
    return graph_states.get(graph_id)


def has_all_graphs_completed(state: WorkflowState, graph_ids: List[str]) -> bool:
    """检查所有指定的图是否已完成
    
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