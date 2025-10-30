"""降级策略实现"""

import random
from typing import Optional, List

from .interfaces import IFallbackStrategy
from .fallback_config import FallbackConfig


class SequentialFallbackStrategy(IFallbackStrategy):
    """顺序降级策略"""
    
    def __init__(self, config: FallbackConfig):
        """
        初始化顺序降级策略
        
        Args:
            config: 降级配置
        """
        self.config = config
    
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        # 检查是否达到最大尝试次数
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查是否还有可用的降级模型
        if attempt >= len(self.config.get_fallback_models()):
            return False
        
        # 检查错误类型是否应该降级
        return self.config.should_fallback_on_error(error)
    
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        fallback_models = self.config.get_fallback_models()
        
        # 第一次尝试使用主模型，后续使用降级模型
        if attempt == 0:
            return None  # 使用主模型
        
        # 获取对应的降级模型
        if attempt - 1 < len(fallback_models):
            return fallback_models[attempt - 1]
        
        return None
    
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        return self.config.calculate_delay(attempt)


class PriorityFallbackStrategy(IFallbackStrategy):
    """优先级降级策略"""
    
    def __init__(self, config: FallbackConfig, priority_map: Optional[dict] = None):
        """
        初始化优先级降级策略
        
        Args:
            config: 降级配置
            priority_map: 优先级映射，错误类型到模型列表的映射
        """
        self.config = config
        self.priority_map = priority_map or {}
    
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        # 检查是否达到最大尝试次数
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查错误类型是否应该降级
        if not self.config.should_fallback_on_error(error):
            return False
        
        # 检查是否有对应的优先级模型
        error_type = type(error).__name__
        if error_type in self.priority_map:
            return True
        
        # 使用默认降级模型
        return len(self.config.get_fallback_models()) > 0
    
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        error_type = type(error).__name__
        
        # 根据错误类型获取优先级模型
        if error_type in self.priority_map:
            priority_models = self.priority_map[error_type]
            if attempt - 1 < len(priority_models):
                return priority_models[attempt - 1]
        
        # 使用默认降级模型
        fallback_models = self.config.get_fallback_models()
        if attempt - 1 < len(fallback_models):
            return fallback_models[attempt - 1]
        
        return None
    
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        return self.config.calculate_delay(attempt)


class RandomFallbackStrategy(IFallbackStrategy):
    """随机降级策略"""
    
    def __init__(self, config: FallbackConfig):
        """
        初始化随机降级策略
        
        Args:
            config: 降级配置
        """
        self.config = config
        self._used_models = set()
    
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        # 检查是否达到最大尝试次数
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查是否还有未使用的降级模型
        available_models = set(self.config.get_fallback_models()) - self._used_models
        if not available_models:
            return False
        
        # 检查错误类型是否应该降级
        return self.config.should_fallback_on_error(error)
    
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        fallback_models = self.config.get_fallback_models()
        
        # 第一次尝试使用主模型
        if attempt == 0:
            return None
        
        # 随机选择一个未使用的降级模型
        available_models = [m for m in fallback_models if m not in self._used_models]
        if available_models:
            selected_model = random.choice(available_models)
            self._used_models.add(selected_model)
            return selected_model
        
        return None
    
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        return self.config.calculate_delay(attempt)


class ErrorTypeBasedStrategy(IFallbackStrategy):
    """基于错误类型的降级策略"""
    
    def __init__(self, config: FallbackConfig, error_model_mapping: Optional[dict] = None):
        """
        初始化基于错误类型的降级策略
        
        Args:
            config: 降级配置
            error_model_mapping: 错误类型到模型列表的映射
        """
        self.config = config
        self.error_model_mapping = error_model_mapping or {}
    
    def should_fallback(self, error: Exception, attempt: int) -> bool:
        """
        判断是否应该降级
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            是否应该降级
        """
        # 检查是否达到最大尝试次数
        if attempt >= self.config.get_max_attempts():
            return False
        
        # 检查错误类型是否应该降级
        if not self.config.should_fallback_on_error(error):
            return False
        
        # 检查是否有对应的模型映射
        error_type = type(error).__name__
        if error_type in self.error_model_mapping:
            return attempt - 1 < len(self.error_model_mapping[error_type])
        
        # 使用默认降级模型
        return len(self.config.get_fallback_models()) > 0
    
    def get_fallback_target(self, error: Exception, attempt: int) -> Optional[str]:
        """
        获取降级目标
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            降级目标模型名称，None表示不降级
        """
        error_type = type(error).__name__
        
        # 根据错误类型获取映射的模型
        if error_type in self.error_model_mapping:
            models = self.error_model_mapping[error_type]
            if attempt - 1 < len(models):
                return models[attempt - 1]
        
        # 使用默认降级模型
        fallback_models = self.config.get_fallback_models()
        if attempt - 1 < len(fallback_models):
            return fallback_models[attempt - 1]
        
        return None
    
    def get_fallback_delay(self, error: Exception, attempt: int) -> float:
        """
        获取降级前的延迟时间
        
        Args:
            error: 发生的错误
            attempt: 当前尝试次数
            
        Returns:
            延迟时间（秒）
        """
        # 根据错误类型调整延迟
        error_type = type(error).__name__
        base_delay = self.config.calculate_delay(attempt)
        
        # 某些错误类型需要更长的延迟
        if error_type in ["RateLimitError", "RateLimitError"]:
            base_delay *= 2
        elif error_type in ["TimeoutError"]:
            base_delay *= 1.5
        
        return base_delay


def create_fallback_strategy(config: FallbackConfig, **kwargs) -> IFallbackStrategy:
    """
    创建降级策略
    
    Args:
        config: 降级配置
        **kwargs: 策略特定参数
        
    Returns:
        降级策略实例
    """
    strategy_type = config.strategy_type.lower()
    
    if strategy_type == "sequential":
        return SequentialFallbackStrategy(config)
    elif strategy_type == "priority":
        return PriorityFallbackStrategy(config, kwargs.get("priority_map"))
    elif strategy_type == "random":
        return RandomFallbackStrategy(config)
    elif strategy_type == "error_type":
        return ErrorTypeBasedStrategy(config, kwargs.get("error_model_mapping"))
    else:
        raise ValueError(f"不支持的降级策略类型: {strategy_type}")