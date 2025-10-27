"""异步执行器单元测试"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Any, Dict, AsyncGenerator

from src.infrastructure.graph.async_executor import (
    IAsyncNodeExecutor,
    IAsyncWorkflowExecutor,
    AsyncNodeExecutor,
    AsyncWorkflowExecutor,
    AsyncGraphBuilder
)
from src.infrastructure.graph.config import GraphConfig
from src.infrastructure.graph.state import WorkflowState, BaseMessage
from src.infrastructure.graph.registry import NodeRegistry, BaseNode
class MockAsyncIterator:
    """模拟异步迭代器类"""
    def __init__(self, chunks):
        self.chunks = chunks
        self.index = 0
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.index < len(self.chunks):
            result = self.chunks[self.index]
            self.index += 1
            return result
        raise StopAsyncIteration


class TestIAsyncNodeExecutor:
    """异步节点执行器接口测试"""
    
    def test_interface_methods(self) -> None:
        """测试接口方法定义"""
        # 确保接口是抽象的
        with pytest.raises(TypeError):
            IAsyncNodeExecutor()  # type: ignore
    
    def test_execute_method_signature(self) -> None:
        """测试execute方法签名"""
        # 检查方法签名
        assert hasattr(IAsyncNodeExecutor, 'execute')
        method = IAsyncNodeExecutor.execute
        assert method.__isabstractmethod__  # type: ignore


class TestIAsyncWorkflowExecutor:
    """异步工作流执行器接口测试"""
    
    def test_interface_methods(self) -> None:
        """测试接口方法定义"""
        # 确保接口是抽象的
        with pytest.raises(TypeError):
            IAsyncWorkflowExecutor()  # type: ignore
    
    def test_execute_method_signature(self) -> None:
        """测试execute方法签名"""
        # 检查方法签名
        assert hasattr(IAsyncWorkflowExecutor, 'execute')
        method = IAsyncWorkflowExecutor.execute
        assert method.__isabstractmethod__  # type: ignore


class TestAsyncNodeExecutor:
    """异步节点执行器测试"""

    @pytest.fixture
    def mock_registry(self) -> Mock:
        """模拟节点注册表"""
        registry = Mock(spec=NodeRegistry)
        return registry

    @pytest.fixture
    def executor(self, mock_registry: Mock) -> AsyncNodeExecutor:
        """创建异步节点执行器实例"""
        return AsyncNodeExecutor(mock_registry)

    @pytest.fixture
    def sample_state(self) -> dict[str, Any]:
        """示例状态"""
        return {
            "messages": [BaseMessage(content="测试消息", type="human")],
            "tool_calls": [],
            "tool_results": []
        }
    
    @pytest.mark.asyncio
    async def test_execute_with_registered_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行已注册的节点"""
        # 创建模拟节点类
        mock_node_class = Mock()
        mock_node_instance = Mock()
        mock_node_instance.execute_async = AsyncMock(return_value=sample_state)
        mock_node_class.return_value = mock_node_instance
        
        # 配置注册表
        mock_registry.get_node_class.return_value = mock_node_class
        
        # 执行
        config = {"type": "test_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_registry.get_node_class.assert_called_once_with("test_node")
        mock_node_instance.execute_async.assert_called_once_with(sample_state, config)
    
    @pytest.mark.asyncio
    async def test_execute_with_sync_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行同步节点"""
        # 创建模拟节点类
        mock_node_class = Mock()
        mock_node_instance = Mock()
        mock_node_instance.execute = Mock(return_value=sample_state)
        # 没有execute_async方法
        del mock_node_instance.execute_async
        mock_node_class.return_value = mock_node_instance
        
        # 配置注册表
        mock_registry.get_node_class.return_value = mock_node_class
        
        # 执行
        config = {"type": "sync_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_node_instance.execute.assert_called_once_with(sample_state, config)
    
    @pytest.mark.asyncio
    async def test_execute_with_builtin_llm_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行内置LLM节点"""
        # 配置注册表返回None，强制使用内置执行器
        mock_registry.get_node_class.return_value = None
        
        config = {"type": "llm_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证结果包含新消息
        assert "messages" in result
        assert len(result["messages"]) > len(sample_state["messages"])
        assert result["messages"][-1].type == "ai"
    
    @pytest.mark.asyncio
    async def test_execute_with_builtin_tool_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行内置工具节点"""
        # 配置注册表返回None，强制使用内置执行器
        mock_registry.get_node_class.return_value = None
        
        # 添加工具调用到状态
        sample_state["tool_calls"] = [{"name": "test_tool", "args": {}}]
        
        config = {"type": "tool_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证结果包含工具结果
        assert "tool_results" in result
        assert len(result["tool_results"]) > 0
    
    @pytest.mark.asyncio
    async def test_execute_with_builtin_analysis_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行内置分析节点"""
        # 配置注册表返回None，强制使用内置执行器
        mock_registry.get_node_class.return_value = None
        
        config = {"type": "analysis_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证结果包含分析
        assert "analysis" in result
        assert result["analysis"] == "分析结果"
    
    @pytest.mark.asyncio
    async def test_execute_with_builtin_condition_node(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行内置条件节点"""
        # 配置注册表返回None，强制使用内置执行器
        mock_registry.get_node_class.return_value = None
        
        config = {"type": "condition_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证结果包含条件结果
        assert "condition_result" in result
        assert result["condition_result"] is True  # type: ignore
    
    @pytest.mark.asyncio
    async def test_execute_with_unknown_node(self, executor: AsyncNodeExecutor, sample_state: dict[str, Any]) -> None:
        """测试执行未知节点类型"""
        # 配置注册表返回None
        executor.node_registry.get_node_class.side_effect = ValueError("未知节点类型")  # type: ignore
        
        config = {"type": "unknown_node"}
        result = await executor.execute(sample_state, config)  # type: ignore
        
        # 验证返回原始状态
        assert result == sample_state
    
    @pytest.mark.asyncio
    async def test_execute_with_exception(self, executor: AsyncNodeExecutor, mock_registry: Mock, sample_state: dict[str, Any]) -> None:
        """测试执行时发生异常"""
        # 配置注册表抛出异常
        mock_registry.get_node_class.side_effect = Exception("测试异常")
        
        config = {"type": "error_node"}
        
        # 验证异常被抛出
        with pytest.raises(Exception, match="测试异常"):
            await executor.execute(sample_state, config)  # type: ignore
    
    def test_get_builtin_executor(self, executor: AsyncNodeExecutor) -> None:
        """测试获取内置执行器"""
        # 测试所有内置类型
        builtin_types = ["llm_node", "tool_node", "analysis_node", "condition_node"]
        
        for node_type in builtin_types:
            executor_func = executor._get_builtin_executor(node_type)
            assert executor_func is not None
            assert asyncio.iscoroutinefunction(executor_func)
        
        # 测试未知类型
        unknown_func = executor._get_builtin_executor("unknown_type")
        assert unknown_func is None


class TestAsyncWorkflowExecutor:
    """异步工作流执行器测试"""

    @pytest.fixture
    def mock_node_executor(self) -> Mock:
        """模拟节点执行器"""
        return Mock(spec=IAsyncNodeExecutor)

    @pytest.fixture
    def executor(self, mock_node_executor: Mock) -> AsyncWorkflowExecutor:
        """创建异步工作流执行器实例"""
        return AsyncWorkflowExecutor(mock_node_executor)

    @pytest.fixture
    def sample_state(self) -> dict[str, Any]:
        """示例状态"""
        return {
            "messages": [BaseMessage(content="测试消息", type="human")],
            "tool_calls": [],
            "tool_results": []
        }
    
    @pytest.mark.asyncio
    async def test_execute_with_ainvoke(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试使用ainvoke方法执行"""
        # 创建模拟图
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(return_value=sample_state)
        
        # 执行
        result = await executor.execute(mock_graph, sample_state)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_graph.ainvoke.assert_called_once_with(sample_state)
    
    @pytest.mark.asyncio
    async def test_execute_with_astream(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试使用astream方法执行"""
        # 创建模拟图
        mock_graph = Mock()
        mock_graph.ainvoke = None  # 没有ainvoke方法
        
        # 创建异步迭代器类
        class MockAsyncIterator:
            def __init__(self, chunks):
                self.chunks = chunks
                self.index = 0
            
            def __aiter__(self):
                return self
            
            async def __anext__(self):
                if self.index < len(self.chunks):
                    result = self.chunks[self.index]
                    self.index += 1
                    return result
                raise StopAsyncIteration
        
        # 创建异步迭代器实例
        chunks = [{"step": "1"}, {"step": "2"}, sample_state]
        mock_iterator = MockAsyncIterator(chunks)
        
        # 设置 astream 方法返回异步迭代器
        mock_graph.astream = Mock(return_value=mock_iterator)
        
        # 执行
        result = await executor.execute(mock_graph, sample_state)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_graph.astream.assert_called_once_with(sample_state)
    
    @pytest.mark.asyncio
    async def test_execute_with_sync_invoke(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试使用同步invoke方法执行"""
        # 创建模拟图
        mock_graph = Mock()
        mock_graph.ainvoke = None  # 没有ainvoke方法
        mock_graph.astream = None  # 没有astream方法
        mock_graph.invoke = Mock(return_value=sample_state)
        
        # 执行
        result = await executor.execute(mock_graph, sample_state)  # type: ignore
        
        # 验证
        assert result == sample_state
        mock_graph.invoke.assert_called_once_with(sample_state, {})
    
    @pytest.mark.asyncio
    async def test_execute_with_exception(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试执行时发生异常"""
        # 创建模拟图
        mock_graph = Mock()
        mock_graph.ainvoke = AsyncMock(side_effect=Exception("测试异常"))
        
        # 验证异常被抛出
        with pytest.raises(Exception, match="测试异常"):
            await executor.execute(mock_graph, sample_state)  # type: ignore
    
    @pytest.mark.asyncio
    async def test_execute_with_streaming(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试流式执行"""
        # 创建模拟图
        mock_graph = Mock()
        # 设置流式返回和回调
        callback = Mock()
        chunks = [{"step": "1"}, {"step": "2"}, sample_state]
        
        # 创建异步迭代器实例
        mock_iterator = MockAsyncIterator(chunks)
        
        # 设置 astream 方法返回异步迭代器
        mock_graph.astream = Mock(return_value=mock_iterator)
        
        # 执行
        result = await executor.execute_with_streaming(mock_graph, sample_state, callback)  # type: ignore
        
        # 验证
        assert result == sample_state
        assert callback.call_count == len(chunks)
        mock_graph.astream.assert_called_once_with(sample_state)
    
    @pytest.mark.asyncio
    async def test_execute_with_streaming_sync(self, executor: AsyncWorkflowExecutor, sample_state: dict[str, Any]) -> None:
        """测试同步流式执行"""
        # 创建模拟图
        mock_graph = Mock()
        mock_graph.astream = None  # 没有astream方法
        mock_graph.stream = Mock(return_value=iter([{"step": "1"}, {"step": "2"}, sample_state]))
        
        callback = Mock()
        
        # 执行
        result = await executor.execute_with_streaming(mock_graph, sample_state, callback)  # type: ignore
        
        # 验证
        assert result == sample_state
        assert callback.call_count == 3
        mock_graph.stream.assert_called_once_with(sample_state)


class TestAsyncGraphBuilder:
    """异步图构建器测试"""
    
    @pytest.fixture
    def mock_base_builder(self) -> Mock:
        """模拟基础构建器"""
        return Mock()
    
    @pytest.fixture
    def builder(self, mock_base_builder: Mock) -> AsyncGraphBuilder:
        """创建异步图构建器实例"""
        return AsyncGraphBuilder(mock_base_builder)
    
    @pytest.fixture
    def sample_config(self) -> Mock:
        """示例配置"""
        config = Mock(spec=GraphConfig)
        return config
    
    def test_build_graph(self, builder: AsyncGraphBuilder, mock_base_builder: Mock, sample_config: Mock) -> None:
        """测试构建图"""
        # 配置模拟
        mock_graph = Mock()
        mock_base_builder.build_graph.return_value = mock_graph
        
        # 执行
        result = builder.build_graph(sample_config)
        
        # 验证
        assert result == mock_graph
        mock_base_builder.build_graph.assert_called_once_with(sample_config)
    
    def test_build_async_workflow_executor(self, builder: AsyncGraphBuilder) -> None:
        """测试构建异步工作流执行器"""
        # 执行
        result = builder.build_async_workflow_executor()
        
        # 验证
        assert isinstance(result, AsyncWorkflowExecutor)
        assert isinstance(result.node_executor, AsyncNodeExecutor)
    
    def test_build_async_node_executor(self, builder: AsyncGraphBuilder) -> None:
        """测试构建异步节点执行器"""
        # 执行
        result = builder.build_async_node_executor()
        
        # 验证
        assert isinstance(result, AsyncNodeExecutor)