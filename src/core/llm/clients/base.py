"""LLM客户端基类"""

import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator, Sequence, TypeVar, Generic

from src.interfaces.messages import IBaseMessage

from src.interfaces.llm import ILLMClient, ILLMCallHook, LLMResponse
from src.infrastructure.llm.models import TokenUsage, LLMError, ModelInfo
from typing import Dict, Any, Optional

# 使用核心层的配置
from src.core.config.models import LLMConfig
from src.interfaces.llm.exceptions import (
    LLMCallError,
    LLMModelNotFoundError,
    LLMInvalidRequestError,
    LLMTokenLimitError,
)

# 定义配置类型变量(服务于范型)
ConfigType = TypeVar('ConfigType', bound=LLMConfig)


class BaseLLMClient(ILLMClient, Generic[ConfigType]):
    """LLM客户端基类"""

    def __init__(self, config: ConfigType) -> None:
        """
        初始化客户端

        Args:
            config: 客户端配置
        """
        self.config: ConfigType = config
        self._hooks: List[ILLMCallHook] = []
        self._model_info: Optional[ModelInfo] = None

    def add_hook(self, hook: ILLMCallHook) -> None:
        """
        添加调用钩子

        Args:
            hook: 钩子实例
        """
        self._hooks.append(hook)

    def remove_hook(self, hook: ILLMCallHook) -> None:
        """
        移除调用钩子

        Args:
            hook: 钩子实例
        """
        if hook in self._hooks:
            self._hooks.remove(hook)

    def clear_hooks(self) -> None:
        """清除所有钩子"""
        self._hooks.clear()

    def _call_before_hooks(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用前置钩子"""
        for hook in self._hooks:
            try:
                # 类型转换：IBaseMessage -> BaseMessage，用于hooks接口兼容
                hook.before_call(messages, parameters, **kwargs)
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook before_call failed: {e}")

    def _call_after_hooks(
        self,
        response: LLMResponse,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> None:
        """调用后置钩子"""
        for hook in self._hooks:
            try:
                hook.after_call(response, messages, parameters, **kwargs)
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook after_call failed: {e}")

    def _call_error_hooks(
        self,
        error: Exception,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> Optional[LLMResponse]:
        """调用错误钩子"""
        for hook in self._hooks:
            try:
                response = hook.on_error(error, messages, parameters, **kwargs)
                if response is not None:
                    return response
            except Exception as e:
                # 钩子错误不应该影响主流程
                print(f"Warning: Hook on_error failed: {e}")

        return None

    def _measure_time(self, func: Any, *args: Any, **kwargs: Any) -> tuple[LLMResponse, float]:
        """测量函数执行时间"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            return result, end_time - start_time
        except Exception as e:
            end_time = time.time()
            raise e

    def _handle_api_error(self, error: Exception) -> LLMCallError:
        """处理API错误"""
        # 从基础设施层导入错误处理器
        from ....infrastructure.error_management.impl.llm import ErrorHandlerFactory, ErrorContext

        # 创建错误上下文
        context = ErrorContext(
            model_name=self.config.model_name, model_type=self.config.model_type
        )

        # 使用错误处理器处理错误
        error_handler = ErrorHandlerFactory.create_handler(self.config.model_type)
        llm_error = error_handler.handle_error(error, context.to_dict())
        
        # 保留原始错误信息
        if not hasattr(llm_error, 'original_error') or llm_error.original_error is None:
            llm_error.original_error = error
        if not hasattr(llm_error, 'error_context') or llm_error.error_context is None:
            llm_error.error_context = context.to_dict()
            
        return llm_error
    
    def _create_enhanced_error(
        self,
        error_class: type[LLMCallError],
        message: str,
        original_error: Exception,
        **kwargs: Any
    ) -> LLMCallError:
        """创建增强的错误对象，保留原始错误信息"""
        # 对于LLMModelNotFoundError，model_name是位置参数，不需要在kwargs中传递
        if error_class is LLMModelNotFoundError:
            error: LLMCallError = error_class(self.config.model_name)
            # 覆盖默认消息
            error.args = (message,)
        else:
            # 对于其他异常，model_name作为关键字参数传递
            error = error_class(message, model_name=self.config.model_name, **kwargs)
        
        error.original_error = original_error
        error.error_type = type(original_error).__name__
        return error

    def _create_response(
        self,
        content: str,
        message: Any = None,
        token_usage: Optional[TokenUsage] = None,
        finish_reason: Optional[str] = None,
        function_call: Optional[Dict[str, Any]] = None,
        response_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """创建响应对象"""
        # 使用接口定义的LLMResponse结构
        return LLMResponse(
            content=content,
            model=self.config.model_name,
            finish_reason=finish_reason,
            tokens_used=token_usage.total_tokens if token_usage else None,
            metadata=metadata or {},
        )

    def _merge_parameters(self, parameters: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """合并参数"""
        # 基础参数
        merged: Dict[str, Any] = {
            "temperature": self.config.temperature,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
        }

        # 添加max_tokens
        if self.config.max_tokens:
            merged["max_tokens"] = self.config.max_tokens

        # 添加函数调用参数
        if self.config.functions:
            merged["functions"] = self.config.functions

        if self.config.function_call:
            merged["function_call"] = self.config.function_call

        # 合并传入的参数
        if parameters:
            merged.update(parameters)

        return merged
    
    def _extract_system_message(self, messages: Sequence[IBaseMessage]) -> Optional[str]:
        """提取系统消息内容"""
        from src.infrastructure.messages.types import SystemMessage
        
        for message in messages:
            if isinstance(message, SystemMessage):
                # 确保返回字符串类型
                content = message.content
                if isinstance(content, str):
                    return content
                elif isinstance(content, list):
                    # 如果是列表，转换为字符串
                    return str(content)
        return None
    
    def _prepare_parameters_with_system_message(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Dict[str, Any]
    ) -> tuple[Sequence[IBaseMessage], Dict[str, Any]]:
        """准备参数，包括系统消息处理"""
        # 提取系统消息
        system_message = self._extract_system_message(messages)
        
        # 如果有系统消息，添加到参数中
        params = parameters.copy()
        if system_message:
            params["system"] = system_message
            
        return messages, params
    
    def _extract_function_call_enhanced(self, response: Any) -> Optional[Dict[str, Any]]:
        """增强的函数调用信息提取，使用类型安全的接口"""
        # 使用类型安全的接口检查tool_calls
        if hasattr(response, "has_tool_calls") and callable(response.has_tool_calls):
            if response.has_tool_calls():
                tool_calls = response.get_tool_calls()
                if tool_calls:
                    # 使用基础设施层的解析器解析工具调用
                    from src.infrastructure.messages.tool_call_parser import ToolCallParser
                    
                    # 标准化工具调用数据
                    normalized_calls = [
                        ToolCallParser.normalize_tool_call_data(call)
                        for call in tool_calls
                    ]
                    if normalized_calls:
                        return normalized_calls[0]
        
        return None

    def _validate_messages(self, messages: Sequence[IBaseMessage]) -> None:
        """验证消息列表"""
        if not messages:
            raise LLMInvalidRequestError("消息列表不能为空")

        # 检查消息内容
        for i, message in enumerate(messages):
            if not hasattr(message, "content") or not message.content:
                raise LLMInvalidRequestError(f"消息 {i} 缺少内容")

    def _validate_token_limit(self, messages: Sequence[IBaseMessage]) -> None:
        """验证Token限制"""
        # 如果配置中没有设置max_tokens，则跳过验证
        if not self.config.max_tokens:
            return
            
        try:
            # 通过依赖注入获取Token计算服务提供者
            from src.interfaces.dependency_injection import calculate_messages_tokens
            
            # 计算消息列表的token数量
            token_count = calculate_messages_tokens(
                messages,
                self.config.model_type,
                self.config.model_name
            )
            
            # 检查是否超过限制
            if token_count > self.config.max_tokens:
                raise LLMTokenLimitError(
                    message=f"Token数量超过限制: {token_count} > {self.config.max_tokens}",
                    token_count=token_count,
                    limit=self.config.max_tokens,
                    model_name=self.config.model_name
                )
                
        except Exception as e:
            # 如果是TokenLimitError，直接抛出
            if isinstance(e, LLMTokenLimitError):
                raise
                
            # 对于其他错误（如服务不可用），记录警告但不阻止请求
            # 这确保了即使token计算服务不可用，系统仍能正常工作
            print(f"Warning: Token验证失败，继续执行请求: {e}")

    async def generate(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        生成文本响应（异步）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Returns:
            LLMResponse: 生成的响应
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 测量执行时间
            start_time = time.time()
            response = await self._do_generate_async(messages, merged_params, **kwargs)
            response_time = time.time() - start_time

            # 调用后置钩子
            self._call_after_hooks(response, messages, merged_params, **kwargs)

            return response

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                return fallback_response

            # 抛出错误
            raise llm_error

    async def stream_generate(  # type: ignore[override]
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本响应（异步）

        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数

        Yields:
            str: 生成的文本片段
        """
        # 验证输入
        self._validate_messages(messages)
        self._validate_token_limit(messages)

        # 合并参数
        merged_params = self._merge_parameters(parameters)

        # 调用前置钩子
        self._call_before_hooks(messages, merged_params, **kwargs)

        try:
            # 调用内部异步流式生成方法
            async for chunk in self._do_stream_generate_async(messages, merged_params, **kwargs):
                yield chunk

        except Exception as e:
            # 转换为LLM错误
            if not isinstance(e, LLMCallError):
                llm_error = self._handle_api_error(e)
            else:
                llm_error = e

            # 尝试通过钩子恢复
            fallback_response = self._call_error_hooks(
                llm_error, messages, merged_params, **kwargs
            )
            if fallback_response is not None:
                # 如果钩子返回了响应，则返回模拟的流式内容
                for chunk in fallback_response.content.split():
                    yield chunk + " "
            else:
                # 抛出错误
                raise llm_error

    @abstractmethod
    async def _do_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> LLMResponse:
        """执行异步生成操作（子类实现）"""
        pass

    @abstractmethod
    def _do_stream_generate_async(
        self, messages: Sequence[IBaseMessage], parameters: Dict[str, Any], **kwargs: Any
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作（子类实现）"""
        pass


    @abstractmethod
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用（子类实现）"""
        pass

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        if self._model_info is None:
            self._model_info = ModelInfo(
                name=self.config.model_name,
                type=self.config.model_type,
                supports_function_calling=self.supports_function_calling(),
                supports_streaming=True,
                metadata=self.config.metadata or {},
            )

        return self._model_info.to_dict()