"""PlanExecute状态定义

提供计划执行模式的状态管理。
"""

from typing import Dict, Any, List, Annotated, Optional, cast
import operator
from typing_extensions import TypedDict

from .base import LCBaseMessage
from .workflow import WorkflowState, create_workflow_state, create_plan_execute_state


# 计划执行状态类型定义
PlanExecuteState = Dict[str, Any]

# 类型注解
class _PlanExecuteState(TypedDict, total=False):
    """计划执行状态类型注解

    扩展工作流状态，添加计划执行特定的字段。
    """
    # 基础字段 (继承自WorkflowState)
    messages: Annotated[List[LCBaseMessage], operator.add]
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
    workflow_id: str
    workflow_name: str
    workflow_config: Dict[str, Any]
    current_graph: str
    analysis: Optional[str]
    decision: Optional[str]

    # 计划执行特定字段
    plan: Optional[str]
    steps: Annotated[List[str], operator.add]
    step_results: Annotated[List[Dict[str, Any]], operator.add]

    # 计划执行配置
    max_steps: int
    current_step_index: int
    
    # 执行状态
    plan_complete: bool
    execution_complete: bool


def create_plan_execute_state(
    workflow_id: str,
    workflow_name: str,
    input_text: str,
    max_iterations: int = 10,
    max_steps: int = 10
) -> PlanExecuteState:
    """创建计划执行状态
    
    Args:
        workflow_id: 工作流ID
        workflow_name: 工作流名称
        input_text: 输入文本
        max_iterations: 最大迭代次数
        max_steps: 最大步骤数
        
    Returns:
        PlanExecuteState实例
    """
    workflow_state = create_workflow_state(
        workflow_id=workflow_id,
        workflow_name=workflow_name,
        input_text=input_text,
        max_iterations=max_iterations
    )
    
    return {
        **workflow_state,
        "plan": None,
        "steps": [],
        "current_step": "",
        "step_results": [],
        "max_steps": max_steps,
        "current_step_index": 0,
        "plan_complete": False,
        "execution_complete": False
    }


def update_plan_execute_state_with_plan(
    state: PlanExecuteState,
    plan: str,
    steps: List[str]
) -> PlanExecuteState:
    """用计划更新计划执行状态
    
    Args:
        state: 当前计划执行状态
        plan: 计划内容
        steps: 计划步骤列表
        
    Returns:
        更新后的计划执行状态
    """
    return {
        **state,
        "plan": plan,
        "steps": steps,
        "plan_complete": True
    }


def update_plan_execute_state_with_current_step(
    state: PlanExecuteState,
    current_step: str
) -> PlanExecuteState:
    """用当前步骤更新计划执行状态
    
    Args:
        state: 当前计划执行状态
        current_step: 当前步骤
        
    Returns:
        更新后的计划执行状态
    """
    return {
        **state,
        "current_step": current_step
    }


def add_step_result(
    state: PlanExecuteState,
    step: str,
    result: Any,
    success: bool = True,
    error: Optional[str] = None
) -> PlanExecuteState:
    """添加步骤结果
    
    Args:
        state: 当前计划执行状态
        step: 步骤名称
        result: 执行结果
        success: 是否成功
        error: 错误信息
        
    Returns:
        更新后的计划执行状态
    """
    current_step_index = state.get("current_step_index", 0)
    new_step_index = current_step_index + 1
    
    step_result = {
        "step_index": new_step_index,
        "step": step,
        "result": result,
        "success": success,
        "error": error,
        "timestamp": state.get("start_time")
    }
    
    updated_step_results = state.get("step_results", []) + [step_result]
    
    # 检查是否所有步骤都已完成
    steps = state.get("steps", [])
    all_steps_complete = new_step_index >= len(steps)
    
    return {
        **state,
        "step_results": updated_step_results,
        "current_step_index": new_step_index,
        "execution_complete": all_steps_complete,
        "complete": all_steps_complete
    }


def get_next_step(state: PlanExecuteState) -> Optional[str]:
    """获取下一个要执行的步骤
    
    Args:
        state: 计划执行状态
        
    Returns:
        下一个步骤，如果没有则返回None
    """
    steps = cast(List[str], state.get("steps", []))
    current_step_index = cast(int, state.get("current_step_index", 0))

    if current_step_index < len(steps):
        return steps[current_step_index]

    return None


def get_current_step_info(state: PlanExecuteState) -> Optional[Dict[str, Any]]:
    """获取当前步骤信息
    
    Args:
        state: 计划执行状态
        
    Returns:
        当前步骤信息，如果没有则返回None
    """
    step_results = state.get("step_results", [])
    return step_results[-1] if step_results else None


def has_plan_execute_reached_max_steps(state: PlanExecuteState) -> bool:
    """检查计划执行是否达到最大步骤数
    
    Args:
        state: 计划执行状态
        
    Returns:
        是否达到最大步骤数
    """
    current_step_index = cast(int, state.get("current_step_index", 0))
    max_steps = cast(int, state.get("max_steps", 10))

    return current_step_index >= max_steps


def is_plan_complete(state: PlanExecuteState) -> bool:
    """检查计划是否完成
    
    Args:
        state: 计划执行状态
        
    Returns:
        计划是否完成
    """
    return cast(bool, state.get("plan_complete", False))


def is_execution_complete(state: PlanExecuteState) -> bool:
    """检查执行是否完成
    
    Args:
        state: 计划执行状态
        
    Returns:
        执行是否完成
    """
    return cast(bool, state.get("execution_complete", False))


def get_plan_execute_progress(state: PlanExecuteState) -> Dict[str, Any]:
    """获取计划执行进度
    
    Args:
        state: 计划执行状态
        
    Returns:
        进度信息
    """
    steps = state.get("steps", [])
    current_step_index = state.get("current_step_index", 0)
    step_results = state.get("step_results", [])
    
    total_steps = len(steps)
    completed_steps = len(step_results)
    progress_percentage = (completed_steps / total_steps * 100) if total_steps > 0 else 0
    
    return {
        "total_steps": total_steps,
        "completed_steps": completed_steps,
        "current_step_index": current_step_index,
        "progress_percentage": progress_percentage,
        "next_step": get_next_step(state),
        "is_complete": is_execution_complete(state)
    }


def get_plan_execute_summary(state: PlanExecuteState) -> str:
    """获取计划执行摘要
    
    Args:
        state: 计划执行状态
        
    Returns:
        执行摘要字符串
    """
    plan = state.get("plan", "无计划")
    steps = state.get("steps", [])
    step_results = state.get("step_results", [])
    
    summary_parts = [
        f"计划执行摘要:",
        f"计划: {plan}",
        f"总步骤数: {len(steps)}",
        f"已完成步骤: {len(step_results)}"
    ]
    
    if step_results:
        summary_parts.append("\n执行结果:")
        for i, result in enumerate(step_results, 1):
            status = "✓" if result.get("success", False) else "✗"
            summary_parts.append(
                f"  {i}. {result.get('step', '未知步骤')} {status}"
            )
            if result.get("error"):
                summary_parts.append(f"     错误: {result['error']}")
    
    progress = get_plan_execute_progress(state)
    summary_parts.append(f"\n进度: {progress['progress_percentage']:.1f}%")
    
    return "\n".join(summary_parts)