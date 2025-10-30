"""支持Hook的节点基类

提供Hook机制集成到节点系统的基类实现。
"""

from typing import Dict, Any, Optional, List
from abc import abstractmethod

from ..registry import BaseNode, NodeExecutionResult
from ..hooks.interfaces import IHookManager, HookContext, HookPoint, HookExecutionResult
from ..hooks.decorators import _get_hook_manager


class HookableNode(BaseNode):
    """支持Hook的节点基类"""
    
    def __init__(self, hook_manager: Optional[IHookManager] = None) -> None:
        """初始化HookableNode
        
        Args:
            hook_manager: Hook管理器实例
        """
        super().__init__()
        self._hook_manager = hook_manager
    
    @property
    def hook_manager(self) -> Optional[IHookManager]:
        """获取Hook管理器"""
        return self._hook_manager or _get_hook_manager()
    
    def execute(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行节点逻辑（带Hook支持）"""
        manager = self.hook_manager
        if not manager:
            # 如果没有Hook管理器，调用子类实现
            return self._execute_without_hooks(state, config)
        
        node_type = self.node_type
        
        # 创建前置Hook上下文
        before_context = HookContext(
            node_type=node_type,
            state=state,
            config=config,
            hook_point=HookPoint.BEFORE_EXECUTE
        )
        
        # 执行前置Hook
        before_result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, before_context)
        
        # 检查是否需要中断执行
        if not before_result.should_continue:
            return NodeExecutionResult(
                state=before_result.modified_state or state,
                next_node=before_result.force_next_node,
                metadata={
                    "interrupted_by_hooks": True,
                    "hook_metadata": before_result.metadata
                }
            )
        
        # 更新状态
        if before_result.modified_state:
            state = before_result.modified_state
        
        # 执行节点逻辑
        try:
            result = self._execute_without_hooks(state, config)
            
            # 创建后置Hook上下文
            after_context = HookContext(
                node_type=node_type,
                state=result.state,
                config=config,
                hook_point=HookPoint.AFTER_EXECUTE,
                execution_result=result
            )
            
            # 执行后置Hook
            after_result = manager.execute_hooks(HookPoint.AFTER_EXECUTE, after_context)
            
            # 应用Hook结果
            if after_result.modified_state:
                result.state = after_result.modified_state
            
            if after_result.force_next_node:
                result.next_node = after_result.force_next_node
            
            if after_result.metadata:
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update(after_result.metadata)
            
            return result
            
        except Exception as e:
            # 创建错误Hook上下文
            error_context = HookContext(
                node_type=node_type,
                state=state,
                config=config,
                hook_point=HookPoint.ON_ERROR,
                error=e
            )
            
            # 执行错误Hook
            error_result = manager.execute_hooks(HookPoint.ON_ERROR, error_context)
            
            # 检查Hook是否处理了错误
            if not error_result.should_continue:
                return NodeExecutionResult(
                    state=error_result.modified_state or state,
                    next_node=error_result.force_next_node or "error_handler",
                    metadata={
                        "error_handled_by_hooks": True,
                        "original_error": str(e),
                        "hook_metadata": error_result.metadata
                    }
                )
            
            # 如果Hook没有处理错误，重新抛出异常
            raise e
    
    @abstractmethod
    def _execute_without_hooks(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
        """不使用Hook的执行逻辑（子类需要实现）
        
        Args:
            state: 当前Agent状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        raise NotImplementedError("子类必须实现 _execute_without_hooks 方法")


def make_node_hookable(node_class: type, hook_manager: Optional[IHookManager] = None) -> type:
    """将现有节点类转换为支持Hook的节点类
    
    Args:
        node_class: 原始节点类
        hook_manager: Hook管理器实例
        
    Returns:
        type: 支持Hook的节点类
    """
    class HookableNodeWrapper(HookableNode):
        """Hookable节点包装器"""
        
        def __init__(self, *args, **kwargs) -> None:
            """初始化包装器"""
            # 提取hook_manager参数
            self._hook_manager_arg = kwargs.pop('hook_manager', hook_manager)
            
            # 创建原始节点实例
            self._original_node = node_class(*args, **kwargs)
            
            # 初始化HookableNode
            super().__init__(self._hook_manager_arg)
        
        @property
        def node_type(self) -> str:
            """节点类型标识"""
            return self._original_node.node_type
        
        def _execute_without_hooks(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
            """调用原始节点的execute方法"""
            return self._original_node.execute(state, config)
        
        def get_config_schema(self) -> Dict[str, Any]:
            """获取节点配置Schema"""
            return self._original_node.get_config_schema()
        
        def validate_config(self, config: Dict[str, Any]) -> List[str]:
            """验证节点配置"""
            return self._original_node.validate_config(config)
        
        def __getattr__(self, name):
            """代理其他属性到原始节点"""
            return getattr(self._original_node, name)
    
    # 保持原始类的名称和文档
    HookableNodeWrapper.__name__ = f"Hookable{node_class.__name__}"
    HookableNodeWrapper.__qualname__ = f"Hookable{node_class.__qualname__}"
    if hasattr(node_class, '__doc__'):
        HookableNodeWrapper.__doc__ = node_class.__doc__
    
    return HookableNodeWrapper