"""内存状态存储适配器

提供基于内存的状态存储适配器实现，支持历史记录和快照的存储操作。
"""

import logging
from typing import Any

from .base import BaseStateStorageAdapter
from .memory_backend import MemoryStorageBackend


logger = logging.getLogger(__name__)


class MemoryStateStorageAdapter(BaseStateStorageAdapter):
    """内存状态存储适配器
    
    基于内存存储后端实现的状态存储适配器。
    """
    
    def __init__(self, **config: Any) -> None:
        """初始化内存状态存储适配器
        
        Args:
            **config: 配置参数
        """
        backend = MemoryStorageBackend(**config)
        super().__init__(backend)
        
        # 连接到后端
        self._run_async_method(backend.connect)