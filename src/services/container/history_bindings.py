"""History相关服务依赖注入绑定配置

统一注册History管理、统计、追踪、成本计算等服务。
"""

from src.services.logger import get_logger
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
from src.adapters.repository.history import SQLiteHistoryRepository, MemoryHistoryRepository
from src.core.common.types import ServiceLifetime
from src.interfaces.common_infra import ILogger

# 导入日志绑定
from .logger_bindings import register_logger_services

logger = get_logger(__name__)


def register_history_services(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册所有History相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    
    示例配置:
    ```yaml
    history:
      storage:
        primary_backend: sqlite
        sqlite:
          db_path: ./data/history.db
        memory:
          max_records: 10000
      
      manager:
        enable_async_batching: true
        batch_size: 10
        batch_timeout: 1.0
      
      cost_calculator:
        custom_pricing:
          gpt-4-custom:
            input_price: 0.025
            output_price: 0.05
            currency: "USD"
            provider: "openai"
      
      token_tracker:
        cache_ttl: 300
    ```
    """
    logger.info("开始注册History服务...")
    
    try:
        # 首先注册日志服务
        register_logger_services(container, config, environment)
        
        # 注册存储后端
        register_history_storage(container, config, environment)
        
        # 注册核心服务
        register_history_manager(container, config, environment)
        register_cost_calculator(container, config, environment)
        register_token_tracker(container, config, environment)
        register_statistics_service(container, config, environment)
        
        # 注册钩子服务
        register_history_hooks(container, config, environment)
        
        logger.info("History服务注册完成")
        
    except Exception as e:
        logger.error(f"注册History服务失败: {e}")
        raise


def register_history_storage(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History存储服务"""
    logger.info("注册History存储服务...")
    
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
        logger.info(f"注册SQLite History存储: {db_path}")
    
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
        logger.info(f"注册内存History存储: max_records={max_records}")
    
    else:
        raise ValueError(f"不支持的History存储后端: {primary_backend}")


def register_history_manager(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History管理器"""
    logger.info("注册History管理器...")
    
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
    
    logger.info(f"注册History管理器: async_batching={enable_async_batching}, "
                f"batch_size={batch_size}, timeout={batch_timeout}")


def register_cost_calculator(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册成本计算器"""
    logger.info("注册成本计算器...")
    
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
        logger.info(f"注册成本计算器，自定义定价模型数量: {len(custom_pricing)}")
    else:
        logger.info("注册成本计算器，使用默认定价")


def register_token_tracker(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册Token追踪器"""
    logger.info("注册Token追踪器...")
    
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
    
    container.register_factory(
        ITokenTracker,
        lambda: WorkflowTokenTracker(
            storage=container.get(IHistoryRepository),
            token_calculation_service=container.get(TokenCalculationService),
            cache_ttl=cache_ttl
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info(f"注册Token追踪器: cache_ttl={cache_ttl}s")


def register_statistics_service(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册统计服务"""
    logger.info("注册统计服务...")
    
    container.register_factory(
        HistoryStatisticsService,
        lambda: HistoryStatisticsService(
            storage=container.get(IHistoryRepository),
            logger=container.get(ILogger, default=None)
        ),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    logger.info("注册统计服务完成")


def register_history_hooks(
    container,
    config: Dict[str, Any],
    environment: str = "default"
) -> None:
    """注册History钩子服务"""
    logger.info("注册History钩子服务...")
    
    # 注册HistoryRecordingHook工厂
    def create_history_hook(workflow_context: Optional[Dict[str, Any]] = None):
        return HistoryRecordingHook(
            history_manager=container.get(IHistoryManager),
            token_calculation_service=container.get(TokenCalculationService),
            cost_calculator=container.get(ICostCalculator),
            workflow_context=workflow_context or {}
        )
    
    container.register_factory(
        HistoryRecordingHook,
        create_history_hook,
        environment=environment,
        lifetime=ServiceLifetime.TRANSIENT  # 钩子通常是瞬态的
    )
    
    logger.info("注册History钩子服务完成")


def register_history_test_services(
    container,
    environment: str = "test"
) -> None:
    """注册测试环境的History服务"""
    logger.info("注册测试环境History服务...")
    
    test_config = {
        "history": {
            "storage": {
                "primary_backend": "memory",
                "memory": {
                    "max_records": 1000
                }
            },
            "manager": {
                "enable_async_batching": False,
                "batch_size": 5,
                "batch_timeout": 0.5
            },
            "token_tracker": {
                "cache_ttl": 60
            }
        }
    }
    
    register_history_services(container, test_config, environment)
    logger.info("测试环境History服务注册完成")


def get_history_service_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """获取History服务配置摘要
    
    Args:
        config: 完整配置字典
        
    Returns:
        Dict[str, Any]: History服务配置摘要
    """
    history_config = config.get("history", {})
    
    return {
        "storage_backend": history_config.get("storage", {}).get("primary_backend", "sqlite"),
        "async_batching": history_config.get("manager", {}).get("enable_async_batching", True),
        "batch_size": history_config.get("manager", {}).get("batch_size", 10),
        "custom_pricing_models": len(history_config.get("cost_calculator", {}).get("custom_pricing", {})),
        "token_tracker_cache_ttl": history_config.get("token_tracker", {}).get("cache_ttl", 300)
    }


def validate_history_config(config: Dict[str, Any]) -> tuple[bool, list[str]]:
    """验证History服务配置
    
    Args:
        config: 配置字典
        
    Returns:
        tuple[bool, list[str]]: (是否有效, 错误列表)
    """
    errors = []
    
    if "history" not in config:
        errors.append("缺少history配置节")
        return False, errors
    
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
    
    return len(errors) == 0, errors