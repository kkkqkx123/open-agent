"""工作流运行器 - 新架构实现

提供简化的工作流执行接口，自动状态初始化，错误处理和重试机制。
"""

from typing import Dict, Any, Optional, List, Union, Generator, AsyncIterator
from dataclasses import dataclass
from datetime import datetime
import logging
import asyncio

from ..loading.loader_service import UniversalLoaderService
from ..workflow_instance import WorkflowInstance
from src.core.workflow.exceptions import WorkflowExecutionError

logger = logging.getLogger(__name__)


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果"""
    workflow_name: str
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


class WorkflowRunner:
    """工作流运行器 - 新架构实现
    
    提供简化的工作流执行接口，自动状态初始化，错误处理和重试机制。
    """
    
    def __init__(
        self, 
        loader_service: Optional[UniversalLoaderService] = None,
        max_retries: int = 3,
        default_timeout: int = 300
    ):
        """初始化工作流运行器
        
        Args:
            loader_service: 统一加载器服务
            max_retries: 最大重试次数
            default_timeout: 默认超时时间（秒）
        """
        self.loader_service = loader_service or UniversalLoaderService()
        self.max_retries = max_retries
        self.default_timeout = default_timeout
        
        # 执行统计
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
        
        logger.debug("工作流运行器初始化完成")
    
    def run_workflow(
        self, 
        config_path: str, 
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowExecutionResult:
        """运行工作流
        
        Args:
            config_path: 配置文件路径
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 加载工作流
            workflow = self.loader_service.load_from_file(config_path)
            
            # 执行工作流（带重试）
            result = self._execute_with_retry(workflow, initial_data, **kwargs)
            
            # 更新统计
            self._update_stats(True, (datetime.now() - start_time).total_seconds())
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=True,
                result=result,
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "config_path": config_path,
                    "retries_used": kwargs.get("_retry_count", 0)
                }
            )
            
        except Exception as e:
            # 更新统计
            self._update_stats(False, (datetime.now() - start_time).total_seconds())
            
            logger.error(f"工作流执行失败: {config_path}, 错误: {e}")
            
            return WorkflowExecutionResult(
                workflow_name="unknown",
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "config_path": config_path,
                    "error_type": type(e).__name__
                }
            )
    
    def run_workflow_instance(
        self,
        workflow: WorkflowInstance,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowExecutionResult:
        """运行工作流实例
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 执行工作流（带重试）
            result = self._execute_with_retry(workflow, initial_data, **kwargs)
            
            # 更新统计
            self._update_stats(True, (datetime.now() - start_time).total_seconds())
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=True,
                result=result,
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "retries_used": kwargs.get("_retry_count", 0)
                }
            )
            
        except Exception as e:
            # 更新统计
            self._update_stats(False, (datetime.now() - start_time).total_seconds())
            
            logger.error(f"工作流实例执行失败: {workflow.config.name}, 错误: {e}")
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "error_type": type(e).__name__
                }
            )
    
    async def run_workflow_async(
        self, 
        config_path: str, 
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowExecutionResult:
        """异步运行工作流
        
        Args:
            config_path: 配置文件路径
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 加载工作流
            workflow = self.loader_service.load_from_file(config_path)
            
            # 异步执行工作流（带重试）
            result = await self._execute_with_retry_async(workflow, initial_data, **kwargs)
            
            # 更新统计
            self._update_stats(True, (datetime.now() - start_time).total_seconds())
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=True,
                result=result,
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "config_path": config_path,
                    "retries_used": kwargs.get("_retry_count", 0),
                    "execution_mode": "async"
                }
            )
            
        except Exception as e:
            # 更新统计
            self._update_stats(False, (datetime.now() - start_time).total_seconds())
            
            logger.error(f"工作流异步执行失败: {config_path}, 错误: {e}")
            
            return WorkflowExecutionResult(
                workflow_name="unknown",
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "config_path": config_path,
                    "error_type": type(e).__name__,
                    "execution_mode": "async"
                }
            )
    
    async def run_workflow_instance_async(
        self,
        workflow: WorkflowInstance,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> WorkflowExecutionResult:
        """异步运行工作流实例
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            WorkflowExecutionResult: 执行结果
        """
        start_time = datetime.now()
        
        try:
            # 异步执行工作流（带重试）
            result = await self._execute_with_retry_async(workflow, initial_data, **kwargs)
            
            # 更新统计
            self._update_stats(True, (datetime.now() - start_time).total_seconds())
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=True,
                result=result,
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "retries_used": kwargs.get("_retry_count", 0),
                    "execution_mode": "async"
                }
            )
            
        except Exception as e:
            # 更新统计
            self._update_stats(False, (datetime.now() - start_time).total_seconds())
            
            logger.error(f"工作流实例异步执行失败: {workflow.config.name}, 错误: {e}")
            
            return WorkflowExecutionResult(
                workflow_name=workflow.config.name,
                success=False,
                error=str(e),
                execution_time=(datetime.now() - start_time).total_seconds(),
                start_time=start_time,
                end_time=datetime.now(),
                metadata={
                    "error_type": type(e).__name__,
                    "execution_mode": "async"
                }
            )
    
    def stream_workflow(
        self, 
        config_path: str, 
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """流式运行工作流
        
        Args:
            config_path: 配置文件路径
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        try:
            # 加载工作流
            workflow = self.loader_service.load_from_file(config_path)
            
            # 流式执行
            for chunk in workflow.stream(initial_data, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"工作流流式执行失败: {config_path}, 错误: {e}")
            raise
    
    def stream_workflow_instance(
        self,
        workflow: WorkflowInstance,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Generator[Dict[str, Any], None, None]:
        """流式运行工作流实例
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        try:
            # 流式执行
            for chunk in workflow.stream(initial_data, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"工作流实例流式执行失败: {workflow.config.name}, 错误: {e}")
            raise
    
    async def stream_workflow_async(
        self, 
        config_path: str, 
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式运行工作流
        
        Args:
            config_path: 配置文件路径
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        try:
            # 加载工作流
            workflow = self.loader_service.load_from_file(config_path)
            
            # 异步流式执行
            async for chunk in workflow.stream_async(initial_data, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"工作流异步流式执行失败: {config_path}, 错误: {e}")
            raise
    
    async def stream_workflow_instance_async(
        self,
        workflow: WorkflowInstance,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> AsyncIterator[Dict[str, Any]]:
        """异步流式运行工作流实例
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Yields:
            Dict[str, Any]: 中间状态
        """
        try:
            # 异步流式执行
            async for chunk in workflow.stream_async(initial_data, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"工作流实例异步流式执行失败: {workflow.config.name}, 错误: {e}")
            raise
    
    def validate_workflow_config(self, config_path: str) -> Dict[str, Any]:
        """验证工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 验证结果
        """
        try:
            validation_result = self.loader_service.validate_workflow(config_path)
            
            return {
                "config_path": config_path,
                "is_valid": len([issue for issue in validation_result if issue.severity.value == "error"]) == 0,
                "errors": [issue.message for issue in validation_result if issue.severity.value == "error"],
                "warnings": [issue.message for issue in validation_result if issue.severity.value == "warning"],
                "suggestions": [issue.suggestion for issue in validation_result if issue.suggestion],
                "summary": f"发现 {len(validation_result)} 个问题"
            }
            
        except Exception as e:
            return {
                "config_path": config_path,
                "is_valid": False,
                "errors": [f"验证过程中发生异常: {e}"],
                "warnings": [],
                "suggestions": [],
                "summary": "验证失败"
            }
    
    def get_workflow_info(self, config_path: str) -> Optional[Dict[str, Any]]:
        """获取工作流信息
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Optional[Dict[str, Any]]: 工作流信息
        """
        try:
            return self.loader_service.get_workflow_info(config_path)
        except Exception as e:
            logger.error(f"获取工作流信息失败: {config_path}, 错误: {e}")
            return None
    
    def get_execution_statistics(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        stats = self._execution_stats.copy()
        
        if stats["total_executions"] > 0:
            stats["success_rate"] = stats["successful_executions"] / stats["total_executions"]
            stats["average_execution_time"] = stats["total_execution_time"] / stats["total_executions"]
        else:
            stats["success_rate"] = 0.0
            stats["average_execution_time"] = 0.0
        
        return stats
    
    def reset_statistics(self) -> None:
        """重置统计信息"""
        self._execution_stats = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0
        }
        logger.debug("统计信息已重置")
    
    def _execute_with_retry(
        self,
        workflow: WorkflowInstance,
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """带重试的执行
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        last_exception: Optional[Exception] = None
        
        # 过滤掉内部参数，只传递给工作流配置相关的参数
        workflow_kwargs = {k: v for k, v in kwargs.items() if not k.startswith('_')}
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"重试执行工作流 (第 {attempt} 次): {workflow.config.name}")
                    # 创建一个新的字典，添加重试计数，但不修改原始kwargs
                    temp_kwargs = workflow_kwargs.copy()
                    temp_kwargs["_retry_count"] = attempt
                
                    return workflow.run(initial_data, **temp_kwargs)
                else:
                    return workflow.run(initial_data, **workflow_kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(f"工作流执行失败，准备重试: {e}")
                    # 可以在这里添加重试延迟
                    # time.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"工作流执行失败，已达到最大重试次数: {e}")
                    break
        
        if last_exception is not None:
            raise last_exception
        else:
            # 如果没有异常被记录，抛出一个通用异常
            raise WorkflowExecutionError("工作流执行失败，但没有捕获到具体异常")
    
    async def _execute_with_retry_async(
        self, 
        workflow: WorkflowInstance, 
        initial_data: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """异步带重试的执行
        
        Args:
            workflow: 工作流实例
            initial_data: 初始数据
            **kwargs: 其他参数
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        last_exception: Optional[Exception] = None
        
        for attempt in range(self.max_retries + 1):
            try:
                if attempt > 0:
                    logger.info(f"异步重试执行工作流 (第 {attempt} 次): {workflow.config.name}")
                    kwargs["_retry_count"] = attempt
                
                return await workflow.run_async(initial_data, **kwargs)
                
            except Exception as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    logger.warning(f"工作流异步执行失败，准备重试: {e}")
                    # 可以在这里添加重试延迟
                    # await asyncio.sleep(2 ** attempt)  # 指数退避
                else:
                    logger.error(f"工作流异步执行失败，已达到最大重试次数: {e}")
                    break
        
        if last_exception is not None:
            raise last_exception
        else:
            # 如果没有异常被记录，抛出一个通用异常
            raise WorkflowExecutionError("工作流异步执行失败，但没有捕获到具体异常")
    
    def _update_stats(self, success: bool, execution_time: float) -> None:
        """更新统计信息
        
        Args:
            success: 是否成功
            execution_time: 执行时间
        """
        self._execution_stats["total_executions"] += 1
        self._execution_stats["total_execution_time"] += execution_time
        
        if success:
            self._execution_stats["successful_executions"] += 1
        else:
            self._execution_stats["failed_executions"] += 1


# 便捷函数
def run_workflow(config_path: str, initial_data: Optional[Dict[str, Any]] = None) -> WorkflowExecutionResult:
    """运行工作流（便捷函数）
    
    Args:
        config_path: 配置文件路径
        initial_data: 初始数据
        
    Returns:
        WorkflowExecutionResult: 执行结果
    """
    runner = WorkflowRunner()
    return runner.run_workflow(config_path, initial_data)


async def run_workflow_async(config_path: str, initial_data: Optional[Dict[str, Any]] = None) -> WorkflowExecutionResult:
    """异步运行工作流（便捷函数）
    
    Args:
        config_path: 配置文件路径
        initial_data: 初始数据
        
    Returns:
        WorkflowExecutionResult: 执行结果
    """
    runner = WorkflowRunner()
    return await runner.run_workflow_async(config_path, initial_data)