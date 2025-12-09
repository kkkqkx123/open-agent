"""线程存储后端实现

提供线程存储功能的具体实现。
"""

from typing import Dict, Any, Optional, List
from src.services.logger.injection import get_logger

from ..core.base_backend import BaseStorageBackend
from ..core.mixins.thread_mixin import ThreadStorageMixin
from src.interfaces.storage import IThreadStorage


logger = get_logger(__name__)


class ThreadBackend(BaseStorageBackend, IThreadStorage):
    """线程存储后端
    
    提供线程存储功能的具体实现，通过组合基础后端和线程混入。
    """
    
    def __init__(self, provider, **config: Any) -> None:
        """初始化线程后端
        
        Args:
            provider: 存储提供者实例
            **config: 其他配置参数
        """
        super().__init__(provider=provider, **config)
        
        # 创建线程存储混入
        self._thread_mixin = ThreadStorageMixin(provider)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 连接到提供者
        await self._provider.connect()
        
        # 创建线程表
        await self._provider.create_table("threads", {})
        logger.debug("Thread backend connected and initialized")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        await self._provider.disconnect()
        logger.debug("Thread backend disconnected")
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        provider_health = await self._provider.health_check()
        
        return {
            "status": "healthy" if self._connected else "disconnected",
            "provider": provider_health,
            "table_exists": await self._provider.table_exists("threads")
        }
    
    # === IThreadStorage 接口实现 ===
    
    async def save_thread(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据"""
        return await self._thread_mixin.save_thread(thread_id, data)
    
    async def load_thread(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据"""
        return await self._thread_mixin.load_thread(thread_id)
    
    async def delete_thread(self, thread_id: str) -> bool:
        """删除线程数据"""
        return await self._thread_mixin.delete_thread(thread_id)
    
    async def list_threads(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出线程"""
        return await self._thread_mixin.list_threads(filters, limit)
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查线程是否存在"""
        return await self._thread_mixin.thread_exists(thread_id)
    
    async def get_threads_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """根据会话ID获取线程列表"""
        return await self._thread_mixin.get_threads_by_session(session_id)
    
    async def update_thread_status(self, thread_id: str, status: str) -> bool:
        """更新线程状态"""
        return await self._thread_mixin.update_thread_status(thread_id, status)
    
    async def get_thread_branches(self, thread_id: str) -> List[str]:
        """获取线程关联的分支ID列表"""
        return await self._thread_mixin.get_thread_branches(thread_id)
    
    # === IStorage 接口实现（委托给提供者）===
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        return await self._provider.save("threads", data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self._provider.load("threads", id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        return await self._provider.update("threads", id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self._provider.delete("threads", id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        return await self._provider.exists("threads", id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        return await self._provider.list("threads", filters, limit)
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        return await self._provider.query("threads", query, params)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        return await self._provider.count("threads", filters)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        return await self._provider.batch_save("threads", data_list)
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        return await self._provider.batch_delete("threads", ids)
    
    async def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """流式列出数据（简化实现）"""
        results = await self.list(filters, batch_size)
        return results