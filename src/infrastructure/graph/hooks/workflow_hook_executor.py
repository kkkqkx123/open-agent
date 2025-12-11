"""工作流Hook执行器实现

从核心层迁移过来的Hook执行器，专门负责Hook的执行逻辑。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, List, Optional, Callable, TYPE_CHECKING
from collections import defaultdict

from src.interfaces.workflow.hooks import IHookExecutor, IHook, HookPoint, HookContext, HookExecutionResult
from src.interfaces.state import IWorkflowState
from src.interfaces.workflow.graph import NodeExecutionResult

# 延迟导入以避免循环依赖
def _get_hook_registry():
    from src.core.workflow.registry import HookRegistry
    return HookRegistry

if TYPE_CHECKING:
    from src.core.state import WorkflowState


logger = get_logger(__name__)


class WorkflowHookExecutor(IHookExecutor):
    """工作流Hook执行器
    
    专门负责Hook的执行逻辑，包括：
    - Hook的获取和过滤
    - Hook点的执行
    - 统一的Hook执行接口（execute_with_hooks）
    - 性能统计和错误处理
    """
    
    def __init__(self, hook_registry: Optional[Any] = None):
        """初始化Hook执行器
        
        Args:
            hook_registry: Hook注册表，如果为None则创建新的
        """
        if hook_registry is None:
            # 动态获取HookRegistry类
            HookRegistry = _get_hook_registry()
            hook_registry = HookRegistry()
        
        self.registry = hook_registry
        self._hooks_cache: Dict[str, List[IHook]] = defaultdict(list)
        self._execution_counters: Dict[str, int] = defaultdict(int)
        self._performance_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
        self._hook_configs: Dict[str, Any] = {}
    
    def _get_workflow_state(self):
        """延迟导入WorkflowState以避免循环导入"""
        from src.core.state import WorkflowState
        return WorkflowState
    
    def set_hook_configs(self, configs: Dict[str, Any]) -> None:
        """设置Hook配置
        
        Args:
            configs: Hook配置字典
        """
        self._hook_configs = configs
        # 清空缓存，因为配置可能已更改
        self._hooks_cache.clear()
    
    def get_enabled_hooks(self, node_type: Optional[str]) -> List[IHook]:
        """获取指定节点的Hook列表
        
        Args:
            node_type: 节点类型
            
        Returns:
            List[IHook]: Hook列表
        """
        # 处理None值
        if node_type is None:
            node_type = "default"
        
        # 从缓存获取
        if node_type in self._hooks_cache:
            return self._hooks_cache[node_type]
        
        hooks = []
        
        # 获取Hook配置
        hook_configs = self._hook_configs.get('hooks', {})
        
        # 处理全局Hook
        global_configs = {c['id']: c for c in hook_configs.get('global', [])}
        for config in global_configs.values():
            if config.get('enabled', False):
                hook = self.registry.get_hook(config['id'])
                if hook and isinstance(hook, IHook):
                    # 初始化Hook
                    if self._initialize_hook(hook, config.get('config', {})):
                        hooks.append((hook, config.get('priority', 50)))
        
        # 处理节点特定Hook
        node_configs = hook_configs.get('node_specific', {}).get(node_type, [])
        for config in node_configs:
            if config.get('enabled', False):
                hook = self.registry.get_hook(config['id'])
                if hook and isinstance(hook, IHook):
                    # 初始化Hook
                    if self._initialize_hook(hook, config.get('config', {})):
                        hooks.append((hook, config.get('priority', 50)))
        
        # 按优先级排序
        hooks.sort(key=lambda x: x[1])
        enabled_hooks = [hook for hook, _ in hooks]
        
        # 缓存结果
        self._hooks_cache[node_type] = enabled_hooks
        
        return enabled_hooks
    
    def _initialize_hook(self, hook: IHook, config: Dict[str, Any]) -> bool:
        """初始化Hook
        
        Args:
            hook: Hook实例
            config: Hook配置
            
        Returns:
            bool: 初始化是否成功
        """
        try:
            # 验证配置
            errors = hook.validate_config(config)
            if errors:
                logger.error(f"Hook {hook.name} 配置验证失败: {errors}")
                return False
            
            # 初始化Hook
            if hook.initialize(config):
                logger.debug(f"Hook {hook.name} 初始化成功")
                return True
            else:
                logger.error(f"Hook {hook.name} 初始化失败")
                return False
                
        except Exception as e:
            logger.error(f"初始化Hook失败 {hook.name}: {e}")
            return False
    
    def execute_hooks(self, hook_point: HookPoint, context: HookContext) -> HookExecutionResult:
        """执行指定Hook点的所有Hook
        
        Args:
            hook_point: Hook执行点
            context: Hook执行上下文
            
        Returns:
            HookExecutionResult: 合并后的Hook执行结果
        """
        hooks = self.get_enabled_hooks(context.node_type)
        
        # 过滤支持当前Hook点的Hook
        applicable_hooks = [
            hook for hook in hooks 
            if hook_point in hook.get_supported_hook_points()
        ]
        
        if not applicable_hooks:
            return HookExecutionResult(should_continue=True)
        
        logger.debug(f"开始执行 {len(applicable_hooks)} 个 {hook_point.value} Hook")
        
        # 执行Hook
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        should_continue = True
        metadata: Dict[str, Any] = {"executed_hooks": []}
        
        for hook in applicable_hooks:
            try:
                hook_start_time = time.time()
                
                # 根据Hook点调用相应方法
                if hook_point == HookPoint.BEFORE_EXECUTE:
                    result = hook.before_execute(context)
                elif hook_point == HookPoint.AFTER_EXECUTE:
                    result = hook.after_execute(context)
                elif hook_point == HookPoint.ON_ERROR:
                    result = hook.on_error(context)
                elif hook_point == HookPoint.BEFORE_COMPILE:
                    result = hook.before_compile(context)
                elif hook_point == HookPoint.AFTER_COMPILE:
                    result = hook.after_compile(context)
                else:
                    continue
                
                hook_execution_time = time.time() - hook_start_time
                
                # 记录Hook执行信息
                metadata["executed_hooks"].append({
                    "hook_name": hook.name,
                    "execution_time": hook_execution_time,
                    "success": True
                })
                
                # 应用Hook结果
                if not result.should_continue:
                    should_continue = False
                
                if result.modified_state:
                    modified_state = result.modified_state
                
                if result.modified_result:
                    modified_result = result.modified_result
                
                if result.force_next_node:
                    force_next_node = result.force_next_node
                
                # 合并元数据
                if result.metadata:
                    metadata.update(result.metadata)
                
                # 如果Hook要求停止执行，则中断后续Hook
                if not should_continue:
                    logger.debug(f"Hook {hook.name} 要求停止执行")
                    break
                    
            except Exception as e:
                logger.error(f"执行Hook {hook.name} 时发生错误: {e}")
                metadata["executed_hooks"].append({
                    "hook_name": hook.name,
                    "success": False,
                    "error": str(e)
                })
                # 继续执行其他Hook，不中断整个流程
        
        return HookExecutionResult(
            should_continue=should_continue,
            modified_state=modified_state,
            modified_result=modified_result,
            force_next_node=force_next_node,
            metadata=metadata
        )
    
    def execute_with_hooks(
        self,
        node_type: str,
        state: IWorkflowState,
        config: Dict[str, Any],
        node_executor_func: Callable[[IWorkflowState, Dict[str, Any]], NodeExecutionResult]
    ) -> NodeExecutionResult:
        """统一的Hook执行接口
        
        Args:
            node_type: 节点类型
            state: 当前状态
            config: 节点配置
            node_executor_func: 节点执行函数
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 增加执行计数
        self.increment_execution_count(node_type)
        
        # 创建前置Hook上下文
        before_context = HookContext(
            hook_point=HookPoint.BEFORE_EXECUTE,
            config=config,
            node_type=node_type,
            state=state
        )
        
        # 执行前置Hook
        before_result = self.execute_hooks(HookPoint.BEFORE_EXECUTE, before_context)
        
        # 检查是否需要中断执行
        if not before_result.should_continue:
            # 类型转换：确保状态类型匹配
            final_state = before_result.modified_state or state
            if hasattr(final_state, 'to_dict'):
                # 如果是IWorkflowState，转换为WorkflowState
                final_state = self._get_workflow_state().from_dict(final_state.to_dict())  # type: ignore
            
            return NodeExecutionResult(
                state=final_state,  # type: ignore
                next_node=before_result.force_next_node,
                metadata={
                    "interrupted_by_hooks": True,
                    "hook_metadata": before_result.metadata
                }
            )
        
        # 更新状态（如果Hook修改了状态）
        if before_result.modified_state:
            # 类型转换：确保状态类型匹配
            if hasattr(before_result.modified_state, 'to_dict'):
                # 如果是IWorkflowState，转换为WorkflowState
                state = self._get_workflow_state().from_dict(before_result.modified_state.to_dict())  # type: ignore
            else:
                state = before_result.modified_state  # type: ignore
        
        # 执行节点逻辑
        try:
            start_time = time.time()
            result = node_executor_func(state, config)
            execution_time = time.time() - start_time
            
            # 更新性能统计
            self.update_performance_stats(node_type, execution_time, success=True)
            
            # 创建后置Hook上下文
            # 注意：这里需要使用接口层的NodeExecutionResult类型
            from src.interfaces.workflow.graph import NodeExecutionResult as InterfaceNodeExecutionResult
            interface_result = InterfaceNodeExecutionResult(
                state=result.state,
                next_node=result.next_node,
                metadata=result.metadata
            )
            
            # 确保 result.state 是 IWorkflowState 类型
            final_state = result.state if isinstance(result.state, IWorkflowState) else state
            
            after_context = HookContext(
                hook_point=HookPoint.AFTER_EXECUTE,
                config=config,
                node_type=node_type,
                state=final_state,
                execution_result=interface_result
            )
            
            # 执行后置Hook
            after_result = self.execute_hooks(HookPoint.AFTER_EXECUTE, after_context)
            
            # 应用Hook结果
            if after_result.modified_state:
                # 类型转换：确保状态类型匹配
                if hasattr(after_result.modified_state, 'to_dict'):
                    # 如果是IWorkflowState，转换为WorkflowState
                    result.state = self._get_workflow_state().from_dict(after_result.modified_state.to_dict())  # type: ignore
                else:
                    result.state = after_result.modified_state  # type: ignore
            
            if after_result.force_next_node:
                result.next_node = after_result.force_next_node
            
            if after_result.metadata:
                if result.metadata is None:
                    result.metadata = {}
                result.metadata.update(after_result.metadata)
            
            return result
            
        except Exception as e:
            # 更新性能统计
            self.update_performance_stats(node_type, 0, success=False)
            
            # 创建错误Hook上下文
            error_context = HookContext(
                hook_point=HookPoint.ON_ERROR,
                config=config,
                node_type=node_type,
                state=state,
                error=e
            )
            
            # 执行错误Hook
            error_result = self.execute_hooks(HookPoint.ON_ERROR, error_context)
            
            # 检查Hook是否处理了错误
            if not error_result.should_continue:
                # 类型转换：确保状态类型匹配
                final_state = error_result.modified_state or state
                if hasattr(final_state, 'to_dict'):
                    # 如果是IWorkflowState，转换为WorkflowState
                    final_state = self._get_workflow_state().from_dict(final_state.to_dict())
                
                return NodeExecutionResult(
                    state=final_state,  # type: ignore
                    next_node=error_result.force_next_node or "error_handler",
                    metadata={
                        "error_handled_by_hooks": True,
                        "original_error": str(e),
                        "hook_metadata": error_result.metadata
                    }
                )
            
            # 如果Hook没有处理错误，重新抛出异常
            raise e
    
    def get_execution_count(self, node_type: str) -> int:
        """获取节点执行次数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 执行次数
        """
        return self._execution_counters[node_type]
    
    def increment_execution_count(self, node_type: str) -> int:
        """增加节点执行计数
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: 增加后的执行次数
        """
        self._execution_counters[node_type] += 1
        return self._execution_counters[node_type]
    
    def update_performance_stats(
        self, 
        node_type: str, 
        execution_time: float, 
        success: bool = True
    ) -> None:
        """更新性能统计
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间
            success: 是否成功
        """
        stats = self._performance_stats[node_type]
        
        if "total_executions" not in stats:
            stats["total_executions"] = 0
            stats["successful_executions"] = 0
            stats["failed_executions"] = 0
            stats["total_execution_time"] = 0.0
            stats["min_execution_time"] = float('inf')
            stats["max_execution_time"] = 0.0
        
        stats["total_executions"] += 1
        stats["total_execution_time"] += execution_time
        
        if success:
            stats["successful_executions"] += 1
        else:
            stats["failed_executions"] += 1
        
        stats["min_execution_time"] = min(stats["min_execution_time"], execution_time)
        stats["max_execution_time"] = max(stats["max_execution_time"], execution_time)
        stats["avg_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 性能统计信息
        """
        return dict(self._performance_stats)
    
    def clear_cache(self) -> None:
        """清空Hook缓存"""
        self._hooks_cache.clear()
    
    def cleanup(self) -> None:
        """清理Hook执行器资源"""
        try:
            # 清空缓存
            self.clear_cache()
            self._execution_counters.clear()
            self._performance_stats.clear()
            self._hook_configs.clear()
            
            logger.info("Hook执行器清理完成")
            
        except Exception as e:
            logger.error(f"Hook执行器清理失败: {e}")