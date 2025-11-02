"""LangGraph状态定义

提供符合LangGraph最佳实践的状态定义和管理。
"""

from typing import Any, List, Optional, Annotated
import operator
import logging
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

# 导入消息类型 - 项目依赖LangChain，因此直接导入
from langchain_core.messages import BaseMessage as LCBaseMessage, HumanMessage as LCHumanMessage, AIMessage as LCAIMessage, SystemMessage as LCSystemMessage, ToolMessage as LCToolMessage  # type: ignore

# 重新定义消息类型，以避免与langchain_core冲突
class BaseMessage:
    def __init__(self, content: str, type: str = "base"):
        self.content = content
        self.type = type

class HumanMessage(BaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "human")

class AIMessage(BaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "ai")

class SystemMessage(BaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "system")

class ToolMessage(BaseMessage):
    def __init__(self, content: str, tool_call_id: str = ""):
        super().__init__(content, "tool")
        self.tool_call_id = tool_call_id

# 保留自定义消息类型定义，用于兼容性（使用不同名称避免冲突）
class GraphBaseMessage:
    def __init__(self, content: str, type: str = "base"):
        self.content = content
        self.type = type

class GraphHumanMessage(GraphBaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "human")

class GraphAIMessage(GraphBaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "ai")

class GraphSystemMessage(GraphBaseMessage):
    def __init__(self, content: str):
        super().__init__(content, "system")

class GraphToolMessage(GraphBaseMessage):
    def __init__(self, content: str, tool_call_id: str = ""):
        super().__init__(content, "tool")
        self.tool_call_id = tool_call_id


class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"


# 基础状态定义 - 符合LangGraph TypedDict模式
class BaseGraphState(TypedDict, total=False):
    """基础图状态"""
    # 使用reducer确保消息列表是追加而不是覆盖
    messages: Annotated[List[LCBaseMessage], operator.add]

    # 可选字段
    metadata: dict[str, Any]


# AgentState已移除，统一使用WorkflowState

class WorkflowState(BaseGraphState, total=False):
    """工作流状态 - 统一状态模型"""
    # Agent特定的状态字段 (从AgentState合并)
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

    # 额外字段
    start_time: Optional[str]
    current_step: Optional[str]
    workflow_name: Optional[str]

    # 新增业务字段以匹配域状态
    context: dict[str, Any]
    task_history: List[dict[str, Any]]
    execution_metrics: dict[str, Any]
    logs: List[dict[str, Any]]
    custom_fields: dict[str, Any]

    # 时间信息
    last_update_time: Optional[str]

    # Agent配置扩展
    agent_config: dict[str, Any]  # 包含agent_type等配置

    # 工作流特定字段
    workflow_id: str
    step_name: Optional[str]

    # 分析结果
    analysis: Optional[str]

    # 决策结果
    decision: Optional[str]

    # 条件结果
    condition_result: Optional[bool]


class ReActState(WorkflowState, total=False):
    """ReAct模式状态"""
    # ReAct特定的状态字段
    thought: Optional[str]
    action: Optional[str]
    observation: Optional[str]

    # 步骤跟踪
    steps: Annotated[List[dict[str, Any]], operator.add]


class PlanExecuteState(WorkflowState, total=False):
    """计划执行状态"""
    # 计划执行特定字段
    plan: Optional[str]
    steps: Annotated[List[str], operator.add]
    plan_current_step: Optional[str]  # 重命名避免与父类冲突
    step_results: Annotated[List[dict[str, Any]], operator.add]


# 状态工厂函数
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
        "metadata": {}
    }


def create_workflow_state(
    workflow_id: str,
    input_text: str,
    max_iterations: int = 10
) -> WorkflowState:
    """创建工作流状态

    Args:
        workflow_id: 工作流ID
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        WorkflowState实例
    """
    base_agent_state = create_agent_state(input_text, max_iterations)
    
    # 创建完整的工作流状态
    workflow_state: WorkflowState = {
    **base_agent_state,
    "workflow_id": workflow_id,
    "step_name": None,
    "analysis": None,
    "decision": None,
    "condition_result": None,
        "context": {}
    }
    return workflow_state


def create_react_state(
    workflow_id: str,
    input_text: str,
    max_iterations: int = 10
) -> ReActState:
    """创建ReAct状态

    Args:
        workflow_id: 工作流ID
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        ReActState实例
    """
    base_workflow_state = create_workflow_state(workflow_id, input_text, max_iterations)
    
    # 创建完整的ReAct状态
    react_state: ReActState = {
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
) -> PlanExecuteState:
    """创建计划执行状态

    Args:
        workflow_id: 工作流ID
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        PlanExecuteState实例
    """
    base_workflow_state = create_workflow_state(workflow_id, input_text, max_iterations)
    
    # 创建完整的计划执行状态
    plan_execute_state: PlanExecuteState = {
        **base_workflow_state,
        "plan": None,
        "steps": [],
        "current_step": None,
        "step_results": []
    }
    return plan_execute_state


# 消息创建函数
def create_message(content: str, role: str, **kwargs: Any) -> "LCBaseMessage":
    """创建消息
    
    Args:
        content: 消息内容
        role: 消息角色
        **kwargs: 其他参数
        
    Returns:
        LangChain BaseMessage实例
    """
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


# 状态更新函数
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


# 状态验证函数
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


# 状态序列化函数
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
            message = create_message(
                content=msg_data["content"],
                role=msg_data["type"],
                tool_call_id=msg_data.get("tool_call_id", "")
            )
            messages.append(message)
        state["messages"] = messages
    
    return state


# 向后兼容的别名 - AgentState已移除，统一使用WorkflowState
# AgentState = WorkflowState  # 已移除