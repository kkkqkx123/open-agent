"""状态管理DI配置

负责注册状态管理相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.state.interfaces import IStateCrudManager, IStateLifecycleManager
from src.infrastructure.state.state_manager import StateManager
from src.domain.state.collaboration_manager import StateLifecycleManagerImpl
from src.infrastructure.state.interfaces import IStateSnapshotStore, IStateHistoryManager

logger = logging.getLogger(__name__)


class StateConfigRegistration:
    """状态管理注册类
    
    负责注册状态管理相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册状态管理服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册状态管理服务")
        
        # 注册状态CRUD管理器
        container.register(
            IStateCrudManager,
            StateManager,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态生命周期管理器
        container.register_factory(
            IStateLifecycleManager,
            lambda: StateLifecycleManagerImpl(
                crud_manager=container.get(IStateCrudManager),
                snapshot_store=container.get(IStateSnapshotStore),
                history_manager=container.get(IStateHistoryManager)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("状态管理服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "state_crud_manager": IStateCrudManager,
            "state_lifecycle_manager": IStateLifecycleManager,
        }