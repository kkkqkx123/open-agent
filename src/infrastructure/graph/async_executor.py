"""改进的异步工作流执行器实现

移除模拟的异步延迟，提供真正的异步执行能力。
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Callable, Awaitable, Union, cast
from abc import ABC, abstractmethod

from .config import GraphConfig
from .states import WorkflowState, update_state_with_message, BaseMessage, LCBaseMessage, AIMessage
from .registry import NodeRegistry, get_global_registry
from .adapters.state_adapter import StateAdapter
from src.infrastructure.async_utils.event_loop_manager import AsyncLock, AsyncContextManager
from typing import TYPE_CHECKING

from src.infrastructure.llm.interfaces import ILLMClient
from src.infrastructure.tools.executor import IToolExecutor

logger = logging.getLogger(__name__)


class IAsyncNodeExecutor(ABC):
    """异步节点执行器接口"""
    
    @abstractmethod
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点逻辑"""
        pass
    
    @abstractmethod
    async def cleanup(self) -> None:
        """清理资源"""
        pass


class IAsyncWorkflowExecutor(ABC):
    """异步工作流执行器接口"""
    
    @abstractmethod
    async def execute(self, graph: Any, initial_state: WorkflowState, **kwargs: Any) -> WorkflowState:
        """异步执行工作流"""
        pass


