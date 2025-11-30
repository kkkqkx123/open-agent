"""执行策略基类

提供执行策略的基础接口和抽象实现。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.interfaces.workflow.execution import IWorkflowExecutor
    from ..core.execution_context import ExecutionContext, ExecutionResult
    from src.interfaces.workflow.core import IWorkflow

class IExecutionStrategy(ABC):
    """执行策略接口
    
    定义不同的执行策略接口。
    """
    
    @abstractmethod
    def execute(
        self, 
        executor: 'IWorkflowExecutor', 
        workflow: 'IWorkflow', 
        context: 'ExecutionContext'
    ) -> 'ExecutionResult':
        """使用策略执行工作流
        
        Args:
            executor: 工作流执行器
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            ExecutionResult: 执行结果
        """
        pass
    
    @abstractmethod
    def can_handle(self, workflow: 'IWorkflow', context: 'ExecutionContext') -> bool:
        """判断策略是否适用
        
        Args:
            workflow: 工作流实例
            context: 执行上下文
            
        Returns:
            bool: 是否适用此策略
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称
        
        Returns:
            str: 策略名称
        """
        pass
    
    def get_priority(self) -> int:
        """获取策略优先级
        
        Returns:
            int: 优先级，数值越高优先级越高
        """
        return 0


class BaseStrategy(IExecutionStrategy):
    """执行策略基类
    
    提供执行策略的通用实现。
    """
    
    def __init__(self, name: str, priority: int = 0):
        """初始化策略
        
        Args:
            name: 策略名称
            priority: 优先级
        """
        self._name = name
        self._priority = priority
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return self._name
    
    def get_priority(self) -> int:
        """获取策略优先级"""
        return self._priority
    
    def validate_context(self, context: 'ExecutionContext') -> None:
        """验证执行上下文
        
        Args:
            context: 执行上下文
            
        Raises:
            ValueError: 上下文无效
        """
        if not context:
            raise ValueError("执行上下文不能为空")
    
    def create_execution_result(
        self, 
        success: bool, 
        result: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        workflow_name: Optional[str] = None
    ) -> 'ExecutionResult':
        """创建执行结果
        
        Args:
            success: 是否成功
            result: 执行结果
            error: 错误信息
            metadata: 元数据
            workflow_name: 工作流名称
            
        Returns:
            ExecutionResult: 执行结果
        """
        from ..core.execution_context import ExecutionResult
        
        return ExecutionResult(
            success=success,
            result=result or {},
            error=error,
            metadata=metadata or {},
            strategy_name=self._name,
            workflow_name=workflow_name
        )