"""Hook管理器

管理Hook的生命周期、配置和执行。
"""

from typing import Dict, Any, List, Optional, Type
from src.interfaces.workflow.hooks import IHook, IHookSystem, HookPoint, HookContext, HookExecutionResult
from src.interfaces.dependency_injection import get_logger
from src.core.workflow.registry import HookRegistry

logger = get_logger(__name__)


class HookManager(IHookSystem):
    """Hook管理器
    
    负责Hook的完整生命周期管理，包括注册、配置、执行和清理。
    """
    
    def __init__(self):
        """初始化Hook管理器"""
        self.registry = HookRegistry()
        self._hook_configs: Dict[str, Any] = {}
        self._initialized_hooks: Dict[str, IHook] = {}
        self._builtin_hooks: List[IHook] = []
    
    def register_hook(
        self,
        hook_point: HookPoint,
        hook: IHook,
        priority: int = 50
    ) -> None:
        """注册Hook
        
        Args:
            hook_point: Hook点
            hook: Hook实例
            priority: 优先级，数值越小优先级越高
        """
        self.registry.register_hook(hook_point, hook, priority)
    
    def unregister_hook(
        self,
        hook_point: HookPoint,
        hook_id: str
    ) -> bool:
        """注销Hook
        
        Args:
            hook_point: Hook点
            hook_id: Hook ID
            
        Returns:
            bool: 是否成功注销
        """
        # 清理已初始化的Hook
        if hook_id in self._initialized_hooks:
            hook = self._initialized_hooks[hook_id]
            try:
                hook.cleanup()
            except Exception as e:
                logger.error(f"清理Hook {hook_id} 时发生错误: {e}")
            finally:
                del self._initialized_hooks[hook_id]
        
        return self.registry.unregister_hook(hook_point, hook_id)
    
    async def execute_hooks(
        self,
        hook_point: HookPoint,
        context: HookContext
    ) -> HookExecutionResult:
        """执行Hook
        
        Args:
            hook_point: Hook点
            context: Hook执行上下文
            
        Returns:
            Hook执行结果
        """
        hooks = self.registry.get_hooks_for_point(hook_point)
        
        if not hooks:
            return HookExecutionResult(should_continue=True)
        
        logger.debug(f"开始执行 {len(hooks)} 个 {hook_point.value} Hook")
        
        # 执行Hook
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        should_continue = True
        metadata: Dict[str, Any] = {"executed_hooks": []}
        
        for hook in hooks:
            try:
                # 确保Hook已初始化
                if hook.hook_id not in self._initialized_hooks:
                    self._initialize_hook(hook)
                
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
                
                # 记录Hook执行信息
                metadata["executed_hooks"].append({
                    "hook_id": hook.hook_id,
                    "hook_name": hook.name,
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
                    "hook_id": hook.hook_id,
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
    
    def get_hooks_for_point(self, hook_point: HookPoint) -> List[IHook]:
        """获取指定Hook点的所有Hook
        
        Args:
            hook_point: Hook点
            
        Returns:
            List[IHook]: Hook列表
        """
        return self.registry.get_hooks_for_point(hook_point)
    
    def clear_hooks(self, hook_point: Optional[HookPoint] = None) -> None:
        """清除Hook
        
        Args:
            hook_point: 要清除的Hook点，如果为None则清除所有
        """
        if hook_point is None:
            # 清理所有已初始化的Hook
            for hook_id, hook in self._initialized_hooks.items():
                try:
                    hook.cleanup()
                except Exception as e:
                    logger.error(f"清理Hook {hook_id} 时发生错误: {e}")
            self._initialized_hooks.clear()
        else:
            # 清理指定Hook点的Hook
            hooks = self.registry.get_hooks_for_point(hook_point)
            for hook in hooks:
                if hook.hook_id in self._initialized_hooks:
                    try:
                        hook.cleanup()
                    except Exception as e:
                        logger.error(f"清理Hook {hook.hook_id} 时发生错误: {e}")
                    finally:
                        del self._initialized_hooks[hook.hook_id]
        
        self.registry.clear_hooks(hook_point)
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        stats = self.registry.get_registry_stats()
        stats.update({
            "initialized_hooks": len(self._initialized_hooks),
            "builtin_hooks": len(self._builtin_hooks)
        })
        return stats
    
    def register_builtin_hooks(self) -> None:
        """注册内置Hook"""
        try:
            from .metrics_collection import MetricsCollectionHook
            from .logging import LoggingHook
            from .performance_monitoring import PerformanceMonitoringHook
            from .dead_loop_detection import DeadLoopDetectionHook
            from .error_recovery import ErrorRecoveryHook
            
            # 注册内置Hook
            builtin_hooks = [
                MetricsCollectionHook(),
                LoggingHook(),
                PerformanceMonitoringHook(),
                DeadLoopDetectionHook(),
                ErrorRecoveryHook()
            ]
            
            for hook in builtin_hooks:
                self._builtin_hooks.append(hook)
                
                # 注册到支持的Hook点
                for hook_point in hook.get_supported_hook_points():
                    self.register_hook(hook_point, hook)
                
                logger.debug(f"已注册内置Hook: {hook.name}")
            
            logger.info(f"已注册 {len(builtin_hooks)} 个内置Hook")
            
        except ImportError as e:
            logger.warning(f"无法导入内置Hook: {e}")
        except Exception as e:
            logger.error(f"注册内置Hook失败: {e}")
    
    def load_hooks_from_config(self, config: Dict[str, Any]) -> None:
        """从配置加载Hook
        
        Args:
            config: Hook配置
        """
        self._hook_configs = config
        
        # 注册内置Hook
        if config.get("enable_builtin", True):
            self.register_builtin_hooks()
        
        # 加载外部Hook
        external_configs = config.get("external_hooks", [])
        for hook_config in external_configs:
            if not hook_config.get("enabled", False):
                continue
            
            try:
                hook = self._load_external_hook(hook_config)
                if hook:
                    # 注册到支持的Hook点
                    for hook_point in hook.get_supported_hook_points():
                        self.register_hook(hook_point, hook, hook_config.get("priority", 50))
                    
                    logger.info(f"已加载外部Hook: {hook.name}")
            except Exception as e:
                logger.error(f"加载外部Hook失败 {hook_config.get('name', 'unknown')}: {e}")
    
    def _load_external_hook(self, config: Dict[str, Any]) -> Optional[IHook]:
        """加载外部Hook
        
        Args:
            config: Hook配置
            
        Returns:
            Optional[IHook]: Hook实例，加载失败则返回None
        """
        module_name = config.get('module')
        class_name = config.get('class')
        
        if not module_name or not class_name:
            logger.error(f"Hook配置缺少module或class: {config}")
            return None
        
        try:
            # 动态导入模块
            import importlib
            module = importlib.import_module(module_name)
            hook_class = getattr(module, class_name)
            
            # 实例化Hook
            hook = hook_class()
            
            # 验证Hook接口
            if not isinstance(hook, IHook):
                logger.error(f"Hook {class_name} 未实现正确的接口")
                return None
            
            return hook
            
        except ImportError as e:
            logger.error(f"无法导入Hook模块 {module_name}: {e}")
            return None
        except AttributeError as e:
            logger.error(f"Hook类 {class_name} 在模块 {module_name} 中不存在: {e}")
            return None
        except Exception as e:
            logger.error(f"实例化Hook失败 {class_name}: {e}")
            return None
    
    def _initialize_hook(self, hook: IHook) -> None:
        """初始化Hook
        
        Args:
            hook: Hook实例
        """
        if hook.hook_id in self._initialized_hooks:
            return
        
        try:
            # 获取Hook配置
            hook_config = self._hook_configs.get("hook_configs", {}).get(hook.hook_id, {})
            
            # 初始化Hook
            if hook.initialize(hook_config):
                self._initialized_hooks[hook.hook_id] = hook
                logger.debug(f"Hook {hook.name} 初始化成功")
            else:
                logger.error(f"Hook {hook.name} 初始化失败")
                
        except Exception as e:
            logger.error(f"初始化Hook失败 {hook.name}: {e}")
    
    def cleanup(self) -> None:
        """清理Hook管理器资源"""
        try:
            # 清理所有已初始化的Hook
            for hook_id, hook in self._initialized_hooks.items():
                try:
                    hook.cleanup()
                except Exception as e:
                    logger.error(f"清理Hook {hook_id} 时发生错误: {e}")
            
            # 清空注册表
            self.registry.clear_hooks()
            self._initialized_hooks.clear()
            self._builtin_hooks.clear()
            self._hook_configs.clear()
            
            logger.info("Hook管理器清理完成")
            
        except Exception as e:
            logger.error(f"Hook管理器清理失败: {e}")