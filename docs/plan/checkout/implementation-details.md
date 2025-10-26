# LangGraph Checkpoint 实现细节

## 1. 接口定义

### 1.1 Checkpoint 存储接口

```python
# src/domain/checkpoint/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class ICheckpointStore(ABC):
    """Checkpoint存储接口"""
    
    @abstractmethod
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        pass
    
    @abstractmethod
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        pass
    
    @abstractmethod
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint"""
        pass
    
    @abstractmethod
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        pass
    
    @abstractmethod
    async def get_latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint"""
        pass
    
    @abstractmethod
    async def cleanup_old_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        pass
```

### 1.2 Checkpoint 管理器接口

```python
# src/application/checkpoint/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

class ICheckpointManager(ABC):
    """Checkpoint管理器接口"""
    
    @abstractmethod
    async def create_checkpoint(
        self, 
        session_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint"""
        pass
    
    @abstractmethod
    async def get_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint"""
        pass
    
    @abstractmethod
    async def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint"""
        pass
    
    @abstractmethod
    async def delete_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        pass
    
    @abstractmethod
    async def get_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint"""
        pass
    
    @abstractmethod
    async def restore_from_checkpoint(
        self, 
        session_id: str, 
        checkpoint_id: str
    ) -> Optional[Any]:
        """从checkpoint恢复状态"""
        pass
```

## 2. SQLite 存储实现

### 2.1 数据库表结构

```sql
-- checkpoints 表
CREATE TABLE IF NOT EXISTS checkpoints (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    workflow_id TEXT NOT NULL,
    state_data TEXT NOT NULL,  -- JSON序列化的工作流状态
    metadata TEXT NOT NULL,     -- JSON序列化的元数据
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_checkpoints_session_id ON checkpoints(session_id);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at);
CREATE INDEX IF NOT EXISTS idx_checkpoints_session_workflow ON checkpoints(session_id, workflow_id);
```

### 2.2 SQLiteCheckpointStore 实现

```python
# src/infrastructure/checkpoint/sqlite_store.py
import aiosqlite
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from ...domain.checkpoint.interfaces import ICheckpointStore

class SQLiteCheckpointStore(ICheckpointStore):
    """SQLite checkpoint存储实现"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._connection_pool = None
    
    async def _get_connection(self) -> aiosqlite.Connection:
        """获取数据库连接"""
        if self._connection_pool is None:
            self._connection_pool = await aiosqlite.connect(self.db_path)
            await self._initialize_database()
        return self._connection_pool
    
    async def _initialize_database(self):
        """初始化数据库表"""
        async with self._get_connection() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    workflow_id TEXT NOT NULL,
                    state_data TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建索引
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_session_id ON checkpoints(session_id)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at)')
            await conn.execute('CREATE INDEX IF NOT EXISTS idx_checkpoints_session_workflow ON checkpoints(session_id, workflow_id)')
            
            await conn.commit()
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        try:
            async with self._get_connection() as conn:
                await conn.execute('''
                    INSERT OR REPLACE INTO checkpoints 
                    (id, session_id, workflow_id, state_data, metadata, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    checkpoint_data['id'],
                    checkpoint_data['session_id'],
                    checkpoint_data['workflow_id'],
                    json.dumps(checkpoint_data['state_data']),
                    json.dumps(checkpoint_data['metadata']),
                    datetime.now().isoformat()
                ))
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"保存checkpoint失败: {e}")
            return False
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    'SELECT * FROM checkpoints WHERE id = ?', 
                    (checkpoint_id,)
                )
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'session_id': row[1],
                        'workflow_id': row[2],
                        'state_data': json.loads(row[3]),
                        'metadata': json.loads(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                return None
        except Exception as e:
            logger.error(f"加载checkpoint失败: {e}")
            return None
    
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute(
                    'SELECT * FROM checkpoints WHERE session_id = ? ORDER BY created_at DESC',
                    (session_id,)
                )
                rows = await cursor.fetchall()
                
                checkpoints = []
                for row in rows:
                    checkpoints.append({
                        'id': row[0],
                        'session_id': row[1],
                        'workflow_id': row[2],
                        'state_data': json.loads(row[3]),
                        'metadata': json.loads(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    })
                return checkpoints
        except Exception as e:
            logger.error(f"列出checkpoint失败: {e}")
            return []
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        try:
            async with self._get_connection() as conn:
                await conn.execute(
                    'DELETE FROM checkpoints WHERE id = ?',
                    (checkpoint_id,)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f"删除checkpoint失败: {e}")
            return False
    
    async def get_latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint"""
        try:
            async with self._get_connection() as conn:
                cursor = await conn.execute('''
                    SELECT * FROM checkpoints 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT 1
                ''', (session_id,))
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'id': row[0],
                        'session_id': row[1],
                        'workflow_id': row[2],
                        'state_data': json.loads(row[3]),
                        'metadata': json.loads(row[4]),
                        'created_at': row[5],
                        'updated_at': row[6]
                    }
                return None
        except Exception as e:
            logger.error(f"获取最新checkpoint失败: {e}")
            return None
    
    async def cleanup_old_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            async with self._get_connection() as conn:
                # 获取需要删除的checkpoint ID
                cursor = await conn.execute('''
                    SELECT id FROM checkpoints 
                    WHERE session_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT -1 OFFSET ?
                ''', (session_id, max_count))
                
                rows = await cursor.fetchall()
                deleted_count = 0
                
                for row in rows:
                    await conn.execute(
                        'DELETE FROM checkpoints WHERE id = ?',
                        (row[0],)
                    )
                    deleted_count += 1
                
                await conn.commit()
                return deleted_count
        except Exception as e:
            logger.error(f"清理旧checkpoint失败: {e}")
            return 0
    
    async def close(self):
        """关闭数据库连接"""
        if self._connection_pool:
            await self._connection_pool.close()
            self._connection_pool = None
```

