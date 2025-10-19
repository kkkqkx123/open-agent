"""LLM调用钩子实现"""

import time
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .interfaces import ILLMCallHook
from .models import LLMResponse, LLMError
from .exceptions import (
    LLMCallError,
    LLMTimeoutError,
    LLMRateLimitError,
    LLMAuthenticationError,
    LLMModelNotFoundError,
    LLMTokenLimitError,
    LLMContentFilterError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError,
    LLMFallbackError
)

logger = logging.getLogger(__name__)


class LoggingHook(ILLMCallHook):
    """日志记录钩子"""
    
    def __init__(self, log_requests: bool = True, log_responses: bool = True, log_errors: bool = True) -> None:
        """
        初始化日志钩子
        
        Args:
            log_requests: 是否记录请求
            log_responses: 是否记录响应
            log_errors: 是否记录错误
        """
        self.log_requests = log_requests
        self.log_responses = log_responses
        self.log_errors = log_errors
    
    def before_call(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用前的日志"""
        if not self.log_requests:
            return
        
        # 记录请求信息
        logger.info(f"LLM调用开始 - 消息数量: {len(messages)}, 参数: {parameters}")
        
        # 记录消息内容（调试级别）
        if logger.isEnabledFor(logging.DEBUG):
            for i, message in enumerate(messages):
                logger.debug(f"消息 {i+1}: {message.content[:100]}...")
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用后的日志"""
        if not self.log_responses or response is None:
            return
        
        # 记录响应信息
        logger.info(
            f"LLM调用完成 - 模型: {response.model}, "
            f"响应时间: {response.response_time:.2f}s, "
            f"Token使用: {response.token_usage.total_tokens}"
        )
        
        # 记录响应内容（调试级别）
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug(f"响应内容: {response.content[:200]}...")
    
    def on_error(
        self,
        error: Exception,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """记录错误日志"""
        if not self.log_errors:
            return None
        
        # 记录错误信息
        logger.error(f"LLM调用失败 - 错误类型: {type(error).__name__}, 错误信息: {str(error)}")
        
        # 不尝试恢复错误
        return None


class MetricsHook(ILLMCallHook):
    """指标收集钩子"""
    
    def __init__(self) -> None:
        """初始化指标钩子"""
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "error_counts": {}
        }
    
    def before_call(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用开始"""
        self.metrics["total_calls"] += 1
        kwargs["_start_time"] = time.time()
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用完成"""
        if response is None:
            return
            
        self.metrics["successful_calls"] += 1
        
        # 记录Token使用
        self.metrics["total_tokens"] += response.token_usage.total_tokens
        
        # 记录响应时间
        if response.response_time:
            self.metrics["total_response_time"] += response.response_time
    
    def on_error(
        self,
        error: Exception,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """记录错误"""
        self.metrics["failed_calls"] += 1
        
        # 记录错误类型计数
        error_type = type(error).__name__
        self.metrics["error_counts"][error_type] = self.metrics["error_counts"].get(error_type, 0) + 1
        
        # 不尝试恢复错误
        return None
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取指标"""
        total_calls = self.metrics["total_calls"]
        
        if total_calls == 0:
            return self.metrics.copy()
        
        # 计算平均值
        avg_response_time = self.metrics["total_response_time"] / max(self.metrics["successful_calls"], 1)
        avg_tokens = self.metrics["total_tokens"] / max(self.metrics["successful_calls"], 1)
        success_rate = self.metrics["successful_calls"] / total_calls
        
        return {
            **self.metrics,
            "average_response_time": avg_response_time,
            "average_tokens_per_call": avg_tokens,
            "success_rate": success_rate
        }
    
    def reset_metrics(self) -> None:
        """重置指标"""
        self.metrics = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
            "total_response_time": 0.0,
            "error_counts": {}
        }


class FallbackHook(ILLMCallHook):
    """降级处理钩子"""
    
    def __init__(self, fallback_models: List[str], max_attempts: int = 3) -> None:
        """
        初始化降级钩子
        
        Args:
            fallback_models: 降级模型列表
            max_attempts: 最大尝试次数
        """
        self.fallback_models = fallback_models
        self.max_attempts = max_attempts
    
    def before_call(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用开始"""
        # 记录当前尝试次数
        if "_attempt_count" not in kwargs:
            kwargs["_attempt_count"] = 1
        else:
            kwargs["_attempt_count"] += 1
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用成功"""
        # 成功调用，不需要降级
        pass
    
    def on_error(
        self,
        error: Exception,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """尝试降级处理"""
        # 检查是否应该重试
        if not self._should_retry(error, kwargs):
            return None
        
        # 获取当前尝试次数
        attempt_count = kwargs.get("_attempt_count", 1)
        
        # 检查是否超过最大尝试次数
        if attempt_count >= self.max_attempts:
            logger.error(f"降级失败：已达到最大尝试次数 {self.max_attempts}")
            return None
        
        # 获取下一个降级模型
        fallback_model = self._get_next_fallback_model(attempt_count)
        if not fallback_model:
            logger.error("降级失败：没有可用的降级模型")
            return None
        
        logger.info(f"尝试降级到模型: {fallback_model} (第 {attempt_count + 1} 次尝试)")
        
        try:
            # 这里需要重新创建客户端并调用
            # 实际实现中需要依赖注入或工厂模式
            # 这里只是示例，实际实现会更复杂
            from .factory import get_global_factory
            
            factory = get_global_factory()
            
            # 创建降级模型配置
            fallback_config = {
                "model_type": self._get_model_type(fallback_model),
                "model_name": fallback_model
            }
            
            # 创建降级客户端
            fallback_client = factory.create_client(fallback_config)
            
            # 调用降级客户端
            response = fallback_client.generate(messages, parameters)
            
            # 标记为降级响应
            response.metadata["fallback_model"] = fallback_model
            response.metadata["fallback_attempt"] = attempt_count + 1
            
            return response
            
        except Exception as fallback_error:
            logger.error(f"降级到模型 {fallback_model} 失败: {fallback_error}")
            return None
    
    def _should_retry(self, error: Exception, kwargs: Dict[str, Any]) -> bool:
        """判断是否应该重试"""
        # 检查错误类型是否可重试
        retryable_errors = (
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError
        )
        
        return isinstance(error, retryable_errors)
    
    def _get_next_fallback_model(self, attempt_count: int) -> Optional[str]:
        """获取下一个降级模型"""
        if attempt_count - 1 < len(self.fallback_models):
            return self.fallback_models[attempt_count - 1]
        return None
    
    def _get_model_type(self, model_name: str) -> str:
        """根据模型名称获取模型类型"""
        if "gpt" in model_name.lower():
            return "openai"
        elif "gemini" in model_name.lower():
            return "gemini"
        elif "claude" in model_name.lower():
            return "anthropic"
        else:
            return "mock"


class RetryHook(ILLMCallHook):
    """重试钩子"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0, backoff_factor: float = 2.0) -> None:
        """
        初始化重试钩子
        
        Args:
            max_retries: 最大重试次数
            retry_delay: 初始重试延迟（秒）
            backoff_factor: 退避因子
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
    
    def before_call(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用开始"""
        # 记录当前重试次数
        if "_retry_count" not in kwargs:
            kwargs["_retry_count"] = 0
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """记录调用成功"""
        # 成功调用，重置重试计数
        pass
    
    def on_error(
        self,
        error: Exception,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """尝试重试"""
        # 检查是否应该重试
        if not self._should_retry(error):
            return None
        
        # 获取当前重试次数
        retry_count = kwargs.get("_retry_count", 0)
        
        # 检查是否超过最大重试次数
        if retry_count >= self.max_retries:
            logger.error(f"重试失败：已达到最大重试次数 {self.max_retries}")
            return None
        
        # 计算延迟时间
        delay = self.retry_delay * (self.backoff_factor ** retry_count)
        
        logger.info(f"等待 {delay:.2f} 秒后重试 (第 {retry_count + 1} 次重试)")
        
        # 等待
        time.sleep(delay)
        
        # 更新重试计数
        kwargs["_retry_count"] = retry_count + 1
        
        # 这里不能直接重试，因为钩子不能重新调用原方法
        # 实际实现需要在客户端中处理重试逻辑
        # 这里只是记录重试意图
        return None
    
    def _should_retry(self, error: Exception) -> bool:
        """判断是否应该重试"""
        # 检查错误类型是否可重试
        retryable_errors = (
            LLMTimeoutError,
            LLMRateLimitError,
            LLMServiceUnavailableError
        )
        
        return isinstance(error, retryable_errors)


class CompositeHook(ILLMCallHook):
    """组合钩子"""
    
    def __init__(self, hooks: List[ILLMCallHook]) -> None:
        """
        初始化组合钩子
        
        Args:
            hooks: 钩子列表
        """
        self.hooks = hooks
    
    def before_call(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """调用所有钩子的before_call方法"""
        for hook in self.hooks:
            try:
                hook.before_call(messages, parameters, **kwargs)
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} before_call 失败: {e}")
    
    def after_call(
        self,
        response: Optional[LLMResponse],
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> None:
        """调用所有钩子的after_call方法"""
        for hook in self.hooks:
            try:
                hook.after_call(response, messages, parameters, **kwargs)
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} after_call 失败: {e}")
    
    def on_error(
        self,
        error: Exception,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Optional[LLMResponse]:
        """调用所有钩子的on_error方法，返回第一个非None结果"""
        for hook in self.hooks:
            try:
                result = hook.on_error(error, messages, parameters, **kwargs)
                if result is not None:
                    return result
            except Exception as e:
                logger.error(f"钩子 {type(hook).__name__} on_error 失败: {e}")
        
        return None
    
    def add_hook(self, hook: ILLMCallHook) -> None:
        """添加钩子"""
        self.hooks.append(hook)
    
    def remove_hook(self, hook: ILLMCallHook) -> None:
        """移除钩子"""
        if hook in self.hooks:
            self.hooks.remove(hook)