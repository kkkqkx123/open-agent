"""历史管理服务依赖注入配置

提供历史管理相关服务的依赖注入配置。
"""

import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

from src.interfaces.container import IDependencyContainer
from src.core.history.interfaces import IHistoryStorage, ITokenTracker
from src.interfaces.history import IHistoryManager, ICostCalculator
from src.core.history.entities import BaseHistoryRecord, RecordType, WorkflowTokenStatistics
from src.services.history.manager import HistoryManager
from src.services.history.hooks import HistoryRecordingHook
from src.services.history.cost_calculator import CostCalculator
from src.services.history.token_tracker import WorkflowTokenTracker
from src.services.history.statistics_service import HistoryStatisticsService
from src.services.llm.token_calculation_service import TokenCalculationService
from src.adapters.storage.adapters.file import FileStateStorageAdapter
from src.core.common.exceptions import ConfigurationError


logger = logging.getLogger(__name__)


def register_history_services(
    container: IDependencyContainer,
    config: Dict[str, Any]
) -> None:
    """
    注册历史管理相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    try:
        history_config = config.get("history", {})
        
        if not history_config.get("enabled", False):
            logger.info("历史管理功能已禁用")
            return
        
        logger.info("开始注册历史管理服务")
        
        # 注册存储适配器
        _register_storage_services(container, history_config)
        
        # 注册Token计算服务
        _register_token_calculation_service(container, history_config)
        
        # 注册成本计算器
        _register_cost_calculator(container, history_config)
        
        # 注册Token追踪器
        _register_token_tracker(container, history_config)
        
        # 注册历史管理器
        _register_history_manager(container, history_config)
        
        # 注册统计服务
        _register_statistics_service(container, history_config)
        
        # 注册历史记录钩子
        _register_history_hook(container, history_config)
        
        logger.info("历史管理服务注册完成")
        
    except Exception as e:
        logger.error(f"注册历史管理服务失败: {e}")
        raise ConfigurationError(f"注册历史管理服务失败: {e}")


def _register_storage_services(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册存储相关服务"""
    try:
        storage_config = history_config.get("storage", {})
        storage_type = storage_config.get("type", "file")
        
        if storage_type == "file":
            storage_path = Path(storage_config.get("path", "./history"))
            storage_path.mkdir(parents=True, exist_ok=True)
            
            from src.services.container import container as global_container
            global_container.register_factory(
                IHistoryStorage,
                lambda c: FileHistoryStorageAdapter(base_path=str(storage_path))
            )
            
            logger.info(f"注册文件存储适配器: {storage_path}")
            
        elif storage_type == "memory":
            from src.adapters.storage.adapters.memory import MemoryStateStorageAdapter
            
            from src.services.container import container as global_container
            global_container.register_factory(
                IHistoryStorage,
                lambda c: MemoryStateStorageAdapter()
            )
            
            logger.info("注册内存存储适配器")
            
        elif storage_type == "sqlite":
            from src.adapters.storage.adapters.sqlite import SQLiteStateStorageAdapter
            from src.services.container import container as global_container
            
            db_path = storage_config.get("db_path", "./history.db")
            global_container.register_factory(
                IHistoryStorage,
                lambda c: SQLiteStateStorageAdapter(db_path=db_path)
            )
            
            logger.info(f"注册SQLite存储适配器: {db_path}")
            
        else:
            raise ConfigurationError(f"不支持的存储类型: {storage_type}")
            
    except Exception as e:
        raise ConfigurationError(f"注册存储服务失败: {e}")


