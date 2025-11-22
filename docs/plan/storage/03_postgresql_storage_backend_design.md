# PostgreSQL存储后端实现方案

## 概述

本文档详细设计PostgreSQL存储后端的实现方案，作为SQLite的企业级升级选项，提供更强的性能、扩展性和功能特性。

## 设计目标

1. **企业级性能**: 利用PostgreSQL的优化器，提供高性能查询
2. **ACID事务**: 完整的事务支持，确保数据一致性
3. **扩展性**: 支持分区、复制、分片等扩展特性
4. **兼容性**: 完全兼容现有的存储接口
5. **可配置**: 丰富的配置选项，适应不同部署场景

## 技术选型

### 1. PostgreSQL驱动

选择 `asyncpg` 作为异步PostgreSQL驱动：
- 高性能异步驱动
- 原生支持PostgreSQL特性
- 连接池管理
- 类型转换支持

### 2. ORM选择

选择 `SQLAlchemy 2.0` 作为ORM：
- 异步支持
- 强大的查询构建器
- 数据库迁移支持
- 连接池集成

### 3. 迁移工具

选择 `Alembic` 作为数据库迁移工具：
- 自动迁移生成
- 版本控制
- 回滚支持

## 架构设计

### 1. 类继承结构

```python
class PostgreSQLStorageBackend(ConnectionPooledStorageBackend):
    """PostgreSQL存储后端实现"""
    
    def __init__(self, **config):
        # 初始化连接池
        # 配置SQLAlchemy引擎
        # 设置表结构
        pass
```

### 2. 核心组件

#### 2.1 连接管理

```python
class PostgreSQLConnectionManager:
    """PostgreSQL连接管理器"""
    
    def __init__(self, config):
        self.config = config
        self.engine = None
        self.session_factory = None
    
    async def initialize(self):
        """初始化数据库连接"""
        pass
    
    async def get_session(self):
        """获取数据库会话"""
        pass
    
    async def close(self):
        """关闭连接"""
        pass
```

#### 2.2 模型定义

```python
from sqlalchemy import Column, String, DateTime, Text, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import JSONB, UUID

Base = declarative_base()

class StorageRecord(Base):
    """存储记录模型"""
    __tablename__ = 'storage_records'
    
    id = Column(String, primary_key=True)
    data = Column(JSONB, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    compressed = Column(Boolean, default=False)
    type = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    thread_id = Column(String, nullable=True)
    metadata = Column(JSONB, nullable=True)
    
    # 索引定义
    __table_args__ = (
        Index('idx_storage_type', 'type'),
        Index('idx_storage_session_id', 'session_id'),
        Index('idx_storage_thread_id', 'thread_id'),
        Index('idx_storage_expires_at', 'expires_at'),
        Index('idx_storage_created_at', 'created_at'),
        Index('idx_storage_data_gin', 'data', postgresql_using='gin'),
    )
```

#### 2.3 查询构建器

```python
class PostgreSQLQueryBuilder:
    """PostgreSQL查询构建器"""
    
    def __init__(self, session):
        self.session = session
        self.query = session.query(StorageRecord)
    
    def filter_by_id(self, item_id: str):
        """按ID过滤"""
        return self.query.filter(StorageRecord.id == item_id)
    
    def filter_by_session(self, session_id: str):
        """按会话ID过滤"""
        return self.query.filter(StorageRecord.session_id == session_id)
    
    def filter_by_thread(self, thread_id: str):
        """按线程ID过滤"""
        return self.query.filter(StorageRecord.thread_id == thread_id)
    
    def filter_by_type(self, data_type: str):
        """按类型过滤"""
        return self.query.filter(StorageRecord.type == data_type)
    
    def filter_by_data(self, filters: Dict[str, Any]):
        """按数据内容过滤"""
        for key, value in filters.items():
            if isinstance(value, dict):
                # 处理复杂查询
                self._apply_complex_filter(key, value)
            else:
                # 简单JSON查询
                self.query = self.query.filter(
                    StorageRecord.data.op('->>')(key) == str(value)
                )
        return self.query
    
    def _apply_complex_filter(self, key: str, value: Dict[str, Any]):
        """应用复杂过滤器"""
        if '$gt' in value:
            self.query = self.query.filter(
                StorageRecord.data.op('->>')(key) > str(value['$gt'])
            )
        elif '$lt' in value:
            self.query = self.query.filter(
                StorageRecord.data.op('->>')(key) < str(value['$lt'])
            )
        elif '$in' in value:
            self.query = self.query.filter(
                StorageRecord.data.op('->>')(key).in_(map(str, value['$in']))
            )
        elif '$like' in value:
            self.query = self.query.filter(
                StorageRecord.data.op('->>')(key).like(value['$like'])
            )
```

