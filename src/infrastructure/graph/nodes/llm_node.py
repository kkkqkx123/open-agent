"""LLM调用节点

负责调用LLM生成最终答案或执行其他LLM相关任务。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState, AgentMessage
from src.infrastructure.llm.interfaces import ILLMClient


# SimpleAIMessage removed - using AgentMessage directly


@node("llm_node")
class LLMNode(BaseNode):
    """LLM调用节点"""

    def __init__(self, llm_client: Optional[ILLMClient] = None) -> None:
        """初始化LLM节点

        Args:
            llm_client: LLM客户端实例
        """
        self._llm_client = llm_client

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "llm_node"

    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行LLM调用逻辑

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 获取LLM客户端
        llm_client = self._get_llm_client(config)
        
        # 构建系统提示词
        system_prompt = self._build_system_prompt(state, config)
        
        # 准备消息
        messages = self._prepare_messages(state, system_prompt)
        
        # 设置生成参数
        parameters = self._prepare_parameters(config)
        
        # 调用LLM
        response = llm_client.generate(messages=messages, parameters=parameters)
        
        # 更新状态 - 需要将LLMResponse转换为AgentState兼容的消息格式
        # 检查LLMResponse中的message类型并转换为AgentMessage
        if hasattr(response, 'message') and response.message is not None:
            # 如果response有message属性，检查其类型
            if hasattr(response.message, 'content'):
                # 如果message有content属性，使用它
                compatible_message = AgentMessage(
                    content=str(response.message.content),
                    role='ai'
                )
            else:
                # 否则使用response的content
                compatible_message = AgentMessage(
                    content=response.content,
                    role='ai'
                )
        else:
            # 如果没有message属性，直接使用content
            compatible_message = AgentMessage(
                content=response.content,
                role='ai'
            )

        # 手动将消息添加到状态中
        state.messages.append(compatible_message)
        
        # 确定下一步
        next_node = self._determine_next_node(response, config)
        
        return NodeExecutionResult(
            state=state,
            next_node=next_node,
            metadata={
                "llm_response": response.content,
                "token_usage": getattr(response, "token_usage", None),
                "model_info": llm_client.get_model_info(),
                "system_prompt": system_prompt
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
                "system_prompt_template": {
                    "type": "string",
                    "description": "系统提示词模板（支持变量替换）"
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
                "top_p": {
                    "type": "number",
                    "description": "Top-p采样参数",
                    "default": 1.0
                },
                "frequency_penalty": {
                    "type": "number",
                    "description": "频率惩罚",
                    "default": 0.0
                },
                "presence_penalty": {
                    "type": "number",
                    "description": "存在惩罚",
                    "default": 0.0
                },
                "stop_sequences": {
                    "type": "array",
                    "description": "停止序列",
                    "items": {"type": "string"}
                },
                "include_tool_results": {
                    "type": "boolean",
                    "description": "是否在提示词中包含工具执行结果",
                    "default": True
                },
                "context_window_size": {
                    "type": "integer",
                    "description": "上下文窗口大小",
                    "default": 4000
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
        from src.infrastructure.llm.clients.mock import MockLLMClient
        from src.infrastructure.llm.models import LLMResponse, TokenUsage
        from src.infrastructure.llm.config import MockConfig
        
        # 使用我们定义的简单消息类，避免依赖LangChain
        class MockClientImpl(MockLLMClient):
            def __init__(self) -> None:
                super().__init__(MockConfig(model_type="mock", model_name="mock-model"))

            def generate(self, messages: Any, parameters: Optional[Dict[str, Any]] = None, **kwargs: Any) -> "LLMResponse":
                # 简单的模拟响应
                content = "这是一个LLM节点的模拟响应"
                # 使用AgentMessage作为消息类型
                message = AgentMessage(content=content, role='ai')
                return LLMResponse(
                    content=content,
                    message=message,
                    model="mock-model",
                    token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15)
                )
        
        return MockClientImpl()

    def _build_system_prompt(self, state: AgentState, config: Dict[str, Any]) -> str:
        """构建系统提示词

        Args:
            state: 当前Agent状态
            config: 节点配置

        Returns:
            str: 系统提示词
        """
        # 获取基础提示词
        if "system_prompt" in config:
            base_prompt = config["system_prompt"]
        elif "system_prompt_template" in config:
            # 使用模板
            base_prompt = self._process_prompt_template(config["system_prompt_template"], state, config)
        else:
            base_prompt = self._get_default_system_prompt()
        
        # 添加工具结果（如果配置了）
        if config.get("include_tool_results", True) and state.tool_results:
            tool_results_text = self._format_tool_results(state.tool_results)
            base_prompt += f"\n\n工具执行结果：\n{tool_results_text}"
        
        return base_prompt  # type: ignore

    def _process_prompt_template(self, template: str, state: AgentState, config: Dict[str, Any]) -> str:
        """处理提示词模板

        Args:
            template: 提示词模板
            state: 当前Agent状态
            config: 节点配置

        Returns:
            str: 处理后的提示词
        """
        # 简单的模板变量替换
        variables = {
            "max_iterations": str(state.max_iterations),
            "current_step": state.current_step,
            "tool_results_count": str(len(state.tool_results)),
            "messages_count": str(len(state.messages)),
        }
        
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个智能助手，请根据上下文信息提供准确、有用的回答。

请遵循以下原则：
1. 基于提供的工具执行结果和上下文信息回答问题
2. 如果信息不足，请明确说明需要什么额外信息
3. 保持回答简洁明了，重点突出
4. 如果有多个步骤的结果，请按逻辑顺序组织回答
5. 始终保持友好和专业的语调"""

    def _format_tool_results(self, tool_results: List) -> str:
        """格式化工具执行结果

        Args:
            tool_results: 工具执行结果列表

        Returns:
            str: 格式化后的工具结果
        """
        if not tool_results:
            return "没有工具执行结果"
        
        formatted_results = []
        for i, result in enumerate(tool_results, 1):
            # 处理字典格式的工具结果
            if isinstance(result, dict):
                success = result.get("success", True)
                tool_name = result.get("tool_name", f"工具{i}")
                result_value = result.get("result")
                error = result.get("error")
            else:
                # 处理对象格式的工具结果
                success = result.success
                tool_name = result.tool_name
                result_value = result.output  # 使用output属性而不是result
                error = result.error
            
            status = "成功" if success else "失败"
            result_text = f"工具 {i}: {tool_name} - {status}\n"
            
            if success and result_value:
                result_text += f"结果: {result_value}\n"
            elif not success and error:
                result_text += f"错误: {error}\n"
            
            formatted_results.append(result_text)
        
        return "\n".join(formatted_results)

    def _prepare_messages(self, state: AgentState, system_prompt: str) -> List:
        """准备发送给LLM的消息

        Args:
            state: 当前Agent状态
            system_prompt: 系统提示词

        Returns:
            List: 消息列表
        """
        messages = []
        
        # 添加系统消息
        # 使用简单的消息格式，避免依赖LangChain
        messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息（考虑上下文窗口大小）
        context_messages = self._truncate_messages_for_context(
            state.messages,
            system_prompt
        )
        # 将AgentMessage转换为兼容的消息格式
        for msg in context_messages:
            if isinstance(msg, AgentMessage):
                # 如果是AgentMessage，转换为字典格式
                messages.append({"role": msg.role, "content": msg.content})
            else:
                # 如果是其他类型，直接添加
                messages.append(msg)
        
        return messages

    def _truncate_messages_for_context(
        self, 
        messages: List, 
        system_prompt: str,
        max_context_tokens: int = 4000
    ) -> List:
        """根据上下文窗口大小截断消息

        Args:
            messages: 原始消息列表
            system_prompt: 系统提示词
            max_context_tokens: 最大上下文token数

        Returns:
            List: 截断后的消息列表
        """
        # 简单实现：保留最近的消息
        # 实际实现应该计算token数量
        if len(messages) <= 10:  # 简单的消息数量限制
            return messages
        
        # 保留系统消息和最近的消息
        return messages[-10:]

    def _prepare_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备LLM生成参数

        Args:
            config: 节点配置

        Returns:
            Dict[str, Any]: 生成参数
        """
        parameters = {}
        
        # 基本参数
        if "max_tokens" in config:
            parameters["max_tokens"] = config["max_tokens"]
        if "temperature" in config:
            parameters["temperature"] = config["temperature"]
        if "top_p" in config:
            parameters["top_p"] = config["top_p"]
        if "frequency_penalty" in config:
            parameters["frequency_penalty"] = config["frequency_penalty"]
        if "presence_penalty" in config:
            parameters["presence_penalty"] = config["presence_penalty"]
        if "stop_sequences" in config:
            parameters["stop"] = config["stop_sequences"]
        
        return parameters

    def _determine_next_node(self, response: Any, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点

        Args:
            response: LLM响应
            config: 节点配置

        Returns:
            Optional[str]: 下一个节点名称
        """
        # 对于LLM节点，通常是工作流的结束节点
        # 但可以根据配置返回到其他节点
        
        # 检查是否配置了下一个节点
        if "next_node" in config:
            return str(config["next_node"])
        
        # 检查响应内容是否需要进一步处理
        content = getattr(response, 'content', '')
        if self._needs_follow_up(content):
            return "analyze"  # 返回分析节点进行进一步处理
        
        # 默认结束工作流
        return None

    def _needs_follow_up(self, content: str) -> bool:
        """检查是否需要进一步处理

        Args:
            content: 响应内容

        Returns:
            bool: 是否需要进一步处理
        """
        # 简单的启发式判断
        follow_up_indicators = [
            "需要更多信息",
            "无法确定",
            "需要进一步分析",
            "建议查询",
            "让我确认"
        ]
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in follow_up_indicators)