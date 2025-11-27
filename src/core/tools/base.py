"""
工具基类实现

定义了所有工具类型的基础抽象类，提供通用的工具接口和功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple
import asyncio
import time
import json

from src.interfaces.tool.base import ITool, ToolResult


class BaseTool(ITool, ABC):
    """工具基类 - 支持同步和异步两种执行模式
    
    设计原则：
    1. 子类必须实现 execute() 或 execute_async() 之一（或都实现）
    2. 同步工具：只实现 execute()，异步调用通过线程池包装
    3. 异步工具：优先实现 execute_async()，同步调用通过新事件循环包装（仅在必要时）
    4. 双模工具：都实现，同步快速路径不依赖异步
    """

    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters_schema: 参数JSON Schema
        """
        self._name = name
        self._description = description
        self._parameters_schema = parameters_schema

    @property
    def name(self) -> str:
        """工具名称"""
        return self._name

    @property
    def description(self) -> str:
        """工具描述"""
        return self._description

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """参数Schema"""
        return self._parameters_schema

    @parameters_schema.setter
    def parameters_schema(self, value: Dict[str, Any]) -> None:
        """设置参数Schema"""
        self._parameters_schema = value

    # ==================== 执行接口 ====================
    
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具
        
        默认实现：在新事件循环中运行 execute_async()（用于纯异步工具）
        
        子类实现选项：
        1. 重写此方法为同步实现（推荐用于本地快速工具）
        2. 不重写，使用默认异步包装（I/O密集工具）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
            
        Raises:
            RuntimeError: 在嵌套事件循环中调用
        """
        # 检查是否已有运行中的事件循环（避免嵌套）
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                f"工具 {self.name} 不支持在异步上下文中同步调用。"
                "请使用 execute_async() 或在线程池中执行。"
            )
        except RuntimeError as e:
            if "no running event loop" not in str(e).lower():
                raise
        
        # 创建新事件循环执行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.execute_async(**kwargs))
        finally:
            loop.close()

    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具
        
        默认实现：在线程池中运行 execute()（用于纯同步工具）
        
        子类实现选项：
        1. 重写此方法为异步实现（推荐用于I/O密集工具）
        2. 不重写，使用默认线程池包装（同步工具保持兼容）
        
        Args:
            **kwargs: 工具参数
            
        Returns:
            Any: 执行结果
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: self.execute(**kwargs))

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema

        Returns:
            Dict[str, Any]: 工具参数Schema
        """
        return self._parameters_schema

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数

        Args:
            parameters: 待验证的参数

        Returns:
            bool: 验证是否成功
            
        Raises:
            ValueError: 参数验证失败
        """
        try:
            # 基础参数验证逻辑
            required_params = self._parameters_schema.get("required", [])

            # 检查必需参数
            for param in required_params:
                if param not in parameters:
                    raise ValueError(f"缺少必需参数: {param}")

            # 检查参数类型
            properties = self._parameters_schema.get("properties", {})
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    param_schema = properties[param_name]
                    expected_type = param_schema.get("type")

                    if expected_type == "string" and not isinstance(param_value, str):
                        raise ValueError(f"参数 {param_name} 应为字符串类型")
                    elif expected_type == "number" and not isinstance(
                        param_value, (int, float)
                    ):
                        raise ValueError(f"参数 {param_name} 应为数字类型")
                    elif expected_type == "integer" and not isinstance(param_value, int):
                        raise ValueError(f"参数 {param_name} 应为整数类型")
                    elif expected_type == "boolean" and not isinstance(param_value, bool):
                        raise ValueError(f"参数 {param_name} 应为布尔类型")
                    elif expected_type == "array" and not isinstance(param_value, list):
                        raise ValueError(f"参数 {param_name} 应为数组类型")
                    elif expected_type == "object" and not isinstance(param_value, dict):
                        raise ValueError(f"参数 {param_name} 应为对象类型")

            return True
        except ValueError:
            # 重新抛出 ValueError
            raise
        except Exception as e:
            raise ValueError(f"参数验证失败: {str(e)}")

    def initialize_context(self, session_id: Optional[str] = None) -> Optional[str]:
        """初始化工具上下文（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法为空实现。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return session_id

    def cleanup_context(self) -> bool:
        """清理工具上下文（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法为空实现。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return True

    def get_context_info(self) -> Optional[Dict[str, Any]]:
        """获取上下文信息（默认实现）
        
        对于无状态工具（如BuiltinTool），此方法返回None。
        有状态工具（如StatefulBaseTool）会重写此方法。
        """
        return None

    def _create_result(
        self,
        success: bool,
        output: Any = None,
        error: Optional[str] = None,
        execution_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ToolResult:
        """创建工具执行结果

        Args:
            success: 是否成功
            output: 输出结果
            error: 错误信息
            execution_time: 执行时间
            metadata: 元数据

        Returns:
            ToolResult: 执行结果
        """
        return ToolResult(
            success=success,
            output=output,
            error=error,
            tool_name=self.name,
            execution_time=execution_time,
            metadata=metadata,
        )

    def _measure_execution_time(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量函数执行时间

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            tuple: (执行结果, 执行时间)
        """
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            raise e

    async def _measure_execution_time_async(self, func: Any, *args: Any, **kwargs: Any) -> Tuple[Any, float]:
        """测量异步函数执行时间

        Args:
            func: 要执行的异步函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            tuple: (执行结果, 执行时间)
        """
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            return result, execution_time
        except Exception as e:
            execution_time = time.time() - start_time
            raise e

    def safe_execute(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（同步）

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 验证参数
            self.validate_parameters(kwargs)

            # 执行并测量时间
            result, execution_time = self._measure_execution_time(
                self.execute, **kwargs
            )

            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))

    async def safe_execute_async(self, **kwargs: Any) -> ToolResult:
        """安全执行工具（异步）

        Args:
            **kwargs: 工具参数

        Returns:
            ToolResult: 执行结果
        """
        try:
            # 验证参数
            self.validate_parameters(kwargs)

            # 执行并测量时间
            result, execution_time = await self._measure_execution_time_async(
                self.execute_async, **kwargs
            )

            return self._create_result(
                success=True, output=result, execution_time=execution_time
            )
        except Exception as e:
            return self._create_result(success=False, error=str(e))

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式

        Returns:
            Dict[str, Any]: 工具信息字典
        """
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._parameters_schema,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)