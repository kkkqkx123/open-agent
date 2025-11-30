"""LangGraph Checkpoint工厂和管理"""

from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod
import logging
from pathlib import Path
import asyncio

from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.base import BaseCheckpointSaver
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


class CheckpointerConfig:
    """Checkpoint配置"""
    
    def __init__(
        self,
        checkpointer_type: str = "sqlite",
        connection_string: Optional[str] = None,
        storage_path: Optional[str] = None,
        **kwargs
    ):
        self.checkpointer_type = checkpointer_type
        self.connection_string = connection_string
        self.storage_path = storage_path
        self.kwargs = kwargs


class ICheckpointerFactory(ABC):
    """Checkpoint工厂接口"""
    
    @abstractmethod
    def create_checkpointer(self, config: CheckpointerConfig) -> BaseCheckpointSaver:
        """创建checkpoint实例"""
        pass
    
    @abstractmethod
    def create_for_thread(self, thread_id: str) -> BaseCheckpointSaver:
        """为特定thread创建checkpoint"""
        pass
    
    @abstractmethod
    async def cleanup_checkpointer(self, thread_id: str) -> None:
        """清理thread的checkpoint"""
        pass


class CheckpointerFactory(ICheckpointerFactory):
    """Checkpoint工厂实现"""
    
    def __init__(self, default_config: Optional[CheckpointerConfig] = None):
        self._default_config = default_config or CheckpointerConfig()
        self._checkpointer_cache: Dict[str, BaseCheckpointSaver] = {}
    
    def create_checkpointer(self, config: CheckpointerConfig) -> BaseCheckpointSaver:
        """创建checkpoint实例"""
        checkpointer_type = config.checkpointer_type.lower()
        
        if checkpointer_type == "memory":
            return self._create_memory_checkpointer(config)
        elif checkpointer_type == "sqlite":
            return self._create_sqlite_checkpointer(config)
        else:
            raise ValueError(f"Unsupported checkpointer type: {checkpointer_type}")
    
    def create_for_thread(self, thread_id: str) -> BaseCheckpointSaver:
        """为特定thread创建checkpoint"""
        # 检查缓存
        cache_key = f"thread_{thread_id}"
        if cache_key in self._checkpointer_cache:
            return self._checkpointer_cache[cache_key]
        
        # 创建thread专用的checkpoint
        config = CheckpointerConfig(
            checkpointer_type=self._default_config.checkpointer_type,
            connection_string=self._get_thread_connection_string(thread_id),
            storage_path=self._get_thread_storage_path(thread_id),
            **self._default_config.kwargs
        )
        
        checkpointer = self.create_checkpointer(config)
        self._checkpointer_cache[cache_key] = checkpointer
        
        return checkpointer
    
    def _create_memory_checkpointer(self, config: CheckpointerConfig) -> MemorySaver:
        """创建内存checkpoint"""
        logger.info("Creating MemorySaver checkpointer")
        return MemorySaver()
    
    def _create_sqlite_checkpointer(self, config: CheckpointerConfig) -> SqliteSaver:
        """创建SQLite checkpoint"""
        connection_string = config.connection_string
        
        if not connection_string:
            if config.storage_path:
                # 使用存储路径创建数据库文件
                db_path = Path(config.storage_path) / f"checkpoints_{config.kwargs.get('thread_id', 'default')}.db"
                connection_string = f"sqlite:///{db_path}"
            else:
                # 使用内存数据库
                connection_string = ":memory:"
        
        logger.info(f"Creating SqliteSaver checkpointer with connection: {connection_string}")
        # SqliteSaver.from_conn_string returns a context manager, extract the actual saver
        with SqliteSaver.from_conn_string(connection_string) as saver:
            return saver
    
    def _get_thread_connection_string(self, thread_id: str) -> str:
        """获取thread专用的连接字符串"""
        if self._default_config.connection_string:
            # 如果有默认连接字符串，添加thread_id参数
            base_conn = self._default_config.connection_string
            if base_conn.startswith("sqlite:///"):
                # 文件数据库，为每个thread创建单独的文件
                db_path = base_conn[10:]  # 移除 "sqlite:///"
                thread_db_path = Path(db_path).parent / f"checkpoints_{thread_id}.db"
                return f"sqlite:///{thread_db_path}"
            else:
                # 其他数据库，可能需要不同的处理
                return base_conn
        
        # 默认使用文件数据库
        return f"sqlite:///checkpoints_{thread_id}.db"
    
    def _get_thread_storage_path(self, thread_id: str) -> str:
        """获取thread专用的存储路径"""
        if self._default_config.storage_path:
            return self._default_config.storage_path
        
        # 默认存储路径
        return "./checkpoints"
    
    async def cleanup_checkpointer(self, thread_id: str) -> None:
        """清理thread的checkpoint"""
        cache_key = f"thread_{thread_id}"
        if cache_key in self._checkpointer_cache:
            # Simply remove from cache, BaseCheckpointSaver doesn't require explicit cleanup
            del self._checkpointer_cache[cache_key]
            logger.info(f"Cleaned up checkpointer for thread {thread_id}")
    
    async def cleanup_all_checkpoints(self):
        """清理所有checkpoint"""
        for thread_id in list(self._checkpointer_cache.keys()):
            await self.cleanup_checkpointer(thread_id.split("_", 1)[1])


