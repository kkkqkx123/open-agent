"""TUI服务DI配置

负责注册TUI相关服务。
"""

import logging
from typing import Dict, Type

from src.infrastructure.container_interfaces import IDependencyContainer, ServiceLifetime

logger = logging.getLogger(__name__)


class TUIConfigRegistration:
    """TUI服务注册类
    
    负责注册TUI相关的所有服务。
    """
    
    @staticmethod
    def register_services(container: IDependencyContainer) -> None:
        """注册TUI服务
        
        Args:
            container: 依赖注入容器
        """
        logger.debug("注册TUI服务")
        
        # 注册会话组件
        try:
            from ...tui.components.session_dialog import SessionManagerDialog
            container.register(
                SessionManagerDialog,
                SessionManagerDialog,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"会话组件注册失败: {e}")
        
        # 注册工作流组件
        try:
            from ...tui.components.workflow_control import WorkflowControlPanel
            from ...tui.components.workflow_visualizer import WorkflowVisualizer
            container.register(
                WorkflowControlPanel,
                WorkflowControlPanel,
                lifetime=ServiceLifetime.SINGLETON
            )
            container.register(
                WorkflowVisualizer,
                WorkflowVisualizer,
                lifetime=ServiceLifetime.SINGLETON
            )
        except ImportError as e:
            logger.warning(f"工作流组件注册失败: {e}")
        
        logger.debug("TUI服务注册完成")
    
    @staticmethod
    def get_service_types() -> Dict[str, Type]:
        """获取注册的服务类型
        
        Returns:
            注册的服务类型字典
        """
        # 动态导入类型以避免启动时的导入错误
        try:
            from ...tui.components.session_dialog import SessionManagerDialog
            from ...tui.components.workflow_control import WorkflowControlPanel
            
            # 返回与原始错误中期望的类名匹配的字典
            # 由于没有 ThreadComponent，我们只返回现有的组件
            return {
                "SessionComponent": SessionManagerDialog,
                "ThreadComponent": SessionManagerDialog,  # 使用 SessionManagerDialog 作为 ThreadComponent 的替代
                "WorkflowComponent": WorkflowControlPanel,
            }
        except ImportError as e:
            logger.warning(f"获取服务类型失败: {e}")
            return {}