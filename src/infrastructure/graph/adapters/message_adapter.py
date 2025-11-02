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
       
       # 初始化 metadata 和 additional_kwargs
       metadata = {}
       additional_kwargs = {}
       tool_calls = None
       
       # 处理 LangChain 标准的 tool_calls 属性（仅对 LangChain 原生消息）
       if isinstance(graph_message, (LCAIMessage, LCHumanMessage, LCSystemMessage, LCToolMessage)):
           # 使用 getattr 安全地获取属性
           tool_calls_attr = getattr(graph_message, 'tool_calls', None)
           if tool_calls_attr:
               # 转换为标准格式
               tool_calls = []
               for tc in tool_calls_attr:
                   if isinstance(tc, dict):
                       tool_calls.append({
                           "name": tc.get("name", ""),
                           "args": tc.get("args", {}),
                           "id": tc.get("id", ""),
                       })
                   else:
                       # 处理对象形式的工具调用
                       tool_calls.append({
                           "name": getattr(tc, "name", ""),
                           "args": getattr(tc, "args", {}),
                           "id": getattr(tc, "id", ""),
                       })
           
           # 处理 additional_kwargs 中的 tool_calls（OpenAI 格式）
           additional_kwargs_attr = getattr(graph_message, 'additional_kwargs', None)
           if additional_kwargs_attr:
               additional_kwargs = additional_kwargs_attr.copy()
               if "tool_calls" in additional_kwargs:
                   # 如果还没有 tool_calls，从 additional_kwargs 中提取
                   if not tool_calls:
                       tool_calls = []
                       for tc in additional_kwargs["tool_calls"]:
                           if "function" in tc:
                               function = tc["function"]
                               import json
                               try:
                                   args = json.loads(function.get("arguments", "{}"))
                               except json.JSONDecodeError:
                                   args = {}
                               tool_calls.append({
                                   "name": function.get("name", ""),
                                   "args": args,
                                   "id": tc.get("id", ""),
                               })
       
       # 如果是工具消息，添加tool_call_id到metadata
       if isinstance(graph_message, (LCToolMessage, ToolMessage)) and hasattr(graph_message, 'tool_call_id'):
           metadata["tool_call_id"] = getattr(graph_message, 'tool_call_id', '')
       
       # 保持向后兼容，将 tool_calls 也存储在 metadata 中
       if tool_calls:
           metadata["tool_calls"] = tool_calls
       
       domain_message = DomainAgentMessage(
           content=content,
           role=role,
           timestamp=datetime.now(),  # 图系统消息可能没有时间戳，使用当前时间
           metadata=metadata,
           tool_calls=tool_calls,
           additional_kwargs=additional_kwargs
       )
       
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
        
        优先使用新的 tool_calls 属性，如果没有则回退到 metadata
        
        Args:
            domain_message: 域层Agent消息
            
        Returns:
            工具调用列表
        """
        # 优先使用新的 tool_calls 属性
        if domain_message.tool_calls:
            return domain_message.tool_calls
        
        # 回退到 metadata 中的 tool_calls
        return cast(List[Dict[str, Any]], domain_message.metadata.get("tool_calls", []))
    
    def add_tool_calls_to_message(self, domain_message: DomainAgentMessage, tool_calls: List[Dict[str, Any]]) -> DomainAgentMessage:
        """向域层消息添加工具调用信息
        
        同时更新新的 tool_calls 属性和 metadata（向后兼容）
        
        Args:
            domain_message: 域层Agent消息
            tool_calls: 工具调用列表
            
        Returns:
            更新后的域层Agent消息
        """
        # 更新新的 tool_calls 属性
        domain_message.tool_calls = tool_calls
        
        # 保持 metadata 中的 tool_calls（向后兼容）
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