"""执行管理器

提供工作流执行的统一管理服务。
"""

from src.interfaces.dependency_injection import get_logger
import time
import uuid
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Union
from datetime import datetime
from dataclasses import dataclass, field

from src.interfaces.workflow.execution import IWorkflowExecutor
from src.interfaces.workflow.core import IWorkflow
from ..executor import WorkflowExecutor
from ..core.node_executor import INodeExecutor, NodeExecutor
from ..core.execution_context import ExecutionContext, ExecutionResult
from ..strategies.strategy_base import IExecutionStrategy
from ..modes.mode_base import IExecutionMode

if TYPE_CHECKING:
    from ...workflow import Workflow
    from src.interfaces.state import IStateManager

logger = get_logger(__name__)


@dataclass
class ExecutionManagerConfig:
    """执行管理器配置"""
    default_strategy: Optional[str] = None
    default_mode: Optional[str] = None
    enable_monitoring: bool = True
    enable_caching: bool = True
    max_concurrent_executions: int = 10
    execution_timeout: Optional[float] = None


class IExecutionManager:
    """执行管理器接口"""
    pass


class ExecutionManager(IExecutionManager):
    """执行管理器
    
    统一管理所有执行器，提供工作流执行的统一入口。
    """
    
    def __init__(
        self, 
        config: Optional[ExecutionManagerConfig] = None,
        state_manager: Optional['IStateManager'] = None
    ):
        """初始化执行管理器
        
        Args:
            config: 执行管理器配置
            state_manager: 状态管理器
        """
        self.config = config or ExecutionManagerConfig()
        self.state_manager = state_manager
        
        # 核心执行器
        self._workflow_executor = WorkflowExecutor()
        self._node_executor = NodeExecutor()
        
        # 策略和模式注册表
        self._strategies: Dict[str, IExecutionStrategy] = {}
        self._modes: Dict[str, IExecutionMode] = {}
        
        # 执行统计
        self._execution_stats: Dict[str, Any] = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "strategy_usage": {},
            "mode_usage": {}
        }
        
        # 执行缓存
        self._execution_cache: Dict[str, ExecutionResult] = {}
        
        logger.debug("执行管理器初始化完成")
    
    def register_strategy(self, strategy: IExecutionStrategy) -> None:
        """注册执行策略
        
        Args:
            strategy: 执行策略
        """
        self._strategies[strategy.get_strategy_name()] = strategy
        logger.debug(f"执行策略已注册: {strategy.get_strategy_name()}")
    
    def register_mode(self, mode: IExecutionMode) -> None:
        """注册执行模式
        
        Args:
            mode: 执行模式
        """
        self._modes[mode.get_mode_name()] = mode
        logger.debug(f"执行模式已注册: {mode.get_mode_name()}")
    
    def execute_workflow(
        self,
        workflow: Union['Workflow', IWorkflow],
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """执行工作流 - 统一入口
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            config: 执行配置
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 生成执行ID
        execution_id = str(uuid.uuid4())
        
        # 创建执行上下文
        # 使用 getattr 安全访问 config 属性，因为 workflow 可能是 IWorkflow 接口
        workflow_config = getattr(workflow, 'config', None)
        workflow_name = getattr(workflow_config, 'name', getattr(workflow, 'workflow_id', 'unknown'))
        
        context = ExecutionContext(
            workflow_id=workflow_name,
            execution_id=execution_id,
            config=config or {
                "initial_data": initial_data,
                "manager_timestamp": datetime.now().isoformat()
            }
        )
        
        # 设置初始数据
        if initial_data:
            context.set_config("initial_data", initial_data)
        
        start_time = time.time()
        
        try:
            logger.info(f"开始执行工作流: {workflow_name} (ID: {execution_id})")
            
            # 检查缓存
            if self.config.enable_caching and isinstance(workflow, Workflow):
                cached_result = self._get_cached_result(workflow, context)
                if cached_result:
                    logger.info(f"使用缓存结果: {workflow_name}")
                    return cached_result
            
            # 使用新的执行器执行工作流
            from ..executor import WorkflowExecutor
            executor = WorkflowExecutor()
            from src.core.state.implementations.workflow_state import WorkflowState
            initial_state = WorkflowState(
                workflow_id=workflow_name,
                execution_id=execution_id,
                data=initial_data or {}
            )
            result_state = executor.execute(workflow, initial_state, context.config)
            final_state = getattr(result_state, 'data', result_state)
            result = ExecutionResult(
                success=True,
                result=final_state if isinstance(final_state, dict) else {},
                metadata={
                    "workflow_name": workflow_name,
                    "workflow_id": workflow_name,
                    "execution_id": execution_id,
                    "execution_time": time.time() - start_time,
                }
            )
            
            # 缓存结果
            if self.config.enable_caching and result.success and isinstance(workflow, Workflow):
                self._cache_result(workflow, context, result)
            
            # 更新统计
            self._update_stats(True, time.time() - start_time, "coordinator", "sync")
            
            logger.info(f"工作流执行完成: {workflow_name} (ID: {execution_id}), 耗时: {result.execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"工作流执行失败: {workflow_name} (ID: {execution_id}), 错误: {e}")
            
            # 更新统计
            self._update_stats(False, execution_time, None, None)
            
            # 创建错误结果
            result = ExecutionResult(
                success=False,
                error=str(e),
                metadata={
                    "workflow_name": workflow_name,
                    "workflow_id": workflow_name,
                    "execution_id": execution_id,
                    "error_type": type(e).__name__,
                    "execution_time": execution_time
                }
            )
            
            return result
    
    async def execute_workflow_async(
        self,
        workflow: Union['Workflow', IWorkflow],
        initial_data: Optional[Dict[str, Any]] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """异步执行工作流
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            config: 执行配置
            
        Returns:
            ExecutionResult: 执行结果
        """
        # 生成执行ID
        execution_id = str(uuid.uuid4())
        
        # 创建执行上下文
        # 使用 getattr 安全访问 config 属性，因为 workflow 可能是 IWorkflow 接口
        workflow_config = getattr(workflow, 'config', None)
        workflow_name = getattr(workflow_config, 'name', getattr(workflow, 'workflow_id', 'unknown'))
        
        context = ExecutionContext(
            workflow_id=workflow_name,
            execution_id=execution_id,
            config=config or {
                "initial_data": initial_data,
                "manager_timestamp": datetime.now().isoformat(),
                "async_execution": True
            }
        )
        
        # 设置初始数据
        if initial_data:
            context.set_config("initial_data", initial_data)
        
        start_time = time.time()
        
        try:
            logger.info(f"开始异步执行工作流: {workflow_name} (ID: {execution_id})")
            
            # 检查缓存
            if self.config.enable_caching and isinstance(workflow, Workflow):
                cached_result = self._get_cached_result(workflow, context)
                if cached_result:
                    logger.info(f"使用缓存结果: {workflow_name}")
                    return cached_result
            
            # 统一使用协调器异步执行工作流
            from ..executor import WorkflowExecutor
            executor = WorkflowExecutor()
            from src.core.state.implementations.workflow_state import WorkflowState
            initial_state = WorkflowState(
                workflow_id=workflow_name,
                execution_id=execution_id,
                data=initial_data or {}
            )
            result_state = await executor.execute_async(workflow, initial_state, context.config)
            final_state = getattr(result_state, 'data', result_state)
            result = ExecutionResult(
                success=True,
                result=final_state if isinstance(final_state, dict) else {},
                metadata={
                    "workflow_name": workflow_name,
                    "workflow_id": workflow_name,
                    "execution_id": execution_id,
                    "execution_time": time.time() - start_time,
                    "async_execution": True
                }
            )
            
            # 缓存结果
            if self.config.enable_caching and result.success and isinstance(workflow, Workflow):
                self._cache_result(workflow, context, result)
            
            # 更新统计
            self._update_stats(True, time.time() - start_time, "coordinator", "async")
            
            logger.info(f"工作流异步执行完成: {workflow_name} (ID: {execution_id}), 耗时: {result.execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"工作流异步执行失败: {workflow_name} (ID: {execution_id}), 错误: {e}")
            
            # 更新统计
            self._update_stats(False, execution_time, None, None)
            
            # 创建错误结果
            result = ExecutionResult(
                success=False,
                error=str(e),
                metadata={
                    "workflow_name": workflow_name,
                    "workflow_id": workflow_name,
                    "execution_id": execution_id,
                    "error_type": type(e).__name__,
                    "execution_time": execution_time,
                    "async_execution": True
                }
            )
            
            return result
    
    def _select_strategy(
        self, 
        workflow: 'Workflow',
        context: ExecutionContext
    ) -> IExecutionStrategy:
        """自动选择执行策略
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            IExecutionStrategy: 执行策略
        """
        # 检查是否强制指定了策略
        forced_strategy = context.get_config("strategy")
        if forced_strategy and forced_strategy in self._strategies:
            return self._strategies[forced_strategy]
        
        # 检查默认策略
        if self.config.default_strategy and self.config.default_strategy in self._strategies:
            default_strategy = self._strategies[self.config.default_strategy]
            if default_strategy.can_handle(workflow, context):
                return default_strategy
        
        # 按优先级选择适用的策略
        applicable_strategies = [
            (name, strategy) for name, strategy in self._strategies.items()
            if strategy.can_handle(workflow, context)
        ]
        
        if applicable_strategies:
            # 按优先级排序
            applicable_strategies.sort(key=lambda x: x[1].get_priority(), reverse=True)
            return applicable_strategies[0][1]
        
        # 返回默认策略（如果没有注册任何策略，使用RetryStrategyImpl）
        from ..strategies.retry_strategy import RetryStrategyImpl
        return RetryStrategyImpl()
    
    def _select_mode(
        self, 
        workflow: 'Workflow',
        context: ExecutionContext
    ) -> IExecutionMode:
        """自动选择执行模式
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            IExecutionMode: 执行模式
        """
        # 检查是否强制指定了模式
        forced_mode = context.get_config("mode")
        if forced_mode and forced_mode in self._modes:
            return self._modes[forced_mode]
        
        # 检查默认模式
        if self.config.default_mode and self.config.default_mode in self._modes:
            return self._modes[self.config.default_mode]
        
        # 检查是否需要异步执行
        if context.get_config("async_enabled", False):
            if "async" in self._modes:
                return self._modes["async"]
            elif "hybrid" in self._modes:
                return self._modes["hybrid"]
        
        # 检查是否需要流式执行
        if context.get_config("streaming_enabled", False):
            if "hybrid" in self._modes:
                return self._modes["hybrid"]
        
        # 默认使用同步模式
        if "sync" in self._modes:
            return self._modes["sync"]
        elif "hybrid" in self._modes:
            return self._modes["hybrid"]
        
        # 如果没有注册任何模式，创建一个默认的同步模式
        from ..modes.sync_mode import SyncMode
        return SyncMode()
    
    def _get_cached_result(
        self, 
        workflow: 'Workflow',
        context: ExecutionContext
    ) -> Optional[ExecutionResult]:
        """获取缓存结果
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            Optional[ExecutionResult]: 缓存的结果
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(workflow, context)
        
        # 检查缓存
        if cache_key in self._execution_cache:
            cached_result = self._execution_cache[cache_key]
            
            # 检查缓存是否过期
            if self._is_cache_valid(cached_result):
                return cached_result
            else:
                # 删除过期缓存
                del self._execution_cache[cache_key]
        
        return None
    
    def _cache_result(
        self, 
        workflow: 'Workflow',
        context: ExecutionContext, 
        result: ExecutionResult
    ) -> None:
        """缓存执行结果
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            result: 执行结果
        """
        # 生成缓存键
        cache_key = self._generate_cache_key(workflow, context)
        
        # 添加缓存时间戳
        result.metadata["cached_at"] = time.time()
        
        # 缓存结果
        self._execution_cache[cache_key] = result
        
        # 限制缓存大小
        if len(self._execution_cache) > 100:
            # 删除最旧的缓存项
            oldest_key = min(self._execution_cache.keys(), 
                           key=lambda k: self._execution_cache[k].metadata.get("cached_at", 0))
            del self._execution_cache[oldest_key]
    
    def _generate_cache_key(
        self, 
        workflow: 'Workflow',
        context: ExecutionContext
    ) -> str:
        """生成缓存键
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            str: 缓存键
        """
        import hashlib
        
        # 组合工作流ID、配置和初始数据
        cache_data = {
            "workflow_id": workflow.config.name,
            "workflow_version": getattr(workflow.config, 'version', '1.0.0'),
            "config": context.config,
            "initial_data": context.get_config("initial_data")
        }
        
        # 生成哈希
        cache_string = str(sorted(cache_data.items()))
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    def _is_cache_valid(self, result: ExecutionResult) -> bool:
        """检查缓存是否有效
        
        Args:
            result: 缓存的结果
            
        Returns:
            bool: 是否有效
        """
        cached_at = result.metadata.get("cached_at", 0)
        current_time = time.time()
        
        # 缓存有效期为1小时
        return (current_time - float(cached_at)) < 3600
    
    def _update_stats(
        self,
        success: bool,
        execution_time: float,
        strategy_name: Optional[str],
        mode_name: Optional[str]
    ) -> None:
        """更新执行统计
        
        Args:
            success: 是否成功
            execution_time: 执行时间
            strategy_name: 策略名称
            mode_name: 模式名称
        """
        self._execution_stats["total_executions"] += 1
        self._execution_stats["total_execution_time"] += execution_time
        
        if success:
            self._execution_stats["successful_executions"] += 1
        else:
            self._execution_stats["failed_executions"] += 1
        
        # 更新策略使用统计
        if strategy_name:
            if strategy_name not in self._execution_stats["strategy_usage"]:
                self._execution_stats["strategy_usage"][strategy_name] = 0
            self._execution_stats["strategy_usage"][strategy_name] += 1
        
        # 更新模式使用统计
        if mode_name:
            if mode_name not in self._execution_stats["mode_usage"]:
                self._execution_stats["mode_usage"][mode_name] = 0
            self._execution_stats["mode_usage"][mode_name] += 1
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._execution_stats.copy()
        
        total_executions = stats["total_executions"]
        if total_executions > 0:
            stats["success_rate"] = stats["successful_executions"] / total_executions
            stats["average_execution_time"] = stats["total_execution_time"] / total_executions
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        stats["cache_size"] = len(self._execution_cache)
        stats["registered_strategies"] = list(self._strategies.keys())
        stats["registered_modes"] = list(self._modes.keys())
        
        return stats
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "strategy_usage": {},
            "mode_usage": {}
        }
        logger.debug("执行统计信息已重置")
    
    def clear_cache(self) -> None:
        """清空缓存"""
        self._execution_cache.clear()
        logger.debug("执行缓存已清空")
    
    def get_available_strategies(self) -> List[str]:
        """获取可用的执行策略列表
        
        Returns:
            List[str]: 策略名称列表
        """
        return list(self._strategies.keys())
    
    def get_available_modes(self) -> List[str]:
        """获取可用的执行模式列表
        
        Returns:
            List[str]: 模式名称列表
        """
        return list(self._modes.keys())