"""
会话服务绑定
"""

from typing import Dict, Any
from src.interfaces.sessions import ISessionService
from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class SessionServiceBindings:
    """会话服务绑定"""
    
    def register_services(self, container: IDependencyContainer, config: Dict[str, Any]):
        """注册会话服务
        
        Args:
            container: 依赖注入容器
            config: 配置信息
        """
        # 注册会话服务
        def session_service_factory():
            from src.services.sessions.service import SessionService
            from src.core.sessions.core_interfaces import ISessionCore
            from pathlib import Path
            
            # 获取日志实例
            try:
                from src.interfaces.logger import ILogger
                logger = container.get(ILogger)
            except:
                logger = None
            
            # 创建会话核心的简单实现（实现ISessionCore）
            class SimpleSessionCore(ISessionCore):
                def create_session(self, user_id=None, metadata=None):
                    from src.core.sessions.entities import Session
                    return Session(
                        user_id=user_id or "default_user",
                        metadata=metadata or {}
                    )
                
                def validate_session_state(self, session_data):
                    return True
                
                def create_user_request(self, content, user_id=None, metadata=None):
                    from src.core.sessions.entities import UserRequestEntity
                    return UserRequestEntity(
                        content=content,
                        user_id=user_id or "default_user",
                        metadata=metadata or {}
                    )
                
                def create_user_interaction(self, session_id, interaction_type, content, thread_id=None, metadata=None):
                    from src.core.sessions.entities import UserInteractionEntity
                    return UserInteractionEntity(
                        session_id=session_id,
                        interaction_type=interaction_type,
                        content=content,
                        thread_id=thread_id,
                        metadata=metadata or {}
                    )
            
            session_core = SimpleSessionCore()
            
            # 使用配置中的存储路径
            storage_path = config.get("storage_path")
            if storage_path:
                storage_path = Path(storage_path)
            
            return SessionService(
                session_core=session_core,
                session_repository=None,
                thread_service=None,
                coordinator=None,
                session_validator=None,
                state_transition=None,
                git_service=None,
                storage_path=storage_path,
                logger=logger,
                session_state_manager=None
            )
        
        container.register_factory(
            ISessionService,
            session_service_factory,
            lifetime=ServiceLifetime.SINGLETON
        )