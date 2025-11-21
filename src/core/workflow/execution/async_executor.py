"""
异步节点执行器实现

提供单个节点的异步执行能力，与节点注册表集成，处理状态转换和错误处理。
"""

import logging
import asyncio
import time
from typing import Any, Dict, Optional, List, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from src.core.workflow.config.config import GraphConfig
from src.core.workflow.states import WorkflowState, update_state_with_message, BaseMessage, AIMessage
from src.core.workflow.graph.nodes.registry import NodeRegistry, get_global_registry
from src.services.workflow.state_converter import WorkflowStateConverter
from core.common.async_tuils import AsyncLock, AsyncContextManager
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.llm import ILLMClient
    from src.core.tools.executor import IToolExecutor

logger = logging.getLogger(__name__)


@dataclass
class NodeExecutionContext:
    """节点执行上下文"""
    node_id: str
    node_type: str
    execution_id: str
    workflow_id: str
    start_time: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if self.start_time == 0:
            self.start_time = time.time()


@dataclass
class NodeExecutionResult:
    """节点执行结果"""
    success: bool
    state: WorkflowState
    next_node: Optional[str] = None
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class IAsyncNodeExecutor(ABC):
    """异步节点执行器接口"""
    
    @abstractmethod
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点逻辑"""
        pass
    
    @abstractmethod
    async def execute_with_context(
        self, 
        state: WorkflowState, 
        config: Dict[str, Any],
        context: NodeExecutionContext
    ) -> NodeExecutionResult:
        """带上下文的异步执行"""
        pass


class AsyncNodeExecutor(IAsyncNodeExecutor):
    """异步节点执行器实现
    
    专注于节点级别的异步执行，与节点注册表集成，处理状态转换。
    """
    
    def __init__(
        self,
        node_registry: Optional[NodeRegistry] = None,
        state_converter: Optional[WorkflowStateConverter] = None
    ):
        """初始化异步节点执行器
        
        Args:
            node_registry: 节点注册表，如果为None则使用全局注册表
            state_converter: 状态转换器，如果为None则创建新实例
        """
        self.node_registry = node_registry or get_global_registry()
        self.state_converter = state_converter or WorkflowStateConverter()
        self._execution_lock = AsyncLock()
        
        logger.debug("异步节点执行器初始化完成")
    
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点逻辑
        
        Args:
            state: 工作流状态
            config: 节点配置，必须包含 node_type
            
        Returns:
            WorkflowState: 执行后的状态
            
        Raises:
            ValueError: 当配置中缺少 node_type 时
            Exception: 当节点执行失败时
        """
        # 创建基本执行上下文
        context = NodeExecutionContext(
            node_id=config.get('node_id', 'unknown'),
            node_type=config.get('node_type', ''),
            execution_id=f"exec_{int(time.time() * 1000)}",
            workflow_id=config.get('workflow_id', 'unknown'),
            start_time=time.time(),
            metadata=config.get('metadata', {})
        )
        
        # 执行节点并返回状态
        result = await self.execute_with_context(state, config, context)
        
        if not result.success:
            raise Exception(f"节点执行失败: {result.error}")
        
        return result.state
    
    async def execute_with_context(
        self, 
        state: WorkflowState, 
        config: Dict[str, Any],
        context: NodeExecutionContext
    ) -> NodeExecutionResult:
        """带上下文的异步执行
        
        Args:
            state: 工作流状态
            config: 节点配置
            context: 执行上下文
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        start_time = time.time()
        
        try:
            # 获取节点类型
            node_type = config.get('node_type')
            if not node_type:
                raise ValueError("配置中缺少 node_type")
            
            logger.debug(f"开始异步执行节点: {node_type} (ID: {context.node_id})")
            
            # 获取节点实例
            node = self.node_registry.get_node_instance(node_type)
            
            # 验证节点配置
            validation_errors = node.validate_config(config)
            if validation_errors:
                raise ValueError(f"节点配置验证失败: {', '.join(validation_errors)}")
            
            # 转换状态格式（如果需要）
            converted_state = self._prepare_input_state(state, config)
            
            # 执行节点
            if hasattr(node, 'execute_async'):
                # 节点支持异步执行
                node_result = await node.execute_async(converted_state, config)
            else:
                # 节点只支持同步执行，在线程池中运行
                loop = asyncio.get_event_loop()
                node_result = await loop.run_in_executor(None, node.execute, converted_state, config)
            
            # 处理执行结果
            final_state = self._process_node_result(node_result, state, config)
            
            # 计算执行时间
            execution_time = time.time() - start_time
            
            logger.debug(f"节点异步执行完成: {node_type}, 耗时: {execution_time:.3f}s")
            
            return NodeExecutionResult(
                success=True,
                state=final_state,
                next_node=self._extract_next_node(node_result),
                execution_time=execution_time,
                metadata={
                    'node_type': node_type,
                    'execution_id': context.execution_id,
                    'supports_async': hasattr(node, 'execute_async')
                }
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"节点 {context.node_type} 执行失败: {str(e)}"
            logger.error(error_msg)
            
            return NodeExecutionResult(
                success=False,
                state=state,  # 返回原始状态
                error=error_msg,
                execution_time=execution_time,
                metadata={
                    'node_type': context.node_type,
                    'execution_id': context.execution_id,
                    'error_type': type(e).__name__
                }
            )
    
    async def execute_batch(
        self,
        states: List[WorkflowState],
        configs: List[Dict[str, Any]]
    ) -> List[NodeExecutionResult]:
        """批量异步执行节点
        
        Args:
            states: 状态列表
            configs: 配置列表
            
        Returns:
            List[NodeExecutionResult]: 执行结果列表
        """
        if len(states) != len(configs):
            raise ValueError("状态和配置数量不匹配")
        
        # 创建执行任务
        tasks = []
        for i, (state, config) in enumerate(zip(states, configs)):
            context = NodeExecutionContext(
                node_id=config.get('node_id', f'batch_node_{i}'),
                node_type=config.get('node_type', ''),
                execution_id=f"batch_exec_{i}_{int(time.time() * 1000)}",
                workflow_id=config.get('workflow_id', 'batch_execution'),
                start_time=time.time(),
                metadata={'batch_index': i}
            )
            task = self.execute_with_context(state, config, context)
            tasks.append(task)
        
        # 并发执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(NodeExecutionResult(
                    success=False,
                    state=states[i],
                    error=str(result),
                    metadata={'error_type': type(result).__name__}
                ))
            else:
                processed_results.append(result)
        
        return processed_results
    
    def _prepare_input_state(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """准备输入状态
        
        Args:
            state: 原始状态
            config: 节点配置
            
        Returns:
            WorkflowState: 准备后的状态
        """
        # 如果配置指定了状态预处理，则应用预处理
        if 'state_preprocessing' in config:
            preprocessing_config = config['state_preprocessing']
            
            # 添加节点信息到状态
            if preprocessing_config.get('add_node_info', False):
                state.set_value('current_node', config.get('node_id'))
                state.set_value('current_node_type', config.get('node_type'))
            
            # 清理临时字段
            if preprocessing_config.get('clear_temp_fields', False):
                temp_fields = preprocessing_config.get('temp_fields', [])
                for field in temp_fields:
                    if field in state.values:
                        del state.values[field]
        
        return state
    
    def _process_node_result(
        self,
        node_result: Any,
        original_state: WorkflowState,
        config: Dict[str, Any]
    ) -> WorkflowState:
        """处理节点执行结果
        
        Args:
            node_result: 节点执行结果
            original_state: 原始状态
            config: 节点配置
            
        Returns:
            WorkflowState: 处理后的最终状态
        """
        # 如果节点返回的是 NodeExecutionResult
        if hasattr(node_result, 'state'):
            final_state = node_result.state
        elif isinstance(node_result, dict):
            # 如果返回的是字典，使用 from_dict 方法创建新的 WorkflowState
            try:
                final_state = WorkflowState.from_dict(node_result)
            except Exception:
                # 如果 from_dict 失败，使用原始状态并更新值
                final_state = original_state
                # 更新原始状态的值
                for key, value in node_result.items():
                    if hasattr(final_state, key):
                        setattr(final_state, key, value)
                    else:
                        final_state.set_value(key, value)
        elif isinstance(node_result, WorkflowState):
            # 如果直接返回 WorkflowState
            final_state = node_result
        else:
            # 其他情况，保持原始状态
            logger.warning(f"节点返回了未知类型的结果: {type(node_result)}")
            final_state = original_state
        
        # 应用后处理配置
        if 'state_postprocessing' in config:
            postprocessing_config = config['state_postprocessing']
            
            # 添加执行时间戳
            if postprocessing_config.get('add_timestamp', False):
                final_state.set_value('last_execution_time', time.time())
            
            # 添加节点执行标记
            if postprocessing_config.get('mark_execution', False):
                executed_nodes = final_state.get_value('executed_nodes', [])
                executed_nodes.append(config.get('node_id'))
                final_state.set_value('executed_nodes', executed_nodes)
        
        return final_state
    
    def _extract_next_node(self, node_result: Any) -> Optional[str]:
        """从节点结果中提取下一个节点
        
        Args:
            node_result: 节点执行结果
            
        Returns:
            Optional[str]: 下一个节点ID，如果没有则返回None
        """
        # 如果节点返回的是 NodeExecutionResult
        if hasattr(node_result, 'next_node'):
            return node_result.next_node
        
        # 如果返回的是字典
        if isinstance(node_result, dict):
            return node_result.get('next_node')
        
        # 其他情况返回None
        return None
    
    async def cleanup(self):
        """清理资源"""
        # 当前实现中没有需要清理的资源
        pass


# 便捷函数
async def execute_node_async(
    state: WorkflowState,
    node_type: str,
    config: Optional[Dict[str, Any]] = None
) -> WorkflowState:
    """异步执行单个节点的便捷函数
    
    Args:
        state: 工作流状态
        node_type: 节点类型
        config: 节点配置
        
    Returns:
        WorkflowState: 执行后的状态
    """
    executor = AsyncNodeExecutor()
    
    if config is None:
        config = {}
    
    config['node_type'] = node_type
    
    return await executor.execute(state, config)


async def execute_nodes_batch(
    states: List[WorkflowState],
    node_types: List[str],
    configs: Optional[List[Dict[str, Any]]] = None
) -> List[NodeExecutionResult]:
    """批量异步执行节点的便捷函数
    
    Args:
        states: 状态列表
        node_types: 节点类型列表
        configs: 配置列表
        
    Returns:
        List[NodeExecutionResult]: 执行结果列表
    """
    if configs is None:
        configs = [{} for _ in range(len(states))]
    
    # 添加节点类型到配置
    for i, node_type in enumerate(node_types):
        if i < len(configs):
            configs[i]['node_type'] = node_type
    
    executor = AsyncNodeExecutor()
    return await executor.execute_batch(states, configs)