"""协作工作流执行器

提供带协作机制的工作流状态执行能力。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Callable, Union
from datetime import datetime
import logging

from src.services.workflow.state_converter import WorkflowStateConverter, WorkflowStateAdapter
from src.core.state.state_interfaces import IEnhancedStateManager

logger = logging.getLogger(__name__)


class ICollaborationExecutor(ABC):
    """协作执行器接口"""
    
    @abstractmethod
    def execute_with_collaboration(
        self,
        graph_state: Union[Dict[str, Any], Any],
        node_executor: Callable[[WorkflowStateAdapter], WorkflowStateAdapter]
    ) -> Union[Dict[str, Any], Any]:
        """带协作机制的状态执行"""
        pass


class CollaborationExecutor(ICollaborationExecutor):
    """协作执行器 - 支持协作管理的状态转换
    
    提供带协作机制的工作流执行能力，包括：
    - 状态验证
    - 状态快照
    - 状态变更记录
    """
    
    def __init__(self, state_manager: IEnhancedStateManager):
        """初始化协作执行器
        
        Args:
            state_manager: 增强状态管理器
        """
        self.state_converter = WorkflowStateConverter()
        self.state_manager = state_manager
    
    def execute_with_collaboration(
        self,
        graph_state: Union[Dict[str, Any], Any],
        node_executor: Callable[[WorkflowStateAdapter], WorkflowStateAdapter]
    ) -> Union[Dict[str, Any], Any]:
        """带协作机制的状态执行
        
        Args:
            graph_state: 图系统状态
            node_executor: 节点执行函数，接收WorkflowStateAdapter并返回修改后的WorkflowStateAdapter
            
        Returns:
            转换后的图系统状态
        """
        # 1. 转换为WorkflowStateAdapter
        adapter_state = self.state_converter.from_graph_state(graph_state)  # type: ignore
        
        # 2. 状态验证
        validation_errors = self._validate_state(adapter_state)
        
        # 3. 记录状态变化开始
        snapshot_id = self._create_pre_execution_snapshot(adapter_state)
        
        # 4. 执行业务逻辑
        try:
            result_adapter_state = node_executor(adapter_state)
            # 获取workflow_id用于日志记录
            workflow_id = self._get_workflow_id(adapter_state)
            logger.debug(f"节点执行成功，workflow_id: {workflow_id}")
        except Exception as e:
            # 获取workflow_id用于日志记录
            workflow_id = self._get_workflow_id(adapter_state)
            logger.error(f"节点执行失败，workflow_id: {workflow_id}, 错误: {str(e)}")
            # 记录执行错误
            self._record_execution_error(adapter_state, snapshot_id, str(e))
            raise
        
        # 5. 记录状态变化结束
        self._record_state_completion(result_adapter_state, snapshot_id, validation_errors)
        
        # 6. 转换回图状态
        result_state = self.state_converter.to_graph_state(result_adapter_state)
        
        # 7. 添加协作元数据
        return self._add_collaboration_metadata(result_state, snapshot_id, validation_errors)  # type: ignore
    
    def _validate_state(self, adapter_state: WorkflowStateAdapter) -> List[str]:
        """状态验证
        
        Args:
            adapter_state: WorkflowStateAdapter对象
            
        Returns:
            List[str]: 验证错误列表
        """
        # 使用状态管理器进行验证，这里可以添加自定义验证逻辑
        # 目前返回空列表，表示没有验证错误
        return []
    
    def _create_pre_execution_snapshot(self, adapter_state: WorkflowStateAdapter) -> str:
        """创建执行前快照
        
        Args:
            adapter_state: WorkflowStateAdapter对象
            
        Returns:
            str: 快照ID
        """
        # 转换WorkflowStateAdapter为字典格式
        from dataclasses import asdict
        state_dict = asdict(adapter_state)
        
        # 使用快照管理器创建快照
        return self.state_manager.snapshot_manager.create_snapshot(
            adapter_state.workflow_id, state_dict, "pre_execution"
        )
    
    def _get_workflow_id(self, adapter_state: WorkflowStateAdapter) -> str:
        """获取工作流ID
        
        Args:
            adapter_state: WorkflowStateAdapter对象
            
        Returns:
            str: 工作流ID
        """
        return str(adapter_state.workflow_id) if adapter_state.workflow_id else "unknown"
    
    def _record_execution_error(self, adapter_state: WorkflowStateAdapter,
                               snapshot_id: str, error_message: str) -> None:
        """记录执行错误
        
        Args:
            adapter_state: WorkflowStateAdapter对象
            snapshot_id: 快照ID
            error_message: 错误消息
        """
        try:
            workflow_id = self._get_workflow_id(adapter_state)
                 
            # 使用历史管理器记录状态变化
            self.state_manager.history_manager.record_state_change(
                workflow_id,
                {},
                {"error": error_message, "snapshot_id": snapshot_id},
                "execution_error"
            )
        except Exception as e:
            logger.error(f"记录执行错误失败: {str(e)}")
    
    def _record_state_completion(self, adapter_state: WorkflowStateAdapter,
                                snapshot_id: str, validation_errors: List[str]) -> None:
        """记录状态完成
        
        Args:
            adapter_state: WorkflowStateAdapter对象
            snapshot_id: 快照ID
            validation_errors: 验证错误列表
        """
        try:
            workflow_id = self._get_workflow_id(adapter_state)
                 
            # 转换WorkflowStateAdapter为字典格式
            from dataclasses import asdict
            state_dict = asdict(adapter_state)
            
            # 添加验证错误到状态字典
            state_dict["validation_errors"] = validation_errors
                    
            # 使用历史管理器记录状态变化
            self.state_manager.history_manager.record_state_change(
                workflow_id,
                {},
                state_dict,
                "execution_completed"
            )
        except Exception as e:
            logger.error(f"记录状态完成失败: {str(e)}")
    
    def _add_collaboration_metadata(self, graph_state: Dict[str, Any],
                                   snapshot_id: str, validation_errors: List[str]) -> Dict[str, Any]:
        """添加协作元数据
        
        Args:
            graph_state: 图系统状态
            snapshot_id: 快照ID
            validation_errors: 验证错误列表
            
        Returns:
            Dict[str, Any]: 更新后的图系统状态
        """
        if "metadata" not in graph_state:
            graph_state["metadata"] = {}
        
        graph_state["metadata"].update({
            "collaboration_snapshot_id": snapshot_id,
            "validation_errors": validation_errors,
            "collaboration_timestamp": datetime.now().isoformat(),
            "collaboration_enabled": True
        })
        
        return graph_state