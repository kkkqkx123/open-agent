"""基础图状态定义

提供所有状态类型的基础定义。
"""

from typing import Dict, Any, List, Annotated, Optional, Sequence
import operator
from typing_extensions import TypedDict

# 导入消息类型
try:
    from langchain_core.messages import BaseMessage as LCBaseMessage  # type: ignore
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    
    # 后备消息类型定义 - 使用不同的类名避免冲突
    class FallbackLCBaseMessage:
        def __init__(self, content: str, type: str = "base"):
            self.content = content
            self.type = type
    
    # 创建别名以便后续使用
    LCBaseMessage = FallbackLCBaseMessage

# 统一的消息类型定义
class BaseMessage:
    """统一消息基类"""
    def __init__(self, content: str, type: str = "base", tool_call_id: Optional[str] = None, **kwargs: Any):
        self.content = content
        self.type = type
        self.tool_call_id = tool_call_id
        for key, value in kwargs.items():
            setattr(self, key, value)

class HumanMessage(BaseMessage):
    """人类消息"""
    def __init__(self, content: str):
        super().__init__(content, "human")

class AIMessage(BaseMessage):
    """AI消息"""
    def __init__(self, content: str):
        super().__init__(content, "ai")

class SystemMessage(BaseMessage):
    """系统消息"""
    def __init__(self, content: str):
        super().__init__(content, "system")

class ToolMessage(BaseMessage):
    """工具消息"""
    def __init__(self, content: str, tool_call_id: str = ""):
        super().__init__(content, "tool", tool_call_id=tool_call_id)


class MessageRole:
    """消息角色常量"""
    HUMAN = "human"
    AI = "ai"
    SYSTEM = "system"
    TOOL = "tool"


# 基础图状态类型定义
# 使用Dict[str, Any]以支持字典操作，同时保持类型兼容性
BaseGraphState = Dict[str, Any]

# 类型注解，用于IDE提示和文档
class _BaseGraphState(TypedDict, total=False):
    """基础图状态类型注解

    所有状态类型的基础类，提供通用的状态字段。
    """
    # 使用reducer确保消息列表是追加而不是覆盖
    messages: Annotated[List[BaseMessage], operator.add]

    # 可选字段
    metadata: Dict[str, Any]

    # 执行上下文
    execution_context: Dict[str, Any]

    # 当前步骤
    current_step: str


def create_base_state(
    messages: Optional[Sequence[BaseMessage]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    execution_context: Optional[Dict[str, Any]] = None,
    current_step: str = "start"
) -> BaseGraphState:
    """创建基础状态

    Args:
        messages: 初始消息列表
        metadata: 元数据
        execution_context: 执行上下文
        current_step: 当前步骤

    Returns:
        BaseGraphState实例
    """
    return {
        "messages": list(messages) if messages is not None else [],
        "metadata": metadata or {},
        "execution_context": execution_context or {},
        "current_step": current_step
    }


def create_message(content: str, role: str, **kwargs: Any) -> BaseMessage:
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


def adapt_langchain_message(message: Any) -> BaseMessage:
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
            return ToolMessage(
                content=message.content, 
                tool_call_id=getattr(message, 'tool_call_id', '')
            )
        else:
            return BaseMessage(content=message.content, type=message.type)
    else:
        return BaseMessage(content=str(message), type="base")