class AsyncNodeExecutor(IAsyncNodeExecutor, AsyncContextManager):
    """改进的异步节点执行器实现
    
    移除模拟延迟，提供真正的异步执行。
    """
    
    def __init__(self, node_registry: Optional[NodeRegistry] = None):
        self.node_registry = node_registry or get_global_registry()
        self.state_adapter = StateAdapter()
        self._lock = AsyncLock()
        self._llm_client = None
        self._tool_executor = None
    
    async def _get_dependencies(self):
        """获取依赖项（懒加载）"""
        if self._llm_client is None or self._tool_executor is None:
            from src.infrastructure.di_config import get_global_container
            container = get_global_container()
            
            if self._llm_client is None:
                from src.infrastructure.llm.interfaces import ILLMClient
                self._llm_client = container.get(ILLMClient)
            
            if self._tool_executor is None:
                from src.infrastructure.tools.interfaces import IToolManager
                # 获取工具管理器，然后创建执行器
                tool_manager = container.get(IToolManager)
                from src.infrastructure.tools.executor import AsyncToolExecutor
                from src.infrastructure.logger.logger import Logger
                tool_logger = Logger("AsyncToolExecutor")
                self._tool_executor = AsyncToolExecutor(
                    tool_manager=tool_manager,
                    logger=tool_logger
                )
    
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行节点
        
        节点执行降级过程：
        1. 首先尝试从节点注册表获取自定义节点类并执行
        2. 如果自定义节点类型不存在（抛出ValueError），则降级到内置节点执行器
        3. 内置节点类型包括：llm_node, tool_node, analysis_node, condition_node
        4. 如果节点类型完全未知，则记录警告并返回原始状态
        """
        async with self._lock:
            try:
                # 获取节点配置
                node_type = config.get("type", "default")
                
                # 从注册表获取节点类
                try:
                    node_class = self.node_registry.get_node_class(node_type)
                    if node_class:
                        node_instance = node_class()
                        
                        # 优先使用异步执行
                        if hasattr(node_instance, 'execute_async'):
                            domain_state = self.state_adapter.from_graph_state(state)
                            workflow_state_for_async = self.state_adapter.to_graph_state(domain_state)
                            result = await node_instance.execute_async(workflow_state_for_async, config)
                            return result.state
                        else:
                            # 同步执行在线程池中运行
                            domain_state = self.state_adapter.from_graph_state(state)
                            workflow_state_for_sync = self.state_adapter.to_graph_state(domain_state)
                            
                            loop = asyncio.get_running_loop()
                            result = await loop.run_in_executor(
                                None, node_instance.execute, workflow_state_for_sync, config
                            )
                            return result.state
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
        await self._get_dependencies()
        
        try:
            # 提取消息
            messages = state.get("messages", [])
            if not messages:
                logger.warning("LLM节点没有收到消息")
                return state
            
            # 调用LLM客户端
            if self._llm_client and hasattr(self._llm_client, 'generate_async'):
                response = await self._llm_client.generate_async(messages, config)
            else:
                # 如果没有异步方法，使用同步方法
                if self._llm_client:
                    response = self._llm_client.generate(messages, config)
                else:
                    # 如果LLM客户端未初始化，返回错误
                    from .states import AIMessage
                    response = AIMessage(content="LLM客户端未初始化")
            
            # 更新状态 - 修复响应对象的处理
            # 假设response本身就是一个消息对象
            new_messages = messages + [response]
            return {**state, "messages": new_messages}
            
        except Exception as e:
            logger.error(f"LLM节点执行失败: {e}")
            # 添加错误消息
            from .states import AIMessage
            error_message = AIMessage(content=f"LLM执行错误: {str(e)}")
            new_messages = state.get("messages", []) + [error_message]
            return {**state, "messages": new_messages}
    
    async def _execute_tool_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行工具节点"""
        await self._get_dependencies()
        
        try:
            # 提取工具调用
            tool_calls = state.get("tool_calls", [])
            if not tool_calls:
                logger.warning("工具节点没有收到工具调用")
                return state
            
            # 执行工具调用
            from src.domain.tools.interfaces import ToolCall
            tool_call_objects = [ToolCall(**call) for call in tool_calls]
            
            if self._tool_executor:
                if len(tool_call_objects) == 1:
                    # 单个工具调用
                    result = await self._tool_executor.execute_async(tool_call_objects[0])
                    tool_results = [result]
                else:
                    # 多个工具调用并行执行
                    tool_results = await self._tool_executor.execute_parallel_async(tool_call_objects)
            else:
                # 如果工具执行器未初始化，返回错误
                from src.domain.tools.interfaces import ToolResult
                tool_results = [ToolResult(
                    success=False,
                    error="工具执行器未初始化",
                    tool_name=tool_call_objects[0].name if tool_call_objects else "unknown"
                )]
            
            # 更新状态
            new_tool_results = state.get("tool_results", []) + [
                {
                    "tool_call": call.__dict__ if hasattr(call, '__dict__') else call,
                    "result": result.__dict__ if hasattr(result, '__dict__') else result
                }
                for call, result in zip(tool_calls, tool_results)
            ]
            
            return {**state, "tool_results": new_tool_results}
            
        except Exception as e:
            logger.error(f"工具节点执行失败: {e}")
            # 添加错误结果
            tool_calls = state.get("tool_calls", [])
            error_result = {
                "tool_call": tool_calls[0] if tool_calls else {},
                "result": {"success": False, "error": str(e)}
            }
            new_tool_results = state.get("tool_results", []) + [error_result]
            return {**state, "tool_results": new_tool_results}
    
    async def _execute_analysis_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行分析节点"""
        try:
            # 提取需要分析的内容
            messages = state.get("messages", [])
            if not messages:
                return state
            
            # 简单的分析逻辑（可以根据需要扩展）
            last_message = messages[-1]
            content = str(last_message.content)
            
            # 执行分析（这里可以调用实际的分析服务）
            analysis_result = {
                "message_length": len(content),
                "message_type": last_message.type if hasattr(last_message, 'type') else "unknown",
                "timestamp": asyncio.get_event_loop().time()
            }
            
            return {**state, "analysis": analysis_result}
            
        except Exception as e:
            logger.error(f"分析节点执行失败: {e}")
            return {**state, "analysis": {"error": str(e)}}
    
    async def _execute_condition_node_async(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """异步执行条件节点"""
        try:
            # 提取条件配置
            condition_config = config.get("condition", {})
            condition_type = condition_config.get("type", "default")
            
            # 根据条件类型执行不同的判断逻辑
            if condition_type == "message_count":
                messages = state.get("messages", [])
                result = len(messages) >= condition_config.get("min_count", 1)
            elif condition_type == "content_contains":
                messages = state.get("messages", [])
                search_text = condition_config.get("text", "")
                result = any(search_text in str(msg.content) for msg in messages)
            else:
                # 默认条件
                result = True
            
            return {**state, "condition_result": result}
            
        except Exception as e:
            logger.error(f"条件节点执行失败: {e}")
            return {**state, "condition_result": False}
    
    async def cleanup(self):
        """清理资源"""
        # 清理依赖项
        self._llm_client = None
        self._tool_executor = None


class AsyncWorkflowExecutor(IAsyncWorkflowExecutor, AsyncContextManager):
    """改进的异步工作流执行器实现
    
    提供真正的异步工作流执行能力。
    """
    
    def __init__(self, node_executor: Optional[IAsyncNodeExecutor] = None):
        self.node_executor = node_executor or AsyncNodeExecutor()
        self._lock = AsyncLock()
    
    async def execute(self, graph: Any, initial_state: WorkflowState, **kwargs: Any) -> WorkflowState:
        """异步执行工作流"""
        async with self._lock:
            try:
                # 检查图是否支持异步执行
                if hasattr(graph, 'ainvoke') and callable(getattr(graph, 'ainvoke')):
                    # 使用LangGraph的异步invoke方法
                    result = await graph.ainvoke(initial_state, **kwargs)
                    return cast(WorkflowState, result)
                elif hasattr(graph, 'astream') and callable(getattr(graph, 'astream')):
                    # 使用LangGraph的异步stream方法
                    final_state = initial_state
                    async for chunk in graph.astream(initial_state, **kwargs):
                        final_state = chunk
                    return final_state
                else:
                    # 如果图不支持异步，使用线程池执行同步方法
                    loop = asyncio.get_running_loop()
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
        **kwargs: Any
    ) -> WorkflowState:
        """异步执行工作流并支持流式回调"""
        async with self._lock:
            try:
                if hasattr(graph, 'astream') and callable(getattr(graph, 'astream')):
                    # 使用LangGraph的异步流式执行
                    final_state = initial_state
                    async for chunk in graph.astream(initial_state, **kwargs):
                        final_state = chunk
                        if callback:
                            # 如果回调是同步函数，在线程池中执行
                            if not asyncio.iscoroutinefunction(callback):
                                loop = asyncio.get_running_loop()
                                await loop.run_in_executor(None, callback, chunk)
                            else:
                                await callback(chunk)
                    return final_state
                else:
                    # 使用同步流式方法（在事件循环中执行）
                    loop = asyncio.get_running_loop()
                    
                    def sync_stream() -> WorkflowState:
                        result = initial_state
                        for chunk in graph.stream(initial_state, **kwargs):
                            result = chunk
                            if callback:
                                callback(chunk)
                        return result
                    
                    return await loop.run_in_executor(None, sync_stream)
                    
            except Exception as e:
                logger.error(f"工作流流式异步执行失败: {e}")
                raise
    
    async def cleanup(self):
        """清理资源"""
        if hasattr(self.node_executor, 'cleanup'):
            await self.node_executor.cleanup()


class AsyncGraphBuilder:
    """改进的异步图构建器
    
    提供更好的异步支持。
    """
    
    def __init__(self, base_builder: Any):
        """初始化异步图构建器"""
        self.base_builder = base_builder
    
    def build_graph(self, config: GraphConfig) -> Any:
        """构建支持异步执行的图"""
        # 使用基础构建器构建图
        graph = self.base_builder.build_graph(config)
        
        # 确保图支持异步执行
        if hasattr(graph, 'config'):
            # 配置异步相关选项
            graph.config.setdefault("async_execution", True)
            graph.config.setdefault("streaming", True)
        
        return graph
    
    def build_async_workflow_executor(self) -> AsyncWorkflowExecutor:
        """构建异步工作流执行器"""
        return AsyncWorkflowExecutor()
    
    def build_async_node_executor(self) -> AsyncNodeExecutor:
        """构建异步节点执行器"""
        return AsyncNodeExecutor()