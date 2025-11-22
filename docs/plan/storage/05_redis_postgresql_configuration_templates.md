# Redis和PostgreSQL配置模板

## 概述

本文档提供Redis和PostgreSQL存储后端的完整配置模板，包括不同环境和使用场景的配置示例。

## Redis配置模板

### 1. 基础Redis配置模板

#### 1.1 开发环境配置

```yaml
# Redis开发环境配置
redis_development:
  # 存储类型定义
  storage_type:
    name: "redis"
    class: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis开发环境存储"
    category: "nosql"
    features:
      - "distributed"
      - "persistent"
      - "high_performance"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "medium"
  
  # 连接配置
  connection:
    host: "${REDIS_HOST:localhost}"
    port: "${REDIS_PORT:6379}"
    db: "${REDIS_DB:0}"
    password: "${REDIS_PASSWORD:}"
    timeout: 30
    connect_timeout: 10
    retry_on_timeout: true
    retry_count: 3
    retry_delay: 1.0
  
  # 连接池配置
  pool:
    pool_size: 5
    max_connections: 10
    socket_timeout: 30
    socket_connect_timeout: 30
    health_check_interval: 30
    max_idle_time: 300
  
  # 序列化配置
  serialization:
    format: "json"  # json, pickle, msgpack
    compression_enabled: false
    compression_algorithm: "gzip"
  
  # TTL配置
  ttl:
    enabled: true
    strategy: "sliding"  # absolute, sliding, none
    default_ttl_seconds: 1800
    cleanup_interval_seconds: 300
  
  # 性能配置
  performance:
    batch_size: 100
    pipeline_enabled: true
    pipeline_max_size: 500
    max_memory_policy: "allkeys-lru"
  
  # 监控配置
  monitoring:
    metrics_enabled: true
    slow_log_enabled: true
    slow_log_threshold_ms: 100
    health_check_enabled: true
    health_check_interval_seconds: 60
  
  # 持久化配置
  persistence:
    enabled: false
    save_interval_seconds: 300
    backup_enabled: false
    backup_path: "backups/redis/dev"
  
  # 安全配置
  security:
    ssl_enabled: false
    cert_file: ""
    key_file: ""
    ca_file: ""
```

#### 1.2 测试环境配置

```yaml
# Redis测试环境配置
redis_testing:
  storage_type:
    name: "redis"
    class: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis测试环境存储"
    category: "nosql"
    features:
      - "distributed"
      - "volatile"
      - "high_performance"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "low"
  
  connection:
    host: "${REDIS_TEST_HOST:localhost}"
    port: "${REDIS_TEST_PORT:6379}"
    db: "${REDIS_TEST_DB:1}"
    password: "${REDIS_TEST_PASSWORD:}"
    timeout: 10
    connect_timeout: 5
    retry_on_timeout: false
    retry_count: 1
    retry_delay: 0.5
  
  pool:
    pool_size: 2
    max_connections: 5
    socket_timeout: 10
    socket_connect_timeout: 10
    health_check_interval: 60
    max_idle_time: 60
  
  serialization:
    format: "json"
    compression_enabled: false
    compression_algorithm: "gzip"
  
  ttl:
    enabled: true
    strategy: "absolute"
    default_ttl_seconds: 300
    cleanup_interval_seconds: 60
  
  performance:
    batch_size: 50
    pipeline_enabled: true
    pipeline_max_size: 100
    max_memory_policy: "allkeys-lru"
  
  monitoring:
    metrics_enabled: false
    slow_log_enabled: false
    health_check_enabled: true
    health_check_interval_seconds: 120
  
  persistence:
    enabled: false
    backup_enabled: false
  
  security:
    ssl_enabled: false
```

#### 1.3 生产环境配置

