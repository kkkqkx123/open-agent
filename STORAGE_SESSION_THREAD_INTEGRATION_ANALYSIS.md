# Storage 模块与 Session、Thread 集成分析

## 当前设计的问题

### 1. **接口不匹配问题**
```
❌ 现状:
- SQLiteSessionStore 实现 ISessionStore (在 src/interfaces/sessions/storage.py)
- SQLiteThreadStore 实现 IThreadStore (在 src/interfaces/threads/storage.py)
- 但 ISessionStore 定义的是 AbstractSessionData，不是 Session 实体
- 实际实现使用 Session 实体处理

结果: 接口与实现签名不符
```

### 2. **架构层级混乱**
```
当前结构:
┌─────────────────────────────────────────────────┐
│  SessionService (src/services/session/)         │
│  - 依赖 ISessionStore                          │
│  - 依赖 ISessionCore                           │
│  - 使用 FileSystem 存储会话数据                 │
└─────────────────────────────────────────────────┘
          │
          ├─→ SQLiteSessionStore (src/adapters/storage/)
          │     └─ 直接操作 Session 实体
          │
          └─→ SQLiteThreadStore (src/adapters/storage/)
                └─ 直接操作 Thread 实体


问题:
1. SessionService 同时依赖 Storage 和 Core，引入循环依赖风险
2. Session/Thread 实体是核心概念，不应该直接在适配器层序列化/反序列化
3. SQLiteSessionStore/SQLiteThreadStore 是存储实现，与 Session/Thread 业务逻辑强耦合
4. 缺乏统一的存储抽象层 (src/adapters/storage/ 中已有通用框架，但未被使用)
```

### 3. **职责分离不清**
```
SQLiteSessionStore 的职责过重:
- 存储适配器 ✓
- 实体转换 (不应该)
- 业务查询逻辑 (list_by_status, search, cleanup 等)

Session 生命周期管理:
- SessionService 处理业务流程 (create, track_interaction...)
- SQLiteSessionStore 处理持久化
- 但中间没有清晰的边界
```

### 4. **数据一致性问题**
```
当前流程:
1. SessionService 创建会话 (SessionEntity via ISessionCore)
2. SessionService 序列化为 Dict 保存到 FileSystem
3. 另外 SQLiteSessionStore 有自己的表结构（thread_ids, tags 等）
4. 两套存储逻辑不同步 → 数据可能不一致

同样的问题也存在于 Thread
```

### 5. **缺乏统一存储协调**
```
目前没有统一的多存储协调:
- Session 数据保存到 FileSystem + Git
- Thread 数据保存到 SQLite (但实际使用的不多)
- Checkpoint 数据单独管理
- History 数据单独管理

不能保证跨存储的事务一致性
```

---

## 最佳集成方案

### 方案选择标准
根据架构特点，推荐：**统一存储适配器 + 分层服务**

### 核心思路
```
┌─────────────────────────────────────────────────┐
│         业务层 (Business Logic)                 │
│  SessionService / ThreadService                │
│  - 无存储细节，纯业务逻辑                       │
└────────────────┬────────────────────────────────┘
                 │ 依赖
┌────────────────▼────────────────────────────────┐
│         仓储层 (Repository)    [新增]           │
│  SessionRepository / ThreadRepository           │
│  - 协调多存储                                    │
│  - 实体与数据模型转换                           │
│  - 查询逻辑编排                                 │
└────────────────┬────────────────────────────────┘
                 │ 依赖
┌────────────────▼────────────────────────────────┐
│      适配器层 (Adapters)                        │
│  - IUnifiedSessionStorage (接口)  [新增]        │
│  - IUnifiedThreadStorage (接口)   [新增]        │
│  - SQLiteSessionBackend / FileSessionBackend   │
│  - SQLiteThreadBackend / MemoryThreadBackend   │
└────────────────┬────────────────────────────────┘
                 │ 依赖
┌────────────────▼────────────────────────────────┐
│      存储引擎层 (Storage Engines)               │
│  - SQLiteStorage / FileStorage / MemoryStorage  │
│  - 已有实现在 src/adapters/storage/backends/  │
└─────────────────────────────────────────────────┘
```

