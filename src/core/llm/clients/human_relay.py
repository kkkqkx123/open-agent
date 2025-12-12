"""HumanRelay LLM客户端实现"""

import asyncio
from typing import List, Dict, Any, AsyncGenerator, Sequence, cast
from src.interfaces.messages import IBaseMessage
from src.infrastructure.messages.types import HumanMessage, AIMessage

from .base import BaseLLMClient
from src.core.config.models import HumanRelayConfig
from src.infrastructure.llm.models import TokenUsage
from src.interfaces.llm.exceptions import LLMTimeoutError, LLMInvalidRequestError
from src.interfaces.llm import LLMResponse


class HumanRelayClient(BaseLLMClient[HumanRelayConfig]):
    """HumanRelay LLM客户端实现 - 通过前端与Web LLM交互"""
    
    def __init__(self, config: HumanRelayConfig) -> None:
        """
        初始化HumanRelay客户端
        
        Args:
            config: HumanRelay配置
        """
        super().__init__(config)
        self.mode = config.mode  # "single" 或 "multi"
        self.conversation_history: List[IBaseMessage] = []
        self.max_history_length = config.max_history_length
        self.prompt_template = config.prompt_template
        self.incremental_prompt_template = config.incremental_prompt_template
    
    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        if self.mode == "single":
            return await self._single_turn_generate(messages, parameters, **kwargs)
        else:
            return await self._multi_turn_generate(messages, parameters, **kwargs)
    
    def _do_generate(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        # 使用EventLoopManager运行异步方法
        from core.common.async_utils import run_async  # type: ignore
        result = run_async(self._do_generate_async(messages, parameters, **kwargs))
        return cast(LLMResponse, result)
    
    async def _single_turn_generate(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """单轮对话模式"""
        # 构建完整提示词
        full_prompt = self._build_full_prompt(messages)
        
        # 获取超时设置
        timeout = self._get_timeout(parameters)
        
        # 通过前端交互 - 模拟实现
        try:
            # 这里需要实际的前端接口实现，暂时返回模拟响应
            user_response = f"模拟响应: {full_prompt[:100]}..."  # 模拟用户响应
        except LLMTimeoutError:
            raise LLMTimeoutError(f"单轮对话超时（{timeout}秒）", timeout=timeout)
        
        # 创建响应
        return self._create_human_relay_response(user_response, messages)
    
    async def _multi_turn_generate(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """多轮对话模式"""
        # 更新对话历史
        self._update_conversation_history(messages)
        
        # 构建增量提示词
        incremental_prompt = self._build_incremental_prompt(messages)
        
        # 获取超时设置
        timeout = self._get_timeout(parameters)
        
        # 通过前端交互 - 模拟实现
        try:
            # 这里需要实际的前端接口实现，暂时返回模拟响应
            user_response = f"模拟响应: {incremental_prompt[:100]}..."  # 模拟用户响应
        except LLMTimeoutError:
            raise LLMTimeoutError(f"多轮对话超时（{timeout}秒）", timeout=timeout)
        
        # 创建响应
        return self._create_human_relay_response(user_response, messages)
    
    def _build_full_prompt(self, messages: Sequence[IBaseMessage]) -> str:
        """构建完整提示词"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")
        
        # 格式化消息为文本
        formatted_messages = self._format_messages(messages)
        
        # 使用模板
        if self.prompt_template:
            return self.prompt_template.format(prompt=formatted_messages)
        return formatted_messages
    
    def _build_incremental_prompt(self, messages: Sequence[IBaseMessage]) -> str:
        """构建增量提示词"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")
        
        # 格式化新消息
        formatted_messages = self._format_messages(messages)
        
        # 格式化对话历史 - 模拟实现
        formatted_history = "\n".join([f"{msg.type}: {msg.content}" for msg in self.conversation_history])
        
        # 使用模板
        if self.incremental_prompt_template:
            return self.incremental_prompt_template.format(
                incremental_prompt=formatted_messages,
                conversation_history=formatted_history
            )
        return formatted_messages
    
    def _format_messages(self, messages: Sequence[IBaseMessage]) -> str:
        """格式化消息为文本"""
        formatted_lines = []
        for message in messages:
            role = "用户" if message.type == "human" else "AI"
            content = str(message.content)
            formatted_lines.append(f"{role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def _update_conversation_history(self, messages: Sequence[IBaseMessage]) -> None:
        """更新对话历史"""
        self.conversation_history.extend(messages)
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            # 保留最新的消息
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _create_human_relay_response(
        self, user_response: str, original_messages: Sequence[IBaseMessage]
    ) -> LLMResponse:
        """创建HumanRelay响应"""
        # 创建AI消息
        ai_message = AIMessage(content=user_response)
        
        # 估算Token使用情况
        token_usage = self._estimate_token_usage(user_response, original_messages)
        
        # 创建响应对象
        return self._create_response(
            content=user_response,
            message=ai_message,
            token_usage=token_usage,
            finish_reason="stop",
            metadata={
                "mode": self.mode,
                "history_length": len(self.conversation_history),
                "frontend_type": "human_relay"  # 使用固定值，因为frontend_interface不存在
            }
        )
    
    def _estimate_token_usage(
        self, response: str, messages: Sequence[IBaseMessage]
    ) -> TokenUsage:
        """估算Token使用情况"""
        # 简单估算：按字符数除以4估算token数
        response_tokens = max(len(response) // 4, 1)
        
        # 估算输入token
        input_text = "\n".join([str(msg.content) for msg in messages])
        prompt_tokens = max(len(input_text) // 4, 1)
        
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=response_tokens,
            total_tokens=prompt_tokens + response_tokens,
        )
    
    def _get_timeout(self, parameters: Dict[str, Any]) -> int:
        """获取超时设置"""
        # 优先级：参数 > 配置 > 默认值
        timeout = parameters.get('frontend_timeout')
        if timeout is None:
            timeout = self.config.metadata_config.get('frontend_timeout', 300)
        
        # 返回验证后的超时值，限制在合理范围内
        return cast(int, max(10, min(timeout, 3600)))  # 限制在10秒到1小时之间
    
    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator() -> AsyncGenerator[str, None]:
            # HumanRelay不支持真正的流式生成，但可以模拟
            response = await self._do_generate_async(messages, parameters, **kwargs)
            
            # 按字符流式输出
            for char in response.content:
                yield char
                await asyncio.sleep(0.01)  # 模拟流式延迟

        return _async_generator()
    
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)
    
    def clear_conversation_history(self) -> None:
        """清除对话历史"""
        self.conversation_history.clear()
    
    def get_conversation_history(self) -> List[IBaseMessage]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def set_conversation_history(self, history: List[IBaseMessage]) -> None:
        """设置对话历史"""
        self.conversation_history = history.copy()
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]