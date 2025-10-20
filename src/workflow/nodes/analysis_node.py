"""分析节点

负责分析用户输入和上下文，判断是否需要调用工具，并生成相应的响应。
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..registry import BaseNode, NodeExecutionResult, node
from ...prompts.agent_state import AgentState
from ...llm.interfaces import ILLMClient
from ...infrastructure.container import IDependencyContainer


@node("analysis_node")
class AnalysisNode(BaseNode):
    """分析节点"""

    def __init__(self, llm_client: Optional[ILLMClient] = None) -> None:
        """初始化分析节点

        Args:
            llm_client: LLM客户端实例
        """
        self._llm_client = llm_client

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "analysis_node"

    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行分析逻辑

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 获取LLM客户端
        llm_client = self._get_llm_client(config)
        
        # 构建系统提示词
        system_prompt = config.get("system_prompt", self._get_default_system_prompt())
        
        # 检查是否需要调用工具
        max_tokens = config.get("max_tokens", 2000)
        temperature = config.get("temperature", 0.7)
        
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
        
        # 更新状态
        state.add_message(response)
        
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

    def _get_llm_client(self, config: Dict[str, Any]) -> ILLMClient:
        """获取LLM客户端

        Args:
            config: 节点配置

        Returns:
            ILLMClient: LLM客户端实例
        """
        if self._llm_client:
            return self._llm_client
        
        # 从依赖容器获取
        # TODO: 实现完整的LLM客户端工厂注册和获取逻辑
        # try:
        #     from ...infrastructure import get_global_container
        #     container = get_global_container()
        #     llm_client_name = config["llm_client"]
        #     # 这里需要根据实际的LLM客户端获取方式调整
        #     # 假设容器中有LLM客户端工厂
        #     llm_factory = container.get(type(ILLMClient))
        #     return llm_factory.create_client({"name": llm_client_name})
        # except Exception:
        #     # 如果无法获取客户端，返回模拟客户端
        #     pass

        # 暂时直接返回模拟客户端
        return self._create_mock_client()

    def _create_mock_client(self) -> ILLMClient:
        """创建模拟LLM客户端"""
        from ...llm.clients.mock_client import MockLLMClient
        from ...llm.models import LLMResponse, TokenUsage
        from ...llm.config import MockConfig
        from langchain_core.messages import AIMessage

        class MockClient(MockLLMClient):
            def __init__(self) -> None:
                super().__init__(MockConfig(model_type="mock", model_name="mock-model"))

            def generate(self, messages: Any, parameters: Any = None, **kwargs: Any) -> LLMResponse:
                # 简单的模拟响应
                content = "这是一个分析节点的模拟响应"
                return LLMResponse(
                    content=content,
                    message=AIMessage(content=content),
                    model="mock-model",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                )

        return MockClient()

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个智能助手，负责分析用户输入并决定是否需要调用工具。

请根据用户的请求：
1. 如果需要获取外部信息或执行操作，请调用相应的工具
2. 如果可以直接回答，请提供详细的回答
3. 始终保持友好和专业的语调

分析用户意图后，选择最合适的行动。"""

    def _prepare_messages(self, state: AgentState, system_prompt: str) -> list:
        """准备发送给LLM的消息

        Args:
            state: 当前Agent状态
            system_prompt: 系统提示词

        Returns:
            list: 消息列表
        """
        messages = []
        
        # 添加系统消息
        try:
            from langchain_core.messages import SystemMessage
            messages.append(SystemMessage(content=system_prompt))
        except ImportError:
            # 如果LangChain不可用，使用简单消息
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        messages.extend(state.messages)
        
        return messages

    def _get_tool_functions(self, config: Dict[str, Any]) -> Optional[list]:
        """获取工具函数定义

        Args:
            config: 节点配置

        Returns:
            Optional[list]: 工具函数定义列表
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
            return "execute_tool"
        
        # 检查响应内容是否包含工具调用指示
        content = getattr(response, 'content', '')
        if self._contains_tool_indication(content):
            return "execute_tool"
        
        # 默认返回None，表示工作流结束
        return None

    def _contains_tool_indication(self, content: str) -> bool:
        """检查内容是否包含工具调用指示

        Args:
            content: 响应内容

        Returns:
            bool: 是否包含工具调用指示
        """
        tool_keywords = ["我需要", "让我查询", "让我搜索", "我需要调用", "工具", "查询", "搜索"]
        content_lower = content.lower()
        return any(keyword in content_lower for keyword in tool_keywords)