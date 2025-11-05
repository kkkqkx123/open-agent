"""支持Hook的Graph构建器

集成Hook机制的Graph构建器。
"""

from typing import Dict, Any, Optional, List, Callable, Union, TYPE_CHECKING, cast
from pathlib import Path
import yaml
import logging

from .builder import GraphBuilder, NodeWithAdapterExecutor, EnhancedNodeWithAdapterExecutor
from .config import GraphConfig, NodeConfig
from .states import WorkflowState
from .registry import BaseNode
from .plugins.manager import PluginManager

if TYPE_CHECKING:
    from .nodes.hookable_node import create_hookable_node_class
    from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class HookAwareGraphBuilder(GraphBuilder):
    """支持Hook的Graph构建器"""
    
    def __init__(
        self,
        node_registry=None,
        template_registry=None,
        state_collaboration_manager: Optional['IStateCollaborationManager'] = None,
        plugin_manager: Optional[PluginManager] = None
    ) -> None:
        """初始化HookAwareGraphBuilder
        
        Args:
            node_registry: 节点注册表
            template_registry: 模板注册表
            state_collaboration_manager: 状态协作管理器
            plugin_manager: 插件管理器
        """
        super().__init__(
            node_registry=node_registry,
            template_registry=template_registry,
            state_collaboration_manager=state_collaboration_manager
        )
        self.plugin_manager = plugin_manager
    
    def create_node_executor(
        self, 
        node_config: NodeConfig,
        node_instance: BaseNode
    ) -> Union[NodeWithAdapterExecutor, EnhancedNodeWithAdapterExecutor]:
        """创建节点执行器（支持Hook）
        
        Args:
            node_config: 节点配置
            node_instance: 节点实例
            
        Returns:
            节点执行器
        """
        # 如果有插件管理器，创建支持Hook的节点
        if self.plugin_manager and hasattr(node_instance, 'node_type'):
            from .nodes.hookable_node import create_hookable_node_class
            
            hookable_node_class = create_hookable_node_class(
                type(node_instance),
                plugin_manager=self.plugin_manager
            )
            
            hookable_node = hookable_node_class()
            
            # 创建适配器执行器
            return NodeWithAdapterExecutor(
                node=hookable_node,
                adapter=self.state_collaboration_manager.get_adapter(node_instance.node_type)
                if self.state_collaboration_manager else None
            )
        
        # 否则使用原始逻辑
        return super().create_node_executor(node_config, node_instance)
    
    def build_from_config(
        self, 
        config_path: str,
        config: Optional[GraphConfig] = None
    ) -> 'WorkflowState':
        """从配置构建工作流（支持Hook）
        
        Args:
            config_path: 配置文件路径
            config: 图配置对象
            
        Returns:
            工作流状态
        """
        # 初始化插件管理器（如果需要）
        if self.plugin_manager and not self.plugin_manager._initialized:
            self.plugin_manager.initialize()
        
        # 调用父类方法
        return super().build_from_config(config_path, config)