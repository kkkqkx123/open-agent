"""CLI服务DI配置

负责注册CLI相关服务。
"""

import logging
from typing import Dict, Type
from typing import TYPE_CHECKING

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class CLIConfigRegistration:
    """CLI服务注册类
    
    负责注册CLI相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册CLI服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册CLI服务")
        
        # 注册运行命令
        try:
            from ...cli.run_command import RunCommand
            container.register(
                RunCommand,
                RunCommand,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"运行命令注册失败: {e}")
        
        # CLI中没有单独的ConfigCommand类，配置功能通过click命令实现
        # 不再尝试导入不存在的ConfigCommand
        
        logger.debug("CLI服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        try:
            from ...cli.run_command import RunCommand
            
            return {
                "run_command": RunCommand,
            }
        except ImportError:
            # 如果导入失败，返回空字典
            return {}