"""Mock LLM客户端实现（用于测试）"""

import random
import time
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, Generator
from typing import Dict, Any, Optional, List, AsyncGenerator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

from .base import BaseLLMClient
from ..models import LLMResponse, TokenUsage
from ..config import MockConfig
from ..exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError
)


class MockLLMClient(BaseLLMClient):
    """Mock LLM客户端实现，用于测试"""
    
    def __init__(self, config: MockConfig) -> None:
        """
        初始化Mock客户端
        
        Args:
            config: Mock配置
        """
        super().__init__(config)
        
        # Mock特定配置
        self.response_delay = config.response_delay
        self.error_rate = config.error_rate
        self.error_types = config.error_types
        
        # 预定义的响应模板
        self._response_templates = {
            "default": "这是一个模拟的LLM响应。",
            "coding": "这是一个代码生成的模拟响应：\n```python\ndef hello_world():\n    print('Hello, World!')\n```",
            "analysis": "这是一个数据分析的模拟响应：根据提供的数据，我得出以下结论...",
            "creative": "这是一个创意写作的模拟响应：在遥远的星球上，有一个充满奇迹的世界...",
            "translation": "这是一个翻译的模拟响应：Hello, World! -> 你好，世界！"
        }
    
    def _do_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs
    ) -> LLMResponse:
        """执行生成操作"""
        # 模拟响应延迟
        if self.response_delay > 0:
            time.sleep(self.response_delay)
        
        # 模拟错误
        self._maybe_throw_error()
        
        # 生成响应内容
        content = self._generate_response_content(messages)
        
        # 估算Token使用情况
        token_usage = self._estimate_token_usage(content)
        
        # 创建响应对象
        return self._create_response(
            content=content,
            message=AIMessage(content=content),
            token_usage=token_usage,
            finish_reason="stop"
        )
    
    async def _do_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs
    ) -> LLMResponse:
        """执行异步生成操作"""
        # 模拟响应延迟
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)
        
        # 模拟错误
        self._maybe_throw_error()
        
        # 生成响应内容
        content = self._generate_response_content(messages)
        
        # 估算Token使用情况
        token_usage = self._estimate_token_usage(content)
        
        # 创建响应对象
        return self._create_response(
            content=content,
            message=AIMessage(content=content),
            token_usage=token_usage,
            finish_reason="stop"
        )
    
    def _do_stream_generate(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs
    ) -> Generator[str, None, None]:
        """执行流式生成操作"""
        try:
            # 模拟错误
            self._maybe_throw_error()
            
            # 生成完整响应
            content = self._generate_response_content(messages)
            
            # 模拟流式输出
            words = content.split()
            for i, word in enumerate(words):
                # 模拟延迟
                if self.response_delay > 0:
                    time.sleep(self.response_delay / len(words))
                
                # 输出单词（添加空格，除了最后一个）
                if i < len(words) - 1:
                    yield word + " "
                else:
                    yield word
                    
        except Exception as e:
            raise self._handle_mock_error(e)

    def _do_stream_generate_async(
        self,
        messages: List[BaseMessage],
        parameters: Dict[str, Any],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """执行异步流式生成操作"""
        async def _async_generator():
            try:
                # 模拟错误
                self._maybe_throw_error()
                
                # 生成完整响应
                content = self._generate_response_content(messages)
                
                # 模拟流式输出
                words = content.split()
                for i, word in enumerate(words):
                    # 模拟延迟
                    if self.response_delay > 0:
                        await asyncio.sleep(self.response_delay / len(words))
                    
                    # 输出单词（添加空格，除了最后一个）
                    if i < len(words) - 1:
                        yield word + " "
                    else:
                        yield word
                        
            except Exception as e:
                raise self._handle_mock_error(e)
        
        return _async_generator()
    
    def get_token_count(self, text: str) -> int:
        """计算文本的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("mock", self.config.model_name)
        return counter.count_tokens(text)
    
    def get_messages_token_count(self, messages: List[BaseMessage]) -> int:
        """计算消息列表的token数量"""
        from ..token_counter import TokenCounterFactory
        
        # 使用Token计算器
        counter = TokenCounterFactory.create_counter("mock", self.config.model_name)
        return counter.count_messages_tokens(messages)
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # Mock客户端支持函数调用
        return True
    
    def _generate_response_content(self, messages: List[BaseMessage]) -> str:
        """生成响应内容"""
        if not messages:
            return self._response_templates["default"]
        
        # 获取最后一条消息的内容
        last_message = messages[-1]
        content = str(last_message.content).lower()
        
        # 根据内容选择响应模板
        if "代码" in content or "code" in content or "编程" in content:
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
        # 简单估算
        content_tokens = self.get_token_count(content)
        
        # 估算输入token（假设输入和输出长度相似）
        prompt_tokens = max(content_tokens, 10)
        
        return TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=content_tokens,
            total_tokens=prompt_tokens + content_tokens
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
        if isinstance(error, (LLMTimeoutError, LLMRateLimitError, LLMServiceUnavailableError, LLMInvalidRequestError)):
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