"""历史存储服务注册模块"""

from typing import Dict, Any
from pathlib import Path

from src.infrastructure.container import IDependencyContainer
from src.domain.history.interfaces import IHistoryManager
from src.application.history.manager import HistoryManager
from src.infrastructure.history.storage.file_storage import FileHistoryStorage


def register_history_services(container: IDependencyContainer, config: Dict[str, Any]) -> None:
    """注册历史存储相关服务
    
    Args:
        container: 依赖注入容器
        config: 配置字典
    """
    history_config = config.get("history", {})
    
    # 检查是否启用历史存储
    if not history_config.get("enabled", False):
        return
    
    # 注册存储
    storage_path = Path(history_config.get("storage_path", "./history"))
    container.register_instance(
        FileHistoryStorage,
        FileHistoryStorage(storage_path)
    )
    
    # 注册管理器
    container.register(
        IHistoryManager,
        HistoryManager,
        lifetime="singleton"
    )