"""重试策略

提供工作流执行的重试策略实现。
"""

from src.interfaces.dependency_injection import get_logger
import time
import asyncio
from typing import Optional, List, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from typing import TYPE_CHECKING

from .strategy_base import BaseStrategy, IExecutionStrategy

from src.interfaces.workflow.execution import IWorkflowExecutor
from ..core.execution_context import ExecutionContext, ExecutionResult

if TYPE_CHECKING:
    from src.interfaces.workflow.core import IWorkflow

logger = get_logger(__name__)


class RetryStrategy(Enum):
    """重试策略枚举"""
    FIXED_DELAY = "fixed_delay"        # 固定延迟
    EXPONENTIAL_BACKOFF = "exponential_backoff"  # 指数退避
    LINEAR_BACKOFF = "linear_backoff"   # 线性退避
    RANDOM_JITTER = "random_jitter"     # 随机抖动


@dataclass
class RetryConfig:
    """重试配置"""
    max_retries: int = 3
    strategy: RetryStrategy = RetryStrategy.EXPONENTIAL_BACKOFF
    base_delay: float = 1.0  # 基础延迟时间（秒）
    max_delay: float = 60.0  # 最大延迟时间（秒）
    multiplier: float = 2.0  # 退避倍数
    jitter: bool = True  # 是否添加随机抖动
    retry_on_exceptions: List[type] = field(default_factory=lambda: [Exception])
    stop_on_exceptions: List[type] = field(default_factory=list)
    retry_condition: Optional[Callable[[Exception], bool]] = None
    
    def should_retry(self, exception: Exception, attempt: int) -> bool:
        """判断是否应该重试
        
        Args:
            exception: 异常对象
            attempt: 当前尝试次数
            
        Returns:
            bool: 是否应该重试
        """
        # 检查是否超过最大重试次数
        if attempt >= self.max_retries:
            return False
        
        # 检查是否在停止重试的异常列表中
        for stop_exception in self.stop_on_exceptions:
            if isinstance(exception, stop_exception):
                return False
        
        # 检查是否在重试的异常列表中
        for retry_exception in self.retry_on_exceptions:
            if isinstance(exception, retry_exception):
                # 如果有自定义重试条件，使用自定义条件
                if self.retry_condition:
                    return self.retry_condition(exception)
                return True
        
        return False
    
    def calculate_delay(self, attempt: int) -> float:
        """计算延迟时间
        
        Args:
            attempt: 当前尝试次数
            
        Returns:
            float: 延迟时间（秒）
        """
        import random
        
        if self.strategy == RetryStrategy.FIXED_DELAY:
            delay = self.base_delay
        elif self.strategy == RetryStrategy.EXPONENTIAL_BACKOFF:
            delay = self.base_delay * (self.multiplier ** attempt)
        elif self.strategy == RetryStrategy.LINEAR_BACKOFF:
            delay = self.base_delay * (attempt + 1)
        elif self.strategy == RetryStrategy.RANDOM_JITTER:
            delay = self.base_delay + random.uniform(0, self.base_delay)
        else:
            delay = self.base_delay
        
        # 应用最大延迟限制
        delay = min(delay, self.max_delay)
        
        # 添加随机抖动
        if self.jitter and self.strategy != RetryStrategy.RANDOM_JITTER:
            jitter_amount = delay * 0.1  # 10% 的抖动
            delay += random.uniform(-jitter_amount, jitter_amount)
        
        return max(0, delay)  # 确保延迟时间不为负


