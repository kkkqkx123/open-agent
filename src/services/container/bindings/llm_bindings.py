"""LLM服务依赖注入绑定配置

统一注册LLM相关的服务，包括Token计算、配置管理等。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
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

# 接口导入 - 集中化的接口定义
from src.interfaces.llm import (
    ITokenConfigProvider,
    ITokenCostCalculator,
    IRetryLogger,
    IFallbackLogger
)
from src.interfaces.logger import ILogger
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class LLMServiceBindings(BaseServiceBindings):
    """LLM服务绑定类
    
    负责注册所有LLM相关服务，包括：
    - 配置加载器和管理器
    - Token计算相关服务
    - 重试和降级服务
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证LLM配置"""
        errors = []
        
        if "llm" not in config:
            errors.append("缺少llm配置节")
        else:
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
        
        if errors:
            raise ValueError(f"LLM配置验证失败: {errors}")
    
    def _do_register_services(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行LLM服务注册"""
        register_config_loader(container, config, environment)
        register_config_manager(container, config, environment)
        register_provider_discovery(container, config, environment)
        register_token_config_provider(container, config, environment)
        register_token_cost_calculator(container, config, environment)
        register_token_calculation_service(container, config, environment)
        register_token_calculation_decorator(container, config, environment)
        register_retry_services(container, config, environment)
        register_fallback_services(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 延迟导入具体实现类，避免循环依赖
            def get_service_types() -> list:
                from src.services.llm.token_calculation_service import TokenCalculationService
                from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
                from src.services.llm.retry.retry_manager import RetryManager
                from src.services.llm.fallback_system.fallback_executor import FallbackExecutor
                
                return [
                    ITokenConfigProvider,
                    ITokenCostCalculator,
                    IRetryLogger,
                    IFallbackLogger,
                    TokenCalculationService,
                    TokenCalculationDecorator,
                    RetryManager,
                    FallbackExecutor
                ]
            
            service_types = get_service_types()
            self.setup_injection_layer(container, service_types)
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置LLM服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置LLM注入层失败: {e}", file=__import__('sys').stderr)


def register_config_loader(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册配置加载器"""
    print(f"[INFO] 注册配置加载器...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    # 延迟导入具体实现
    def create_config_loader() -> 'ConfigLoader':
        from src.core.config.config_loader import ConfigLoader
        return ConfigLoader(base_path)
    
    container.register_factory(
        ConfigLoader,
        create_config_loader,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册配置加载器: base_path={base_path}", file=sys.stdout)


def register_config_manager(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册LLM配置管理器"""
    print(f"[INFO] 注册LLM配置管理器...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    # 延迟导入具体实现
    def create_config_manager() -> 'LLMConfigManager':
        from src.core.config.config_manager import ConfigManager as LLMConfigManager
        
        # ConfigManager 已经实现了 IUnifiedConfigManager 接口的所有方法
        return LLMConfigManager(base_path=base_path)

    container.register_factory(
        LLMConfigManager,
        create_config_manager,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册LLM配置管理器: base_path={base_path}", file=sys.stdout)


def register_provider_discovery(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Provider配置发现器"""
    print(f"[INFO] 注册Provider配置发现器...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    config_manager_config = llm_config.get("config_manager", {})
    base_path = config_manager_config.get("base_path", "configs/llms")
    
    # 延迟导入具体实现
    def create_config_discovery() -> 'ConfigDiscovery':
        from src.infrastructure.llm.config import ConfigDiscovery
        return ConfigDiscovery(config_dir=base_path)
    
    container.register_factory(
        ConfigDiscovery,
        create_config_discovery,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册Provider配置发现器完成", file=sys.stdout)


def register_token_config_provider(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token配置提供者"""
    print(f"[INFO] 注册Token配置提供者...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    enable_config_provider = token_calc_config.get("enable_config_provider", True)
    
    if enable_config_provider:
        # 延迟导入具体实现
        def create_token_config_provider() -> 'ProviderConfigTokenConfigProvider':
            from src.services.llm.config import ProviderConfigTokenConfigProvider
            return ProviderConfigTokenConfigProvider(
                config_discovery=container.get(ConfigDiscovery)
            )
        
        container.register_factory(
            ITokenConfigProvider,
            create_token_config_provider,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 同时注册具体实现类
        container.register_factory(
            ProviderConfigTokenConfigProvider,
            create_token_config_provider,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        print(f"[INFO] 注册Token配置提供者完成", file=sys.stdout)
    else:
        print(f"[INFO] Token配置提供者已禁用", file=sys.stdout)


def register_token_cost_calculator(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token成本计算器"""
    print(f"[INFO] 注册Token成本计算器...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    enable_cost_calculator = token_calc_config.get("enable_cost_calculator", True)
    
    if enable_cost_calculator and container.has_service(ITokenConfigProvider):
        # 延迟导入具体实现
        def create_token_cost_calculator() -> 'ProviderConfigTokenCostCalculator':
            from src.services.llm.config import ProviderConfigTokenCostCalculator
            return ProviderConfigTokenCostCalculator(
                config_provider=container.get(ITokenConfigProvider)
            )
        
        container.register_factory(
            ITokenCostCalculator,
            create_token_cost_calculator,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 同时注册具体实现类
        container.register_factory(
            ProviderConfigTokenCostCalculator,
            create_token_cost_calculator,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        print(f"[INFO] 注册Token成本计算器完成", file=sys.stdout)
    else:
        print(f"[INFO] Token成本计算器已禁用或缺少依赖", file=sys.stdout)


def register_token_calculation_service(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册基础Token计算服务"""
    print(f"[INFO] 注册基础Token计算服务...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    token_calc_config = llm_config.get("token_calculation", {})
    default_provider = token_calc_config.get("default_provider", "openai")
    
    # 延迟导入具体实现
    def create_token_calculation_service() -> 'TokenCalculationService':
        from src.services.llm.token_calculation_service import TokenCalculationService
        return TokenCalculationService(default_provider=default_provider)
    
    container.register_factory(
        TokenCalculationService,
        create_token_calculation_service,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册基础Token计算服务: default_provider={default_provider}", file=sys.stdout)


def register_token_calculation_decorator(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token计算装饰器"""
    print(f"[INFO] 注册Token计算装饰器...", file=sys.stdout)
    
    def create_decorator() -> 'TokenCalculationDecorator':
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
    
    print(f"[INFO] 注册Token计算装饰器完成", file=sys.stdout)




def register_retry_services(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册重试相关服务"""
    print(f"[INFO] 注册重试服务...", file=sys.stdout)
    
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
        
        print(f"[INFO] 重试服务注册完成", file=sys.stdout)
    else:
        print(f"[INFO] 重试服务已禁用", file=sys.stdout)


def register_fallback_services(
    container: Any,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册降级相关服务"""
    print(f"[INFO] 注册降级服务...", file=sys.stdout)
    
    llm_config = config.get("llm", {})
    fallback_config = llm_config.get("fallback", {})
    enable_fallback = fallback_config.get("enabled", True)
    
    if enable_fallback:
        # 延迟导入具体实现
        def create_fallback_config() -> 'FallbackConfig':
            from src.infrastructure.llm.fallback import FallbackConfig
            return FallbackConfig.from_dict(fallback_config)

        def create_fallback_logger() -> 'DefaultRetryLogger':
            from src.services.llm.retry.strategies import DefaultRetryLogger
            return DefaultRetryLogger(fallback_config.get("logging", {}).get("enabled", True))

        def create_fallback_executor() -> 'FallbackExecutor':
            from src.services.llm.fallback_system.fallback_executor import FallbackExecutor
            return FallbackExecutor(
                config=container.get(FallbackConfig),
                logger=container.get(IFallbackLogger)
            )

        def create_conditional_fallback() -> 'ConditionalFallback':
            from src.services.llm.fallback_system.strategies import ConditionalFallback
            return ConditionalFallback()
        
        # 注册降级配置
        container.register_factory(
            FallbackConfig,
            create_fallback_config,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册降级日志记录器
        container.register_factory(
            IFallbackLogger,
            create_fallback_logger,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册降级执行器
        container.register_factory(
            FallbackExecutor,
            create_fallback_executor,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册条件降级工具类
        container.register_instance(
            ConditionalFallback,
            create_conditional_fallback(),
            environment=environment
        )
        
        print(f"[INFO] 降级服务注册完成", file=sys.stdout)
    else:
        print(f"[INFO] 降级服务已禁用", file=sys.stdout)