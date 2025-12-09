"""会话服务依赖注入绑定配置 - 更新版本

使用基础设施层组件，通过继承BaseServiceBindings简化代码。
重构后使用接口依赖，避免循环依赖。
"""

import sys
from typing import Dict, Any, TYPE_CHECKING, Union

if TYPE_CHECKING:
    # 仅在类型检查时导入，避免运行时循环依赖
    from src.adapters.storage.backends import ThreadBackend
    from src.adapters.storage.association_repository import SessionThreadAssociationRepository
    from src.adapters.storage.backends import SessionBackend
    from src.services.threads.repository import ThreadRepository
    from src.services.sessions.repository import SessionRepository
    from src.services.sessions.service import SessionService
    from src.services.sessions.coordinator import SessionThreadCoordinator
    from src.services.sessions.synchronizer import SessionThreadSynchronizer
    from src.services.sessions.transaction import SessionThreadTransaction
    from src.adapters.storage.backends.base import ISessionStorageBackend
    from src.adapters.storage.backends.thread_base import IThreadStorageBackend

# 接口导入 - 集中化的接口定义
from src.interfaces.sessions import ISessionRepository
from src.interfaces.sessions.service import ISessionService
from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer,
    ISessionThreadTransaction
)
from src.interfaces.threads import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.core.sessions.interfaces import ISessionCore, ISessionStateTransition, ISessionValidator
from src.interfaces.logger import ILogger
from src.interfaces.container.core import ServiceLifetime
from src.services.container.core.base_service_bindings import BaseServiceBindings


