"""LLM钩子单元测试"""

import pytest
import time
from unittest.mock import Mock, patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from src.llm.hooks import (
    LoggingHook,
    MetricsHook,
    FallbackHook,
    RetryHook,
    CompositeHook
)
from src.llm.models import LLMResponse, TokenUsage
from src.llm.exceptions import (
    LLMTimeoutError,
    LLMRateLimitError,
    LLMServiceUnavailableError,
    LLMInvalidRequestError
)


class TestLoggingHook:
    """日志钩子测试类"""
    
    @pytest.fixture
    def hook(self):
        """创建钩子实例"""
        return LoggingHook(log_requests=True, log_responses=True, log_errors=True)
    
    def test_before_call(self, hook):
        """测试调用前日志"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        with patch('src.llm.hooks.logger') as mock_logger:
            hook.before_call(messages, parameters)
            
            # 验证日志被记录
            mock_logger.info.assert_called_once()
            assert "LLM调用开始" in mock_logger.info.call_args[0][0]
    
    def test_after_call(self, hook):
        """测试调用后日志"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        response = LLMResponse(
            content="测试响应",
            message=AIMessage(content="测试响应"),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            model="test-model",
            response_time=1.5
        )
        
        with patch('src.llm.hooks.logger') as mock_logger:
            hook.after_call(response, messages, parameters)
            
            # 验证日志被记录
            mock_logger.info.assert_called_once()
            assert "LLM调用完成" in mock_logger.info.call_args[0][0]
    
    def test_on_error(self, hook):
        """测试错误日志"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        error = Exception("测试错误")
        
        with patch('src.llm.hooks.logger') as mock_logger:
            result = hook.on_error(error, messages, parameters)
            
            # 验证日志被记录
            mock_logger.error.assert_called_once()
            assert "LLM调用失败" in mock_logger.error.call_args[0][0]
            
            # 验证返回None
            assert result is None
    
    def test_disabled_logging(self):
        """测试禁用日志"""
        hook = LoggingHook(log_requests=False, log_responses=False, log_errors=False)
        
        with patch('src.llm.hooks.logger') as mock_logger:
            hook.before_call([], {})
            hook.after_call(None, [], {})
            hook.on_error(Exception("test"), [], {})
            
            # 验证没有日志被记录
            mock_logger.info.assert_not_called()
            mock_logger.error.assert_not_called()


class TestMetricsHook:
    """指标钩子测试类"""
    
    @pytest.fixture
    def hook(self):
        """创建钩子实例"""
        return MetricsHook()
    
    def test_before_call(self, hook):
        """测试调用前指标"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        # 记录初始指标
        initial_metrics = hook.get_metrics()
        initial_calls = initial_metrics["total_calls"]
        
        # 调用钩子
        hook.before_call(messages, parameters)
        
        # 验证指标更新
        metrics = hook.get_metrics()
        assert metrics["total_calls"] == initial_calls + 1
    
    def test_after_call(self, hook):
        """测试调用后指标"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        response = LLMResponse(
            content="测试响应",
            message=AIMessage(content="测试响应"),
            token_usage=TokenUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            model="test-model",
            response_time=1.5
        )
        
        # 先调用before_call
        hook.before_call(messages, parameters)
        
        # 调用after_call
        hook.after_call(response, messages, parameters)
        
        # 验证指标更新
        metrics = hook.get_metrics()
        assert metrics["successful_calls"] == 1
        assert metrics["total_tokens"] == 15
        assert metrics["total_response_time"] == 1.5
    
    def test_on_error(self, hook):
        """测试错误指标"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        error = LLMTimeoutError("测试超时")
        
        # 先调用before_call
        hook.before_call(messages, parameters)
        
        # 调用on_error
        result = hook.on_error(error, messages, parameters)
        
        # 验证指标更新
        metrics = hook.get_metrics()
        assert metrics["failed_calls"] == 1
        assert metrics["error_counts"]["LLMTimeoutError"] == 1
        
        # 验证返回None
        assert result is None
    
    def test_get_metrics(self, hook):
        """测试获取指标"""
        # 添加一些数据
        hook.metrics["total_calls"] = 10
        hook.metrics["successful_calls"] = 8
        hook.metrics["failed_calls"] = 2
        hook.metrics["total_tokens"] = 100
        hook.metrics["total_response_time"] = 5.0
        
        # 获取指标
        metrics = hook.get_metrics()
        
        # 验证计算指标
        assert metrics["average_response_time"] == 5.0 / 8
        assert metrics["average_tokens_per_call"] == 100 / 8
        assert metrics["success_rate"] == 0.8
    
    def test_reset_metrics(self, hook):
        """测试重置指标"""
        # 添加一些数据
        hook.metrics["total_calls"] = 10
        
        # 重置指标
        hook.reset_metrics()
        
        # 验证指标被重置
        metrics = hook.get_metrics()
        assert metrics["total_calls"] == 0
        assert metrics["successful_calls"] == 0
        assert metrics["failed_calls"] == 0


