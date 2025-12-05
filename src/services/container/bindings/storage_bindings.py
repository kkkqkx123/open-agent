"""存储相关服务依赖注入绑定配置

统一注册 Session 和 Thread 的存储服务。
使用基础设施层组件，通过继承BaseServiceBindings简化代码。
"""

import sys
from typing import Dict, Any

from src.services.logger import get_logger
from src.interfaces.logger import ILogger
from src.services.container.core.base_service_bindings import BaseServiceBindings


class StorageServiceBindings(BaseServiceBindings):
    """Storage服务绑定类
    
    负责注册所有存储相关服务，包括：
    - Session存储后端
    - Thread存储后端
    - 相关仓储和服务
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证Storage配置"""
        # Storage服务通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行Storage服务注册"""
        # 导入并注册Session服务
        from .session_bindings import SessionServiceBindings
        session_bindings = SessionServiceBindings()
        session_bindings._do_register_services(container, config, environment)
        
        # 导入并注册Thread服务
        from .thread_bindings import ThreadServiceBindings
        thread_bindings = ThreadServiceBindings()
        thread_bindings._do_register_services(container, config, environment)
    
    def _post_register(
        self,
        container,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 导入服务类型
            from src.interfaces.sessions import ISessionRepository, ISessionService
            from src.interfaces.threads import IThreadRepository, IThreadService
            
            service_types = [
                ISessionRepository,
                ISessionService,
                IThreadRepository,
                IThreadService
            ]
            
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.sessions.injection import (
                set_session_repository_instance,
                set_session_service_instance
            )
            from src.services.threads.injection import (
                set_thread_repository_instance,
                set_thread_service_instance
            )
            
            if container.has_service(ISessionRepository):
                set_session_repository_instance(container.get(ISessionRepository))
            
            if container.has_service(ISessionService):
                set_session_service_instance(container.get(ISessionService))
            
            if container.has_service(IThreadRepository):
                set_thread_repository_instance(container.get(IThreadRepository))
            
            if container.has_service(IThreadService):
                set_thread_service_instance(container.get(IThreadService))
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置Storage服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置Storage注入层失败: {e}", file=sys.stderr)


