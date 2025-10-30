"""Hook管理器实现

提供Hook的注册、执行和配置管理功能。
"""

import logging
import time
from typing import Dict, Any, List, Optional, Type, Callable
from collections import defaultdict

from .interfaces import (
    INodeHook, IHookManager, IHookConfigLoader, IHookExecutionService,
    HookContext, HookPoint, HookExecutionResult
)
from .config import (
    HookConfig, NodeHookConfig, GlobalHookConfig,
    HookType, merge_hook_configs
)
from .builtin import create_builtin_hook
from ..registry import NodeExecutionResult

logger = logging.getLogger(__name__)


class HookConfigLoader(IHookConfigLoader):
    """Hook配置加载器"""
    
    def __init__(self, config_loader) -> None:
        """初始化配置加载器
        
        Args:
            config_loader: 基础配置加载器
        """
        self.config_loader = config_loader
    
    def load_global_hooks(self) -> List[Dict[str, Any]]:
        """加载全局Hook配置"""
        try:
            global_config = self.config_loader.load("hooks/global_hooks.yaml")
            return global_config.get("global_hooks", [])
        except Exception as e:
            logger.warning(f"加载全局Hook配置失败: {e}")
            return []
    
    def load_node_hooks(self, node_type: str) -> List[Dict[str, Any]]:
        """加载指定节点的Hook配置"""
        try:
            node_config_path = f"hooks/{node_type}_hooks.yaml"
            node_config = self.config_loader.load(node_config_path)
            return node_config.get(node_type, {}).get("hooks", [])
        except Exception as e:
            logger.debug(f"加载节点 {node_type} Hook配置失败: {e}")
            return []
    
    def merge_hook_configs(
        self, 
        global_configs: List[Dict[str, Any]], 
        node_configs: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并全局和节点Hook配置"""
        # 转换为配置对象
        global_hook_configs = [HookConfig(**config) for config in global_configs]
        node_hook_configs = [HookConfig(**config) for config in node_configs]
        
        # 创建全局和节点配置对象
        global_config = GlobalHookConfig(hooks=global_hook_configs)
        node_config = NodeHookConfig(node_type="", hooks=node_hook_configs, inherit_global=True)
        
        # 合并配置
        merged_configs = merge_hook_configs(global_config, node_config)
        
        # 转换回字典
        return [config.dict() for config in merged_configs]


class NodeHookManager(IHookManager, IHookExecutionService):
    """节点Hook管理器"""
    
    def __init__(self, config_loader) -> None:
        """初始化Hook管理器
        
        Args:
            config_loader: 配置加载器
        """
        self.config_loader = config_loader
        self.hook_config_loader = HookConfigLoader(config_loader)
        
        # Hook注册表: {node_type: [hook]}
        self._hooks: Dict[str, List[INodeHook]] = defaultdict(list)
        
        # 全局Hook列表
        self._global_hooks: List[INodeHook] = []
        
        # Hook类型到创建函数的映射
        self._hook_factories: Dict[HookType, Callable] = {}
        
        # 注册内置Hook工厂
        self._register_builtin_hook_factories()
        
        # 节点执行计数器（用于死循环检测等）
        self._execution_counters: Dict[str, int] = defaultdict(int)
        
        # 性能统计
        self._performance_stats: Dict[str, Dict[str, Any]] = defaultdict(dict)
    
    def _register_builtin_hook_factories(self) -> None:
        """注册内置Hook工厂函数"""
        for hook_type in HookType:
            self._hook_factories[hook_type] = create_builtin_hook
    
    def register_hook_factory(self, hook_type: HookType, factory: Callable) -> None:
        """注册Hook工厂函数
        
        Args:
            hook_type: Hook类型
            factory: Hook工厂函数
        """
        self._hook_factories[hook_type] = factory
    
    def register_hook(self, hook: INodeHook, node_types: Optional[List[str]] = None) -> None:
        """注册Hook
        
        Args:
            hook: Hook实例
            node_types: 适用的节点类型列表，None表示全局Hook
        """
        # 注入执行服务
        hook.set_execution_service(self)
        
        if node_types is None:
            # 全局Hook
            self._global_hooks.append(hook)
            logger.debug(f"注册全局Hook: {hook.hook_type}")
        else:
            # 节点特定Hook
            for node_type in node_types:
                self._hooks[node_type].append(hook)
                logger.debug(f"为节点 {node_type} 注册Hook: {hook.hook_type}")
    
    def get_hooks_for_node(self, node_type: str) -> List[INodeHook]:
        """获取指定节点的Hook列表"""
        # 合并全局Hook和节点特定Hook
        hooks = []
        
        # 添加全局Hook
        hooks.extend(self._global_hooks)
        
        # 添加节点特定Hook
        if node_type in self._hooks:
            hooks.extend(self._hooks[node_type])
        
        # 按优先级排序（如果Hook有priority属性）
        hooks.sort(key=lambda h: getattr(h, 'priority', 0), reverse=True)
        
        return hooks
    
    def execute_hooks(
        self, 
        hook_point: HookPoint, 
        context: HookContext
    ) -> HookExecutionResult:
        """执行指定Hook点的所有Hook"""
        hooks = self.get_hooks_for_node(context.node_type)
        
        # 过滤支持当前Hook点的Hook
        applicable_hooks = [
            hook for hook in hooks 
            if hook.is_enabled() and hook_point in hook.get_supported_hook_points()
        ]
        
        if not applicable_hooks:
            return HookExecutionResult(should_continue=True)
        
        # 执行Hook
        modified_state = context.state
        modified_result = context.execution_result
        force_next_node = None
        should_continue = True
        metadata = {"executed_hooks": []}
        
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
                else:
                    continue
                
                hook_execution_time = time.time() - hook_start_time
                
                # 记录Hook执行信息
                metadata["executed_hooks"].append({
                    "hook_type": hook.hook_type,
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
                    logger.debug(f"Hook {hook.hook_type} 要求停止执行")
                    break
                    
            except Exception as e:
                logger.error(f"执行Hook {hook.hook_type} 时发生错误: {e}")
                metadata["executed_hooks"].append({
                    "hook_type": hook.hook_type,
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
    
    def load_hooks_from_config(self, config_path: Optional[str] = None) -> None:
        """从配置文件加载Hook"""
        # 加载全局Hook配置
        global_hook_configs = self.hook_config_loader.load_global_hooks()
        
        # 创建并注册全局Hook
        for hook_config_dict in global_hook_configs:
            hook = self._create_hook_from_config(hook_config_dict)
            if hook:
                self.register_hook(hook)
        
        logger.info(f"从配置加载了 {len(global_hook_configs)} 个全局Hook")
    
    def load_node_hooks_from_config(self, node_type: str) -> None:
        """从配置文件加载指定节点的Hook"""
        # 加载节点Hook配置
        node_hook_configs = self.hook_config_loader.load_node_hooks(node_type)
        
        # 创建并注册节点Hook
        for hook_config_dict in node_hook_configs:
            hook = self._create_hook_from_config(hook_config_dict)
            if hook:
                self.register_hook(hook, [node_type])
        
        if node_hook_configs:
            logger.info(f"为节点 {node_type} 加载了 {len(node_hook_configs)} 个Hook")
    
    def _create_hook_from_config(self, hook_config_dict: Dict[str, Any]) -> Optional[INodeHook]:
        """从配置创建Hook实例"""
        try:
            # 解析Hook配置
            hook_config = HookConfig(**hook_config_dict)
            
            # 获取Hook工厂函数
            factory = self._hook_factories.get(hook_config.type)
            if not factory:
                logger.warning(f"未知的Hook类型: {hook_config.type}")
                return None
            
            # 创建Hook实例
            hook = factory(hook_config.config)
            
            return hook
            
        except Exception as e:
            logger.error(f"创建Hook失败: {e}")
            return None
    
    def clear_hooks(self) -> None:
        """清除所有Hook"""
        self._hooks.clear()
        self._global_hooks.clear()
        logger.info("已清除所有Hook")
    
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
    
    def reset_execution_count(self, node_type: str) -> None:
        """重置节点执行计数
        
        Args:
            node_type: 节点类型
        """
        self._execution_counters[node_type] = 0
    
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
    
    def get_node_performance_stats(self, node_type: str) -> Dict[str, Any]:
        """获取指定节点的性能统计
        
        Args:
            node_type: 节点类型
            
        Returns:
            Dict[str, Any]: 性能统计数据
        """
        return self._performance_stats.get(node_type, {})
    
    def get_global_hooks_count(self) -> int:
        """获取全局Hook数量
        
        Returns:
            int: 全局Hook数量
        """
        return len(self._global_hooks)
    
    def get_node_hooks_count(self, node_type: str) -> int:
        """获取指定节点的Hook数量
        
        Args:
            node_type: 节点类型
            
        Returns:
            int: Hook数量
        """
        return len(self._hooks.get(node_type, []))
    
    def get_all_node_hooks_counts(self) -> Dict[str, int]:
        """获取所有节点的Hook数量
        
        Returns:
            Dict[str, int]: 节点类型到Hook数量的映射
        """
        return {node_type: len(hooks) for node_type, hooks in self._hooks.items()}
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息
        
        Returns:
            Dict[str, Dict[str, Any]]: 节点类型到性能统计的映射
        """
        return dict(self._performance_stats)