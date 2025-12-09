"""
工具格式化器实现（简化版本）

提供工具的格式化功能，只支持Function Calling和JSONL两种策略。
"""

import json
import re
from typing import Any, Dict, List, Optional, Union, Sequence

from src.interfaces.messages import IBaseMessage
from src.interfaces.llm import ILLMClient
from src.interfaces.tool.base import IToolFormatter, ToolCall, ITool
from src.services.logger import get_logger

logger = get_logger(__name__)

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
        # 其他模型默认使用JSONL
        else:
            return "jsonl"

    def parse_llm_response(self, response: IBaseMessage) -> ToolCall:
        """解析LLM的工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用

        Raises:
            ValueError: 响应格式不正确
        """
        # 检查是否有function_call属性（在additional_kwargs中）
        if (
            hasattr(response, "additional_kwargs")
            and "function_call" in response.additional_kwargs
        ):
            function_call = response.additional_kwargs["function_call"]
            arguments: Dict[str, Any] = json.loads(function_call["arguments"])
            call_id: Optional[str] = function_call.get("id")
            return ToolCall(
                name=function_call["name"],
                arguments=arguments,
                call_id=call_id,
            )

        # 检查是否有tool_calls属性（多工具调用，在additional_kwargs中）
        if (
            hasattr(response, "additional_kwargs")
            and "tool_calls" in response.additional_kwargs
        ):
            tool_calls = response.additional_kwargs["tool_calls"]
            if tool_calls:
                # 返回第一个工具调用
                tool_call = tool_calls[0]
                function = tool_call["function"]
                arguments = json.loads(function["arguments"])
                call_id = tool_call.get("id")
                return ToolCall(
                    name=function["name"],
                    arguments=arguments,
                    call_id=call_id,
                )

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

    def parse_llm_response_batch(self, response: "IBaseMessage") -> List[ToolCall]:
        """解析LLM的工具调用响应（批量）

        Args:
            response: LLM响应消息

        Returns:
            List[ToolCall]: 解析后的工具调用列表
        """
        tool_calls: List[ToolCall] = []
        
        # 检查是否有tool_calls属性（多工具调用，在additional_kwargs中）
        if (
            hasattr(response, "additional_kwargs")
            and "tool_calls" in response.additional_kwargs
        ):
            tool_calls_data = response.additional_kwargs["tool_calls"]
            for tool_call_data in tool_calls_data:
                try:
                    function = tool_call_data["function"]
                    arguments = json.loads(function["arguments"])
                    call_id = tool_call_data.get("id")
                    tool_call = ToolCall(
                        name=function["name"],
                        arguments=arguments,
                        call_id=call_id,
                    )
                    tool_calls.append(tool_call)
                except (KeyError, json.JSONDecodeError):
                    continue
        
        # 如果没有多工具调用，尝试单工具调用
        if not tool_calls:
            try:
                tool_call = self.parse_llm_response(response)
                tool_calls.append(tool_call)
            except ValueError:
                pass
        
        return tool_calls



class ToolFormatter(IToolFormatter):
    """工具格式化器（简化版本）

    根据模型能力自动选择合适的格式化策略，只支持function_calling和jsonl。
    """

    def __init__(self) -> None:
        """初始化工具格式化器"""
        self.function_calling_formatter = FunctionCallingFormatter()
        self.jsonl_formatter = JsonlFormatter()

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
        # 优先检测Function Calling支持
        if llm_client.supports_function_calling():
            return "function_calling"
        # 否则使用JSONL
        else:
            return "jsonl"

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
            # 如果失败，尝试JSONL解析
            try:
                result = self.jsonl_formatter.parse_llm_response(response)
                return result
            except ValueError:
                # 如果都失败，抛出异常
                raise ValueError("无法解析LLM响应为工具调用")

    def parse_llm_response_batch(self, response: IBaseMessage) -> List[ToolCall]:
        """解析LLM的工具调用响应（批量）

        Args:
            response: LLM响应消息

        Returns:
            List[ToolCall]: 解析后的工具调用列表

        Raises:
            ValueError: 响应格式不正确
        """
        # 首先尝试Function Calling解析（多工具调用）
        try:
            if hasattr(response, "additional_kwargs") and "tool_calls" in response.additional_kwargs:
                tool_calls_data = response.additional_kwargs["tool_calls"]
                tool_calls = []
                for tool_call_data in tool_calls_data:
                    function = tool_call_data["function"]
                    arguments = json.loads(function["arguments"])
                    tool_call = ToolCall(
                        name=function["name"],
                        arguments=arguments,
                        call_id=tool_call_data.get("id")
                    )
                    tool_calls.append(tool_call)
                return tool_calls
        except (ValueError, KeyError, json.JSONDecodeError):
            pass

        # 尝试JSONL批量解析
        try:
            return self.jsonl_formatter.parse_llm_response_batch(response)
        except ValueError:
            pass

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
        elif strategy == "jsonl":
            result = self.jsonl_formatter.format_for_llm(tools)
            return result
        else:
            raise ValueError(f"不支持的格式化策略: {strategy}")

    def parse_llm_response_batch_with_strategy(
        self, response: "IBaseMessage", strategy: str
    ) -> List[ToolCall]:
        """使用指定策略解析LLM响应（批量）

        Args:
            response: LLM响应消息
            strategy: 格式化策略

        Returns:
            List[ToolCall]: 解析后的工具调用列表

        Raises:
            ValueError: 不支持的策略或解析失败
        """
        if strategy == "function_calling":
            return self.function_calling_formatter.parse_llm_response_batch(response)
        elif strategy == "jsonl":
            return self.jsonl_formatter.parse_llm_response_batch(response)
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
        elif strategy == "jsonl":
            result = self.jsonl_formatter.parse_llm_response(response)
            return result
        else:
            raise ValueError(f"不支持的格式化策略: {strategy}")


