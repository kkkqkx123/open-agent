"""通用应用层接口定义

提供应用层的通用接口，包括业务服务、协调器和横切关注点。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic, AsyncIterator
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from .common_domain import ExecutionContext as BaseExecutionContext

# 泛型类型变量
T = TypeVar('T')
K = TypeVar('K')
R = TypeVar('R')

'''
应用层枚举定义
'''

class OperationStatus(str, Enum):
    """
    操作状态枚举
    
    定义应用层操作的执行状态。
    """
    PENDING = "pending"      # 等待执行
    RUNNING = "running"      # 正在执行
    COMPLETED = "completed"  # 执行完成
    FAILED = "failed"        # 执行失败
    CANCELLED = "cancelled"  # 已取消


class Priority(str, Enum):
    """
    优先级枚举
    
    定义操作的优先级。
    """
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

'''
应用层数据传输对象
'''

@dataclass
class OperationResult:
    """
    操作结果数据传输对象
    
    封装应用层操作的执行结果，提供统一的返回格式。
    """
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self) -> None:
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PagedResult:
    """
    分页结果数据传输对象
    
    封装分页查询的结果，提供统一的分页信息。
    """
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
    
    @property
    def total_pages(self) -> int:
        """计算总页数"""
        return (self.total + self.page_size - 1) // self.page_size


# 使用统一的执行上下文，但为了向后兼容保留别名
ExecutionContext = BaseExecutionContext


'''
应用层基础服务接口
'''

class IBaseService(ABC):
    """
    基础服务接口
    
    定义应用层服务的通用契约，所有业务服务应实现此接口。
    """
    
    @abstractmethod
    async def initialize(self) -> None:
        """
        初始化服务
        
        执行服务初始化逻辑，如加载配置、建立连接等。
        """
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """
        关闭服务
        
        执行服务清理逻辑，如释放资源、关闭连接等。
        """
        pass
    
    @abstractmethod
    def get_service_status(self) -> Dict[str, Any]:
        """
        获取服务状态
        
        Returns:
            Dict[str, Any]: 服务状态信息
        """
        pass
    
    @abstractmethod
    async def health_check(self) -> OperationResult:
        """
        健康检查
        
        Returns:
            OperationResult: 健康检查结果
        """
        pass


class ICrudService(Generic[T, K], ABC):
    """
    CRUD服务接口
    
    提供标准的创建、读取、更新、删除操作的服务接口。
    """
    
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> K:
        """
        创建实体
        
        Args:
            data: 实体数据
            
        Returns:
            K: 创建的实体ID
            
        Raises:
            ValidationException: 数据验证失败
            CreationException: 创建失败
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: K) -> Optional[T]:
        """
        根据ID获取实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            Optional[T]: 实体对象，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update(self, entity_id: K, updates: Dict[str, Any]) -> bool:
        """
        更新实体
        
        Args:
            entity_id: 实体ID
            updates: 更新数据
            
        Returns:
            bool: 是否更新成功
            
        Raises:
            NotFoundException: 实体不存在
            ValidationException: 数据验证失败
        """
        pass
    
    @abstractmethod
    async def delete(self, entity_id: K) -> bool:
        """
        删除实体
        
        Args:
            entity_id: 实体ID
            
        Returns:
            bool: 是否删除成功
            
        Raises:
            NotFoundException: 实体不存在
        """
        pass
    
    @abstractmethod
    async def list(
        self,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
        page: int = 1,
        page_size: int = 20
    ) -> PagedResult:
        """
        列出实体
        
        Args:
            filters: 过滤条件
            sort_by: 排序字段
            sort_order: 排序顺序
            page: 页码
            page_size: 页面大小
            
        Returns:
            PagedResult: 分页结果
        """
        pass


class IQueryService(Generic[T], ABC):
    """
    查询服务接口
    
    提供复杂查询功能的服务接口。
    """
    
    @abstractmethod
    async def query(self, query: str, parameters: Dict[str, Any]) -> List[T]:
        """
        执行查询
        
        Args:
            query: 查询语句
            parameters: 查询参数
            
        Returns:
            List[T]: 查询结果列表
        """
        pass
    
    @abstractmethod
    async def search(
        self,
        search_term: str,
        fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10
    ) -> List[T]:
        """
        搜索实体
        
        Args:
            search_term: 搜索词
            fields: 搜索字段
            filters: 过滤条件
            limit: 结果限制
            
        Returns:
            List[T]: 搜索结果列表
        """
        pass
    
    @abstractmethod
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        统计数量
        
        Args:
            filters: 过滤条件
            
        Returns:
            int: 符合条件的实体数量
        """
        pass


