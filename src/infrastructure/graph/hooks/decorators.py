"""Hook装饰器

提供装饰器来简化Hook机制集成到现有节点系统。
"""

import functools
from typing import Dict, Any, Optional, Callable

from .interfaces import IHookManager, HookContext, HookPoint, HookExecutionResult
from .manager import NodeHookManager
from ..registry import BaseNode, NodeExecutionResult


def with_hooks(hook_manager: Optional[IHookManager] = None):
    """Hook装饰器工厂函数
    
    Args:
        hook_manager: Hook管理器实例，如果为None则尝试从全局获取
        
    Returns:
        Callable: 装饰器函数
    """
    def decorator(execute_method: Callable) -> Callable:
        """装饰器函数
        
        Args:
            execute_method: 节点执行方法
            
        Returns:
            Callable: 装饰后的执行方法
        """
        @functools.wraps(execute_method)
        def wrapper(self, state, config: Dict[str, Any]) -> NodeExecutionResult:
            """包装的执行方法
            
            Args:
                self: 节点实例
                state: Agent状态
                config: 节点配置
                
            Returns:
                NodeExecutionResult: 执行结果
            """
            # 获取Hook管理器
            manager = hook_manager or _get_hook_manager()
            if not manager:
                # 如果没有Hook管理器，直接执行原方法
                return execute_method(self, state, config)
            
            # 获取节点类型
            node_type = getattr(self, 'node_type', self.__class__.__name__)
            
            # 创建Hook上下文
            context = HookContext(
                node_type=node_type,
                state=state,
                config=config,
                hook_point=HookPoint.BEFORE_EXECUTE
            )
            
            # 执行前置Hook
            before_result = manager.execute_hooks(HookPoint.BEFORE_EXECUTE, context)
            
            # 检查是否需要中断执行
            if not before_result.should_continue:
                # Hook要求中断执行
                result = NodeExecutionResult(
                    state=before_result.modified_state or state,
                    next_node=before_result.force_next_node,
                    metadata={
                        "interrupted_by_hooks": True,
                        "hook_metadata": before_result.metadata
                    }
                )
                return result
            
            # 更新状态（如果Hook修改了状态）
            if before_result.modified_state:
                state = before_result.modified_state
            
            # 执行节点逻辑
            try:
                result = execute_method(self, state, config)
                
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
                    # Hook要求中断错误处理
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
        
        return wrapper
    return decorator


def hook_node(hook_manager: Optional[IHookManager] = None):
    """节点类装饰器
    
    Args:
        hook_manager: Hook管理器实例
        
    Returns:
        Callable: 类装饰器
    """
    def decorator(node_class: type) -> type:
        """类装饰器
        
        Args:
            node_class: 节点类
            
        Returns:
            type: 装饰后的节点类
        """
        # 保存原始的execute方法
        original_execute = node_class.execute
        
        # 应用Hook装饰器
        node_class.execute = with_hooks(hook_manager)(original_execute)
        
        return node_class
    return decorator




def _get_hook_manager() -> Optional[IHookManager]:
    """获取全局Hook管理器
    
    Returns:
        Optional[IHookManager]: Hook管理器实例
    """
    try:
        # 尝试从依赖容器获取
        from src.infrastructure.container import get_global_container
        container = get_global_container()
        return container.get(IHookManager)  # type: ignore
    except Exception:
        # 如果无法获取，返回None
        return None


# 全局Hook管理器实例
_global_hook_manager: Optional[IHookManager] = None


def set_global_hook_manager(hook_manager: IHookManager) -> None:
    """设置全局Hook管理器
    
    Args:
        hook_manager: Hook管理器实例
    """
    global _global_hook_manager
    _global_hook_manager = hook_manager


def get_global_hook_manager() -> Optional[IHookManager]:
    """获取全局Hook管理器
    
    Returns:
        Optional[IHookManager]: Hook管理器实例
    """
    return _global_hook_manager


def clear_global_hook_manager() -> None:
    """清除全局Hook管理器"""
    global _global_hook_manager
    _global_hook_manager = None