## 配置设计

### 1. 基础配置

```yaml
postgresql:
  class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
  description: "PostgreSQL企业级存储后端"
  metadata:
    category: "database"
    features:
      - "acid"
      - "transactional"
      - "indexed"
      - "backup"
      - "partitioning"
      - "replication"
      - "json_support"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "high"
  config:
    # 连接配置
    host: "${POSTGRES_HOST:localhost}"
    port: "${POSTGRES_PORT:5432}"
    database: "${POSTGRES_DB:storage}"
    username: "${POSTGRES_USER:postgres}"
    password: "${POSTGRES_PASSWORD:}"
    
    # 连接池配置
    connection_pool_size: 10
    connection_pool_max_overflow: 20
    connection_pool_timeout: 30
    connection_pool_recycle: 3600
    
    # SSL配置
    ssl_enabled: false
    ssl_cert_file: ""
    ssl_key_file: ""
    ssl_ca_file: ""
    ssl_mode: "prefer"  # disable, allow, prefer, require, verify-ca, verify-full
    
    # 连接参数
    connect_timeout: 10
    command_timeout: 30
    statement_timeout: 30000
    
    # 表配置
    table_name: "storage_records"
    schema_name: "public"
    
    # 索引配置
    auto_create_indexes: true
    index_type: "btree"  # btree, gin, gist, hash
    
    # 分区配置
    partitioning_enabled: false
    partition_strategy: "range"  # range, list, hash
    partition_column: "created_at"
    partition_interval: "monthly"  # daily, weekly, monthly, yearly
    
    # 压缩配置
    compression_enabled: false
    compression_algorithm: "pglz"  # pglz, lz4
    
    # TTL配置
    ttl_enabled: true
    ttl_cleanup_interval_hours: 1
    default_ttl_days: 30
    
    # 批量操作配置
    batch_size: 1000
    bulk_insert_enabled: true
    bulk_update_enabled: true
    
    # 备份配置
    backup_enabled: true
    backup_interval_hours: 24
    backup_retention_days: 30
    backup_path: "backups/postgresql"
    
    # 监控配置
    metrics_enabled: true
    slow_query_threshold_ms: 1000
    explain_analyze_enabled: false
    
    # 迁移配置
    auto_migrate: true
    migration_table: "alembic_version"
```

### 2. 环境特定配置

```yaml
environments:
  development:
    storage_types:
      postgresql:
        config:
          host: "localhost"
          port: 5432
          database: "storage_dev"
          username: "postgres"
          password: "postgres"
          connection_pool_size: 5
          auto_migrate: true
          partitioning_enabled: false
          ssl_enabled: false
  
  testing:
    storage_types:
      postgresql:
        config:
          host: "localhost"
          port: 5432
          database: "storage_test"
          username: "postgres"
          password: "postgres"
          connection_pool_size: 2
          ttl_enabled: false
          backup_enabled: false
          metrics_enabled: false
  
  production:
    storage_types:
      postgresql:
        config:
          host: "${POSTGRES_HOST}"
          port: "${POSTGRES_PORT:5432}"
          database: "${POSTGRES_DB}"
          username: "${POSTGRES_USER}"
          password: "${POSTGRES_PASSWORD}"
          connection_pool_size: 20
          connection_pool_max_overflow: 40
          ssl_enabled: true
          ssl_mode: "require"
          partitioning_enabled: true
          partition_strategy: "range"
          partition_interval: "monthly"
          compression_enabled: true
          backup_enabled: true
          backup_interval_hours: 6
          metrics_enabled: true
          slow_query_threshold_ms: 500
```

