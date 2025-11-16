"""检查点配置注册

负责注册检查点相关的领域层服务。
"""

import logging
from typing import Dict, Type, Any

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.domain.checkpoint.interfaces import ICheckpointStore

logger = logging.getLogger(__name__)


class CheckpointConfigRegistration:
    """检查点配置注册类"""
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册检查点服务
        
        Args:
            container: 依赖注入容器
        """
        logger.info("注册检查点相关服务")
        
        # 注册检查点存储接口实现
        try:
            # 内存存储实现
            from src.infrastructure.checkpoint.memory_store import MemoryCheckpointStore
            container.register(
                interface=ICheckpointStore,
                implementation=MemoryCheckpointStore,
                lifetime=ServiceLifetime.TRANSIENT
            )
            
            # SQLite存储实现
            from src.infrastructure.checkpoint.sqlite_store import SQLiteCheckpointStore
            container.register(
                interface=ICheckpointStore,
                implementation=SQLiteCheckpointStore,
                lifetime=ServiceLifetime.TRANSIENT
            )
            
            logger.debug("检查点存储服务注册完成")
        except ImportError as e:
            logger.warning(f"检查点存储服务注册失败: {e}")
        
        # 注册LangGraph适配器
        try:
            from src.infrastructure.checkpoint.langgraph_adapter import LangGraphAdapter, ILangGraphAdapter
            container.register(
                interface=ILangGraphAdapter,
                implementation=LangGraphAdapter,
                lifetime=ServiceLifetime.SINGLETON
            )
            
            logger.debug("LangGraph适配器注册完成")
        except ImportError as e:
            logger.warning(f"LangGraph适配器注册失败: {e}")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            服务类型字典
        """
        from src.domain.checkpoint.interfaces import ICheckpointStore
        from src.infrastructure.checkpoint.langgraph_adapter import ILangGraphAdapter
        
        return {
            "checkpoint_store": ICheckpointStore,
            "langgraph_adapter": ILangGraphAdapter
        }