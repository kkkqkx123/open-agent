"""LLM依赖注入便利层

使用通用依赖注入框架提供简洁的LLM服务获取方式。
"""

from typing import Optional

from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    IRetryLogger,
    IFallbackLogger,
    TokenCalculationConfig,
    TokenCostInfo
)
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.services.llm.retry.retry_manager import RetryManager
from src.services.llm.fallback_system.fallback_executor import FallbackExecutor
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


class _StubTokenConfigProvider(ITokenConfigProvider):
    """临时 TokenConfigProvider 实现（用于极端情况）"""
    
    def get_token_config(self, model_type: str, model_name: str) -> Optional[TokenCalculationConfig]:
        """获取Token配置"""
        return TokenCalculationConfig(
            provider_name=model_type,
            model_name=model_name,
            tokenizer_type="gpt2",
            cost_per_input_token=0.0,
            cost_per_output_token=0.0
        )
    
    def get_supported_models(self) -> dict[str, list[str]]:
        """获取支持的模型列表"""
        return {
            "openai": ["gpt-3.5-turbo", "gpt-4"],
            "anthropic": ["claude-3-sonnet"]
        }
    
    def is_model_supported(self, model_type: str, model_name: str) -> bool:
        """检查是否支持指定模型"""
        supported = self.get_supported_models()
        return model_type in supported and model_name in supported[model_type]
    
    def refresh_config_cache(self) -> None:
        """刷新配置缓存"""
        pass


class _StubTokenCostCalculator(ITokenCostCalculator):
    """临时 TokenCostCalculator 实现（用于极端情况）"""
    
    def calculate_cost(
        self,
        input_tokens: int,
        output_tokens: int,
        model_type: str,
        model_name: str
    ) -> Optional[TokenCostInfo]:
        """计算成本"""
        return TokenCostInfo(
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            input_cost=0.0,
            output_cost=0.0,
            total_cost=0.0,
            model_type=model_type,
            model_name=model_name
        )
    
    def get_model_pricing_info(self, model_type: str, model_name: str) -> Optional[dict]:
        """获取定价信息"""
        return {
            "input_price": 0.0,
            "output_price": 0.0,
            "currency": "USD"
        }


class _StubRetryLogger(IRetryLogger):
    """临时 RetryLogger 实现（用于极端情况）"""
    
    def log_retry_attempt(self, func_name: str, error: Exception, attempt: int, delay: float) -> None:
        """记录重试尝试"""
        pass


class _StubFallbackLogger(IFallbackLogger):
    """临时 FallbackLogger 实现（用于极端情况）"""
    
    def log_fallback_attempt(self, primary_model: str, fallback_model: str,
                            error: Exception, attempt: int) -> None:
        """记录降级尝试"""
        pass
    
    def log_fallback_success(self, primary_model: str, fallback_model: str,
                           response, attempt: int) -> None:
        """记录降级成功"""
        pass
    
    def log_fallback_failure(self, primary_model: str, error: Exception,
                           total_attempts: int) -> None:
        """记录降级失败"""
        pass
    
    def log_retry_success(self, func_name: str, result, attempt: int) -> None:
        """记录重试成功"""
        pass
    
    def log_retry_failure(self, func_name: str, error: Exception, total_attempts: int) -> None:
        """记录重试失败"""
        pass


class _StubTokenCalculationService(TokenCalculationService):
    """临时 TokenCalculationService 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def count_tokens(self, text: str, model: str) -> int:
        """计算Token数量"""
        return len(text.split())
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """估算成本"""
        return 0.0


class _StubTokenCalculationDecorator(TokenCalculationDecorator):
    """临时 TokenCalculationDecorator 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def count_tokens(self, text: str, model: str) -> int:
        """计算Token数量"""
        return len(text.split())
    
    def estimate_cost(self, tokens: int, model: str) -> float:
        """估算成本"""
        return 0.0