class CheckpointerManager:
    """Checkpoint管理器 - 高级管理功能"""
    
    def __init__(self, factory: ICheckpointerFactory):
        self._factory = factory
        self._active_checkpoints: Dict[str, BaseCheckpointSaver] = {}
    
    async def get_checkpointer_for_thread(self, thread_id: str) -> BaseCheckpointSaver:
        """获取thread的checkpoint，如果不存在则创建"""
        if thread_id not in self._active_checkpoints:
            self._active_checkpoints[thread_id] = self._factory.create_for_thread(thread_id)
        
        return self._active_checkpoints[thread_id]
    
    async def create_branch_checkpointer(
        self, 
        parent_thread_id: str, 
        branch_thread_id: str,
        checkpoint_id: Optional[str] = None
    ) -> BaseCheckpointSaver:
        """为分支创建checkpoint"""
        # 创建分支专用的checkpoint
        branch_checkpointer = self._factory.create_for_thread(branch_thread_id)
        
        # 如果需要从特定checkpoint开始，可以在这里初始化
        if checkpoint_id:
            logger.info(f"Creating branch {branch_thread_id} from checkpoint {checkpoint_id}")
        
        self._active_checkpoints[branch_thread_id] = branch_checkpointer
        return branch_checkpointer
    
    async def merge_checkpoints(
        self,
        main_thread_id: str,
        branch_thread_id: str,
        merge_strategy: str = "overwrite"
    ):
        """合并分支checkpoint到主线"""
        main_checkpointer = await self.get_checkpointer_for_thread(main_thread_id)
        branch_checkpointer = self._active_checkpoints.get(branch_thread_id)
        
        if not branch_checkpointer:
            raise ValueError(f"No active checkpointer found for branch thread {branch_thread_id}")
        
        # 这里实现具体的合并逻辑
        # 实际实现会依赖于具体的checkpoint数据结构
        logger.info(f"Merging checkpoints from {branch_thread_id} to {main_thread_id} using {merge_strategy}")
        
        # 合并完成后清理分支checkpoint
        await self.cleanup_checkpointer(branch_thread_id)
    
    async def cleanup_checkpointer(self, thread_id: str):
        """清理thread的checkpoint"""
        if thread_id in self._active_checkpoints:
            await self._factory.cleanup_checkpointer(thread_id)
            del self._active_checkpoints[thread_id]
    
    async def get_checkpoint_history(
        self, 
        thread_id: str,
        limit: Optional[int] = None
    ) -> list:
        """获取checkpoint历史"""
        checkpointer = await self.get_checkpointer_for_thread(thread_id)
        
        # 这里需要根据具体的checkpointer实现来获取历史
        # BaseCheckpointSaver has list method for getting checkpoints
        try:
            # Use the base class method to list checkpoints
            # The 'list' method takes optional config and filter parameters
            filter_dict: Optional[Dict[str, Any]] = {"thread_id": thread_id} if thread_id else None
            checkpoints = []
            for checkpoint in checkpointer.list(config=None, filter=filter_dict, limit=limit):
                checkpoints.append(checkpoint)
            return checkpoints
        except Exception as e:
            logger.error(f"Error getting checkpoint history for thread {thread_id}: {e}")
            return []