```yaml
# Redis生产环境配置
redis_production:
  storage_type:
    name: "redis"
    class: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis生产环境存储"
    category: "nosql"
    features:
      - "distributed"
      - "persistent"
      - "clustered"
      - "high_performance"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "high"
  
  # 集群配置
  cluster:
    enabled: true
    nodes:
      - host: "${REDIS_NODE_1_HOST}"
        port: "${REDIS_NODE_1_PORT:6379}"
        password: "${REDIS_NODE_1_PASSWORD:}"
      - host: "${REDIS_NODE_2_HOST}"
        port: "${REDIS_NODE_2_PORT:6379}"
        password: "${REDIS_NODE_2_PASSWORD:}"
      - host: "${REDIS_NODE_3_HOST}"
        port: "${REDIS_NODE_3_PORT:6379}"
        password: "${REDIS_NODE_3_PASSWORD:}"
      - host: "${REDIS_NODE_4_HOST}"
        port: "${REDIS_NODE_4_PORT:6379}"
        password: "${REDIS_NODE_4_PASSWORD:}"
      - host: "${REDIS_NODE_5_HOST}"
        port: "${REDIS_NODE_5_PORT:6379}"
        password: "${REDIS_NODE_5_PASSWORD:}"
      - host: "${REDIS_NODE_6_HOST}"
        port: "${REDIS_NODE_6_PORT:6379}"
        password: "${REDIS_NODE_6_PASSWORD:}"
    skip_full_coverage_check: true
    max_connections_per_node: 10
  
  # 哨兵配置（备选）
  sentinel:
    enabled: false
    hosts:
      - host: "${REDIS_SENTINEL_1_HOST}"
        port: "${REDIS_SENTINEL_1_PORT:26379}"
      - host: "${REDIS_SENTINEL_2_HOST}"
        port: "${REDIS_SENTINEL_2_PORT:26379}"
      - host: "${REDIS_SENTINEL_3_HOST}"
        port: "${REDIS_SENTINEL_3_PORT:26379}"
    service_name: "${REDIS_SENTINEL_SERVICE_NAME:mymaster}"
    password: "${REDIS_SENTINEL_PASSWORD:}"
  
  connection:
    host: "${REDIS_HOST}"
    port: "${REDIS_PORT:6379}"
    db: "${REDIS_DB:0}"
    password: "${REDIS_PASSWORD}"
    timeout: 30
    connect_timeout: 10
    retry_on_timeout: true
    retry_count: 3
    retry_delay: 1.0
  
  pool:
    pool_size: 20
    max_connections: 50
    socket_timeout: 30
    socket_connect_timeout: 30
    health_check_interval: 30
    max_idle_time: 300
  
  serialization:
    format: "msgpack"  # 更高性能的二进制格式
    compression_enabled: true
    compression_algorithm: "lz4"  # 快速压缩算法
  
  ttl:
    enabled: true
    strategy: "absolute"
    default_ttl_seconds: 3600
    cleanup_interval_seconds: 300
  
  performance:
    batch_size: 1000
    pipeline_enabled: true
    pipeline_max_size: 2000
    max_memory_policy: "allkeys-lru"
    tcp_keepalive: true
    tcp_keepalive_idle: 300
  
  monitoring:
    metrics_enabled: true
    slow_log_enabled: true
    slow_log_threshold_ms: 50
    health_check_enabled: true
    health_check_interval_seconds: 30
    command_stats_enabled: true
  
  persistence:
    enabled: true
    save_interval_seconds: 600
    backup_enabled: true
    backup_interval_hours: 6
    backup_path: "${REDIS_BACKUP_PATH:/var/backups/redis}"
    backup_retention_days: 30
    compression_enabled: true
  
  security:
    ssl_enabled: true
    ssl_mode: "require"
    cert_file: "${REDIS_SSL_CERT_FILE}"
    key_file: "${REDIS_SSL_KEY_FILE}"
    ca_file: "${REDIS_SSL_CA_FILE}"
    ssl_cert_reqs: "required"
  
  # 高可用配置
  high_availability:
    enabled: true
    failover_timeout: 60
    read_from_replicas: true
    replica_read_timeout: 10
```

### 2. Redis专用配置模板

#### 2.1 缓存专用配置

```yaml
# Redis缓存专用配置
redis_cache:
  storage_type:
    name: "redis"
    class: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis缓存存储"
    category: "nosql"
    features:
      - "cache"
      - "volatile"
      - "high_performance"
  
  connection:
    host: "${REDIS_CACHE_HOST:localhost}"
    port: "${REDIS_CACHE_PORT:6379}"
    db: "${REDIS_CACHE_DB:2}"
    password: "${REDIS_CACHE_PASSWORD:}"
    timeout: 5
    connect_timeout: 3
  
  pool:
    pool_size: 10
    max_connections: 20
    socket_timeout: 5
    socket_connect_timeout: 5
  
  serialization:
    format: "msgpack"
    compression_enabled: true
    compression_algorithm: "lz4"
  
  ttl:
    enabled: true
    strategy: "absolute"
    default_ttl_seconds: 300  # 5分钟缓存
    cleanup_interval_seconds: 60
  
  performance:
    batch_size: 100
    pipeline_enabled: true
    pipeline_max_size: 500
    max_memory_policy: "allkeys-lru"
  
  cache_specific:
    eviction_policy: "allkeys-lru"
    max_memory_mb: "${REDIS_CACHE_MAX_MEMORY:1024}"
    sample_size: 5
    lazy_expire: true
  
  monitoring:
    metrics_enabled: true
    cache_hit_ratio_enabled: true
    slow_log_threshold_ms: 10
```

#### 2.2 会话存储配置

