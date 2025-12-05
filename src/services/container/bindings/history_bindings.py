"""History相关服务依赖注入绑定配置

统一注册History管理、统计、追踪、成本计算等服务。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
"""

import sys
from typing import Dict, Any, Optional

from src.interfaces.history import IHistoryManager, ICostCalculator
from src.core.history.interfaces import ITokenTracker
from src.interfaces.repository.history import IHistoryRepository
from src.services.history.manager import HistoryManager
from src.services.history.statistics_service import HistoryStatisticsService
from src.services.history.cost_calculator import CostCalculator
from src.services.history.token_tracker import WorkflowTokenTracker
from src.services.history.hooks import HistoryRecordingHook
from src.services.llm.token_calculation_service import TokenCalculationService
from src.services.llm.token_calculation_decorator import TokenCalculationDecorator
from src.adapters.repository.history import SQLiteHistoryRepository, MemoryHistoryRepository
from src.interfaces.common_infra import ServiceLifetime
from src.interfaces.logger import ILogger
from src.services.container.core.base_service_bindings import BaseServiceBindings


class HistoryServiceBindings(BaseServiceBindings):
    """History服务绑定类
    
    负责注册所有History相关服务，包括：
    - History存储后端
    - History管理器
    - 成本计算器
    - Token追踪器
    - 统计服务
    - History钩子
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证History配置"""
        errors = []
        
        if "history" not in config:
            errors.append("缺少history配置节")
        else:
            history_config = config["history"]
            
            # 验证存储配置
            if "storage" not in history_config:
                errors.append("缺少storage配置")
            else:
                storage_config = history_config["storage"]
                primary_backend = storage_config.get("primary_backend")
                
                if not primary_backend:
                    errors.append("storage.primary_backend不能为空")
                elif primary_backend not in ["sqlite", "memory"]:
                    errors.append(f"不支持的存储后端: {primary_backend}")
                
                # 验证SQLite配置
                if primary_backend == "sqlite":
                    sqlite_config = storage_config.get("sqlite", {})
                    if not sqlite_config.get("db_path"):
                        errors.append("SQLite存储需要配置db_path")
            
            # 验证管理器配置
            if "manager" in history_config:
                manager_config = history_config["manager"]
                batch_size = manager_config.get("batch_size", 10)
                batch_timeout = manager_config.get("batch_timeout", 1.0)
                
                if not isinstance(batch_size, int) or batch_size <= 0:
                    errors.append("manager.batch_size必须是正整数")
                
                if not isinstance(batch_timeout, (int, float)) or batch_timeout <= 0:
                    errors.append("manager.batch_timeout必须是正数")
            
            # 验证成本计算器配置
            if "cost_calculator" in history_config:
                calculator_config = history_config["cost_calculator"]
                custom_pricing = calculator_config.get("custom_pricing", {})
                
                if isinstance(custom_pricing, dict):
                    for model_name, pricing in custom_pricing.items():
                        if not isinstance(pricing, dict):
                            errors.append(f"模型{model_name}的定价配置必须是字典")
                            continue
                        
                        input_price = pricing.get("input_price")
                        output_price = pricing.get("output_price")
                        
                        if input_price is not None and (not isinstance(input_price, (int, float)) or input_price < 0):
                            errors.append(f"模型{model_name}的input_price必须是非负数")
                        
                        if output_price is not None and (not isinstance(output_price, (int, float)) or output_price < 0):
                            errors.append(f"模型{model_name}的output_price必须是非负数")
            
            # 验证Token追踪器配置
            if "token_tracker" in history_config:
                tracker_config = history_config["token_tracker"]
                cache_ttl = tracker_config.get("cache_ttl", 300)
                
                if not isinstance(cache_ttl, int) or cache_ttl < 0:
                    errors.append("token_tracker.cache_ttl必须是非负整数")
        
        if errors:
            raise ValueError(f"History配置验证失败: {errors}")
    
    def _do_register_services(
        self,
        container,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行History服务注册"""
        _register_history_storage(container, config, environment)
        _register_history_manager(container, config, environment)
        _register_cost_calculator(container, config, environment)
        _register_token_tracker(container, config, environment)
        _register_statistics_service(container, config, environment)
        _register_history_hooks(container, config, environment)
    
    def _post_register(
        self,
        container,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为History服务设置注入层
            service_types = [
                IHistoryManager,
                ICostCalculator,
                ITokenTracker,
                IHistoryRepository,
                HistoryStatisticsService,
                HistoryRecordingHook,
                TokenCalculationService,
                TokenCalculationDecorator
            ]
            
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.history.injection import (
                set_history_manager_instance,
                set_cost_calculator_instance,
                set_token_tracker_instance,
                set_history_repository_instance,
                set_statistics_service_instance,
                set_history_hooks_instance,
                set_token_calculation_service_instance,
                set_token_calculation_decorator_instance
            )
            
            if container.has_service(IHistoryManager):
                set_history_manager_instance(container.get(IHistoryManager))
            
            if container.has_service(ICostCalculator):
                set_cost_calculator_instance(container.get(ICostCalculator))
            
            if container.has_service(ITokenTracker):
                set_token_tracker_instance(container.get(ITokenTracker))
            
            if container.has_service(IHistoryRepository):
                set_history_repository_instance(container.get(IHistoryRepository))
            
            if container.has_service(HistoryStatisticsService):
                set_statistics_service_instance(container.get(HistoryStatisticsService))
            
            if container.has_service(HistoryRecordingHook):
                set_history_hooks_instance(container.get(HistoryRecordingHook))
            
            if container.has_service(TokenCalculationService):
                set_token_calculation_service_instance(container.get(TokenCalculationService))
            
            if container.has_service(TokenCalculationDecorator):
                set_token_calculation_decorator_instance(container.get(TokenCalculationDecorator))
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置History服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置History注入层失败: {e}", file=sys.stderr)


def _register_history_storage(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History存储服务"""
    print(f"[INFO] 注册History存储服务...", file=sys.stdout)
    
    history_config = config.get("history", {})
    storage_config = history_config.get("storage", {})
    primary_backend = storage_config.get("primary_backend", "sqlite")
    
    # 注册SQLite存储
    if primary_backend == "sqlite":
        sqlite_config = storage_config.get("sqlite", {})
        db_path = sqlite_config.get("db_path", "./data/history.db")
        
        container.register_factory(
            IHistoryRepository,
            lambda: SQLiteHistoryRepository({"db_path": db_path}),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        print(f"[INFO] 注册SQLite History存储: {db_path}", file=sys.stdout)
    
    # 注册内存存储（用于测试）
    elif primary_backend == "memory":
        memory_config = storage_config.get("memory", {})
        max_records = memory_config.get("max_records", 10000)
        
        container.register_factory(
            IHistoryRepository,
            lambda: MemoryHistoryRepository({"max_records": max_records}),
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
        print(f"[INFO] 注册内存History存储: max_records={max_records}", file=sys.stdout)
    
    else:
        raise ValueError(f"不支持的History存储后端: {primary_backend}")


def _register_history_manager(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History管理器"""
    print(f"[INFO] 注册History管理器...", file=sys.stdout)
    
    history_config = config.get("history", {})
    manager_config = history_config.get("manager", {})
    
    enable_async_batching = manager_config.get("enable_async_batching", True)
    batch_size = manager_config.get("batch_size", 10)
    batch_timeout = manager_config.get("batch_timeout", 1.0)
    
    container.register_factory(
        IHistoryManager,
        lambda: HistoryManager(
            storage=container.get(IHistoryRepository),
            enable_async_batching=enable_async_batching,
            batch_size=batch_size,
            batch_timeout=batch_timeout,
            logger=container.get(ILogger, default=None)
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册History管理器: async_batching={enable_async_batching}, "
          f"batch_size={batch_size}, timeout={batch_timeout}", file=sys.stdout)


def _register_cost_calculator(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册成本计算器"""
    print(f"[INFO] 注册成本计算器...", file=sys.stdout)
    
    history_config = config.get("history", {})
    calculator_config = history_config.get("cost_calculator", {})
    custom_pricing = calculator_config.get("custom_pricing", {})
    
    container.register_factory(
        ICostCalculator,
        lambda: CostCalculator(pricing_config=custom_pricing),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    if custom_pricing:
        print(f"[INFO] 注册成本计算器，自定义定价模型数量: {len(custom_pricing)}", file=sys.stdout)
    else:
        print(f"[INFO] 注册成本计算器，使用默认定价", file=sys.stdout)


def _register_token_tracker(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token追踪器"""
    print(f"[INFO] 注册Token追踪器...", file=sys.stdout)
    
    history_config = config.get("history", {})
    tracker_config = history_config.get("token_tracker", {})
    cache_ttl = tracker_config.get("cache_ttl", 300)
    
    # 确保TokenCalculationService已注册
    if not container.has_service(TokenCalculationService):
        container.register(
            TokenCalculationService,
            TokenCalculationService,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    # 优先使用装饰器，如果不存在则使用基础服务
    def get_token_service():
        if container.has_service(TokenCalculationDecorator):
            return container.get(TokenCalculationDecorator)
        else:
            return container.get(TokenCalculationService)
    
    container.register_factory(
        ITokenTracker,
        lambda: WorkflowTokenTracker(
            storage=container.get(IHistoryRepository),
            token_calculation_service=get_token_service(),
            cache_ttl=cache_ttl
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册Token追踪器: cache_ttl={cache_ttl}s", file=sys.stdout)


def _register_statistics_service(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册统计服务"""
    print(f"[INFO] 注册统计服务...", file=sys.stdout)
    
    container.register_factory(
        HistoryStatisticsService,
        lambda: HistoryStatisticsService(
            storage=container.get(IHistoryRepository),
            logger=container.get(ILogger, default=None)
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] 注册统计服务完成", file=sys.stdout)


def _register_history_hooks(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History钩子服务"""
    print(f"[INFO] 注册History钩子服务...", file=sys.stdout)
    
    # 注册HistoryRecordingHook工厂
    def create_history_hook(workflow_context: Optional[Dict[str, Any]] = None):
        # 优先使用装饰器，如果不存在则使用基础服务
        def get_token_service():
            if container.has_service(TokenCalculationDecorator):
                return container.get(TokenCalculationDecorator)
            else:
                return container.get(TokenCalculationService)
        
        return HistoryRecordingHook(
            history_manager=container.get(IHistoryManager),
            token_calculation_service=get_token_service(),
            cost_calculator=container.get(ICostCalculator),
            workflow_context=workflow_context or {}
        )
    
    container.register_factory(
        HistoryRecordingHook,
        create_history_hook,
        environment=environment,
        lifetime=ServiceLifetime.TRANSIENT  # 钩子通常是瞬态的
    )
    
    print(f"[INFO] 注册History钩子服务完成", file=sys.stdout)

