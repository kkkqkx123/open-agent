"""混合执行模式

提供工作流的混合执行模式实现，可以根据节点特性自动选择同步或异步执行。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, TYPE_CHECKING

from .mode_base import BaseMode, IExecutionMode
from .sync_mode import SyncMode
from .async_mode import AsyncMode

if TYPE_CHECKING:
    from src.interfaces import IWorkflowState
    from src.interfaces.workflow.core import INode
    from src.core.workflow.execution.core.execution_context import ExecutionContext, NodeResult

logger = get_logger(__name__)


class IHybridMode(IExecutionMode):
    """混合模式接口"""
    pass


class HybridMode(BaseMode, IHybridMode):
    """混合执行模式
    
    根据节点特性自动选择同步或异步执行，提供最优的执行性能。
    """
    
    def __init__(self, prefer_async: bool = True):
        """初始化混合模式
        
        Args:
            prefer_async: 是否优先使用异步执行
        """
        super().__init__("hybrid", supports_async=True)
        self.prefer_async = prefer_async
        self.sync_mode = SyncMode()
        self.async_mode = AsyncMode()
        logger.debug(f"混合执行模式初始化完成，优先异步: {prefer_async}")
    
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
        # 根据节点特性选择执行模式
        execution_mode = self._select_execution_mode(node, context)
        
        if execution_mode == "async":
            # 使用异步模式执行（同步包装）
            return self.async_mode.execute_node(node, state, context)
        else:
            # 使用同步模式执行
            return self.sync_mode.execute_node(node, state, context)
    
    async def execute_node_async(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ) -> 'NodeResult':
        """异步执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Returns:
            NodeResult: 节点执行结果
        """
        # 根据节点特性选择执行模式
        execution_mode = self._select_execution_mode(node, context)
        
        if execution_mode == "async":
            # 使用异步模式执行
            return await self.async_mode.execute_node_async(node, state, context)
        else:
            # 使用同步模式执行（异步包装）
            return await self.sync_mode.execute_node_async(node, state, context)
    
    def supports_streaming(self) -> bool:
        """是否支持流式执行
        
        Returns:
            bool: 支持流式执行
        """
        return True
    
    async def execute_node_stream(
        self, 
        node: 'INode', 
        state: 'IWorkflowState', 
        context: 'ExecutionContext'
    ):
        """流式执行节点
        
        Args:
            node: 节点实例
            state: 当前状态
            context: 执行上下文
            
        Yields:
            Dict[str, Any]: 流式事件
        """
        # 根据节点特性选择执行模式
        execution_mode = self._select_execution_mode(node, context)
        
        if execution_mode == "async":
            # 使用异步模式流式执行
            async for event in self.async_mode.execute_node_stream(node, state, context):
                yield event
        else:
            # 使用异步模式流式执行
            async for event in self.async_mode.execute_node_stream(node, state, context):
                yield event
    
    def _select_execution_mode(
        self, 
        node: 'INode', 
        context: 'ExecutionContext'
    ) -> str:
        """选择执行模式
        
        Args:
            node: 节点实例
            context: 执行上下文
            
        Returns:
            str: 执行模式 ("sync" 或 "async")
        """
        # 检查上下文是否强制指定了执行模式
        forced_mode = context.get_config("force_execution_mode")
        if forced_mode in ["sync", "async"]:
            return forced_mode
        
        # 检查节点是否支持异步执行
        if hasattr(node, 'execute_async'):
            # 节点支持异步执行
            if self.prefer_async:
                return "async"
            else:
                # 检查节点是否更适合同步执行
                if self._is_sync_preferred(node, context):
                    return "sync"
                else:
                    return "async"
        else:
            # 节点只支持同步执行
            return "sync"
    
    def _is_sync_preferred(
        self, 
        node: 'INode', 
        context: 'ExecutionContext'
    ) -> bool:
        """判断是否应该优先使用同步执行
        
        Args:
            node: 节点实例
            context: 执行上下文
            
        Returns:
            bool: 是否应该优先使用同步执行
        """
        # 检查节点类型
        node_type = getattr(node, 'node_type', '').lower()
        
        # 某些类型的节点更适合同步执行
        sync_preferred_types = [
            'calculator',
            'validator',
            'transformer',
            'converter'
        ]
        
        if node_type in sync_preferred_types:
            return True
        
        # 检查节点配置
        if hasattr(node, 'config'):
            config = getattr(node, 'config', {})
            if config.get('prefer_sync', False):
                return True
        
        # 检查上下文配置
        if context.get_config('prefer_sync', False):
            return True
        
        # 检查工作流复杂度
        if context.get_config('simple_workflow', False):
            return True
        
        return False
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            "mode": "hybrid",
            "prefer_async": self.prefer_async,
            "supported_modes": ["sync", "async", "streaming"],
            "mode_selection_criteria": [
                "node_async_support",
                "node_type",
                "node_config",
                "context_config",
                "workflow_complexity"
            ]
        }
    
    def configure_mode_selection(
        self, 
        prefer_async: Optional[bool] = None,
        sync_preferred_types: Optional[List[str]] = None
    ) -> None:
        """配置模式选择策略
        
        Args:
            prefer_async: 是否优先使用异步执行
            sync_preferred_types: 优先同步执行的节点类型列表
        """
        if prefer_async is not None:
            self.prefer_async = prefer_async
        
        # 这里可以扩展更多的配置选项
        logger.debug(f"混合模式配置已更新，优先异步: {self.prefer_async}")
    
    def analyze_node_execution_characteristics(
        self, 
        node: 'INode'
    ) -> Dict[str, Any]:
        """分析节点执行特性
        
        Args:
            node: 节点实例
            
        Returns:
            Dict[str, Any]: 节点执行特性分析
        """
        characteristics = {
            "node_id": getattr(node, 'node_id', 'unknown'),
            "node_type": getattr(node, 'node_type', 'unknown'),
            "supports_async": hasattr(node, 'execute_async'),
            "supports_streaming": hasattr(node, 'execute_stream') or hasattr(node, 'execute_stream_async'),
            "recommended_mode": self._select_execution_mode(node, ExecutionContext("test", "test"))
        }
        
        # 分析节点复杂度
        if hasattr(node, 'config'):
            config = getattr(node, 'config', {})
            characteristics.update({
                "has_complex_config": len(config) > 5,
                "config_keys": list(config.keys())
            })
        
        # 分析节点依赖
        if hasattr(node, 'dependencies'):
            dependencies = getattr(node, 'dependencies', [])
            characteristics.update({
                "has_dependencies": len(dependencies) > 0,
                "dependency_count": len(dependencies)
            })
        
        return characteristics