class TestFallbackHook:
    """降级钩子测试类"""
    
    @pytest.fixture
    def hook(self):
        """创建钩子实例"""
        return FallbackHook(fallback_models=["mock-model", "test-model"], max_attempts=3)
    
    def test_before_call(self, hook):
        """测试调用前钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        # 第一次调用
        hook.before_call(messages, parameters)
        assert parameters["_attempt_count"] == 1
        
        # 第二次调用
        hook.before_call(messages, parameters)
        assert parameters["_attempt_count"] == 2
    
    def test_after_call(self, hook):
        """测试调用后钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        response = LLMResponse(
            content="测试响应",
            message=AIMessage(content="测试响应"),
            token_usage=TokenUsage(),
            model="test-model"
        )
        
        # 调用钩子（应该不做任何事）
        hook.after_call(response, messages, parameters)
    
    def test_on_error_retryable(self, hook):
        """测试可重试错误"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_attempt_count": 1}
        error = LLMTimeoutError("测试超时")
        
        with patch('src.llm.factory.get_global_factory') as mock_get_factory:
            mock_factory = Mock()
            mock_client = Mock()
            mock_response = LLMResponse(
                content="降级响应",
                message=AIMessage(content="降级响应"),
                token_usage=TokenUsage(),
                model="mock-model"
            )
            mock_client.generate.return_value = mock_response
            mock_factory.create_client.return_value = mock_client
            mock_get_factory.return_value = mock_factory
            
            # 调用钩子
            result = hook.on_error(error, messages, parameters)
            
            # 验证返回降级响应
            assert result is not None
            assert result.content == "降级响应"
            assert result.metadata["fallback_model"] == "mock-model"
            assert result.metadata["fallback_attempt"] == 2
    
    def test_on_error_non_retryable(self, hook):
        """测试不可重试错误"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_attempt_count": 1}
        error = LLMInvalidRequestError("无效请求")
        
        # 调用钩子
        result = hook.on_error(error, messages, parameters)
        
        # 验证返回None
        assert result is None
    
    def test_on_error_max_attempts(self, hook):
        """测试达到最大尝试次数"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_attempt_count": 3}
        error = LLMTimeoutError("测试超时")
        
        # 调用钩子
        result = hook.on_error(error, messages, parameters)
        
        # 验证返回None
        assert result is None
    
    def test_should_retry(self, hook):
        """测试是否应该重试"""
        # 可重试错误
        assert hook._should_retry(LLMTimeoutError("超时")) is True
        assert hook._should_retry(LLMRateLimitError("频率限制")) is True
        assert hook._should_retry(LLMServiceUnavailableError("服务不可用")) is True
        
        # 不可重试错误
        assert hook._should_retry(LLMInvalidRequestError("无效请求")) is False
        assert hook._should_retry(Exception("普通错误")) is False
    
    def test_get_next_fallback_model(self, hook):
        """测试获取下一个降级模型"""
        # 第一次尝试
        model = hook._get_next_fallback_model(1)
        assert model == "mock-model"
        
        # 第二次尝试
        model = hook._get_next_fallback_model(2)
        assert model == "test-model"
        
        # 超出范围
        model = hook._get_next_fallback_model(3)
        assert model is None
    
    def test_get_model_type(self, hook):
        """测试获取模型类型"""
        assert hook._get_model_type("gpt-4") == "openai"
        assert hook._get_model_type("gemini-pro") == "gemini"
        assert hook._get_model_type("claude-3") == "anthropic"
        assert hook._get_model_type("unknown-model") == "mock"


class TestRetryHook:
    """重试钩子测试类"""
    
    @pytest.fixture
    def hook(self):
        """创建钩子实例"""
        return RetryHook(max_retries=3, retry_delay=0.1, backoff_factor=2.0)
    
    def test_before_call(self, hook):
        """测试调用前钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        # 第一次调用
        hook.before_call(messages, parameters)
        assert parameters["_retry_count"] == 0
        
        # 第二次调用
        parameters["_retry_count"] = 1
        hook.before_call(messages, parameters)
        assert parameters["_retry_count"] == 1
    
    def test_after_call(self, hook):
        """测试调用后钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        response = LLMResponse(
            content="测试响应",
            message=AIMessage(content="测试响应"),
            token_usage=TokenUsage(),
            model="test-model"
        )
        
        # 调用钩子（应该不做任何事）
        hook.after_call(response, messages, parameters)
    
    def test_on_error_retryable(self, hook):
        """测试可重试错误"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_retry_count": 1}
        error = LLMTimeoutError("测试超时")
        
        with patch('time.sleep') as mock_sleep:
            # 调用钩子
            result = hook.on_error(error, messages, parameters)
            
            # 验证等待
            mock_sleep.assert_called_once_with(0.2)  # 0.1 * 2.0^1
            
            # 验证重试计数更新
            assert parameters["_retry_count"] == 2
            
            # 验证返回None（钩子不能直接重试）
            assert result is None
    
    def test_on_error_non_retryable(self, hook):
        """测试不可重试错误"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_retry_count": 1}
        error = LLMInvalidRequestError("无效请求")
        
        with patch('time.sleep') as mock_sleep:
            # 调用钩子
            result = hook.on_error(error, messages, parameters)
            
            # 验证没有等待
            mock_sleep.assert_not_called()
            
            # 验证返回None
            assert result is None
    
    def test_on_error_max_retries(self, hook):
        """测试达到最大重试次数"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7, "_retry_count": 3}
        error = LLMTimeoutError("测试超时")
        
        # 调用钩子
        result = hook.on_error(error, messages, parameters)
        
        # 验证返回None
        assert result is None
    
    def test_should_retry(self, hook):
        """测试是否应该重试"""
        # 可重试错误
        assert hook._should_retry(LLMTimeoutError("超时")) is True
        assert hook._should_retry(LLMRateLimitError("频率限制")) is True
        assert hook._should_retry(LLMServiceUnavailableError("服务不可用")) is True
        
        # 不可重试错误
        assert hook._should_retry(LLMInvalidRequestError("无效请求")) is False
        assert hook._should_retry(Exception("普通错误")) is False


