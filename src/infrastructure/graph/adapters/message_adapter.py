"""消息适配器

提供域层AgentMessage与图系统消息之间的转换功能。
"""

from typing import List, Dict, Any, cast, Union
from datetime import datetime

from src.domain.agent.state import AgentMessage as DomainAgentMessage
from src.infrastructure.graph.state import BaseMessage as GraphBaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage, LCBaseMessage, LCHumanMessage, LCAIMessage, LCSystemMessage, LCToolMessage


class MessageAdapter:
    """消息适配器
    
    负责在域层AgentMessage和图系统消息之间进行转换。
    """
    
    def to_graph_message(self, domain_message: DomainAgentMessage) -> Union[GraphBaseMessage, LCBaseMessage]:
       """将域层AgentMessage转换为图系统消息
       
       Args:
           domain_message: 域层Agent消息
           
       Returns:
           图系统兼容的消息
       """
       # 确保content是字符串类型
       content = domain_message.content
       if not isinstance(content, str):
           content = str(content)
       
       if domain_message.role == "user":
           return LCHumanMessage(content=content)
       elif domain_message.role == "assistant":
           return LCAIMessage(content=content)
       elif domain_message.role == "system":
           return LCSystemMessage(content=content)
       elif domain_message.role == "tool":
           tool_call_id = domain_message.metadata.get("tool_call_id", "")
           return LCToolMessage(content=content, tool_call_id=tool_call_id)
       else:
           return LCBaseMessage(content=content, type=domain_message.role)
    
    def from_graph_message(self, graph_message: Union[GraphBaseMessage, LCBaseMessage]) -> DomainAgentMessage:
       """将图系统消息转换为域层AgentMessage
       
       Args:
           graph_message: 图系统消息
           
       Returns:
           域层Agent消息
       """
       # 确定角色并进行映射
       if hasattr(graph_message, 'type'):
           # 图系统角色到域层角色的映射
           role_mapping = {
               "human": "user",
               "ai": "assistant",
               "system": "system",
               "tool": "tool"
           }
           role = role_mapping.get(graph_message.type, "unknown")
       else:
           # 根据消息类型推断角色
           if isinstance(graph_message, (LCHumanMessage, HumanMessage)):
               role = "user"
           elif isinstance(graph_message, (LCAIMessage, AIMessage)):
               role = "assistant"
           elif isinstance(graph_message, (LCSystemMessage, SystemMessage)):
               role = "system"
           elif isinstance(graph_message, (LCToolMessage, ToolMessage)):
               role = "tool"
           else:
               role = "unknown"
       
       # 创建域层消息
       # 确保content是字符串类型
       content = graph_message.content
       if not isinstance(content, str):
           content = str(content)
       
       domain_message = DomainAgentMessage(
           content=content,
           role=role,
           timestamp=datetime.now(),  # 图系统消息可能没有时间戳，使用当前时间
           metadata={}
       )
       
       # 如果是工具消息，添加tool_call_id到metadata
       if isinstance(graph_message, (LCToolMessage, ToolMessage)) and hasattr(graph_message, 'tool_call_id'):
           domain_message.metadata["tool_call_id"] = getattr(graph_message, 'tool_call_id', '')
       
       return domain_message
    
    def to_graph_messages(self, domain_messages: List[DomainAgentMessage]) -> List[Union[GraphBaseMessage, LCBaseMessage]]:
       """批量转换域层消息为图系统消息
       
       Args:
           domain_messages: 域层Agent消息列表
           
       Returns:
           图系统消息列表
       """
       return [self.to_graph_message(msg) for msg in domain_messages]
    
    def from_graph_messages(self, graph_messages: List[Union[GraphBaseMessage, LCBaseMessage]]) -> List[DomainAgentMessage]:
       """批量转换图系统消息为域层消息
       
       Args:
           graph_messages: 图系统消息列表
           
       Returns:
           域层Agent消息列表
       """
       return [self.from_graph_message(msg) for msg in graph_messages]
    
    def extract_tool_calls(self, domain_message: DomainAgentMessage) -> List[Dict[str, Any]]:
        """从域层消息中提取工具调用信息
        
        Args:
            domain_message: 域层Agent消息
            
        Returns:
            工具调用列表
        """
        return cast(List[Dict[str, Any]], domain_message.metadata.get("tool_calls", []))
    
    def add_tool_calls_to_message(self, domain_message: DomainAgentMessage, tool_calls: List[Dict[str, Any]]) -> DomainAgentMessage:
        """向域层消息添加工具调用信息
        
        Args:
            domain_message: 域层Agent消息
            tool_calls: 工具调用列表
            
        Returns:
            更新后的域层Agent消息
        """
        domain_message.metadata["tool_calls"] = tool_calls
        return domain_message
    
    def create_system_message(self, content: str) -> DomainAgentMessage:
        """创建系统消息
        
        Args:
            content: 消息内容
            
        Returns:
            域层系统消息
        """
        return DomainAgentMessage(
            content=content,
            role="system",
            timestamp=datetime.now(),
            metadata={}
        )
    
    def create_user_message(self, content: str) -> DomainAgentMessage:
        """创建用户消息
        
        Args:
            content: 消息内容
            
        Returns:
            域层用户消息
        """
        return DomainAgentMessage(
            content=content,
            role="user",
            timestamp=datetime.now(),
            metadata={}
        )
    
    def create_assistant_message(self, content: str) -> DomainAgentMessage:
        """创建助手消息
        
        Args:
            content: 消息内容
            
        Returns:
            域层助手消息
        """
        return DomainAgentMessage(
            content=content,
            role="assistant",
            timestamp=datetime.now(),
            metadata={}
        )
    
    def create_tool_message(self, content: str, tool_call_id: str = "") -> DomainAgentMessage:
        """创建工具消息
        
        Args:
            content: 消息内容
            tool_call_id: 工具调用ID
            
        Returns:
            域层工具消息
        """
        return DomainAgentMessage(
            content=content,
            role="tool",
            timestamp=datetime.now(),
            metadata={"tool_call_id": tool_call_id}
        )