@dataclass
class RetryAttempt:
    """重试尝试记录"""
    attempt_number: int
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    exception: Optional[Exception] = None
    delay_before: float = 0.0
    
    @property
    def duration(self) -> Optional[float]:
        """获取尝试持续时间（秒）"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None


class RetryStrategyImpl(BaseStrategy):
    """重试策略实现
    
    提供可配置的重试机制，支持多种重试策略和条件判断。
    """
    
    def __init__(self, config: Optional[RetryConfig] = None):
        """初始化重试策略
        
        Args:
            config: 重试配置
        """
        super().__init__("retry", priority=10)
        self.config = config or RetryConfig()
        logger.debug(f"重试策略初始化完成，策略: {self.config.strategy.value}")
    
    def execute(
        self, 
        executor: 'IWorkflowExecutor', 
        workflow: 'IWorkflow', 
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """使用重试策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        attempts = []
        
        for attempt in range(self.config.max_retries + 1):
            attempt_start = datetime.now()
            
            # 计算延迟时间（除了第一次尝试）
            delay_before = 0.0
            if attempt > 0:
                delay_before = self.config.calculate_delay(attempt - 1)
                if delay_before > 0:
                    logger.info(f"等待 {delay_before:.2f} 秒后重试 (第 {attempt} 次)")
                    time.sleep(delay_before)
            
            try:
                # 执行工作流
                logger.debug(f"执行工作流尝试 {attempt + 1}/{self.config.max_retries + 1}: {workflow.name}")
                
                # 创建初始状态（从工作流创建）
                from src.core.state.factories.state_factory import create_workflow_state
                initial_state = create_workflow_state(
                    values=context.metadata or {},
                    config=context.config or {}
                )
                
                result_state = executor.execute(workflow, initial_state, context.config)
                
                # 转换状态为执行结果
                execution_result = self.create_execution_result(
                    success=True,
                    result=result_state.values if hasattr(result_state, 'values') else {},
                    metadata=getattr(result_state, 'metadata', {}) or {}
                )
                
                # 记录成功的尝试
                attempt_end = datetime.now()
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    start_time=attempt_start,
                    end_time=attempt_end,
                    success=True,
                    delay_before=delay_before
                )
                attempts.append(attempt_record)
                
                total_time = (attempt_end - start_time).total_seconds()
                logger.info(f"工作流执行成功: {workflow.name}, 尝试次数: {attempt + 1}, 总耗时: {total_time:.2f}秒")
                
                # 添加重试元数据到结果
                execution_result.metadata.update({
                    "retry_attempts": attempt + 1,
                    "retry_total_time": total_time,
                    "retry_strategy": self.config.strategy.value,
                    "retry_attempts_detail": [
                        {
                            "attempt": a.attempt_number,
                            "success": a.success,
                            "duration": a.duration,
                            "delay_before": a.delay_before
                        } for a in attempts
                    ]
                })
                
                return execution_result
                
            except Exception as e:
                # 记录失败的尝试
                attempt_end = datetime.now()
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    start_time=attempt_start,
                    end_time=attempt_end,
                    success=False,
                    exception=e,
                    delay_before=delay_before
                )
                attempts.append(attempt_record)
                
                # 判断是否应该重试
                if not self.config.should_retry(e, attempt):
                    logger.error(f"工作流执行失败，不再重试: {e}")
                    break
                
                logger.warning(f"工作流执行失败，准备重试: {e}")
        
        # 所有尝试都失败了
        total_time = (datetime.now() - start_time).total_seconds()
        last_exception = attempts[-1].exception if attempts else None
        
        logger.error(f"工作流执行失败，已达到最大重试次数: {self.config.max_retries}, 总耗时: {total_time:.2f}秒")
        
        # 创建失败结果
        result = self.create_execution_result(
            success=False,
            error=str(last_exception) if last_exception else "未知错误",
            metadata={
                "retry_attempts": len(attempts),
                "retry_total_time": total_time,
                "retry_strategy": self.config.strategy.value,
                "retry_attempts_detail": [
                    {
                        "attempt": a.attempt_number,
                        "success": a.success,
                        "duration": a.duration,
                        "delay_before": a.delay_before,
                        "error": str(a.exception) if a.exception else None
                    } for a in attempts
                ]
            }
        )
        
        return result
    
    async def execute_async(
        self, 
        executor: 'IWorkflowExecutor', 
        workflow: 'IWorkflow', 
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """异步使用重试策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        start_time = datetime.now()
        attempts = []
        
        for attempt in range(self.config.max_retries + 1):
            attempt_start = datetime.now()
            
            # 计算延迟时间（除了第一次尝试）
            delay_before = 0.0
            if attempt > 0:
                delay_before = self.config.calculate_delay(attempt - 1)
                if delay_before > 0:
                    logger.info(f"等待 {delay_before:.2f} 秒后重试 (第 {attempt} 次)")
                    await asyncio.sleep(delay_before)
            
            try:
                # 异步执行工作流
                logger.debug(f"异步执行工作流尝试 {attempt + 1}/{self.config.max_retries + 1}: {workflow.name}")
                
                # 创建初始状态（从工作流创建）
                from src.core.state.factories.state_factory import create_workflow_state
                initial_state = create_workflow_state(
                    values=context.metadata or {},
                    config=context.config or {}
                )
                
                result_state = await executor.execute_async(workflow, initial_state, context.config)
                
                # 转换状态为执行结果
                execution_result = self.create_execution_result(
                    success=True,
                    result=result_state.values if hasattr(result_state, 'values') else {},
                    metadata=getattr(result_state, 'metadata', {}) or {}
                )
                
                # 记录成功的尝试
                attempt_end = datetime.now()
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    start_time=attempt_start,
                    end_time=attempt_end,
                    success=True,
                    delay_before=delay_before
                )
                attempts.append(attempt_record)
                
                total_time = (attempt_end - start_time).total_seconds()
                logger.info(f"工作流异步执行成功: {workflow.name}, 尝试次数: {attempt + 1}, 总耗时: {total_time:.2f}秒")
                
                # 添加重试元数据到结果
                execution_result.metadata.update({
                    "retry_attempts": attempt + 1,
                    "retry_total_time": total_time,
                    "retry_strategy": self.config.strategy.value,
                    "retry_attempts_detail": [
                        {
                            "attempt": a.attempt_number,
                            "success": a.success,
                            "duration": a.duration,
                            "delay_before": a.delay_before
                        } for a in attempts
                    ],
                    "execution_mode": "async"
                })
                
                return execution_result
                
            except Exception as e:
                # 记录失败的尝试
                attempt_end = datetime.now()
                attempt_record = RetryAttempt(
                    attempt_number=attempt,
                    start_time=attempt_start,
                    end_time=attempt_end,
                    success=False,
                    exception=e,
                    delay_before=delay_before
                )
                attempts.append(attempt_record)
                
                # 判断是否应该重试
                if not self.config.should_retry(e, attempt):
                    logger.error(f"工作流异步执行失败，不再重试: {e}")
                    break
                
                logger.warning(f"工作流异步执行失败，准备重试: {e}")
        
        # 所有尝试都失败了
        total_time = (datetime.now() - start_time).total_seconds()
        last_exception = attempts[-1].exception if attempts else None
        
        logger.error(f"工作流异步执行失败，已达到最大重试次数: {self.config.max_retries}, 总耗时: {total_time:.2f}秒")
        
        # 创建失败结果
        result = self.create_execution_result(
            success=False,
            error=str(last_exception) if last_exception else "未知错误",
            metadata={
                "retry_attempts": len(attempts),
                "retry_total_time": total_time,
                "retry_strategy": self.config.strategy.value,
                "retry_attempts_detail": [
                    {
                        "attempt": a.attempt_number,
                        "success": a.success,
                        "duration": a.duration,
                        "delay_before": a.delay_before,
                        "error": str(a.exception) if a.exception else None
                    } for a in attempts
                ],
                "execution_mode": "async"
            }
        )
        
        return result
    
    def can_handle(self, workflow: 'IWorkflow', context: 'ExecutionContext') -> bool:
        """判断是否适用重试策略
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            bool: 是否适用重试策略
        """
        return context.get_config("retry_enabled", False) or self.config.max_retries > 0
    
    def update_config(self, config: RetryConfig) -> None:
        """更新重试配置
        
        Args:
            config: 新的重试配置
        """
        self.config = config
        logger.debug(f"重试配置已更新，策略: {self.config.strategy.value}")


# 预定义的重试配置
class RetryConfigs:
    """预定义的重试配置"""
    
    @staticmethod
    def conservative() -> RetryConfig:
        """保守的重试配置"""
        return RetryConfig(
            max_retries=2,
            strategy=RetryStrategy.FIXED_DELAY,
            base_delay=2.0,
            max_delay=10.0,
            jitter=False
        )
    
    @staticmethod
    def aggressive() -> RetryConfig:
        """激进的重试配置"""
        return RetryConfig(
            max_retries=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=0.5,
            max_delay=30.0,
            multiplier=1.5,
            jitter=True
        )
    
    @staticmethod
    def network_friendly() -> RetryConfig:
        """网络友好的重试配置"""
        return RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=1.0,
            max_delay=60.0,
            multiplier=2.0,
            jitter=True,
            retry_on_exceptions=[ConnectionError, TimeoutError]
        )
    
    @staticmethod
    def quick_retry() -> RetryConfig:
        """快速重试配置"""
        return RetryConfig(
            max_retries=3,
            strategy=RetryStrategy.LINEAR_BACKOFF,
            base_delay=0.1,
            max_delay=1.0,
            jitter=False
        )