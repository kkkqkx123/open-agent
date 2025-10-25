# 后端数据处理与持久化分析

## 1. 当前数据存储结构分析

### 1.1 会话数据存储
**存储位置**: `sessions/` 目录
**存储格式**: JSON文件
**文件命名**: `{session_id}.json`
**数据结构**:
```json
{
  "metadata": {
    "session_id": "react-251022-174800-1f73e8",
    "workflow_config_path": "configs/workflows/react.yaml",
    "workflow_id": "react_20241022_174800_1f73e8",
    "agent_config": {...},
    "created_at": "2024-10-22T17:48:00Z",
    "updated_at": "2024-10-22T17:48:30Z",
    "status": "active"
  },
  "state": {
    "messages": [...],
    "tool_results": [...],
    "current_step": "think",
    "max_iterations": 10,
    "iteration_count": 3,
    "workflow_name": "react",
    "start_time": "2024-10-22T17:48:00Z",
    "errors": []
  },
  "workflow_config": {...}
}
```

### 1.2 历史数据存储
**存储位置**: `history/` 目录
**存储格式**: JSON Lines (每行一个JSON记录)
**文件命名**: `{YYYYMM}/{session_id}.jsonl`
**记录类型**:
- `message`: 用户/助手消息
- `tool_call`: 工具调用记录
- `llm_request`: LLM请求记录
- `llm_response`: LLM响应记录
- `token_usage`: Token使用记录
- `cost`: 成本记录

**示例记录**:
```jsonl
{"record_id": "msg_123", "session_id": "react-251022-174800-1f73e8", "timestamp": "2024-10-22T17:48:00Z", "record_type": "message", "message_type": "user", "content": "Hello", "metadata": {}}
{"record_id": "tool_456", "session_id": "react-251022-174800-1f73e8", "timestamp": "2024-10-22T17:48:01Z", "record_type": "tool_call", "tool_name": "search", "tool_input": {"query": "test"}, "tool_output": {"results": [...]}, "metadata": {}}
{"record_id": "token_789", "session_id": "react-251022-174800-1f73e8", "timestamp": "2024-10-22T17:48:02Z", "record_type": "token_usage", "model": "gpt-3.5-turbo", "prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150, "source": "api_call"}
```

### 1.3 配置数据存储
**存储位置**: `configs/` 目录
**存储格式**: YAML文件
**分类存储**:
- `global.yaml`: 全局配置
- `llms/`: 模型配置
- `workflows/`: 工作流配置
- `agents/`: Agent配置

## 2. 后端需要处理的数据类型分析

### 2.1 会话相关数据

#### 2.1.1 会话元数据
- **session_id**: 会话唯一标识
- **workflow_config_path**: 工作流配置路径
- **workflow_id**: 工作流实例ID
- **agent_config**: Agent配置信息
- **created_at**: 创建时间
- **updated_at**: 更新时间
- **status**: 会话状态 (active, paused, completed, error)

#### 2.1.2 会话状态数据
- **messages**: 消息历史
- **tool_results**: 工具调用结果
- **current_step**: 当前执行步骤
- **iteration_count**: 迭代计数
- **max_iterations**: 最大迭代次数
- **workflow_name**: 工作流名称
- **start_time**: 开始时间
- **errors**: 错误列表

#### 2.1.3 会话统计信息
- **total_sessions**: 总会话数
- **active_sessions**: 活跃会话数
- **avg_duration**: 平均会话时长
- **success_rate**: 成功率
- **error_count**: 错误计数

### 2.2 工作流相关数据

#### 2.2.1 工作流配置数据
- **workflow_id**: 工作流ID
- **name**: 工作流名称
- **description**: 工作流描述
- **version**: 版本号
- **nodes**: 节点定义
- **edges**: 连接定义
- **config_path**: 配置文件路径

#### 2.2.2 工作流执行数据
- **execution_path**: 执行路径
- **node_states**: 节点状态
- **current_node**: 当前节点
- **execution_time**: 执行时间
- **performance_metrics**: 性能指标

#### 2.2.3 工作流可视化数据
- **node_positions**: 节点位置
- **layout_algorithm**: 布局算法
- **visualization_settings**: 可视化设置

### 2.3 分析统计相关数据

