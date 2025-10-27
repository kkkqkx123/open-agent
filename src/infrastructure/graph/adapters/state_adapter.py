"""状态适配器

提供域层AgentState与图系统状态之间的转换功能。
"""

from typing import Dict, Any, List, Optional, cast, Union
from datetime import datetime
from dataclasses import asdict

from src.domain.agent.state import AgentState as DomainAgentState, AgentMessage as DomainAgentMessage, AgentStatus
from src.infrastructure.graph.states.agent import AgentState as GraphAgentState, create_agent_state as create_graph_agent_state
from src.infrastructure.graph.states.base import BaseMessage as GraphBaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from src.domain.tools.interfaces import ToolResult


class StateAdapter:
    """状态适配器
    
    负责在域层AgentState和图系统AgentState之间进行转换。
    """
    
    def to_graph_state(self, domain_state: DomainAgentState) -> GraphAgentState:
        """将域层AgentState转换为图系统AgentState
        
        Args:
            domain_state: 域层Agent状态
            
        Returns:
            图系统兼容的Agent状态
        """
        # 转换消息
        messages = self._convert_messages_to_graph(domain_state.messages)
        
        # 创建基础图状态
        graph_state = create_graph_agent_state(
            input_text=domain_state.current_task or "",
            agent_id=domain_state.agent_id,
            agent_config={"agent_type": domain_state.agent_type},
            max_iterations=domain_state.max_iterations,
            messages=messages
        )
        
        # 更新其他字段
        graph_state.update({
            "output": self._get_last_assistant_message(domain_state.messages),
            "tool_calls": self._convert_tool_calls(domain_state),
            "tool_results": self._convert_tool_results(domain_state.tool_results),
            "iteration_count": domain_state.iteration_count,
            "errors": [str(error) for error in domain_state.errors],
            "complete": domain_state.status == AgentStatus.COMPLETED,
            "execution_result": {
                "status": domain_state.status.value,
                "start_time": domain_state.start_time.isoformat() if domain_state.start_time else None,
                "last_update_time": domain_state.last_update_time.isoformat() if domain_state.last_update_time else None,
                "execution_duration": domain_state.get_execution_duration(),
                "custom_fields": domain_state.custom_fields
            }
        })
        
        return graph_state
    
    def from_graph_state(self, graph_state: GraphAgentState) -> DomainAgentState:
        """将图系统AgentState转换为域层AgentState
        
        Args:
            graph_state: 图系统Agent状态
            
        Returns:
            域层Agent状态
        """
        # 创建域层状态
        domain_state = DomainAgentState()
        
        # 设置基本信息
        domain_state.agent_id = graph_state.get("agent_id", "")
        domain_state.agent_type = graph_state.get("agent_config", {}).get("agent_type", "")
        
        # 转换消息
        messages = graph_state.get("messages", [])
        domain_state.messages = self._convert_messages_from_graph(messages)
        
        # 设置任务信息
        domain_state.current_task = graph_state.get("input", "")
        
        # 转换工具结果
        tool_results_data = graph_state.get("tool_results", [])
        domain_state.tool_results = self._convert_tool_results_from_graph(tool_results_data)
        
        # 设置控制信息
        domain_state.current_step = graph_state.get("current_step", "")
        domain_state.max_iterations = graph_state.get("max_iterations", 10)
        domain_state.iteration_count = graph_state.get("iteration_count", 0)
        
        # 设置状态
        complete = graph_state.get("complete", False)
        domain_state.status = AgentStatus.COMPLETED if complete else AgentStatus.RUNNING
        
        # 设置时间信息
        execution_result = graph_state.get("execution_result", {})
        if execution_result.get("start_time"):
            domain_state.start_time = datetime.fromisoformat(execution_result["start_time"])
        if execution_result.get("last_update_time"):
            domain_state.last_update_time = datetime.fromisoformat(execution_result["last_update_time"])
        
        # 设置错误和自定义字段
        domain_state.errors = [{"message": error} for error in graph_state.get("errors", [])]
        domain_state.custom_fields = execution_result.get("custom_fields", {})
        
        return domain_state
    
    def _convert_messages_to_graph(self, domain_messages: List[DomainAgentMessage]) -> List[GraphBaseMessage]:
        """将域层消息转换为图系统消息"""
        graph_messages: List[GraphBaseMessage] = []
        
        for domain_msg in domain_messages:
            if domain_msg.role == "user":
                graph_msg = HumanMessage(content=domain_msg.content)
            elif domain_msg.role == "assistant":
                graph_msg = AIMessage(content=domain_msg.content)  # type: ignore
            elif domain_msg.role == "system":
                graph_msg = SystemMessage(content=domain_msg.content)  # type: ignore
            elif domain_msg.role == "tool":
                graph_msg = ToolMessage(
                    content=domain_msg.content,
                    tool_call_id=domain_msg.metadata.get("tool_call_id", "")
                )  # type: ignore
            else:
                graph_msg = GraphBaseMessage(content=domain_msg.content, type=domain_msg.role)  # type: ignore
            
            graph_messages.append(graph_msg)
        
        return graph_messages
    
    def _convert_messages_from_graph(self, graph_messages: List[GraphBaseMessage]) -> List[DomainAgentMessage]:
        """将图系统消息转换为域层消息"""
        domain_messages = []
        
        for graph_msg in graph_messages:
            # 确定角色并进行映射
            if hasattr(graph_msg, 'type'):
                # 图系统角色到域层角色的映射
                role_mapping = {
                    "human": "user",
                    "ai": "assistant",
                    "system": "system",
                    "tool": "tool"
                }
                role = role_mapping.get(graph_msg.type, "unknown")
            else:
                # 根据消息类型推断角色
                if isinstance(graph_msg, HumanMessage):
                    role = "user"
                elif isinstance(graph_msg, AIMessage):
                    role = "assistant"
                elif isinstance(graph_msg, SystemMessage):
                    role = "system"
                elif isinstance(graph_msg, ToolMessage):
                    role = "tool"
                else:
                    role = "unknown"
            
            # 创建域层消息
            domain_msg = DomainAgentMessage(
                content=graph_msg.content,
                role=role,
                timestamp=datetime.now(),  # 图系统消息可能没有时间戳，使用当前时间
                metadata={}
            )
            
            # 如果是工具消息，添加tool_call_id到metadata
            if isinstance(graph_msg, ToolMessage) and hasattr(graph_msg, 'tool_call_id'):
                domain_msg.metadata["tool_call_id"] = graph_msg.tool_call_id
            
            domain_messages.append(domain_msg)
        
        return domain_messages
    
    def _get_last_assistant_message(self, messages: List[DomainAgentMessage]) -> Optional[str]:
        """获取最后一条助手消息的内容"""
        for msg in reversed(messages):
            if msg.role == "assistant":
                return msg.content
        return None
    
    def _convert_tool_calls(self, domain_state: DomainAgentState) -> List[Dict[str, Any]]:
        """转换工具调用信息"""
        tool_calls = []
        
        # 从最后一条消息中提取工具调用
        last_message = domain_state.get_last_message()
        if last_message and "tool_calls" in last_message.metadata:
            tool_calls = last_message.metadata["tool_calls"]
        
        return tool_calls
    
    def _convert_tool_results(self, tool_results: List[ToolResult]) -> List[Dict[str, Any]]:
        """转换工具结果"""
        return [
            {
                "tool_name": result.tool_name,
                "success": result.success,
                "output": result.output,
                "error": result.error
            }
            for result in tool_results
        ]
    
    def _convert_tool_results_from_graph(self, tool_results_data: List[Dict[str, Any]]) -> List[ToolResult]:
        """从图系统工具结果转换回域层工具结果"""
        tool_results = []
        
        for result_data in tool_results_data:
            tool_result = ToolResult(
                tool_name=result_data.get("tool_name", ""),
                success=result_data.get("success", False),
                output=result_data.get("output"),
                error=result_data.get("error")
            )
            tool_results.append(tool_result)
        
        return tool_results