```yaml
# Redis会话存储配置
redis_session:
  storage_type:
    name: "redis"
    class: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis会话存储"
    category: "nosql"
    features:
      - "session"
      - "persistent"
      - "distributed"
  
  connection:
    host: "${REDIS_SESSION_HOST:localhost}"
    port: "${REDIS_SESSION_PORT:6379}"
    db: "${REDIS_SESSION_DB:3}"
    password: "${REDIS_SESSION_PASSWORD:}"
    timeout: 10
    connect_timeout: 5
  
  pool:
    pool_size: 15
    max_connections: 30
    socket_timeout: 10
    socket_connect_timeout: 10
  
  serialization:
    format: "json"
    compression_enabled: false
  
  ttl:
    enabled: true
    strategy: "sliding"  # 会话使用滑动过期
    default_ttl_seconds: 1800  # 30分钟会话
    cleanup_interval_seconds: 300
  
  session_specific:
    key_prefix: "session:"
    session_timeout: 1800
    heartbeat_interval: 300
    max_sessions: 10000
  
  monitoring:
    metrics_enabled: true
    session_stats_enabled: true
    active_sessions_tracking: true
```

## PostgreSQL配置模板

### 1. 基础PostgreSQL配置模板

#### 1.1 开发环境配置

```yaml
# PostgreSQL开发环境配置
postgresql_development:
  storage_type:
    name: "postgresql"
    class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL开发环境存储"
    category: "database"
    features:
      - "acid"
      - "transactional"
      - "indexed"
    performance:
      read_speed: "medium"
      write_speed: "medium"
      scalability: "low"
  
  # 连接配置
  connection:
    host: "${POSTGRES_HOST:localhost}"
    port: "${POSTGRES_PORT:5432}"
    database: "${POSTGRES_DB:storage_dev}"
    timeout: 30
    connect_timeout: 10
    command_timeout: 30
    statement_timeout: 30000
  
  # 认证配置
  authentication:
    username: "${POSTGRES_USER:postgres}"
    password: "${POSTGRES_PASSWORD:postgres}"
  
  # SSL配置
  ssl:
    enabled: false
    ssl_mode: "prefer"
    cert_file: ""
    key_file: ""
    ca_file: ""
  
  # 连接池配置
  pool:
    pool_size: 5
    max_overflow: 10
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
  
  # 数据库配置
  database:
    schema_name: "public"
    table_name: "storage_records"
    auto_create_tables: true
    auto_migrate: true
  
  # 索引配置
  indexes:
    auto_create: true
    index_type: "btree"
    analyze_after_create: true
  
  # 分区配置
  partitioning:
    enabled: false
    strategy: "none"
  
  # 压缩配置
  compression:
    enabled: false
    algorithm: "pglz"
  
  # TTL配置
  ttl:
    enabled: true
    cleanup_interval_hours: 1
    default_ttl_days: 7
  
  # 批量操作配置
  batch_operations:
    batch_size: 100
    bulk_insert_enabled: true
    bulk_update_enabled: true
    bulk_delete_enabled: true
  
  # 监控配置
  monitoring:
    metrics_enabled: true
    slow_query_enabled: true
    slow_query_threshold_ms: 1000
    health_check_enabled: true
    health_check_interval_seconds: 60
  
  # 备份配置
  backup:
    enabled: false
    backup_interval_hours: 24
    backup_path: "backups/postgresql/dev"
    backup_retention_days: 7
  
  # 迁移配置
  migration:
    auto_migrate: true
    migration_table: "alembic_version"
    migration_path: "migrations"
```

#### 1.2 测试环境配置

```yaml
# PostgreSQL测试环境配置
postgresql_testing:
  storage_type:
    name: "postgresql"
    class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL测试环境存储"
    category: "database"
    features:
      - "acid"
      - "transactional"
      - "indexed"
    performance:
      read_speed: "medium"
      write_speed: "medium"
      scalability: "low"
  
  connection:
    host: "${POSTGRES_TEST_HOST:localhost}"
    port: "${POSTGRES_TEST_PORT:5432}"
    database: "${POSTGRES_TEST_DB:storage_test}"
    timeout: 10
    connect_timeout: 5
    command_timeout: 10
    statement_timeout: 10000
  
  authentication:
    username: "${POSTGRES_TEST_USER:postgres}"
    password: "${POSTGRES_TEST_PASSWORD:postgres}"
  
  ssl:
    enabled: false
    ssl_mode: "disable"
  
  pool:
    pool_size: 2
    max_overflow: 5
    pool_timeout: 10
    pool_recycle: 1800
    pool_pre_ping: true
  
  database:
    schema_name: "public"
    table_name: "storage_records"
    auto_create_tables: true
    auto_migrate: true
  
  indexes:
    auto_create: true
    index_type: "btree"
    analyze_after_create: false
  
  partitioning:
    enabled: false
  
  compression:
    enabled: false
  
  ttl:
    enabled: false  # 测试环境禁用TTL
  
  batch_operations:
    batch_size: 50
    bulk_insert_enabled: true
    bulk_update_enabled: true
    bulk_delete_enabled: true
  
  monitoring:
    metrics_enabled: false
    slow_query_enabled: false
    health_check_enabled: true
    health_check_interval_seconds: 120
  
  backup:
    enabled: false
  
  migration:
    auto_migrate: true
    migration_table: "alembic_version_test"
```