## 实现细节

### 1. 核心方法实现

#### 1.1 保存操作

```python
async def save_impl(self, data: Union[Dict[str, Any], bytes], compressed: bool = False) -> str:
    """PostgreSQL保存实现"""
    try:
        # 生成ID
        item_id = StorageCommonUtils.validate_data_id(data)
        
        # 准备数据
        current_time = datetime.utcnow()
        
        # 构建记录
        record = StorageRecord(
            id=item_id,
            data=data,
            created_at=data.get("created_at", current_time),
            updated_at=current_time,
            expires_at=data.get("expires_at"),
            compressed=compressed,
            type=data.get("type"),
            session_id=data.get("session_id"),
            thread_id=data.get("thread_id"),
            metadata=data.get("metadata", {})
        )
        
        # 使用UPSERT操作
        async with self.get_session() as session:
            await session.execute(
                insert(StorageRecord)
                .values(**record.__dict__)
                .on_conflict_do_update(
                    index_elements=['id'],
                    set_=dict(
                        data=record.data,
                        updated_at=record.updated_at,
                        expires_at=record.expires_at,
                        compressed=record.compressed,
                        type=record.type,
                        session_id=record.session_id,
                        thread_id=record.thread_id,
                        metadata=record.metadata
                    )
                )
            )
            await session.commit()
        
        self._update_stats("save")
        return item_id
        
    except Exception as e:
        raise StorageError(f"Failed to save data to PostgreSQL: {e}")
```

#### 1.2 加载操作

```python
async def load_impl(self, id: str) -> Optional[Dict[str, Any]]:
    """PostgreSQL加载实现"""
    try:
        async with self.get_session() as session:
            # 查询记录
            result = await session.execute(
                select(StorageRecord).where(StorageRecord.id == id)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return None
            
            # 检查是否过期
            if record.expires_at and record.expires_at < datetime.utcnow():
                # 删除过期记录
                await session.execute(
                    delete(StorageRecord).where(StorageRecord.id == id)
                )
                await session.commit()
                return None
            
            # 返回数据
            data = record.data
            data['id'] = record.id
            data['created_at'] = record.created_at
            data['updated_at'] = record.updated_at
            
            if record.expires_at:
                data['expires_at'] = record.expires_at
            
            if record.type:
                data['type'] = record.type
            
            if record.session_id:
                data['session_id'] = record.session_id
            
            if record.thread_id:
                data['thread_id'] = record.thread_id
            
            if record.metadata:
                data['metadata'] = record.metadata
        
        self._update_stats("load")
        return data
        
    except Exception as e:
        raise StorageError(f"Failed to load data {id} from PostgreSQL: {e}")
```

#### 1.3 查询操作

```python
async def list_impl(self, filters: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """PostgreSQL列表实现"""
    try:
        async with self.get_session() as session:
            # 构建查询
            query_builder = PostgreSQLQueryBuilder(session)
            query = query_builder.filter_by_data(filters)
            
            # 添加过期过滤
            query = query.filter(
                or_(
                    StorageRecord.expires_at.is_(None),
                    StorageRecord.expires_at > datetime.utcnow()
                )
            )
            
            # 排序
            query = query.order_by(StorageRecord.created_at.desc())
            
            # 限制数量
            if limit:
                query = query.limit(limit)
            
            # 执行查询
            result = await session.execute(query)
            records = result.scalars().all()
            
            # 转换为字典
            results = []
            for record in records:
                data = record.data
                data['id'] = record.id
                data['created_at'] = record.created_at
                data['updated_at'] = record.updated_at
                
                if record.expires_at:
                    data['expires_at'] = record.expires_at
                
                if record.type:
                    data['type'] = record.type
                
                if record.session_id:
                    data['session_id'] = record.session_id
                
                if record.thread_id:
                    data['thread_id'] = record.thread_id
                
                if record.metadata:
                    data['metadata'] = record.metadata
                
                results.append(data)
        
        self._update_stats("list")
        return results
        
    except Exception as e:
        raise StorageError(f"Failed to list data from PostgreSQL: {e}")
```

