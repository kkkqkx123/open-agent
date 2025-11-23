"""性能分析面板组件

包含性能指标收集、分析和可视化功能
"""

from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path
import statistics

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.progress import Progress, BarColumn, TextColumn
from rich.layout import Layout
from rich.columns import Columns

from ..config import TUIConfig


class MetricType(Enum):
    """指标类型枚举"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class PerformanceMetric:
    """性能指标"""
    
    def __init__(
        self,
        name: str,
        metric_type: MetricType,
        value: float,
        timestamp: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ):
        self.name = name
        self.metric_type = metric_type
        self.value = value
        self.timestamp = timestamp or datetime.now()
        self.labels = labels or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            Dict[str, Any]: 指标字典
        """
        return {
            "name": self.name,
            "metric_type": self.metric_type.value,
            "value": self.value,
            "timestamp": self.timestamp.isoformat(),
            "labels": self.labels
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PerformanceMetric":
        """从字典创建指标
        
        Args:
            data: 指标字典
            
        Returns:
            PerformanceMetric: 性能指标
        """
        return cls(
            name=data["name"],
            metric_type=MetricType(data["metric_type"]),
            value=data["value"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            labels=data.get("labels", {})
        )


class PerformanceData:
    """性能数据"""
    
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.metrics: List[PerformanceMetric] = []
        self.start_time = datetime.now()
        self.end_time: Optional[datetime] = None
    
    def add_metric(self, metric: PerformanceMetric) -> None:
        """添加指标
        
        Args:
            metric: 性能指标
        """
        self.metrics.append(metric)
    
    def get_metrics_by_name(self, name: str) -> List[PerformanceMetric]:
        """根据名称获取指标
        
        Args:
            name: 指标名称
            
        Returns:
            List[PerformanceMetric]: 指标列表
        """
        return [metric for metric in self.metrics if metric.name == name]
    
    def get_metrics_in_range(self, start_time: datetime, end_time: datetime) -> List[PerformanceMetric]:
        """获取时间范围内的指标
        
        Args:
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[PerformanceMetric]: 指标列表
        """
        return [
            metric for metric in self.metrics
            if start_time <= metric.timestamp <= end_time
        ]
    
    def get_metric_statistics(self, name: str) -> Dict[str, float]:
        """获取指标统计信息
        
        Args:
            name: 指标名称
            
        Returns:
            Dict[str, float]: 统计信息
        """
        metrics = self.get_metrics_by_name(name)
        if not metrics:
            return {}
        
        values = [metric.value for metric in metrics]
        
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "mean": statistics.mean(values),
            "median": statistics.median(values),
            "stdev": statistics.stdev(values) if len(values) > 1 else 0.0
        }
    
    def finalize(self) -> None:
        """完成数据收集"""
        self.end_time = datetime.now()


class PerformanceAnalyzer:
    """性能分析器"""
    
    def __init__(self):
        self.data: Dict[str, PerformanceData] = {}
        self.current_session: Optional[str] = None
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # 回调函数
        self.on_metric_added: Optional[Callable[[PerformanceMetric], None]] = None
        self.on_analysis_completed: Optional[Callable[[str, Dict[str, Any]], None]] = None
    
    def set_metric_added_callback(self, callback: Callable[[PerformanceMetric], None]) -> None:
        """设置指标添加回调
        
        Args:
            callback: 回调函数
        """
        self.on_metric_added = callback
    
    def set_analysis_completed_callback(self, callback: Callable[[str, Dict[str, Any]], None]) -> None:
        """设置分析完成回调
        
        Args:
            callback: 回调函数
        """
        self.on_analysis_completed = callback
    
    def start_session(self, session_id: str) -> None:
        """开始会话
        
        Args:
            session_id: 会话ID
        """
        self.current_session = session_id
        self.data[session_id] = PerformanceData(session_id)
    
    def end_session(self, session_id: Optional[str] = None) -> None:
        """结束会话
        
        Args:
            session_id: 会话ID
        """
        session_id = session_id or self.current_session
        if session_id and session_id in self.data:
            self.data[session_id].finalize()
        
        if session_id == self.current_session:
            self.current_session = None
    
    def add_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        labels: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None
    ) -> None:
        """添加指标
        
        Args:
            name: 指标名称
            value: 指标值
            metric_type: 指标类型
            labels: 标签
            session_id: 会话ID
        """
        session_id = session_id or self.current_session
        if not session_id or session_id not in self.data:
            return
        
        metric = PerformanceMetric(name, metric_type, value, labels=labels)
        self.data[session_id].add_metric(metric)
        
        if self.on_metric_added:
            self.on_metric_added(metric)
    
    def increment_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """递增计数器
        
        Args:
            name: 指标名称
            value: 递增值
            labels: 标签
        """
        self.add_metric(name, value, MetricType.COUNTER, labels)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表盘值
        
        Args:
            name: 指标名称
            value: 指标值
            labels: 标签
        """
        self.add_metric(name, value, MetricType.GAUGE, labels)
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器
        
        Args:
            name: 指标名称
            duration: 持续时间
            labels: 标签
        """
        self.add_metric(name, duration, MetricType.TIMER, labels)
    
    def analyze_session(self, session_id: str) -> Dict[str, Any]:
        """分析会话性能
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if session_id not in self.data:
            return {}
        
        # 检查缓存
        cache_key = f"{session_id}_{self.data[session_id].end_time or datetime.now().isoformat()}"
        if cache_key in self.analysis_cache:
            return self.analysis_cache[cache_key]
        
        data = self.data[session_id]
        analysis = {
            "session_id": session_id,
            "start_time": data.start_time.isoformat(),
            "end_time": data.end_time.isoformat() if data.end_time else None,
            "duration": (data.end_time - data.start_time).total_seconds() if data.end_time else 0,
            "total_metrics": len(data.metrics),
            "metric_summary": {},
            "performance_issues": [],
            "recommendations": []
        }
        
        # 按指标类型分组分析
        metric_groups = {}
        for metric in data.metrics:
            if metric.name not in metric_groups:
                metric_groups[metric.name] = []
            metric_groups[metric.name].append(metric)
        
        # 分析每个指标
        for name, metrics in metric_groups.items():
            stats = data.get_metric_statistics(name)
            analysis["metric_summary"][name] = {
                "type": metrics[0].metric_type.value,
                "count": len(metrics),
                "statistics": stats
            }
            
            # 性能问题检测
            if metrics[0].metric_type == MetricType.TIMER:
                if stats.get("mean", 0) > 5.0:  # 超过5秒
                    analysis["performance_issues"].append({
                        "type": "slow_operation",
                        "metric": name,
                        "value": stats["mean"],
                        "threshold": 5.0
                    })
                    analysis["recommendations"].append(f"优化 {name} 操作，平均耗时 {stats['mean']:.2f} 秒")
            
            elif metrics[0].metric_type == MetricType.COUNTER:
                if stats.get("count", 0) > 1000:  # 超过1000次调用
                    analysis["performance_issues"].append({
                        "type": "high_frequency",
                        "metric": name,
                        "value": stats["count"],
                        "threshold": 1000
                    })
                    analysis["recommendations"].append(f"考虑缓存 {name} 操作，调用次数 {stats['count']}")
        
        # 缓存分析结果
        self.analysis_cache[cache_key] = analysis
        
        if self.on_analysis_completed:
            self.on_analysis_completed(session_id, analysis)
        
        return analysis
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """获取会话摘要
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话摘要
        """
        if session_id not in self.data:
            return {}
        
        data = self.data[session_id]
        
        # 计算关键指标
        total_duration = 0
        operation_count = 0
        error_count = 0
        
        for metric in data.metrics:
            if metric.name == "operation_duration":
                total_duration += metric.value
                operation_count += 1
            elif metric.name == "error_count":
                error_count += metric.value
        
        return {
            "session_id": session_id,
            "duration": (data.end_time - data.start_time).total_seconds() if data.end_time else 0,
            "total_operations": operation_count,
            "total_duration": total_duration,
            "average_operation_time": total_duration / operation_count if operation_count > 0 else 0,
            "error_count": error_count,
            "error_rate": (error_count / operation_count * 100) if operation_count > 0 else 0
        }


class PerformanceAnalyzerPanel:
    """性能分析面板组件"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.analyzer = PerformanceAnalyzer()
        self.show_details = False
        self.selected_session: Optional[str] = None
        self.auto_refresh = True
        
        # 设置回调
        self.analyzer.set_analysis_completed_callback(self._on_analysis_completed)
        
        # 外部回调
        self.on_performance_action: Optional[Callable[[str, Any], None]] = None
    
    def set_performance_action_callback(self, callback: Callable[[str, Any], None]) -> None:
        """设置性能动作回调
        
        Args:
            callback: 回调函数
        """
        self.on_performance_action = callback
    
    def _on_analysis_completed(self, session_id: str, analysis: Dict[str, Any]) -> None:
        """分析完成处理
        
        Args:
            session_id: 会话ID
            analysis: 分析结果
        """
        if self.on_performance_action:
            self.on_performance_action("analysis_completed", {
                "session_id": session_id,
                "analysis": analysis
            })
    
    def toggle_details(self) -> None:
        """切换详情显示"""
        self.show_details = not self.show_details
    
    def select_session(self, session_id: str) -> None:
        """选择会话
        
        Args:
            session_id: 会话ID
        """
        self.selected_session = session_id
    
    def start_monitoring(self, session_id: str) -> None:
        """开始监控
        
        Args:
            session_id: 会话ID
        """
        self.analyzer.start_session(session_id)
    
    def stop_monitoring(self, session_id: Optional[str] = None) -> None:
        """停止监控
        
        Args:
            session_id: 会话ID
        """
        self.analyzer.end_session(session_id)
    
    def record_operation(self, operation: str, duration: float) -> None:
        """记录操作
        
        Args:
            operation: 操作名称
            duration: 持续时间
        """
        self.analyzer.record_timer(f"{operation}_duration", duration)
        self.analyzer.increment_counter(f"{operation}_count")
    
    def record_error(self, error_type: str) -> None:
        """记录错误
        
        Args:
            error_type: 错误类型
        """
        self.analyzer.increment_counter(f"{error_type}_error")
        self.analyzer.increment_counter("total_error")
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if key == "d":
            self.toggle_details()
        elif key == "a":
            self.analyze_current_session()
        elif key == "r":
            self.toggle_auto_refresh()
        
        return None
    
    def analyze_current_session(self) -> Optional[Dict[str, Any]]:
        """分析当前会话
        
        Returns:
            Optional[Dict[str, Any]]: 分析结果
        """
        if self.selected_session:
            return self.analyzer.analyze_session(self.selected_session)
        return None
    
    def toggle_auto_refresh(self) -> None:
        """切换自动刷新"""
        self.auto_refresh = not self.auto_refresh
    
    def render(self) -> Panel:
        """渲染分析面板
        
        Returns:
            Panel: 分析面板
        """
        if self.show_details and self.selected_session:
            content = self._render_detailed_analysis()
        else:
            content = self._render_summary()
        
        return Panel(
            content,
            title="性能分析器 (D=详情, A=分析, R=自动刷新)",
            border_style="green",
            padding=(1, 1)
        )
    
    def _render_summary(self) -> Table:
        """渲染摘要信息
        
        Returns:
            Table: 摘要表格
        """
        table = Table.grid()
        table.add_column()
        
        # 获取所有会话
        sessions = list(self.analyzer.data.keys())
        
        if not sessions:
            table.add_row("无性能数据")
            return table
        
        # 显示会话列表
        summary_text = Text()
        summary_text.append("会话列表:\\n", style="bold")
        
        for session_id in sessions[:5]:  # 显示前5个会话
            summary = self.analyzer.get_session_summary(session_id)
            session_display = session_id[:8] + "..."
            
            marker = "●" if session_id == self.selected_session else "○"
            summary_text.append(f"{marker} {session_display}\\n")
            summary_text.append(f"  操作: {summary['total_operations']}, ")
            summary_text.append(f"错误: {summary['error_count']}, ")
            summary_text.append(f"平均耗时: {summary['average_operation_time']:.2f}s\\n")
        
        # 自动刷新状态
        refresh_status = "开启" if self.auto_refresh else "关闭"
        summary_text.append(f"\\n自动刷新: {refresh_status}")
        
        table.add_row(summary_text)
        
        return table
    
    def _render_detailed_analysis(self) -> Table:
        """渲染详细分析
        
        Returns:
            Table: 详细分析表格
        """
        if not self.selected_session:
            table = Table.grid()
            table.add_row("请选择一个会话")
            return table
        
        analysis = self.analyzer.analyze_session(self.selected_session)
        
        if not analysis:
            table = Table.grid()
            table.add_row("无分析数据")
            return table
        
        # 创建分析表格
        table = Table.grid()
        table.add_column()
        
        # 基本信息
        info_text = Text()
        info_text.append(f"会话: {self.selected_session[:8]}...\\n", style="bold")
        info_text.append(f"持续时间: {analysis['duration']:.2f}秒\\n")
        info_text.append(f"总指标数: {analysis['total_metrics']}\\n\\n")
        
        # 性能问题
        if analysis["performance_issues"]:
            info_text.append("性能问题:\\n", style="bold red")
            for issue in analysis["performance_issues"]:
                info_text.append(f"• {issue['metric']}: {issue['value']:.2f}\\n")
            info_text.append("\\n")
        
        # 建议
        if analysis["recommendations"]:
            info_text.append("优化建议:\\n", style="bold yellow")
            for rec in analysis["recommendations"]:
                info_text.append(f"• {rec}\\n")
        
        table.add_row(info_text)
        
        return table