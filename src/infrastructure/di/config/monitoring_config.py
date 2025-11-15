"""监控服务DI配置

负责注册监控系统相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime
from src.infrastructure.monitoring.performance_monitor import IPerformanceMonitor, PerformanceMonitor

logger = logging.getLogger(__name__)


class MonitoringConfigRegistration:
    """监控服务注册类
    
    负责注册监控系统相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册监控服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册监控系统服务")
        
        # 注册性能监控器
        container.register(
            IPerformanceMonitor,
            PerformanceMonitor,
            lifetime=ServiceLifetime.SINGLETON
        )
        
        logger.debug("监控系统服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        return {
            "performance_monitor": IPerformanceMonitor,
        }