"""重试策略单元测试"""

import pytest
import asyncio
from unittest.mock import MagicMock, patch

from src.infrastructure.llm.retry.strategies import (
    DefaultRetryLogger,
    ExponentialBackoffStrategy,
    LinearBackoffStrategy,
    FixedDelayStrategy,
    AdaptiveRetryStrategy,
    ConditionalRetryStrategy,
    StatusCodeRetryCondition,
    ErrorTypeRetryCondition,
    create_retry_strategy
)
from src.infrastructure.llm.retry.interfaces import IRetryLogger, IRetryCondition
from typing import cast, Any
from src.infrastructure.llm.retry.retry_config import RetryConfig


class TestDefaultRetryLogger:
    """默认重试日志记录器测试"""
    
    def test_log_retry_attempt_enabled(self):
        """测试启用时记录重试尝试"""
        logger = DefaultRetryLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            logger.log_retry_attempt("test_function", Exception("test error"), 2, 1.5)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Retry]" in call_args
            assert "test_function" in call_args
            assert "test error" in call_args
            assert "2" in call_args
            assert "1.50" in call_args
    
    def test_log_retry_attempt_disabled(self):
        """测试禁用时不记录重试尝试"""
        logger = DefaultRetryLogger(enabled=False)
        
        with patch('builtins.print') as mock_print:
            logger.log_retry_attempt("test_function", Exception("test error"), 2, 1.5)
            
            mock_print.assert_not_called()
    
    def test_log_retry_success_enabled(self):
        """测试启用时记录重试成功"""
        logger = DefaultRetryLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            logger.log_retry_success("test_function", "result", 3)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Retry]" in call_args
            assert "test_function" in call_args
            assert "3" in call_args
            assert "成功" in call_args
    
    def test_log_retry_failure_enabled(self):
        """测试启用时记录重试失败"""
        logger = DefaultRetryLogger(enabled=True)
        
        with patch('builtins.print') as mock_print:
            logger.log_retry_failure("test_function", Exception("final error"), 5)
            
            mock_print.assert_called_once()
            call_args = mock_print.call_args[0][0]
            assert "[Retry]" in call_args
            assert "test_function" in call_args
            assert "final error" in call_args
            assert "5" in call_args
            assert "失败" in call_args


class TestExponentialBackoffStrategy:
    """指数退避重试策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return ExponentialBackoffStrategy(config)
    
    def test_should_retry_within_limits(self, strategy):
        """测试在限制内应该重试"""
        error = Exception("test error")
        assert strategy.should_retry(error, 1) == True
        assert strategy.should_retry(error, 2) == True
    
    def test_should_retry_exceed_attempts(self, strategy):
        """测试超过最大尝试次数不应该重试"""
        error = Exception("test error")
        assert strategy.should_retry(error, 3) == False
        assert strategy.should_retry(error, 4) == False
    
    def test_get_retry_delay(self, strategy):
        """测试获取重试延迟"""
        error = Exception("test error")
        
        delay1 = strategy.get_retry_delay(error, 1)
        delay2 = strategy.get_retry_delay(error, 2)
        delay3 = strategy.get_retry_delay(error, 3)
        
        # 指数退避：1.0, 2.0, 4.0
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 4.0
    
    def test_get_retry_delay_with_max_limit(self, strategy):
        """测试延迟受最大值限制"""
        strategy.config.max_delay = 3.0
        
        error = Exception("test error")
        delay = strategy.get_retry_delay(error, 3)  # 应该是4.0但被限制为3.0
        
        assert delay == 3.0
    
    def test_on_retry_attempt(self, strategy):
        """测试重试尝试回调"""
        logger = MagicMock(spec=IRetryLogger)
        strategy.logger = logger
        
        error = Exception("test error")
        strategy.on_retry_attempt(error, 2, 1.5)
        
        logger.log_retry_attempt.assert_called_once_with("function", error, 2, 1.5)
    
    def test_on_retry_success(self, strategy):
        """测试重试成功回调"""
        logger = MagicMock(spec=IRetryLogger)
        strategy.logger = logger
        
        result = "success"
        strategy.on_retry_success(result, 3)
        
        logger.log_retry_success.assert_called_once_with("function", result, 3)
    
    def test_on_retry_failure(self, strategy):
        """测试重试失败回调"""
        logger = MagicMock(spec=IRetryLogger)
        strategy.logger = logger
        
        error = Exception("final error")
        strategy.on_retry_failure(error, 5)
        
        logger.log_retry_failure.assert_called_once_with("function", error, 5)


class TestLinearBackoffStrategy:
    """线性退避重试策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=1.0,
            max_delay=10.0,
            jitter=False
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return LinearBackoffStrategy(config)
    
    def test_get_retry_delay(self, strategy):
        """测试获取重试延迟"""
        error = Exception("test error")
        
        delay1 = strategy.get_retry_delay(error, 1)
        delay2 = strategy.get_retry_delay(error, 2)
        delay3 = strategy.get_retry_delay(error, 3)
        
        # 线性退避：1.0, 2.0, 3.0
        assert delay1 == 1.0
        assert delay2 == 2.0
        assert delay3 == 3.0
    
    def test_get_retry_delay_with_jitter(self, strategy):
        """测试带抖动的延迟"""
        strategy.config.jitter = True
        
        error = Exception("test error")
        delay = strategy.get_retry_delay(error, 2)
        
        # 应该在1.0到2.0之间（2.0 * (0.5 + random * 0.5)）
        assert 1.0 <= delay <= 2.0


