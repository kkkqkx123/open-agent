"""工具性能监控器

专门用于监控工具执行的性能指标。
"""

from typing import Optional, Dict, Any

from ..base_monitor import BasePerformanceMonitor


class ToolPerformanceMonitor(BasePerformanceMonitor):
    """工具性能监控器"""
    
    def __init__(self, max_history_size: int = 1000):
        """初始化工具性能监控器
        
        Args:
            max_history_size: 最大历史记录大小
        """
        super().__init__(max_history_size)
        self._config.update({
            "module": "tool",
            "description": "工具性能监控"
        })
    
    def record_tool_execution(self,
                            tool_name: str,
                            execution_time: float,
                            success: bool = True,
                            error_type: Optional[str] = None) -> None:
        """记录工具执行
        
        Args:
            tool_name: 工具名称
            execution_time: 执行时间（秒）
            success: 是否成功
            error_type: 错误类型（如果失败）
        """
        labels = {"tool_name": tool_name}
        
        # 记录执行时间
        self.record_timer("tool.execution_time", execution_time, labels)
        
        # 记录成功/失败计数
        if success:
            self.increment_counter("tool.success", 1, labels)
        else:
            self.increment_counter("tool.failure", 1, labels)
            
            # 如果有错误类型，记录错误类型计数
            if error_type:
                error_labels = {"tool_name": tool_name, "error_type": error_type}
                self.increment_counter("tool.errors", 1, error_labels)
    
    def record_tool_usage(self, tool_name: str) -> None:
        """记录工具使用
        
        Args:
            tool_name: 工具名称
        """
        labels = {"tool_name": tool_name}
        
        # 记录使用计数
        self.increment_counter("tool.usage", 1, labels)