---

## 详细实现方案

### Step 1: 定义统一的存储接口 (src/interfaces/)

#### 1.1 统一的 Session 存储接口
```python
# src/interfaces/sessions/storage.py (修改)

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.core.sessions.entities import Session, SessionStatus

class ISessionRepository(ABC):
    """会话仓储接口 - 协调所有会话存储操作"""
    
    @abstractmethod
    async def create(self, session: Session) -> bool:
        """创建会话"""
        pass
    
    @abstractmethod
    async def get(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        pass
    
    @abstractmethod
    async def update(self, session: Session) -> bool:
        """更新会话"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除会话"""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: SessionStatus) -> List[Session]:
        """按状态列会话"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Session]:
        """搜索会话"""
        pass
    
    @abstractmethod
    async def get_session_count_by_status(self) -> Dict[str, int]:
        """获取各状态会话数量"""
        pass
    
    # 交互历史管理 (新增)
    @abstractmethod
    async def add_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """添加用户交互"""
        pass
    
    @abstractmethod
    async def get_interactions(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取交互历史"""
        pass
```

#### 1.2 统一的 Thread 存储接口
```python
# src/interfaces/threads/storage.py (修改)

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from src.core.threads.entities import Thread, ThreadStatus

class IThreadRepository(ABC):
    """线程仓储接口 - 协调所有线程存储操作"""
    
    @abstractmethod
    async def create(self, thread: Thread) -> bool:
        """创建线程"""
        pass
    
    @abstractmethod
    async def get(self, thread_id: str) -> Optional[Thread]:
        """获取线程"""
        pass
    
    @abstractmethod
    async def update(self, thread: Thread) -> bool:
        """更新线程"""
        pass
    
    @abstractmethod
    async def delete(self, thread_id: str) -> bool:
        """删除线程"""
        pass
    
    @abstractmethod
    async def list_by_session(self, session_id: str) -> List[Thread]:
        """按会话列线程"""
        pass
    
    @abstractmethod
    async def list_by_status(self, status: ThreadStatus) -> List[Thread]:
        """按状态列线程"""
        pass
    
    @abstractmethod
    async def search(
        self, 
        query: str, 
        session_id: Optional[str] = None, 
        limit: int = 10
    ) -> List[Thread]:
        """搜索线程"""
        pass
```

#### 1.3 存储后端接口 (Backend)
```python
# src/interfaces/sessions/backends.py (新增)

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from src.core.sessions.entities import Session, SessionStatus

class ISessionStorageBackend(ABC):
    """会话存储后端接口 - 单一存储实现"""
    
    @abstractmethod
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        pass
    
    @abstractmethod
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """删除会话数据"""
        pass
    
    @abstractmethod
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键"""
        pass
```

---

### Step 2: 实现仓储层 (src/services/)

