"""LLM服务依赖注入绑定配置

统一注册LLM相关的服务，包括Token计算、配置管理等。
"""

from src.services.logger import get_logger
from typing import Dict, Any, Optional

from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    IRetryLogger,
    IFallbackLogger
)
from src.interfaces.common_infra import ILogger
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.services.llm.config import (
    ProviderConfigTokenConfigProvider,
    ProviderConfigTokenCostCalculator
)
from src.services.llm.retry.retry_manager import RetryManager
from src.services.llm.fallback_system.fallback_executor import FallbackExecutor
from src.services.llm.retry.strategies import DefaultRetryLogger
from src.services.llm.fallback_system.strategies import ConditionalFallback
from src.core.config.config_manager import ConfigManager as LLMConfigManager
from src.infrastructure.llm.config import ConfigDiscovery
from src.infrastructure.llm.retry import RetryConfig
from src.infrastructure.llm.fallback import FallbackConfig
from src.core.config.config_loader import ConfigLoader
from src.core.common.types import ServiceLifetime

logger = get_logger(__name__)


def register_llm_services(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册所有LLM相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    
    示例配置:
    ```yaml
    llm:
      token_calculation:
        default_provider: "openai"
        enable_config_provider: true
        enable_cost_calculator: true
      
      config_manager:
        base_path: "configs/llms"
        enable_provider_configs: true
    ```
    """
    logger.info("开始注册LLM服务...")
    
    try:
        # 注册配置加载器
        register_config_loader(container, config, environment)
        
        # 注册配置管理器
        register_config_manager(container, config, environment)
        
        # 注册Provider配置发现器
        register_provider_discovery(container, config, environment)
        
        # 注册Token配置提供者
        register_token_config_provider(container, config, environment)
        
        # 注册Token成本计算器
        register_token_cost_calculator(container, config, environment)
        
        # 注册基础Token计算服务
        register_token_calculation_service(container, config, environment)
        
        # 注册Token计算装饰器
        register_token_calculation_decorator(container, config, environment)
        
        # 注册重试服务
        register_retry_services(container, config, environment)
        
        # 注册降级服务
        register_fallback_services(container, config, environment)
        
        logger.info("LLM服务注册完成")
        
    except Exception as e:
        logger.error(f"注册LLM服务失败: {e}")
        raise


def register_config_loader(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册配置加载器"""
    logger.info("注册配置加载器...")
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    container.register_factory(
        ConfigLoader,
        lambda: ConfigLoader(base_path),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info(f"注册配置加载器: base_path={base_path}")


def register_config_manager(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册LLM配置管理器"""
    logger.info("注册LLM配置管理器...")
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    container.register_factory(
        LLMConfigManager,
        lambda: LLMConfigManager(
            base_path=base_path
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info(f"注册LLM配置管理器: base_path={base_path}")


def register_provider_discovery(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Provider配置发现器"""
    logger.info("注册Provider配置发现器...")
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    container.register_factory(
        ConfigDiscovery,
        lambda: ConfigDiscovery(config_dir=base_path),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info("注册Provider配置发现器完成")


def register_token_config_provider(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token配置提供者"""
    logger.info("注册Token配置提供者...")
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    enable_config_provider = token_calc_config.get("enable_config_provider", True)
    
    if enable_config_provider:
        container.register_factory(
            ITokenConfigProvider,
            lambda: ProviderConfigTokenConfigProvider(
                config_discovery=container.get(ConfigDiscovery)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 同时注册具体实现类
        container.register_factory(
            ProviderConfigTokenConfigProvider,
            lambda: ProviderConfigTokenConfigProvider(
                config_discovery=container.get(ConfigDiscovery)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("注册Token配置提供者完成")
    else:
        logger.info("Token配置提供者已禁用")


def register_token_cost_calculator(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token成本计算器"""
    logger.info("注册Token成本计算器...")
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    enable_cost_calculator = token_calc_config.get("enable_cost_calculator", True)
    
    if enable_cost_calculator and container.has_service(ITokenConfigProvider):
        container.register_factory(
            ITokenCostCalculator,
            lambda: ProviderConfigTokenCostCalculator(
                config_provider=container.get(ITokenConfigProvider)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 同时注册具体实现类
        container.register_factory(
            ProviderConfigTokenCostCalculator,
            lambda: ProviderConfigTokenCostCalculator(
                config_provider=container.get(ITokenConfigProvider)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("注册Token成本计算器完成")
    else:
        logger.info("Token成本计算器已禁用或缺少依赖")


def register_token_calculation_service(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册基础Token计算服务"""
    logger.info("注册基础Token计算服务...")
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    default_provider = token_calc_config.get("default_provider", "openai")
    
    container.register_factory(
        TokenCalculationService,
        lambda: TokenCalculationService(default_provider=default_provider),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info(f"注册基础Token计算服务: default_provider={default_provider}")


def register_token_calculation_decorator(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token计算装饰器"""
    logger.info("注册Token计算装饰器...")
    
    def create_decorator():
        base_service = container.get(TokenCalculationService)
        config_provider = container.get(ITokenConfigProvider, default=None)
        cost_calculator = container.get(ITokenCostCalculator, default=None)
        
        return TokenCalculationDecorator(
            base_service=base_service,
            config_provider=config_provider,
            cost_calculator=cost_calculator
        )
    
    container.register_factory(
        TokenCalculationDecorator,
        create_decorator,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info("注册Token计算装饰器完成")


def register_llm_test_services(
    container,
    environment: str = "test"
) -> None:
    """注册测试环境的LLM服务"""
    logger.info("注册测试环境LLM服务...")
    
    test_config = {
        "llm": {
            "token_calculation": {
                "default_provider": "openai",
                "enable_config_provider": False,  # 测试环境禁用配置提供者
                "enable_cost_calculator": False   # 测试环境禁用成本计算器
            },
            "config_manager": {
                "base_path": "configs/llms",
                "enable_provider_configs": False
            },
            "retry": {
                "enabled": False,  # 测试环境禁用重试
                "max_attempts": 3,
                "base_delay": 0.1
            },
            "fallback": {
                "enabled": False,  # 测试环境禁用降级
                "max_attempts": 2,
                "fallback_models": []
            }
        }
    }
    
    register_llm_services(container, test_config, environment)
    logger.info("测试环境LLM服务注册完成")


def get_llm_service_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """获取LLM服务配置摘要
    
    Args:
        config: 完整配置字典
        
    Returns:
        Dict[str, Any]: LLM服务配置摘要
    """
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    config_manager_config = llm_config.get("config_manager", {})
    
    retry_config = llm_config.get("retry", {})
    fallback_config = llm_config.get("fallback", {})
    
    return {
        "default_provider": token_calc_config.get("default_provider", "openai"),
        "config_provider_enabled": token_calc_config.get("enable_config_provider", True),
        "cost_calculator_enabled": token_calc_config.get("enable_cost_calculator", True),
        "provider_configs_enabled": config_manager_config.get("enable_provider_configs", True),
        "config_base_path": config_manager_config.get("base_path", "configs/llms"),
        "retry_enabled": retry_config.get("enabled", True),
        "fallback_enabled": fallback_config.get("enabled", True)
    }


def validate_llm_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """验证LLM服务配置
    
    Args:
        config: 配置字典
        
    Returns:
        tuple[bool, list[str]]: (是否有效, 错误列表)
    """
    errors = []
    
    if "llm" not in config:
        errors.append("缺少llm配置节")
        return False, errors
    
    llm_config = config["llm"]
    
    # 验证Token计算配置
    if "token_calculation" in llm_config:
        token_calc_config = llm_config["token_calculation"]
        default_provider = token_calc_config.get("default_provider")
        
        if default_provider and not isinstance(default_provider, str):
            errors.append("token_calculation.default_provider必须是字符串")
    
    # 验证配置管理器配置
    if "config_manager" in llm_config:
        config_manager_config = llm_config["config_manager"]
        base_path = config_manager_config.get("base_path")
        
        if base_path and not isinstance(base_path, str):
            errors.append("config_manager.base_path必须是字符串")
    
    # 验证重试配置
    if "retry" in llm_config:
        retry_config = llm_config["retry"]
        if not isinstance(retry_config, dict):
            errors.append("retry配置必须是字典")
        else:
            max_attempts = retry_config.get("max_attempts")
            if max_attempts is not None and (not isinstance(max_attempts, int) or max_attempts < 1):
                errors.append("retry.max_attempts必须是大于0的整数")
            
            base_delay = retry_config.get("base_delay")
            if base_delay is not None and (not isinstance(base_delay, (int, float)) or base_delay < 0):
                errors.append("retry.base_delay必须是非负数")
    
    # 验证降级配置
    if "fallback" in llm_config:
        fallback_config = llm_config["fallback"]
        if not isinstance(fallback_config, dict):
            errors.append("fallback配置必须是字典")
        else:
            max_attempts = fallback_config.get("max_attempts")
            if max_attempts is not None and (not isinstance(max_attempts, int) or max_attempts < 1):
                errors.append("fallback.max_attempts必须是大于0的整数")
            
            fallback_models = fallback_config.get("fallback_models")
            if fallback_models is not None and not isinstance(fallback_models, list):
                errors.append("fallback.fallback_models必须是列表")
    
    return len(errors) == 0, errors


def register_retry_services(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册重试相关服务"""
    logger.info("注册重试服务...")
    
    llm_config = config.get("llm", {})
    retry_config = llm_config.get("retry", {})
    enable_retry = retry_config.get("enabled", True)
    
    if enable_retry:
        # 注册重试配置
        container.register_factory(
            RetryConfig,
            lambda: RetryConfig.from_dict(retry_config),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册重试日志记录器
        container.register_factory(
            IRetryLogger,
            lambda: DefaultRetryLogger(retry_config.get("logging", {}).get("enabled", True)),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册重试管理器
        container.register_factory(
            RetryManager,
            lambda: RetryManager(
                config=container.get(RetryConfig),
                logger=container.get(IRetryLogger)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.info("重试服务注册完成")
    else:
        logger.info("重试服务已禁用")


def register_fallback_services(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册降级相关服务"""
    logger.info("注册降级服务...")
    
    llm_config = config.get("llm", {})
    fallback_config = llm_config.get("fallback", {})
    enable_fallback = fallback_config.get("enabled", True)
    
    if enable_fallback:
        # 注册降级配置
        container.register_factory(
            FallbackConfig,
            lambda: FallbackConfig.from_dict(fallback_config),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册降级日志记录器
        container.register_factory(
            IFallbackLogger,
            lambda: DefaultRetryLogger(fallback_config.get("logging", {}).get("enabled", True)),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册降级执行器
        container.register_factory(
            FallbackExecutor,
            lambda: FallbackExecutor(
                config=container.get(FallbackConfig),
                logger=container.get(IFallbackLogger)
            ),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册条件降级工具类
        container.register_instance(
            ConditionalFallback,
            ConditionalFallback(),
            environment=environment
        )
        
        logger.info("降级服务注册完成")
    else:
        logger.info("降级服务已禁用")