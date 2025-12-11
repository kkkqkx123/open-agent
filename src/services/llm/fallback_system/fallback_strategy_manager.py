"""降级策略管理器

负责策略的初始化和管理，包括 Core 层和 Services 层的策略。
"""

from typing import Optional
from src.interfaces.llm import IFallbackStrategy
# 从基础设施层导入降级配置
from src.infrastructure.llm.fallback import FallbackConfig
from src.infrastructure.llm.fallback import FallbackEngine

# Services 层的导入
from src.interfaces.llm import ITaskGroupManager, IPollingPoolManager
from src.core.llm.wrappers.fallback_manager import (
    GroupBasedFallbackStrategy,
    PollingPoolFallbackStrategy,
)


class FallbackStrategyManager:
    """降级策略管理器
    
    负责策略的初始化和管理，包括：
    1. Core 层策略的初始化和管理
    2. Services 层策略的初始化和管理
    3. 策略的动态切换和配置
    4. 策略的延迟初始化
    """
    
    def __init__(self, 
                 config: Optional[FallbackConfig] = None,
                 task_group_manager: Optional[ITaskGroupManager] = None,
                 polling_pool_manager: Optional[IPollingPoolManager] = None):
        """
        初始化降级策略管理器
        
        Args:
            config: 降级配置
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
        """
        self.config = config
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        
        # Core 层策略
        self._strategy: Optional[IFallbackStrategy] = None
        
        # Services 层策略
        self._group_strategy: Optional[GroupBasedFallbackStrategy] = None
        self._pool_strategy: Optional[PollingPoolFallbackStrategy] = None
        
        # 延迟初始化策略，避免循环依赖
        self._strategies_initialized = False
    
    def _initialize_strategies(self):
        """延迟初始化策略，避免循环依赖"""
        if self._strategies_initialized:
            return
            
        # Core 层策略初始化
        if self.config:
            self._engine = FallbackEngine(self.config)
        
        # Services 层策略初始化
        if self.task_group_manager:
            self._group_strategy = GroupBasedFallbackStrategy(self.task_group_manager)
        if self.polling_pool_manager:
            self._pool_strategy = PollingPoolFallbackStrategy(self.polling_pool_manager)
            
        self._strategies_initialized = True
    
    def get_core_strategy(self) -> Optional[IFallbackStrategy]:
        """
        获取 Core 层策略
        
        Returns:
            Core 层策略实例
        """
        self._initialize_strategies()
        return self._strategy
    
    def get_group_strategy(self) -> Optional[GroupBasedFallbackStrategy]:
        """
        获取任务组策略
        
        Returns:
            任务组策略实例
        """
        self._initialize_strategies()
        return self._group_strategy
    
    def get_pool_strategy(self) -> Optional[PollingPoolFallbackStrategy]:
        """
        获取轮询池策略
        
        Returns:
            轮询池策略实例
        """
        self._initialize_strategies()
        return self._pool_strategy
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置并重新初始化策略
        
        Args:
            config: 新的降级配置
        """
        self.config = config
        self._engine = FallbackEngine(config)
        self._strategies_initialized = False  # 重新初始化策略
    
    def update_task_group_manager(self, task_group_manager: ITaskGroupManager) -> None:
        """
        更新任务组管理器并重新初始化策略
        
        Args:
            task_group_manager: 新的任务组管理器
        """
        self.task_group_manager = task_group_manager
        self._strategies_initialized = False  # 重新初始化策略
    
    def update_polling_pool_manager(self, polling_pool_manager: IPollingPoolManager) -> None:
        """
        更新轮询池管理器并重新初始化策略
        
        Args:
            polling_pool_manager: 新的轮询池管理器
        """
        self.polling_pool_manager = polling_pool_manager
        self._strategies_initialized = False  # 重新初始化策略
    
    def is_parallel_strategy(self) -> bool:
        """
        检查是否是并行降级策略
        
        Returns:
            是否是并行降级策略
        """
        self._initialize_strategies()
        if not self._strategy:
            return False
        
        from .strategies import ParallelFallbackStrategy
        return isinstance(self._strategy, ParallelFallbackStrategy)
    
    def get_strategy_type(self) -> Optional[str]:
        """
        获取策略类型
        
        Returns:
            策略类型名称
        """
        self._initialize_strategies()
        if not self._strategy:
            return None
        
        return type(self._strategy).__name__
    
    def has_group_strategy(self) -> bool:
        """
        检查是否有任务组策略
        
        Returns:
            是否有任务组策略
        """
        self._initialize_strategies()
        return self._group_strategy is not None
    
    def has_pool_strategy(self) -> bool:
        """
        检查是否有轮询池策略
        
        Returns:
            是否有轮询池策略
        """
        self._initialize_strategies()
        return self._pool_strategy is not None
    
    def reset_strategies(self) -> None:
        """重置所有策略"""
        self._strategy = None
        self._group_strategy = None
        self._pool_strategy = None
        self._strategies_initialized = False