'''
应用层协调器接口
'''

class ICoordinator(ABC):
    """
    协调器接口
    
    负责协调多个服务的执行，处理跨服务的业务逻辑。
    """
    
    @abstractmethod
    async def execute_workflow(
        self,
        workflow_id: str,
        context: ExecutionContext,
        **kwargs: Any
    ) -> OperationResult:
        """
        执行工作流
        
        Args:
            workflow_id: 工作流ID
            context: 执行上下文
            **kwargs: 额外参数
            
        Returns:
            OperationResult: 执行结果
        """
        pass
    
    @abstractmethod
    async def coordinate_services(
        self,
        service_operations: List[Callable],
        context: ExecutionContext,
        rollback_on_error: bool = True
    ) -> List[OperationResult]:
        """
        协调服务操作
        
        Args:
            service_operations: 服务操作列表
            context: 执行上下文
            rollback_on_error: 错误时是否回滚
            
        Returns:
            List[OperationResult]: 操作结果列表
        """
        pass


'''
应用层事件接口
'''

class IEventPublisher(ABC):
    """
    事件发布器接口
    
    负责发布领域事件，支持事件驱动架构。
    """
    
    @abstractmethod
    async def publish(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        context: Optional[ExecutionContext] = None
    ) -> None:
        """
        发布事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            context: 执行上下文
        """
        pass
    
    @abstractmethod
    async def publish_batch(
        self,
        events: List[Dict[str, Any]],
        context: Optional[ExecutionContext] = None
    ) -> None:
        """
        批量发布事件
        
        Args:
            events: 事件列表
            context: 执行上下文
        """
        pass


class IEventHandler(ABC):
    """
    事件处理器接口
    
    定义事件处理的契约。
    """
    
    @abstractmethod
    async def handle(
        self,
        event_type: str,
        event_data: Dict[str, Any],
        context: Optional[ExecutionContext] = None
    ) -> OperationResult:
        """
        处理事件
        
        Args:
            event_type: 事件类型
            event_data: 事件数据
            context: 执行上下文
            
        Returns:
            OperationResult: 处理结果
        """
        pass
    
    @abstractmethod
    def get_supported_event_types(self) -> List[str]:
        """
        获取支持的事件类型
        
        Returns:
            List[str]: 支持的事件类型列表
        """
        pass


'''
应用层任务接口
'''

class ITaskScheduler(ABC):
    """
    任务调度器接口
    
    负责调度和执行异步任务。
    """
    
    @abstractmethod
    async def schedule_task(
        self,
        task_func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict[str, Any]] = None,
        delay: Optional[float] = None,
        priority: Priority = Priority.NORMAL
    ) -> str:
        """
        调度任务
        
        Args:
            task_func: 任务函数
            args: 位置参数
            kwargs: 关键字参数
            delay: 延迟时间（秒）
            priority: 优先级
            
        Returns:
            str: 任务ID
        """
        pass
    
    @abstractmethod
    async def cancel_task(self, task_id: str) -> bool:
        """
        取消任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            bool: 是否取消成功
        """
        pass
    
    @abstractmethod
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        获取任务状态
        
        Args:
            task_id: 任务ID
            
        Returns:
            Dict[str, Any]: 任务状态信息
        """
        pass
    
    @abstractmethod
    async def list_tasks(
        self,
        status: Optional[OperationStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        列出任务
        
        Args:
            status: 操作状态过滤
            limit: 结果限制
            
        Returns:
            List[Dict[str, Any]]: 任务列表
        """
        pass


'''
应用层监控接口
'''

class IMetricsCollector(ABC):
    """
    指标收集器接口
    
    负责收集和报告应用层指标。
    """
    
    @abstractmethod
    async def record_counter(
        self,
        metric_name: str,
        value: int = 1,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录计数器指标
        
        Args:
            metric_name: 指标名称
            value: 计数值
            tags: 标签
        """
        pass
    
    @abstractmethod
    async def record_gauge(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录仪表指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            tags: 标签
        """
        pass
    
    @abstractmethod
    async def record_histogram(
        self,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        记录直方图指标
        
        Args:
            metric_name: 指标名称
            value: 指标值
            tags: 标签
        """
        pass
    
    @abstractmethod
    async def get_metrics_summary(self) -> Dict[str, Any]:
        """
        获取指标摘要
        
        Returns:
            Dict[str, Any]: 指标摘要信息
        """
        pass