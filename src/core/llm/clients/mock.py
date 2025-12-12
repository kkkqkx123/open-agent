"""Mock LLM客户端实现（用于测试）"""

import random
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator, Union, Sequence

from src.interfaces.messages import IBaseMessage
from src.infrastructure.messages.types import HumanMessage, AIMessage, SystemMessage

from .base import BaseLLMClient
from src.interfaces.llm import LLMResponse
from src.infrastructure.llm.models import TokenUsage
from src.core.config.models import MockConfig, LLMConfig
from src.interfaces.llm.exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
)


class MockLLMClient(BaseLLMClient[MockConfig]):
    """Mock LLM客户端实现，用于测试"""

    def __init__(self, config: Union[MockConfig, LLMConfig]) -> None:
        """
        初始化Mock客户端

        Args:
            config: Mock配置或LLM客户端配置
        """
        super().__init__(config)  # type: ignore

        # 处理不同类型的配置
        if isinstance(config, MockConfig):
            # Mock特定配置
            self.response_delay = config.response_delay
            self.error_rate = config.error_rate
            self.error_types = config.error_types
        else:
            # 从LLMConfig中提取Mock特定配置，使用默认值
            self.response_delay = getattr(config, "response_delay", 0.1)
            self.error_rate = getattr(config, "error_rate", 0.0)
            self.error_types = getattr(config, "error_types", ["timeout", "rate_limit"])

        # 预定义的响应模板
        self._response_templates = {
            "default": "这是一个模拟的LLM响应。",
            "coding": "这是一个代码生成的模拟响应：\n```python\ndef hello_world():\n    print('Hello, World!')\n```",
            "analysis": "这是一个数据分析的模拟响应：根据提供的数据，我得出以下结论...",
            "creative": "这是一个创意写作的模拟响应：在遥远的星球上，有一个充满奇迹的世界...",
            "translation": "这是一个翻译的模拟响应：Hello, World! -> 你好，世界！",
        }

    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        # 模拟响应延迟
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

        # 模拟错误
        self._maybe_throw_error()

        # 生成响应内容
        content = self._generate_response_content(messages, parameters)

        # 估算Token使用情况
        token_usage = self._estimate_token_usage(content)

        # 创建响应对象
        return self._create_response(
            content=content,
            message=AIMessage(content=content),
            token_usage=token_usage,
            finish_reason="stop",
        )

    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator() -> AsyncGenerator[str, None]:
            try:
                # 模拟错误
                self._maybe_throw_error()

                # 生成完整响应
                content = self._generate_response_content(messages, parameters)

                # 确保有多个chunk，即使内容很短也要分割
                # 总是按字符分割以确保有多个chunk
                for i, char in enumerate(content):
                    # 模拟延迟
                    if self.response_delay > 0:
                        await asyncio.sleep(self.response_delay / len(content))
                    yield char

            except Exception as e:
                raise self._handle_mock_error(e)

        return _async_generator()


    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)

    def _generate_response_content(
        self, messages: Sequence[IBaseMessage], parameters: Optional[Dict[str, Any]] = None
    ) -> str:
        """生成响应内容"""
        if not messages:
            return self._response_templates["default"]

        # 获取最后一条消息的内容
        last_message = messages[-1]
        content = str(last_message.content).lower()

        # 根据参数调整响应内容
        response_content = self._get_base_response(content)

        # 只在非测试环境下添加参数信息
        if parameters and getattr(self, "_include_params_in_response", False):
            # 根据参数调整响应
            if parameters.get("temperature", 0.7) > 0.8:
                response_content += " [高温度随机响应]"
            elif parameters.get("temperature", 0.7) < 0.3:
                response_content += " [低温度确定性响应]"

            if parameters.get("max_tokens"):
                response_content += f" [最大token限制: {parameters['max_tokens']}]"

            if parameters.get("top_p"):
                response_content += f" [Top-P: {parameters['top_p']}]"

            if parameters.get("top_k"):
                response_content += f" [Top-K: {parameters['top_k']}]"

            if parameters.get("frequency_penalty", 0) != 0:
                response_content += f" [频率惩罚: {parameters['frequency_penalty']}]"

            if parameters.get("presence_penalty", 0) != 0:
                response_content += f" [存在惩罚: {parameters['presence_penalty']}]"

            if parameters.get("stop"):
                response_content += f" [停止序列: {parameters['stop']}]"

            if parameters.get("stop_sequences"):
                response_content += f" [停止序列: {parameters['stop_sequences']}]"

            if parameters.get("tool_choice"):
                response_content += f" [工具选择: {parameters['tool_choice']}]"

            if parameters.get("response_format"):
                response_content += f" [响应格式: {parameters['response_format']}]"

            if parameters.get("system"):
                response_content += f" [系统指令: {parameters['system']}]"

            if parameters.get("system_instruction"):
                response_content += f" [系统指令: {parameters['system_instruction']}]"

            if parameters.get("thinking_config"):
                response_content += f" [思考配置: {parameters['thinking_config']}]"

            if parameters.get("reasoning"):
                response_content += f" [推理配置: {parameters['reasoning']}]"

            if parameters.get("verbosity"):
                response_content += f" [详细程度: {parameters['verbosity']}]"

            if parameters.get("candidate_count"):
                response_content += f" [候选数量: {parameters['candidate_count']}]"

            if parameters.get("response_mime_type"):
                response_content += (
                    f" [响应MIME类型: {parameters['response_mime_type']}]"
                )

            if parameters.get("safety_settings"):
                response_content += f" [安全设置: {parameters['safety_settings']}]"

            if parameters.get("service_tier"):
                response_content += f" [服务层: {parameters['service_tier']}]"

            if parameters.get("safety_identifier"):
                response_content += f" [安全标识符: {parameters['safety_identifier']}]"

            if parameters.get("store"):
                response_content += " [存储: 启用]"

            if parameters.get("web_search_options"):
                response_content += (
                    f" [网络搜索选项: {parameters['web_search_options']}]"
                )

            if parameters.get("seed"):
                response_content += f" [种子: {parameters['seed']}]"

            if parameters.get("user"):
                response_content += f" [用户: {parameters['user']}]"

        return response_content

    def _get_base_response(self, content: str) -> str:
        """根据内容选择基础响应模板"""
        if (
            "代码" in content
            or "code" in content
            or "编程" in content
            or "函数" in content
        ):
            return self._response_templates["coding"]
        elif "分析" in content or "analysis" in content or "数据" in content:
            return self._response_templates["analysis"]
        elif "创意" in content or "creative" in content or "写作" in content:
            return self._response_templates["creative"]
        elif "翻译" in content or "translation" in content or "translate" in content:
            return self._response_templates["translation"]
        else:
            return self._response_templates["default"]

    def _estimate_token_usage(self, content: str) -> TokenUsage:
        """估算Token使用情况"""
        # 简单估算：使用字符数除以4作为token数（常见的估算方法）
        content_tokens = len(content) // 4

        # 估算输入token（假设输入和输出长度相似）
        prompt_tokens = max(content_tokens, 10)

        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=content_tokens,
            total_tokens=prompt_tokens + content_tokens,
        )

    def _maybe_throw_error(self) -> None:
        """根据错误率随机抛出错误"""
        if self.error_rate <= 0:
            return

        if random.random() < self.error_rate:
            # 随机选择一个错误类型
            error_type = random.choice(self.error_types)

            if error_type == "timeout":
                raise LLMTimeoutError("模拟超时错误", timeout=self.config.timeout)
            elif error_type == "rate_limit":
                raise LLMRateLimitError("模拟频率限制错误", retry_after=60)
            elif error_type == "service_unavailable":
                raise LLMServiceUnavailableError("模拟服务不可用错误")
            else:
                raise LLMInvalidRequestError(f"模拟{error_type}错误")

    def _handle_mock_error(self, error: Exception) -> Exception:
        """处理Mock错误"""
        # 如果已经是LLM错误，直接返回
        if isinstance(
            error,
            (
                LLMTimeoutError,
                LLMRateLimitError,
                LLMServiceUnavailableError,
                LLMInvalidRequestError,
            ),
        ):
            return error

        # 否则包装为通用错误
        return LLMInvalidRequestError(f"Mock错误: {str(error)}")

    def set_response_template(self, key: str, template: str) -> None:
        """设置响应模板"""
        self._response_templates[key] = template

    def get_response_template(self, key: str) -> Optional[str]:
        """获取响应模板"""
        return self._response_templates.get(key)

    def set_error_rate(self, error_rate: float) -> None:
        """设置错误率"""
        if 0 <= error_rate <= 1:
            self.error_rate = error_rate
        else:
            raise ValueError("错误率必须在0到1之间")

    def set_response_delay(self, delay: float) -> None:
        """设置响应延迟"""
        if delay >= 0:
            self.response_delay = delay
        else:
            raise ValueError("响应延迟必须大于等于0")

    def _validate_messages(self, messages: Sequence[IBaseMessage]) -> None:
        """验证消息列表（Mock客户端允许空消息列表）"""
        # Mock客户端允许空消息列表，用于测试
        pass