### 2. 高级功能

#### 2.1 分区表管理

```python
class PostgreSQLPartitionManager:
    """PostgreSQL分区表管理器"""
    
    def __init__(self, engine, config):
        self.engine = engine
        self.config = config
    
    async def create_partitions(self):
        """创建分区表"""
        if not self.config.get('partitioning_enabled'):
            return
        
        strategy = self.config.get('partition_strategy', 'range')
        column = self.config.get('partition_column', 'created_at')
        interval = self.config.get('partition_interval', 'monthly')
        
        if strategy == 'range':
            await self._create_range_partitions(column, interval)
        elif strategy == 'list':
            await self._create_list_partitions(column)
        elif strategy == 'hash':
            await self._create_hash_partitions(column)
    
    async def _create_range_partitions(self, column: str, interval: str):
        """创建范围分区"""
        # 实现范围分区逻辑
        pass
    
    async def maintain_partitions(self):
        """维护分区表"""
        # 创建新分区
        # 删除旧分区
        pass
```

#### 2.2 索引管理

```python
class PostgreSQLIndexManager:
    """PostgreSQL索引管理器"""
    
    def __init__(self, engine):
        self.engine = engine
    
    async def create_indexes(self):
        """创建索引"""
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_storage_type ON storage_records (type)",
            "CREATE INDEX IF NOT EXISTS idx_storage_session_id ON storage_records (session_id)",
            "CREATE INDEX IF NOT EXISTS idx_storage_thread_id ON storage_records (thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_storage_expires_at ON storage_records (expires_at)",
            "CREATE INDEX IF NOT EXISTS idx_storage_created_at ON storage_records (created_at)",
            "CREATE INDEX IF NOT EXISTS idx_storage_data_gin ON storage_records USING gin (data)",
        ]
        
        async with self.engine.begin() as conn:
            for index_sql in indexes:
                await conn.execute(text(index_sql))
    
    async def analyze_indexes(self):
        """分析索引使用情况"""
        async with self.engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    indexname,
                    idx_scan,
                    idx_tup_read,
                    idx_tup_fetch
                FROM pg_stat_user_indexes
                WHERE tablename = 'storage_records'
                ORDER BY idx_scan DESC
            """))
            return result.fetchall()
```

#### 2.3 健康检查

```python
async def health_check_impl(self) -> Dict[str, Any]:
    """PostgreSQL健康检查实现"""
    try:
        start_time = time.time()
        
        async with self.get_session() as session:
            # 测试连接
            await session.execute(text("SELECT 1"))
            
            # 获取数据库信息
            result = await session.execute(text("""
                SELECT 
                    version(),
                    current_database(),
                    current_user,
                    pg_database_size(current_database()) as db_size,
                    pg_stat_database.datid,
                    pg_stat_database.numbackends,
                    pg_stat_database.xact_commit,
                    pg_stat_database.xact_rollback,
                    pg_stat_database.blks_read,
                    pg_stat_database.blks_hit,
                    pg_stat_database.tup_returned,
                    pg_stat_database.tup_fetched,
                    pg_stat_database.tup_inserted,
                    pg_stat_database.tup_updated,
                    pg_stat_database.tup_deleted
                FROM pg_stat_database
                WHERE datname = current_database()
            """))
            
            db_info = result.fetchone()
            
            # 获取表统计信息
            result = await session.execute(text("""
                SELECT 
                    schemaname,
                    tablename,
                    n_tup_ins,
                    n_tup_upd,
                    n_tup_del,
                    n_live_tup,
                    n_dead_tup
                FROM pg_stat_user_tables
                WHERE tablename = 'storage_records'
            """))
            
            table_stats = result.fetchone()
            
            # 计算响应时间
            response_time = (time.time() - start_time) * 1000
        
        return {
            "status": "healthy",
            "response_time_ms": response_time,
            "database_info": {
                "version": db_info.version,
                "database": db_info.current_database,
                "user": db_info.current_user,
                "size_bytes": db_info.db_size,
                "connections": db_info.numbackends,
                "transactions_committed": db_info.xact_commit,
                "transactions_rolled_back": db_info.xact_rollback,
            },
            "table_stats": {
                "records_inserted": table_stats.n_tup_ins,
                "records_updated": table_stats.n_tup_upd,
                "records_deleted": table_stats.n_tup_del,
                "live_records": table_stats.n_live_tup,
                "dead_records": table_stats.n_dead_tup,
            },
            "config": {
                "host": self.host,
                "port": self.port,
                "database": self.database,
                "connection_pool_size": self.connection_pool_size,
                "partitioning_enabled": self.partitioning_enabled,
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "response_time_ms": 0,
        }
```