## 3. 内存存储实现

```python
# src/infrastructure/checkpoint/memory_store.py
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import threading

from ...domain.checkpoint.interfaces import ICheckpointStore

class MemoryCheckpointStore(ICheckpointStore):
    """内存checkpoint存储实现（用于测试）"""
    
    def __init__(self):
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
    
    async def save(self, checkpoint_data: Dict[str, Any]) -> bool:
        """保存checkpoint数据"""
        with self._lock:
            checkpoint_id = checkpoint_data.get('id', str(uuid.uuid4()))
            checkpoint_data['id'] = checkpoint_id
            checkpoint_data['created_at'] = datetime.now().isoformat()
            checkpoint_data['updated_at'] = datetime.now().isoformat()
            
            self._checkpoints[checkpoint_id] = checkpoint_data.copy()
            return True
    
    async def load(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        with self._lock:
            return self._checkpoints.get(checkpoint_id)
    
    async def list_by_session(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint"""
        with self._lock:
            checkpoints = [
                checkpoint for checkpoint in self._checkpoints.values()
                if checkpoint['session_id'] == session_id
            ]
            return sorted(checkpoints, key=lambda x: x['created_at'], reverse=True)
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        with self._lock:
            if checkpoint_id in self._checkpoints:
                del self._checkpoints[checkpoint_id]
                return True
            return False
    
    async def get_latest(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint"""
        with self._lock:
            session_checkpoints = [
                checkpoint for checkpoint in self._checkpoints.values()
                if checkpoint['session_id'] == session_id
            ]
            if session_checkpoints:
                return max(session_checkpoints, key=lambda x: x['created_at'])
            return None
    
    async def cleanup_old_checkpoints(self, session_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        with self._lock:
            session_checkpoints = [
                checkpoint for checkpoint in self._checkpoints.values()
                if checkpoint['session_id'] == session_id
            ]
            
            if len(session_checkpoints) <= max_count:
                return 0
            
            # 按创建时间排序，保留最新的max_count个
            session_checkpoints.sort(key=lambda x: x['created_at'], reverse=True)
            checkpoints_to_delete = session_checkpoints[max_count:]
            
            deleted_count = 0
            for checkpoint in checkpoints_to_delete:
                del self._checkpoints[checkpoint['id']]
                deleted_count += 1
            
            return deleted_count
    
    def clear(self):
        """清除所有checkpoint（仅用于测试）"""
        with self._lock:
            self._checkpoints.clear()
```

## 4. Checkpoint 管理器实现