class _StubRetryManager(RetryManager):
    """临时 RetryManager 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def execute_with_retry(self, func, *args, **kwargs):
        """执行带重试的操作"""
        return func(*args, **kwargs)


class _StubFallbackExecutor(FallbackExecutor):
    """临时 FallbackExecutor 实现（用于极端情况）"""
    
    def __init__(self):
        # 不调用父类初始化，避免依赖问题
        pass
    
    def execute_with_fallback(self, primary_func, fallback_funcs, *args, **kwargs):
        """执行带降级的操作"""
        return primary_func(*args, **kwargs)


def _create_fallback_token_config_provider() -> ITokenConfigProvider:
    """创建fallback token config provider"""
    return _StubTokenConfigProvider()


def _create_fallback_token_cost_calculator() -> ITokenCostCalculator:
    """创建fallback token cost calculator"""
    return _StubTokenCostCalculator()


def _create_fallback_retry_logger() -> IRetryLogger:
    """创建fallback retry logger"""
    return _StubRetryLogger()


def _create_fallback_fallback_logger() -> IFallbackLogger:
    """创建fallback fallback logger"""
    return _StubFallbackLogger()


def _create_fallback_token_calculation_service() -> TokenCalculationService:
    """创建fallback token calculation service"""
    return _StubTokenCalculationService()


def _create_fallback_token_calculation_decorator() -> TokenCalculationDecorator:
    """创建fallback token calculation decorator"""
    return _StubTokenCalculationDecorator()


def _create_fallback_retry_manager() -> RetryManager:
    """创建fallback retry manager"""
    return _StubRetryManager()


def _create_fallback_fallback_executor() -> FallbackExecutor:
    """创建fallback fallback executor"""
    return _StubFallbackExecutor()


# 注册LLM注入
_token_config_provider_injection = get_global_injection_registry().register(
    ITokenConfigProvider, _create_fallback_token_config_provider
)
_token_cost_calculator_injection = get_global_injection_registry().register(
    ITokenCostCalculator, _create_fallback_token_cost_calculator
)
_retry_logger_injection = get_global_injection_registry().register(
    IRetryLogger, _create_fallback_retry_logger
)
_fallback_logger_injection = get_global_injection_registry().register(
    IFallbackLogger, _create_fallback_fallback_logger
)
_token_calculation_service_injection = get_global_injection_registry().register(
    TokenCalculationService, _create_fallback_token_calculation_service
)
_token_calculation_decorator_injection = get_global_injection_registry().register(
    TokenCalculationDecorator, _create_fallback_token_calculation_decorator
)
_retry_manager_injection = get_global_injection_registry().register(
    RetryManager, _create_fallback_retry_manager
)
_fallback_executor_injection = get_global_injection_registry().register(
    FallbackExecutor, _create_fallback_fallback_executor
)


@injectable(ITokenConfigProvider, _create_fallback_token_config_provider)
def get_token_config_provider() -> ITokenConfigProvider:
    """获取Token配置提供者实例
    
    Returns:
        ITokenConfigProvider: Token配置提供者实例
    """
    return _token_config_provider_injection.get_instance()


@injectable(ITokenCostCalculator, _create_fallback_token_cost_calculator)
def get_token_cost_calculator() -> ITokenCostCalculator:
    """获取Token成本计算器实例
    
    Returns:
        ITokenCostCalculator: Token成本计算器实例
    """
    return _token_cost_calculator_injection.get_instance()


@injectable(IRetryLogger, _create_fallback_retry_logger)
def get_retry_logger() -> IRetryLogger:
    """获取重试日志记录器实例
    
    Returns:
        IRetryLogger: 重试日志记录器实例
    """
    return _retry_logger_injection.get_instance()


@injectable(IFallbackLogger, _create_fallback_fallback_logger)
def get_fallback_logger() -> IFallbackLogger:
    """获取降级日志记录器实例
    
    Returns:
        IFallbackLogger: 降级日志记录器实例
    """
    return _fallback_logger_injection.get_instance()


@injectable(TokenCalculationService, _create_fallback_token_calculation_service)
def get_token_calculation_service() -> TokenCalculationService:
    """获取Token计算服务实例
    
    Returns:
        TokenCalculationService: Token计算服务实例
    """
    return _token_calculation_service_injection.get_instance()


@injectable(TokenCalculationDecorator, _create_fallback_token_calculation_decorator)
def get_token_calculation_decorator() -> TokenCalculationDecorator:
    """获取Token计算装饰器实例
    
    Returns:
        TokenCalculationDecorator: Token计算装饰器实例
    """
    return _token_calculation_decorator_injection.get_instance()


@injectable(RetryManager, _create_fallback_retry_manager)
def get_retry_manager() -> RetryManager:
    """获取重试管理器实例
    
    Returns:
        RetryManager: 重试管理器实例
    """
    return _retry_manager_injection.get_instance()


@injectable(FallbackExecutor, _create_fallback_fallback_executor)
def get_fallback_executor() -> FallbackExecutor:
    """获取降级执行器实例
    
    Returns:
        FallbackExecutor: 降级执行器实例
    """
    return _fallback_executor_injection.get_instance()


# 设置实例的函数
def set_token_config_provider_instance(token_config_provider: ITokenConfigProvider) -> None:
    """在应用启动时设置全局 TokenConfigProvider 实例
    
    Args:
        token_config_provider: ITokenConfigProvider 实例
    """
    _token_config_provider_injection.set_instance(token_config_provider)


def set_token_cost_calculator_instance(token_cost_calculator: ITokenCostCalculator) -> None:
    """在应用启动时设置全局 TokenCostCalculator 实例
    
    Args:
        token_cost_calculator: ITokenCostCalculator 实例
    """
    _token_cost_calculator_injection.set_instance(token_cost_calculator)


def set_retry_logger_instance(retry_logger: IRetryLogger) -> None:
    """在应用启动时设置全局 RetryLogger 实例
    
    Args:
        retry_logger: IRetryLogger 实例
    """
    _retry_logger_injection.set_instance(retry_logger)


def set_fallback_logger_instance(fallback_logger: IFallbackLogger) -> None:
    """在应用启动时设置全局 FallbackLogger 实例
    
    Args:
        fallback_logger: IFallbackLogger 实例
    """
    _fallback_logger_injection.set_instance(fallback_logger)


def set_token_calculation_service_instance(token_calculation_service: TokenCalculationService) -> None:
    """在应用启动时设置全局 TokenCalculationService 实例
    
    Args:
        token_calculation_service: TokenCalculationService 实例
    """
    _token_calculation_service_injection.set_instance(token_calculation_service)


def set_token_calculation_decorator_instance(token_calculation_decorator: TokenCalculationDecorator) -> None:
    """在应用启动时设置全局 TokenCalculationDecorator 实例
    
    Args:
        token_calculation_decorator: TokenCalculationDecorator 实例
    """
    _token_calculation_decorator_injection.set_instance(token_calculation_decorator)


def set_retry_manager_instance(retry_manager: RetryManager) -> None:
    """在应用启动时设置全局 RetryManager 实例
    
    Args:
        retry_manager: RetryManager 实例
    """
    _retry_manager_injection.set_instance(retry_manager)


def set_fallback_executor_instance(fallback_executor: FallbackExecutor) -> None:
    """在应用启动时设置全局 FallbackExecutor 实例
    
    Args:
        fallback_executor: FallbackExecutor 实例
    """
    _fallback_executor_injection.set_instance(fallback_executor)


# 清除实例的函数
def clear_token_config_provider_instance() -> None:
    """清除全局 TokenConfigProvider 实例"""
    _token_config_provider_injection.clear_instance()


def clear_token_cost_calculator_instance() -> None:
    """清除全局 TokenCostCalculator 实例"""
    _token_cost_calculator_injection.clear_instance()


def clear_retry_logger_instance() -> None:
    """清除全局 RetryLogger 实例"""
    _retry_logger_injection.clear_instance()


def clear_fallback_logger_instance() -> None:
    """清除全局 FallbackLogger 实例"""
    _fallback_logger_injection.clear_instance()


def clear_token_calculation_service_instance() -> None:
    """清除全局 TokenCalculationService 实例"""
    _token_calculation_service_injection.clear_instance()


def clear_token_calculation_decorator_instance() -> None:
    """清除全局 TokenCalculationDecorator 实例"""
    _token_calculation_decorator_injection.clear_instance()


def clear_retry_manager_instance() -> None:
    """清除全局 RetryManager 实例"""
    _retry_manager_injection.clear_instance()


def clear_fallback_executor_instance() -> None:
    """清除全局 FallbackExecutor 实例"""
    _fallback_executor_injection.clear_instance()


# 获取状态的函数
def get_token_config_provider_status() -> dict:
    """获取Token配置提供者注入状态"""
    return _token_config_provider_injection.get_status()


def get_token_cost_calculator_status() -> dict:
    """获取Token成本计算器注入状态"""
    return _token_cost_calculator_injection.get_status()


def get_retry_logger_status() -> dict:
    """获取重试日志记录器注入状态"""
    return _retry_logger_injection.get_status()


def get_fallback_logger_status() -> dict:
    """获取降级日志记录器注入状态"""
    return _fallback_logger_injection.get_status()


def get_token_calculation_service_status() -> dict:
    """获取Token计算服务注入状态"""
    return _token_calculation_service_injection.get_status()


def get_token_calculation_decorator_status() -> dict:
    """获取Token计算装饰器注入状态"""
    return _token_calculation_decorator_injection.get_status()


def get_retry_manager_status() -> dict:
    """获取重试管理器注入状态"""
    return _retry_manager_injection.get_status()


def get_fallback_executor_status() -> dict:
    """获取降级执行器注入状态"""
    return _fallback_executor_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_token_config_provider",
    "get_token_cost_calculator",
    "get_retry_logger",
    "get_fallback_logger",
    "get_token_calculation_service",
    "get_token_calculation_decorator",
    "get_retry_manager",
    "get_fallback_executor",
    "set_token_config_provider_instance",
    "set_token_cost_calculator_instance",
    "set_retry_logger_instance",
    "set_fallback_logger_instance",
    "set_token_calculation_service_instance",
    "set_token_calculation_decorator_instance",
    "set_retry_manager_instance",
    "set_fallback_executor_instance",
    "clear_token_config_provider_instance",
    "clear_token_cost_calculator_instance",
    "clear_retry_logger_instance",
    "clear_fallback_logger_instance",
    "clear_token_calculation_service_instance",
    "clear_token_calculation_decorator_instance",
    "clear_retry_manager_instance",
    "clear_fallback_executor_instance",
    "get_token_config_provider_status",
    "get_token_cost_calculator_status",
    "get_retry_logger_status",
    "get_fallback_logger_status",
    "get_token_calculation_service_status",
    "get_token_calculation_decorator_status",
    "get_retry_manager_status",
    "get_fallback_executor_status",
]