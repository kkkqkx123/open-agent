"""ReAct状态定义

提供ReAct（Reasoning and Acting）模式的状态管理。
"""

from typing import Dict, Any, List, Annotated, Optional
import operator
from typing_extensions import TypedDict

from .workflow import WorkflowState, create_workflow_state


class ReActState(WorkflowState, total=False):
    """ReAct模式状态
    
    扩展工作流状态，添加ReAct特定的字段。
    """
    # ReAct特定的状态字段
    thought: Optional[str]
    action: Optional[str]
    observation: Optional[str]
    
    # 步骤跟踪
    steps: Annotated[List[Dict[str, Any]], operator.add]
    
    # ReAct配置
    max_steps: int
    current_step_index: int


def create_react_state(
    workflow_id: str,
    workflow_name: str,
    input_text: str,
    max_iterations: int = 10,
    max_steps: int = 10
) -> ReActState:
    """创建ReAct状态
    
    Args:
        workflow_id: 工作流ID
        workflow_name: 工作流名称
        input_text: 输入文本
        max_iterations: 最大迭代次数
        max_steps: 最大步骤数
        
    Returns:
        ReActState实例
    """
    workflow_state = create_workflow_state(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        input_text=input_text,
        max_iterations=max_iterations
    )
    
    return {
        **workflow_state,
        "thought": None,
        "action": None,
        "observation": None,
        "steps": [],
        "max_steps": max_steps,
        "current_step_index": 0
    }


def update_react_state_with_thought(
    state: ReActState,
    thought: str
) -> ReActState:
    """用思考更新ReAct状态
    
    Args:
        state: 当前ReAct状态
        thought: 思考内容
        
    Returns:
        更新后的ReAct状态
    """
    return {
        **state,
        "thought": thought
    }


def update_react_state_with_action(
    state: ReActState,
    action: str
) -> ReActState:
    """用动作更新ReAct状态
    
    Args:
        state: 当前ReAct状态
        action: 动作内容
        
    Returns:
        更新后的ReAct状态
    """
    return {
        **state,
        "action": action
    }


def update_react_state_with_observation(
    state: ReActState,
    observation: str
) -> ReActState:
    """用观察更新ReAct状态
    
    Args:
        state: 当前ReAct状态
        observation: 观察内容
        
    Returns:
        更新后的ReAct状态
    """
    return {
        **state,
        "observation": observation
    }


def add_react_step(
    state: ReActState,
    thought: Optional[str] = None,
    action: Optional[str] = None,
    observation: Optional[str] = None
) -> ReActState:
    """添加ReAct步骤
    
    Args:
        state: 当前ReAct状态
        thought: 思考内容
        action: 动作内容
        observation: 观察内容
        
    Returns:
        更新后的ReAct状态
    """
    current_step_index = state.get("current_step_index", 0)
    new_step_index = current_step_index + 1
    
    step = {
        "step_index": new_step_index,
        "thought": thought or state.get("thought"),
        "action": action or state.get("action"),
        "observation": observation or state.get("observation"),
        "timestamp": state.get("start_time")
    }
    
    updated_steps = state.get("steps", []) + [step]
    
    return {
        **state,
        "steps": updated_steps,
        "current_step_index": new_step_index,
        "thought": thought,
        "action": action,
        "observation": observation
    }


def get_current_react_step(state: ReActState) -> Optional[Dict[str, Any]]:
    """获取当前ReAct步骤
    
    Args:
        state: ReAct状态
        
    Returns:
        当前步骤，如果没有步骤则返回None
    """
    steps = state.get("steps", [])
    return steps[-1] if steps else None


def has_react_reached_max_steps(state: ReActState) -> bool:
    """检查ReAct是否达到最大步骤数
    
    Args:
        state: ReAct状态
        
    Returns:
        是否达到最大步骤数
    """
    current_step_index = state.get("current_step_index", 0)
    max_steps = state.get("max_steps", 10)
    
    return current_step_index >= max_steps


def is_react_cycle_complete(state: ReActState) -> bool:
    """检查ReAct循环是否完成
    
    Args:
        state: ReAct状态
        
    Returns:
        循环是否完成
    """
    return (
        state.get("thought") is not None and
        state.get("action") is not None and
        state.get("observation") is not None
    )


def reset_react_cycle(state: ReActState) -> ReActState:
    """重置ReAct循环，准备下一轮
    
    Args:
        state: 当前ReAct状态
        
    Returns:
        重置后的ReAct状态
    """
    return {
        **state,
        "thought": None,
        "action": None,
        "observation": None
    }


def get_react_summary(state: ReActState) -> str:
    """获取ReAct执行摘要
    
    Args:
        state: ReAct状态
        
    Returns:
        执行摘要字符串
    """
    steps = state.get("steps", [])
    if not steps:
        return "尚未执行任何步骤"
    
    summary_parts = [f"ReAct执行摘要 (共{len(steps)}步):"]
    
    for i, step in enumerate(steps, 1):
        summary_parts.append(f"\n步骤 {i}:")
        if step.get("thought"):
            summary_parts.append(f"  思考: {step['thought']}")
        if step.get("action"):
            summary_parts.append(f"  动作: {step['action']}")
        if step.get("observation"):
            summary_parts.append(f"  观察: {step['observation']}")
    
    return "\n".join(summary_parts)