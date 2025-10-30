"""降级策略单元测试"""

import pytest
from unittest.mock import MagicMock

from src.infrastructure.llm.fallback_system.strategies import (
    SequentialFallbackStrategy,
    PriorityFallbackStrategy,
    RandomFallbackStrategy,
    ErrorTypeBasedStrategy,
    create_fallback_strategy
)
from src.infrastructure.llm.fallback_system.fallback_config import FallbackConfig


class TestSequentialFallbackStrategy:
    """顺序降级策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["model2", "model3"],
            strategy_type="sequential"
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return SequentialFallbackStrategy(config)
    
    def test_should_fallback_within_limits(self, strategy):
        """测试在限制内应该降级"""
        error = Exception("test error")
        assert strategy.should_fallback(error, 1) == True
        assert strategy.should_fallback(error, 2) == True
    
    def test_should_fallback_exceed_attempts(self, strategy):
        """测试超过最大尝试次数不应该降级"""
        error = Exception("test error")
        assert strategy.should_fallback(error, 3) == False
        assert strategy.should_fallback(error, 4) == False
    
    def test_should_fallback_exceed_models(self, strategy):
        """测试超过降级模型数量不应该降级"""
        error = Exception("test error")
        assert strategy.should_fallback(error, 3) == False  # 只有2个降级模型
    
    def test_get_fallback_target_first_attempt(self, strategy):
        """测试第一次尝试返回None（使用主模型）"""
        error = Exception("test error")
        target = strategy.get_fallback_target(error, 0)
        assert target is None
    
    def test_get_fallback_target_subsequent_attempts(self, strategy):
        """测试后续尝试返回降级模型"""
        error = Exception("test error")
        target1 = strategy.get_fallback_target(error, 1)
        target2 = strategy.get_fallback_target(error, 2)
        target3 = strategy.get_fallback_target(error, 3)
        
        assert target1 == "model2"
        assert target2 == "model3"
        assert target3 is None  # 超出降级模型数量
    
    def test_get_fallback_delay(self, strategy):
        """测试获取降级延迟"""
        error = Exception("test error")
        delay1 = strategy.get_fallback_delay(error, 1)
        delay2 = strategy.get_fallback_delay(error, 2)
        
        assert delay1 >= 0
        assert delay2 >= 0
        # 由于可能有抖动，只检查基本范围
        assert delay1 <= strategy.config.max_delay
        assert delay2 <= strategy.config.max_delay


class TestPriorityFallbackStrategy:
    """优先级降级策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["default_model1", "default_model2"],
            strategy_type="priority"
        )
    
    @pytest.fixture
    def priority_map(self):
        """创建优先级映射"""
        return {
            "TimeoutError": ["timeout_model1", "timeout_model2"],
            "RateLimitError": ["ratelimit_model1"]
        }
    
    @pytest.fixture
    def strategy(self, config, priority_map):
        """创建策略实例"""
        return PriorityFallbackStrategy(config, priority_map)
    
    def test_should_fallback_with_priority_mapping(self, strategy):
        """测试有优先级映射时应该降级"""
        error = TimeoutError("test timeout")
        assert strategy.should_fallback(error, 1) == True
    
    def test_should_fallback_without_priority_mapping(self, strategy):
        """测试无优先级映射时使用默认降级模型"""
        error = ValueError("test value error")
        assert strategy.should_fallback(error, 1) == True
    
    def test_should_fallback_exceed_attempts(self, strategy):
        """测试超过最大尝试次数不应该降级"""
        error = TimeoutError("test timeout")
        assert strategy.should_fallback(error, 3) == False
    
    def test_get_fallback_target_with_priority_mapping(self, strategy):
        """测试有优先级映射时获取降级目标"""
        timeout_error = TimeoutError("test timeout")
        ratelimit_error = Exception("rate limit exceeded")
        
        # 测试超时错误的优先级模型
        target1 = strategy.get_fallback_target(timeout_error, 1)
        target2 = strategy.get_fallback_target(timeout_error, 2)
        
        assert target1 == "timeout_model1"
        assert target2 == "timeout_model2"
        
        # 测试频率限制错误的优先级模型
        target3 = strategy.get_fallback_target(ratelimit_error, 1)
        assert target3 == "ratelimit_model1"
    
    def test_get_fallback_target_fallback_to_default(self, strategy):
        """测试回退到默认降级模型"""
        error = ValueError("test value error")
        
        target1 = strategy.get_fallback_target(error, 1)
        target2 = strategy.get_fallback_target(error, 2)
        
        assert target1 == "default_model1"
        assert target2 == "default_model2"


