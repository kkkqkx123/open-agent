"""工具性能监控器

专门用于监控工具执行的性能指标，使用零内存存储。
"""

from typing import Optional

from ..lightweight_monitor import LightweightPerformanceMonitor
from ..logger_writer import PerformanceMetricsLogger


class ToolPerformanceMonitor(LightweightPerformanceMonitor):
    """工具性能监控器 - 零内存存储版本"""
    
    def __init__(self, logger: Optional[PerformanceMetricsLogger] = None):
        """初始化工具性能监控器
        
        Args:
            logger: 性能指标日志写入器，如果为None则创建默认实例
        """
        super().__init__(logger or PerformanceMetricsLogger("tool_metrics"))
    
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
        self.logger.log_tool_execution(
            tool_name=tool_name,
            execution_time=execution_time,
            success=success,
            error_type=error_type
        )
    
    def record_tool_usage(self, tool_name: str) -> None:
        """记录工具使用
        
        Args:
            tool_name: 工具名称
        """
        # 记录使用计数
        self.logger.log_counter(
            "tool_usage",
            1.0,
            {"tool_name": tool_name}
        )