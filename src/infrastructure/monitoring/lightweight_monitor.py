"""轻量级性能监控器

实现零内存存储的性能监控基类。
"""

from typing import Dict, Any, Optional
from .logger_writer import PerformanceMetricsLogger


class LightweightPerformanceMonitor:
    """轻量级性能监控器 - 零内存存储
    
    不保存任何状态，直接将指标写入日志。
    """
    
    def __init__(self, logger: Optional[PerformanceMetricsLogger] = None):
        """初始化轻量级监控器
        
        Args:
            logger: 性能指标日志写入器，如果为None则创建默认实例
        """
        self.logger = logger or PerformanceMetricsLogger()
    
    def record_timer(self, metric_name: str, value: float, 
                    labels: Optional[Dict[str, str]] = None) -> None:
        """记录计时器值
        
        Args:
            metric_name: 指标名称
            value: 时间值（秒）
            labels: 标签字典
        """
        self.logger.log_timer(metric_name, value, labels)
    
    def increment_counter(self, metric_name: str, value: float = 1.0,
                        labels: Optional[Dict[str, str]] = None) -> None:
        """增加计数器值
        
        Args:
            metric_name: 指标名称
            value: 增加的值，默认为1.0
            labels: 标签字典
        """
        self.logger.log_counter(metric_name, value, labels)
    
    def set_gauge(self, metric_name: str, value: float,
                 labels: Optional[Dict[str, str]] = None) -> None:
        """设置仪表值
        
        Args:
            metric_name: 指标名称
            value: 仪表值
            labels: 标签字典
        """
        self.logger.log_gauge(metric_name, value, labels)
    
    def observe_histogram(self, metric_name: str, value: float,
                        labels: Optional[Dict[str, str]] = None) -> None:
        """观察直方图值
        
        Args:
            metric_name: 指标名称
            value: 观察值
            labels: 标签字典
        """
        # 对于直方图，我们简化为记录多个值
        self.logger.log_timer(f"{metric_name}_histogram", value, labels)
    
    def get_metric(self, metric_name: str, metric_type: str, 
                  labels: Optional[Dict[str, str]] = None) -> Any:
        """获取指标值
        
        在零内存存储模式下，此方法返回None，因为数据不保存在内存中。
        
        Args:
            metric_name: 指标名称
            metric_type: 指标类型
            labels: 标签字典
            
        Returns:
            None - 零内存存储不支持直接获取指标
        """
        return None
    
    def get_all_metrics(self) -> Dict[str, Any]:
        """获取所有指标
        
        在零内存存储模式下，此方法返回空字典，因为数据不保存在内存中。
        
        Returns:
            空字典 - 零内存存储不支持直接获取指标
        """
        return {}
    
    def reset_metrics(self) -> None:
        """重置所有指标
        
        在零内存存储模式下，此方法不执行任何操作，因为没有数据需要重置。
        """
        pass
    
    def generate_report(self) -> Dict[str, Any]:
        """生成性能报告
        
        在零内存存储模式下，此方法返回基本信息，因为数据不保存在内存中。
        
        Returns:
            基本的报告信息
        """
        return {
            "timestamp": None,
            "storage_type": "zero_memory",
            "message": "Metrics are written to logs, not stored in memory"
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """配置监控器
        
        Args:
            config: 配置字典
        """
        # 在零内存存储模式下，配置主要用于日志记录器
        # 这里可以添加日志级别的配置等
        pass