class TestFixedDelayStrategy:
    """固定延迟重试策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=2.0,
            jitter=False
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return FixedDelayStrategy(config)
    
    def test_get_retry_delay(self, strategy):
        """测试获取重试延迟"""
        error = Exception("test error")
        
        delay1 = strategy.get_retry_delay(error, 1)
        delay2 = strategy.get_retry_delay(error, 2)
        delay3 = strategy.get_retry_delay(error, 3)
        
        # 固定延迟：都是2.0
        assert delay1 == 2.0
        assert delay2 == 2.0
        assert delay3 == 2.0


class TestAdaptiveRetryStrategy:
    """自适应重试策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=1.0,
            max_delay=60.0,
            exponential_base=2.0,
            jitter=False
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return AdaptiveRetryStrategy(config)
    
    def test_should_retry_records_error_history(self, strategy):
        """测试应该重试时记录错误历史"""
        error1 = Exception("error1")
        error2 = Exception("error2")
        
        strategy.should_retry(error1, 1)
        strategy.should_retry(error2, 2)
        
        assert len(strategy._error_history) == 2
        assert strategy._error_history[0] == error1
        assert strategy._error_history[1] == error2
    
    def test_get_retry_delay_adjusts_for_error_type(self, strategy):
        """测试根据错误类型调整延迟"""
        rate_limit_error = Exception("rate limit exceeded")
        timeout_error = Exception("timeout occurred")
        normal_error = Exception("normal error")
        
        delay_rate_limit = strategy.get_retry_delay(rate_limit_error, 1)
        delay_timeout = strategy.get_retry_delay(timeout_error, 1)
        delay_normal = strategy.get_retry_delay(normal_error, 1)
        
        # 频率限制错误应该有最长的延迟
        assert delay_rate_limit > delay_timeout
        assert delay_rate_limit > delay_normal
        # 超时错误应该比普通错误稍长
        assert delay_timeout > delay_normal
    
    def test_get_retry_delay_adjusts_for_repeated_errors(self, strategy):
        """测试对重复错误调整延迟"""
        error = Exception("repeated error")
        
        # 第一次错误
        delay1 = strategy.get_retry_delay(error, 1)
        strategy._error_history.append(error)
        
        # 第二次相同错误
        delay2 = strategy.get_retry_delay(error, 2)
        strategy._error_history.append(error)
        
        # 第三次相同错误
        delay3 = strategy.get_retry_delay(error, 3)
        
        # 延迟应该逐渐增加
        assert delay3 > delay2 > delay1
    
    def test_on_retry_success_clears_error_history(self, strategy):
        """测试重试成功时清空错误历史"""
        # 添加一些错误历史
        strategy._error_history = [Exception("error1"), Exception("error2")]
        
        strategy.on_retry_success("result", 3)
        
        assert len(strategy._error_history) == 0


