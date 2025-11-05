"""支持Hook的节点基类

提供Hook机制集成到节点系统的基类实现。
"""

from typing import Dict, Any, Optional, Callable, TYPE_CHECKING
from abc import abstractmethod

from ..registry import BaseNode, NodeExecutionResult
from ..plugins.interfaces import HookContext, HookPoint, HookExecutionResult

if TYPE_CHECKING:
    from ..plugins.manager import PluginManager


class HookableNode(BaseNode):
    """支持Hook的节点基类
    
    简化设计，直接集成Hook功能，避免多层包装。
    """
    
    def __init__(self, plugin_manager: Optional['PluginManager'] = None) -> None:
        """初始化HookableNode
        
        Args:
            plugin_manager: 插件管理器实例
        """
        super().__init__()
        self._plugin_manager = plugin_manager
    
    @property
    def plugin_manager(self) -> Optional['PluginManager']:
        """获取插件管理器"""
        return self._plugin_manager
    
    def execute(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑（带Hook支持）"""
        manager = self.plugin_manager
        if not manager:
            # 如果没有插件管理器，直接执行核心逻辑
            return self._execute_core(state, config)
        
        node_type = self.node_type
        
        # 使用统一的Hook执行接口
        return manager.execute_with_hooks(
            node_type=node_type,
            state=state,
            config=config,
            node_executor_func=self._execute_core
        )
    
    @abstractmethod
    def _execute_core(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点核心逻辑（子类需要实现）
        
        Args:
            state: 当前Agent状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        raise NotImplementedError("子类必须实现 _execute_core 方法")


def create_hookable_node_class(
    node_class: type,
    plugin_manager: Optional['PluginManager'] = None
) -> type:
    """创建支持Hook的节点类
    
    Args:
        node_class: 原始节点类
        plugin_manager: 插件管理器实例
        
    Returns:
        type: 支持Hook的节点类
    """
    class HookableNodeClass(HookableNode):
        """支持Hook的节点类"""
        
        def __init__(self, *args, **kwargs) -> None:
            """初始化节点"""
            # 提取plugin_manager参数
            self._plugin_manager_arg = kwargs.pop('plugin_manager', plugin_manager)
            
            # 创建原始节点实例
            self._original_node = node_class(*args, **kwargs)
            
            # 初始化HookableNode
            super().__init__(self._plugin_manager_arg)
        
        @property
        def node_type(self) -> str:
            """节点类型标识"""
            return self._original_node.node_type
        
        def _execute_core(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
            """调用原始节点的execute方法"""
            return self._original_node.execute(state, config)
        
        def get_config_schema(self) -> Dict[str, Any]:
            """获取节点配置Schema"""
            return self._original_node.get_config_schema()
        
        def validate_config(self, config: Dict[str, Any]) -> list:
            """验证节点配置"""
            return self._original_node.validate_config(config)
        
        def __getattr__(self, name):
            """代理其他属性到原始节点"""
            return getattr(self._original_node, name)
    
    # 保持原始类的名称和文档
    HookableNodeClass.__name__ = f"Hookable{node_class.__name__}"
    HookableNodeClass.__qualname__ = f"Hookable{node_class.__qualname__}"
    if hasattr(node_class, '__doc__'):
        HookableNodeClass.__doc__ = node_class.__doc__
    
    return HookableNodeClass