class TestRandomFallbackStrategy:
    """随机降级策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["model1", "model2", "model3"],
            strategy_type="random"
        )
    
    @pytest.fixture
    def strategy(self, config):
        """创建策略实例"""
        return RandomFallbackStrategy(config)
    
    def test_should_fallback_within_limits(self, strategy):
        """测试在限制内应该降级"""
        error = Exception("test error")
        assert strategy.should_fallback(error, 1) == True
        assert strategy.should_fallback(error, 2) == True
    
    def test_should_fallback_no_available_models(self, strategy):
        """测试没有可用模型时不应该降级"""
        error = Exception("test error")
        
        # 使用所有模型
        strategy._used_models = {"model1", "model2", "model3"}
        
        assert strategy.should_fallback(error, 1) == False
    
    def test_get_fallback_target_first_attempt(self, strategy):
        """测试第一次尝试返回None（使用主模型）"""
        error = Exception("test error")
        target = strategy.get_fallback_target(error, 0)
        assert target is None
    
    def test_get_fallback_target_random_selection(self, strategy):
        """测试随机选择降级模型"""
        error = Exception("test error")
        
        # 多次选择应该返回不同的模型（随机性）
        targets = set()
        for _ in range(10):
            target = strategy.get_fallback_target(error, 1)
            if target:
                targets.add(target)
        
        # 应该至少选择了一个模型
        assert len(targets) > 0
        # 所有选择的模型都应该在可用模型列表中
        for target in targets:
            assert target in strategy.config.fallback_models
    
    def test_get_fallback_target_no_duplicates(self, strategy):
        """测试不会重复选择已使用的模型"""
        error = Exception("test error")
        
        # 选择所有可用模型
        selected_models = set()
        for i in range(1, 4):  # 3个可用模型
            target = strategy.get_fallback_target(error, i)
            if target:
                selected_models.add(target)
        
        # 应该选择了所有不同的模型
        assert len(selected_models) == 3
        assert selected_models == {"model1", "model2", "model3"}


class TestErrorTypeBasedStrategy:
    """基于错误类型的降级策略测试"""
    
    @pytest.fixture
    def config(self):
        """创建测试配置"""
        return FallbackConfig(
            enabled=True,
            max_attempts=3,
            fallback_models=["default_model1", "default_model2"],
            strategy_type="error_type"
        )
    
    @pytest.fixture
    def error_model_mapping(self):
        """创建错误类型映射"""
        return {
            "TimeoutError": ["timeout_model1", "timeout_model2"],
            "RateLimitError": ["ratelimit_model1"],
            "ConnectionError": ["connection_model1"]
        }
    
    @pytest.fixture
    def strategy(self, config, error_model_mapping):
        """创建策略实例"""
        return ErrorTypeBasedStrategy(config, error_model_mapping)
    
    def test_should_fallback_with_mapping(self, strategy):
        """测试有映射的错误类型应该降级"""
        timeout_error = TimeoutError("test timeout")
        assert strategy.should_fallback(timeout_error, 1) == True
    
    def test_should_fallback_without_mapping(self, strategy):
        """测试无映射的错误类型使用默认降级模型"""
        value_error = ValueError("test value error")
        assert strategy.should_fallback(value_error, 1) == True
    
    def test_get_fallback_target_with_mapping(self, strategy):
        """测试有映射时获取降级目标"""
        timeout_error = TimeoutError("test timeout")
        
        target1 = strategy.get_fallback_target(timeout_error, 1)
        target2 = strategy.get_fallback_target(timeout_error, 2)
        
        assert target1 == "timeout_model1"
        assert target2 == "timeout_model2"
    
    def test_get_fallback_target_fallback_to_default(self, strategy):
        """测试回退到默认降级模型"""
        value_error = ValueError("test value error")
        
        target1 = strategy.get_fallback_target(value_error, 1)
        target2 = strategy.get_fallback_target(value_error, 2)
        
        assert target1 == "default_model1"
        assert target2 == "default_model2"
    
    def test_get_fallback_delay_adjusted_by_error_type(self, strategy):
        """测试根据错误类型调整延迟"""
        timeout_error = TimeoutError("test timeout")
        ratelimit_error = Exception("rate limit exceeded")
        value_error = ValueError("test value error")
        
        delay_timeout = strategy.get_fallback_delay(timeout_error, 1)
        delay_ratelimit = strategy.get_fallback_delay(ratelimit_error, 1)
        delay_value = strategy.get_fallback_delay(value_error, 1)
        
        # 频率限制错误应该有更长的延迟
        assert delay_ratelimit > delay_value
        # 超时错误应该有稍长的延迟
        assert delay_timeout > delay_value


class TestCreateFallbackStrategy:
    """创建降级策略测试"""
    
    def test_create_sequential_strategy(self):
        """测试创建顺序策略"""
        config = FallbackConfig(strategy_type="sequential")
        strategy = create_fallback_strategy(config)
        assert isinstance(strategy, SequentialFallbackStrategy)
    
    def test_create_priority_strategy(self):
        """测试创建优先级策略"""
        config = FallbackConfig(strategy_type="priority")
        priority_map = {"TimeoutError": ["model1"]}
        strategy = create_fallback_strategy(config, priority_map=priority_map)
        assert isinstance(strategy, PriorityFallbackStrategy)
    
    def test_create_random_strategy(self):
        """测试创建随机策略"""
        config = FallbackConfig(strategy_type="random")
        strategy = create_fallback_strategy(config)
        assert isinstance(strategy, RandomFallbackStrategy)
    
    def test_create_error_type_strategy(self):
        """测试创建基于错误类型的策略"""
        config = FallbackConfig(strategy_type="error_type")
        error_mapping = {"TimeoutError": ["model1"]}
        strategy = create_fallback_strategy(config, error_model_mapping=error_mapping)
        assert isinstance(strategy, ErrorTypeBasedStrategy)
    
    def test_create_unsupported_strategy(self):
        """测试创建不支持的策略类型"""
        config = FallbackConfig(strategy_type="unsupported")
        with pytest.raises(ValueError, match="不支持的降级策略类型"):
            create_fallback_strategy(config)