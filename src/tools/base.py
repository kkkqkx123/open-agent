"""
工具基类实现

定义了所有工具类型的基础抽象类，提供通用的工具接口和功能。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union, Tuple
import asyncio
import time
import json

from .interfaces import ToolResult


class BaseTool(ABC):
    """工具基类

    所有工具类型的基础抽象类，定义了工具的基本接口和通用功能。
    """

    def __init__(self, name: str, description: str, parameters_schema: Dict[str, Any]):
        """初始化工具

        Args:
            name: 工具名称
            description: 工具描述
            parameters_schema: 参数JSON Schema
        """
        self.name = name
        self.description = description
        self.parameters_schema = parameters_schema

    @abstractmethod
    def execute(self, **kwargs: Any) -> Any:
        """同步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        pass

    @abstractmethod
    async def execute_async(self, **kwargs: Any) -> Any:
        """异步执行工具

        Args:
            **kwargs: 工具参数

        Returns:
            Any: 执行结果
        """
        pass

    def get_schema(self) -> Dict[str, Any]:
        """获取工具Schema

        Returns:
            Dict[str, Any]: 工具参数Schema
        """
        return self.parameters_schema

    def validate_parameters(self, parameters: Dict[str, Any]) -> None:
        """验证参数

        Args:
            parameters: 待验证的参数

        Raises:
            ValueError: 参数验证失败
        """
        # 基础参数验证逻辑
        required_params = self.parameters_schema.get("required", [])

        # 检查必需参数
        for param in required_params:
            if param not in parameters:
                raise ValueError(f"缺少必需参数: {param}")

        # 检查参数类型
        properties = self.parameters_schema.get("properties", {})
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
            "parameters": self.parameters_schema,
        }

    def __str__(self) -> str:
        """字符串表示"""
        return f"{self.name}: {self.description}"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)
