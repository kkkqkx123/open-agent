"""执行统计功能 - 新架构实现

提供执行计数器、成功率统计、平均/最大/最小执行时间、按工作流分组统计等功能。
"""

from typing import Dict, Any, Optional, List, Union, Callable, TypeVar
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from src.interfaces.dependency_injection import get_logger
import threading
import time
import json
from pathlib import Path

logger = get_logger(__name__)

# 定义支持比较的类型变量
T = TypeVar('T', bound=Union[int, float])


@dataclass
class WorkflowExecutionResult:
    """工作流执行结果数据类
    
    用于统计执行信息的数据模型，包含执行时间、成功状态等信息。
    """
    workflow_name: Optional[str] = None
    success: bool = False
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class StatisticPeriod(Enum):
    """统计周期枚举"""
    REALTIME = "realtime"    # 实时统计
    HOURLY = "hourly"        # 每小时统计
    DAILY = "daily"          # 每日统计
    WEEKLY = "weekly"        # 每周统计
    MONTHLY = "monthly"      # 每月统计


@dataclass
class ExecutionRecord:
    """执行记录"""
    workflow_name: str
    success: bool
    execution_time: float
    start_time: datetime
    end_time: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def duration(self) -> timedelta:
        """获取执行持续时间"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_name": self.workflow_name,
            "success": self.success,
            "execution_time": self.execution_time,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "metadata": self.metadata
        }


@dataclass
class WorkflowStatistics:
    """工作流统计信息"""
    workflow_name: str
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    total_execution_time: float = 0.0
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    last_execution_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    error_types: Dict[str, int] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.successful_executions / self.total_executions
    
    @property
    def average_execution_time(self) -> float:
        """平均执行时间"""
        if self.successful_executions == 0:
            return 0.0
        return self.total_execution_time / self.successful_executions
    
    def update(self, record: ExecutionRecord) -> None:
        """更新统计信息
        
        Args:
            record: 执行记录
        """
        self.total_executions += 1
        self.last_execution_time = record.end_time
        
        if record.success:
            self.successful_executions += 1
            self.total_execution_time += record.execution_time
            self.last_success_time = record.end_time
            
            # 更新最小和最大执行时间
            if self.min_execution_time is None or record.execution_time < self.min_execution_time:
                self.min_execution_time = record.execution_time
            
            if self.max_execution_time is None or record.execution_time > self.max_execution_time:
                self.max_execution_time = record.execution_time
        else:
            self.failed_executions += 1
            self.last_failure_time = record.end_time
            
            # 统计错误类型
            error_type = record.metadata.get("error_type", "unknown")
            self.error_types[error_type] = self.error_types.get(error_type, 0) + 1
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "workflow_name": self.workflow_name,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "success_rate": self.success_rate,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": self.average_execution_time,
            "min_execution_time": self.min_execution_time,
            "max_execution_time": self.max_execution_time,
            "last_execution_time": self.last_execution_time.isoformat() if self.last_execution_time else None,
            "last_success_time": self.last_success_time.isoformat() if self.last_success_time else None,
            "last_failure_time": self.last_failure_time.isoformat() if self.last_failure_time else None,
            "error_types": self.error_types
        }


@dataclass
class GlobalStatistics:
    """全局统计信息"""
    total_workflows: int = 0
    total_executions: int = 0
    total_successful_executions: int = 0
    total_failed_executions: int = 0
    total_execution_time: float = 0.0
    workflow_stats: Dict[str, WorkflowStatistics] = field(default_factory=dict)
    period_stats: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    @property
    def success_rate(self) -> float:
        """全局成功率"""
        if self.total_executions == 0:
            return 0.0
        return self.total_successful_executions / self.total_executions
    
    @property
    def average_execution_time(self) -> float:
        """全局平均执行时间"""
        if self.total_successful_executions == 0:
            return 0.0
        return self.total_execution_time / self.total_successful_executions
    
    def update(self, record: ExecutionRecord) -> None:
        """更新全局统计信息
        
        Args:
            record: 执行记录
        """
        self.total_executions += 1
        
        if record.success:
            self.total_successful_executions += 1
            self.total_execution_time += record.execution_time
        else:
            self.total_failed_executions += 1
        
        # 更新工作流统计
        if record.workflow_name not in self.workflow_stats:
            self.workflow_stats[record.workflow_name] = WorkflowStatistics(
                workflow_name=record.workflow_name
            )
            self.total_workflows += 1
        
        self.workflow_stats[record.workflow_name].update(record)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_workflows": self.total_workflows,
            "total_executions": self.total_executions,
            "total_successful_executions": self.total_successful_executions,
            "total_failed_executions": self.total_failed_executions,
            "success_rate": self.success_rate,
            "total_execution_time": self.total_execution_time,
            "average_execution_time": self.average_execution_time,
            "workflow_stats": {
                name: stats.to_dict() 
                for name, stats in self.workflow_stats.items()
            },
            "period_stats": self.period_stats
        }


class ExecutionStatsCollector:
    """执行统计收集器
    
    收集和管理工作流执行统计信息。
    """
    
    def __init__(
        self,
        enable_persistence: bool = True,
        persistence_path: Optional[str] = None,
        max_records: int = 10000
    ):
        """初始化执行统计收集器
        
        Args:
            enable_persistence: 是否启用持久化
            persistence_path: 持久化路径
            max_records: 最大记录数
        """
        self.enable_persistence = enable_persistence
        self.persistence_path = persistence_path or "data/execution_stats.json"
        self.max_records = max_records
        
        # 统计数据
        self.global_stats = GlobalStatistics()
        self.records: List[ExecutionRecord] = []
        
        # 线程安全
        self._lock = threading.Lock()
        
        # 加载持久化数据
        if self.enable_persistence:
            self._load_stats()
        
        logger.debug("执行统计收集器初始化完成")
    
    def record_execution(self, result: WorkflowExecutionResult) -> None:
        """记录执行结果
        
        Args:
            result: 工作流执行结果
        """
        if not result.start_time or not result.end_time:
            logger.warning("执行结果缺少时间信息，跳过记录")
            return
        
        # 创建执行记录
        record = ExecutionRecord(
            workflow_name=result.workflow_name or "unknown",
            success=result.success,
            execution_time=result.execution_time or 0.0,
            start_time=result.start_time,
            end_time=result.end_time,
            metadata=result.metadata or {}
        )
        
        with self._lock:
            # 添加记录
            self.records.append(record)
            
            # 限制记录数量
            if len(self.records) > self.max_records:
                self.records = self.records[-self.max_records:]
            
            # 更新统计信息
            self.global_stats.update(record)
            
            # 持久化
            if self.enable_persistence:
                self._save_stats()
        
        logger.debug(f"记录执行结果: {result.workflow_name or 'unknown'}, 成功: {result.success}")
    
    def record_batch_execution(self, results: List[WorkflowExecutionResult]) -> None:
        """记录批量执行结果
        
        Args:
            results: 批量执行结果列表
        """
        for workflow_result in results:
            self.record_execution(workflow_result)
    
    def get_global_statistics(self) -> GlobalStatistics:
        """获取全局统计信息
        
        Returns:
            GlobalStatistics: 全局统计信息
        """
        with self._lock:
            return self.global_stats
    
    def get_workflow_statistics(self, workflow_name: str) -> Optional[WorkflowStatistics]:
        """获取工作流统计信息
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            Optional[WorkflowStatistics]: 工作流统计信息
        """
        with self._lock:
            return self.global_stats.workflow_stats.get(workflow_name)
    
    def get_period_statistics(
        self,
        period: StatisticPeriod,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取周期统计信息
        
        Args:
            period: 统计周期
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            Dict[str, Any]: 周期统计信息
        """
        with self._lock:
            # 过滤记录
            filtered_records = self._filter_records_by_period(period, start_time, end_time)
            
            if not filtered_records:
                return {
                    "period": period.value,
                    "start_time": start_time.isoformat() if start_time else None,
                    "end_time": end_time.isoformat() if end_time else None,
                    "total_executions": 0,
                    "successful_executions": 0,
                    "failed_executions": 0,
                    "success_rate": 0.0,
                    "average_execution_time": 0.0
                }
            
            # 计算统计信息
            total_executions = len(filtered_records)
            successful_executions = sum(1 for r in filtered_records if r.success)
            failed_executions = total_executions - successful_executions
            success_rate = successful_executions / total_executions if total_executions > 0 else 0.0
            
            successful_records = [r for r in filtered_records if r.success]
            average_execution_time = (
                sum(r.execution_time for r in successful_records) / len(successful_records)
                if successful_records else 0.0
            )
            
            return {
                "period": period.value,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "total_executions": total_executions,
                "successful_executions": successful_executions,
                "failed_executions": failed_executions,
                "success_rate": success_rate,
                "average_execution_time": average_execution_time,
                "min_execution_time": min(r.execution_time for r in successful_records) if successful_records else None,
                "max_execution_time": max(r.execution_time for r in successful_records) if successful_records else None
            }
    
    def get_top_workflows(
        self,
        metric: str = "total_executions",
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """获取排名前N的工作流
        
        Args:
            metric: 排序指标
            limit: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 工作流排名列表
        """
        with self._lock:
            workflows = []
            
            for workflow_name, stats in self.global_stats.workflow_stats.items():
                workflows.append({
                    "workflow_name": workflow_name,
                    "total_executions": stats.total_executions,
                    "success_rate": stats.success_rate,
                    "average_execution_time": stats.average_execution_time,
                    "last_execution_time": stats.last_execution_time
                })
            
            # 排序
            if metric in ["total_executions", "success_rate", "average_execution_time"]:
                # 使用类型转换确保类型安全
                def sort_key(x: Dict[str, Any]) -> Union[int, float]:
                    value = x[metric]
                    # 确保返回的是支持比较的类型
                    if isinstance(value, (int, float)):
                        return value
                    return 0.0
                
                workflows.sort(key=sort_key, reverse=True)
            
            return workflows[:limit]
    
    def get_recent_executions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取最近的执行记录
        
        Args:
            limit: 返回数量
            
        Returns:
            List[Dict[str, Any]]: 执行记录列表
        """
        with self._lock:
            recent_records = sorted(self.records, key=lambda r: r.end_time, reverse=True)[:limit]
            return [record.to_dict() for record in recent_records]
    
    def reset_statistics(self, workflow_name: Optional[str] = None) -> None:
        """重置统计信息
        
        Args:
            workflow_name: 工作流名称，如果为None则重置所有统计
        """
        with self._lock:
            if workflow_name:
                # 重置特定工作流统计
                if workflow_name in self.global_stats.workflow_stats:
                    self.global_stats.workflow_stats[workflow_name] = WorkflowStatistics(
                        workflow_name=workflow_name
                    )
                
                # 移除相关记录
                self.records = [r for r in self.records if r.workflow_name != workflow_name]
            else:
                # 重置所有统计
                self.global_stats = GlobalStatistics()
                self.records.clear()
            
            # 持久化
            if self.enable_persistence:
                self._save_stats()
        
        logger.info(f"重置统计信息: {workflow_name or '全部'}")
    
    def export_statistics(self, file_path: str) -> None:
        """导出统计信息
        
        Args:
            file_path: 导出文件路径
        """
        with self._lock:
            data = {
                "export_time": datetime.now().isoformat(),
                "global_statistics": self.global_stats.to_dict(),
                "recent_executions": self.get_recent_executions(100)
            }
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"统计信息已导出到: {file_path}")
    
    def _filter_records_by_period(
        self,
        period: StatisticPeriod,
        start_time: Optional[datetime],
        end_time: Optional[datetime]
    ) -> List[ExecutionRecord]:
        """按周期过滤记录
        
        Args:
            period: 统计周期
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[ExecutionRecord]: 过滤后的记录
        """
        now = datetime.now()
        
        if start_time is None or end_time is None:
            if period == StatisticPeriod.REALTIME:
                start_time = now - timedelta(hours=1)
                end_time = now
            elif period == StatisticPeriod.HOURLY:
                start_time = now.replace(minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(hours=1)
            elif period == StatisticPeriod.DAILY:
                start_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=1)
            elif period == StatisticPeriod.WEEKLY:
                start_time = now - timedelta(days=now.weekday())
                start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(weeks=1)
            elif period == StatisticPeriod.MONTHLY:
                start_time = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                end_time = start_time + timedelta(days=31)
        
        # 过滤记录
        return [
            record for record in self.records
            if start_time <= record.end_time < end_time
        ]
    
    def _load_stats(self) -> None:
        """加载持久化统计信息"""
        try:
            if Path(self.persistence_path).exists():
                with open(self.persistence_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 恢复全局统计
                if "global_statistics" in data:
                    global_data = data["global_statistics"]
                    self.global_stats = GlobalStatistics(
                        total_workflows=global_data.get("total_workflows", 0),
                        total_executions=global_data.get("total_executions", 0),
                        total_successful_executions=global_data.get("total_successful_executions", 0),
                        total_failed_executions=global_data.get("total_failed_executions", 0),
                        total_execution_time=global_data.get("total_execution_time", 0.0),
                        period_stats=global_data.get("period_stats", {})
                    )
                    
                    # 恢复工作流统计
                    for workflow_name, workflow_data in global_data.get("workflow_stats", {}).items():
                        stats = WorkflowStatistics(workflow_name=workflow_name)
                        stats.total_executions = workflow_data.get("total_executions", 0)
                        stats.successful_executions = workflow_data.get("successful_executions", 0)
                        stats.failed_executions = workflow_data.get("failed_executions", 0)
                        stats.total_execution_time = workflow_data.get("total_execution_time", 0.0)
                        stats.min_execution_time = workflow_data.get("min_execution_time")
                        stats.max_execution_time = workflow_data.get("max_execution_time")
                        stats.error_types = workflow_data.get("error_types", {})
                        
                        if workflow_data.get("last_execution_time"):
                            stats.last_execution_time = datetime.fromisoformat(workflow_data["last_execution_time"])
                        if workflow_data.get("last_success_time"):
                            stats.last_success_time = datetime.fromisoformat(workflow_data["last_success_time"])
                        if workflow_data.get("last_failure_time"):
                            stats.last_failure_time = datetime.fromisoformat(workflow_data["last_failure_time"])
                        
                        self.global_stats.workflow_stats[workflow_name] = stats
                
                logger.debug(f"加载统计信息完成: {len(self.global_stats.workflow_stats)} 个工作流")
            
        except Exception as e:
            logger.error(f"加载统计信息失败: {e}")
    
    def _save_stats(self) -> None:
        """保存持久化统计信息"""
        try:
            Path(self.persistence_path).parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "last_updated": datetime.now().isoformat(),
                "global_statistics": self.global_stats.to_dict()
            }
            
            with open(self.persistence_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"保存统计信息失败: {e}")


# 全局统计收集器实例
_global_stats_collector: Optional[ExecutionStatsCollector] = None


def get_global_stats_collector() -> ExecutionStatsCollector:
    """获取全局统计收集器
    
    Returns:
        ExecutionStatsCollector: 全局统计收集器
    """
    global _global_stats_collector
    if _global_stats_collector is None:
        _global_stats_collector = ExecutionStatsCollector()
    return _global_stats_collector


def record_execution(result: WorkflowExecutionResult) -> None:
    """记录执行结果（便捷函数）
    
    Args:
        result: 工作流执行结果
    """
    collector = get_global_stats_collector()
    collector.record_execution(result)


def record_batch_execution(results: List[WorkflowExecutionResult]) -> None:
    """记录批量执行结果（便捷函数）
    
    Args:
        results: 批量执行结果列表
    """
    collector = get_global_stats_collector()
    collector.record_batch_execution(results)