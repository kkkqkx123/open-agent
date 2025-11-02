"""LLM调用节点

负责调用LLM生成最终答案或执行其他LLM相关任务。
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..registry import BaseNode, NodeExecutionResult, node
from ..state import WorkflowState
from src.infrastructure.llm.interfaces import ILLMClient
from ..node_config_loader import get_node_config_loader


@node("llm_node")
class LLMNode(BaseNode):
    """LLM调用节点"""

    def __init__(self, llm_client: ILLMClient) -> None:
        """初始化LLM节点

        Args:
            llm_client: LLM客户端实例（必需）
        """
        self._llm_client = llm_client

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "llm_node"

    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行LLM调用逻辑

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
        system_prompt = self._build_system_prompt(state, merged_config)
        
        # 准备消息
        messages = self._prepare_messages(state, system_prompt)
        
        # 设置生成参数
        parameters = self._prepare_parameters(merged_config)
        
        # 调用LLM
        response = llm_client.generate(messages=messages, parameters=parameters)
        
        # 更新状态 - 添加LLM响应到消息列表
        from langchain_core.messages import AIMessage  # type: ignore
        
        ai_message = AIMessage(content=response.content)
        
        # 安全地更新消息列表
        if "messages" not in state:
            state["messages"] = []
        state["messages"].append(ai_message)
        
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


    def _build_system_prompt(self, state: WorkflowState, config: Dict[str, Any]) -> str:
        """构建系统提示词

        Args:
            state: 当前工作流状态
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
        if config.get("include_tool_results", True) and "tool_results" in state and state["tool_results"]:
            tool_results_text = self._format_tool_results(state["tool_results"])
            base_prompt += f"\n\n工具执行结果：\n{tool_results_text}"
        
        return base_prompt

    def _process_prompt_template(self, template: str, state: WorkflowState, config: Dict[str, Any]) -> str:
        """处理提示词模板

        Args:
            template: 提示词模板
            state: 当前工作流状态
            config: 节点配置

        Returns:
            str: 处理后的提示词
        """
        # 简单的模板变量替换
        variables = {
            "max_iterations": str(state.get("max_iterations", 10)),
            "current_step": state.get("current_step", ""),
            "tool_results_count": str(len(state.get("tool_results", []))),
            "messages_count": str(len(state.get("messages", []))),
        }
        
        result = template
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        config_loader = get_node_config_loader()
        return config_loader.get_config_value(
            self.node_type,
            "system_prompt",
            """你是一个智能助手，请根据上下文信息提供准确、有用的回答。

请遵循以下原则：
1. 基于提供的工具执行结果和上下文信息回答问题
2. 如果信息不足，请明确说明需要什么额外信息
3. 保持回答简洁明了，重点突出
4. 如果有多个步骤的结果，请按逻辑顺序组织回答
5. 始终保持友好和专业的语调"""
        )

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
                success = getattr(result, 'success', True)
                tool_name = getattr(result, 'tool_name', f"工具{i}")
                result_value = getattr(result, 'output', None)
                error = getattr(result, 'error', None)
            
            status = "成功" if success else "失败"
            result_text = f"工具 {i}: {tool_name} - {status}\n"
            
            if success and result_value:
                result_text += f"结果: {result_value}\n"
            elif not success and error:
                result_text += f"错误: {error}\n"
            
            formatted_results.append(result_text)
        
        return "\n".join(formatted_results)

    def _prepare_messages(self, state: WorkflowState, system_prompt: str) -> List:
        """准备发送给LLM的消息

        Args:
            state: 当前工作流状态
            system_prompt: 系统提示词

        Returns:
            List: 消息列表
        """
        messages = []
        
        # 添加系统消息
        from langchain_core.messages import SystemMessage  # type: ignore
        messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息（考虑上下文窗口大小）
        context_messages = self._truncate_messages_for_context(
            state.get("messages", []),
            system_prompt
        )
        messages.extend(context_messages)
        
        return messages

    def _truncate_messages_for_context(
        self,
        messages: List,
        system_prompt: str,
        max_context_tokens: Optional[int] = None
    ) -> List:
        """根据上下文窗口大小截断消息

        Args:
            messages: 原始消息列表
            system_prompt: 系统提示词
            max_context_tokens: 最大上下文token数

        Returns:
            List: 截断后的消息列表
        """
        # 从配置获取上下文窗口大小和消息历史限制
        config_loader = get_node_config_loader()
        context_window_size = max_context_tokens or config_loader.get_config_value(
            self.node_type, "context_window_size", 4000
        )
        max_message_history = config_loader.get_config_value(
            self.node_type, "max_message_history", 10
        )
        
        # 简单实现：保留最近的消息
        # 实际实现应该计算token数量
        if len(messages) <= max_message_history:
            return messages
        
        # 保留系统消息和最近的消息
        return messages[-max_message_history:]

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
            return "analysis_node"  # 返回分析节点进行进一步处理
        
        # 默认结束工作流
        return None

    def _needs_follow_up(self, content: str) -> bool:
        """检查是否需要进一步处理

        Args:
            content: 响应内容

        Returns:
            bool: 是否需要进一步处理
        """
        # 从配置获取后续处理指示词
        config_loader = get_node_config_loader()
        follow_up_indicators = config_loader.get_config_value(
            self.node_type,
            "follow_up_indicators",
            [
                "需要更多信息",
                "无法确定",
                "需要进一步分析",
                "建议查询",
                "让我确认"
            ]
        )
        
        content_lower = content.lower()
        return any(indicator in content_lower for indicator in follow_up_indicators)