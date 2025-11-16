"""重放功能依赖注入配置"""

from typing import Optional
from src.infrastructure.container import EnhancedDependencyContainer
from src.application.replay.replay_processor import ReplayProcessor
from src.application.replay.replay_analyzer import ReplayAnalyzer
from src.infrastructure.replay.config_service import ReplayConfigService
from src.infrastructure.replay.replay_source_adapter import HistoryCheckpointReplaySource
from src.domain.replay.interfaces import IReplayEngine, IReplayAnalyzer, IReplaySource
from src.domain.history.interfaces import IHistoryManager
from src.domain.checkpoint.interfaces import ICheckpointManager
from src.infrastructure.common.cache.cache_manager import CacheManager
from src.infrastructure.common.monitoring.performance_monitor import PerformanceMonitor


def register_replay_services(container: EnhancedDependencyContainer) -> None:
    """注册重放相关服务
    
    Args:
        container: 依赖注入容器
    """
    
    # 配置服务
    container.register(
        ReplayConfigService,
        ReplayConfigService,
        lifetime="singleton"
    )
    
    # 回放数据源适配器
    container.register(
        IReplaySource,
        HistoryCheckpointReplaySource,
        lifetime="singleton"
    )
    
    # 回放处理器
    container.register(
        IReplayEngine,
        ReplayProcessor,
        lifetime="singleton"
    )
    
    # 回放分析器
    container.register(
        IReplayAnalyzer,
        ReplayAnalyzer,
        lifetime="singleton"
    )


def register_replay_services_with_dependencies(
    container: EnhancedDependencyContainer,
    history_manager: IHistoryManager,
    checkpoint_manager: ICheckpointManager,
    cache_manager: Optional[CacheManager] = None,
    performance_monitor: Optional[PerformanceMonitor] = None
) -> None:
    """注册重放服务并指定依赖
    
    Args:
        container: 依赖注入容器
        history_manager: 历史管理器实例
        checkpoint_manager: 检查点管理器实例
        cache_manager: 缓存管理器实例
        performance_monitor: 性能监控器实例
    """
    
    # 注册已提供的依赖
    container.register_instance(IHistoryManager, history_manager)
    container.register_instance(ICheckpointManager, checkpoint_manager)
    
    if cache_manager:
        container.register_instance(CacheManager, cache_manager)
    
    if performance_monitor:
        container.register_instance(PerformanceMonitor, performance_monitor)
    
    # 注册重放服务
    register_replay_services(container)