"""
工具格式化器实现

提供工具的格式化功能，支持Function Calling和结构化输出两种策略。
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Sequence

from src.interfaces.llm import ILLMClient
from src.interfaces.messages import IBaseMessage
from src.interfaces.tool.base import IToolFormatter, ToolCall, ITool

class FunctionCallingFormatter(IToolFormatter):
    """Function Calling格式化策略

    将工具格式化为LLM Function Calling格式。
    """

    def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的格式

        Args:
            tools: 工具列表

        Returns:
            Dict[str, Any]: 格式化后的工具描述
        """
        functions: List[Dict[str, Any]] = []
        for tool in tools:
            function: Dict[str, Any] = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_schema(),
            }
            functions.append(function)

        return {"functions": functions}

    def detect_strategy(self, llm_client: ILLMClient) -> str:
        """检测模型支持的输出策略

        Args:
            llm_client: LLM客户端实例

        Returns:
            str: 策略类型
        """
        # 通过LLM客户端的supports_function_calling方法判断是否支持Function Calling
        if llm_client.supports_function_calling():
            return "function_calling"
        # 其他模型默认使用结构化输出
        else:
            return "structured_output"

    def parse_llm_response(self, response: IBaseMessage) -> ToolCall:
        """解析LLM的工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 响应格式不正确
        """
        # 使用类型安全的接口检查工具调用
        if response.has_tool_calls():
            tool_calls = response.get_tool_calls()
            if tool_calls:
                # 使用基础设施层的解析器解析工具调用
                from src.infrastructure.messages.tool_call_parser import ToolCallParser
                
                parsed_tool_calls = ToolCallParser.parse_tool_calls(tool_calls)
                if parsed_tool_calls:
                    return parsed_tool_calls[0]

        # 尝试从内容中解析JSON格式的工具调用
        if hasattr(response, "content") and response.content:
            try:
                # 处理content可能是列表的情况
                content = response.content
                if isinstance(content, list):
                    # 如果是列表，提取文本内容
                    content = " ".join(
                        item.get("text", "") if isinstance(item, dict) else str(item)
                        for item in content
                        if isinstance(item, (dict, str))
                    )
                content = content.strip()
                if content.startswith("{") and content.endswith("}"):
                    data = json.loads(content)
                    if "name" in data and "parameters" in data:
                        arguments = data["parameters"]
                        call_id = data.get("call_id")
                        return ToolCall(
                            name=data["name"],
                            arguments=arguments,
                            call_id=call_id,
                        )
            except json.JSONDecodeError:
                pass

        raise ValueError("LLM响应不包含有效的工具调用")


class StructuredOutputFormatter(IToolFormatter):
    """结构化输出格式化策略

    将工具格式化为结构化输出提示词格式。
    """

    def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的格式

        Args:
            tools: 工具列表

        Returns:
            Dict[str, Any]: 格式化后的工具描述
        """
        tool_descriptions: List[str] = []
        for tool in tools:
            desc: str = f"- {tool.name}: {tool.description}"
            tool_descriptions.append(desc)

        prompt: str = f"""
请按以下JSON格式调用工具：
{{
    "name": "工具名称",
    "parameters": {{
        "参数1": "值1",
        "参数2": "值2"
    }}
}}

可用工具：
{chr(10).join(tool_descriptions)}

