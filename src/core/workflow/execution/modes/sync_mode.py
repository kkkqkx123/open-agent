"""同步执行模式

提供工作流的同步执行模式实现。
"""

from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, Optional, TYPE_CHECKING

from .mode_base import BaseMode, IExecutionMode

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import INode
    from src.core.workflow.execution.core.execution_context import ExecutionContext, NodeResult

logger = get_logger(__name__)


class ISyncMode(IExecutionMode):
    """同步模式接口"""
    pass


class SyncMode(BaseMode, ISyncMode):
    """同步执行模式
    
    提供节点的同步执行能力。
    """
    
    def __init__(self):
        """初始化同步模式"""
        super().__init__("sync", supports_async=False)
        logger.debug("同步执行模式初始化完成")
    
    def execute_node(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """同步执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        start_time = time.time()
        
        try:
            # 验证输入
            self.validate_inputs(node, state, context)
            
            logger.debug(f"同步执行节点: {getattr(node, 'node_id', 'unknown')}")
            
            # 执行节点（将IWorkflowState作为IState使用）
            node_result = node.execute(state, context.config)  # type: ignore
            
            # 处理执行结果
            result = self._process_node_result(node_result, state, context)
            
            # 设置执行时间
            result.execution_time = time.time() - start_time
            
            logger.debug(f"节点同步执行完成: {getattr(node, 'node_id', 'unknown')}, 耗时: {result.execution_time:.3f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"节点同步执行失败: {e}")
            
            return self.handle_execution_error(e, node, state)
    
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """异步执行节点（同步模式不支持）
        
        同步模式不支持异步执行。
        如需异步执行，请使用AsyncMode。
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Raises:
            RuntimeError: 同步模式不支持异步执行
        """
        raise RuntimeError(
            f"SyncMode does not support async execution. "
            f"Use AsyncMode for async execution of node '{getattr(node, 'node_id', 'unknown')}'. "
            f"Or call execute_node() instead of execute_node_async()."
        )
    
    def _process_node_result(
        self, 
        node_result: Any, 
        original_state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """处理节点执行结果
        
        Args:
            node_result: 节点执行结果
            original_state: 原始状态
            context: 执行上下文
            
        Returns:
            NodeResult: 处理后的节点执行结果
        """
        # 提取状态
        if hasattr(node_result, 'state'):
            final_state = node_result.state
        elif isinstance(node_result, dict):
            # 如果返回的是字典，尝试更新状态
            final_state = original_state
            for key, value in node_result.items():
                if hasattr(final_state, key):
                    setattr(final_state, key, value)
                else:
                    final_state = final_state.set_field(key, value)
        else:
            # 其他情况，保持原始状态
            final_state = original_state
        
        # 提取下一个节点
        next_node = None
        if hasattr(node_result, 'next_node'):
            next_node = node_result.next_node  # type: ignore
        elif isinstance(node_result, dict):
            next_node = node_result.get('next_node')  # type: ignore
        
        # 提取元数据
        metadata: Dict[str, Any] = {}
        if hasattr(node_result, 'metadata'):
            metadata = node_result.metadata  # type: ignore
        elif isinstance(node_result, dict):
            metadata = node_result.get('metadata', {})  # type: ignore
        
        # 添加节点信息到元数据
        metadata.update({
            "node_id": getattr(node_result, 'node_id', getattr(original_state, 'current_node_id', 'unknown')),
            "node_type": getattr(node_result, 'node_type', 'unknown'),
            "execution_timestamp": time.time(),
            "execution_mode": "sync"
        })
        
        return self.create_node_result(
            success=True,
            state=final_state,
            next_node=next_node,
            metadata=metadata
        )