"""内存状态存储适配器

提供基于内存的状态存储适配器实现，支持历史记录和快照的存储操作。
"""

import logging
import asyncio
from typing import Any

from .sync_adapter import SyncStateStorageAdapter
from .memory_backend import MemoryStorageBackend
from .metrics import StorageMetrics
from .transaction import TransactionManager


logger = logging.getLogger(__name__)


class MemoryStateStorageAdapter(SyncStateStorageAdapter):
    """内存状态存储适配器
    
    基于内存存储后端实现的状态存储适配器。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存状态存储适配器
        
        Args:
            **config: 配置参数
        """
        backend = MemoryStorageBackend(**config)
        
        # 创建指标收集器
        metrics = StorageMetrics()
        
        # 创建事务管理器
        transaction_manager = TransactionManager(backend)
        
        # 初始化基类
        super().__init__(
            backend=backend,
            metrics=metrics,
            transaction_manager=transaction_manager
        )
        
        # 连接到后端
        if hasattr(backend, 'connect'):
            if asyncio.iscoroutinefunction(backend.connect):
                # 异步方法，需要特殊处理
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor() as executor:
                            future = executor.submit(asyncio.run, backend.connect())
                            future.result()
                    else:
                        asyncio.run(backend.connect())
                except Exception as e:
                    logger.error(f"Failed to connect to backend: {e}")
            else:
                # 同步方法，直接调用
                result = backend.connect()
                if result is not None:
                    logger.debug(f"Backend connect returned: {result}")