#### 2.3.1 性能指标数据
- **response_time**: 响应时间
- **throughput**: 吞吐量
- **error_rate**: 错误率
- **resource_usage**: 资源使用率

#### 2.3.2 Token使用数据
- **prompt_tokens**: 输入Token数
- **completion_tokens**: 输出Token数
- **total_tokens**: 总Token数
- **model**: 使用的模型
- **cost**: 成本估算

#### 2.3.3 成本分析数据
- **total_cost**: 总成本
- **cost_by_model**: 按模型分类成本
- **cost_by_session**: 按会话分类成本
- **cost_trends**: 成本趋势

### 2.4 错误相关数据

#### 2.4.1 错误记录数据
- **error_id**: 错误ID
- **error_type**: 错误类型
- **error_message**: 错误消息
- **stack_trace**: 堆栈跟踪
- **timestamp**: 发生时间
- **session_id**: 关联会话ID
- **severity**: 严重程度

#### 2.4.2 错误统计信息
- **error_count**: 错误总数
- **error_by_type**: 按类型分类错误
- **error_by_session**: 按会话分类错误
- **error_trends**: 错误趋势

### 2.5 历史数据

#### 2.5.1 消息历史数据
- **message_type**: 消息类型 (user, assistant, system)
- **content**: 消息内容
- **timestamp**: 时间戳
- **metadata**: 元数据

#### 2.5.2 工具调用历史数据
- **tool_name**: 工具名称
- **tool_input**: 工具输入
- **tool_output**: 工具输出
- **success**: 是否成功
- **execution_time**: 执行时间

#### 2.5.3 LLM调用历史数据
- **model**: 使用的模型
- **provider**: 提供商
- **messages**: 消息列表
- **parameters**: 参数
- **response**: 响应内容
- **token_usage**: Token使用情况

## 3. 数据持久化需求分析

### 3.1 需要持久化的数据

#### 3.1.1 会话持久化
- **会话元数据**：必须持久化，支持会话恢复
- **会话状态**：定期保存，支持断点续传
- **会话统计**：聚合数据，支持性能分析

#### 3.1.2 历史数据持久化
- **消息历史**：完整记录，支持审计和回放
- **工具调用历史**：详细记录，支持调试和分析
- **LLM调用历史**：完整记录，支持成本分析
- **性能指标历史**：时间序列数据，支持趋势分析

#### 3.1.3 配置数据持久化
- **用户配置**：个性化设置
- **系统配置**：全局参数
- **工作流配置**：工作流定义

#### 3.1.4 分析数据持久化
- **聚合统计数据**：预计算的统计结果
- **趋势数据**：时间序列分析结果
- **报告数据**：生成的分析报告

### 3.2 临时数据（不需要持久化）
- **实时状态**：当前执行状态（内存中）
- **缓存数据**：可重新计算的数据
- **会话临时数据**：运行时的临时变量

## 4. 存储方案选择

### 4.1 首选方案：SQLite + JSON Lines

#### 4.1.1 SQLite数据库
**适用场景**：
- 结构化查询需求（会话元数据、配置数据、统计数据）
- 关系型数据（会话-历史记录关联）
- 聚合查询和统计

**数据库设计**：
```sql
-- 会话表
CREATE TABLE sessions (
    session_id TEXT PRIMARY KEY,
    workflow_config_path TEXT NOT NULL,
    workflow_id TEXT,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    agent_config TEXT, -- JSON存储
    metadata TEXT -- JSON存储
);

-- 工作流表
CREATE TABLE workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    version TEXT,
    config_path TEXT,
    loaded_at TIMESTAMP,
    last_used TIMESTAMP,
    usage_count INTEGER DEFAULT 0,
    config_data TEXT -- JSON存储
);

-- 统计数据表
CREATE TABLE statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    metric_type TEXT NOT NULL,
    metric_value REAL NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 错误记录表
CREATE TABLE errors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    severity TEXT DEFAULT 'error',
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

-- 配置表
CREATE TABLE configurations (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    config_type TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引优化
CREATE INDEX idx_sessions_status ON sessions(status);
CREATE INDEX idx_sessions_created_at ON sessions(created_at);
CREATE INDEX idx_statistics_session_metric ON statistics(session_id, metric_type);
CREATE INDEX idx_errors_session_timestamp ON errors(session_id, timestamp);
```

