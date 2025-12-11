"""协作策略

提供工作流的协作执行策略实现。
"""

from src.interfaces.dependency_injection import get_logger
from typing import TYPE_CHECKING, Dict, Any, Optional, List, Callable
from dataclasses import dataclass, field
from datetime import datetime

from .strategy_base import BaseStrategy, IExecutionStrategy

if TYPE_CHECKING:
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from src.interfaces.workflow.core import IWorkflow
    from ..core.execution_context import ExecutionContext, ExecutionResult
    from src.interfaces.workflow.core import IWorkflow
    from src.interfaces.state.manager import IStateManager

logger = get_logger(__name__)


@dataclass
class CollaborationConfig:
    """协作执行配置"""
    enable_snapshots: bool = True  # 是否启用快照
    enable_validation: bool = True  # 是否启用验证
    enable_history_tracking: bool = True  # 是否启用历史跟踪
    snapshot_on_node_start: bool = True  # 节点开始时创建快照
    snapshot_on_node_complete: bool = True  # 节点完成时创建快照
    snapshot_on_error: bool = True  # 错误时创建快照
    validation_rules: List[Callable] = field(default_factory=list)  # 验证规则列表


class ICollaborationStrategy(IExecutionStrategy):
    """协作策略接口"""
    pass


class CollaborationStrategy(BaseStrategy, ICollaborationStrategy):
    """协作策略实现
    
    提供带协作机制的工作流执行能力，包括状态验证、快照和历史跟踪。
    """
    
    def __init__(
        self, 
        state_manager: Optional['IStateManager'] = None,
        config: Optional[CollaborationConfig] = None
    ):
        """初始化协作策略
        
        Args:
            state_manager: 增强状态管理器
            config: 协作配置
        """
        super().__init__("collaboration", priority=25)
        self.state_manager = state_manager
        self.config = config or CollaborationConfig()
        logger.debug("协作策略初始化完成")
    
    def execute(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """使用协作策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.debug(f"开始协作执行工作流: {workflow.config.name}")
        
        # 创建协作执行上下文
        collaboration_context = self._create_collaboration_context(context)
        
        try:
            # 创建初始状态
            from src.core.state.factories.state_factory import create_workflow_state
            initial_state = create_workflow_state(
                workflow_id=collaboration_context.workflow_id,
                execution_id=collaboration_context.execution_id,
                config=collaboration_context.config,
                metadata=collaboration_context.metadata
            )
            
            # 执行工作流
            workflow_state_result = executor.execute(workflow, initial_state)
            
            # 将 IWorkflowState 结果转换为 ExecutionResult
            execution_result = self.create_execution_result(
                success=True,
                result=workflow_state_result.values if hasattr(workflow_state_result, 'values') else {},
                metadata=getattr(workflow_state_result, 'metadata', {}) or {}
            )
            
            # 添加协作元数据
            self._add_collaboration_metadata(execution_result, {
                "enable_snapshots": self.config.enable_snapshots,
                "enable_validation": self.config.enable_validation,
                "enable_history_tracking": self.config.enable_history_tracking
            })
            
            logger.debug(f"协作执行完成: {getattr(workflow, 'name', 'Unknown')}")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"协作执行失败: {e}")
            
            # 记录协作错误
            if self.state_manager and self.config.enable_history_tracking:
                self._record_collaboration_error(context, str(e))
            
            # 创建错误结果
            result = self.create_execution_result(
                success=False,
                error=str(e),
                metadata={
                    "collaboration_enabled": True,
                    "collaboration_error": True,
                    "error_type": type(e).__name__
                }
            )
            
            return result
    
    async def execute_async(
        self,
        executor: 'IWorkflowExecutor',
        workflow: 'IWorkflow',
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """异步使用协作策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        logger.debug(f"开始异步协作执行工作流: {getattr(workflow, 'name', 'Unknown')}")
        
        # 创建协作执行上下文
        collaboration_context = self._create_collaboration_context(context)
        
        try:
            # 创建初始状态
            from src.core.state.factories.state_factory import create_workflow_state
            initial_state = create_workflow_state(
                workflow_id=collaboration_context.workflow_id,
                execution_id=collaboration_context.execution_id,
                config=collaboration_context.config,
                metadata=collaboration_context.metadata
            )
            
            # 异步执行工作流
            workflow_state_result = await executor.execute_async(workflow, initial_state)
            
            # 将 IWorkflowState 结果转换为 ExecutionResult
            execution_result = self.create_execution_result(
                success=True,
                result=workflow_state_result.values if hasattr(workflow_state_result, 'values') else {},
                metadata=getattr(workflow_state_result, 'metadata', {}) or {}
            )
            
            # 添加协作元数据
            self._add_collaboration_metadata(execution_result, {
                "enable_snapshots": self.config.enable_snapshots,
                "enable_validation": self.config.enable_validation,
                "enable_history_tracking": self.config.enable_history_tracking
            }, execution_mode="async")
            
            logger.debug(f"异步协作执行完成: {getattr(workflow, 'name', 'Unknown')}")
            
            return execution_result
            
        except Exception as e:
            logger.error(f"异步协作执行失败: {e}")
            
            # 记录协作错误
            if self.state_manager and self.config.enable_history_tracking:
                self._record_collaboration_error(context, str(e))
            
            # 创建错误结果
            result = self.create_execution_result(
                success=False,
                error=str(e),
                metadata={
                    "collaboration_enabled": True,
                    "collaboration_error": True,
                    "error_type": type(e).__name__,
                    "execution_mode": "async"
                }
            )
            
            return result
    
    def can_handle(self, workflow: 'IWorkflow', context: 'ExecutionContext') -> bool:
        """判断是否适用协作策略
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            bool: 是否适用协作策略
        """
        return (
            context.get_config("collaboration_enabled", False) or
            self.state_manager is not None or
            any(key in context.config for key in [
                "enable_snapshots", "enable_validation", "enable_history_tracking"
            ])
        )
    
    def _create_collaboration_context(self, context: 'ExecutionContext') -> 'ExecutionContext':
        """创建协作执行上下文
        
        Args:
            context: 原始执行上下文
            
        Returns:
            ExecutionContext: 协作执行上下文
        """
        # 复制原始上下文并添加协作配置
        collaboration_config = {
            **context.config,
            "collaboration_enabled": True,
            "enable_snapshots": self.config.enable_snapshots,
            "enable_validation": self.config.enable_validation,
            "enable_history_tracking": self.config.enable_history_tracking,
            "snapshot_on_node_start": self.config.snapshot_on_node_start,
            "snapshot_on_node_complete": self.config.snapshot_on_node_complete,
            "snapshot_on_error": self.config.snapshot_on_error
        }
        
        collaboration_metadata = {
            **context.metadata,
            "collaboration_enabled": True,
            "collaboration_timestamp": datetime.now().isoformat()
        }
        
        return ExecutionContext(
            workflow_id=context.workflow_id,
            execution_id=context.execution_id,
            config={
                **collaboration_config,
                **collaboration_metadata
            }
        )
    
    def _validate_state(self, state: Any, context: 'ExecutionContext') -> List[str]:
        """验证状态
        
        Args:
            state: 状态对象
            context: 执行上下文
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not self.config.enable_validation:
            return errors
        
        # 应用自定义验证规则
        for rule in self.config.validation_rules:
            try:
                rule_errors = rule(state, context)
                if rule_errors:
                    errors.extend(rule_errors)
            except Exception as e:
                logger.warning(f"验证规则执行失败: {e}")
                errors.append(f"验证规则执行失败: {e}")
        
        # 默认验证规则
        if state is None:
            errors.append("状态不能为空")
        
        return errors
    
    def _create_snapshot(
        self, 
        state: Any, 
        context: 'ExecutionContext', 
        snapshot_type: str
    ) -> Optional[str]:
        """创建状态快照
        
        Args:
            state: 状态对象
            context: 执行上下文
            snapshot_type: 快照类型
            
        Returns:
            Optional[str]: 快照ID
        """
        if not self.config.enable_snapshots or not self.state_manager:
            return None
        
        try:
            # 转换状态为字典格式
            if hasattr(state, '__dict__'):
                state_dict = state.__dict__
            elif hasattr(state, 'get_data'):
                state_dict = state.get_data()
            else:
                state_dict = {"state": state}
            
            # 创建快照
            snapshot_id = self.state_manager.snapshot_manager.create_snapshot(
                context.workflow_id,
                state_dict,
                snapshot_type
            )
            
            logger.debug(f"创建快照成功: {snapshot_id}, 类型: {snapshot_type}")
            
            return snapshot_id
            
        except Exception as e:
            logger.error(f"创建快照失败: {e}")
            return None
    
    def _record_state_change(
        self, 
        context: 'ExecutionContext', 
        from_state: Any, 
        to_state: Any, 
        change_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录状态变化
        
        Args:
            context: 执行上下文
            from_state: 原始状态
            to_state: 目标状态
            change_type: 变化类型
            metadata: 元数据
        """
        if not self.config.enable_history_tracking or not self.state_manager:
            return
        
        try:
            # 转换状态为字典格式
            from_dict = self._state_to_dict(from_state)
            to_dict = self._state_to_dict(to_state)
            
            # 记录状态变化
            self.state_manager.history_manager.record_state_change(
                agent_id=context.execution_id,
                old_state=from_dict,
                new_state=to_dict,
                action=change_type
            )
            
        except Exception as e:
            logger.error(f"记录状态变化失败: {e}")
    
    def _record_collaboration_error(self, context: 'ExecutionContext', error_message: str) -> None:
        """记录协作错误
        
        Args:
            context: 执行上下文
            error_message: 错误消息
        """
        if not self.state_manager:
            return
        
        try:
            # 记录协作错误
            self.state_manager.history_manager.record_state_change(
                agent_id=context.execution_id,
                old_state={},
                new_state={"collaboration_error": error_message},
                action="collaboration_error"
            )
            
        except Exception as e:
            logger.error(f"记录协作错误失败: {e}")
    
    def _add_collaboration_metadata(
        self, 
        result: Any,
        collaboration_config: Dict[str, Any],
        execution_mode: str = "sync"
    ) -> None:
        """添加协作元数据到执行结果
        
        Args:
            result: 执行结果
            collaboration_config: 协作配置
            execution_mode: 执行模式（sync/async）
        """
        metadata_update: Dict[str, Any] = {
            "collaboration_enabled": True,
            "collaboration_config": collaboration_config
        }
        
        if execution_mode == "async":
            metadata_update["execution_mode"] = "async"
        
        # 尝试更新元数据
        if isinstance(result, dict):
            if 'metadata' in result and isinstance(result['metadata'], dict):
                result['metadata'].update(metadata_update)  # type: ignore
            else:
                result['metadata'] = metadata_update  # type: ignore
        elif hasattr(result, 'metadata'):
            if isinstance(getattr(result, 'metadata', None), dict):
                result.metadata.update(metadata_update)  # type: ignore
    
    def _state_to_dict(self, state: Any) -> Dict[str, Any]:
        """将状态转换为字典
        
        Args:
            state: 状态对象
            
        Returns:
            Dict[str, Any]: 状态字典
        """
        if state is None:
            return {}
        
        if hasattr(state, '__dict__'):
            return state.__dict__
        elif hasattr(state, 'get_data'):
            return state.get_data()
        elif isinstance(state, dict):
            return state
        else:
            return {"value": state}
    
    def set_state_manager(self, state_manager: 'IStateManager') -> None:
        """设置状态管理器
        
        Args:
            state_manager: 增强状态管理器
        """
        self.state_manager = state_manager
        logger.debug("协作策略的状态管理器已更新")
    
    def update_config(self, config: CollaborationConfig) -> None:
        """更新协作配置
        
        Args:
            config: 新的协作配置
        """
        self.config = config
        logger.debug("协作策略的配置已更新")
    
    def get_collaboration_info(self, context: 'ExecutionContext') -> Dict[str, Any]:
        """获取协作信息
        
        Args:
            context: 执行上下文
            
        Returns:
            Dict[str, Any]: 协作信息
        """
        info = {
            "collaboration_enabled": True,
            "config": {
                "enable_snapshots": self.config.enable_snapshots,
                "enable_validation": self.config.enable_validation,
                "enable_history_tracking": self.config.enable_history_tracking,
                "snapshot_on_node_start": self.config.snapshot_on_node_start,
                "snapshot_on_node_complete": self.config.snapshot_on_node_complete,
                "snapshot_on_error": self.config.snapshot_on_error
            }
        }
        
        # 获取快照信息
        if self.state_manager and self.config.enable_snapshots:
            try:
                snapshots = self.state_manager.snapshot_manager.get_snapshots_by_agent(context.workflow_id)
                info["snapshots"] = {
                    "total_count": len(snapshots),
                    "latest_snapshot": snapshots[-1].snapshot_id if snapshots else None
                }
            except Exception as e:
                logger.warning(f"获取快照信息失败: {e}")
        
        # 获取历史信息
        if self.state_manager and self.config.enable_history_tracking:
            try:
                history = self.state_manager.history_manager.get_state_history(context.workflow_id)
                info["history"] = {
                    "total_changes": len(history),
                    "latest_change": history[-1].action if history else None
                }
            except Exception as e:
                logger.warning(f"获取历史信息失败: {e}")
        
        return info