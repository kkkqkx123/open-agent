"""Checkpoint模块的依赖注入配置"""

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..container.container import DIContainer

from .memory_store import MemoryCheckpointStore
from .sqlite_store import SQLiteCheckpointStore
from .langgraph_adapter import LangGraphAdapter


def register_checkpoint_services(container: 'DIContainer'):
    """注册checkpoint相关服务"""
    
    # 注册LangGraph适配器
    container.register_singleton('langgraph_adapter', LangGraphAdapter)
    
    # 注册checkpoint存储实现
    container.register_transient('memory_checkpoint_store', MemoryCheckpointStore)
    container.register_transient('sqlite_checkpoint_store', SQLiteCheckpointStore)
    
    # 也可以注册为接口类型
    container.register_transient('checkpoint_store', MemoryCheckpointStore, name='memory')
    container.register_transient('checkpoint_store', SQLiteCheckpointStore, name='sqlite')