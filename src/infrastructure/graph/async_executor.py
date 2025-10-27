"""异步工作流执行器实现

提供符合LangGraph最佳实践的异步执行功能。
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable, Union
from abc import ABC, abstractmethod

from .config import GraphConfig
from .state import WorkflowState, update_state_with_message, BaseMessage
from .registry import NodeRegistry, get_global_registry


logger = logging.getLogger(__name__)


class IAsyncNodeExecutor(ABC):
    """异步节点执行器接口"""
    
    @abstractmethod
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点逻辑"""
        pass


class IAsyncWorkflowExecutor(ABC):
    """异步工作流执行器接口"""
    
    @abstractmethod
    async def execute(self, graph: Any, initial_state: WorkflowState, **kwargs) -> WorkflowState:
        """异步执行工作流"""
        pass


class AsyncNodeExecutor(IAsyncNodeExecutor):
    """异步节点执行器实现"""
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None):
        self.node_registry = node_registry or get_global_registry()
    
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点"""
        try:
            # 获取节点配置
            node_type = config.get("type", "default")
            
            # 从注册表获取节点类
            try:
                node_class = self.node_registry.get_node_class(node_type)
                if node_class:
                    node_instance = node_class()
                    if hasattr(node_instance, 'execute_async'):
                        # 如果节点支持异步执行
                        return await node_instance.execute_async(state, config)
                    else:
                        # 否则使用同步执行（在事件循环中）
                        return await asyncio.get_event_loop().run_in_executor(
                            None, node_instance.execute, state, config
                        )
            except ValueError:
                # 节点类型不存在，尝试内置节点
                pass
            
            # 执行内置节点类型
            builtin_executor = self._get_builtin_executor(node_type)
            if builtin_executor:
                return await builtin_executor(state, config)
            
            # 默认返回原始状态
            logger.warning(f"未知节点类型: {node_type}，返回原始状态")
            return state
            
        except Exception as e:
            logger.error(f"节点执行失败: {e}")
            raise
    
    def _get_builtin_executor(self, node_type: str) -> Optional[Callable[[WorkflowState, Dict[str, Any]], Awaitable[WorkflowState]]]:
        """获取内置节点执行器"""
        builtin_executors = {
            "llm_node": self._execute_llm_node_async,
            "tool_node": self._execute_tool_node_async,
            "analysis_node": self._execute_analysis_node_async,
            "condition_node": self._execute_condition_node_async,
        }
        return builtin_executors.get(node_type)
    
    async def _execute_llm_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行LLM节点"""
        # 这里应该调用实际的LLM服务
        # 简化实现
        await asyncio.sleep(0.01)  # 模拟异步操作
        # 修复：使用TypedDict兼容的更新方式
        new_messages = state.get("messages", []) + [BaseMessage(content="LLM响应", type="ai")]
        return {**state, "messages": new_messages}
    
    async def _execute_tool_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行工具节点"""
        # 这里应该调用实际的工具服务
        # 简化实现
        await asyncio.sleep(0.01)  # 模拟异步操作
        # 修复：使用TypedDict兼容的更新方式
        new_tool_results = state.get("tool_results", []) + [{"tool_call": state.get("tool_calls", [{}])[0] if state.get("tool_calls") else {}, "result": "模拟结果"}]
        return {**state, "tool_results": new_tool_results}
    
    async def _execute_analysis_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行分析节点"""
        # 这里应该执行实际的分析逻辑
        # 简化实现
        await asyncio.sleep(0.01)  # 模拟异步操作
        # 修复：使用TypedDict兼容的更新方式
        return {**state, "analysis": "分析结果"}
    
    async def _execute_condition_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行条件节点"""
        # 这里应该执行实际的条件判断
        # 简化实现
        await asyncio.sleep(0.01)  # 模拟异步操作
        # 修复：使用TypedDict兼容的更新方式
        return {**state, "condition_result": True}


class AsyncWorkflowExecutor(IAsyncWorkflowExecutor):
    """异步工作流执行器实现"""
    
    def __init__(self, node_executor: Optional[IAsyncNodeExecutor] = None):
        self.node_executor = node_executor or AsyncNodeExecutor()
    
    async def execute(self, graph: Any, initial_state: WorkflowState, **kwargs) -> WorkflowState:
        """异步执行工作流"""
        try:
            # 检查图是否支持异步执行
            if hasattr(graph, 'ainvoke') and callable(getattr(graph, 'ainvoke')):
                # 使用LangGraph的异步invoke方法
                result = await graph.ainvoke(initial_state, **kwargs)
                return result
            elif hasattr(graph, 'astream') and callable(getattr(graph, 'astream')):
                # 使用LangGraph的异步stream方法
                async for chunk in graph.astream(initial_state, **kwargs):
                    # 处理流式结果
                    pass
                # 返回最终状态
                return initial_state
            else:
                # 如果图不支持异步，使用线程池执行同步方法
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(
                    None, graph.invoke, initial_state, kwargs
                )
                
        except Exception as e:
            logger.error(f"工作流异步执行失败: {e}")
            raise
    
    async def execute_with_streaming(
        self, 
        graph: Any, 
        initial_state: WorkflowState, 
        callback: Optional[Callable[[WorkflowState], None]] = None,
        **kwargs
    ) -> WorkflowState:
        """异步执行工作流并支持流式回调"""
        try:
            if hasattr(graph, 'astream') and callable(getattr(graph, 'astream')):
                # 使用LangGraph的异步流式执行
                final_state = initial_state
                async for chunk in graph.astream(initial_state, **kwargs):
                    final_state = chunk
                    if callback:
                        callback(chunk)
                return final_state
            else:
                # 使用同步流式方法（在事件循环中执行）
                loop = asyncio.get_event_loop()
                
                def sync_stream():
                    result = None
                    for chunk in graph.stream(initial_state, **kwargs):
                        result = chunk
                        if callback:
                            callback(chunk)
                    return result
                
                return await loop.run_in_executor(None, sync_stream)
                
        except Exception as e:
            logger.error(f"工作流流式异步执行失败: {e}")
            raise


class AsyncGraphBuilder:
    """异步图构建器 - 扩展原有的GraphBuilder以支持异步执行"""
    
    def __init__(self, base_builder: Any):
        """初始化异步图构建器
        Args:
            base_builder: 基础图构建器实例
        """
        self.base_builder = base_builder
    
    def build_graph(self, config: GraphConfig) -> Any:
        """构建支持异步执行的图"""
        # 使用基础构建器构建图
        graph = self.base_builder.build_graph(config)
        
        # 如果需要额外的异步支持，可以在此处添加
        # 目前主要依赖LangGraph的原生异步支持
        
        return graph
    
    def build_async_workflow_executor(self) -> AsyncWorkflowExecutor:
        """构建异步工作流执行器"""
        return AsyncWorkflowExecutor()
    
    def build_async_node_executor(self) -> AsyncNodeExecutor:
        """构建异步节点执行器"""
        return AsyncNodeExecutor()