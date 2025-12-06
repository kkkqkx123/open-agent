"""资源管理器实现

提供图资源的监控、限制和管理功能。
"""

from typing import Any, Dict, List, Optional

__all__ = ("ResourceManager", "ResourceLimits", "GraphResource", "ResourceUsage")


class ResourceLimits:
    """资源限制配置。"""
    
    def __init__(
        self,
        max_active_graphs: int = 100,
        max_memory_mb: int = 1024,
        max_checkpoints_per_graph: int = 1000,
        max_execution_time_seconds: int = 3600
    ):
        """初始化资源限制。
        
        Args:
            max_active_graphs: 最大活动图数量
            max_memory_mb: 最大内存使用量（MB）
            max_checkpoints_per_graph: 每个图的最大检查点数
            max_execution_time_seconds: 最大执行时间（秒）
        """
        self.max_active_graphs = max_active_graphs
        self.max_memory_mb = max_memory_mb
        self.max_checkpoints_per_graph = max_checkpoints_per_graph
        self.max_execution_time_seconds = max_execution_time_seconds


class GraphResource:
    """图资源信息。"""
    
    def __init__(
        self,
        graph_id: str,
        created_at: str,
        memory_usage_mb: float = 0.0,
        checkpoint_count: int = 0,
        execution_time_seconds: float = 0.0
    ):
        """初始化图资源。
        
        Args:
            graph_id: 图ID
            created_at: 创建时间
            memory_usage_mb: 内存使用量（MB）
            checkpoint_count: 检查点数量
            execution_time_seconds: 执行时间（秒）
        """
        self.graph_id = graph_id
        self.created_at = created_at
        self.memory_usage_mb = memory_usage_mb
        self.checkpoint_count = checkpoint_count
        self.execution_time_seconds = execution_time_seconds


class ResourceUsage:
    """资源使用情况。"""
    
    def __init__(
        self,
        active_graphs: int = 0,
        total_memory_mb: float = 0.0,
        total_checkpoints: int = 0,
        average_execution_time: float = 0.0
    ):
        """初始化资源使用情况。
        
        Args:
            active_graphs: 活动图数量
            total_memory_mb: 总内存使用量（MB）
            total_checkpoints: 总检查点数量
            average_execution_time: 平均执行时间（秒）
        """
        self.active_graphs = active_graphs
        self.total_memory_mb = total_memory_mb
        self.total_checkpoints = total_checkpoints
        self.average_execution_time = average_execution_time


