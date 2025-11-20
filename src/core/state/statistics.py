"""存储统计信息管理

提供统一的存储统计数据结构和收集器。
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


@dataclass
class StorageStatistics:
    """存储统计信息数据类
    
    包含统一的存储统计指标。
    """
    
    # 基础信息
    status: str = "unknown"
    timestamp: float = 0.0
    
    # 容量信息
    total_size_bytes: int = 0
    total_size_mb: float = 0.0
    total_items: int = 0
    
    # 记录统计
    total_records: int = 0
    expired_records: int = 0
    compressed_records: int = 0
    
    # 性能指标
    total_operations: int = 0
    total_reads: int = 0
    total_writes: int = 0
    total_deletes: int = 0
    
    # 备份信息
    backup_count: int = 0
    last_backup_time: Optional[float] = None
    
    # 存储特定信息
    extra_info: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            统计信息字典
        """
        return asdict(self)
    
    def get_compression_ratio(self) -> float:
        """获取压缩比
        
        Returns:
            压缩比（0-1）
        """
        if self.total_records == 0:
            return 0.0
        return self.compressed_records / self.total_records
    
    def get_expiration_ratio(self) -> float:
        """获取过期数据比例
        
        Returns:
            过期比例（0-1）
        """
        if self.total_records == 0:
            return 0.0
        return self.expired_records / self.total_records
    
    def get_average_item_size(self) -> float:
        """获取平均项大小
        
        Returns:
            平均大小（字节）
        """
        if self.total_items == 0:
            return 0.0
        return self.total_size_bytes / self.total_items
    
    def get_operation_stats(self) -> Dict[str, int]:
        """获取操作统计
        
        Returns:
            操作统计字典
        """
        return {
            "total_operations": self.total_operations,
            "total_reads": self.total_reads,
            "total_writes": self.total_writes,
            "total_deletes": self.total_deletes,
        }


@dataclass
class FileStorageStatistics(StorageStatistics):
    """文件存储统计信息
    
    特定于文件存储的统计指标。
    """
    
    directory_path: Optional[str] = None
    file_count: int = 0
    subdirectory_count: int = 0
    largest_file_size: int = 0


@dataclass
class DatabaseStorageStatistics(StorageStatistics):
    """数据库存储统计信息
    
    特定于数据库存储的统计指标。
    """
    
    database_path: Optional[str] = None
    page_count: int = 0
    page_size: int = 4096
    table_count: int = 0
    index_count: int = 0
    cache_hit_ratio: float = 0.0


@dataclass
class MemoryStorageStatistics(StorageStatistics):
    """内存存储统计信息
    
    特定于内存存储的统计指标。
    """
    
    memory_used_bytes: int = 0
    memory_limit_bytes: Optional[int] = None
    memory_usage_ratio: float = 0.0


class StatisticsCollector(ABC):
    """统计信息收集器基类
    
    定义收集存储统计信息的接口。
    """
    
    @abstractmethod
    def collect(self) -> StorageStatistics:
        """收集统计信息
        
        Returns:
            统计信息对象
        """
        pass


class StatisticsAggregator:
    """统计信息聚合器
    
    合并多个存储的统计信息。
    """
    
    def __init__(self):
        """初始化聚合器"""
        self.collectors: List[StatisticsCollector] = []
    
    def add_collector(self, collector: StatisticsCollector) -> None:
        """添加统计收集器
        
        Args:
            collector: 统计收集器
        """
        self.collectors.append(collector)
    
    def remove_collector(self, collector: StatisticsCollector) -> None:
        """移除统计收集器
        
        Args:
            collector: 统计收集器
        """
        if collector in self.collectors:
            self.collectors.remove(collector)
    
    def collect_all(self) -> List[StorageStatistics]:
        """收集所有统计信息
        
        Returns:
            统计信息列表
        """
        stats = []
        for collector in self.collectors:
            try:
                stat = collector.collect()
                stats.append(stat)
            except Exception:
                # 忽略单个收集器的错误
                pass
        return stats
    
    def aggregate(self) -> StorageStatistics:
        """聚合所有统计信息
        
        Returns:
            聚合后的统计信息
        """
        all_stats = self.collect_all()
        
        if not all_stats:
            return StorageStatistics()
        
        # 聚合统计
        aggregated = StorageStatistics()
        aggregated.status = "aggregated"
        
        import time
        aggregated.timestamp = time.time()
        
        for stat in all_stats:
            aggregated.total_size_bytes += stat.total_size_bytes
            aggregated.total_items += stat.total_items
            aggregated.total_records += stat.total_records
            aggregated.expired_records += stat.expired_records
            aggregated.compressed_records += stat.compressed_records
            aggregated.total_operations += stat.total_operations
            aggregated.total_reads += stat.total_reads
            aggregated.total_writes += stat.total_writes
            aggregated.total_deletes += stat.total_deletes
            aggregated.backup_count += stat.backup_count
        
        # 计算平均值
        if aggregated.total_size_bytes > 0:
            aggregated.total_size_mb = round(aggregated.total_size_bytes / (1024 * 1024), 2)
        
        return aggregated


class HealthCheckHelper:
    """健康检查助手
    
    基于统计信息生成健康检查报告。
    """
    
    @staticmethod
    def prepare_health_check_response(
        status: str,
        stats: StorageStatistics,
        config: Dict[str, Any],
        **additional_info
    ) -> Dict[str, Any]:
        """准备健康检查响应
        
        Args:
            status: 状态（healthy/degraded/unhealthy）
            stats: 统计信息
            config: 配置信息
            **additional_info: 额外信息
            
        Returns:
            健康检查响应字典
        """
        response: Dict[str, Any] = {
            "status": status,
            "timestamp": stats.timestamp,
            "config": config,
        }
        
        # 添加统计信息
        stats_dict = stats.to_dict()
        for key, value in stats_dict.items():
            response[f"stat_{key}"] = value
        
        # 添加计算指标
        response["compression_ratio"] = stats.get_compression_ratio()
        response["expiration_ratio"] = stats.get_expiration_ratio()
        response["average_item_size"] = stats.get_average_item_size()
        response["operation_stats"] = stats.get_operation_stats()
        
        # 添加额外信息
        response.update(additional_info)
        
        return response
