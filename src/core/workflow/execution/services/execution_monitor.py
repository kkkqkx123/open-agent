"""执行监控器

提供工作流执行的监控和性能分析服务。
"""

from src.interfaces.dependency_injection import get_logger
import time
import threading
from typing import Dict, Any, Optional, List, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict, deque

if TYPE_CHECKING:
    from ..core.execution_context import ExecutionContext, ExecutionResult

logger = get_logger(__name__)


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"          # 计数器
    GAUGE = "gauge"              # 仪表盘
    HISTOGRAM = "histogram"      # 直方图
    TIMER = "timer"              # 计时器


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"                # 信息
    WARNING = "warning"          # 警告
    ERROR = "error"              # 错误
    CRITICAL = "critical"        # 严重


@dataclass
class Metric:
    """监控指标"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime = field(default_factory=datetime.now)
    labels: Dict[str, str] = field(default_factory=dict)
    unit: str = ""
    description: str = ""


@dataclass
class Alert:
    """告警信息"""
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    execution_id: Optional[str] = None
    workflow_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PerformanceReport:
    """性能报告"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    start_time: datetime
    end_time: Optional[datetime]
    total_time: float
    node_count: int
    success: bool
    metrics: Dict[str, Any] = field(default_factory=dict)
    alerts: List[Alert] = field(default_factory=list)


class IExecutionMonitor:
    """执行监控器接口"""
    pass