#### 1.3 生产环境配置

```yaml
# PostgreSQL生产环境配置
postgresql_production:
  storage_type:
    name: "postgresql"
    class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL生产环境存储"
    category: "database"
    features:
      - "acid"
      - "transactional"
      - "indexed"
      - "partitioning"
      - "replication"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "high"
  
  # 主库连接配置
  connection:
    host: "${POSTGRES_PRIMARY_HOST}"
    port: "${POSTGRES_PRIMARY_PORT:5432}"
    database: "${POSTGRES_DB}"
    timeout: 30
    connect_timeout: 10
    command_timeout: 30
    statement_timeout: 60000
  
  authentication:
    username: "${POSTGRES_USER}"
    password: "${POSTGRES_PASSWORD}"
  
  # SSL配置
  ssl:
    enabled: true
    ssl_mode: "require"
    cert_file: "${POSTGRES_SSL_CERT_FILE}"
    key_file: "${POSTGRES_SSL_KEY_FILE}"
    ca_file: "${POSTGRES_SSL_CA_FILE}"
    ssl_cert_reqs: "verify-full"
  
  # 连接池配置
  pool:
    pool_size: 20
    max_overflow: 40
    pool_timeout: 30
    pool_recycle: 3600
    pool_pre_ping: true
    pool_reset_on_return: "commit"
  
  # 数据库配置
  database:
    schema_name: "storage"
    table_name: "storage_records"
    auto_create_tables: true
    auto_migrate: true
    vacuum_enabled: true
    vacuum_interval_hours: 24
    analyze_enabled: true
    analyze_interval_hours: 6
  
  # 索引配置
  indexes:
    auto_create: true
    index_type: "btree"
    analyze_after_create: true
    concurrent_index_creation: true
    index_maintenance_enabled: true
    index_maintenance_interval_hours: 24
  
  # 分区配置
  partitioning:
    enabled: true
    strategy: "range"  # range, list, hash
    partition_column: "created_at"
    partition_interval: "monthly"  # daily, weekly, monthly, yearly
    partition_retention_months: 12
    auto_create_partitions: true
    partition_maintenance_enabled: true
    partition_maintenance_interval_hours: 6
  
  # 压缩配置
  compression:
    enabled: true
    algorithm: "lz4"  # pglz, lz4
    compression_level: 9
  
  # TTL配置
  ttl:
    enabled: true
    cleanup_interval_hours: 1
    default_ttl_days: 90
    cleanup_batch_size: 1000
    vacuum_after_cleanup: true
  
  # 批量操作配置
  batch_operations:
    batch_size: 1000
    bulk_insert_enabled: true
    bulk_update_enabled: true
    bulk_delete_enabled: true
    bulk_insert_batch_size: 5000
    bulk_update_batch_size: 2000
    bulk_delete_batch_size: 5000
  
  # 监控配置
  monitoring:
    metrics_enabled: true
    slow_query_enabled: true
    slow_query_threshold_ms: 500
    health_check_enabled: true
    health_check_interval_seconds: 30
    explain_analyze_enabled: true
    query_plan_cache_enabled: true
    lock_monitoring_enabled: true
    deadlock_detection_enabled: true
  
  # 备份配置
  backup:
    enabled: true
    backup_type: "full"  # full, incremental, differential
    backup_interval_hours: 6
    backup_path: "${POSTGRES_BACKUP_PATH:/var/backups/postgresql}"
    backup_retention_days: 30
    backup_compression: true
    backup_parallel_jobs: 4
    point_in_time_recovery: true
    wal_archiving: true
    wal_archive_path: "${POSTGRES_WAL_ARCHIVE_PATH:/var/lib/postgresql/wal_archive}"
  
  # 迁移配置
  migration:
    auto_migrate: true
    migration_table: "alembic_version"
    migration_path: "migrations"
    migration_timeout_seconds: 300
    rollback_enabled: true
    migration_backup_enabled: true
  
  # 复制配置
  replication:
    enabled: true
    replica_hosts:
      - host: "${POSTGRES_REPLICA_1_HOST}"
        port: "${POSTGRES_REPLICA_1_PORT:5432}"
        username: "${POSTGRES_REPLICA_USER}"
        password: "${POSTGRES_REPLICA_PASSWORD}"
      - host: "${POSTGRES_REPLICA_2_HOST}"
        port: "${POSTGRES_REPLICA_2_PORT:5432}"
        username: "${POSTGRES_REPLICA_USER}"
        password: "${POSTGRES_REPLICA_PASSWORD}"
    read_from_replicas: true
    replica_read_timeout: 10
    replica_health_check_enabled: true
    replica_health_check_interval_seconds: 30
  
  # 性能调优配置
  performance_tuning:
    work_mem: "64MB"
    maintenance_work_mem: "256MB"
    effective_cache_size: "4GB"
    shared_buffers: "1GB"
    random_page_cost: 1.1
    effective_io_concurrency: 200
    max_parallel_workers_per_gather: 4
    max_parallel_workers: 8
    checkpoint_completion_target: 0.9
    wal_buffers: "64MB"
    default_statistics_target: 100
  
  # 安全配置
  security:
    row_level_security: true
    audit_enabled: true
    audit_log_path: "${POSTGRES_AUDIT_LOG_PATH:/var/log/postgresql/audit.log}"
    connection_logging: true
    password_encryption: "scram-sha-256"
    ssl_renegotiation_limit: 0
```

