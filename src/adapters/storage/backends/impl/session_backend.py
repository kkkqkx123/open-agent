"""会话存储后端实现

提供会话存储功能的具体实现。
"""

from typing import Dict, Any, Optional, List
from src.interfaces.dependency_injection import get_logger

from ..core.mixins.session_mixin import SessionStorageMixin
from src.interfaces.storage import ISessionStorage


logger = get_logger(__name__)


class SessionBackend(ISessionStorage):
    """会话存储后端
    
    专注于会话存储业务逻辑，通过组合会话混入实现功能。
    """
    
    def __init__(self, provider, **config: Any) -> None:
        """初始化会话后端
        
        Args:
            provider: 存储提供者实例
            **config: 其他配置参数
        """
        self._provider = provider
        self._config = config
        self._connected = False
        
        # 创建会话存储混入
        self._session_mixin = SessionStorageMixin(provider)
    
    async def connect(self) -> None:
        """连接到存储后端"""
        if self._connected:
            return
        
        # 连接到提供者
        await self._provider.connect()
        
        # 创建会话表
        await self._provider.create_table("sessions", {})
        self._connected = True
        logger.debug("Session backend connected and initialized")
    
    async def disconnect(self) -> None:
        """断开与存储后端的连接"""
        if not self._connected:
            return
        
        await self._provider.disconnect()
        self._connected = False
        logger.debug("Session backend disconnected")
    
    async def is_connected(self) -> bool:
        """检查是否已连接"""
        return self._connected
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
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
    
    def stream_list(
        self,
        filters: Dict[str, Any],
        batch_size: int = 100
    ):
        """流式列出数据（简化实现）"""
        # 注意：这里应该返回异步迭代器，简化实现
        async def generator():
            results = await self.list(filters, batch_size)
            yield results
        return generator()
    
    async def transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务（简化实现）"""
        # 简化实现：按顺序执行操作
        for op in operations:
            op_type = op.get("type")
            data = op.get("data")
            
            if data is None:
                continue
                
            if op_type == "save":
                await self.save(data)
            elif op_type == "update":
                await self.update(data["id"], data["updates"])
            elif op_type == "delete":
                await self.delete(data["id"])
        
        return True
    
    async def close(self) -> None:
        """关闭存储连接"""
        await self.disconnect()