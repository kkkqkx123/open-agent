"""协作工作流执行器

提供带协作机制的工作流状态执行能力。
"""

from typing import Dict, Any, List, Callable, Union
from datetime import datetime
import logging

from src.services.workflow.state_converter import WorkflowStateConverter
from src.domain.state.interfaces import IStateLifecycleManager

logger = logging.getLogger(__name__)


class CollaborationExecutor:
    """协作执行器 - 支持协作管理的状态转换
    
    提供带协作机制的工作流执行能力，包括：
    - 状态验证
    - 状态快照
    - 状态变更记录
    """
    
    def __init__(self, collaboration_manager: IStateLifecycleManager):
        """初始化协作执行器
        
        Args:
            collaboration_manager: 状态生命周期管理器
        """
        self.state_converter = WorkflowStateConverter()
        self.collaboration_manager = collaboration_manager
    
    def execute_with_collaboration(
        self,
        graph_state: Union[Dict[str, Any], Any],
        node_executor: Callable[[Any], Any]
    ) -> Union[Dict[str, Any], Any]:
        """带协作机制的状态执行
        
        Args:
            graph_state: 图系统状态
            node_executor: 节点执行函数，接收域状态并返回修改后的域状态
            
        Returns:
            转换后的图系统状态
        """
        # 1. 转换为域状态
        domain_state = self.state_converter.from_graph_state(graph_state)  # type: ignore
        
        # 2. 状态验证
        validation_errors = self._validate_state(domain_state)
        
        # 3. 记录状态变化开始
        snapshot_id = self._create_pre_execution_snapshot(domain_state)
        
        # 4. 执行业务逻辑
        try:
            result_domain_state = node_executor(domain_state)
            logger.debug(f"节点执行成功，workflow_id: {domain_state.workflow_id}")
        except Exception as e:
            logger.error(f"节点执行失败，workflow_id: {domain_state.workflow_id}, 错误: {str(e)}")
            # 记录执行错误
            self._record_execution_error(domain_state, snapshot_id, str(e))
            raise
        
        # 5. 记录状态变化结束
        self._record_state_completion(result_domain_state, snapshot_id, validation_errors)
        
        # 6. 转换回图状态
        result_state = self.state_converter.to_graph_state(result_domain_state)
        
        # 7. 添加协作元数据
        return self._add_collaboration_metadata(result_state, snapshot_id, validation_errors)  # type: ignore
    
    def _validate_state(self, domain_state: Any) -> List[str]:
        """状态验证
        
        Args:
            domain_state: 域状态对象
            
        Returns:
            List[str]: 验证错误列表
        """
        return self.collaboration_manager.validate_domain_state(domain_state)
    
    def _create_pre_execution_snapshot(self, domain_state: Any) -> str:
        """创建执行前快照
        
        Args:
            domain_state: 域状态对象
            
        Returns:
            str: 快照ID
        """
        return self.collaboration_manager.create_snapshot(
            domain_state, "pre_execution"
        )
    
    def _record_execution_error(self, domain_state: Any,
                               snapshot_id: str, error_message: str) -> None:
        """记录执行错误
        
        Args:
            domain_state: 域状态对象
            snapshot_id: 快照ID
            error_message: 错误消息
        """
        try:
            # 处理字典型和对象型的域状态
            if hasattr(domain_state, 'workflow_id'):
                workflow_id = domain_state.workflow_id
            elif isinstance(domain_state, dict):
                workflow_id = domain_state.get("workflow_id", "unknown")  # type: ignore
            else:
                workflow_id = "unknown"
                
            self.collaboration_manager.record_state_change(
                workflow_id,
                "execution_error",
                {},
                {"error": error_message, "snapshot_id": snapshot_id}
            )
        except Exception as e:
            logger.error(f"记录执行错误失败: {str(e)}")
    
    def _record_state_completion(self, domain_state: Any,
                                snapshot_id: str, validation_errors: List[str]) -> None:
        """记录状态完成
        
        Args:
            domain_state: 域状态对象
            snapshot_id: 快照ID
            validation_errors: 验证错误列表
        """
        try:
            # 处理字典型和对象型的域状态
            if hasattr(domain_state, 'workflow_id'):
                workflow_id = domain_state.workflow_id
            elif isinstance(domain_state, dict):
                workflow_id = domain_state.get("workflow_id", "unknown")  # type: ignore
            else:
                workflow_id = "unknown"
                
            # 转换域状态为字典格式
            if isinstance(domain_state, dict):
                state_dict = domain_state
            else:
                # 对于dataclass或对象，尝试转换为字典
                if hasattr(domain_state, '__dict__'):
                    state_dict = domain_state.__dict__
                else:
                    state_dict = {}
                    
            self.collaboration_manager.record_state_change(
                workflow_id,
                "execution_completed",
                {},
                state_dict
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
