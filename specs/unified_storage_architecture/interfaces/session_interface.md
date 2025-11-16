# Session模块接口设计

## 概述

Session模块负责管理用户会话的持久化存储。基于分析，Session模块的存储需求相对简单，可以采用简化的适配器实现，甚至直接使用统一存储接口。

## 现有接口分析

### 当前接口 (ISessionStore)

```python
class ISessionStore(ABC):
    """会话存储接口"""

    @abstractmethod
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        pass
```

### 问题分析

1. **同步接口**：当前接口是同步的，需要改为异步
2. **返回值不一致**：`save_session`返回bool，但其他方法可能抛出异常
3. **缺少批量操作**：没有批量保存或删除的接口
4. **缺少查询功能**：只能列出所有会话，无法按条件过滤

## 新接口设计

### 方案一：简化适配器实现

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List

class ISessionStore(ABC):
    """会话存储接口（异步版本）"""

    @abstractmethod
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            session_data: 会话数据
            
        Raises:
            StorageError: 保存失败时抛出
        """
        pass

    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，如果不存在则返回None
        """
        pass

    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Raises:
            StorageNotFoundError: 会话不存在时抛出
            StorageError: 删除失败时抛出
        """
        pass

    @abstractmethod
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话
        
        Args:
            filters: 过滤条件，如 {"status": "active"}
            limit: 限制返回数量
            
        Returns:
            会话列表
        """
        pass

    @abstractmethod
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话是否存在
        """
        pass

    @abstractmethod
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """更新会话数据
        
        Args:
            session_id: 会话ID
            updates: 要更新的字段
            
        Raises:
            StorageNotFoundError: 会话不存在时抛出
            StorageError: 更新失败时抛出
        """
        pass

    @abstractmethod
    async def batch_save_sessions(self, sessions: Dict[str, Dict[str, Any]]) -> None:
        """批量保存会话
        
        Args:
            sessions: 会话数据字典 {session_id: session_data}
            
        Raises:
            StorageError: 保存失败时抛出
        """
        pass

    @abstractmethod
    async def batch_delete_sessions(self, session_ids: List[str]) -> None:
        """批量删除会话
        
        Args:
            session_ids: 会话ID列表
            
        Raises:
            StorageError: 删除失败时抛出
        """
        pass
```

### 方案二：直接使用统一存储接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Protocol

class ISessionService(Protocol):
    """会话服务接口（基于统一存储）"""
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话数据"""
        ...
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        ...
    
    async def delete_session(self, session_id: str) -> None:
        """删除会话数据"""
        ...
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        ...
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        ...
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """更新会话数据"""
        ...

class SessionService:
    """会话服务实现（基于统一存储）"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话数据"""
        data = {
            "id": session_id,
            "type": "session",
            "data": session_data,
            "metadata": session_data.get("metadata", {})
        }
        await self._storage.save(data)
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        data = await self._storage.load(session_id)
        if data and data.get("type") == "session":
            return data.get("data")
        return None
    
    async def delete_session(self, session_id: str) -> None:
        """删除会话数据"""
        success = await self._storage.delete(session_id)
        if not success:
            raise StorageNotFoundError(f"Session not found: {session_id}")
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        query_filters = {"type": "session"}
        if filters:
            query_filters.update(filters)
        
        results = await self._storage.list(query_filters, limit)
        return [result.get("data") for result in results]
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return await self._storage.exists(session_id)
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """更新会话数据"""
        await self._storage.update(session_id, {"data": updates})
```

## 数据模型

### Session数据模型

```python
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

class SessionMetadata(BaseModel):
    """会话元数据"""
    session_id: str
    workflow_config_path: Optional[str] = None
    status: str = "unknown"  # active, inactive, completed, failed
    created_at: datetime
    updated_at: datetime
    user_id: Optional[str] = None
    tags: List[str] = []

class SessionData(BaseModel):
    """会话数据"""
    metadata: SessionMetadata
    thread_configs: Dict[str, Any] = {}
    workflow_state: Dict[str, Any] = {}
    settings: Dict[str, Any] = {}
```

## 实现示例

### 基于统一存储的适配器实现

```python
from typing import Dict, Any, Optional, List
from ...domain.storage.interfaces import IUnifiedStorage
from ...domain.storage.exceptions import StorageNotFoundError, StorageError