class JsonlFormatter(IToolFormatter):
    """JSONL格式化策略

    将工具格式化为JSONL格式，支持批量工具调用。
    """

    def format_for_llm(self, tools: Sequence[ITool]) -> Dict[str, Any]:
        """将工具格式化为LLM可识别的JSONL格式

        Args:
            tools: 工具列表

        Returns:
            Dict[str, Any]: 格式化后的工具描述
        """
        tool_schemas = []
        for tool in tools:
            schema = {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.get_schema(),
            }
            tool_schemas.append(schema)

        # 生成JSONL格式的提示词
        prompt = f"""
请按以下JSONL格式调用工具（每行一个JSON对象）：
{{"name": "工具名称", "parameters": {{"参数1": "值1", "参数2": "值2"}}}}
{{"name": "工具名称", "parameters": {{"参数1": "值1", "参数2": "值2"}}}}

可用工具：
{chr(10).join([f"- {tool.name}: {tool.description}" for tool in tools])}

请只返回JSONL格式的工具调用，每行一个JSON对象，不要包含其他文本。
""".strip()

        return {"prompt": prompt, "tools": tool_schemas}

    def detect_strategy(self, llm_client: ILLMClient) -> str:
        """检测模型支持的输出策略

        Args:
            llm_client: LLM客户端实例

        Returns:
            str: 策略类型
        """
        # JSONL格式化器总是返回jsonl策略
        return "jsonl"

    def parse_llm_response(self, response: IBaseMessage) -> ToolCall:
        """解析LLM的JSONL工具调用响应

        Args:
            response: LLM响应消息

        Returns:
            ToolCall: 解析后的工具调用（返回第一个有效的工具调用）

        Raises:
            ValueError: 响应格式不正确
        """
        # 先尝试批量解析，返回第一个有效的工具调用
        tool_calls = self.parse_llm_response_batch(response)
        if tool_calls:
            return tool_calls[0]
        
        raise ValueError(f"无法从响应中解析JSONL格式的工具调用: {response.content}")

    def parse_llm_response_batch(self, response: IBaseMessage) -> List[ToolCall]:
        """解析LLM的JSONL工具调用响应（批量）

        Args:
            response: LLM响应消息

        Returns:
            List[ToolCall]: 解析后的工具调用列表

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

        tool_calls: List[ToolCall] = []

        # 尝试解析JSONL格式（每行一个JSON对象）
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            try:
                data = json.loads(line)
                if "name" in data and "parameters" in data:
                    arguments: Dict[str, Any] = data["parameters"]
                    call_id: Optional[str] = data.get("call_id")
                    tool_call = ToolCall(
                        name=data["name"],
                        arguments=arguments,
                        call_id=call_id,
                    )
                    tool_calls.append(tool_call)
                    logger.debug(f"成功解析第{line_num}行JSONL工具调用: {data['name']}")
            except json.JSONDecodeError as e:
                logger.warning(f"第{line_num}行JSONL解析失败: {line}, 错误: {e}")
                continue

        # 如果JSONL解析失败，尝试单行JSON解析（向后兼容）
        if not tool_calls:
            try:
                # 查找JSON对象
                json_match = re.search(r"\{.*\}", content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    data = json.loads(json_str)
                    if "name" in data and "parameters" in data:
                        arguments: Dict[str, Any] = data["parameters"]
                        call_id: Optional[str] = data.get("call_id")
                        tool_call = ToolCall(
                            name=data["name"],
                            arguments=arguments,
                            call_id=call_id,
                        )
                        tool_calls.append(tool_call)
                        logger.debug("回退到单JSON解析成功")
            except (json.JSONDecodeError, AttributeError) as e:
                logger.warning(f"单JSON解析也失败: {e}")

        if not tool_calls:
            raise ValueError(f"无法从响应中解析JSONL格式的工具调用: {content}")

        return tool_calls