class TestCompositeHook:
    """组合钩子测试类"""
    
    @pytest.fixture
    def hooks(self):
        """创建子钩子"""
        hook1 = Mock(spec=LoggingHook)
        hook2 = Mock(spec=MetricsHook)
        return [hook1, hook2]
    
    @pytest.fixture
    def composite_hook(self, hooks):
        """创建组合钩子"""
        return CompositeHook(hooks)
    
    def test_before_call(self, composite_hook, hooks):
        """测试调用前钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        # 调用组合钩子
        composite_hook.before_call(messages, parameters)
        
        # 验证所有子钩子被调用
        for hook in hooks:
            hook.before_call.assert_called_once_with(messages, parameters, **{})
    
    def test_after_call(self, composite_hook, hooks):
        """测试调用后钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        response = LLMResponse(
            content="测试响应",
            message=AIMessage(content="测试响应"),
            token_usage=TokenUsage(),
            model="test-model"
        )
        
        # 调用组合钩子
        composite_hook.after_call(response, messages, parameters)
        
        # 验证所有子钩子被调用
        for hook in hooks:
            hook.after_call.assert_called_once_with(response, messages, parameters, **{})
    
    def test_on_error(self, composite_hook, hooks):
        """测试错误钩子"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        error = Exception("测试错误")
        
        # 设置第一个钩子返回None，第二个钩子返回响应
        hooks[0].on_error.return_value = None
        mock_response = LLMResponse(
            content="恢复响应",
            message=AIMessage(content="恢复响应"),
            token_usage=TokenUsage(),
            model="test-model"
        )
        hooks[1].on_error.return_value = mock_response
        
        # 调用组合钩子
        result = composite_hook.on_error(error, messages, parameters)
        
        # 验证所有子钩子被调用
        for hook in hooks:
            hook.on_error.assert_called_once_with(error, messages, parameters, **{})
        
        # 验证返回第一个非None结果
        assert result is mock_response
    
    def test_add_hook(self, composite_hook, hooks):
        """测试添加钩子"""
        new_hook = Mock()
        
        # 添加钩子
        composite_hook.add_hook(new_hook)
        
        # 验证钩子被添加
        assert new_hook in composite_hook.hooks
        assert len(composite_hook.hooks) == len(hooks) + 1
    
    def test_remove_hook(self, composite_hook, hooks):
        """测试移除钩子"""
        # 移除第一个钩子
        composite_hook.remove_hook(hooks[0])
        
        # 验证钩子被移除
        assert hooks[0] not in composite_hook.hooks
        assert len(composite_hook.hooks) == len(hooks) - 1
    
    def test_hook_error_handling(self, composite_hook, hooks):
        """测试钩子错误处理"""
        messages = [HumanMessage(content="测试消息")]
        parameters = {"temperature": 0.7}
        
        # 设置第一个钩子抛出异常
        hooks[0].before_call.side_effect = Exception("钩子错误")
        
        with patch('src.llm.hooks.logger') as mock_logger:
            # 调用组合钩子
            composite_hook.before_call(messages, parameters)
            
            # 验证错误被记录
            mock_logger.error.assert_called_once()
            
            # 验证第二个钩子仍然被调用
            hooks[1].before_call.assert_called_once()