#### 2.1 Session 仓储实现
```python
# src/services/session/repository.py (新增)

import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

from src.interfaces.sessions.storage import ISessionRepository
from src.interfaces.sessions.backends import ISessionStorageBackend
from src.core.sessions.entities import Session, SessionStatus
from src.core.common.exceptions import StorageError

logger = logging.getLogger(__name__)

class SessionRepository(ISessionRepository):
    """会话仓储实现 - 协调多个存储后端"""
    
    def __init__(self, 
                 primary_backend: ISessionStorageBackend,
                 secondary_backends: Optional[List[ISessionStorageBackend]] = None):
        """
        Args:
            primary_backend: 主存储后端（必须）
            secondary_backends: 辅助存储后端列表，用于冗余和查询扩展
        """
        self.primary_backend = primary_backend
        self.secondary_backends = secondary_backends or []
    
    async def create(self, session: Session) -> bool:
        """创建会话 - 保存到所有后端"""
        try:
            # 将 Session 实体转换为存储格式
            data = self._session_to_dict(session)
            
            # 保存到主后端
            if not await self.primary_backend.save(session.session_id, data):
                raise StorageError("Failed to save to primary backend")
            
            # 保存到辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(session.session_id, data)
                except Exception as e:
                    logger.warning(f"Failed to save to secondary backend: {e}")
            
            logger.info(f"Session created: {session.session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise StorageError(f"Failed to create session: {e}")
    
    async def get(self, session_id: str) -> Optional[Session]:
        """获取会话 - 优先从主后端读取"""
        try:
            # 从主后端读取
            data = await self.primary_backend.load(session_id)
            if data is None:
                # 尝试从辅助后端读取
                for backend in self.secondary_backends:
                    try:
                        data = await backend.load(session_id)
                        if data:
                            break
                    except Exception:
                        continue
            
            if data:
                return self._dict_to_session(data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def update(self, session: Session) -> bool:
        """更新会话 - 更新所有后端"""
        try:
            data = self._session_to_dict(session)
            
            # 更新主后端
            if not await self.primary_backend.save(session.session_id, data):
                raise StorageError("Failed to update primary backend")
            
            # 更新辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.save(session.session_id, data)
                except Exception as e:
                    logger.warning(f"Failed to update secondary backend: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to update session: {e}")
            raise StorageError(f"Failed to update session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话 - 删除所有后端"""
        try:
            # 删除主后端
            primary_deleted = await self.primary_backend.delete(session_id)
            
            # 删除辅助后端
            for backend in self.secondary_backends:
                try:
                    await backend.delete(session_id)
                except Exception as e:
                    logger.warning(f"Failed to delete from secondary backend: {e}")
            
            return primary_deleted
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            raise StorageError(f"Failed to delete session: {e}")
    
    async def add_interaction(self, session_id: str, interaction: Dict[str, Any]) -> bool:
        """添加交互"""
        try:
            session = await self.get(session_id)
            if not session:
                raise StorageError(f"Session not found: {session_id}")
            
            # 交互保存在会话元数据中
            if "interactions" not in session.metadata:
                session.metadata["interactions"] = []
            
            session.metadata["interactions"].append(interaction)
            session.updated_at = datetime.now()
            
            return await self.update(session)
            
        except Exception as e:
            logger.error(f"Failed to add interaction: {e}")
            raise StorageError(f"Failed to add interaction: {e}")
    
    async def get_interactions(self, session_id: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取交互"""
        try:
            session = await self.get(session_id)
            if not session:
                return []
            
            interactions = session.metadata.get("interactions", [])
            if limit:
                interactions = interactions[-limit:]
            
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to get interactions: {e}")
            return []
    
    # === 私有方法 ===
    
    def _session_to_dict(self, session: Session) -> Dict[str, Any]:
        """会话实体转为字典"""
        return {
            "session_id": session.session_id,
            "status": session.status.value,
            "message_count": session.message_count,
            "checkpoint_count": session.checkpoint_count,
            "created_at": session.created_at.isoformat(),
            "updated_at": session.updated_at.isoformat(),
            "metadata": session.metadata,
            "tags": session.tags,
            "thread_ids": session.thread_ids
        }
    
    def _dict_to_session(self, data: Dict[str, Any]) -> Session:
        """字典转为会话实体"""
        return Session(
            session_id=data["session_id"],
            _status=SessionStatus(data["status"]),
            message_count=data.get("message_count", 0),
            checkpoint_count=data.get("checkpoint_count", 0),
            _created_at=datetime.fromisoformat(data["created_at"]),
            _updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
            tags=data.get("tags", []),
            thread_ids=data.get("thread_ids", [])
        )
```

---

### Step 3: 实现具体的存储后端 (src/adapters/storage/)