class ResourceManager:
    """资源管理器，提供图资源的监控、限制和管理功能。"""
    
    def __init__(self, resource_limits: ResourceLimits):
        """初始化资源管理器。
        
        Args:
            resource_limits: 资源限制配置
        """
        self.resource_limits = resource_limits
        self.active_graphs: Dict[str, GraphResource] = {}
        self.usage_monitor = ResourceUsageMonitor()
    
    def register_graph(self, graph_id: str, graph: Any) -> None:
        """注册图资源。
        
        Args:
            graph_id: 图ID
            graph: 图实例
        """
        import datetime
        
        # 检查资源限制
        self._check_resource_limits()
        
        # 创建图资源
        resource = GraphResource(
            graph_id=graph_id,
            created_at=datetime.datetime.now().isoformat(),
            memory_usage_mb=self._estimate_memory_usage(graph),
            checkpoint_count=0,
            execution_time_seconds=0.0
        )
        
        self.active_graphs[graph_id] = resource
    
    def destroy_graph(self, graph_id: str) -> None:
        """彻底清理图资源。
        
        Args:
            graph_id: 图ID
        """
        if graph_id in self.active_graphs:
            del self.active_graphs[graph_id]
    
    def monitor_resources(self) -> ResourceUsage:
        """监控资源使用情况。
        
        Returns:
            资源使用情况
        """
        total_memory = sum(resource.memory_usage_mb for resource in self.active_graphs.values())
        total_checkpoints = sum(resource.checkpoint_count for resource in self.active_graphs.values())
        
        if self.active_graphs:
            avg_execution_time = sum(resource.execution_time_seconds for resource in self.active_graphs.values()) / len(self.active_graphs)
        else:
            avg_execution_time = 0.0
        
        return ResourceUsage(
            active_graphs=len(self.active_graphs),
            total_memory_mb=total_memory,
            total_checkpoints=total_checkpoints,
            average_execution_time=avg_execution_time
        )
    
    def enforce_limits(self) -> None:
        """强制执行资源限制。
        
        Raises:
            ResourceLimitExceededError: 资源限制超出
        """
        usage = self.monitor_resources()
        
        if usage.active_graphs > self.resource_limits.max_active_graphs:
            raise ResourceLimitExceededError(
                f"活动图数量超出限制: {usage.active_graphs} > {self.resource_limits.max_active_graphs}"
            )
        
        if usage.total_memory_mb > self.resource_limits.max_memory_mb:
            raise ResourceLimitExceededError(
                f"内存使用量超出限制: {usage.total_memory_mb}MB > {self.resource_limits.max_memory_mb}MB"
            )
    
    async def check_checkpoint_limits(self) -> None:
        """检查检查点限制。
        
        Raises:
            ResourceLimitExceededError: 检查点限制超出
        """
        for graph_id, resource in self.active_graphs.items():
            if resource.checkpoint_count >= self.resource_limits.max_checkpoints_per_graph:
                raise ResourceLimitExceededError(
                    f"图 {graph_id} 的检查点数量超出限制: {resource.checkpoint_count} > {self.resource_limits.max_checkpoints_per_graph}"
                )
    
    def update_graph_usage(self, graph_id: str, **kwargs) -> None:
        """更新图资源使用情况。
        
        Args:
            graph_id: 图ID
            **kwargs: 要更新的字段
        """
        if graph_id in self.active_graphs:
            resource = self.active_graphs[graph_id]
            for key, value in kwargs.items():
                if hasattr(resource, key):
                    setattr(resource, key, value)
    
    def get_graph_resource(self, graph_id: str) -> Optional[GraphResource]:
        """获取图资源信息。
        
        Args:
            graph_id: 图ID
            
        Returns:
            图资源信息（如果存在）
        """
        return self.active_graphs.get(graph_id)
    
    def get_resource_stats(self) -> Dict[str, Any]:
        """获取资源统计信息。
        
        Returns:
            资源统计信息字典
        """
        usage = self.monitor_resources()
        
        return {
            "usage": {
                "active_graphs": usage.active_graphs,
                "total_memory_mb": usage.total_memory_mb,
                "total_checkpoints": usage.total_checkpoints,
                "average_execution_time": usage.average_execution_time
            },
            "limits": {
                "max_active_graphs": self.resource_limits.max_active_graphs,
                "max_memory_mb": self.resource_limits.max_memory_mb,
                "max_checkpoints_per_graph": self.resource_limits.max_checkpoints_per_graph,
                "max_execution_time_seconds": self.resource_limits.max_execution_time_seconds
            },
            "utilization": {
                "graph_utilization": usage.active_graphs / self.resource_limits.max_active_graphs,
                "memory_utilization": usage.total_memory_mb / self.resource_limits.max_memory_mb
            }
        }
    
    def _check_resource_limits(self) -> None:
        """检查资源限制。
        
        Raises:
            ResourceLimitExceededError: 资源限制超出
        """
        self.enforce_limits()
    
    def _estimate_memory_usage(self, graph: Any) -> float:
        """估算图内存使用量。
        
        Args:
            graph: 图实例
            
        Returns:
            估算的内存使用量（MB）
        """
        # 简化实现：基于图的大小估算
        try:
            import sys
            
            # 获取图的大小
            graph_size = sys.getsizeof(graph)
            
            # 转换为MB
            return graph_size / (1024 * 1024)
        except Exception:
            # 如果无法估算，返回默认值
            return 10.0


class ResourceUsageMonitor:
    """资源使用监控器。"""
    
    def __init__(self):
        """初始化资源使用监控器。"""
        self.history: List[ResourceUsage] = []
        self.max_history_size = 100
    
    def record_usage(self, usage: ResourceUsage) -> None:
        """记录资源使用情况。
        
        Args:
            usage: 资源使用情况
        """
        self.history.append(usage)
        
        # 检查历史记录大小限制
        if len(self.history) > self.max_history_size:
            self.history.pop(0)
    
    def get_usage_trend(self, window_size: int = 10) -> Dict[str, Any]:
        """获取资源使用趋势。
        
        Args:
            window_size: 窗口大小
            
        Returns:
            使用趋势信息
        """
        if len(self.history) < window_size:
            return {"trend": "insufficient_data"}
        
        recent_usage = self.history[-window_size:]
        
        # 计算趋势
        memory_trend = self._calculate_trend([usage.total_memory_mb for usage in recent_usage])
        checkpoint_trend = self._calculate_trend([usage.total_checkpoints for usage in recent_usage])
        
        return {
            "trend": {
                "memory": memory_trend,
                "checkpoints": checkpoint_trend
            },
            "current": recent_usage[-1].__dict__
        }
    
    def _calculate_trend(self, values: List[float]) -> str:
        """计算趋势。
        
        Args:
            values: 值列表
            
        Returns:
            趋势描述
        """
        if len(values) < 2:
            return "stable"
        
        # 简单的线性趋势计算
        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]
        
        first_avg = sum(first_half) / len(first_half)
        second_avg = sum(second_half) / len(second_half)
        
        if second_avg > first_avg * 1.1:
            return "increasing"
        elif second_avg < first_avg * 0.9:
            return "decreasing"
        else:
            return "stable"


class ResourceLimitExceededError(Exception):
    """资源限制超出错误。"""
    pass