class ExecutionMonitor(IExecutionMonitor):
    """执行监控器
    
    提供工作流执行的实时监控、性能分析和告警功能。
    """
    
    def __init__(
        self, 
        max_history: int = 1000,
        alert_thresholds: Optional[Dict[str, float]] = None
    ):
        """初始化执行监控器
        
        Args:
            max_history: 最大历史记录数
            alert_thresholds: 告警阈值配置
        """
        self.max_history = max_history
        self.alert_thresholds = alert_thresholds or {
            "execution_time": 300.0,      # 执行时间超过5分钟
            "error_rate": 0.1,           # 错误率超过10%
            "memory_usage": 0.8,         # 内存使用率超过80%
            "cpu_usage": 0.9             # CPU使用率超过90%
        }
        
        # 监控数据存储
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._alerts: deque = deque(maxlen=max_history)
        self._performance_reports: deque = deque(maxlen=max_history)
        
        # 统计数据
        self._statistics = {
            "total_executions": 0,
            "successful_executions": 0,
            "failed_executions": 0,
            "total_execution_time": 0.0,
            "average_execution_time": 0.0,
            "error_rate": 0.0
        }
        
        # 告警回调
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 监控锁
        self._lock = threading.RLock()
        
        logger.debug("执行监控器初始化完成")
    
    def start_execution_monitoring(self, context: 'ExecutionContext') -> None:
        """开始执行监控
        
        Args:
            context: 执行上下文
        """
        with self._lock:
            # 记录执行开始
            self._record_metric("execution_started", 1.0, MetricType.COUNTER, {
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id
            })
            
            logger.debug(f"开始监控执行: {context.execution_id}")
    
    def end_execution_monitoring(
        self, 
        context: 'ExecutionContext', 
        result: 'ExecutionResult'
    ) -> None:
        """结束执行监控
        
        Args:
            context: 执行上下文
            result: 执行结果
        """
        with self._lock:
            # 记录执行结束
            self._record_metric("execution_completed", 1.0, MetricType.COUNTER, {
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id,
                "success": str(result.success)
            })
            
            # 记录执行时间
            if result.execution_time:
                self._record_metric("execution_time", result.execution_time, MetricType.TIMER, {
                    "workflow_id": context.workflow_id,
                    "execution_id": context.execution_id
                })
            
            # 更新统计
            self._update_statistics(result)
            
            # 生成性能报告
            report = self._generate_performance_report(context, result)
            self._performance_reports.append(report)
            
            # 检查告警
            self._check_alerts(context, result)
            
            logger.debug(f"结束监控执行: {context.execution_id}, 成功: {result.success}")
    
    def record_node_execution(
        self, 
        context: 'ExecutionContext', 
        node_id: str, 
        node_type: str, 
        execution_time: float, 
        success: bool
    ) -> None:
        """记录节点执行
        
        Args:
            context: 执行上下文
            node_id: 节点ID
            node_type: 节点类型
            execution_time: 执行时间
            success: 是否成功
        """
        with self._lock:
            # 记录节点执行指标
            self._record_metric("node_execution_time", execution_time, MetricType.TIMER, {
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id,
                "node_id": node_id,
                "node_type": node_type
            })
            
            self._record_metric("node_executed", 1.0, MetricType.COUNTER, {
                "workflow_id": context.workflow_id,
                "execution_id": context.execution_id,
                "node_id": node_id,
                "node_type": node_type,
                "success": str(success)
            })
    
    def record_custom_metric(
        self, 
        name: str, 
        value: float, 
        metric_type: MetricType,
        labels: Optional[Dict[str, str]] = None
    ) -> None:
        """记录自定义指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            labels: 标签
        """
        with self._lock:
            self._record_metric(name, value, metric_type, labels or {})
    
    def add_alert_callback(self, callback: Callable[[Alert], None]) -> None:
        """添加告警回调
        
        Args:
            callback: 告警回调函数
        """
        self._alert_callbacks.append(callback)
        logger.debug("告警回调已添加")
    
    def get_metrics(
        self, 
        name: Optional[str] = None, 
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Metric]:
        """获取监控指标
        
        Args:
            name: 指标名称
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Metric]: 指标列表
        """
        with self._lock:
            metrics = []
            
            if name:
                if name in self._metrics:
                    metrics.extend(self._filter_metrics_by_time(self._metrics[name], start_time, end_time))
            else:
                for metric_list in self._metrics.values():
                    metrics.extend(self._filter_metrics_by_time(metric_list, start_time, end_time))
            
            return sorted(metrics, key=lambda m: m.timestamp, reverse=True)
    
    def get_alerts(
        self, 
        level: Optional[AlertLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Alert]:
        """获取告警信息
        
        Args:
            level: 告警级别
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Alert]: 告警列表
        """
        with self._lock:
            alerts = list(self._alerts)
            
            # 过滤级别
            if level:
                alerts = [a for a in alerts if a.level == level]
            
            # 过滤时间
            alerts = self._filter_alerts_by_time(alerts, start_time, end_time)
            
            return sorted(alerts, key=lambda a: a.timestamp, reverse=True)
    
    def get_performance_reports(
        self, 
        workflow_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[PerformanceReport]:
        """获取性能报告
        
        Args:
            workflow_id: 工作流ID
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[PerformanceReport]: 性能报告列表
        """
        with self._lock:
            reports = list(self._performance_reports)
            
            # 过滤工作流ID
            if workflow_id:
                reports = [r for r in reports if r.workflow_id == workflow_id]
            
            # 过滤时间
            reports = self._filter_reports_by_time(reports, start_time, end_time)
            
            return sorted(reports, key=lambda r: r.start_time, reverse=True)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        with self._lock:
            stats = self._statistics.copy()
            
            # 计算错误率
            if stats["total_executions"] > 0:
                stats["error_rate"] = stats["failed_executions"] / stats["total_executions"]
            else:
                stats["error_rate"] = 0.0
            
            # 添加监控统计
            stats["monitoring"] = {
                "total_metrics": sum(len(metrics) for metrics in self._metrics.values()),
                "total_alerts": len(self._alerts),
                "total_reports": len(self._performance_reports),
                "metric_types": list(self._metrics.keys())
            }
            
            return stats
    
    def _record_metric(
        self, 
        name: str, 
        value: float, 
        metric_type: MetricType,
        labels: Dict[str, str]
    ) -> None:
        """记录指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            labels: 标签
        """
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels
        )
        
        self._metrics[name].append(metric)
    
    def _update_statistics(self, result: 'ExecutionResult') -> None:
        """更新统计信息
        
        Args:
            result: 执行结果
        """
        self._statistics["total_executions"] += 1
        
        if result.success:
            self._statistics["successful_executions"] += 1
        else:
            self._statistics["failed_executions"] += 1
        
        if result.execution_time:
            self._statistics["total_execution_time"] += result.execution_time
            self._statistics["average_execution_time"] = (
                self._statistics["total_execution_time"] / self._statistics["total_executions"]
            )
    
    def _generate_performance_report(
        self, 
        context: 'ExecutionContext', 
        result: 'ExecutionResult'
    ) -> PerformanceReport:
        """生成性能报告
        
        Args:
            context: 执行上下文
            result: 执行结果
            
        Returns:
            PerformanceReport: 性能报告
        """
        # 收集相关指标
        execution_metrics = self.get_metrics(
            start_time=context.start_time,
            end_time=context.end_time
        )
        
        # 计算性能指标
        metrics = {
            "total_nodes": result.total_nodes,
            "successful_nodes": len(result.successful_nodes),
            "failed_nodes": len(result.failed_nodes),
            "node_success_rate": result.success_rate,
            "average_node_time": 0.0
        }
        
        # 计算平均节点执行时间
        node_times = [
            m.value for m in execution_metrics 
            if m.name == "node_execution_time" and m.labels.get("execution_id") == context.execution_id
        ]
        if node_times:
            metrics["average_node_time"] = sum(node_times) / len(node_times)
        
        return PerformanceReport(
            execution_id=context.execution_id,
            workflow_id=context.workflow_id,
            workflow_name=result.metadata.get("workflow_name", "unknown"),
            start_time=context.start_time or datetime.now(),
            end_time=context.end_time,
            total_time=result.execution_time or 0.0,
            node_count=result.total_nodes,
            success=result.success,
            metrics=metrics,
            alerts=[]
        )
    
    def _check_alerts(
        self, 
        context: 'ExecutionContext', 
        result: 'ExecutionResult'
    ) -> None:
        """检查告警
        
        Args:
            context: 执行上下文
            result: 执行结果
        """
        alerts = []
        
        # 检查执行时间告警
        if result.execution_time and result.execution_time > self.alert_thresholds["execution_time"]:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"执行时间过长: {result.execution_time:.2f}秒",
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                metadata={"execution_time": result.execution_time}
            ))
        
        # 检查错误率告警
        if not result.success:
            error_rate = 1.0 - result.success_rate
            if error_rate > self.alert_thresholds["error_rate"]:
                alerts.append(Alert(
                    level=AlertLevel.ERROR,
                    message=f"错误率过高: {error_rate:.2%}",
                    execution_id=context.execution_id,
                    workflow_id=context.workflow_id,
                    metadata={"error_rate": error_rate}
                ))
        
        # 检查节点失败告警
        if len(result.failed_nodes) > 0:
            alerts.append(Alert(
                level=AlertLevel.WARNING,
                message=f"节点执行失败: {result.failed_nodes}个节点",
                execution_id=context.execution_id,
                workflow_id=context.workflow_id,
                metadata={"failed_nodes": result.failed_nodes}
            ))
        
        # 添加告警并触发回调
        for alert in alerts:
            self._alerts.append(alert)
            self._trigger_alert_callbacks(alert)
    
    def _trigger_alert_callbacks(self, alert: Alert) -> None:
        """触发告警回调
        
        Args:
            alert: 告警信息
        """
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
    
    def _filter_metrics_by_time(
        self, 
        metrics: deque, 
        start_time: Optional[datetime], 
        end_time: Optional[datetime]
    ) -> List[Metric]:
        """按时间过滤指标
        
        Args:
            metrics: 指标队列
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Metric]: 过滤后的指标列表
        """
        filtered = list(metrics)
        
        if start_time:
            filtered = [m for m in filtered if m.timestamp >= start_time]
        
        if end_time:
            filtered = [m for m in filtered if m.timestamp <= end_time]
        
        return filtered
    
    def _filter_alerts_by_time(
        self, 
        alerts: List[Alert], 
        start_time: Optional[datetime], 
        end_time: Optional[datetime]
    ) -> List[Alert]:
        """按时间过滤告警
        
        Args:
            alerts: 告警列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[Alert]: 过滤后的告警列表
        """
        filtered = alerts
        
        if start_time:
            filtered = [a for a in filtered if a.timestamp >= start_time]
        
        if end_time:
            filtered = [a for a in filtered if a.timestamp <= end_time]
        
        return filtered
    
    def _filter_reports_by_time(
        self, 
        reports: List[PerformanceReport], 
        start_time: Optional[datetime], 
        end_time: Optional[datetime]
    ) -> List[PerformanceReport]:
        """按时间过滤性能报告
        
        Args:
            reports: 性能报告列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[PerformanceReport]: 过滤后的性能报告列表
        """
        filtered = reports
        
        if start_time:
            filtered = [r for r in filtered if r.start_time >= start_time]
        
        if end_time:
            filtered = [r for r in filtered if r.start_time <= end_time]
        
        return filtered
    
    def reset_monitoring_data(self) -> None:
        """重置监控数据"""
        with self._lock:
            self._metrics.clear()
            self._alerts.clear()
            self._performance_reports.clear()
            self._statistics = {
                "total_executions": 0,
                "successful_executions": 0,
                "failed_executions": 0,
                "total_execution_time": 0.0,
                "average_execution_time": 0.0,
                "error_rate": 0.0
            }
        
        logger.debug("监控数据已重置")