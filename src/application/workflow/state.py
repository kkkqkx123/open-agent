"""工作流状态定义

定义工作流中使用的各种状态类型和数据结构。
"""

from typing import Dict, Any, List, Optional, Annotated, Union, TYPE_CHECKING, cast
from dataclasses import dataclass
import operator
import logging
from datetime import datetime
from typing_extensions import TypedDict

logger = logging.getLogger(__name__)

# 导入消息类型
if TYPE_CHECKING:
    from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
else:
    try:
        from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
        LANGCHAIN_AVAILABLE = True
    except ImportError:
        logger.warning("LangChain not available, using fallback message types")
        LANGCHAIN_AVAILABLE = False

        # 后备消息类型定义
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


class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"


class ToolResult:
    """工具执行结果"""
    def __init__(self, tool_name: str, success: bool, output: Any = None, error: Optional[str] = None):
        self.tool_name = tool_name
        self.success = success
        self.output = output
        self.error = error


class WorkflowStatus:
    """工作流状态枚举"""
    NOT_STARTED = "not_started"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BaseWorkflowState(TypedDict):
    """基础工作流状态"""
    # 使用reducer确保消息列表是追加而不是覆盖
    messages: Annotated[List[BaseMessage], operator.add]
    
    # 可选字段
    metadata: Dict[str, Any]


class AgentState(BaseWorkflowState):
    """Agent状态 - 扩展基础状态"""
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


class WorkflowState(AgentState):
    """工作流状态 - 扩展Agent状态"""
    # 工作流特定字段
    workflow_name: str
    current_step: Optional[str]
    
    # 分析结果
    analysis: Optional[str]
    
    # 决策结果
    decision: Optional[str]
    
    # 上下文信息
    context: Dict[str, Any]
    
    # 工作流执行信息
    start_time: Optional[datetime]
    max_iterations: int
    iteration_count: int
    workflow_id: Optional[str]
    errors: List[str]
    custom_fields: Dict[str, Any]


class ReActState(WorkflowState):
    """ReAct模式状态"""
    # ReAct特定的状态字段
    thought: Optional[str]
    action: Optional[str]
    observation: Optional[str]
    
    # 步骤跟踪
    steps: Annotated[List[Dict[str, Any]], operator.add]


class PlanExecuteState(WorkflowState):
    """计划执行状态"""
    # 计划执行特定字段
    plan: Optional[str]
    steps: Annotated[List[str], operator.add]
    current_step: Optional[str]
    step_results: Annotated[List[Dict[str, Any]], operator.add]


# 状态工厂函数
def create_agent_state(
    input_text: str,
    max_iterations: int = 10,
    messages: Optional[List[BaseMessage]] = None
) -> AgentState:
    """创建Agent状态
    
    Args:
        input_text: 输入文本
        max_iterations: 最大迭代次数
        messages: 初始消息列表
        
    Returns:
        AgentState实例
    """
    if messages is None:
        messages = [HumanMessage(content=input_text)]
    
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
    workflow_name: str,
    input_text: str,
    max_iterations: int = 10
) -> WorkflowState:
    """创建工作流状态

    Args:
        workflow_name: 工作流名称
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        WorkflowState实例
    """
    base_state = create_agent_state(input_text, max_iterations)
    return cast(WorkflowState, {
        **base_state,
        "workflow_name": workflow_name,
        "current_step": None,
        "analysis": None,
        "decision": None,
        "context": {},
        "start_time": datetime.now(),
        "workflow_id": None,
    "custom_fields": {}
    })


def create_react_state(
    workflow_name: str,
    input_text: str,
    max_iterations: int = 10
) -> ReActState:
    """创建ReAct状态

    Args:
        workflow_name: 工作流名称
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        ReActState实例
    """
    base_state = create_workflow_state(workflow_name, input_text, max_iterations)
    return cast(ReActState, {
        **base_state,
        "thought": None,
        "action": None,
        "observation": None,
    "steps": []
    })


def create_plan_execute_state(
    workflow_name: str,
    input_text: str,
    max_iterations: int = 10
) -> PlanExecuteState:
    """创建计划执行状态

    Args:
        workflow_name: 工作流名称
        input_text: 输入文本
        max_iterations: 最大迭代次数

    Returns:
        PlanExecuteState实例
    """
    base_state = create_workflow_state(workflow_name, input_text, max_iterations)
    return cast(PlanExecuteState, {
        **base_state,
        "plan": None,
        "steps": [],
        "current_step": None,
    "step_results": []
    })


# 消息创建函数
def create_message(content: str, role: str, **kwargs) -> BaseMessage:
    """创建消息
    
    Args:
        content: 消息内容
        role: 消息角色
        **kwargs: 其他参数
        
    Returns:
        BaseMessage实例
    """
    if role == MessageRole.HUMAN:
        return HumanMessage(content=content)
    elif role == MessageRole.AI:
        return AIMessage(content=content)
    elif role == MessageRole.SYSTEM:
        return SystemMessage(content=content)
    elif role == MessageRole.TOOL:
        return ToolMessage(content=content, tool_call_id=kwargs.get("tool_call_id", ""))
    else:
        return BaseMessage(content=content, type=role)


def adapt_langchain_message(message) -> BaseMessage:
    """适配LangChain消息到内部消息格式
    
    Args:
        message: LangChain消息对象
        
    Returns:
        BaseMessage实例
    """
    if hasattr(message, 'content') and hasattr(message, 'type'):
        if message.type == 'human':
            return HumanMessage(content=message.content)
        elif message.type == 'ai':
            return AIMessage(content=message.content)
        elif message.type == 'system':
            return SystemMessage(content=message.content)
        elif message.type == 'tool':
            return ToolMessage(content=message.content, tool_call_id=getattr(message, 'tool_call_id', ''))
        else:
            return BaseMessage(content=message.content, type=message.type)
    else:
        return BaseMessage(content=str(message), type="base")