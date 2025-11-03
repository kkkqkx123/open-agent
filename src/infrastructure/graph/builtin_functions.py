"""内置函数定义

定义常用的内置节点函数和条件函数。
"""

from typing import Dict, Any, List, Optional, Callable, Union
import time
import logging

from .states import WorkflowState

logger = logging.getLogger(__name__)


# 内置节点函数
def llm_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """LLM节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取配置
    config = state_dict.get("config", {})
    system_prompt = config.get("system_prompt", "你是一个AI助手")
    max_tokens = config.get("max_tokens", 1000)
    temperature = config.get("temperature", 0.7)
    
    # 模拟LLM调用
    response = f"LLM响应 (系统提示: {system_prompt[:50]}..., 最大token: {max_tokens}, 温度: {temperature})"
    
    # 更新消息历史
    messages = state_dict.get("messages", [])
    messages.append({"role": "assistant", "content": response})
    
    return {
        **state_dict,
        "messages": messages,
        "last_response": response
    }


def tool_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """工具节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取工具调用
    tool_calls = state_dict.get("tool_calls", [])
    if not tool_calls:
        return state_dict
    
    # 模拟工具执行
    tool_results = []
    for tool_call in tool_calls:
        tool_name = tool_call.get("name", "unknown_tool")
        tool_args = tool_call.get("args", {})
        
        # 模拟工具结果
        result = f"工具 '{tool_name}' 执行结果: {tool_args}"
        tool_results.append({
            "tool_call": tool_call,
            "result": result,
            "timestamp": time.time()
        })
    
    # 更新工具结果
    existing_results = state_dict.get("tool_results", [])
    all_results = existing_results + tool_results
    
    return {
        **state_dict,
        "tool_results": all_results,
        "tool_calls": []  # 清空待处理的工具调用
    }


def analysis_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """分析节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取输入数据
    messages = state_dict.get("messages", [])
    tool_results = state_dict.get("tool_results", [])
    
    # 模拟分析过程
    analysis = "分析结果: "
    if messages:
        analysis += f"处理了 {len(messages)} 条消息"
    if tool_results:
        analysis += f", 执行了 {len(tool_results)} 个工具"
    
    return {
        **state_dict,
        "analysis": analysis,
        "analysis_timestamp": time.time()
    }


def condition_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """条件节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取条件配置
    config = state_dict.get("config", {})
    conditions = config.get("conditions", [])
    
    # 评估条件
    condition_results = []
    for condition in conditions:
        condition_type = condition.get("type", "unknown")
        condition_result = {
            "type": condition_type,
            "result": False,  # 默认为False
            "timestamp": time.time()
        }
        
        # 简单的条件评估逻辑
        if condition_type == "always_true":
            condition_result["result"] = True
        elif condition_type == "has_messages":
            condition_result["result"] = len(state_dict.get("messages", [])) > 0
        elif condition_type == "has_tool_results":
            condition_result["result"] = len(state_dict.get("tool_results", [])) > 0
        
        condition_results.append(condition_result)
    
    return {
        **state_dict,
        "condition_results": condition_results
    }


