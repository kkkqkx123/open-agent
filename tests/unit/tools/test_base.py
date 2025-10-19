"""
BaseTool单元测试
"""

import pytest
from unittest.mock import Mock, patch
import asyncio

from src.tools.base import BaseTool
from src.tools.interfaces import ToolResult


class TestTool(BaseTool):
    """测试工具类"""

    def __init__(self):
        super().__init__(
            name="test_tool",
            description="测试工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer", "default": 10},
                },
                "required": ["param1"],
            },
        )

    def execute(self, **kwargs):
        """同步执行"""
        return f"执行结果: {kwargs}"

    async def execute_async(self, **kwargs):
        """异步执行"""
        return f"异步执行结果: {kwargs}"


class TestBaseTool:
    """BaseTool测试类"""

    def setup_method(self):
        """测试前设置"""
        self.tool = TestTool()

    def test_initialization(self):
        """测试初始化"""
        assert self.tool.name == "test_tool"
        assert self.tool.description == "测试工具"
        assert "param1" in self.tool.parameters_schema["properties"]
        assert "param2" in self.tool.parameters_schema["properties"]
        assert "param1" in self.tool.parameters_schema["required"]

    def test_get_schema(self):
        """测试获取Schema"""
        schema = self.tool.get_schema()
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema

    def test_validate_parameters_success(self):
        """测试参数验证成功"""
        # 有效参数
        self.tool.validate_parameters({"param1": "value1"})

        # 带默认参数
        self.tool.validate_parameters({"param1": "value1", "param2": 20})

    def test_validate_parameters_missing_required(self):
        """测试缺少必需参数"""
        with pytest.raises(ValueError, match="缺少必需参数: param1"):
            self.tool.validate_parameters({})

    def test_validate_parameters_wrong_type(self):
        """测试参数类型错误"""
        with pytest.raises(ValueError, match="参数 param1 应为字符串类型"):
            self.tool.validate_parameters({"param1": 123})

        with pytest.raises(ValueError, match="参数 param2 应为整数类型"):
            self.tool.validate_parameters({"param1": "value1", "param2": "not_int"})

    def test_create_result(self):
        """测试创建结果"""
        result = self.tool._create_result(
            success=True, output="test output", execution_time=1.5
        )

        assert result.success is True
        assert result.output == "test output"
        assert result.execution_time == 1.5
        assert result.tool_name == "test_tool"

    def test_measure_execution_time(self):
        """测试执行时间测量"""

        def test_func():
            return "test result"

        result, execution_time = self.tool._measure_execution_time(test_func)
        assert result == "test result"
        assert execution_time > 0

    async def test_measure_execution_time_async(self):
        """测试异步执行时间测量"""

        async def test_func():
            await asyncio.sleep(0.1)
            return "test result"

        result, execution_time = await self.tool._measure_execution_time_async(
            test_func
        )
        assert result == "test result"
        assert execution_time >= 0.1

    def test_safe_execute_success(self):
        """测试安全执行成功"""
        result = self.tool.safe_execute(param1="value1")
        assert result.success is True
        assert result.output is not None and "执行结果:" in result.output
        assert result.tool_name == "test_tool"
        assert result.execution_time is not None

    def test_safe_execute_validation_error(self):
        """测试安全执行验证错误"""
        result = self.tool.safe_execute()  # 缺少必需参数
        assert result.success is False
        assert result.error is not None and "缺少必需参数" in result.error
        assert result.tool_name == "test_tool"

    async def test_safe_execute_async_success(self):
        """测试异步安全执行成功"""
        result = await self.tool.safe_execute_async(param1="value1")
        assert result.success is True
        assert result.output is not None and "异步执行结果:" in result.output
        assert result.tool_name == "test_tool"
        assert result.execution_time is not None

    async def test_safe_execute_async_validation_error(self):
        """测试异步安全执行验证错误"""
        result = await self.tool.safe_execute_async()  # 缺少必需参数
        assert result.success is False
        assert result.error is not None and "缺少必需参数" in result.error
        assert result.tool_name == "test_tool"

    def test_to_dict(self):
        """测试转换为字典"""
        tool_dict = self.tool.to_dict()
        assert tool_dict["name"] == "test_tool"
        assert tool_dict["description"] == "测试工具"
        assert "parameters" in tool_dict

    def test_str_representation(self):
        """测试字符串表示"""
        str_repr = str(self.tool)
        assert "test_tool" in str_repr
        assert "测试工具" in str_repr

    def test_repr_representation(self):
        """测试详细字符串表示"""
        repr_str = repr(self.tool)
        assert "test_tool" in repr_str
        assert "测试工具" in repr_str


class TestErrorHandling:
    """错误处理测试"""

    def setup_method(self):
        """测试前设置"""
        self.tool = TestTool()

    def test_execute_exception_handling(self):
        """测试执行异常处理"""

        class ErrorTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="error_tool",
                    description="错误工具",
                    parameters_schema={"type": "object", "properties": {}},
                )

            def execute(self, **kwargs):
                raise ValueError("测试错误")

            async def execute_async(self, **kwargs):
                raise ValueError("异步测试错误")

        error_tool = ErrorTool()
        result = error_tool.safe_execute()
        assert result.success is False
        assert result.error is not None and "测试错误" in result.error

    async def test_execute_async_exception_handling(self):
        """测试异步执行异常处理"""

        class ErrorTool(BaseTool):
            def __init__(self):
                super().__init__(
                    name="error_tool",
                    description="错误工具",
                    parameters_schema={"type": "object", "properties": {}},
                )

            def execute(self, **kwargs):
                raise ValueError("测试错误")

            async def execute_async(self, **kwargs):
                raise ValueError("异步测试错误")

        error_tool = ErrorTool()
        result = await error_tool.safe_execute_async()
        assert result.success is False
        assert result.error is not None and "异步测试错误" in result.error
