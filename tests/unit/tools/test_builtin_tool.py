"""
BuiltinTool单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, patch

from src.tools.types.builtin_tool import BuiltinTool
from src.tools.config import BuiltinToolConfig


class TestBuiltinTool:
    """BuiltinTool测试类"""

    def test_sync_function_tool(self):
        """测试同步函数工具"""

        def test_function(param1: str, param2: int = 10):
            """测试函数"""
            return f"结果: {param1}, {param2}"

        config = BuiltinToolConfig(
            name="sync_tool",
            tool_type="builtin",
            description="同步工具测试",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
                "required": ["param1"],
            },
        )

        tool = BuiltinTool(test_function, config)

        # 测试基本属性
        assert tool.name == "sync_tool"
        assert tool.description == "同步工具测试"
        assert tool.is_async is False

        # 测试同步执行
        result = tool.execute(param1="test", param2=20)
        assert result == "结果: test, 20"

        # 测试异步执行（同步函数的异步包装）
        async def test_async():
            result = await tool.execute_async(param1="test", param2=20)
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_async())
            assert result == "结果: test, 20"
        finally:
            loop.close()

    def test_async_function_tool(self):
        """测试异步函数工具"""

        async def async_test_function(param1: str, param2: int = 10):
            """异步测试函数"""
            await asyncio.sleep(0.01)  # 模拟异步操作
            return f"异步结果: {param1}, {param2}"

        config = BuiltinToolConfig(
            name="async_tool",
            tool_type="builtin",
            description="异步工具测试",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
                "required": ["param1"],
            },
        )

        tool = BuiltinTool(async_test_function, config)

        # 测试基本属性
        assert tool.name == "async_tool"
        assert tool.description == "异步工具测试"
        assert tool.is_async is True

        # 测试同步执行（异步函数的同步包装）
        result = tool.execute(param1="test", param2=20)
        assert result == "异步结果: test, 20"

        # 测试异步执行
        async def test_async():
            result = await tool.execute_async(param1="test", param2=20)
            return result

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(test_async())
            assert result == "异步结果: test, 20"
        finally:
            loop.close()

    def test_infer_schema(self):
        """测试Schema推断"""

        def test_function(param1: str, param2: int = 10, param3: bool = True):
            """测试函数"""
            pass

        config = BuiltinToolConfig(
            name="schema_test",
            tool_type="builtin",
            description="Schema测试",
            parameters_schema={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                    "param3": {"type": "boolean"},
                },
                "required": ["param1", "param2", "param3"],
            },
        )

        tool = BuiltinTool(test_function, config)
        schema = tool.parameters_schema

        # 验证推断的Schema
        assert schema["type"] == "object"
        assert "param1" in schema["properties"]
        assert "param2" in schema["properties"]
        assert "param3" in schema["properties"]

        assert schema["properties"]["param1"]["type"] == "string"
        assert schema["properties"]["param2"]["type"] == "integer"
        assert schema["properties"]["param3"]["type"] == "boolean"

        assert "param1" in schema["required"]
        assert "param2" not in schema["required"]  # 有默认值
        assert "param3" not in schema["required"]  # 有默认值

    def test_from_function(self):
        """测试从函数创建工具"""

        def test_function(param1: str):
            """测试函数"""
            return f"结果: {param1}"

        tool = BuiltinTool.from_function(
            test_function, name="from_func_tool", description="从函数创建的工具"
        )

        assert tool.name == "from_func_tool"
        assert tool.description == "从函数创建的工具"
        assert tool.func == test_function

    def test_create_tool_decorator(self):
        """测试工具装饰器"""
        schema = {
            "type": "object",
            "properties": {"param1": {"type": "string"}},
            "required": ["param1"],
        }

        @BuiltinTool.create_tool(
            name="decorator_tool", description="装饰器工具", parameters_schema=schema
        )
        def decorated_function(param1: str):
            """装饰器函数"""
            return f"装饰结果: {param1}"

        # 检查函数属性
        assert hasattr(decorated_function, "_tool")
        tool = getattr(decorated_function, "_tool")

        assert tool.name == "decorator_tool"
        assert tool.description == "装饰器工具"
        assert tool.parameters_schema == schema

        # 测试函数仍然可以正常调用
        result = decorated_function("test")
        assert result == "装饰结果: test"

    def test_get_function(self):
        """测试获取原始函数"""

        def test_function(param1: str):
            return f"结果: {param1}"

        config = BuiltinToolConfig(
            name="test_tool",
            tool_type="builtin",
            description="测试工具",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        tool = BuiltinTool(test_function, config)
        assert tool.get_function() == test_function

    def test_is_async_function(self):
        """测试检查是否为异步函数"""

        def sync_function(param1: str):
            return f"同步结果: {param1}"

        async def async_function(param1: str):
            return f"异步结果: {param1}"

        sync_config = BuiltinToolConfig(
            name="sync_tool",
            tool_type="builtin",
            description="同步工具",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        async_config = BuiltinToolConfig(
            name="async_tool",
            tool_type="builtin",
            description="异步工具",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        sync_tool = BuiltinTool(sync_function, sync_config)
        async_tool = BuiltinTool(async_function, async_config)

        assert sync_tool.is_async_function() is False
        assert async_tool.is_async_function() is True

    def test_function_with_self_parameter(self):
        """测试包含self参数的函数（方法）"""

        class TestClass:
            def method_function(self, param1: str):
                """方法函数"""
                return f"方法结果: {param1}"

        obj = TestClass()
        config = BuiltinToolConfig(
            name="method_tool",
            tool_type="builtin",
            description="方法工具",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        tool = BuiltinTool(obj.method_function, config)
        schema = tool.parameters_schema

        # self参数应该被跳过
        assert "param1" in schema["properties"]
        assert "self" not in schema["properties"]

    def test_function_exception_handling(self):
        """测试函数异常处理"""

        def error_function(param1: str):
            raise ValueError("测试错误")

        config = BuiltinToolConfig(
            name="error_tool",
            tool_type="builtin",
            description="错误工具",
            parameters_schema={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        tool = BuiltinTool(error_function, config)

        # 测试同步执行异常
        with pytest.raises(ValueError, match="内置工具执行错误"):
            tool.execute(param1="test")

        # 测试异步执行异常
        async def test_async():
            with pytest.raises(ValueError, match="内置工具异步执行错误"):
                await tool.execute_async(param1="test")

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(test_async())
        finally:
            loop.close()