def wait_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """等待节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取等待配置
    config = state_dict.get("config", {})
    wait_duration = config.get("wait_duration", 1.0)
    
    # 模拟等待
    time.sleep(wait_duration)
    
    # 更新等待状态
    messages = state_dict.get("messages", [])
    messages.append({
        "role": "system",
        "content": f"等待了 {wait_duration} 秒"
    })
    
    return {
        **state_dict,
        "messages": messages,
        "is_waiting": False,
        "wait_end_time": time.time()
    }


def plan_execute_agent_node(state: Union[WorkflowState, Dict[str, Any]]) -> Dict[str, Any]:
    """Plan-Execute Agent节点函数

    Args:
        state: 工作流状态

    Returns:
        Dict[str, Any]: 更新后的状态
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 获取配置
    config = state_dict.get("config", {})
    max_steps = config.get("max_steps", 5)
    max_iterations = config.get("max_iterations", 10)
    
    # 获取上下文
    context = state_dict.get("context", {})
    current_plan = context.get("current_plan", [])
    current_step_index = context.get("current_step_index", 0)
    
    # 获取工作流状态
    workflow_iteration_count = state_dict.get("workflow_iteration_count", 0)
    workflow_messages = state_dict.get("workflow_messages", [])
    
    # 如果还没有计划，生成一个
    if not current_plan:
        new_plan = [
            "收集和分析相关信息",
            "制定详细的执行方案",
            "逐步执行计划中的每个步骤",
            "验证和调整执行结果",
            "总结最终成果"
        ]
        context["current_plan"] = new_plan
        context["current_step_index"] = 0
        context["plan_completed"] = False
        context["needs_review"] = True
        
        workflow_messages.append({
            "role": "assistant",
            "content": f"已生成计划: {new_plan}"
        })
        
        return {
            **state_dict,
            "context": context,
            "workflow_messages": workflow_messages
        }
    
    # 如果计划需要审查，标记审查完成
    if context.get("needs_review", False):
        context["needs_review"] = False
        workflow_messages.append({
            "role": "assistant",
            "content": "计划审查完成，开始执行"
        })
        
        return {
            **state_dict,
            "context": context,
            "workflow_messages": workflow_messages
        }
    
    # 执行当前步骤
    if current_step_index < len(current_plan):
        current_step = current_plan[current_step_index]
        context["current_step_index"] = current_step_index + 1
        
        # 检查是否完成所有步骤
        if context["current_step_index"] >= len(current_plan):
            context["plan_completed"] = True
        
        workflow_messages.append({
            "role": "assistant",
            "content": f"执行步骤 {current_step_index + 1}: {current_step}"
        })
        
        return {
            **state_dict,
            "context": context,
            "workflow_messages": workflow_messages
        }
    
    # 计划已完成
    workflow_messages.append({
        "role": "assistant",
        "content": "计划执行完成"
    })
    
    return {
        **state_dict,
        "context": context,
        "workflow_messages": workflow_messages
    }


# 内置条件函数
def has_tool_calls(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """条件：是否有工具调用

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    tool_calls = state_dict.get("tool_calls", [])
    
    return "tool_node" if tool_calls else "llm_node"


def needs_more_info(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """条件：是否需要更多信息

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    analysis = state_dict.get("analysis", "")
    
    return "analysis_node" if not analysis else "end"


def is_complete(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """条件：是否完成

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    complete = state_dict.get("complete", False)
    
    return "end" if complete else "continue"


def has_messages(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """条件：是否有消息

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    messages = state_dict.get("messages", [])
    
    return "process" if messages else "wait"


def has_errors(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """条件：是否有错误

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    errors = state_dict.get("errors", [])
    
    return "error_handler" if errors else "continue"


def plan_execute_router(state: Union[WorkflowState, Dict[str, Any]]) -> str:
    """Plan-Execute Agent路由函数

    Args:
        state: 工作流状态

    Returns:
        str: 下一个节点名称
    """
    state_dict: Dict[str, Any] = dict(state) if isinstance(state, dict) else dict(state.__dict__ if hasattr(state, '__dict__') else {})
    
    # 首先检查是否有错误
    if state_dict.get("workflow_errors"):
        return "error_handler"
    
    # 检查计划状态
    context = state_dict.get("context", {})
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


# 内置函数字典
BUILTIN_NODE_FUNCTIONS = {
    "llm_node": llm_node,
    "tool_node": tool_node,
    "analysis_node": analysis_node,
    "condition_node": condition_node,
    "wait_node": wait_node,
    "plan_execute_agent_node": plan_execute_agent_node,
}

BUILTIN_CONDITION_FUNCTIONS = {
    "has_tool_calls": has_tool_calls,
    "needs_more_info": needs_more_info,
    "is_complete": is_complete,
    "has_messages": has_messages,
    "has_errors": has_errors,
    "plan_execute_router": plan_execute_router,
}


def get_builtin_node_function(name: str) -> Optional[Callable]:
    """获取内置节点函数
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 节点函数
    """
    return BUILTIN_NODE_FUNCTIONS.get(name)


def get_builtin_condition_function(name: str) -> Optional[Callable]:
    """获取内置条件函数
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 条件函数
    """
    return BUILTIN_CONDITION_FUNCTIONS.get(name)


def list_builtin_node_functions() -> List[str]:
    """列出所有内置节点函数
    
    Returns:
        List[str]: 函数名称列表
    """
    return list(BUILTIN_NODE_FUNCTIONS.keys())


def list_builtin_condition_functions() -> List[str]:
    """列出所有内置条件函数
    
    Returns:
        List[str]: 函数名称列表
    """
    return list(BUILTIN_CONDITION_FUNCTIONS.keys())