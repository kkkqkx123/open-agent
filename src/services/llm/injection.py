"""LLM服务依赖注入便利层

使用通用依赖注入框架提供简洁的LLM服务获取方式。
"""

from typing import Optional
from unittest.mock import Mock

from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    IRetryLogger,
    IFallbackLogger
)
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.services.llm.retry.retry_manager import RetryManager
from src.services.llm.fallback_system.fallback_executor import FallbackExecutor
from src.services.container.injection.injection_base import get_global_injection_registry
from src.services.container.injection.injection_decorators import injectable


def _create_fallback_token_config_provider() -> ITokenConfigProvider:
    """创建fallback Token配置提供者"""
    return Mock(spec=ITokenConfigProvider)


def _create_fallback_token_cost_calculator() -> ITokenCostCalculator:
    """创建fallback Token成本计算器"""
    return Mock(spec=ITokenCostCalculator)


def _create_fallback_retry_logger() -> IRetryLogger:
    """创建fallback重试日志记录器"""
    return Mock(spec=IRetryLogger)


def _create_fallback_fallback_logger() -> IFallbackLogger:
    """创建fallback降级日志记录器"""
    return Mock(spec=IFallbackLogger)


def _create_fallback_token_calculation_service() -> TokenCalculationService:
    """创建fallback Token计算服务"""
    return TokenCalculationService()


def _create_fallback_token_calculation_decorator() -> TokenCalculationDecorator:
    """创建fallback Token计算装饰器"""
    return Mock(spec=TokenCalculationDecorator)


def _create_fallback_retry_manager() -> RetryManager:
    """创建fallback重试管理器"""
    return Mock(spec=RetryManager)


def _create_fallback_fallback_executor() -> FallbackExecutor:
    """创建fallback降级执行器"""
    return Mock(spec=FallbackExecutor)


# 注册LLM服务注入
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


# 设置实例的便捷函数
def set_token_config_provider_instance(provider: ITokenConfigProvider) -> None:
    """设置Token配置提供者实例"""
    _token_config_provider_injection.set_instance(provider)


def set_token_cost_calculator_instance(calculator: ITokenCostCalculator) -> None:
    """设置Token成本计算器实例"""
    _token_cost_calculator_injection.set_instance(calculator)


def set_retry_logger_instance(logger: IRetryLogger) -> None:
    """设置重试日志记录器实例"""
    _retry_logger_injection.set_instance(logger)


def set_fallback_logger_instance(logger: IFallbackLogger) -> None:
    """设置降级日志记录器实例"""
    _fallback_logger_injection.set_instance(logger)


def set_token_calculation_service_instance(service: TokenCalculationService) -> None:
    """设置Token计算服务实例"""
    _token_calculation_service_injection.set_instance(service)


def set_token_calculation_decorator_instance(decorator: TokenCalculationDecorator) -> None:
    """设置Token计算装饰器实例"""
    _token_calculation_decorator_injection.set_instance(decorator)


def set_retry_manager_instance(manager: RetryManager) -> None:
    """设置重试管理器实例"""
    _retry_manager_injection.set_instance(manager)


def set_fallback_executor_instance(executor: FallbackExecutor) -> None:
    """设置降级执行器实例"""
    _fallback_executor_injection.set_instance(executor)


# 清除实例的便捷函数（主要用于测试）
def clear_token_config_provider_instance() -> None:
    """清除Token配置提供者实例"""
    _token_config_provider_injection.clear_instance()


def clear_token_cost_calculator_instance() -> None:
    """清除Token成本计算器实例"""
    _token_cost_calculator_injection.clear_instance()


def clear_retry_logger_instance() -> None:
    """清除重试日志记录器实例"""
    _retry_logger_injection.clear_instance()


def clear_fallback_logger_instance() -> None:
    """清除降级日志记录器实例"""
    _fallback_logger_injection.clear_instance()


def clear_token_calculation_service_instance() -> None:
    """清除Token计算服务实例"""
    _token_calculation_service_injection.clear_instance()


def clear_token_calculation_decorator_instance() -> None:
    """清除Token计算装饰器实例"""
    _token_calculation_decorator_injection.clear_instance()


def clear_retry_manager_instance() -> None:
    """清除重试管理器实例"""
    _retry_manager_injection.clear_instance()


def clear_fallback_executor_instance() -> None:
    """清除降级执行器实例"""
    _fallback_executor_injection.clear_instance()


# 获取状态的便捷函数
def get_token_config_provider_status() -> dict:
    """获取Token配置提供者状态"""
    return _token_config_provider_injection.get_status()


def get_token_cost_calculator_status() -> dict:
    """获取Token成本计算器状态"""
    return _token_cost_calculator_injection.get_status()


def get_retry_logger_status() -> dict:
    """获取重试日志记录器状态"""
    return _retry_logger_injection.get_status()


def get_fallback_logger_status() -> dict:
    """获取降级日志记录器状态"""
    return _fallback_logger_injection.get_status()


def get_token_calculation_service_status() -> dict:
    """获取Token计算服务状态"""
    return _token_calculation_service_injection.get_status()


def get_token_calculation_decorator_status() -> dict:
    """获取Token计算装饰器状态"""
    return _token_calculation_decorator_injection.get_status()


def get_retry_manager_status() -> dict:
    """获取重试管理器状态"""
    return _retry_manager_injection.get_status()


def get_fallback_executor_status() -> dict:
    """获取降级执行器状态"""
    return _fallback_executor_injection.get_status()


# 导出的公共接口
__all__ = [
    # 获取函数
    "get_token_config_provider",
    "get_token_cost_calculator",
    "get_retry_logger",
    "get_fallback_logger",
    "get_token_calculation_service",
    "get_token_calculation_decorator",
    "get_retry_manager",
    "get_fallback_executor",
    
    # 设置函数
    "set_token_config_provider_instance",
    "set_token_cost_calculator_instance",
    "set_retry_logger_instance",
    "set_fallback_logger_instance",
    "set_token_calculation_service_instance",
    "set_token_calculation_decorator_instance",
    "set_retry_manager_instance",
    "set_fallback_executor_instance",
    
    # 清除函数
    "clear_token_config_provider_instance",
    "clear_token_cost_calculator_instance",
    "clear_retry_logger_instance",
    "clear_fallback_logger_instance",
    "clear_token_calculation_service_instance",
    "clear_token_calculation_decorator_instance",
    "clear_retry_manager_instance",
    "clear_fallback_executor_instance",
    
    # 状态函数
    "get_token_config_provider_status",
    "get_token_cost_calculator_status",
    "get_retry_logger_status",
    "get_fallback_logger_status",
    "get_token_calculation_service_status",
    "get_token_calculation_decorator_status",
    "get_retry_manager_status",
    "get_fallback_executor_status",
]