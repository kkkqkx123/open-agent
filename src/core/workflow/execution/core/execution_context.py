"""执行上下文

提供执行过程中的上下文信息和结果类型定义。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, Optional, List, TYPE_CHECKING, Literal
from enum import Enum

from src.core.common import WorkflowExecutionContext

if TYPE_CHECKING:
    from src.interfaces.state import IWorkflowState
    from ...workflow import Workflow

class ExecutionStatus(str, Enum):
    """执行状态枚举
    
    定义工作流执行过程中的各种状态。
    """
    PENDING = "pending"        # 等待中
    RUNNING = "running"        # 运行中
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 失败
    CANCELLED = "cancelled"    # 已取消
    PAUSED = "paused"          # 已暂停


@dataclass
class ExecutionContext(WorkflowExecutionContext):
    """工作流执行上下文 - 继承自通用执行上下文
    
    扩展了基础执行上下文，添加工作流特定的功能。
    """
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ExecutionStatus = ExecutionStatus.PENDING
    
    def __post_init__(self):
        """初始化后处理"""
        super().__post_init__()
        if self.start_time is None:
            self.start_time = datetime.now()
    
    @property
    def execution_time(self) -> Optional[float]:
        """获取执行时间（秒）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键
            default: 默认值
            
        Returns:
            Any: 配置值
        """
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any) -> None:
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value
    
    def get_metadata(self, key: str, default: Any = None) -> Any:
        """获取元数据值
        
        Args:
            key: 元数据键
            default: 默认值
            
        Returns:
            Any: 元数据值
        """
        return self.metadata.get(key, default)
    
    def set_metadata(self, key: str, value: Any) -> None:
        """设置元数据值
        
        Args:
            key: 元数据键
            value: 元数据值
        """
        self.metadata[key] = value
    
    def mark_started(self) -> None:
        """标记为开始执行"""
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
    
    def mark_completed(self) -> None:
        """标记为完成"""
        self.status = ExecutionStatus.COMPLETED
        self.end_time = datetime.now()
    
    def mark_failed(self) -> None:
        """标记为失败"""
        self.status = ExecutionStatus.FAILED
        self.end_time = datetime.now()
    
    def mark_cancelled(self) -> None:
        """标记为取消"""
        self.status = ExecutionStatus.CANCELLED
        self.end_time = datetime.now()
    
    def mark_paused(self) -> None:
        """标记为暂停"""
        self.status = ExecutionStatus.PAUSED


@dataclass
class NodeResult:
    """节点执行结果"""
    success: bool
    state: 'IWorkflowState'
    next_node: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    mode_name: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ExecutionResult:
    """工作流执行结果"""
    success: bool
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    strategy_name: Optional[str] = None
    node_results: List[NodeResult] = field(default_factory=list)
    workflow_name: Optional[str] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}
        if self.node_results is None:
            self.node_results = []
    
    @property
    def successful_nodes(self) -> List[NodeResult]:
        """获取成功执行的节点"""
        return [nr for nr in self.node_results if nr.success]
    
    @property
    def failed_nodes(self) -> List[NodeResult]:
        """获取执行失败的节点"""
        return [nr for nr in self.node_results if not nr.success]
    
    @property
    def total_nodes(self) -> int:
        """获取总节点数"""
        return len(self.node_results)
    
    @property
    def success_rate(self) -> float:
        """获取成功率"""
        if self.total_nodes == 0:
            return 0.0
        return len(self.successful_nodes) / self.total_nodes
    
    def add_node_result(self, node_result: NodeResult) -> None:
        """添加节点执行结果
        
        Args:
            node_result: 节点执行结果
        """
        self.node_results.append(node_result)
    
    def get_node_result(self, node_id: str) -> Optional[NodeResult]:
        """获取指定节点的执行结果
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[NodeResult]: 节点执行结果
        """
        for nr in self.node_results:
            if nr.metadata.get("node_id") == node_id:
                return nr
        return None


@dataclass
class BatchJob:
    """批量作业"""
    job_id: str
    workflow_id: str
    config_path: Optional[str] = None
    initial_data: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    workflow_instance: Optional['Workflow'] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.metadata is None:
            self.metadata = {}


@dataclass
class BatchExecutionResult:
    """批量执行结果"""
    success: bool
    total_jobs: int
    successful_jobs: int
    failed_jobs: int
    total_time: float = 0.0
    results: List[ExecutionResult] = field(default_factory=list)
    errors: List[Dict[str, Any]] = field(default_factory=list)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if self.results is None:
            self.results = []
        if self.errors is None:
            self.errors = []
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_jobs == 0:
            return 0.0
        return self.successful_jobs / self.total_jobs
    
    @property
    def average_execution_time(self) -> float:
        """平均执行时间"""
        if self.successful_jobs == 0:
            return 0.0
        total_time = sum(r.execution_time for r in self.results if r.success)
        return total_time / self.successful_jobs
    
    def get_successful_results(self) -> List[ExecutionResult]:
        """获取成功的结果"""
        return [r for r in self.results if r.success]
    
    def get_failed_results(self) -> List[ExecutionResult]:
        """获取失败的结果"""
        return [r for r in self.results if not r.success]