### 2. PostgreSQL专用配置模板

#### 2.1 分析型数据库配置

```yaml
# PostgreSQL分析型数据库配置
postgresql_analytics:
  storage_type:
    name: "postgresql"
    class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL分析型数据库"
    category: "database"
    features:
      - "analytics"
      - "columnar"
      - "partitioning"
    performance:
      read_speed: "high"
      write_speed: "medium"
      scalability: "high"
  
  connection:
    host: "${POSTGRES_ANALYTICS_HOST}"
    port: "${POSTGRES_ANALYTICS_PORT:5432}"
    database: "${POSTGRES_ANALYTICS_DB:analytics}"
    timeout: 60
    connect_timeout: 15
    command_timeout: 300
    statement_timeout: 300000
  
  authentication:
    username: "${POSTGRES_ANALYTICS_USER}"
    password: "${POSTGRES_ANALYTICS_PASSWORD}"
  
  ssl:
    enabled: true
    ssl_mode: "require"
  
  pool:
    pool_size: 10
    max_overflow: 20
    pool_timeout: 60
    pool_recycle: 7200
  
  database:
    schema_name: "analytics"
    table_name: "analytics_records"
    auto_create_tables: true
    auto_migrate: true
  
  # 分析型特定配置
  analytics:
    # 列存扩展
    columnar_enabled: true
    columnar_compression: "zstd"
    columnar_stripe_size: 10000
    
    # 分区策略
    partitioning:
      enabled: true
      strategy: "range"
      partition_column: "event_timestamp"
      partition_interval: "daily"
      partition_retention_days: 365
    
    # 聚合表
    materialized_views:
      enabled: true
      refresh_interval_minutes: 60
      auto_create: true
    
    # 统计信息
    statistics:
      auto_analyze: true
      analyze_interval_hours: 2
      statistics_target: 1000
      extended_statistics: true
  
  performance_tuning:
    work_mem: "256MB"
    maintenance_work_mem: "1GB"
    effective_cache_size: "8GB"
    shared_buffers: "2GB"
    random_page_cost: 1.0
    effective_io_concurrency: 400
    max_parallel_workers_per_gather: 8
    max_parallel_workers: 16
    enable_bitmapscan: true
    enable_hashagg: true
    enable_hashjoin: true
    enable_indexscan: true
    enable_indexonlyscan: true
    enable_material: true
    enable_mergejoin: true
    enable_nestloop: true
    enable_seqscan: true
    enable_sort: true
    enable_tidscan: true
  
  monitoring:
    query_performance_enabled: true
    explain_analyze_enabled: true
    pg_stat_statements_enabled: true
    pg_stat_statements_max: 10000
    pg_stat_statements_track: "all"
```

#### 2.2 时序数据库配置

