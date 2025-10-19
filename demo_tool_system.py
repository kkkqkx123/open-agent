#!/usr/bin/env python3
"""
工具系统演示脚本

演示工具系统的基本功能，包括工具加载、执行和格式化。
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.infrastructure import TestContainer
from src.tools.interfaces import ToolCall
from src.tools.formatter import ToolFormatter
from src.tools.types.builtin_tool import BuiltinTool
from src.tools.config import BuiltinToolConfig


def demo_basic_usage() -> None:
    """演示基本使用"""
    print("=== 工具系统基本使用演示 ===\n")
    
    # 使用测试容器
    with TestContainer() as container:
        # 获取工具管理器
        tool_manager = container.get_tool_manager()
        logger = container.get_logger()
        
        # 创建工具执行器
        from src.tools.executor import ToolExecutor
        executor = ToolExecutor(tool_manager, logger)
        
        # 创建一个简单的内置工具
        def greet(name: str, language: str = "中文") -> str:
            """问候函数"""
            greetings = {
                "中文": f"你好, {name}!",
                "英文": f"Hello, {name}!",
                "日文": f"こんにちは, {name}!"
            }
            return greetings.get(language, f"你好, {name}!")
        
        # 创建工具配置
        config = BuiltinToolConfig(
            name="greet_tool",
            description="多语言问候工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "要问候的名字"},
                    "language": {
                        "type": "string",
                        "description": "语言",
                        "enum": ["中文", "英文", "日文"],
                        "default": "中文"
                    }
                },
                "required": ["name"]
            }
        )
        
        # 创建并注册工具
        greet_tool = BuiltinTool(greet, config)
        tool_manager.register_tool(greet_tool)
        
        # 列出所有工具
        print("可用工具:")
        for tool_name in tool_manager.list_tools():
            print(f"- {tool_name}")
        print()
        
        # 创建工具调用
        tool_call = ToolCall(
            name="greet_tool",
            arguments={"name": "世界", "language": "中文"}
        )
        
        # 执行工具
        print("执行工具调用:")
        result = executor.execute(tool_call)
        
        if result.success:
            print(f"✅ 执行成功: {result.output}")
            print(f"⏱️ 执行时间: {result.execution_time:.4f}秒")
        else:
            print(f"❌ 执行失败: {result.error}")
        
        print()


def demo_parallel_execution() -> None:
    """演示并行执行"""
    print("=== 并行执行演示 ===\n")
    
    with TestContainer() as container:
        tool_manager = container.get_tool_manager()
        logger = container.get_logger()
        
        from src.tools.executor import ToolExecutor
        executor = ToolExecutor(tool_manager, logger)
        
        # 创建一个计算工具
        def calculate(expression: str) -> str:
            """简单计算器"""
            try:
                # 注意：实际应用中应使用安全的表达式解析器
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"计算错误: {str(e)}"
        
        config = BuiltinToolConfig(
            name="calculator",
            description="简单计算器",
            parameters_schema={
                "type": "object",
                "properties": {
                    "expression": {"type": "string", "description": "数学表达式"}
                },
                "required": ["expression"]
            }
        )
        
        calculator_tool = BuiltinTool(calculate, config)
        tool_manager.register_tool(calculator_tool)
        
        # 创建多个工具调用
        expressions = ["2 + 3", "10 * 5", "100 / 4", "2 ** 8", "sqrt(16)"]
        tool_calls = [
            ToolCall(name="calculator", arguments={"expression": expr})
            for expr in expressions
        ]
        
        print(f"并行执行 {len(tool_calls)} 个计算:")
        
        # 并行执行
        results = executor.execute_parallel(tool_calls)
        
        # 显示结果
        for i, (expr, result) in enumerate(zip(expressions, results)):
            if result.success:
                print(f"{i+1}. {expr} = {result.output}")
            else:
                print(f"{i+1}. {expr} = 错误: {result.error}")
        
        print()


async def demo_async_execution() -> None:
    """演示异步执行"""
    print("=== 异步执行演示 ===\n")
    
    with TestContainer() as container:
        tool_manager = container.get_tool_manager()
        logger = container.get_logger()
        
        from src.tools.executor import ToolExecutor
        executor = ToolExecutor(tool_manager, logger)
        
        # 创建一个异步工具
        async def async_fetch_data(url: str, delay: float = 1.0) -> str:
            """模拟异步获取数据"""
            await asyncio.sleep(delay)
            return f"从 {url} 获取的数据 (延迟 {delay}秒)"
        
        config = BuiltinToolConfig(
            name="async_fetch",
            description="异步数据获取工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL"},
                    "delay": {"type": "number", "description": "延迟时间(秒)", "default": 1.0}
                },
                "required": ["url"]
            }
        )
        
        async_tool = BuiltinTool(async_fetch_data, config)
        tool_manager.register_tool(async_tool)
        
        # 创建工具调用
        tool_call = ToolCall(
            name="async_fetch",
            arguments={"url": "https://example.com/api", "delay": 0.5}
        )
        
        print("执行异步工具调用:")
        result = await executor.execute_async(tool_call)
        
        if result.success:
            print(f"✅ 执行成功: {result.output}")
            print(f"⏱️ 执行时间: {result.execution_time:.4f}秒")
        else:
            print(f"❌ 执行失败: {result.error}")
        
        print()


async def demo_async_parallel_execution() -> None:
    """演示异步并行执行"""
    print("=== 异步并行执行演示 ===\n")
    
    with TestContainer() as container:
        tool_manager = container.get_tool_manager()
        logger = container.get_logger()
        
        from src.tools.executor import ToolExecutor
        executor = ToolExecutor(tool_manager, logger)
        
        # 创建一个异步工具
        async def async_process(task_id: int, duration: float) -> str:
            """模拟异步处理任务"""
            await asyncio.sleep(duration)
            return f"任务 {task_id} 完成 (耗时 {duration}秒)"
        
        config = BuiltinToolConfig(
            name="async_process",
            description="异步任务处理工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "integer", "description": "任务ID"},
                    "duration": {"type": "number", "description": "处理时间(秒)"}
                },
                "required": ["task_id", "duration"]
            }
        )
        
        async_tool = BuiltinTool(async_process, config)
        tool_manager.register_tool(async_tool)
        
        # 创建多个工具调用
        tool_calls = [
            ToolCall(name="async_process", arguments={"task_id": i+1, "duration": 0.5})
            for i in range(5)
        ]
        
        print(f"异步并行执行 {len(tool_calls)} 个任务:")
        
        # 异步并行执行
        results = await executor.execute_parallel_async(tool_calls)
        
        # 显示结果
        for result in results:
            if result.success:
                print(f"✅ {result.output}")
            else:
                print(f"❌ 任务失败: {result.error}")
        
        print()


def demo_formatter() -> None:
    """演示工具格式化"""
    print("=== 工具格式化演示 ===\n")
    
    with TestContainer() as container:
        tool_manager = container.get_tool_manager()
        
        # 创建一个示例工具
        def search(query: str, limit: int = 10) -> str:
            """搜索函数"""
            return f"搜索 '{query}' 的前 {limit} 个结果"
        
        config = BuiltinToolConfig(
            name="search",
            description="搜索工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "搜索查询"},
                    "limit": {"type": "integer", "description": "结果数量限制", "default": 10}
                },
                "required": ["query"]
            }
        )
        
        search_tool = BuiltinTool(search, config)
        
        # 创建格式化器
        formatter = ToolFormatter()
        
        # 格式化工具
        tools = [search_tool]
        formatted = formatter.format_for_llm(tools)
        
        print("Function Calling 格式:")
        print(formatted)
        print()
        
        # 模拟LLM响应
        from langchain_core.messages import AIMessage
        mock_response = AIMessage(
            content="",
            additional_kwargs={
                "function_call": {
                    "name": "search",
                    "arguments": '{"query": "Python教程", "limit": 5}'
                }
            }
        )
        
        # 解析响应
        try:
            tool_call = formatter.parse_llm_response(mock_response)
            print("解析的工具调用:")
            print(f"工具名称: {tool_call.name}")
            print(f"参数: {tool_call.arguments}")
        except Exception as e:
            print(f"解析失败: {e}")
        
        print()


def demo_error_handling() -> None:
    """演示错误处理"""
    print("=== 错误处理演示 ===\n")
    
    with TestContainer() as container:
        tool_manager = container.get_tool_manager()
        logger = container.get_logger()
        
        from src.tools.executor import ToolExecutor
        executor = ToolExecutor(tool_manager, logger)
        
        # 创建一个会出错的工具
        def error_function(should_error: bool = False) -> str:
            """可能出错的函数"""
            if should_error:
                raise ValueError("这是一个测试错误")
            return "成功执行"
        
        config = BuiltinToolConfig(
            name="error_tool",
            description="错误测试工具",
            parameters_schema={
                "type": "object",
                "properties": {
                    "should_error": {"type": "boolean", "description": "是否触发错误", "default": False}
                }
            }
        )
        
        error_tool = BuiltinTool(error_function, config)
        tool_manager.register_tool(error_tool)
        
        # 测试成功执行
        print("1. 成功执行:")
        tool_call = ToolCall(name="error_tool", arguments={"should_error": False})
        result = executor.execute(tool_call)
        
        if result.success:
            print(f"✅ {result.output}")
        else:
            print(f"❌ {result.error}")
        
        # 测试错误执行
        print("\n2. 错误执行:")
        tool_call = ToolCall(name="error_tool", arguments={"should_error": True})
        result = executor.execute(tool_call)
        
        if result.success:
            print(f"✅ {result.output}")
        else:
            print(f"❌ {result.error}")
        
        # 测试参数验证错误
        print("\n3. 参数验证错误:")
        tool_call = ToolCall(name="error_tool", arguments={"invalid_param": "value"})
        result = executor.execute_with_validation(tool_call)
        
        if result.success:
            print(f"✅ {result.output}")
        else:
            print(f"❌ {result.error}")
        
        print()


async def main() -> None:
    """主函数"""
    print("🔧 工具系统演示\n")
    
    try:
        # 基本使用演示
        demo_basic_usage()
        
        # 并行执行演示
        demo_parallel_execution()
        
        # 异步执行演示
        await demo_async_execution()
        
        # 异步并行执行演示
        await demo_async_parallel_execution()
        
        # 格式化演示
        demo_formatter()
        
        # 错误处理演示
        demo_error_handling()
        
        print("🎉 所有演示完成!")
        
    except Exception as e:
        print(f"❌ 演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 运行演示
    asyncio.run(main())