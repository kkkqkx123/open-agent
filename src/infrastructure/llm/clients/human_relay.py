"""HumanRelay LLM客户端实现"""

import asyncio
from typing import List, Dict, Any, Optional, AsyncGenerator, Generator, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage

from .base import BaseLLMClient
from ..config import HumanRelayConfig
from ..models import LLMResponse, TokenUsage
from ..frontend_interface import create_frontend_interface
from ..frontend_interface_enhanced import create_enhanced_frontend_interface
from ..exceptions import LLMTimeoutError, LLMInvalidRequestError


class HumanRelayClient(BaseLLMClient):
    """HumanRelay LLM客户端实现 - 通过前端与Web LLM交互"""
    
    def __init__(self, config: HumanRelayConfig) -> None:
        """
        初始化HumanRelay客户端
        
        Args:
            config: HumanRelay配置
        """
        super().__init__(config)
        self.mode = config.mode  # "single" 或 "multi"
        
        # 选择前端接口实现
        use_enhanced = config.metadata_config.get('use_enhanced_frontend', False)
        
        if use_enhanced:
            self.frontend_interface = create_enhanced_frontend_interface(config.frontend_config)
        else:
            self.frontend_interface = create_frontend_interface(config.frontend_config)
        
        self.conversation_history: List[BaseMessage] = []
        self.max_history_length = config.max_history_length
        self.prompt_template = config.prompt_template
        self.incremental_prompt_template = config.incremental_prompt_template
    
    async def _do_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作"""
        if self.mode == "single":
            return await self._single_turn_generate(messages, parameters, **kwargs)
        else:
            return await self._multi_turn_generate(messages, parameters, **kwargs)
    
    def _do_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行生成操作"""
        # 同步版本，使用asyncio运行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self._do_generate_async(messages, parameters, **kwargs)
            )
        finally:
            loop.close()
    
    async def _single_turn_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """单轮对话模式"""
        # 构建完整提示词
        full_prompt = self._build_full_prompt(messages)
        
        # 获取超时设置
        timeout = self._get_timeout(parameters)
        
        # 通过前端交互
        try:
            user_response = await self.frontend_interface.wait_with_timeout(
                self.frontend_interface.prompt_user(
                    prompt=full_prompt,
                    mode="single",
                    parameters=parameters,
                    **kwargs
                ),
                timeout=timeout
            )
        except LLMTimeoutError:
            raise LLMTimeoutError(f"单轮对话超时（{timeout}秒）", timeout=timeout)
        
        # 创建响应
        return self._create_human_relay_response(user_response, messages)
    
    async def _multi_turn_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """多轮对话模式"""
        # 更新对话历史
        self._update_conversation_history(messages)
        
        # 构建增量提示词
        incremental_prompt = self._build_incremental_prompt(messages)
        
        # 获取超时设置
        timeout = self._get_timeout(parameters)
        
        # 通过前端交互
        try:
            user_response = await self.frontend_interface.wait_with_timeout(
                self.frontend_interface.prompt_user(
                    prompt=incremental_prompt,
                    mode="multi",
                    conversation_history=self.conversation_history,
                    parameters=parameters,
                    **kwargs
                ),
                timeout=timeout
            )
        except LLMTimeoutError:
            raise LLMTimeoutError(f"多轮对话超时（{timeout}秒）", timeout=timeout)
        
        # 创建响应
        return self._create_human_relay_response(user_response, messages)
    
    def _build_full_prompt(self, messages: Sequence[BaseMessage]) -> str:
        """构建完整提示词"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")
        
        # 格式化消息为文本
        formatted_messages = self._format_messages(messages)
        
        # 使用模板
        return self.prompt_template.format(prompt=formatted_messages)
    
    def _build_incremental_prompt(self, messages: Sequence[BaseMessage]) -> str:
        """构建增量提示词"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")
        
        # 格式化新消息
        formatted_messages = self._format_messages(messages)
        
        # 格式化对话历史
        formatted_history = self.frontend_interface.format_conversation_history(
            self.conversation_history
        )
        
        # 使用模板
        return self.incremental_prompt_template.format(
            incremental_prompt=formatted_messages,
            conversation_history=formatted_history
        )
    
    def _format_messages(self, messages: Sequence[BaseMessage]) -> str:
        """格式化消息为文本"""
        formatted_lines = []
        for message in messages:
            role = "用户" if message.type == "human" else "AI"
            content = str(message.content)
            formatted_lines.append(f"{role}: {content}")
        
        return "\n".join(formatted_lines)
    
    def _update_conversation_history(self, messages: Sequence[BaseMessage]) -> None:
        """更新对话历史"""
        self.conversation_history.extend(messages)
        
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            # 保留最新的消息
            self.conversation_history = self.conversation_history[-self.max_history_length:]
    
    def _create_human_relay_response(
        self, user_response: str, original_messages: Sequence[BaseMessage]
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
                "frontend_type": self.frontend_interface.interface_type
            }
        )
    
    def _estimate_token_usage(
        self, response: str, messages: Sequence[BaseMessage]
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
        
        return self.frontend_interface.validate_timeout(timeout)
    
    async def _do_stream_generate_async(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        # HumanRelay不支持真正的流式生成，但可以模拟
        response = await self._do_generate_async(messages, parameters, **kwargs)
        
        # 按字符流式输出
        for char in response.content:
            yield char
            await asyncio.sleep(0.01)  # 模拟流式延迟
    
    def _do_stream_generate(
        self, messages: Sequence[BaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        # 检查是否已经在事件循环中
        try:
            loop = asyncio.get_running_loop()
            # 如果已经在事件循环中，使用run_coroutine_threadsafe或创建新线程
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    response = new_loop.run_until_complete(
                        self._do_generate_async(messages, parameters, **kwargs)
                    )
                    return response
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                response = future.result()
        except RuntimeError:
            # 没有运行的事件循环，可以使用原来的方法
            response = self._do_generate(messages, parameters, **kwargs)
        
        # 按字符流式输出
        for char in response.content:
            yield char
    
    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        # 简单估算
        return max(len(text) // 4, 1)
    
    def get_messages_token_count(self, messages: Sequence[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        total_text = "\n".join([str(msg.content) for msg in messages])
        return self.get_token_count(total_text)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 从配置中读取是否支持函数调用
        return getattr(self.config, 'function_calling_supported', True)
    
    def clear_conversation_history(self) -> None:
        """清除对话历史"""
        self.conversation_history.clear()
    
    def get_conversation_history(self) -> List[BaseMessage]:
        """获取对话历史"""
        return self.conversation_history.copy()
    
    def set_conversation_history(self, history: List[BaseMessage]) -> None:
        """设置对话历史"""
        self.conversation_history = history.copy()
        # 限制历史长度
        if len(self.conversation_history) > self.max_history_length:
            self.conversation_history = self.conversation_history[-self.max_history_length:]