#### 4.1.2 JSON Lines文件
**适用场景**：
- 大量时间序列数据（历史记录）
- 追加写入频繁的数据
- 需要按时间范围查询的数据

**文件结构**：
```
data/
├── history/
│   ├── 202410/           # 按月分目录
│   │   ├── session_001.jsonl
│   │   ├── session_002.jsonl
│   │   └── aggregated_202410.jsonl  # 聚合数据
│   └── 202411/
├── sessions/
│   ├── metadata.db       # SQLite数据库
│   └── index.json        # 会话索引
└── cache/
    ├── statistics/
    └── trends/
```

### 4.2 备选方案：纯JSON Lines + 索引文件

#### 4.2.1 适用场景
- 简单的键值查询
- 时间序列数据为主
- 不需要复杂关联查询

#### 4.2.2 实现方案
```python
# 会话索引文件 (sessions/index.json)
{
  "sessions": {
    "react-251022-174800-1f73e8": {
      "metadata_file": "sessions/react-251022-174800-1f73e8_meta.json",
      "history_file": "history/202410/react-251022-174800-1f73e8.jsonl",
      "created_at": "2024-10-22T17:48:00Z",
      "updated_at": "2024-10-22T17:48:30Z",
      "status": "active"
    }
  },
  "statistics": {
    "total_sessions": 150,
    "active_sessions": 12,
    "last_updated": "2024-10-22T18:00:00Z"
  }
}
```

## 5. 主项目中直接实现的功能

### 5.1 数据访问层（在主项目中实现）
```python
# src/presentation/api/data_access/session_dao.py
from typing import Optional, Dict, Any, List
from datetime import datetime
import aiosqlite
import json
from pathlib import Path

class SessionDAO:
    """会话数据访问对象"""
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
    
    async def initialize(self):
        """初始化数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    workflow_config_path TEXT NOT NULL,
                    workflow_id TEXT,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    agent_config TEXT,
                    metadata TEXT
                )
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_status ON sessions(status)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_sessions_created_at ON sessions(created_at)
            """)
            await db.commit()
    
    async def create_session(self, session_data: Dict[str, Any]) -> bool:
        """创建会话"""
        metadata = session_data.get("metadata", {})
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO sessions (
                    session_id, workflow_config_path, workflow_id, status,
                    created_at, updated_at, agent_config, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.get("session_id"),
                metadata.get("workflow_config_path"),
                metadata.get("workflow_id"),
                metadata.get("status", "active"),
                metadata.get("created_at"),
                metadata.get("updated_at"),
                json.dumps(metadata.get("agent_config", {})),
                json.dumps(metadata.get("metadata", {}))
            ))
            await db.commit()
            return True
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return {
                        "session_id": row[0],
                        "workflow_config_path": row[1],
                        "workflow_id": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "updated_at": row[5],
                        "agent_config": json.loads(row[6]) if row[6] else {},
                        "metadata": json.loads(row[7]) if row[7] else {}
                    }
                return None
    
    async def list_sessions(
        self, 
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """列出会话"""
        query = "SELECT * FROM sessions"
        params = []
        
        if status:
            query += " WHERE status = ?"
            params.append(status)
        
        query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                sessions = []
                for row in rows:
                    sessions.append({
                        "session_id": row[0],
                        "workflow_config_path": row[1],
                        "workflow_id": row[2],
                        "status": row[3],
                        "created_at": row[4],
                        "updated_at": row[5],
                        "agent_config": json.loads(row[6]) if row[6] else {},
                        "metadata": json.loads(row[7]) if row[7] else {}
                    })
                return sessions
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE sessions SET status = ?, updated_at = ? WHERE session_id = ?",
                (status, datetime.now().isoformat(), session_id)
            )
            await db.commit()
            return cursor.rowcount > 0
    
    async def delete_session(self, session_id: str) -> bool:
        """删除会话"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "DELETE FROM sessions WHERE session_id = ?", (session_id,)
            )
            await db.commit()
            return cursor.rowcount > 0
```

