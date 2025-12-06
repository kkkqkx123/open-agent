"""ThreadCheckpoint依赖注入便利层

使用通用依赖注入框架提供简洁的ThreadCheckpoint服务获取方式。
"""

from typing import Optional, List, Dict, Any, TYPE_CHECKING

from src.core.threads.checkpoints.storage import (
    ThreadCheckpointDomainService,
    CheckpointManager,
    ThreadCheckpointRepository,
    IThreadCheckpointRepository
)
from src.core.threads.checkpoints.manager import ThreadCheckpointManager
from src.services.storage import (
    StorageOrchestrator,
    ThreadStorageService
)
from src.core.storage import StorageConfigManager
from src.services.container.injection.injection_base import get_global_injection_registry

if TYPE_CHECKING:
    from src.core.threads.checkpoints.storage.models import ThreadCheckpoint, CheckpointStatus, CheckpointType, CheckpointStatistics
    from datetime import datetime


class _StubCheckpointRepository(IThreadCheckpointRepository):
    """临时 CheckpointRepository 实现（用于极端情况）"""
    
    async def save(self, checkpoint: "ThreadCheckpoint") -> bool:
        """保存检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_by_id(self, checkpoint_id: str) -> Optional["ThreadCheckpoint"]:
        """根据ID查找检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_by_thread(self, thread_id: str) -> List["ThreadCheckpoint"]:
        """查找Thread的所有检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_active_by_thread(self, thread_id: str) -> List["ThreadCheckpoint"]:
        """查找Thread的所有活跃检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_by_status(self, status: "CheckpointStatus") -> List["ThreadCheckpoint"]:
        """根据状态查找检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_by_type(self, checkpoint_type: "CheckpointType") -> List["ThreadCheckpoint"]:
        """根据类型查找检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_expired(self, before_time: Optional["datetime"] = None) -> List["ThreadCheckpoint"]:
        """查找过期的检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def update(self, checkpoint: "ThreadCheckpoint") -> bool:
        """更新检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def delete_by_thread(self, thread_id: str) -> int:
        """删除Thread的所有检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def delete_expired(self, before_time: Optional["datetime"] = None) -> int:
        """删除过期的检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计Thread的检查点数量"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def count_by_status(self, status: "CheckpointStatus") -> int:
        """根据状态统计检查点数量"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> "CheckpointStatistics":
        """获取检查点统计信息"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def exists(self, checkpoint_id: str) -> bool:
        """检查检查点是否存在"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_latest_by_thread(self, thread_id: str) -> Optional["ThreadCheckpoint"]:
        """查找Thread的最新检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")
    
    async def find_oldest_by_thread(self, thread_id: str) -> Optional["ThreadCheckpoint"]:
        """查找Thread的最旧检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointRepository")


class _StubCheckpointDomainService(ThreadCheckpointDomainService):
    """临时 CheckpointDomainService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    async def create_checkpoint(
        self,
        thread_id: str,
        state_data: Dict[str, Any],
        checkpoint_type: Optional["CheckpointType"] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expiration_hours: Optional[int] = None
    ) -> "ThreadCheckpoint":
        """创建检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointDomainService")
    
    def get_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """获取检查点"""
        return None


class _StubCheckpointManager(CheckpointManager):
    """临时 CheckpointManager 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def manage_checkpoint(self, thread_id: str, checkpoint_data: dict) -> str:
        """管理检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的CheckpointManager")
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """恢复检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的CheckpointManager")


class _StubThreadCheckpointManager(ThreadCheckpointManager):
    """临时 ThreadCheckpointManager 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def create_thread_checkpoint(self, thread_id: str, checkpoint_data: dict) -> str:
        """创建线程检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointManager")
    
    def restore_thread_checkpoint(self, checkpoint_id: str) -> Optional[dict]:
        """恢复线程检查点"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadCheckpointManager")


class _StubStorageOrchestrator(StorageOrchestrator):
    """临时 StorageOrchestrator 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def orchestrate_storage(self, thread_id: str, data: dict) -> str:
        """编排存储"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的StorageOrchestrator")
    
    def retrieve_storage(self, storage_id: str) -> Optional[dict]:
        """检索存储"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的StorageOrchestrator")


class _StubThreadStorageService(ThreadStorageService):
    """临时 ThreadStorageService 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def store_thread_data(self, thread_id: str, data: dict) -> str:
        """存储线程数据"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadStorageService")
    
    def retrieve_thread_data(self, storage_id: str) -> Optional[dict]:
        """检索线程数据"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的ThreadStorageService")


class _StubStorageConfigManager(StorageConfigManager):
    """临时 StorageConfigManager 实现（用于极端情况）"""
    
    def __init__(self) -> None:
        # 不调用父类初始化，避免依赖问题
        pass
    
    def get_storage_config(self, config_name: str) -> Optional[dict]:
        """获取存储配置"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的StorageConfigManager")
    
    def set_storage_config(self, config_name: str, config_data: dict) -> bool:
        """设置存储配置"""
        raise NotImplementedError("使用的是Stub实现，请配置真实的StorageConfigManager")


