"""工作流性能监控器

专门用于监控工作流节点执行的性能指标。
"""

from typing import Optional, Dict, Any

from ..base_monitor import BasePerformanceMonitor


class WorkflowPerformanceMonitor(BasePerformanceMonitor):
    """工作流性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        """初始化工作流性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
        """
        super().__init__(max_history_size)
        self._config.update({
            "module": "workflow",
            "description": "工作流性能监控"
        })
    
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
        labels = {"node_type": node_type}
        
        # 记录执行时间
        self.record_timer("workflow.node.execution_time", execution_time, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("workflow.node.success", 1, labels)
        else:
            self.increment_counter("workflow.node.failure", 1, labels)
            
            # 如果有错误类型，记录错误类型计数
            if error_type:
                error_labels = {"node_type": node_type, "error_type": error_type}
                self.increment_counter("workflow.node.errors", 1, error_labels)
    
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
        labels = {"graph_name": graph_name}
        
        # 记录总执行时间
        self.record_timer("workflow.graph.total_time", total_time, labels)
        
        # 记录节点数量
        self.set_gauge("workflow.graph.node_count", node_count, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("workflow.graph.success", 1, labels)
        else:
            self.increment_counter("workflow.graph.failure", 1, labels)