### 5.2 历史数据访问层（在主项目中实现）
```python
# src/presentation/api/data_access/history_dao.py
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

class HistoryDAO:
    """历史数据访问对象"""
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话历史文件路径"""
        date_prefix = datetime.now().strftime("%Y%m")
        session_dir = self.base_path / "history" / date_prefix
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir / f"{session_id}.jsonl"
    
    def store_record(self, session_id: str, record_data: Dict[str, Any]) -> bool:
        """存储历史记录"""
        try:
            session_file = self._get_session_file(session_id)
            with open(session_file, 'a', encoding='utf-8') as f:
                json.dump(record_data, f, ensure_ascii=False)
                f.write('\n')
            return True
        except Exception:
            return False
    
    def get_session_records(
        self, 
        session_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        record_types: Optional[List[str]] = None,
        limit: int = 1000,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取会话历史记录"""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        records = []
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    if line.strip():
                        try:
                            record = json.loads(line)
                            
                            # 应用过滤条件
                            if start_time or end_time:
                                record_time = datetime.fromisoformat(record.get('timestamp', ''))
                                if start_time and record_time < start_time:
                                    continue
                                if end_time and record_time > end_time:
                                    continue
                            
                            if record_types and record.get('record_type') not in record_types:
                                continue
                            
                            # 应用分页
                            if len(records) >= offset + limit:
                                break
                                
                            if len(records) >= offset:
                                records.append(record)
                                
                        except json.JSONDecodeError:
                            continue
                            
        except Exception:
            pass
        
        return records[offset:offset + limit]
    
    def search_session_records(
        self,
        session_id: str,
        query: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """搜索会话历史记录"""
        session_file = self._get_session_file(session_id)
        if not session_file.exists():
            return []
        
        results = []
        query_lower = query.lower()
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            record = json.loads(line)
                            
                            # 搜索内容
                            content = ""
                            if record.get('record_type') == 'message':
                                content = record.get('content', '')
                            elif record.get('record_type') == 'tool_call':
                                content = str(record.get('tool_input', '')) + str(record.get('tool_output', ''))
                            
                            if query_lower in content.lower():
                                results.append(record)
                                if len(results) >= limit:
                                    break
                                    
                        except json.JSONDecodeError:
                            continue
                            
        except Exception:
            pass
        
        return results
    
    def export_session_data(
        self,
        session_id: str,
        format: str = 'json'
    ) -> Dict[str, Any]:
        """导出会话数据"""
        records = self.get_session_records(session_id, limit=10000)  # 获取所有记录
        
        if format == 'json':
            return {
                "session_id": session_id,
                "export_time": datetime.now().isoformat(),
                "total_records": len(records),
                "records": records
            }
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            if records:
                # 获取所有可能的字段
                all_fields = set()
                for record in records:
                    all_fields.update(record.keys())
                
                writer = csv.DictWriter(output, fieldnames=sorted(all_fields))
                writer.writeheader()
                
                for record in records:
                    writer.writerow(record)
            
            return {
                "session_id": session_id,
                "format": "csv",
                "content": output.getvalue()
            }
        else:
            raise ValueError(f"不支持的导出格式: {format}")
```