class SessionStorageAdapter:
    """会话存储适配器（基于统一存储）"""
    
    def __init__(self, storage: IUnifiedStorage):
        self._storage = storage
    
    async def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """保存会话数据"""
        try:
            # 添加时间戳
            now = datetime.now()
            if "metadata" not in session_data:
                session_data["metadata"] = {}
            
            session_data["metadata"]["updated_at"] = now.isoformat()
            if "created_at" not in session_data["metadata"]:
                session_data["metadata"]["created_at"] = now.isoformat()
            
            data = {
                "id": session_id,
                "type": "session",
                "data": session_data,
                "created_at": now,
                "updated_at": now
            }
            
            await self._storage.save(data)
        except Exception as e:
            raise StorageError(f"Failed to save session {session_id}: {e}")
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            data = await self._storage.load(session_id)
            if data and data.get("type") == "session":
                return data.get("data")
            return None
        except Exception:
            return None
    
    async def delete_session(self, session_id: str) -> None:
        """删除会话数据"""
        try:
            success = await self._storage.delete(session_id)
            if not success:
                raise StorageNotFoundError(f"Session not found: {session_id}")
        except Exception as e:
            if isinstance(e, StorageNotFoundError):
                raise
            raise StorageError(f"Failed to delete session {session_id}: {e}")
    
    async def list_sessions(self, filters: Optional[Dict[str, Any]] = None, 
                          limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """列出会话"""
        try:
            query_filters = {"type": "session"}
            if filters:
                # 将过滤器转换为数据字段查询
                for key, value in filters.items():
                    query_filters[f"data.metadata.{key}"] = value
            
            results = await self._storage.list(query_filters, limit)
            return [result.get("data") for result in results]
        except Exception as e:
            raise StorageError(f"Failed to list sessions: {e}")
    
    async def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        try:
            return await self._storage.exists(session_id)
        except Exception:
            return False
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> None:
        """更新会话数据"""
        try:
            # 添加更新时间戳
            updates["metadata"] = updates.get("metadata", {})
            updates["metadata"]["updated_at"] = datetime.now().isoformat()
            
            await self._storage.update(session_id, {"data": updates})
        except Exception as e:
            raise StorageError(f"Failed to update session {session_id}: {e}")
    
    async def batch_save_sessions(self, sessions: Dict[str, Dict[str, Any]]) -> None:
        """批量保存会话"""
        try:
            operations = []
            now = datetime.now()
            
            for session_id, session_data in sessions.items():
                # 添加时间戳
                if "metadata" not in session_data:
                    session_data["metadata"] = {}
                
                session_data["metadata"]["updated_at"] = now.isoformat()
                if "created_at" not in session_data["metadata"]:
                    session_data["metadata"]["created_at"] = now.isoformat()
                
                operations.append({
                    "type": "save",
                    "data": {
                        "id": session_id,
                        "type": "session",
                        "data": session_data,
                        "created_at": now,
                        "updated_at": now
                    }
                })
            
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to batch save sessions: {e}")
    
    async def batch_delete_sessions(self, session_ids: List[str]) -> None:
        """批量删除会话"""
        try:
            operations = [{"type": "delete", "id": session_id} for session_id in session_ids]
            await self._storage.transaction(operations)
        except Exception as e:
            raise StorageError(f"Failed to batch delete sessions: {e}")
```

## 迁移策略

### 从现有实现迁移

1. **保持接口兼容性**：提供适配器包装现有接口
2. **数据格式转换**：将现有数据格式转换为新格式
3. **逐步迁移**：先实现新接口，再逐步替换旧接口

```python
# 兼容性适配器
class LegacySessionStoreAdapter(ISessionStore):
    """兼容性适配器，将旧接口适配到新实现"""
    
    def __init__(self, session_service: ISessionService):
        self._session_service = session_service
    
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """同步包装异步方法"""
        try:
            import asyncio
            asyncio.run(self._session_service.save_session(session_id, session_data))
            return True
        except Exception:
            return False
    
    # 其他方法的同步包装...
```

## 评估结论

### 可行性评估

1. **技术可行性**：高
   - Session模块需求简单，容易实现
   - 可以直接使用统一存储接口，减少适配器复杂性
   - 异步改造相对简单

2. **迁移风险**：低
   - 数据结构简单，迁移风险低
   - 可以保持接口兼容性
   - 影响范围有限

3. **性能影响**：低
   - Session操作频率不高
   - 数据量相对较小
   - 批量操作可以优化性能

### 推荐方案

**推荐方案二：直接使用统一存储接口**

理由：
1. Session模块需求简单，不需要复杂的适配器
2. 减少代码复杂性，提高可维护性
3. 更好地利用统一存储的功能（如缓存、事务等）
4. 为其他模块提供良好的参考实现

### 实现优先级

1. **高优先级**：实现基本的CRUD操作
2. **中优先级**：添加批量操作和过滤功能
3. **低优先级**：性能优化和监控功能