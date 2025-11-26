"""降级策略实现"""

import random
import asyncio
import concurrent.futures
from typing import Optional, List, Callable, Any

from src.interfaces.llm import IFallbackStrategy
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
        if attempt > len(self.config.get_fallback_models()):
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
        error_str = str(error)
        
        # 根据错误类型获取优先级模型
        for error_class, models in self.priority_map.items():
            if error_type == error_class or error_class.lower() in error_str.lower() or error_class.lower().replace("error", "") in error_str.lower() or ("rate limit" in error_str.lower() and "ratelimit" in error_class.lower()):
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
        error_str = str(error).lower()
        base_delay = self.config.calculate_delay(attempt)
        
        # 某些错误类型需要更长的延迟
        if error_type in ["RateLimitError"] or "rate limit" in error_str:
            base_delay *= 2
        elif error_type in ["TimeoutError"]:
            base_delay *= 1.5
        
        return base_delay


class ParallelFallbackStrategy(IFallbackStrategy):
    """并行降级策略"""
    
    def __init__(self, config: FallbackConfig, timeout: float = 30.0):
        """
        初始化并行降级策略
        
        Args:
            config: 降级配置
            timeout: 并行超时时间
        """
        self.config = config
        self.timeout = timeout
    
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
        if attempt > len(self.config.get_fallback_models()):
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
    
    async def execute_parallel_fallback(self, client_factory, messages, parameters, primary_model, **kwargs):
        """
        执行并行降级
        
        Args:
            client_factory: 客户端工厂
            messages: 消息列表
            parameters: 参数
            primary_model: 主模型名称
            **kwargs: 其他参数
            
        Returns:
            LLM响应
            
        Raises:
            Exception: 所有降级都失败
        """
        fallback_models = self.config.get_fallback_models()
        
        # 创建所有客户端
        clients = []
        for model_name in [primary_model] + fallback_models:
            try:
                client = client_factory.create_client(model_name)
                clients.append((model_name, client))
            except Exception as e:
                print(f"创建客户端失败 {model_name}: {e}")
                continue
        
        if not clients:
            raise Exception("没有可用的客户端")
        
        # 并行调用所有客户端
        async def call_client(model_name, client):
            try:
                if hasattr(client, 'generate_async'):
                    return await client.generate_async(messages, parameters, **kwargs)
                else:
                    # 如果没有异步方法，在线程池中运行同步方法
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(
                        None, client.generate, messages, parameters, **kwargs
                    )
            except Exception as e:
                print(f"客户端调用失败 {model_name}: {e}")
                raise
        
        # 并行执行所有调用 - 使用 asyncio.create_task 确保返回 Task 对象
        tasks = [asyncio.create_task(call_client(model_name, client)) for model_name, client in clients]
        
        try:
            # 等待第一个成功的结果
            done, pending = await asyncio.wait(
                tasks,
                return_when=asyncio.FIRST_COMPLETED,
                timeout=self.timeout
            )
            
            # 取消剩余的任务
            for task in pending:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # 检查已完成的结果
            for task in done:
                try:
                    result = await task
                    return result
                except Exception:
                    continue
            
            raise Exception("所有并行调用都失败")
            
        except asyncio.TimeoutError:
            # 取消所有任务
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            raise Exception("并行降级超时")


class ConditionalFallbackStrategy(IFallbackStrategy):
    """条件降级策略"""
    
    def __init__(self, config: FallbackConfig, conditions: Optional[List[Callable[[Exception], bool]]] = None):
        """
        初始化条件降级策略
        
        Args:
            config: 降级配置
            conditions: 条件函数列表
        """
        self.config = config
        self.conditions = conditions or []
    
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
        if attempt > len(self.config.get_fallback_models()):
            return False
        
        # 检查自定义条件
        for condition in self.conditions:
            if condition(error):
                return True
        
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


class ConditionalFallback:
    """条件降级工具类"""
    
    @staticmethod
    def on_timeout(error: Exception) -> bool:
        """超时条件"""
        return "timeout" in str(error).lower() or "TimeoutError" in type(error).__name__
    
    @staticmethod
    def on_rate_limit(error: Exception) -> bool:
        """频率限制条件"""
        return "rate limit" in str(error).lower() or "RateLimitError" in type(error).__name__
    
    @staticmethod
    def on_service_unavailable(error: Exception) -> bool:
        """服务不可用条件"""
        return "service unavailable" in str(error).lower() or "ServiceUnavailableError" in type(error).__name__
    
    @staticmethod
    def on_authentication_error(error: Exception) -> bool:
        """认证错误条件"""
        return "authentication" in str(error).lower() or "AuthenticationError" in type(error).__name__
    
    @staticmethod
    def on_model_not_found(error: Exception) -> bool:
        """模型未找到条件"""
        return "model not found" in str(error).lower() or "ModelNotFoundError" in type(error).__name__
    
    @staticmethod
    def on_token_limit(error: Exception) -> bool:
        """Token限制条件"""
        return "token limit" in str(error).lower() or "TokenLimitError" in type(error).__name__
    
    @staticmethod
    def on_content_filter(error: Exception) -> bool:
        """内容过滤条件"""
        return "content filter" in str(error).lower() or "ContentFilterError" in type(error).__name__
    
    @staticmethod
    def on_invalid_request(error: Exception) -> bool:
        """无效请求条件"""
        return "invalid request" in str(error).lower() or "InvalidRequestError" in type(error).__name__
    
    @staticmethod
    def on_any_error(error: Exception) -> bool:
        """任意错误条件"""
        return True
    
    @staticmethod
    def on_retryable_error(error: Exception) -> bool:
        """可重试错误条件"""
        retryable_patterns = [
            "timeout", "rate limit", "service unavailable", "overloaded",
            "connection", "network", "temporary"
        ]
        error_str = str(error).lower()
        return any(pattern in error_str for pattern in retryable_patterns)


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
    elif strategy_type == "parallel":
        return ParallelFallbackStrategy(config, kwargs.get("timeout", 30.0))
    elif strategy_type == "conditional":
        return ConditionalFallbackStrategy(config, kwargs.get("conditions"))
    else:
        raise ValueError(f"不支持的降级策略类型: {strategy_type}")