#### 3.1 重构 SQLiteSessionBackend
```python
# src/adapters/storage/backends/sqlite_session_backend.py (新增)

import json
import sqlite3
from typing import Dict, Any, Optional, List
from pathlib import Path

from src.interfaces.sessions.backends import ISessionStorageBackend
from src.core.common.exceptions import StorageError

class SQLiteSessionBackend(ISessionStorageBackend):
    """SQLite 会话存储后端"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    message_count INTEGER DEFAULT 0,
                    checkpoint_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP NOT NULL,
                    updated_at TIMESTAMP NOT NULL,
                    metadata TEXT,
                    tags TEXT,
                    thread_ids TEXT
                )
            """)
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)")
            conn.commit()
    
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO sessions 
                    (session_id, status, message_count, checkpoint_count, 
                     created_at, updated_at, metadata, tags, thread_ids)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    data["session_id"],
                    data["status"],
                    data.get("message_count", 0),
                    data.get("checkpoint_count", 0),
                    data["created_at"],
                    data["updated_at"],
                    json.dumps(data.get("metadata", {})),
                    json.dumps(data.get("tags", [])),
                    json.dumps(data.get("thread_ids", []))
                ))
                conn.commit()
                return True
        except Exception as e:
            raise StorageError(f"Failed to save session: {e}")
    
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT * FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                row = cursor.fetchone()
                if not row:
                    return None
                
                return {
                    "session_id": row[0],
                    "status": row[1],
                    "message_count": row[2],
                    "checkpoint_count": row[3],
                    "created_at": row[4],
                    "updated_at": row[5],
                    "metadata": json.loads(row[6]) if row[6] else {},
                    "tags": json.loads(row[7]) if row[7] else [],
                    "thread_ids": json.loads(row[8]) if row[8] else []
                }
        except Exception as e:
            raise StorageError(f"Failed to load session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话数据"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            raise StorageError(f"Failed to delete session: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                if prefix:
                    cursor = conn.execute(
                        "SELECT session_id FROM sessions WHERE session_id LIKE ?",
                        (f"{prefix}%",)
                    )
                else:
                    cursor = conn.execute("SELECT session_id FROM sessions")
                
                return [row[0] for row in cursor.fetchall()]
        except Exception as e:
            raise StorageError(f"Failed to list keys: {e}")
```

#### 3.2 FileSystem 后端
```python
# src/adapters/storage/backends/file_session_backend.py (新增)

import json
from pathlib import Path
from typing import Dict, Any, Optional, List

from src.interfaces.sessions.backends import ISessionStorageBackend
from src.core.common.exceptions import StorageError

class FileSessionBackend(ISessionStorageBackend):
    """文件系统会话存储后端"""
    
    def __init__(self, base_path: str = "./sessions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        try:
            session_file = self.base_path / f"{session_id}.json"
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            raise StorageError(f"Failed to save session: {e}")
    
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据"""
        try:
            session_file = self.base_path / f"{session_id}.json"
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            raise StorageError(f"Failed to load session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话数据"""
        try:
            session_file = self.base_path / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                return True
            return False
        except Exception as e:
            raise StorageError(f"Failed to delete session: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键"""
        try:
            files = self.base_path.glob(f"{prefix}*.json")
            return [f.stem for f in files]
        except Exception as e:
            raise StorageError(f"Failed to list keys: {e}")
```

---

### Step 4: 服务层集成

#### 4.1 修改 SessionService
```python
# src/services/session/service.py (修改)

class SessionService(ISessionService):
    
    def __init__(
        self,
        session_core: ISessionCore,
        session_repository: ISessionRepository,  # ✓ 修改：使用仓储而非存储
        thread_service: IThreadService,
        **kwargs
    ):
        """初始化会话服务"""
        self._session_core = session_core
        self._session_repository = session_repository  # ✓
        self._thread_service = thread_service
    
    async def create_session(self, user_request: UserRequest) -> str:
        """创建用户会话"""
        try:
            # 1. 创建核心实体
            session_entity = self._session_core.create_session(...)
            
            # 2. 转换为业务实体（Session）
            session = self._entity_to_session(session_entity)
            
            # 3. 保存到仓储（自动协调所有后端）
            await self._session_repository.create(session)  # ✓
            
            return session.session_id
        except Exception as e:
            raise ValidationError(f"创建会话失败: {str(e)}")
    
    async def track_user_interaction(self, session_id: str, interaction: UserInteraction) -> None:
        """追踪用户交互"""
        try:
            interaction_dict = {
                "interaction_id": interaction.interaction_id,
                "session_id": interaction.session_id,
                "thread_id": interaction.thread_id,
                "interaction_type": interaction.interaction_type,
                "content": interaction.content,
                "metadata": interaction.metadata,
                "timestamp": interaction.timestamp.isoformat()
            }
            
            # ✓ 通过仓储添加交互
            await self._session_repository.add_interaction(session_id, interaction_dict)
            
        except Exception as e:
            logger.error(f"追踪用户交互失败: {e}")
```

