"""
存储监控接口定义

定义存储系统的监控功能接口，包括性能监控、健康检查和统计信息收集。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime


class IStorageMonitoring(ABC):
    """存储监控接口
    
    定义存储系统的监控功能，包括性能指标、健康状态和使用统计。
    """
    
    @abstractmethod
    async def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态
        
        Returns:
            健康状态信息，包含状态、响应时间、错误计数等
        """
        pass
    
    @abstractmethod
    async def get_performance_metrics(self) -> Dict[str, Any]:
        """获取性能指标
        
        Returns:
            性能指标信息，包含响应时间、吞吐量、错误率等
        """
        pass
    
    @abstractmethod
    async def get_usage_statistics(self) -> Dict[str, Any]:
        """获取使用统计
        
        Returns:
            使用统计信息，包含存储使用量、操作计数、数据分布等
        """
        pass
    
    @abstractmethod
    async def start_monitoring(self) -> bool:
        """开始监控
        
        Returns:
            是否开始成功
        """
        pass
    
    @abstractmethod
    async def stop_monitoring(self) -> bool:
        """停止监控
        
        Returns:
            是否停止成功
        """
        pass
    
    @abstractmethod
    async def get_monitoring_config(self) -> Dict[str, Any]:
        """获取监控配置
        
        Returns:
            监控配置信息
        """
        pass
    
    @abstractmethod
    async def update_monitoring_config(self, config: Dict[str, Any]) -> bool:
        """更新监控配置
        
        Args:
            config: 新的监控配置
            
        Returns:
            是否更新成功
        """
        pass


class IStorageMetrics(ABC):
    """存储指标接口
    
    定义存储性能指标收集的接口。
    """
    
    @abstractmethod
    async def record_operation(
        self, 
        operation: str, 
        duration: float, 
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """记录操作指标
        
        Args:
            operation: 操作类型
            duration: 操作耗时（秒）
            success: 是否成功
            metadata: 元数据
        """
        pass
    
    @abstractmethod
    async def get_metrics(self, operation: Optional[str] = None) -> Dict[str, Any]:
        """获取指标数据
        
        Args:
            operation: 操作类型，None表示获取所有
            
        Returns:
            指标数据
        """
        pass
    
    @abstractmethod
    async def reset_metrics(self) -> None:
        """重置指标数据"""
        pass
    
    @abstractmethod
    async def get_metrics_summary(self, time_range: Optional[Dict[str, datetime]] = None) -> Dict[str, Any]:
        """获取指标摘要
        
        Args:
            time_range: 时间范围，包含start_time和end_time
            
        Returns:
            指标摘要信息
        """
        pass


class IStorageAlerting(ABC):
    """存储告警接口
    
    定义存储系统告警功能。
    """
    
    @abstractmethod
    async def check_alerts(self) -> List[Dict[str, Any]]:
        """检查告警条件
        
        Returns:
            触发的告警列表
        """
        pass
    
    @abstractmethod
    async def send_alert(self, alert: Dict[str, Any]) -> bool:
        """发送告警
        
        Args:
            alert: 告警信息
            
        Returns:
            是否发送成功
        """
        pass
    
    @abstractmethod
    async def get_alert_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取告警历史
        
        Args:
            limit: 限制返回数量
            
        Returns:
            告警历史列表
        """
        pass
    
    @abstractmethod
    async def configure_alert_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """配置告警规则
        
        Args:
            rules: 告警规则列表
            
        Returns:
            是否配置成功
        """
        pass