```yaml
# PostgreSQL时序数据库配置
postgresql_timeseries:
  storage_type:
    name: "postgresql"
    class: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL时序数据库"
    category: "database"
    features:
      - "timeseries"
      - "partitioning"
      - "compression"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "high"
  
  connection:
    host: "${POSTGRES_TIMESERIES_HOST}"
    port: "${POSTGRES_TIMESERIES_PORT:5432}"
    database: "${POSTGRES_TIMESERIES_DB:timeseries}"
    timeout: 30
    connect_timeout: 10
    command_timeout: 60
    statement_timeout: 60000
  
  authentication:
    username: "${POSTGRES_TIMESERIES_USER}"
    password: "${POSTGRES_TIMESERIES_PASSWORD}"
  
  ssl:
    enabled: true
    ssl_mode: "require"
  
  pool:
    pool_size: 15
    max_overflow: 30
    pool_timeout: 30
    pool_recycle: 3600
  
  database:
    schema_name: "timeseries"
    table_name: "timeseries_records"
    auto_create_tables: true
    auto_migrate: true
  
  # 时序特定配置
  timeseries:
    # TimescaleDB扩展
    timescaledb_enabled: true
    timescaledb_version: "latest"
    
    # 分区策略
    partitioning:
      enabled: true
      strategy: "time"
      partition_column: "timestamp"
      partition_interval: "1 day"
      partition_retention_days: 90
      auto_create_partitions: true
    
    # 压缩策略
    compression:
      enabled: true
      compression_algorithm: "bytedict"
      compression_interval_hours: 24
      compress_after_days: 7
    
    # 连续聚合
    continuous_aggregates:
      enabled: true
      auto_create: true
      refresh_interval_minutes: 15
    
    # 数据保留策略
    retention_policy:
      enabled: true
      default_retention_days: 90
      raw_data_retention_days: 7
      aggregated_data_retention_days: 365
  
  performance_tuning:
    work_mem: "128MB"
    maintenance_work_mem: "512MB"
    effective_cache_size: "4GB"
    shared_buffers: "1GB"
    random_page_cost: 1.1
    effective_io_concurrency: 200
    max_parallel_workers_per_gather: 4
    timescaledb.max_background_workers: 8
    timescaledb.compress_segmentby: "device_id"
    timescaledb.compress_orderby: "timestamp"
  
  monitoring:
    timeseries_metrics_enabled: true
    compression_stats_enabled: true
    retention_stats_enabled: true
    continuous_aggregate_stats_enabled: true
```

## 环境变量配置模板

### 1. Redis环境变量

```bash
# Redis环境变量配置模板

# 基础连接配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# 开发环境
REDIS_DEV_HOST=localhost
REDIS_DEV_PORT=6379
REDIS_DEV_DB=0
REDIS_DEV_PASSWORD=

# 测试环境
REDIS_TEST_HOST=localhost
REDIS_TEST_PORT=6379
REDIS_TEST_DB=1
REDIS_TEST_PASSWORD=

# 生产环境
REDIS_PROD_HOST=redis-cluster.example.com
REDIS_PROD_PORT=6379
REDIS_PROD_DB=0
REDIS_PROD_PASSWORD=your-redis-password

# 集群配置
REDIS_NODE_1_HOST=redis-node-1.example.com
REDIS_NODE_1_PORT=6379
REDIS_NODE_1_PASSWORD=node1-password

REDIS_NODE_2_HOST=redis-node-2.example.com
REDIS_NODE_2_PORT=6379
REDIS_NODE_2_PASSWORD=node2-password

REDIS_NODE_3_HOST=redis-node-3.example.com
REDIS_NODE_3_PORT=6379
REDIS_NODE_3_PASSWORD=node3-password

# 哨兵配置
REDIS_SENTINEL_1_HOST=sentinel-1.example.com
REDIS_SENTINEL_1_PORT=26379
REDIS_SENTINEL_PASSWORD=sentinel-password

REDIS_SENTINEL_SERVICE_NAME=mymaster

# SSL配置
REDIS_SSL_CERT_FILE=/path/to/redis.crt
REDIS_SSL_KEY_FILE=/path/to/redis.key
REDIS_SSL_CA_FILE=/path/to/ca.crt

# 备份配置
REDIS_BACKUP_PATH=/var/backups/redis

# 缓存配置
REDIS_CACHE_HOST=redis-cache.example.com
REDIS_CACHE_PORT=6379
REDIS_CACHE_DB=2
REDIS_CACHE_PASSWORD=cache-password
REDIS_CACHE_MAX_MEMORY=1024

# 会话配置
REDIS_SESSION_HOST=redis-session.example.com
REDIS_SESSION_PORT=6379
REDIS_SESSION_DB=3
REDIS_SESSION_PASSWORD=session-password
```

### 2. PostgreSQL环境变量

