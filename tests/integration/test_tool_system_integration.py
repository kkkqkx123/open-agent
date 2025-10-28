"""
工具系统集成测试

测试工具系统各组件之间的集成。
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from src.infrastructure.tools.manager import ToolManager
from src.infrastructure.tools.executor import ToolExecutor
from src.infrastructure.tools.formatter import ToolFormatter
from src.domain.tools.interfaces import ToolCall, ToolResult
from src.infrastructure.tools.config import BuiltinToolConfig
from src.domain.tools.types.builtin_tool import BuiltinTool
from src.domain.tools.base import BaseTool


class TestToolSystemIntegration:
    """工具系统集成测试类"""

    def setup_method(self):
        """测试前设置"""
        self.mock_config_loader = Mock()
        self.mock_logger = Mock()

        # 创建工具管理器
        self.tool_manager = ToolManager(self.mock_config_loader, self.mock_logger)
        
        # 模拟工具管理器的行为，避免加载配置文件
        self.tool_manager._loaded = True

        # 创建工具执行器
        self.tool_executor = ToolExecutor(self.tool_manager, self.mock_logger)

        # 创建工具格式化器
        self.tool_formatter = ToolFormatter()

        # 创建测试工具
        def test_function(param1: str, param2: int = 10):
            """测试函数"""
            return f"结果: {param1}, {param2}"

        self.test_tool = BuiltinTool(
            test_function,
            BuiltinToolConfig(
                name="test_tool",
                tool_type="builtin",
                description="测试工具",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "param1": {"type": "string"},
                        "param2": {"type": "integer", "default": 10},
                    },
                    "required": ["param1"],
                },
            ),
        )

        # 注册测试工具
        self.tool_manager.register_tool(self.test_tool)
        
        # 模拟get_tool方法的行为
        def mock_get_tool(name: str):
            if name == "test_tool":
                return self.test_tool
            elif name == "slow_tool":
                return self.slow_tool if hasattr(self, 'slow_tool') else self.test_tool
            else:
                raise ValueError(f"工具不存在: {name}")
        
        self.tool_manager.get_tool = Mock(side_effect=mock_get_tool)

    def test_end_to_end_workflow(self):
        """测试端到端工作流"""
        # 1. 格式化工具
        tools: list[BaseTool] = [self.test_tool]  # type: ignore
        formatted = self.tool_formatter.format_for_llm(tools)

        assert "functions" in formatted
        assert len(formatted["functions"]) == 1
        assert formatted["functions"][0]["name"] == "test_tool"

        # 2. 创建工具调用
        tool_call = ToolCall(
            name="test_tool", arguments={"param1": "test_value", "param2": 20}
        )

        # 3. 执行工具
        result = self.tool_executor.execute(tool_call)

        assert result.success is True
        assert result.output is not None and "结果: test_value, 20" in result.output
        assert result.tool_name == "test_tool"
        assert result.execution_time is not None

    async def test_async_end_to_end_workflow(self):
        """测试异步端到端工作流"""
        # 1. 格式化工具
        tools: list[BaseTool] = [self.test_tool]  # type: ignore
        formatted = self.tool_formatter.format_for_llm(tools)

        assert "functions" in formatted

        # 2. 创建工具调用
        tool_call = ToolCall(
            name="test_tool", arguments={"param1": "async_test", "param2": 30}
        )

        # 3. 异步执行工具
        result = await self.tool_executor.execute_async(tool_call)

        assert result.success is True
        assert result.output is not None and "结果: async_test, 30" in result.output
        assert result.tool_name == "test_tool"
        assert result.execution_time is not None

    def test_parallel_execution(self):
        """测试并行执行"""
        # 创建多个工具调用
        tool_calls = [
            ToolCall(name="test_tool", arguments={"param1": f"test_{i}", "param2": i})
            for i in range(5)
        ]

        # 并行执行
        results = self.tool_executor.execute_parallel(tool_calls)

        assert len(results) == 5
        # 验证所有结果都成功
        for result in results:
            assert result.success is True
            assert result.output is not None
            assert result.tool_name == "test_tool"
        
        # 验证每个期望的结果都存在
        expected_outputs = [f"结果: test_{i}, {i}" for i in range(5)]
        actual_outputs = [result.output for result in results if result.output]
        for expected_output in expected_outputs:
            found = any(expected_output in actual_output for actual_output in actual_outputs)
            assert found, f"Expected output '{expected_output}' not found in results. Actual outputs: {actual_outputs}"

    async def test_async_parallel_execution(self):
        """测试异步并行执行"""
        # 创建多个工具调用
        tool_calls = [
            ToolCall(
                name="test_tool", arguments={"param1": f"async_test_{i}", "param2": i}
            )
            for i in range(5)
        ]

        # 异步并行执行
        results = await self.tool_executor.execute_parallel_async(tool_calls)

        assert len(results) == 5
        for i, result in enumerate(results):
            assert result.success is True
            assert (
                result.output is not None
                and f"结果: async_test_{i}, {i}" in result.output
            )
            assert result.tool_name == "test_tool"

    def test_error_handling(self):
        """测试错误处理"""
        # 创建无效的工具调用（缺少必需参数）
        tool_call = ToolCall(name="test_tool", arguments={"param2": 20})  # 缺少param1

        # 执行工具
        result = self.tool_executor.execute(tool_call)

        assert result.success is False
        assert result.error is not None and "缺少必需参数" in result.error
        assert result.tool_name == "test_tool"

    def test_tool_not_found(self):
        """测试工具不存在的情况"""
        # 创建不存在的工具调用
        tool_call = ToolCall(name="nonexistent_tool", arguments={"param1": "test"})

        # 执行工具
        result = self.tool_executor.execute(tool_call)

        assert result.success is False
        assert result.error is not None and "工具不存在" in result.error

    def test_validation_before_execution(self):
        """测试执行前验证"""
        # 创建有效的工具调用
        valid_call = ToolCall(
            name="test_tool", arguments={"param1": "test", "param2": 20}
        )

        # 创建无效的工具调用
        invalid_call = ToolCall(
            name="test_tool", arguments={"param2": 20}  # 缺少param1
        )

        # 测试有效调用
        result = self.tool_executor.execute_with_validation(valid_call)
        assert result.success is True

        # 测试无效调用
        result = self.tool_executor.execute_with_validation(invalid_call)
        assert result.success is False
        assert result.error is not None and "工具调用验证失败" in result.error

    async def test_async_validation_before_execution(self):
        """测试异步执行前验证"""
        # 创建有效的工具调用
        valid_call = ToolCall(
            name="test_tool", arguments={"param1": "async_test", "param2": 30}
        )

        # 创建无效的工具调用
        invalid_call = ToolCall(
            name="test_tool", arguments={"param2": 30}  # 缺少param1
        )

        # 测试有效调用
        result = await self.tool_executor.execute_async_with_validation(valid_call)
        assert result.success is True

        # 测试无效调用
        result = await self.tool_executor.execute_async_with_validation(invalid_call)
        assert result.success is False
        assert result.error is not None and "工具调用验证失败" in result.error

    def test_parallel_execution_with_validation(self):
        """测试带验证的并行执行"""
        # 创建混合的工具调用（有效和无效）
        tool_calls = [
            ToolCall(name="test_tool", arguments={"param1": f"test_{i}", "param2": i})
            for i in range(3)
        ]

        # 添加无效调用
        tool_calls.append(
            ToolCall(name="test_tool", arguments={"param2": 99})
        )  # 缺少param1

        # 并行执行
        results = self.tool_executor.execute_parallel_with_validation(tool_calls)

        assert len(results) == 4

        # 前3个应该成功
        for i in range(3):
            assert results[i].success is True

        # 最后一个应该失败
        assert results[3].success is False
        assert results[3].error is not None and "工具调用验证失败" in results[3].error

    async def test_async_parallel_execution_with_validation(self):
        """测试带验证的异步并行执行"""
        # 创建混合的工具调用（有效和无效）
        tool_calls = [
            ToolCall(
                name="test_tool", arguments={"param1": f"async_test_{i}", "param2": i}
            )
            for i in range(3)
        ]

        # 添加无效调用
        tool_calls.append(
            ToolCall(name="test_tool", arguments={"param2": 99})
        )  # 缺少param1

        # 异步并行执行
        results = await self.tool_executor.execute_parallel_async_with_validation(
            tool_calls
        )

        assert len(results) == 4

        # 前3个应该成功
        for i in range(3):
            assert results[i].success is True

        # 最后一个应该失败
        assert results[3].success is False
        assert results[3].error is not None and "工具调用验证失败" in results[3].error

    def test_formatter_strategy_detection(self):
        """测试格式化策略检测"""
        # 模拟LLM客户端
        mock_llm_client = Mock()
        mock_llm_client.get_model_info.return_value = {"name": "gpt-4"}

        # 检测策略
        strategy = self.tool_formatter.detect_strategy(mock_llm_client)
        assert strategy == "function_calling"

        # 测试其他模型
        mock_llm_client.get_model_info.return_value = {"name": "unknown-model"}
        strategy = self.tool_formatter.detect_strategy(mock_llm_client)
        assert strategy == "structured_output"

    def test_timeout_handling(self):
        """测试超时处理"""

        # 创建一个会超时的工具
        async def slow_function(param1: str):
            # 使用单个长时间的sleep，这样asyncio.wait_for可以正确中断
            await asyncio.sleep(2)  # 2秒的睡眠，应该被0.01秒超时中断
            return f"慢速结果: {param1}"

        self.slow_tool = BuiltinTool(
            slow_function,
            BuiltinToolConfig(
                name="slow_tool",
                tool_type="builtin",
                description="慢速工具",
                parameters_schema={
                    "type": "object",
                    "properties": {"param1": {"type": "string"}},
                    "required": ["param1"],
                },
            ),
        )

        # 注册慢速工具
        self.tool_manager.register_tool(self.slow_tool)

        # 更新Mock以支持slow_tool
        def mock_get_tool(name: str):
            if name == "test_tool":
                return self.test_tool
            elif name == "slow_tool":
                return self.slow_tool
            else:
                raise ValueError(f"工具不存在: {name}")
        
        self.tool_manager.get_tool = Mock(side_effect=mock_get_tool)

        # 创建短超时的执行器
        short_timeout_executor = ToolExecutor(
            self.tool_manager, self.mock_logger, default_timeout=1  # 1秒超时
        )

        # 创建工具调用
        tool_call = ToolCall(name="slow_tool", arguments={"param1": "test"})

        # 执行工具（应该超时）
        async def test_timeout():
            print(f"开始执行超时测试，超时时间: {short_timeout_executor.default_timeout}秒")
            print(f"工具是否有safe_execute_async方法: {hasattr(self.slow_tool, 'safe_execute_async')}")
            print(f"工具是否有execute_async方法: {hasattr(self.slow_tool, 'execute_async')}")
            result = await short_timeout_executor.execute_async(tool_call)
            print(f"执行结果: {result}")
            assert result.success is False
            assert result.error is not None and ("超时" in result.error or "timeout" in result.error.lower())

        # 运行异步测试
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_timeout())
        finally:
            loop.close()
