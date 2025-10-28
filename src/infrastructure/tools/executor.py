"""
工具执行器实现

提供工具的执行功能，支持同步、异步和并行执行，包含安全控制和错误处理。
"""

import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.infrastructure.logger.logger import ILogger
from src.domain.tools.interfaces import IToolExecutor, ITool, ToolCall, ToolResult


class ToolExecutor(IToolExecutor):
    """工具执行器实现

    负责工具的执行，支持同步、异步和并行执行。
    """

    def __init__(
        self,
        tool_manager: Any,  # IToolManager
        logger: ILogger,
        default_timeout: int = 30,
        max_workers: int = 4,
    ):
        """初始化工具执行器

        Args:
            tool_manager: 工具管理器
            logger: 日志记录器
            default_timeout: 默认超时时间（秒）
            max_workers: 最大并行工作线程数
        """
        self.tool_manager = tool_manager
        self.logger = logger
        self.default_timeout = default_timeout
        self.max_workers = max_workers
        self._thread_pool = ThreadPoolExecutor(max_workers=max_workers)

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()

        try:
            # 获取工具实例
            tool = self.tool_manager.get_tool(tool_call.name)

            # 设置超时时间
            timeout = tool_call.timeout or self.default_timeout

            # 记录调用开始
            self.logger.info(f"开始执行工具: {tool_call.name}")

            # 验证参数
            if not tool.validate_parameters(tool_call.arguments):
                return ToolResult(
                    success=False,
                    error="参数验证失败",
                    tool_name=tool_call.name,
                    execution_time=time.time() - start_time
                )

            # 执行工具
            if hasattr(tool, "safe_execute"):
                result = tool.safe_execute(**tool_call.arguments)
            else:
                # 使用工具的execute方法
                output = tool.execute(**tool_call.arguments)
                result = ToolResult(
                    success=True, 
                    output=output, 
                    tool_name=tool_call.name
                )

            # 计算执行时间
            execution_time = time.time() - start_time
            result.execution_time = execution_time

            # 记录调用完成
            if result.success:
                self.logger.info(
                    f"工具执行成功: {tool_call.name}, 耗时: {execution_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"工具执行失败: {tool_call.name}, 错误: {result.error}"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具执行异常: {str(e)}"
            self.logger.error(f"工具执行异常: {tool_call.name}, 错误: {error_msg}")

            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )

    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        start_time = time.time()

        try:
            # 获取工具实例
            tool = self.tool_manager.get_tool(tool_call.name)

            # 设置超时时间
            timeout = tool_call.timeout or self.default_timeout

            # 记录调用开始
            self.logger.info(f"开始异步执行工具: {tool_call.name}")

            # 验证参数
            if not tool.validate_parameters(tool_call.arguments):
                return ToolResult(
                    success=False,
                    error="参数验证失败",
                    tool_name=tool_call.name,
                    execution_time=time.time() - start_time
                )

            # 执行工具，统一应用超时控制
            try:
                if hasattr(tool, "safe_execute_async"):
                    # 对safe_execute_async方法应用超时控制
                    result = await asyncio.wait_for(
                        tool.safe_execute_async(**tool_call.arguments), timeout=timeout
                    )
                else:
                    # 使用工具的execute_async方法
                    output = await asyncio.wait_for(
                        tool.execute_async(**tool_call.arguments), timeout=timeout
                    )
                    result = ToolResult(
                        success=True, output=output, tool_name=tool_call.name
                    )
            except asyncio.TimeoutError:
                raise ValueError(f"工具执行超时: {timeout}秒")

            # 计算执行时间
            execution_time = time.time() - start_time
            result.execution_time = execution_time

            # 记录调用完成
            if result.success:
                self.logger.info(
                    f"工具异步执行成功: {tool_call.name}, 耗时: {execution_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"工具异步执行失败: {tool_call.name}, 错误: {result.error}"
                )

            return result

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具异步执行异常: {str(e)}"
            self.logger.error(f"工具异步执行异常: {tool_call.name}, 错误: {error_msg}")

            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )

    def execute_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行多个工具调用

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        if not tool_calls:
            return []

        self.logger.info(f"开始并行执行 {len(tool_calls)} 个工具调用")
        start_time = time.time()

        # 使用线程池并行执行
        futures = []
        for i, tool_call in enumerate(tool_calls):
            future = self._thread_pool.submit(self.execute, tool_call)
            futures.append((future, i))

        # 收集所有结果
        results: List[ToolResult] = []
        for future, index in futures:
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                error_msg = f"并行执行异常: {str(e)}"
                self.logger.error(
                    f"工具并行执行异常: {tool_calls[index].name}, 错误: {error_msg}"
                )
                results.append(ToolResult(success=False, error=error_msg, tool_name=tool_calls[index].name))

        # 按原始顺序排序结果
        # 使用索引作为键，确保即使有同名工具也能正确处理
        results_dict = {i: result for i, result in enumerate(results)}
        ordered_results = []
        for i, tool_call in enumerate(tool_calls):
            if i in results_dict:
                ordered_results.append(results_dict[i])
            else:
                # 如果结果丢失，创建错误结果
                ordered_results.append(
                    ToolResult(
                        success=False,
                        error="结果丢失",
                        tool_name=tool_call.name
                    )
                )

        total_time = time.time() - start_time
        self.logger.info(f"并行执行完成，总耗时: {total_time:.2f}秒")

        return ordered_results

    async def execute_parallel_async(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """异步并行执行多个工具调用

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        if not tool_calls:
            return []

        self.logger.info(f"开始异步并行执行 {len(tool_calls)} 个工具调用")
        start_time = time.time()

        # 创建异步任务
        tasks = [self.execute_async(tool_call) for tool_call in tool_calls]

        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # 处理异常结果
        processed_results: List[ToolResult] = []
        for i, result in enumerate(results):
            if isinstance(result, BaseException):
                tool_call = tool_calls[i]
                error_msg = f"异步并行执行异常: {str(result)}"
                self.logger.error(
                    f"工具异步并行执行异常: {tool_call.name}, 错误: {error_msg}"
                )

                processed_results.append(
                    ToolResult(success=False, error=error_msg, tool_name=tool_call.name)
                )
            else:
                processed_results.append(result)

        total_time = time.time() - start_time
        self.logger.info(f"异步并行执行完成，总耗时: {total_time:.2f}秒")

        return processed_results

    def validate_tool_call(self, tool_call: ToolCall) -> bool:
        """验证工具调用

        Args:
            tool_call: 工具调用请求

        Returns:
            bool: 是否有效
        """
        try:
            # 检查工具是否存在
            tool = self.tool_manager.get_tool(tool_call.name)

            # 验证参数
            tool.validate_parameters(tool_call.arguments)

            return True
        except Exception as e:
            self.logger.warning(f"工具调用验证失败: {tool_call.name}, 错误: {str(e)}")
            return False

    def execute_with_validation(self, tool_call: ToolCall) -> ToolResult:
        """带验证的工具执行

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        # 验证工具调用
        if not self.validate_tool_call(tool_call):
            return ToolResult(
                success=False, error="工具调用验证失败", tool_name=tool_call.name
            )

        # 执行工具
        return self.execute(tool_call)

    async def execute_async_with_validation(self, tool_call: ToolCall) -> ToolResult:
        """带验证的异步工具执行

        Args:
            tool_call: 工具调用请求

        Returns:
            ToolResult: 执行结果
        """
        # 验证工具调用
        if not self.validate_tool_call(tool_call):
            return ToolResult(
                success=False, error="工具调用验证失败", tool_name=tool_call.name
            )

        # 执行工具
        return await self.execute_async(tool_call)

    def execute_parallel_with_validation(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """带验证的并行工具执行

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        # 过滤有效的工具调用
        valid_calls = []
        invalid_results = []
        # 记录每个调用是有效还是无效
        validation_results = []

        for tool_call in tool_calls:
            is_valid = self.validate_tool_call(tool_call)
            validation_results.append(is_valid)
            if is_valid:
                valid_calls.append(tool_call)
            else:
                invalid_results.append(
                    ToolResult(
                        success=False,
                        error="工具调用验证失败",
                        tool_name=tool_call.name,
                    )
                )

        # 执行有效的工具调用
        valid_results = self.execute_parallel(valid_calls)

        # 按原始顺序合并结果
        ordered_results: List[ToolResult] = []
        valid_index = 0
        invalid_index = 0
        
        for is_valid in validation_results:
            if is_valid:
                if valid_index < len(valid_results):
                    ordered_results.append(valid_results[valid_index])
                    valid_index += 1
            else:
                if invalid_index < len(invalid_results):
                    ordered_results.append(invalid_results[invalid_index])
                    invalid_index += 1
        
        return ordered_results

    async def execute_parallel_async_with_validation(
        self, tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """带验证的异步并行工具执行

        Args:
            tool_calls: 工具调用请求列表

        Returns:
            List[ToolResult]: 执行结果列表
        """
        # 过滤有效的工具调用
        valid_calls = []
        invalid_results = []
        # 记录每个调用是有效还是无效
        validation_results = []

        for tool_call in tool_calls:
            is_valid = self.validate_tool_call(tool_call)
            validation_results.append(is_valid)
            if is_valid:
                valid_calls.append(tool_call)
            else:
                invalid_results.append(
                    ToolResult(
                        success=False,
                        error="工具调用验证失败",
                        tool_name=tool_call.name,
                    )
                )

        # 执行有效的工具调用
        valid_results = await self.execute_parallel_async(valid_calls)

        # 按原始顺序合并结果
        ordered_results: List[ToolResult] = []
        valid_index = 0
        invalid_index = 0
        
        for is_valid in validation_results:
            if is_valid:
                if valid_index < len(valid_results):
                    ordered_results.append(valid_results[valid_index])
                    valid_index += 1
            else:
                if invalid_index < len(invalid_results):
                    ordered_results.append(invalid_results[invalid_index])
                    invalid_index += 1
        
        return ordered_results

    def shutdown(self) -> None:
        """关闭执行器

        清理资源，关闭线程池。
        """
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self.logger.info("工具执行器已关闭")