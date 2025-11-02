"""Agent状态定义

定义Agent的状态模型和相关类。
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class AgentMessage:
    """Agent消息类"""
    content: str
    role: str = "assistant"  # 可以是 "user", "assistant", "system", "tool"
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolResult:
    """工具执行结果"""
    tool_name: str
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class AgentState(Dict[str, Any]):
    """Agent状态类
    
    继承自Dict，提供状态管理功能。
    """
    
    def __init__(
        self,
        agent_id: str = "",
        messages: Optional[List[AgentMessage]] = None,
        tool_results: Optional[List[ToolResult]] = None,
        iteration_count: int = 0,
        max_iterations: int = 10,
        custom_fields: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """初始化Agent状态
        
        Args:
            agent_id: Agent ID
            messages: 消息列表
            tool_results: 工具执行结果列表
            iteration_count: 当前迭代次数
            max_iterations: 最大迭代次数
            custom_fields: 自定义字段
            **kwargs: 其他字段
        """
        super().__init__()
        
        # 基础字段
        self["agent_id"] = agent_id
        self["messages"] = messages or []
        self["tool_results"] = tool_results or []
        self["iteration_count"] = iteration_count
        self["max_iterations"] = max_iterations
        self["custom_fields"] = custom_fields or {}
        
        # 添加其他字段
        for key, value in kwargs.items():
            self[key] = value
        
        # 动态属性访问支持
        self._setup_properties()
    
    def _setup_properties(self):
        """设置动态属性"""
        # 为常用字段提供属性访问
        for field_name in ["agent_id", "iteration_count", "max_iterations"]:
            if field_name in self:
                setattr(self.__class__, field_name, 
                       property(lambda self, f=field_name: self.get(f)))
    
    @property
    def messages(self) -> List[AgentMessage]:
        """获取消息列表"""
        return self.get("messages", [])
    
    @messages.setter
    def messages(self, value: List[AgentMessage]):
        """设置消息列表"""
        self["messages"] = value
    
    @property
    def tool_results(self) -> List[ToolResult]:
        """获取工具执行结果列表"""
        return self.get("tool_results", [])
    
    @tool_results.setter
    def tool_results(self, value: List[ToolResult]):
        """设置工具执行结果列表"""
        self["tool_results"] = value
    
    @property
    def custom_fields(self) -> Dict[str, Any]:
        """获取自定义字段"""
        return self.get("custom_fields", {})
    
    @custom_fields.setter
    def custom_fields(self, value: Dict[str, Any]):
        """设置自定义字段"""
        self["custom_fields"] = value
    
    def add_message(self, message: AgentMessage):
        """添加消息
        
        Args:
            message: 要添加的消息
        """
        self.messages.append(message)
    
    def add_tool_result(self, result: ToolResult):
        """添加工具执行结果
        
        Args:
            result: 要添加的工具执行结果
        """
        self.tool_results.append(result)
    
    def increment_iteration(self):
        """增加迭代次数"""
        self["iteration_count"] = self.get("iteration_count", 0) + 1
    
    def is_max_iterations_reached(self) -> bool:
        """检查是否达到最大迭代次数"""
        return self.get("iteration_count", 0) >= self.get("max_iterations", 10)
    
    def get_last_message(self) -> Optional[AgentMessage]:
        """获取最后一条消息"""
        messages = self.messages
        return messages[-1] if messages else None
    
    def has_errors(self) -> bool:
        """检查是否有错误"""
        for result in self.tool_results:
            if not result.success:
                return True
        return False
    
    def get_errors(self) -> List[str]:
        """获取所有错误信息"""
        errors = []
        for result in self.tool_results:
            if not result.success and result.error:
                errors.append(result.error)
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 状态字典
        """
        result = dict(self)
        
        # 转换复杂对象为字典
        if "messages" in result:
            result["messages"] = [
                {
                    "content": msg.content,
                    "role": msg.role,
                    "timestamp": msg.timestamp.isoformat() if msg.timestamp else None,
                    "metadata": msg.metadata
                }
                for msg in result["messages"]
            ]
        
        if "tool_results" in result:
            result["tool_results"] = [
                {
                    "tool_name": tr.tool_name,
                    "success": tr.success,
                    "output": tr.output,
                    "error": tr.error,
                    "execution_time": tr.execution_time,
                    "timestamp": tr.timestamp.isoformat() if tr.timestamp else None
                }
                for tr in result["tool_results"]
            ]
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """从字典创建AgentState
        
        Args:
            data: 状态字典
            
        Returns:
            AgentState: Agent状态实例
        """
        # 处理消息
        messages = []
        if "messages" in data:
            for msg_data in data["messages"]:
                if isinstance(msg_data, dict):
                    timestamp = msg_data.get("timestamp")
                    if timestamp and isinstance(timestamp, str):
                        from datetime import datetime
                        timestamp = datetime.fromisoformat(timestamp)
                    
                    messages.append(AgentMessage(
                        content=msg_data.get("content", ""),
                        role=msg_data.get("role", "assistant"),
                        timestamp=timestamp,
                        metadata=msg_data.get("metadata", {})
                    ))
                else:
                    # 兼容旧格式
                    messages.append(msg_data)
        
        # 处理工具结果
        tool_results = []
        if "tool_results" in data:
            for tr_data in data["tool_results"]:
                if isinstance(tr_data, dict):
                    timestamp = tr_data.get("timestamp")
                    if timestamp and isinstance(timestamp, str):
                        from datetime import datetime
                        timestamp = datetime.fromisoformat(timestamp)
                    
                    tool_results.append(ToolResult(
                        tool_name=tr_data.get("tool_name", ""),
                        success=tr_data.get("success", False),
                        output=tr_data.get("output"),
                        error=tr_data.get("error"),
                        execution_time=tr_data.get("execution_time", 0.0),
                        timestamp=timestamp
                    ))
                else:
                    # 兼容旧格式
                    tool_results.append(tr_data)
        
        # 创建状态实例
        state_data = dict(data)
        state_data["messages"] = messages
        state_data["tool_results"] = tool_results
        
        return cls(**state_data)