def _register_token_calculation_service(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册Token计算服务"""
    try:
        token_config = history_config.get("token_calculation", {})
        default_provider = token_config.get("default_provider", "openai")
        
        from src.services.container import container as global_container
        global_container.register_factory(
            TokenCalculationService,
            lambda c: TokenCalculationService(default_provider=default_provider)
        )
        
        logger.info(f"注册Token计算服务: 默认提供商={default_provider}")
        
    except Exception as e:
        raise ConfigurationError(f"注册Token计算服务失败: {e}")


def _register_cost_calculator(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册成本计算器"""
    try:
        pricing_config = history_config.get("pricing", {})
        
        from src.services.container import container as global_container
        global_container.register_factory(
            ICostCalculator,
            lambda c: CostCalculator(pricing_config)
        )
        
        logger.info(f"注册成本计算器: 定价配置项={len(pricing_config)}")
        
    except Exception as e:
        raise ConfigurationError(f"注册成本计算器失败: {e}")


def _register_token_tracker(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册Token追踪器"""
    try:
        tracker_config = history_config.get("token_tracker", {})
        cache_ttl = tracker_config.get("cache_ttl", 300)  # 5分钟
        
        from src.services.container import container as global_container
        global_container.register_factory(
            ITokenTracker,
            lambda c: WorkflowTokenTracker(
                storage=c.get(IHistoryStorage),
                token_calculation_service=c.get(TokenCalculationService),
                cache_ttl=cache_ttl
            )
        )
        
        logger.info(f"注册Token追踪器: 缓存TTL={cache_ttl}秒")
        
    except Exception as e:
        raise ConfigurationError(f"注册Token追踪器失败: {e}")


def _register_history_manager(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册历史管理器"""
    try:
        manager_config = history_config.get("manager", {})
        enable_async_batching = manager_config.get("enable_async_batching", True)
        batch_size = manager_config.get("batch_size", 10)
        batch_timeout = manager_config.get("batch_timeout", 1.0)
        
        from src.services.container import container as global_container
        global_container.register_factory(
            IHistoryManager,
            lambda c: HistoryManager(
                storage=c.get(IHistoryStorage),
                enable_async_batching=enable_async_batching,
                batch_size=batch_size,
                batch_timeout=batch_timeout
            )
        )
        
        logger.info(f"注册历史管理器: 批处理={enable_async_batching}, "
                   f"批次大小={batch_size}, 超时={batch_timeout}秒")
        
    except Exception as e:
        raise ConfigurationError(f"注册历史管理器失败: {e}")


def _register_statistics_service(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册统计服务"""
    try:
        from src.services.container import container as global_container
        global_container.register_factory(
            HistoryStatisticsService,
            lambda c: HistoryStatisticsService(storage=c.get(IHistoryStorage))
        )
        
        logger.info("注册历史统计服务")
        
    except Exception as e:
        raise ConfigurationError(f"注册统计服务失败: {e}")


def _register_history_hook(
    container: IDependencyContainer,
    history_config: Dict[str, Any]
) -> None:
    """注册历史记录钩子"""
    try:
        hook_config = history_config.get("hook", {})
        auto_register = hook_config.get("auto_register", True)
        
        if auto_register:
            from src.services.container import container as global_container
            global_container.register_factory(
                HistoryRecordingHook,
                lambda c: HistoryRecordingHook(
                    history_manager=c.get(IHistoryManager),
                    token_calculation_service=c.get(TokenCalculationService),
                    cost_calculator=c.get(ICostCalculator),
                    workflow_context=hook_config.get("workflow_context", {})
                )
            )
            
            logger.info("注册历史记录钩子: 自动注册启用")
        else:
            logger.info("历史记录钩子自动注册已禁用")
        
    except Exception as e:
        raise ConfigurationError(f"注册历史记录钩子失败: {e}")


def register_history_services_with_dependencies(
    container: IDependencyContainer,
    config: Dict[str, Any],
    token_calculation_service: Optional[TokenCalculationService] = None,
    cost_calculator: Optional[CostCalculator] = None
) -> None:
    """
    注册历史管理相关服务（带依赖）
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        token_calculation_service: Token计算器实例
        cost_calculator: 成本计算器实例
    """
    try:
        history_config = config.get("history", {})
        
        if not history_config.get("enabled", False):
            logger.info("历史管理功能已禁用")
            return
        
        logger.info("开始注册历史管理服务（带依赖）")
        
        # 注册存储适配器
        _register_storage_services(container, history_config)
        
        # 注册提供的Token计算服务
        if token_calculation_service:
            from src.services.container import container as global_container
            global_container.register_instance(TokenCalculationService, token_calculation_service)
            logger.info("注册外部Token计算服务")
        else:
            _register_token_calculation_service(container, history_config)
        
        # 注册提供的成本计算器
        if cost_calculator:
            from src.services.container import container as global_container
            global_container.register_instance(ICostCalculator, cost_calculator)
            logger.info("注册外部成本计算器")
        else:
            _register_cost_calculator(container, history_config)
        
        # 注册其他服务
        _register_token_tracker(container, history_config)
        _register_history_manager(container, history_config)
        _register_statistics_service(container, history_config)
        _register_history_hook(container, history_config)
        
        logger.info("历史管理服务注册完成（带依赖）")
        
    except Exception as e:
        logger.error(f"注册历史管理服务失败（带依赖）: {e}")
        raise ConfigurationError(f"注册历史管理服务失败（带依赖）: {e}")


def register_test_history_services(
    container: IDependencyContainer,
    config: Optional[Dict[str, Any]] = None
) -> None:
    """
    注册测试用历史管理服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    try:
        test_config = config or {
            "history": {
                "enabled": True,
                "storage": {
                    "type": "memory"
                },
                "manager": {
                    "enable_async_batching": False  # 测试时禁用批处理
                }
            }
        }
        
        logger.info("注册测试用历史管理服务")
        register_history_services(container, test_config)
        
    except Exception as e:
        logger.error(f"注册测试历史管理服务失败: {e}")
        raise ConfigurationError(f"注册测试历史管理服务失败: {e}")


def get_history_service_config() -> Dict[str, Any]:
    """
    获取历史管理服务的默认配置
    
    Returns:
        Dict[str, Any]: 默认配置
    """
    return {
        "history": {
            "enabled": True,
            "storage": {
                "type": "file",
                "path": "./history"
            },
            "token_calculation": {
                "default_provider": "openai"
            },
            "pricing": {
                # 默认定价配置会在CostCalculator中加载
            },
            "token_tracker": {
                "cache_ttl": 300  # 5分钟
            },
            "manager": {
                "enable_async_batching": True,
                "batch_size": 10,
                "batch_timeout": 1.0
            },
            "hook": {
                "auto_register": True,
                "workflow_context": {}
            }
        }
    }


def validate_history_config(config: Dict[str, Any]) -> bool:
    """
    验证历史管理配置
    
    Args:
        config: 配置字典
        
    Returns:
        bool: 验证是否通过
        
    Raises:
        ConfigurationError: 配置验证失败
    """
    try:
        history_config = config.get("history", {})
        
        if not isinstance(history_config, dict):
            raise ConfigurationError("history配置必须是字典类型")
        
        # 验证存储配置
        storage_config = history_config.get("storage", {})
        if not isinstance(storage_config, dict):
            raise ConfigurationError("storage配置必须是字典类型")
        
        storage_type = storage_config.get("type")
        if storage_type not in ["file", "memory", "sqlite"]:
            raise ConfigurationError(f"不支持的存储类型: {storage_type}")
        
        # 验证Token追踪器配置
        tracker_config = history_config.get("token_tracker", {})
        if not isinstance(tracker_config, dict):
            raise ConfigurationError("token_tracker配置必须是字典类型")
        
        cache_ttl = tracker_config.get("cache_ttl")
        if cache_ttl is not None and (not isinstance(cache_ttl, (int, float)) or cache_ttl <= 0):
            raise ConfigurationError("cache_ttl必须是正数")
        
        # 验证管理器配置
        manager_config = history_config.get("manager", {})
        if not isinstance(manager_config, dict):
            raise ConfigurationError("manager配置必须是字典类型")
        
        batch_size = manager_config.get("batch_size")
        if batch_size is not None and (not isinstance(batch_size, int) or batch_size <= 0):
            raise ConfigurationError("batch_size必须是正整数")
        
        batch_timeout = manager_config.get("batch_timeout")
        if batch_timeout is not None and (not isinstance(batch_timeout, (int, float)) or batch_timeout <= 0):
            raise ConfigurationError("batch_timeout必须是正数")
        
        logger.info("历史管理配置验证通过")
        return True
        
    except Exception as e:
        if isinstance(e, ConfigurationError):
            raise
        logger.error(f"验证历史管理配置失败: {e}")
        raise ConfigurationError(f"验证历史管理配置失败: {e}")


# 为了向后兼容，提供一个简单的文件存储适配器
class FileHistoryStorageAdapter:
    """文件历史存储适配器"""
    
    def __init__(self, base_path: str):
        """
        初始化文件存储适配器
        
        Args:
            base_path: 基础路径
        """
        self.base_path = base_path
    
    async def save_record(self, record: BaseHistoryRecord) -> bool:
        """保存记录"""
        # 这里应该实现实际的文件存储逻辑
        # 为了简化，这里只是返回True
        return True
    
    async def save_records(self, records: List[BaseHistoryRecord]) -> List[bool]:
        """批量保存记录"""
        results = []
        for record in records:
            result = await self.save_record(record)
            results.append(result)
        return results
    
    async def get_record_by_id(self, record_id: str) -> Optional[BaseHistoryRecord]:
        """根据ID获取记录"""
        return None
    
    async def get_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        record_type: Optional[RecordType] = None,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[BaseHistoryRecord]:
        """获取记录"""
        return []
    
    async def get_workflow_token_stats(
        self,
        workflow_id: str,
        model: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[WorkflowTokenStatistics]:
        """获取工作流Token统计"""
        return []
    
    async def update_workflow_token_stats(self, stats: WorkflowTokenStatistics) -> bool:
        """更新工作流Token统计"""
        return True
    
    async def delete_records(
        self,
        session_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        older_than: Optional[datetime] = None
    ) -> int:
        """删除记录"""
        return 0
    
    async def get_storage_statistics(self) -> Dict[str, Any]:
        """获取存储统计"""
        return {"total_records": 0}