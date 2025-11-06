"""工作流性能监控器

专门用于监控工作流节点执行的性能指标，使用零内存存储。
"""

from typing import Optional

from ..lightweight_monitor import LightweightPerformanceMonitor
from ..logger_writer import PerformanceMetricsLogger


class WorkflowPerformanceMonitor(LightweightPerformanceMonitor):
    """工作流性能监控器 - 零内存存储版本"""
    
    def __init__(self, logger: Optional[PerformanceMetricsLogger] = None):
        """初始化工作流性能监控器
        
        Args:
            logger: 性能指标日志写入器，如果为None则创建默认实例
        """
        super().__init__(logger or PerformanceMetricsLogger("workflow_metrics"))
    
    def record_node_execution(self,
                             node_type: str,
                             execution_time: float,
                             success: bool = True,
                             error_type: Optional[str] = None) -> None:
        """记录节点执行
        
        Args:
            node_type: 节点类型
            execution_time: 执行时间（秒）
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        self.logger.log_workflow_node_execution(
            node_type=node_type,
            execution_time=execution_time,
            success=success,
            error_type=error_type
        )
    
    def record_graph_execution(self,
                              graph_name: str,
                              total_time: float,
                              node_count: int,
                              success: bool = True) -> None:
        """记录图执行
        
        Args:
            graph_name: 图名称
            total_time: 总执行时间（秒）
            node_count: 节点数量
            success: 是否成功
        """
        # 记录图执行时间
        self.logger.log_timer(
            "graph_execution",
            total_time,
            {"graph_name": graph_name, "node_count": str(node_count)}
        )
        
        # 记录节点数量
        self.logger.log_gauge(
            "graph_node_count",
            node_count,
            {"graph_name": graph_name}
        )
        
        # 记录成功/失败计数
        if success:
            self.logger.log_counter(
                "graph_success",
                1.0,
                {"graph_name": graph_name}
            )
        else:
            self.logger.log_counter(
                "graph_failure",
                1.0,
                {"graph_name": graph_name}
            )