## 性能优化

### 1. 查询优化

- 使用适当的索引
- 优化查询计划
- 使用预编译语句
- 批量操作优化

### 2. 连接池优化

- 合理设置连接池大小
- 连接复用
- 连接健康检查
- 超时设置

### 3. 表结构优化

- 分区表设计
- 索引策略
- 数据类型选择
- 压缩配置

### 4. 内存优化

- 工作内存配置
- 共享缓冲区配置
- 有效缓存大小
- 维护工作内存

## 依赖管理

### 1. 必需依赖

```toml
[project.optional-dependencies]
postgresql = [
    "asyncpg>=0.28.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.10.0",
]
```

### 2. 可选依赖

```toml
[project.optional-dependencies]
postgresql-optimizations = [
    "asyncpg>=0.28.0",
    "sqlalchemy[asyncio]>=2.0.0",
    "alembic>=1.10.0",
    "psycopg2-binary>=2.9.0",  # 用于同步操作
    "pgspecial>=2.0.0",       # 用于特殊命令
]
```

## 测试策略

### 1. 单元测试

- 测试基本CRUD操作
- 测试事务处理
- 测试错误处理
- 测试数据类型转换

### 2. 集成测试

- 测试连接池
- 测试分区表
- 测试索引性能
- 测试并发操作

### 3. 性能测试

- 基准测试
- 并发测试
- 大数据量测试
- 查询性能测试

## 部署考虑

### 1. 单机部署

- 适用于开发和小规模环境
- 简单配置，易于管理

### 2. 主从部署

- 适用于读密集型应用
- 主从复制配置
- 读写分离

### 3. 集群部署

- 适用于大规模应用
- 使用PostgreSQL集群方案
- 负载均衡配置

## 监控和运维

### 1. 性能监控

- 查询性能监控
- 连接数监控
- 锁等待监控
- 缓存命中率监控

### 2. 日志记录

- 慢查询日志
- 错误日志
- 连接日志
- 事务日志

### 3. 告警机制

- 连接失败告警
- 查询超时告警
- 磁盘空间告警
- 锁等待告警

## 安全考虑

### 1. 认证授权

- 数据库用户权限
- 行级安全策略
- 列级权限控制

### 2. 数据加密

- 传输加密(SSL/TLS)
- 静态数据加密
- 密钥管理

### 3. 审计日志

- 操作审计
- 数据访问审计
- 修改记录审计

## 迁移策略

### 1. 数据迁移

- 从SQLite迁移
- 数据格式转换
- 增量同步机制

### 2. 模式迁移

- 使用Alembic管理
- 自动迁移生成
- 回滚机制

### 3. 配置迁移

- 配置文件转换
- 环境变量映射
- 验证配置正确性

## 总结

PostgreSQL存储后端设计提供了：

1. **企业级特性**: ACID事务、MVCC、并发控制
2. **高性能**: 查询优化器、索引策略、连接池
3. **高扩展性**: 分区表、复制、分片支持
4. **丰富功能**: JSON支持、全文搜索、地理信息
5. **易集成**: 完全兼容现有接口，平滑升级

该设计为系统提供了强大的企业级存储能力，特别适合需要强一致性、高性能和丰富功能的生产环境。