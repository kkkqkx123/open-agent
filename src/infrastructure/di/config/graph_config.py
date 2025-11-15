"""图和工作流服务DI配置

负责注册图和工作流基础设施相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.graph.registry import NodeRegistry
from src.infrastructure.graph.states import StateFactory, StateSerializer
from src.infrastructure.graph.builder import UnifiedGraphBuilder

logger = logging.getLogger(__name__)


class GraphConfigRegistration:
    """图和工作流服务注册类
    
    负责注册图和工作流基础设施相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册图和工作流服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册图和工作流系统服务")
        
        # 注册节点注册表
        container.register(
            NodeRegistry,
            NodeRegistry,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态工厂
        container.register(
            StateFactory,
            StateFactory,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册状态序列化器
        container.register(
            StateSerializer,
            StateSerializer,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        # 注册图构建器
        container.register_factory(
            UnifiedGraphBuilder,
            lambda: UnifiedGraphBuilder(
                node_registry=container.get(NodeRegistry)
            ),
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("图和工作流系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "node_registry": NodeRegistry,
            "state_factory": StateFactory,
            "state_serializer": StateSerializer,
            "graph_builder": UnifiedGraphBuilder,
        }