### 5.3 统计和聚合服务（在主项目中实现）
```python
# src/presentation/api/services/statistics_service.py
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import asyncio

class StatisticsService:
    """统计服务"""
    
    def __init__(self, session_dao, history_dao):
        self.session_dao = session_dao
        self.history_dao = history_dao
    
    async def get_session_statistics(self, session_id: str) -> Dict[str, Any]:
        """获取会话统计信息"""
        # 获取会话基本信息
        session = await self.session_dao.get_session(session_id)
        if not session:
            return {}
        
        # 获取历史记录统计
        all_records = self.history_dao.get_session_records(session_id, limit=10000)
        
        # 计算统计信息
        message_count = len([r for r in all_records if r.get('record_type') == 'message'])
        tool_call_count = len([r for r in all_records if r.get('record_type') == 'tool_call'])
        error_count = len([r for r in all_records if r.get('record_type') == 'error'])
        
        # 计算时间范围
        if all_records:
            start_time = min(r.get('timestamp', '') for r in all_records)
            end_time = max(r.get('timestamp', '') for r in all_records)
            duration = self._calculate_duration(start_time, end_time)
        else:
            duration = 0
        
        return {
            "session_id": session_id,
            "total_messages": message_count,
            "total_tool_calls": tool_call_count,
            "total_errors": error_count,
            "duration_seconds": duration,
            "success_rate": (message_count - error_count) / message_count * 100 if message_count > 0 else 100
        }
    
    async def get_performance_metrics(
        self,
        session_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """获取性能指标"""
        if session_id:
            # 单个会话的性能指标
            return await self._get_session_performance_metrics(session_id)
        else:
            # 系统整体的性能指标
            return await self._get_system_performance_metrics(start_time, end_time)
    
    async def _get_session_performance_metrics(self, session_id: str) -> Dict[str, Any]:
        """获取单个会话的性能指标"""
        records = self.history_dao.get_session_records(session_id, limit=1000)
        
        # 计算响应时间
        response_times = []
        for i, record in enumerate(records):
            if record.get('record_type') == 'llm_response':
                response_time = record.get('response_time', 0)
                if response_time:
                    response_times.append(response_time)
        
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
        else:
            avg_response_time = max_response_time = min_response_time = 0
        
        # Token使用统计
        token_records = [r for r in records if r.get('record_type') == 'token_usage']
        total_tokens = sum(r.get('total_tokens', 0) for r in token_records)
        
        return {
            "session_id": session_id,
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "total_tokens": total_tokens,
            "request_count": len(response_times)
        }
    
    def _calculate_duration(self, start_time: str, end_time: str) -> float:
        """计算时间间隔（秒）"""
        try:
            start = datetime.fromisoformat(start_time)
            end = datetime.fromisoformat(end_time)
            return (end - start).total_seconds()
        except:
            return 0
```

## 6. 缓存策略

### 6.1 内存缓存
```python
# src/presentation/api/cache/memory_cache.py
from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import asyncio

class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self, default_ttl: int = 300):  # 默认5分钟
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = default_ttl
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        async with self._lock:
            if key in self._cache:
                item = self._cache[key]
                if item['expires_at'] > datetime.now():
                    return item['value']
                else:
                    # 过期，删除
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存值"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': expires_at
            }
    
    async def delete(self, key: str) -> None:
        """删除缓存"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """清空缓存"""
        async with self._lock:
            self._cache.clear()
    
    async def cleanup_expired(self) -> None:
        """清理过期缓存"""
        now = datetime.now()
        async with self._lock:
            expired_keys = [
                key for key, item in self._cache.items()
                if item['expires_at'] <= now
            ]
            for key in expired_keys:
                del self._cache[key]
```

### 6.2 缓存应用示例
```python
# 在API服务中使用缓存
class SessionService:
    def __init__(self, session_dao, cache):
        self.session_dao = session_dao
        self.cache = cache
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话（带缓存）"""
        # 先检查缓存
        cached_session = await self.cache.get(f"session:{session_id}")
        if cached_session:
            return cached_session
        
        # 缓存未命中，查询数据库
        session = await self.session_dao.get_session(session_id)
        if session:
            # 存入缓存
            await self.cache.set(f"session:{session_id}", session, ttl=60)
        
        return session
    
    async def update_session_status(self, session_id: str, status: str) -> bool:
        """更新会话状态（清除缓存）"""
        success = await self.session_dao.update_session_status(session_id, status)
        if success:
            # 清除相关缓存
            await self.cache.delete(f"session:{session_id}")
            await self.cache.delete("sessions:list")  # 清除列表缓存
        
        return success
```

## 7. 数据备份和恢复策略

