"""会话存储后端实现

提供会话存储功能的具体实现。
"""

from typing import Dict, Any, Optional, List
from src.services.logger.injection import get_logger

from ..core.base_backend import BaseStorageBackend
from ..core.mixins.session_mixin import SessionStorageMixin
from ..interfaces.storage import ISessionStorage


logger = get_logger(__name__)


class SessionBackend(BaseStorageBackend, ISessionStorage):
    """会话存储后端
    
    提供会话存储功能的具体实现，通过组合基础后端和会话混入。
    """
    
    def __init__(self, provider, **config: Any) -> None:
        """初始化会话后端
        
        Args:
            provider: 存储提供者实例
            **config: 其他配置参数
        """
        super().__init__(provider=provider, **config)
        
        # 创建会话存储混入
        self._session_mixin = SessionStorageMixin(provider)
    
    async def _connect_impl(self) -> None:
        """实际连接实现"""
        # 连接到提供者
        await self._provider.connect()
        
        # 创建会话表
        await self._provider.create_table("sessions", {})
        logger.debug("Session backend connected and initialized")
    
    async def _disconnect_impl(self) -> None:
        """实际断开连接实现"""
        await self._provider.disconnect()
        logger.debug("Session backend disconnected")
    
    async def _health_check_impl(self) -> Dict[str, Any]:
        """实际健康检查实现"""
        provider_health = await self._provider.health_check()
        
        return {
            "status": "healthy" if self._connected else "disconnected",
            "provider": provider_health,
            "table_exists": await self._provider.table_exists("sessions")
        }
    
    # === ISessionStorage 接口实现 ===
    
    async def save_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        return await self._session_mixin.save_session(session_id, data)
    
    async def load_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        return await self._session_mixin.load_session(session_id)
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        return await self._session_mixin.delete_session(session_id)
    
    async def list_sessions(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        return await self._session_mixin.list_sessions(filters, limit)
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return await self._session_mixin.session_exists(session_id)
    
    async def get_session_threads(self, session_id: str) -> List[str]:
        """获取会话关联的线程ID列表"""
        return await self._session_mixin.get_session_threads(session_id)
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        return await self._session_mixin.update_session_status(session_id, status)
    
    # === IStorage 接口实现（委托给提供者）===
    
    async def save(self, data: Dict[str, Any]) -> str:
        """保存数据"""
        return await self._provider.save("sessions", data)
    
    async def load(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据"""
        return await self._provider.load("sessions", id)
    
    async def update(self, id: str, updates: Dict[str, Any]) -> bool:
        """更新数据"""
        return await self._provider.update("sessions", id, updates)
    
    async def delete(self, id: str) -> bool:
        """删除数据"""
        return await self._provider.delete("sessions", id)
    
    async def exists(self, id: str) -> bool:
        """检查数据是否存在"""
        return await self._provider.exists("sessions", id)
    
    async def list(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出数据"""
        return await self._provider.list("sessions", filters, limit)
    
    async def query(self, query: str, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """执行查询"""
        return await self._provider.query("sessions", query, params)
    
    async def count(self, filters: Dict[str, Any]) -> int:
        """计数"""
        return await self._provider.count("sessions", filters)
    
    async def batch_save(self, data_list: List[Dict[str, Any]]) -> List[str]:
        """批量保存"""
        return await self._provider.batch_save("sessions", data_list)
    
    async def batch_delete(self, ids: List[str]) -> int:
        """批量删除"""
        return await self._provider.batch_delete("sessions", ids)
    
    async def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ) -> List[Dict[str, Any]]:
        """流式列出数据（简化实现）"""
        results = await self.list(filters, batch_size)
        return results