class TestConditionalRetryStrategy:
    """条件重试策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return RetryConfig(
            enabled=True,
            max_attempts=3,
            base_delay=1.0
        )
    
    @pytest.fixture
    def mock_conditions(self):
        """创建模拟条件"""
        condition1 = MagicMock(spec=IRetryCondition)
        condition1.should_retry.return_value = True
        
        condition2 = MagicMock(spec=IRetryCondition)
        condition2.should_retry.return_value = True
        
        return [condition1, condition2]
    
    @pytest.fixture
    def strategy(self, config, mock_conditions):
        """创建策略实例"""
        return ConditionalRetryStrategy(config, mock_conditions)
    
    def test_should_retry_all_conditions_pass(self, strategy):
        """测试所有条件通过时应该重试"""
        error = Exception("test error")
        
        result = strategy.should_retry(error, 1)
        
        assert result == True
        for condition in strategy.conditions:
            condition.should_retry.assert_called_with(error, 1)
    
    def test_should_retry_one_condition_fails(self, strategy):
        """测试一个条件失败时不应该重试"""
        strategy.conditions[1].should_retry.return_value = False
        
        error = Exception("test error")
        
        result = strategy.should_retry(error, 1)
        
        assert result == False
    
    def test_should_retry_exceed_attempts(self, strategy):
        """测试超过最大尝试次数不应该重试"""
        error = Exception("test error")
        
        result = strategy.should_retry(error, 3)
        
        assert result == False
        # 条件不应该被检查
        for condition in strategy.conditions:
            condition.should_retry.assert_not_called()


class TestStatusCodeRetryCondition:
    """状态码重试条件测试"""
    
    def test_should_retry_with_matching_status_code(self):
        """测试匹配状态码时应该重试"""
        condition = StatusCodeRetryCondition([500, 502, 503])

        error = cast(Any, Exception("server error"))
        error.response = MagicMock()
        error.response.status_code = 500

        result = condition.should_retry(error, 1)

        assert result == True
    
    def test_should_retry_with_non_matching_status_code(self):
        """测试不匹配状态码时不应该重试"""
        condition = StatusCodeRetryCondition([500, 502, 503])

        error = cast(Any, Exception("client error"))
        error.response = MagicMock()
        error.response.status_code = 400

        result = condition.should_retry(error, 1)

        assert result == False
    
    def test_should_retry_without_response(self):
        """测试没有响应时不应该重试"""
        condition = StatusCodeRetryCondition([500, 502, 503])
        
        error = Exception("no response")
        
        result = condition.should_retry(error, 1)
        
        assert result == False


class TestErrorTypeRetryCondition:
    """错误类型重试条件测试"""
    
    def test_should_retry_with_matching_error_type(self):
        """测试匹配错误类型时应该重试"""
        condition = ErrorTypeRetryCondition(
            retry_error_types=["TimeoutError", "ConnectionError"],
            block_error_types=["AuthenticationError"]
        )
        
        # 测试重试错误类型
        timeout_error = Exception("timeout occurred")
        result = condition.should_retry(timeout_error, 1)
        assert result == True
        
        # 测试错误消息中包含关键词
        connection_error = Exception("connection failed")
        result = condition.should_retry(connection_error, 1)
        assert result == True
    
    def test_should_retry_with_blocking_error_type(self):
        """测试阻塞错误类型时不应该重试"""
        condition = ErrorTypeRetryCondition(
            retry_error_types=["TimeoutError", "ConnectionError"],
            block_error_types=["AuthenticationError"]
        )
        
        # 测试阻塞错误类型
        auth_error = Exception("authentication failed")
        result = condition.should_retry(auth_error, 1)
        assert result == False
        
        # 测试错误消息中包含阻塞关键词
        auth_error_msg = Exception("auth token expired")
        result = condition.should_retry(auth_error_msg, 1)
        assert result == False
    
    def test_should_retry_with_default_allow(self):
        """测试默认允许重试"""
        condition = ErrorTypeRetryCondition(
            retry_error_types=["TimeoutError"],
            block_error_types=["AuthenticationError"]
        )
        
        # 不在重试列表也不在阻塞列表的错误
        generic_error = Exception("generic error")
        result = condition.should_retry(generic_error, 1)
        assert result == True


class TestCreateRetryStrategy:
    """创建重试策略测试"""
    
    def test_create_exponential_backoff_strategy(self):
        """测试创建指数退避策略"""
        config = RetryConfig(strategy_type="exponential_backoff")
        strategy = create_retry_strategy(config)
        assert isinstance(strategy, ExponentialBackoffStrategy)
    
    def test_create_linear_strategy(self):
        """测试创建线性策略"""
        config = RetryConfig(strategy_type="linear")
        strategy = create_retry_strategy(config)
        assert isinstance(strategy, LinearBackoffStrategy)
    
    def test_create_fixed_strategy(self):
        """测试创建固定延迟策略"""
        config = RetryConfig(strategy_type="fixed")
        strategy = create_retry_strategy(config)
        assert isinstance(strategy, FixedDelayStrategy)
    
    def test_create_adaptive_strategy(self):
        """测试创建自适应策略"""
        config = RetryConfig(strategy_type="adaptive")
        strategy = create_retry_strategy(config)
        assert isinstance(strategy, AdaptiveRetryStrategy)
    
    def test_create_conditional_strategy(self):
        """测试创建条件策略"""
        config = RetryConfig(strategy_type="conditional")
        conditions = [MagicMock(spec=IRetryCondition)]
        strategy = create_retry_strategy(config, conditions=conditions)
        assert isinstance(strategy, ConditionalRetryStrategy)
        assert strategy.conditions == conditions
    
    def test_create_unsupported_strategy(self):
        """测试创建不支持的策略类型"""
        config = RetryConfig(strategy_type="unsupported")
        with pytest.raises(ValueError, match="不支持的重试策略类型"):
            create_retry_strategy(config)