def _create_fallback_checkpoint_repository() -> IThreadCheckpointRepository:
    """创建fallback checkpoint repository"""
    return _StubCheckpointRepository()


def _create_fallback_checkpoint_domain_service() -> ThreadCheckpointDomainService:
    """创建fallback checkpoint domain service"""
    return _StubCheckpointDomainService()


def _create_fallback_checkpoint_manager() -> CheckpointManager:
    """创建fallback checkpoint manager"""
    return _StubCheckpointManager()


def _create_fallback_thread_checkpoint_manager() -> ThreadCheckpointManager:
    """创建fallback thread checkpoint manager"""
    return _StubThreadCheckpointManager()


def _create_fallback_storage_orchestrator() -> StorageOrchestrator:
    """创建fallback storage orchestrator"""
    return _StubStorageOrchestrator()


def _create_fallback_thread_storage_service() -> ThreadStorageService:
    """创建fallback thread storage service"""
    return _StubThreadStorageService()


def _create_fallback_storage_config_manager() -> StorageConfigManager:
    """创建fallback storage config manager"""
    return _StubStorageConfigManager()


# 注册ThreadCheckpoint注入
_checkpoint_repository_injection = get_global_injection_registry().register(
    IThreadCheckpointRepository, _create_fallback_checkpoint_repository  # type: ignore
)
_checkpoint_domain_service_injection = get_global_injection_registry().register(
    ThreadCheckpointDomainService, _create_fallback_checkpoint_domain_service
)
_checkpoint_manager_injection = get_global_injection_registry().register(
    CheckpointManager, _create_fallback_checkpoint_manager
)
_thread_checkpoint_manager_injection = get_global_injection_registry().register(
    ThreadCheckpointManager, _create_fallback_thread_checkpoint_manager
)
_storage_orchestrator_injection = get_global_injection_registry().register(
    StorageOrchestrator, _create_fallback_storage_orchestrator
)
_thread_storage_service_injection = get_global_injection_registry().register(
    ThreadStorageService, _create_fallback_thread_storage_service
)
_storage_config_manager_injection = get_global_injection_registry().register(
    StorageConfigManager, _create_fallback_storage_config_manager
)


def get_checkpoint_repository() -> IThreadCheckpointRepository:
    """获取检查点仓储实例
    
    Returns:
        IThreadCheckpointRepository: 检查点仓储实例
    """
    return _checkpoint_repository_injection.get_instance()


def get_checkpoint_domain_service() -> ThreadCheckpointDomainService:
    """获取检查点领域服务实例
    
    Returns:
        ThreadCheckpointDomainService: 检查点领域服务实例
    """
    return _checkpoint_domain_service_injection.get_instance()


def get_checkpoint_manager() -> CheckpointManager:
    """获取检查点管理器实例
    
    Returns:
        CheckpointManager: 检查点管理器实例
    """
    return _checkpoint_manager_injection.get_instance()


def get_thread_checkpoint_manager() -> ThreadCheckpointManager:
    """获取线程检查点管理器实例
    
    Returns:
        ThreadCheckpointManager: 线程检查点管理器实例
    """
    return _thread_checkpoint_manager_injection.get_instance()


def get_storage_orchestrator() -> StorageOrchestrator:
    """获取存储编排器实例
    
    Returns:
        StorageOrchestrator: 存储编排器实例
    """
    return _storage_orchestrator_injection.get_instance()


def get_thread_storage_service() -> ThreadStorageService:
    """获取线程存储服务实例
    
    Returns:
        ThreadStorageService: 线程存储服务实例
    """
    return _thread_storage_service_injection.get_instance()


def get_storage_config_manager() -> StorageConfigManager:
    """获取存储配置管理器实例
    
    Returns:
        StorageConfigManager: 存储配置管理器实例
    """
    return _storage_config_manager_injection.get_instance()


# 设置实例的函数
def set_checkpoint_repository_instance(checkpoint_repository: IThreadCheckpointRepository) -> None:
    """在应用启动时设置全局 CheckpointRepository 实例
    
    Args:
        checkpoint_repository: IThreadCheckpointRepository 实例
    """
    _checkpoint_repository_injection.set_instance(checkpoint_repository)


def set_checkpoint_domain_service_instance(checkpoint_domain_service: ThreadCheckpointDomainService) -> None:
    """在应用启动时设置全局 CheckpointDomainService 实例
    
    Args:
        checkpoint_domain_service: ThreadCheckpointDomainService 实例
    """
    _checkpoint_domain_service_injection.set_instance(checkpoint_domain_service)


