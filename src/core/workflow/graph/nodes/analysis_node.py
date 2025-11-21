"""分析节点

负责分析用户输入和上下文，判断是否需要调用工具，并生成相应的响应。
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass

from .registry import BaseNode, NodeExecutionResult, node
from ...states import WorkflowState
from src.interfaces.llm import ILLMClient
from src.infrastructure.container_interfaces import IDependencyContainer
from ...config.node_config_loader import get_node_config_loader
from langchain_core.messages import AIMessage, SystemMessage


@node("analysis_node")
class AnalysisNode(BaseNode):
    """分析节点"""

    def __init__(self, llm_client: ILLMClient) -> None:
        """初始化分析节点

        Args:
            llm_client: LLM客户端实例（必需）
        """
        self._llm_client = llm_client

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "analysis_node"

    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行分析逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 合并默认配置和运行时配置
        config_loader = get_node_config_loader()
        merged_config = config_loader.merge_configs(self.node_type, config)
        
        # 使用注入的LLM客户端
        llm_client = self._llm_client
        
        # 构建系统提示词
        system_prompt = merged_config.get("system_prompt", self._get_default_system_prompt())
        
        # 检查是否需要调用工具
        max_tokens = merged_config.get("max_tokens", 2000)
        temperature = merged_config.get("temperature", 0.7)
        
        # 准备消息
        messages = self._prepare_messages(state, system_prompt)
        
        # 调用LLM
        response = llm_client.generate(
            messages=messages,
            parameters={
                "max_tokens": max_tokens,
                "temperature": temperature,
                "functions": self._get_tool_functions(config) if llm_client.supports_function_calling() else None
            }
        )
        
        # 更新状态 - 添加LLM响应到消息列表
        ai_message = AIMessage(content=response.content)
        
        # 安全地更新消息列表
        if state.get("messages") is None:
            state.set_value("messages", [])
        state.get("messages", []).append(ai_message)
        
        # 分析响应，确定下一步
        next_node = self._determine_next_node(response, config)
        
        return NodeExecutionResult(
            state=state,
            next_node=next_node,
            metadata={
                "llm_response": response.content,
                "tool_calls": getattr(response, "tool_calls", None),
                "token_usage": getattr(response, "token_usage", None)
            }
        )

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "llm_client": {
                    "type": "string",
                    "description": "LLM客户端配置名称"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "系统提示词"
                },
                "max_tokens": {
                    "type": "integer",
                    "description": "最大生成token数",
                    "default": 2000
                },
                "temperature": {
                    "type": "number",
                    "description": "生成温度",
                    "default": 0.7
                },
                "tool_threshold": {
                    "type": "number",
                    "description": "工具调用阈值",
                    "default": 0.5
                },
                "available_tools": {
                    "type": "array",
                    "description": "可用工具列表",
                    "items": {"type": "string"}
                }
            },
            "required": ["llm_client"]
        }


    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        config_loader = get_node_config_loader()
        result = config_loader.get_config_value(
            self.node_type,
            "system_prompt",
            """你是一个智能助手，负责分析用户输入并决定是否需要调用工具。

请根据用户的请求：
1. 如果需要获取外部信息或执行操作，请调用相应的工具
2. 如果可以直接回答，请提供详细的回答
3. 始终保持友好和专业的语调

分析用户意图后，选择最合适的行动。"""
        )
        # 确保返回字符串类型
        return str(result) if result is not None else ""

    def _prepare_messages(self, state: WorkflowState, system_prompt: str) -> List[Union[SystemMessage, Any]]:
        """准备发送给LLM的消息

        Args:
            state: 当前工作流状态
            system_prompt: 系统提示词

        Returns:
            List[Union[SystemMessage, Any]]: 消息列表
        """
        messages = []
        
        # 添加系统消息
        messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        if state.get("messages") is not None and state.get("messages"):
            messages.extend(state.get("messages", []))
        
        return messages

    def _get_tool_functions(self, config: Dict[str, Any]) -> Optional[List]:
        """获取工具函数定义

        Args:
            config: 节点配置

        Returns:
            Optional[List]: 工具函数定义列表
        """
        available_tools = config.get("available_tools", [])
        if not available_tools:
            return None
        
        # 这里应该从工具管理器获取实际的工具定义
        # 暂时返回空列表
        return []

    def _determine_next_node(self, response: Any, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点

        Args:
            response: LLM响应
            config: 节点配置

        Returns:
            Optional[str]: 下一个节点名称
        """
        # 检查是否有工具调用
        if hasattr(response, 'tool_calls') and response.tool_calls:
            return "tool_node"
        
        # 检查响应内容是否包含工具调用指示
        content = getattr(response, 'content', '')
        if self._contains_tool_indication(content):
            return "tool_node"
        
        # 默认返回None，表示工作流结束
        return None

    def _contains_tool_indication(self, content: str) -> bool:
        """检查内容是否包含工具调用指示

        Args:
            content: 响应内容

        Returns:
            bool: 是否包含工具调用指示
        """
        config_loader = get_node_config_loader()
        tool_keywords = config_loader.get_config_value(
            self.node_type,
            "tool_keywords",
            ["我需要", "让我查询", "让我搜索", "我需要调用", "工具", "查询", "搜索"]
        )
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in tool_keywords)