class SessionServiceBindings(BaseServiceBindings):
    """Session服务绑定类
    
    负责注册所有Session相关服务，包括：
    - Session存储后端
    - Session仓储
    - Thread存储后端
    - Thread仓储
    - Session-Thread关联服务
    - 协调器和同步器
    """
    
    def _validate_config(self, config: Dict[str, Any]) -> None:
        """验证Session配置"""
        # Session服务通常不需要特殊验证
        pass
    
    def _do_register_services(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """执行Session服务注册"""
        _register_session_backends(container, config, environment)
        _register_session_repository(container, config, environment)
        _register_thread_backends(container, config, environment)
        _register_thread_repository(container, config, environment)
        _register_association_repository(container, config, environment)
        _register_synchronizer(container, config, environment)
        _register_transaction_manager(container, config, environment)
        _register_coordinator(container, config, environment)
        _register_session_service(container, config, environment)
    
    def _post_register(
        self,
        container: Any,
        config: Dict[str, Any],
        environment: str = "default"
    ) -> None:
        """注册后处理"""
        # 设置注入层
        try:
            # 为Session服务设置注入层
            service_types = [
                ISessionRepository,
                ISessionService,
                ISessionThreadAssociationRepository,
                ISessionThreadSynchronizer,
                ISessionThreadTransaction,
                IThreadRepository,
                IThreadService
            ]
            
            self.setup_injection_layer(container, service_types)
            
            # 设置全局实例（向后兼容）
            from src.services.sessions.injection import (
                set_session_repository_instance,
                set_session_service_instance,
                set_association_repository_instance,
                set_synchronizer_instance,
                set_transaction_manager_instance,
                set_thread_repository_instance,
                set_thread_service_instance
            )
            
            if container.has_service(ISessionRepository):
                set_session_repository_instance(container.get(ISessionRepository))
            
            if container.has_service(ISessionService):
                set_session_service_instance(container.get(ISessionService))
            
            if container.has_service(ISessionThreadAssociationRepository):
                set_association_repository_instance(container.get(ISessionThreadAssociationRepository))
            
            if container.has_service(ISessionThreadSynchronizer):
                set_synchronizer_instance(container.get(ISessionThreadSynchronizer))
            
            if container.has_service(ISessionThreadTransaction):
                set_transaction_manager_instance(container.get(ISessionThreadTransaction))
            
            if container.has_service(IThreadRepository):
                set_thread_repository_instance(container.get(IThreadRepository))
            
            if container.has_service(IThreadService):
                set_thread_service_instance(container.get(IThreadService))
            
            logger = self.safe_get_service(container, ILogger)
            if logger:
                logger.debug(f"已设置Session服务注入层 (environment: {environment})")
        except Exception as e:
            print(f"[WARNING] 设置Session注入层失败: {e}", file=sys.stderr)


def _register_session_backends(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册会话存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 主后端配置
    primary_backend_type = config.get("session", {}).get("primary_backend", "sqlite")

    # 延迟导入具体实现，避免循环依赖
    def create_primary_backend() -> 'SessionBackend':
        from src.adapters.storage.backends.factory import StorageBackendFactory
        from src.adapters.storage.backends import SessionBackend
        
        factory = StorageBackendFactory()
        
        if primary_backend_type == "sqlite":
            sqlite_config = config.get("session", {}).get("sqlite", {})
            db_path = sqlite_config.get("db_path", "./data/sessions.db")
            
            # 创建SQLite提供者配置
            provider_config = {
                "provider_type": "sqlite",
                "db_path": db_path,
                "max_connections": 10,
                "timeout": 30.0
            }
            
            # 使用工厂创建后端实例
            backend = factory.create_backend("session", provider_config)
            return backend
        else:
            raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    def create_secondary_backends() -> list:
        secondary_backends = []
        secondary_types = config.get("session", {}).get("secondary_backends", [])

        for backend_type in secondary_types:
            from src.adapters.storage.backends.factory import StorageBackendFactory
            from src.adapters.storage.backends import SessionBackend
            
            factory = StorageBackendFactory()
            
            if backend_type == "file":
                file_config = config.get("session", {}).get("file", {})
                base_path = file_config.get("base_path", "./sessions_backup")
                
                # 创建文件提供者配置
                provider_config = {
                    "provider_type": "file",
                    "base_path": base_path,
                    "file_extension": ".json"
                }
                
                # 使用工厂创建后端实例
                backend = factory.create_backend("session", provider_config)
                secondary_backends.append(backend)
                
            elif backend_type == "sqlite":
                sqlite_config = config.get("session", {}).get("sqlite_secondary", {})
                db_path = sqlite_config.get("db_path", "./data/sessions_backup.db")
                
                # 创建SQLite提供者配置
                provider_config = {
                    "provider_type": "sqlite",
                    "db_path": db_path,
                    "max_connections": 10,
                    "timeout": 30.0
                }
                
                # 使用工厂创建后端实例
                backend = factory.create_backend("session", provider_config)
                secondary_backends.append(backend)
                
            else:
                print(f"[WARNING] Unknown secondary backend type: {backend_type}", file=sys.stderr)

        return secondary_backends
    
    # 注册主后端为单例
    container.register(
        "session_primary_backend",
        create_primary_backend,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册辅助后端列表
    secondary_types = config.get("session", {}).get("secondary_backends", [])
    if secondary_types:
        container.register(
            "session_secondary_backends",
            create_secondary_backends,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    print(f"[INFO] Session backends registered: primary={primary_backend_type}, secondary={secondary_types}", file=sys.stdout)


def _register_session_repository(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册会话仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保后端已注册
    _register_session_backends(container, config, environment)
    
    # 创建仓储工厂函数
    def session_repository_factory() -> 'SessionRepository':
        from src.services.sessions.repository import SessionRepository
        primary_backend = container.get("session_primary_backend")
        secondary_backends = container.get("session_secondary_backends", default=[])
        logger = container.get(ILogger, default=None)
        return SessionRepository(primary_backend, secondary_backends, logger)
    
    # 注册仓储为单例
    container.register(
        "session_repository",
        session_repository_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        ISessionRepository,
        lambda: container.get("session_repository"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session repository registered", file=sys.stdout)


def _register_thread_backends(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册线程存储后端
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 主后端配置
    primary_backend_type = config.get("thread", {}).get("primary_backend", "sqlite")
    
    # 延迟导入具体实现，避免循环依赖
    def create_primary_backend() -> 'ThreadBackend':
        from src.adapters.storage.backends.factory import StorageBackendFactory
        from src.adapters.storage.backends import ThreadBackend
        
        factory = StorageBackendFactory()
        
        if primary_backend_type == "sqlite":
            sqlite_config = config.get("thread", {}).get("sqlite", {})
            db_path = sqlite_config.get("db_path", "./data/threads.db")
            
            # 创建SQLite提供者配置
            provider_config = {
                "provider_type": "sqlite",
                "db_path": db_path,
                "max_connections": 10,
                "timeout": 30.0
            }
            
            # 使用工厂创建后端实例
            backend = factory.create_backend("thread", provider_config)
            return backend
        else:
            raise ValueError(f"Unsupported primary backend type: {primary_backend_type}")
    
    def create_secondary_backends() -> list:
        secondary_backends = []
        secondary_types = config.get("thread", {}).get("secondary_backends", [])

        for backend_type in secondary_types:
            from src.adapters.storage.backends.factory import StorageBackendFactory
            from src.adapters.storage.backends import ThreadBackend
            
            factory = StorageBackendFactory()
            
            if backend_type == "file":
                file_config = config.get("thread", {}).get("file", {})
                base_path = file_config.get("base_path", "./threads_backup")
                
                # 创建文件提供者配置
                provider_config = {
                    "provider_type": "file",
                    "base_path": base_path,
                    "file_extension": ".json"
                }
                
                # 使用工厂创建后端实例
                backend = factory.create_backend("thread", provider_config)
                secondary_backends.append(backend)
                
            elif backend_type == "sqlite":
                sqlite_config = config.get("thread", {}).get("sqlite_secondary", {})
                db_path = sqlite_config.get("db_path", "./data/threads_backup.db")
                
                # 创建SQLite提供者配置
                provider_config = {
                    "provider_type": "sqlite",
                    "db_path": db_path,
                    "max_connections": 10,
                    "timeout": 30.0
                }
                
                # 使用工厂创建后端实例
                backend = factory.create_backend("thread", provider_config)
                secondary_backends.append(backend)
                
            else:
                print(f"[WARNING] Unknown secondary backend type: {backend_type}", file=sys.stderr)

        return secondary_backends
    
    # 注册主后端为单例
    container.register(
        "thread_primary_backend",
        create_primary_backend,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册辅助后端列表
    secondary_types = config.get("thread", {}).get("secondary_backends", [])
    if secondary_types:
        container.register(
            "thread_secondary_backends",
            create_secondary_backends,
            environment=environment,
            lifetime=ServiceLifetime.SINGLETON
        )
    
    print(f"[INFO] Thread backends registered: primary={primary_backend_type}, secondary={secondary_types}", file=sys.stdout)


def _register_thread_repository(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册线程仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保后端已注册
    _register_thread_backends(container, config, environment)
    
    # 创建仓储工厂函数
    def thread_repository_factory() -> 'ThreadRepository':
        from src.services.threads.repository import ThreadRepository
        primary_backend = container.get("thread_primary_backend")
        secondary_backends = container.get("thread_secondary_backends", default=[])
        return ThreadRepository(primary_backend, secondary_backends)
    
    # 注册仓储为单例
    container.register(
        "thread_repository",
        thread_repository_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        IThreadRepository,
        lambda: container.get("thread_repository"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Thread repository registered", file=sys.stdout)


def _register_association_repository(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册Session-Thread关联仓储
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保后端已注册
    _register_session_backends(container, config, environment)
    _register_thread_backends(container, config, environment)
    
    # 创建关联仓储工厂函数
    def association_repository_factory() -> 'SessionThreadAssociationRepository':
        from src.adapters.storage.association_repository import SessionThreadAssociationRepository
        session_backend = container.get("session_primary_backend")
        thread_backend = container.get("thread_primary_backend")
        return SessionThreadAssociationRepository(session_backend, thread_backend)
    
    # 注册关联仓储为单例
    container.register(
        "association_repository",
        association_repository_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        ISessionThreadAssociationRepository,
        lambda: container.get("association_repository"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session-Thread association repository registered", file=sys.stdout)


def _register_synchronizer(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册数据同步器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_association_repository(container, config, environment)
    _register_session_repository(container, config, environment)
    _register_thread_repository(container, config, environment)
    
    # 创建同步器工厂函数
    def synchronizer_factory() -> 'SessionThreadSynchronizer':
        from src.services.sessions.synchronizer import SessionThreadSynchronizer
        association_repository = container.get(ISessionThreadAssociationRepository)
        session_repository = container.get(ISessionRepository)
        thread_repository = container.get(IThreadRepository)
        return SessionThreadSynchronizer(
            association_repository=association_repository,
            session_repository=session_repository,
            thread_repository=thread_repository
        )
    
    # 注册同步器为单例
    container.register(
        "session_thread_synchronizer",
        synchronizer_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        ISessionThreadSynchronizer,
        lambda: container.get("session_thread_synchronizer"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session-Thread synchronizer registered", file=sys.stdout)


def _register_transaction_manager(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册事务管理器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_association_repository(container, config, environment)
    _register_session_repository(container, config, environment)
    _register_thread_repository(container, config, environment)
    
    # 创建事务管理器工厂函数
    def transaction_factory() -> 'SessionThreadTransaction':
        from src.services.sessions.transaction import SessionThreadTransaction
        association_repository = container.get(ISessionThreadAssociationRepository)
        session_repository = container.get(ISessionRepository)
        thread_repository = container.get(IThreadRepository)
        thread_service = container.get(IThreadService)
        return SessionThreadTransaction(
            association_repository=association_repository,
            session_repository=session_repository,
            thread_repository=thread_repository,
            thread_service=thread_service
        )
    
    # 注册事务管理器为单例
    container.register(
        "session_thread_transaction",
        transaction_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        ISessionThreadTransaction,
        lambda: container.get("session_thread_transaction"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session-Thread transaction manager registered", file=sys.stdout)


def _register_coordinator(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册协调器
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_synchronizer(container, config, environment)
    _register_transaction_manager(container, config, environment)
    
    # 创建协调器工厂函数
    def coordinator_factory() -> 'SessionThreadCoordinator':
        from src.services.sessions.coordinator import SessionThreadCoordinator
        session_service = container.get(ISessionService)
        thread_service = container.get(IThreadService)
        association_repository = container.get(ISessionThreadAssociationRepository)
        synchronizer = container.get(ISessionThreadSynchronizer)
        transaction = container.get(ISessionThreadTransaction)
        logger = container.get(ILogger, default=None)
        return SessionThreadCoordinator(
            session_service=session_service,
            thread_service=thread_service,
            association_repository=association_repository,
            synchronizer=synchronizer,
            transaction=transaction,
            logger=logger
        )
    
    # 注册协调器为单例
    container.register(
        "session_thread_coordinator",
        coordinator_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session-Thread coordinator registered", file=sys.stdout)


def _register_session_service(container: Any, config: Dict[str, Any], environment: str = "default") -> None:
    """注册会话服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
        environment: 环境名称
    """
    # 确保依赖已注册
    _register_session_repository(container, config, environment)
    _register_coordinator(container, config, environment)
    
    # 创建服务工厂函数
    def session_service_factory() -> 'SessionService':
        from src.services.sessions.service import SessionService
        session_core = container.get(ISessionCore)
        session_repository = container.get(ISessionRepository)
        thread_service = container.get(IThreadService)
        coordinator = container.get("session_thread_coordinator")
        session_validator = container.get(ISessionValidator, default=None)
        state_transition = container.get(ISessionStateTransition, default=None)
        git_service = container.get("IGitService", default=None)
        logger = container.get(ILogger, default=None)
        
        return SessionService(
            session_core=session_core,
            session_repository=session_repository,
            thread_service=thread_service,
            coordinator=coordinator,
            session_validator=session_validator,
            state_transition=state_transition,
            git_service=git_service,
            storage_path=config.get("session", {}).get("storage_path", "./sessions"),
            logger=logger
        )
    
    # 注册服务为单例
    container.register(
        "session_service",
        session_service_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册接口
    container.register(
        ISessionService,
        lambda: container.get("session_service"),
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    print(f"[INFO] Session service registered with coordinator", file=sys.stdout)