def set_checkpoint_manager_instance(checkpoint_manager: CheckpointManager) -> None:
    """在应用启动时设置全局 CheckpointManager 实例
    
    Args:
        checkpoint_manager: CheckpointManager 实例
    """
    _checkpoint_manager_injection.set_instance(checkpoint_manager)


def set_thread_checkpoint_manager_instance(thread_checkpoint_manager: ThreadCheckpointManager) -> None:
    """在应用启动时设置全局 ThreadCheckpointManager 实例
    
    Args:
        thread_checkpoint_manager: ThreadCheckpointManager 实例
    """
    _thread_checkpoint_manager_injection.set_instance(thread_checkpoint_manager)


def set_storage_orchestrator_instance(storage_orchestrator: StorageOrchestrator) -> None:
    """在应用启动时设置全局 StorageOrchestrator 实例
    
    Args:
        storage_orchestrator: StorageOrchestrator 实例
    """
    _storage_orchestrator_injection.set_instance(storage_orchestrator)


def set_thread_storage_service_instance(thread_storage_service: ThreadStorageService) -> None:
    """在应用启动时设置全局 ThreadStorageService 实例
    
    Args:
        thread_storage_service: ThreadStorageService 实例
    """
    _thread_storage_service_injection.set_instance(thread_storage_service)


def set_storage_config_manager_instance(storage_config_manager: StorageConfigManager) -> None:
    """在应用启动时设置全局 StorageConfigManager 实例
    
    Args:
        storage_config_manager: StorageConfigManager 实例
    """
    _storage_config_manager_injection.set_instance(storage_config_manager)


# 清除实例的函数
def clear_checkpoint_repository_instance() -> None:
    """清除全局 CheckpointRepository 实例"""
    _checkpoint_repository_injection.clear_instance()


def clear_checkpoint_domain_service_instance() -> None:
    """清除全局 CheckpointDomainService 实例"""
    _checkpoint_domain_service_injection.clear_instance()


def clear_checkpoint_manager_instance() -> None:
    """清除全局 CheckpointManager 实例"""
    _checkpoint_manager_injection.clear_instance()


def clear_thread_checkpoint_manager_instance() -> None:
    """清除全局 ThreadCheckpointManager 实例"""
    _thread_checkpoint_manager_injection.clear_instance()


def clear_storage_orchestrator_instance() -> None:
    """清除全局 StorageOrchestrator 实例"""
    _storage_orchestrator_injection.clear_instance()


def clear_thread_storage_service_instance() -> None:
    """清除全局 ThreadStorageService 实例"""
    _thread_storage_service_injection.clear_instance()


def clear_storage_config_manager_instance() -> None:
    """清除全局 StorageConfigManager 实例"""
    _storage_config_manager_injection.clear_instance()


# 获取状态的函数
def get_checkpoint_repository_status() -> dict:
    """获取检查点仓储注入状态"""
    return _checkpoint_repository_injection.get_status()


def get_checkpoint_domain_service_status() -> dict:
    """获取检查点领域服务注入状态"""
    return _checkpoint_domain_service_injection.get_status()


def get_checkpoint_manager_status() -> dict:
    """获取检查点管理器注入状态"""
    return _checkpoint_manager_injection.get_status()


def get_thread_checkpoint_manager_status() -> dict:
    """获取线程检查点管理器注入状态"""
    return _thread_checkpoint_manager_injection.get_status()


def get_storage_orchestrator_status() -> dict:
    """获取存储编排器注入状态"""
    return _storage_orchestrator_injection.get_status()


def get_thread_storage_service_status() -> dict:
    """获取线程存储服务注入状态"""
    return _thread_storage_service_injection.get_status()


def get_storage_config_manager_status() -> dict:
    """获取存储配置管理器注入状态"""
    return _storage_config_manager_injection.get_status()


# 导出的公共接口
__all__ = [
    "get_checkpoint_repository",
    "get_checkpoint_domain_service",
    "get_checkpoint_manager",
    "get_thread_checkpoint_manager",
    "get_storage_orchestrator",
    "get_thread_storage_service",
    "get_storage_config_manager",
    "set_checkpoint_repository_instance",
    "set_checkpoint_domain_service_instance",
    "set_checkpoint_manager_instance",
    "set_thread_checkpoint_manager_instance",
    "set_storage_orchestrator_instance",
    "set_thread_storage_service_instance",
    "set_storage_config_manager_instance",
    "clear_checkpoint_repository_instance",
    "clear_checkpoint_domain_service_instance",
    "clear_checkpoint_manager_instance",
    "clear_thread_checkpoint_manager_instance",
    "clear_storage_orchestrator_instance",
    "clear_thread_storage_service_instance",
    "clear_storage_config_manager_instance",
    "get_checkpoint_repository_status",
    "get_checkpoint_domain_service_status",
    "get_checkpoint_manager_status",
    "get_thread_checkpoint_manager_status",
    "get_storage_orchestrator_status",
    "get_thread_storage_service_status",
    "get_storage_config_manager_status",
]