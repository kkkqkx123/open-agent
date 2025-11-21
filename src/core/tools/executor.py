"""改进的工具执行器实现

移除不必要的异步包装，提供真正的异步执行能力。
"""

import asyncio
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from src.interfaces import ILogger
from src.interfaces.tools import ITool, ToolCall, ToolResult
from core.common.async_tuils import AsyncLock, AsyncContextManager


class IToolExecutor(ABC):
    """工具执行器接口"""
    
    @abstractmethod
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass
    
    @abstractmethod
    async def execute_async(self, tool_call: ToolCall) -> ToolResult:
        """异步执行工具调用"""
        pass
    
    @abstractmethod
    def execute_parallel(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行多个工具调用"""
        pass
    
    @abstractmethod
    async def execute_parallel_async(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
        """异步并行执行多个工具调用"""
        pass

logger = logging.getLogger(__name__)


class ConcurrencyLimiter:
    """并发限制器
    
    控制同时执行的工具数量，避免资源耗尽。
    """
    
    def __init__(self, max_concurrent: int = 10):
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_tasks = 0
        self._lock = AsyncLock()
    
    async def execute_with_limit(self, coro: Callable, *args, **kwargs):
        """在并发限制下执行协程"""
        async with self.semaphore:
            async with self._lock:
                self.active_tasks += 1
                logger.debug(f"Active tasks: {self.active_tasks}")
            
            try:
                return await coro(*args, **kwargs)
            finally:
                async with self._lock:
                    self.active_tasks -= 1
                    logger.debug(f"Active tasks: {self.active_tasks}")


class AsyncBatchProcessor:
    """异步批处理器
    
    将多个工具调用批量处理，提高效率。
    """
    
    def __init__(self, batch_size: int = 10, timeout: float = 1.0):
        self.batch_size = batch_size
        self.timeout = timeout
        self.queue = asyncio.Queue()
        self.results = {}
        self.processing = False
    
    async def add_request(self, request_id: str, coro):
        """添加请求到批处理队列"""
        await self.queue.put((request_id, coro))
    
    async def process_batch(self) -> Dict[str, Any]:
        """处理一批请求"""
        batch = []
        
        # 收集批次
        while len(batch) < self.batch_size:
            try:
                item = await asyncio.wait_for(self.queue.get(), timeout=self.timeout)
                batch.append(item)
            except asyncio.TimeoutError:
                break
        
        if not batch:
            return {}
        
        # 批量执行
        logger.debug(f"Processing batch of {len(batch)} requests")
        tasks = [coro for _, coro in batch]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 存储结果
        batch_results = {}
        for (request_id, _), result in zip(batch, results):
            if isinstance(result, Exception):
                batch_results[request_id] = ToolResult(
                    success=False,
                    error=str(result),
                    tool_name=request_id
                )
            else:
                batch_results[request_id] = result
        
        return batch_results


class AsyncToolExecutor(IToolExecutor, AsyncContextManager):
    """改进的异步工具执行器
    
    提供真正的异步执行能力，移除不必要的同步包装。
    """
    
    def __init__(
        self,
        tool_manager: Any,  # IToolManager
        logger: ILogger,
        default_timeout: int = 30,
        max_workers: int = 4,
        max_concurrent: int = 10,
        batch_size: int = 10,
    ):
        """初始化改进的工具执行器
        
        Args:
            tool_manager: 工具管理器
            logger: 日志记录器
            default_timeout: 默认超时时间（秒）
            max_workers: 最大并行工作线程数（仅用于同步工具）
            max_concurrent: 最大并发数
            batch_size: 批处理大小
        """
        self.tool_manager = tool_manager
        self.logger = logger
        self.default_timeout = default_timeout
        self.max_workers = max_workers
        
        # 异步组件
        self.concurrency_limiter = ConcurrencyLimiter(max_concurrent)
        self.batch_processor = AsyncBatchProcessor(batch_size)
        
        # 线程池（仅用于同步工具）
        self._thread_pool: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = AsyncLock()
        
        logger.info(f"AsyncToolExecutor initialized with max_concurrent={max_concurrent}")
    
    async def _get_thread_pool(self) -> ThreadPoolExecutor:
        """获取线程池"""
        return self._thread_pool
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """同步执行工具调用
        
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
                    success=True, output=output, tool_name=tool_call.name
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
    
    async def _execute_tool_with_timeout(
        self, 
        tool: ITool, 
        tool_call: ToolCall, 
        timeout: int
    ) -> ToolResult:
        """带超时的工具执行"""
        try:
            # 同步工具在线程池中执行
            thread_pool = await self._get_thread_pool()
            loop = asyncio.get_running_loop()
            
            output = await asyncio.wait_for(
                loop.run_in_executor(
                    thread_pool,
                    lambda: tool.execute(**tool_call.arguments)
                ),
                timeout=timeout
            )
            return ToolResult(
                success=True,
                output=output,
                tool_name=tool_call.name
            )
                
        except asyncio.TimeoutError:
            raise ValueError(f"工具执行超时: {timeout}秒")
    
    def execute_parallel(
        self,
        tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """同步并行执行多个工具调用
        
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
    
    async def execute_batch(
        self, 
        tool_calls: List[ToolCall]
    ) -> List[ToolResult]:
        """批量执行工具调用
        
        Args:
            tool_calls: 工具调用请求列表
            
        Returns:
            List[ToolResult]: 执行结果列表
        """
        if not tool_calls:
            return []
        
        self.logger.info(f"开始批量执行 {len(tool_calls)} 个工具调用")
        
        # 添加所有请求到批处理器
        request_ids = []
        for i, tool_call in enumerate(tool_calls):
            request_id = f"{tool_call.name}_{i}"
            request_ids.append(request_id)
            await self.batch_processor.add_request(request_id, self.execute(tool_call))
        
        # 处理批次
        batch_results = await self.batch_processor.process_batch()
        
        # 按原始顺序返回结果
        ordered_results = []
        for request_id in request_ids:
            if request_id in batch_results:
                ordered_results.append(batch_results[request_id])
            else:
                # 如果结果丢失，创建错误结果
                ordered_results.append(
                    ToolResult(
                        success=False,
                        error="批处理结果丢失",
                        tool_name=request_id.split('_')[0]
                    )
                )
        
        return ordered_results
    
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
            
            # 检查工具是否支持异步执行
            if hasattr(tool, "execute_async"):
                # 使用工具的异步执行方法
                result = await tool.execute_async(**tool_call.arguments)
                execution_time = time.time() - start_time
                tool_result = ToolResult(
                    success=True,
                    output=result,
                    tool_name=tool_call.name,
                    execution_time=execution_time
                )
            else:
                # 对于同步工具，使用并发限制器在线程池中执行
                tool_result = await self.concurrency_limiter.execute_with_limit(
                    self._execute_tool_with_timeout, tool, tool_call, timeout
                )
                tool_result.execution_time = time.time() - start_time
            
            # 记录调用完成
            if tool_result.success:
                self.logger.info(
                    f"异步工具执行成功: {tool_call.name}, 耗时: {tool_result.execution_time:.2f}秒"
                )
            else:
                self.logger.error(
                    f"异步工具执行失败: {tool_call.name}, 错误: {tool_result.error}"
                )
            
            return tool_result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"异步工具执行异常: {str(e)}"
            self.logger.error(f"异步工具执行异常: {tool_call.name}, 错误: {error_msg}")
            
            return ToolResult(
                success=False,
                error=error_msg,
                tool_name=tool_call.name,
                execution_time=execution_time,
            )
    
    async def execute_parallel_async(self, tool_calls: List[ToolCall]) -> List[ToolResult]:
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
        
        # 创建异步任务列表
        tasks = [self.execute_async(tool_call) for tool_call in tool_calls]
        
        # 并行执行所有任务
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_msg = f"异步并行执行异常: {str(result)}"
                self.logger.error(
                    f"工具异步并行执行异常: {tool_calls[i].name}, 错误: {error_msg}"
                )
                processed_results.append(
                    ToolResult(
                        success=False,
                        error=error_msg,
                        tool_name=tool_calls[i].name
                    )
                )
            else:
                processed_results.append(result)
        
        total_time = time.time() - start_time
        self.logger.info(f"异步并行执行完成，总耗时: {total_time:.2f}秒")
        
        return processed_results
    
    async def cleanup(self):
        """清理资源"""
        if self._thread_pool:
            self._thread_pool.shutdown(wait=True)
            self.logger.info("线程池已关闭")