```bash
# PostgreSQL环境变量配置模板

# 基础连接配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=storage
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# 开发环境
POSTGRES_DEV_HOST=localhost
POSTGRES_DEV_PORT=5432
POSTGRES_DEV_DB=storage_dev
POSTGRES_DEV_USER=postgres
POSTGRES_DEV_PASSWORD=postgres

# 测试环境
POSTGRES_TEST_HOST=localhost
POSTGRES_TEST_PORT=5432
POSTGRES_TEST_DB=storage_test
POSTGRES_TEST_USER=postgres
POSTGRES_TEST_PASSWORD=postgres

# 生产环境
POSTGRES_PRIMARY_HOST=postgres-primary.example.com
POSTGRES_PRIMARY_PORT=5432
POSTGRES_DB=storage_prod
POSTGRES_USER=storage_user
POSTGRES_PASSWORD=your-secure-password

# 复制配置
POSTGRES_REPLICA_1_HOST=postgres-replica-1.example.com
POSTGRES_REPLICA_1_PORT=5432
POSTGRES_REPLICA_USER=replica_user
POSTGRES_REPLICA_PASSWORD=replica-password

POSTGRES_REPLICA_2_HOST=postgres-replica-2.example.com
POSTGRES_REPLICA_2_PORT=5432

# SSL配置
POSTGRES_SSL_CERT_FILE=/path/to/postgresql.crt
POSTGRES_SSL_KEY_FILE=/path/to/postgresql.key
POSTGRES_SSL_CA_FILE=/path/to/ca.crt

# 备份配置
POSTGRES_BACKUP_PATH=/var/backups/postgresql
POSTGRES_WAL_ARCHIVE_PATH=/var/lib/postgresql/wal_archive

# 分析型数据库
POSTGRES_ANALYTICS_HOST=postgres-analytics.example.com
POSTGRES_ANALYTICS_PORT=5432
POSTGRES_ANALYTICS_DB=analytics
POSTGRES_ANALYTICS_USER=analytics_user
POSTGRES_ANALYTICS_PASSWORD=analytics-password

# 时序数据库
POSTGRES_TIMESERIES_HOST=postgres-timeseries.example.com
POSTGRES_TIMESERIES_PORT=5432
POSTGRES_TIMESERIES_DB=timeseries
POSTGRES_TIMESERIES_USER=timeseries_user
POSTGRES_TIMESERIES_PASSWORD=timeseries-password

# 审计配置
POSTGRES_AUDIT_LOG_PATH=/var/log/postgresql/audit.log
```

## 配置验证脚本

### 1. Redis配置验证

```python
#!/usr/bin/env python3
"""
Redis配置验证脚本
"""

import asyncio
import yaml
import redis.asyncio as redis
from typing import Dict, Any, List

class RedisConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def validate(self) -> List[str]:
        """验证Redis配置"""
        errors = []
        
        # 验证基础配置
        errors.extend(self._validate_basic_config())
        
        # 验证连接配置
        errors.extend(await self._validate_connection())
        
        # 验证集群配置
        errors.extend(await self._validate_cluster())
        
        # 验证性能配置
        errors.extend(self._validate_performance())
        
        return errors
    
    def _validate_basic_config(self) -> List[str]:
        """验证基础配置"""
        errors = []
        
        connection = self.config.get("connection", {})
        if not connection.get("host"):
            errors.append("Redis connection host is required")
        
        port = connection.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("Redis connection port must be a valid port number")
        
        return errors
    
    async def _validate_connection(self) -> List[str]:
        """验证连接配置"""
        errors = []
        
        try:
            connection = self.config.get("connection", {})
            pool = self.config.get("pool", {})
            
            # 创建连接池
            redis_client = redis.ConnectionPool(
                host=connection.get("host", "localhost"),
                port=connection.get("port", 6379),
                db=connection.get("db", 0),
                password=connection.get("password"),
                max_connections=pool.get("max_connections", 10),
                socket_timeout=connection.get("timeout", 30),
                socket_connect_timeout=connection.get("connect_timeout", 10)
            )
            
            # 测试连接
            client = redis.Redis(connection_pool=redis_client)
            await client.ping()
            await client.close()
            
        except Exception as e:
            errors.append(f"Redis connection test failed: {e}")
        
        return errors
    
    async def _validate_cluster(self) -> List[str]:
        """验证集群配置"""
        errors = []
        
        cluster_config = self.config.get("cluster", {})
        if cluster_config.get("enabled"):
            nodes = cluster_config.get("nodes", [])
            if len(nodes) < 3:
                errors.append("Redis cluster requires at least 3 nodes")
            
            # 验证每个节点连接
            for node in nodes:
                try:
                    client = redis.Redis(
                        host=node.get("host"),
                        port=node.get("port", 6379),
                        password=node.get("password"),
                        socket_timeout=5
                    )
                    await client.ping()
                    await client.close()
                except Exception as e:
                    errors.append(f"Cluster node {node.get('host')}:{node.get('port')} connection failed: {e}")
        
        return errors
    
    def _validate_performance(self) -> List[str]:
        """验证性能配置"""
        errors = []
        
        performance = self.config.get("performance", {})
        batch_size = performance.get("batch_size", 100)
        if not isinstance(batch_size, int) or batch_size < 1:
            errors.append("Batch size must be a positive integer")
        
        pipeline_max_size = performance.get("pipeline_max_size", 500)
        if not isinstance(pipeline_max_size, int) or pipeline_max_size < 1:
            errors.append("Pipeline max size must be a positive integer")
        
        return errors

# 使用示例
async def validate_redis_config(config_path: str):
    """验证Redis配置"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    validator = RedisConfigValidator(config)
    errors = await validator.validate()
    
    if errors:
        print("Redis configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("Redis configuration is valid")
        return True

if __name__ == "__main__":
    asyncio.run(validate_redis_config("redis_config.yaml"))
```

### 2. PostgreSQL配置验证

