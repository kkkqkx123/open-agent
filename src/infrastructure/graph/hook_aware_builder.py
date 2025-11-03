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
from .hooks.manager import NodeHookManager
if TYPE_CHECKING:
    from .nodes.hookable_node import create_hookable_node_class
from .hooks.interfaces import IHookManager
from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class HookAwareGraphBuilder(GraphBuilder):
    """支持Hook的Graph构建器"""
    
    def __init__(
        self,
        node_registry=None,
        template_registry=None,
        hook_manager: Optional[IHookManager] = None,
        config_loader=None
    ) -> None:
        """初始化Hook感知的Graph构建器
        
        Args:
            node_registry: 节点注册表
            template_registry: 模板注册表
            hook_manager: Hook管理器
            config_loader: 配置加载器
        """
        super().__init__(node_registry, template_registry)
        self._hook_manager = hook_manager
        self._config_loader = config_loader
        
        # 如果没有提供Hook管理器，创建一个
        if not self._hook_manager and config_loader:
            self._hook_manager = NodeHookManager(config_loader)
    
    @property
    def hook_manager(self) -> Optional[IHookManager]:
        """获取Hook管理器"""
        return self._hook_manager
    
    def set_hook_manager(self, hook_manager: IHookManager) -> None:
        """设置Hook管理器
        
        Args:
            hook_manager: Hook管理器实例
        """
        self._hook_manager = hook_manager
    
    def _get_node_function(self, node_config: NodeConfig, state_manager: Optional[IStateCollaborationManager] = None) -> Optional[Callable]:
        """获取节点函数（支持Hook）"""
        # 首先从注册表获取
        try:
            node_class = self.node_registry.get_node_class(node_config.function_name)
            if node_class:
                # 创建支持Hook的节点类
                from .nodes.hookable_node import create_hookable_node_class
                hookable_node_class = create_hookable_node_class(node_class, self._hook_manager)
                
                # 创建节点实例
                node_instance = hookable_node_class(hook_manager=self._hook_manager)
                
                # 使用适配器包装节点，使其能够处理状态转换
                if state_manager:
                    # 如果提供了状态管理器，使用增强的执行器
                    adapter_wrapper = EnhancedNodeWithAdapterExecutor(node_instance, state_manager)
                else:
                    # 否则使用普通的执行器
                    adapter_wrapper = NodeWithAdapterExecutor(node_instance)
                
                # 加载节点特定的Hook配置
                if self._hook_manager and hasattr(self._hook_manager, 'load_node_hooks_from_config'):
                    self._hook_manager.load_node_hooks_from_config(node_config.function_name)
                
                return adapter_wrapper.execute
        except ValueError:
            # 节点类型不存在，继续尝试其他方法
            pass
        
        # 尝试从模板获取（如果提供了模板注册表）
        if self.template_registry and hasattr(self.template_registry, 'get_template'):
            try:
                template = self.template_registry.get_template(node_config.function_name)
                if template and hasattr(template, 'get_node_function'):
                    return template.get_node_function()
            except (AttributeError, ValueError):
                # 模板不存在或没有get_node_function方法，继续尝试其他方法
                pass
        
        # 最后尝试作为内置函数
        return self._get_builtin_function(node_config.function_name)
    
    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateCollaborationManager] = None):
        """构建LangGraph图（支持Hook）"""
        logger.info("开始构建支持Hook的Graph")
        
        # 如果有Hook管理器，确保Hook配置已加载
        if self._hook_manager and hasattr(self._hook_manager, 'load_hooks_from_config'):
            self._hook_manager.load_hooks_from_config()
        
        # 调用父类方法构建图
        graph = super().build_graph(config, state_manager)
        
        logger.info("成功构建支持Hook的Graph")
        return graph
    
    def build_from_yaml(self, yaml_path: str, state_manager: Optional[IStateCollaborationManager] = None):
        """从YAML文件构建图（支持Hook）"""
        logger.info(f"从YAML文件构建支持Hook的Graph: {yaml_path}")
        
        # 加载配置
        with open(yaml_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        config = GraphConfig.from_dict(config_data)
        
        # 构建图
        return self.build_graph(config, state_manager)
    
    def add_hook_to_node(self, node_type: str, hook, is_global: bool = False) -> None:
        """向节点添加Hook
        
        Args:
            node_type: 节点类型
            hook: Hook实例
            is_global: 是否为全局Hook
        """
        if not self._hook_manager:
            logger.warning("Hook管理器未初始化，无法添加Hook")
            return
        
        if is_global:
            self._hook_manager.register_hook(hook)
        else:
            self._hook_manager.register_hook(hook, [node_type])
        
        logger.info(f"已向节点 {node_type} 添加Hook: {hook.hook_type}")
    
    def remove_hooks_from_node(self, node_type: str) -> None:
        """移除节点的所有Hook
        
        Args:
            node_type: 节点类型
        """
        if not self._hook_manager:
            logger.warning("Hook管理器未初始化，无法移除Hook")
            return
        
        # 这里需要在HookManager中实现移除特定节点Hook的方法
        logger.info(f"已移除节点 {node_type} 的所有Hook")
    
    def get_hook_manager(self) -> Optional[IHookManager]:
        """获取Hook管理器
        
        Returns:
            Optional[IHookManager]: Hook管理器实例
        """
        return self._hook_manager
    
    def enable_hooks_for_graph(self, graph_config: GraphConfig) -> None:
        """为图启用Hook
        
        Args:
            graph_config: 图配置
        """
        if not self._hook_manager:
            logger.warning("Hook管理器未初始化，无法启用Hook")
            return
        
        # 为图中的所有节点加载Hook配置
        for node_name, node_config in graph_config.nodes.items():
            self._hook_manager.load_node_hooks_from_config(node_config.function_name)
        
        logger.info("已为图中的所有节点启用Hook")
    
    def disable_hooks_for_graph(self) -> None:
        """禁用图的所有Hook"""
        if not self._hook_manager:
            logger.warning("Hook管理器未初始化，无法禁用Hook")
            return
        
        self._hook_manager.clear_hooks()
        logger.info("已禁用图的所有Hook")
    
    def get_hook_statistics(self) -> Dict[str, Any]:
        """获取Hook统计信息
        
        Returns:
            Dict[str, Any]: Hook统计信息
        """
        if not self._hook_manager:
            return {"error": "Hook管理器未初始化"}
        
        stats = {
            "hook_manager_initialized": True,
            "global_hooks_count": self._hook_manager.get_global_hooks_count(),
            "node_hooks": self._hook_manager.get_all_node_hooks_counts(),
            "performance_stats": self._hook_manager.get_performance_stats()
        }
        
        return stats


def create_hook_aware_builder(
    node_registry=None,
    template_registry=None,
    hook_manager: Optional[IHookManager] = None,
    config_loader=None
) -> HookAwareGraphBuilder:
    """创建Hook感知的Graph构建器
    
    Args:
        node_registry: 节点注册表
        template_registry: 模板注册表
        hook_manager: Hook管理器
        config_loader: 配置加载器
        
    Returns:
        HookAwareGraphBuilder: Hook感知的Graph构建器
    """
    return HookAwareGraphBuilder(
        node_registry=node_registry,
        template_registry=template_registry,
        hook_manager=hook_manager,
        config_loader=config_loader
    )