请只返回JSON格式的工具调用，不要包含其他文本。
""".strip()

        return {"prompt": prompt}

    def detect_strategy(self, llm_client: ILLMClient) -> str:
        """检测模型支持的输出策略

        Args:
            llm_client: LLM客户端实例

        Returns:
            str: 策略类型
        """
        # 结构化输出是通用策略，所有模型都支持
        return "structured_output"

    def parse_llm_response(self, response: IBaseMessage) -> ToolCall:
        """解析LLM的工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 响应格式不正确
        """
        if not hasattr(response, "content") or not response.content:
            raise ValueError("LLM响应内容为空")

        # 处理content可能是列表的情况
        content = response.content
        if isinstance(content, list):
            # 如果是列表，提取文本内容
            content = " ".join(
                item.get("text", "") if isinstance(item, dict) else str(item)
                for item in content
                if isinstance(item, (dict, str))
            )
        content = content.strip()

        # 尝试直接解析JSON
        try:
            data = json.loads(content)
            if "name" in data and "parameters" in data:
                arguments: Dict[str, Any] = data["parameters"]
                call_id: Optional[str] = data.get("call_id")
                return ToolCall(
                    name=data["name"],
                    arguments=arguments,
                    call_id=call_id,
                )
        except json.JSONDecodeError:
            pass

        # 尝试从文本中提取JSON
        try:
            # 查找JSON对象
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                if "name" in data and "parameters" in data:
                    arguments = data["parameters"]
                    call_id = data.get("call_id")
                    return ToolCall(
                        name=data["name"],
                        arguments=arguments,
                        call_id=call_id,
                    )
        except (json.JSONDecodeError, AttributeError):
            pass

        raise ValueError(f"无法从响应中解析工具调用: {content}")


class ToolFormatter(IToolFormatter):
    """工具格式化器

    根据模型能力自动选择合适的格式化策略。
    """

    def __init__(self) -> None:
        """初始化工具格式化器"""
        self.function_calling_formatter = FunctionCallingFormatter()
        self.structured_output_formatter = StructuredOutputFormatter()

    def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的格式

        Args:
            tools: 工具列表

        Returns:
            Dict[str, Any]: 格式化后的工具描述
        """
        # 默认使用Function Calling格式
        result: Dict[str, Any] = self.function_calling_formatter.format_for_llm(tools)
        return result

    def detect_strategy(self, llm_client: ILLMClient) -> str:
        """检测模型支持的输出策略

        Args:
            llm_client: LLM客户端实例

        Returns:
            str: 策略类型
        """
        # 使用Function Calling格式化器的检测逻辑
        result: str = self.function_calling_formatter.detect_strategy(llm_client)
        return result

    def parse_llm_response(self, response: IBaseMessage) -> ToolCall:
        """解析LLM的工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 响应格式不正确
        """
        # 首先尝试Function Calling解析
        try:
            result: ToolCall = self.function_calling_formatter.parse_llm_response(response)
            return result
        except ValueError:
            # 如果失败，尝试结构化输出解析
            try:
                result = self.structured_output_formatter.parse_llm_response(response)
                return result
            except ValueError:
                # 如果都失败，抛出异常
                raise ValueError("无法解析LLM响应为工具调用")

    def format_for_llm_with_strategy(
        self, tools: Sequence[ITool], strategy: str
    ) -> Dict[str, Any]:
        """使用指定策略格式化工具

        Args:
            tools: 工具列表
            strategy: 格式化策略

        Returns:
            Dict[str, Any]: 格式化后的工具描述

        Raises:
            ValueError: 不支持的策略
        """
        result: Dict[str, Any]
        if strategy == "function_calling":
            result = self.function_calling_formatter.format_for_llm(tools)
            return result
        elif strategy == "structured_output":
            result = self.structured_output_formatter.format_for_llm(tools)
            return result
        else:
            raise ValueError(f"不支持的格式化策略: {strategy}")

    def parse_llm_response_with_strategy(
        self, response: IBaseMessage, strategy: str
    ) -> ToolCall:
        """使用指定策略解析LLM响应

        Args:
            response: LLM响应消息
            strategy: 格式化策略

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 不支持的策略或解析失败
        """
        result: ToolCall
        if strategy == "function_calling":
            result = self.function_calling_formatter.parse_llm_response(response)
            return result
        elif strategy == "structured_output":
            result = self.structured_output_formatter.parse_llm_response(response)
            return result
        else:
            raise ValueError(f"不支持的格式化策略: {strategy}")