```python
#!/usr/bin/env python3
"""
PostgreSQL配置验证脚本
"""

import asyncio
import yaml
import asyncpg
from typing import Dict, Any, List

class PostgreSQLConfigValidator:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    async def validate(self) -> List[str]:
        """验证PostgreSQL配置"""
        errors = []
        
        # 验证基础配置
        errors.extend(self._validate_basic_config())
        
        # 验证连接配置
        errors.extend(await self._validate_connection())
        
        # 验证数据库配置
        errors.extend(await self._validate_database())
        
        # 验证性能配置
        errors.extend(self._validate_performance())
        
        return errors
    
    def _validate_basic_config(self) -> List[str]:
        """验证基础配置"""
        errors = []
        
        connection = self.config.get("connection", {})
        if not connection.get("host"):
            errors.append("PostgreSQL connection host is required")
        
        port = connection.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("PostgreSQL connection port must be a valid port number")
        
        authentication = self.config.get("authentication", {})
        if not authentication.get("username"):
            errors.append("PostgreSQL username is required")
        
        if not self.config.get("database", {}).get("database"):
            errors.append("PostgreSQL database name is required")
        
        return errors
    
    async def _validate_connection(self) -> List[str]:
        """验证连接配置"""
        errors = []
        
        try:
            connection = self.config.get("connection", {})
            authentication = self.config.get("authentication", {})
            database = self.config.get("database", {})
            ssl = self.config.get("ssl", {})
            
            # 构建连接字符串
            dsn = (
                f"postgresql://{authentication.get('username')}:{authentication.get('password')}"
                f"@{connection.get('host')}:{connection.get('port')}"
                f"/{database.get('database')}"
            )
            
            # 连接参数
            connect_args = {
                "timeout": connection.get("connect_timeout", 10),
                "command_timeout": connection.get("command_timeout", 30),
                "ssl": ssl.get("enabled", False)
            }
            
            # 测试连接
            conn = await asyncpg.connect(dsn, **connect_args)
            await conn.execute("SELECT 1")
            await conn.close()
            
        except Exception as e:
            errors.append(f"PostgreSQL connection test failed: {e}")
        
        return errors
    
    async def _validate_database(self) -> List[str]:
        """验证数据库配置"""
        errors = []
        
        try:
            connection = self.config.get("connection", {})
            authentication = self.config.get("authentication", {})
            database = self.config.get("database", {})
            
            dsn = (
                f"postgresql://{authentication.get('username')}:{authentication.get('password')}"
                f"@{connection.get('host')}:{connection.get('port')}"
                f"/{database.get('database')}"
            )
            
            conn = await asyncpg.connect(dsn)
            
            # 检查模式是否存在
            schema_name = database.get("schema_name", "public")
            schema_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name = $1)",
                schema_name
            )
            
            if not schema_exists:
                errors.append(f"Schema '{schema_name}' does not exist")
            
            # 检查表是否存在
            table_name = database.get("table_name", "storage_records")
            table_exists = await conn.fetchval(
                "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_schema = $1 AND table_name = $2)",
                schema_name, table_name
            )
            
            if not table_exists and not database.get("auto_create_tables", True):
                errors.append(f"Table '{table_name}' does not exist and auto_create_tables is disabled")
            
            await conn.close()
            
        except Exception as e:
            errors.append(f"Database validation failed: {e}")
        
        return errors
    
    def _validate_performance(self) -> List[str]:
        """验证性能配置"""
        errors = []
        
        batch_operations = self.config.get("batch_operations", {})
        batch_size = batch_operations.get("batch_size", 100)
        if not isinstance(batch_size, int) or batch_size < 1:
            errors.append("Batch size must be a positive integer")
        
        pool = self.config.get("pool", {})
        pool_size = pool.get("pool_size", 10)
        if not isinstance(pool_size, int) or pool_size < 1:
            errors.append("Pool size must be a positive integer")
        
        return errors

# 使用示例
async def validate_postgresql_config(config_path: str):
    """验证PostgreSQL配置"""
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    validator = PostgreSQLConfigValidator(config)
    errors = await validator.validate()
    
    if errors:
        print("PostgreSQL configuration errors:")
        for error in errors:
            print(f"  - {error}")
        return False
    else:
        print("PostgreSQL configuration is valid")
        return True

if __name__ == "__main__":
    asyncio.run(validate_postgresql_config("postgresql_config.yaml"))
```

## 总结

本文档提供了Redis和PostgreSQL存储后端的完整配置模板，包括：

1. **多环境支持**: 开发、测试、生产环境的配置模板
2. **专用配置**: 缓存、会话、分析型、时序数据库等专用配置
3. **环境变量**: 完整的环境变量配置模板
4. **验证脚本**: 自动化配置验证工具

这些配置模板为不同场景提供了开箱即用的配置方案，确保存储系统能够在各种环境中稳定运行。