---

### Step 5: 依赖注入配置

#### 5.1 DI 容器配置
```python
# src/services/container/session_bindings.py (修改)

from src.adapters.storage.backends.sqlite_session_backend import SQLiteSessionBackend
from src.adapters.storage.backends.file_session_backend import FileSessionBackend
from src.services.session.repository import SessionRepository
from src.services.session.service import SessionService

def register_session_services(container: DIContainer, config: Dict[str, Any]):
    """注册会话相关服务"""
    
    # 1. 注册存储后端
    # 主后端：SQLite（持久化）
    sqlite_backend = SQLiteSessionBackend(
        db_path=config.get("session_db_path", "./data/sessions.db")
    )
    container.register_singleton('session_sqlite_backend', sqlite_backend)
    
    # 辅助后端：文件系统（备份）
    file_backend = FileSessionBackend(
        base_path=config.get("session_storage_path", "./sessions")
    )
    container.register_singleton('session_file_backend', file_backend)
    
    # 2. 注册仓储
    def session_repository_factory():
        return SessionRepository(
            primary_backend=sqlite_backend,
            secondary_backends=[file_backend]
        )
    
    container.register_singleton('session_repository', session_repository_factory)
    
    # 3. 注册服务
    def session_service_factory(container):
        return SessionService(
            session_core=container.get('session_core'),
            session_repository=container.get('session_repository'),
            thread_service=container.get('thread_service'),
            **config
        )
    
    container.register_singleton('session_service', session_service_factory)
```

---

## 迁移路径

### Phase 1: 准备（不破坏现有代码）
1. 创建新接口：`ISessionRepository`, `ISessionStorageBackend`
2. 实现新后端：`SQLiteSessionBackend`, `FileSessionBackend`
3. 实现新仓储：`SessionRepository`
4. 保留旧的 `SQLiteSessionStore` 和 `SQLiteThreadStore`

### Phase 2: 切换
1. 修改 `SessionService` 依赖注入配置，使用新仓储
2. 更新单元测试
3. 集成测试验证

### Phase 3: 清理
1. 删除 `SQLiteSessionStore`
2. 删除 `SQLiteThreadStore`
3. 删除旧的存储-实体耦合代码

---

## 核心优势

| 方面 | 改进 |
|------|------|
| **架构清晰** | 分离了业务层、仓储层、适配器层，职责明确 |
| **低耦合** | 服务层与具体存储实现解耦，支持多存储 |
| **易测试** | 可以轻松 Mock 仓储和后端进行单元测试 |
| **扩展性** | 新增存储类型只需实现后端接口 |
| **数据一致性** | 仓储层统一协调所有后端操作 |
| **运维友好** | 支持热切换存储后端，冗余备份 |

---

## 配置示例

```yaml
# configs/storage.yaml

session:
  primary_backend: sqlite
  secondary_backends:
    - file
  
  sqlite:
    db_path: ./data/sessions.db
  
  file:
    base_path: ./sessions_backup

thread:
  primary_backend: sqlite
  secondary_backends: []
  
  sqlite:
    db_path: ./data/threads.db
```

---

## 相关文档

- [AGENTS.md](./AGENTS.md) - 架构依赖规则
- [docs/STORAGE_MIGRATION.md](./docs/STORAGE_MIGRATION.md) - 存储迁移指南