### 7.1 自动备份
```python
# src/presentation/api/backup/backup_service.py
import shutil
from pathlib import Path
from datetime import datetime
import asyncio

class BackupService:
    """数据备份服务"""
    
    def __init__(self, data_path: Path, backup_path: Path):
        self.data_path = data_path
        self.backup_path = backup_path
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    async def create_backup(self, backup_name: Optional[str] = None) -> Path:
        """创建数据备份"""
        if not backup_name:
            backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.backup_path / backup_name
        backup_dir.mkdir(exist_ok=True)
        
        # 备份SQLite数据库
        db_file = self.data_path / "sessions" / "metadata.db"
        if db_file.exists():
            await asyncio.to_thread(
                shutil.copy2, db_file, backup_dir / "metadata.db"
            )
        
        # 备份历史数据
        history_dir = self.data_path / "history"
        if history_dir.exists():
            await asyncio.to_thread(
                shutil.copytree, history_dir, backup_dir / "history"
            )
        
        # 备份会话数据
        sessions_dir = self.data_path / "sessions"
        if sessions_dir.exists():
            await asyncio.to_thread(
                shutil.copytree, sessions_dir, backup_dir / "sessions"
            )
        
        # 创建备份元数据
        metadata = {
            "backup_name": backup_name,
            "created_at": datetime.now().isoformat(),
            "data_path": str(self.data_path),
            "backup_path": str(backup_dir)
        }
        
        with open(backup_dir / "metadata.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        
        return backup_dir
    
    async def restore_backup(self, backup_name: str) -> bool:
        """恢复数据备份"""
        backup_dir = self.backup_path / backup_name
        if not backup_dir.exists():
            return False
        
        try:
            # 读取备份元数据
            with open(backup_dir / "metadata.json", 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            # 恢复数据库
            db_backup = backup_dir / "metadata.db"
            if db_backup.exists():
                target_db = self.data_path / "sessions" / "metadata.db"
                target_db.parent.mkdir(parents=True, exist_ok=True)
                await asyncio.to_thread(
                    shutil.copy2, db_backup, target_db
                )
            
            # 恢复历史数据
            history_backup = backup_dir / "history"
            if history_backup.exists():
                target_history = self.data_path / "history"
                if target_history.exists():
                    await asyncio.to_thread(shutil.rmtree, target_history)
                await asyncio.to_thread(
                    shutil.copytree, history_backup, target_history
                )
            
            # 恢复会话数据
            sessions_backup = backup_dir / "sessions"
            if sessions_backup.exists():
                target_sessions = self.data_path / "sessions"
                if target_sessions.exists():
                    await asyncio.to_thread(shutil.rmtree, target_sessions)
                await asyncio.to_thread(
                    shutil.copytree, sessions_backup, target_sessions
                )
            
            return True
            
        except Exception as e:
            print(f"恢复备份失败: {e}")
            return False
```

## 8. 数据迁移策略

### 8.1 从现有文件系统迁移
```python
# src/presentation/api/migration/file_system_migration.py
import json
from pathlib import Path
from datetime import datetime

class FileSystemMigration:
    """文件系统数据迁移"""
    
    def __init__(self, old_data_path: Path, new_data_path: Path):
        self.old_data_path = old_data_path
        self.new_data_path = new_data_path
    
    def migrate_sessions(self) -> int:
        """迁移会话数据"""
        migrated_count = 0
        
        # 迁移会话文件
        old_sessions_dir = self.old_data_path / "sessions"
        if old_sessions_dir.exists():
            for session_file in old_sessions_dir.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    # 迁移到新的存储格式
                    self._migrate_session_data(session_data)
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"迁移会话文件失败 {session_file}: {e}")
        
        return migrated_count
    
    def migrate_history(self) -> int:
        """迁移历史数据"""
        migrated_count = 0
        
        # 迁移历史文件
        old_history_dir = self.old_data_path / "history"
        if old_history_dir.exists():
            for history_file in old_history_dir.rglob("*.jsonl"):
                try:
                    new_history_file = self._get_new_history_path(history_file)
                    new_history_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 复制历史文件
                    import shutil
                    shutil.copy2(history_file, new_history_file)
                    migrated_count += 1
                    
                except Exception as e:
                    print(f"迁移历史文件失败 {history_file}: {e}")
        
        return migrated_count
    
    def _migrate_session_data(self, session_data: Dict[str, Any]) -> None:
        """迁移单个会话数据"""
        # 这里可以实现数据格式转换逻辑
        # 例如：更新字段名称、添加新字段、转换数据格式等
        pass
    
    def _get_new_history_path(self, old_path: Path) -> Path:
        """获取新的历史文件路径"""
        # 保持相对路径结构
        relative_path = old_path.relative_to(self.old_data_path / "history")
        return self.new_data_path / "history" / relative_path
```

这个详细的数据分析文档提供了完整的数据处理策略，包括存储方案选择、持久化需求、缓存策略和备份恢复机制，确保后端API能够高效、可靠地处理各种类型的数据。