```python
# src/application/checkpoint/manager.py
import uuid
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

from ...domain.checkpoint.interfaces import ICheckpointStore
from .interfaces import ICheckpointManager

class CheckpointManager(ICheckpointManager):
    """Checkpoint管理器实现"""
    
    def __init__(self, checkpoint_store: ICheckpointStore):
        self.checkpoint_store = checkpoint_store
    
    async def create_checkpoint(
        self, 
        session_id: str, 
        workflow_id: str, 
        state: Any,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建checkpoint"""
        checkpoint_id = str(uuid.uuid4())
        
        checkpoint_data = {
            'id': checkpoint_id,
            'session_id': session_id,
            'workflow_id': workflow_id,
            'state_data': self._serialize_state(state),
            'metadata': metadata or {},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        success = await self.checkpoint_store.save(checkpoint_data)
        if success:
            return checkpoint_id
        else:
            raise RuntimeError("创建checkpoint失败")
    
    async def get_checkpoint(self, session_id: str, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """获取checkpoint"""
        checkpoint = await self.checkpoint_store.load(checkpoint_id)
        if checkpoint and checkpoint['session_id'] == session_id:
            return checkpoint
        return None
    
    async def list_checkpoints(self, session_id: str) -> List[Dict[str, Any]]:
        """列出会话的所有checkpoint"""
        return await self.checkpoint_store.list_by_session(session_id)
    
    async def delete_checkpoint(self, session_id: str, checkpoint_id: str) -> bool:
        """删除checkpoint"""
        checkpoint = await self.checkpoint_store.load(checkpoint_id)
        if checkpoint and checkpoint['session_id'] == session_id:
            return await self.checkpoint_store.delete(checkpoint_id)
        return False
    
    async def get_latest_checkpoint(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话的最新checkpoint"""
        return await self.checkpoint_store.get_latest(session_id)
    
    async def restore_from_checkpoint(
        self, 
        session_id: str, 
        checkpoint_id: str
    ) -> Optional[Any]:
        """从checkpoint恢复状态"""
        checkpoint = await self.get_checkpoint(session_id, checkpoint_id)
        if checkpoint:
            return self._deserialize_state(checkpoint['state_data'])
        return None
    
    def _serialize_state(self, state: Any) -> Dict[str, Any]:
        """序列化工作流状态"""
        # 这里需要根据具体的工作流状态类型进行序列化
        # 可以使用现有的会话状态序列化逻辑
        if hasattr(state, 'to_dict'):
            return state.to_dict()
        elif hasattr(state, '__dict__'):
            return state.__dict__
        else:
            return {'state': str(state)}
    
    def _deserialize_state(self, state_data: Dict[str, Any]) -> Any:
        """反序列化工作流状态"""
        # 这里需要根据具体的工作流状态类型进行反序列化
        # 可以使用现有的会话状态反序列化逻辑
        from ...domain.prompts.agent_state import AgentState
        # 这里需要根据实际状态类型进行反序列化
        # 暂时返回原始数据，实际实现需要根据具体状态类型处理
        return state_data
```

## 5. 配置支持

### 5.1 Checkpoint 配置类

```python
# src/domain/checkpoint/config.py
from dataclasses import dataclass, field
from typing import Optional, List

@dataclass
class CheckpointConfig:
    """Checkpoint配置"""
    enabled: bool = True
    storage_type: str = "sqlite"  # "sqlite" | "memory"
    auto_save: bool = True
    save_interval: int = 5  # 每5步保存一次
    max_checkpoints: int = 100
    retention_days: int = 30
    trigger_conditions: List[str] = field(default_factory=lambda: ["tool_call", "state_change"])
    
    @classmethod
    def from_dict(cls, data: dict) -> "CheckpointConfig":
        """从字典创建配置"""
        return cls(
            enabled=data.get("enabled", True),
            storage_type=data.get("storage_type", "sqlite"),
            auto_save=data.get("auto_save", True),
            save_interval=data.get("save_interval", 5),
            max_checkpoints=data.get("max_checkpoints", 100),
            retention_days=data.get("retention_days", 30),
            trigger_conditions=data.get("trigger_conditions", ["tool_call", "state_change"])
        )
```

这个实现方案提供了完整的checkpoint系统架构，包括SQLite和内存存储实现，以及配置支持。