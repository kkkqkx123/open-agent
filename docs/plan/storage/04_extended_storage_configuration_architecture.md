# 扩展存储配置选项架构

## 概述

本文档设计扩展的存储配置选项架构，为Redis和PostgreSQL存储后端提供统一、灵活、可扩展的配置管理系统。

## 设计目标

1. **统一配置**: 为所有存储类型提供统一的配置接口
2. **灵活扩展**: 支持新存储类型的配置扩展
3. **类型安全**: 使用强类型配置模型，确保配置正确性
4. **环境适配**: 支持多环境配置和动态切换
5. **验证机制**: 提供完整的配置验证和错误报告

## 架构设计

### 1. 配置层次结构

```
configs/
├── storage/                          # 存储配置目录
│   ├── storage_types.yaml           # 存储类型定义
│   ├── storage_adapters.yaml        # 存储适配器配置
│   ├── storage_profiles.yaml        # 存储配置文件
│   ├── storage_policies.yaml        # 存储策略配置
│   └── environments/                # 环境特定配置
│       ├── development.yaml
│       ├── testing.yaml
│       ├── staging.yaml
│       └── production.yaml
├── storage/                         # 原有存储配置（向后兼容）
│   └── storage.yaml
└── global.yaml                      # 全局配置
```

### 2. 配置模型设计

#### 2.1 基础配置模型

```python
from typing import Dict, Any, Optional, List, Union
from enum import Enum
from pydantic import BaseModel, Field, validator

class StorageType(str, Enum):
    """存储类型枚举"""
    MEMORY = "memory"
    SQLITE = "sqlite"
    FILE = "file"
    REDIS = "redis"
    POSTGRESQL = "postgresql"

class SerializationFormat(str, Enum):
    """序列化格式枚举"""
    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"

class TTLStrategy(str, Enum):
    """TTL策略枚举"""
    NONE = "none"
    ABSOLUTE = "absolute"
    SLIDING = "sliding"

class CompressionAlgorithm(str, Enum):
    """压缩算法枚举"""
    GZIP = "gzip"
    LZ4 = "lz4"
    ZSTD = "zstd"

class StorageCategory(str, Enum):
    """存储类别枚举"""
    MEMORY = "memory"
    DATABASE = "database"
    NOSQL = "nosql"
    FILESYSTEM = "filesystem"
    DISTRIBUTED = "distributed"

class StorageFeature(str, Enum):
    """存储特性枚举"""
    PERSISTENT = "persistent"
    VOLATILE = "volatile"
    TRANSACTIONAL = "transactional"
    DISTRIBUTED = "distributed"
    CLUSTERED = "clustered"
    INDEXED = "indexed"
    BACKUP = "backup"
    COMPRESSION = "compression"
    ENCRYPTION = "encryption"
    HIGH_PERFORMANCE = "high_performance"
    SCALABLE = "scalable"
```

#### 2.2 连接配置模型

```python
class ConnectionConfig(BaseModel):
    """连接配置基类"""
    host: str = Field(..., description="主机地址")
    port: int = Field(..., description="端口号")
    timeout: int = Field(30, description="连接超时时间（秒）")
    retry_count: int = Field(3, description="重试次数")
    retry_delay: float = Field(1.0, description="重试延迟（秒）")

class PoolConfig(BaseModel):
    """连接池配置"""
    pool_size: int = Field(10, description="连接池大小")
    max_overflow: int = Field(20, description="最大溢出连接数")
    pool_timeout: int = Field(30, description="池超时时间（秒）")
    pool_recycle: int = Field(3600, description="连接回收时间（秒）")
    pool_pre_ping: bool = Field(True, description="连接预检查")

class SSLConfig(BaseModel):
    """SSL配置"""
    enabled: bool = Field(False, description="是否启用SSL")
    cert_file: Optional[str] = Field(None, description="证书文件路径")
    key_file: Optional[str] = Field(None, description="私钥文件路径")
    ca_file: Optional[str] = Field(None, description="CA证书文件路径")
    ssl_mode: str = Field("prefer", description="SSL模式")

class AuthenticationConfig(BaseModel):
    """认证配置"""
    username: Optional[str] = Field(None, description="用户名")
    password: Optional[str] = Field(None, description="密码")
    token: Optional[str] = Field(None, description="认证令牌")
    api_key: Optional[str] = Field(None, description="API密钥")
```

#### 2.3 存储特定配置模型

```python
class RedisConfig(BaseModel):
    """Redis存储配置"""
    # 连接配置
    connection: ConnectionConfig
    pool: PoolConfig
    authentication: Optional[AuthenticationConfig] = None
    
    # Redis特定配置
    db: int = Field(0, description="数据库编号")
    sentinel_enabled: bool = Field(False, description="是否启用哨兵模式")
    sentinel_hosts: List[str] = Field(default_factory=list, description="哨兵主机列表")
    sentinel_service_name: str = Field("mymaster", description="哨兵服务名称")
    
    # 集群配置
    cluster_enabled: bool = Field(False, description="是否启用集群模式")
    cluster_nodes: List[Dict[str, Any]] = Field(default_factory=list, description="集群节点列表")
    cluster_skip_full_coverage_check: bool = Field(True, description="跳过完整覆盖检查")
    
    # 序列化配置
    serialization_format: SerializationFormat = Field(SerializationFormat.JSON, description="序列化格式")
    compression_enabled: bool = Field(False, description="是否启用压缩")
    compression_algorithm: CompressionAlgorithm = Field(CompressionAlgorithm.GZIP, description="压缩算法")
    
    # TTL配置
    ttl_strategy: TTLStrategy = Field(TTLStrategy.ABSOLUTE, description="TTL策略")
    default_ttl_seconds: int = Field(3600, description="默认TTL（秒）")
    
    # 性能配置
    batch_size: int = Field(100, description="批量操作大小")
    pipeline_enabled: bool = Field(True, description="是否启用管道")
    pipeline_max_size: int = Field(1000, description="管道最大大小")
    
    # 监控配置
    metrics_enabled: bool = Field(True, description="是否启用指标")
    slow_log_enabled: bool = Field(True, description="是否启用慢查询日志")
    slow_log_threshold_ms: int = Field(100, description="慢查询阈值（毫秒）")

class PostgreSQLConfig(BaseModel):
    """PostgreSQL存储配置"""
    # 连接配置
    connection: ConnectionConfig
    pool: PoolConfig
    authentication: AuthenticationConfig
    ssl: SSLConfig
    
    # 数据库配置
    database: str = Field(..., description="数据库名称")
    schema_name: str = Field("public", description="模式名称")
    table_name: str = Field("storage_records", description="表名称")
    
    # 连接参数
    connect_timeout: int = Field(10, description="连接超时（秒）")
    command_timeout: int = Field(30, description="命令超时（秒）")
    statement_timeout: int = Field(30000, description="语句超时（毫秒）")
    
    # 索引配置
    auto_create_indexes: bool = Field(True, description="自动创建索引")
    index_type: str = Field("btree", description="索引类型")
    
    # 分区配置
    partitioning_enabled: bool = Field(False, description="是否启用分区")
    partition_strategy: str = Field("range", description="分区策略")
    partition_column: str = Field("created_at", description="分区列")
    partition_interval: str = Field("monthly", description="分区间隔")
    
    # 压缩配置
    compression_enabled: bool = Field(False, description="是否启用压缩")
    compression_algorithm: str = Field("pglz", description="压缩算法")
    
    # TTL配置
    ttl_enabled: bool = Field(True, description="是否启用TTL")
    ttl_cleanup_interval_hours: int = Field(1, description="TTL清理间隔（小时）")
    default_ttl_days: int = Field(30, description="默认TTL（天）")
    
    # 批量操作配置
    batch_size: int = Field(1000, description="批量操作大小")
    bulk_insert_enabled: bool = Field(True, description="是否启用批量插入")
    bulk_update_enabled: bool = Field(True, description="是否启用批量更新")
    
    # 迁移配置
    auto_migrate: bool = Field(True, description="是否自动迁移")
    migration_table: str = Field("alembic_version", description="迁移表名称")
    
    # 监控配置
    metrics_enabled: bool = Field(True, description="是否启用指标")
    slow_query_threshold_ms: int = Field(1000, description="慢查询阈值（毫秒）")
    explain_analyze_enabled: bool = Field(False, description="是否启用执行计划分析")
```

#### 2.4 统一存储配置模型

```python
class StorageTypeConfig(BaseModel):
    """存储类型配置"""
    name: str = Field(..., description="存储类型名称")
    class_path: str = Field(..., description="实现类路径")
    description: str = Field(..., description="描述")
    category: StorageCategory = Field(..., description="存储类别")
    features: List[StorageFeature] = Field(default_factory=list, description="特性列表")
    
    # 性能指标
    performance: Dict[str, str] = Field(default_factory=dict, description="性能指标")
    
    # 依赖配置
    dependencies: List[str] = Field(default_factory=list, description="依赖包列表")
    optional_dependencies: List[str] = Field(default_factory=list, description="可选依赖包列表")
    
    # 配置模式
    config_schema: Dict[str, Any] = Field(default_factory=dict, description="配置模式")
    
    # 默认配置
    default_config: Dict[str, Any] = Field(default_factory=dict, description="默认配置")

class StorageProfileConfig(BaseModel):
    """存储配置文件"""
    name: str = Field(..., description="配置文件名称")
    storage_type: StorageType = Field(..., description="存储类型")
    enabled: bool = Field(True, description="是否启用")
    is_default: bool = Field(False, description="是否为默认配置")
    
    # 存储特定配置
    config: Union[RedisConfig, PostgreSQLConfig, Dict[str, Any]] = Field(..., description="存储配置")
    
    # 元数据
    description: Optional[str] = Field(None, description="描述")
    tags: List[str] = Field(default_factory=list, description="标签")
    
    # 环境限制
    environments: List[str] = Field(default_factory=list, description="适用环境列表")

class StoragePolicyConfig(BaseModel):
    """存储策略配置"""
    name: str = Field(..., description="策略名称")
    description: str = Field(..., description="策略描述")
    
    # TTL策略
    ttl_policy: Dict[str, Any] = Field(default_factory=dict, description="TTL策略")
    
    # 备份策略
    backup_policy: Dict[str, Any] = Field(default_factory=dict, description="备份策略")
    
    # 清理策略
    cleanup_policy: Dict[str, Any] = Field(default_factory=dict, description="清理策略")
    
    # 监控策略
    monitoring_policy: Dict[str, Any] = Field(default_factory=dict, description="监控策略")
    
    # 安全策略
    security_policy: Dict[str, Any] = Field(default_factory=dict, description="安全策略")

class StorageEnvironmentConfig(BaseModel):
    """存储环境配置"""
    environment: str = Field(..., description="环境名称")
    
    # 默认存储类型
    default_storage_type: StorageType = Field(..., description="默认存储类型")
    
    # 存储配置文件
    profiles: List[StorageProfileConfig] = Field(default_factory=list, description="存储配置文件列表")
    
    # 策略配置
    policies: List[StoragePolicyConfig] = Field(default_factory=list, description="策略配置列表")
    
    # 全局设置
    global_settings: Dict[str, Any] = Field(default_factory=dict, description="全局设置")
```

### 3. 配置文件结构

#### 3.1 存储类型定义 (`storage_types.yaml`)

```yaml
# 存储类型定义文件
version: "1.0"

# 全局设置
global:
  default_type: "sqlite"
  enable_validation: true
  enable_metrics: true

# 存储类型定义
storage_types:
  redis:
    name: "Redis"
    class_path: "src.adapters.storage.backends.redis_backend.RedisStorageBackend"
    description: "Redis分布式存储后端"
    category: "nosql"
    features:
      - "distributed"
      - "persistent"
      - "clustered"
      - "high_performance"
      - "pubsub"
    performance:
      read_speed: "high"
      write_speed: "high"
      scalability: "high"
      consistency: "eventual"
    dependencies:
      - "redis>=5.0.0"
    optional_dependencies:
      - "msgpack>=1.0.0"
      - "lz4>=4.0.0"
    config_schema:
      type: "object"
      properties:
        connection:
          $ref: "#/schemas/ConnectionConfig"
        pool:
          $ref: "#/schemas/PoolConfig"
        serialization_format:
          type: "string"
          enum: ["json", "pickle", "msgpack"]
          default: "json"
        ttl_strategy:
          type: "string"
          enum: ["none", "absolute", "sliding"]
          default: "absolute"
    default_config:
      connection:
        host: "localhost"
        port: 6379
        timeout: 30
      pool:
        pool_size: 10
        max_overflow: 20
      serialization_format: "json"
      ttl_strategy: "absolute"
      default_ttl_seconds: 3600

  postgresql:
    name: "PostgreSQL"
    class_path: "src.adapters.storage.backends.postgresql_backend.PostgreSQLStorageBackend"
    description: "PostgreSQL企业级存储后端"
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
      consistency: "strong"
    dependencies:
      - "asyncpg>=0.28.0"
      - "sqlalchemy[asyncio]>=2.0.0"
      - "alembic>=1.10.0"
    optional_dependencies:
      - "psycopg2-binary>=2.9.0"
      - "pgspecial>=2.0.0"
    config_schema:
      type: "object"
      properties:
        connection:
          $ref: "#/schemas/ConnectionConfig"
        pool:
          $ref: "#/schemas/PoolConfig"
        authentication:
          $ref: "#/schemas/AuthenticationConfig"
        ssl:
          $ref: "#/schemas/SSLConfig"
        database:
          type: "string"
          description: "数据库名称"
        partitioning_enabled:
          type: "boolean"
          default: false
    default_config:
      connection:
        host: "localhost"
        port: 5432
        timeout: 30
      pool:
        pool_size: 10
        max_overflow: 20
      authentication:
        username: "postgres"
        password: ""
      ssl:
        enabled: false
        ssl_mode: "prefer"
      database: "storage"
      partitioning_enabled: false

# 配置模式定义
schemas:
  ConnectionConfig:
    type: "object"
    properties:
      host:
        type: "string"
        description: "主机地址"
      port:
        type: "integer"
        description: "端口号"
      timeout:
        type: "integer"
        default: 30
        description: "连接超时时间（秒）"
    required:
      - "host"
      - "port"

  PoolConfig:
    type: "object"
    properties:
      pool_size:
        type: "integer"
        default: 10
        description: "连接池大小"
      max_overflow:
        type: "integer"
        default: 20
        description: "最大溢出连接数"
      pool_timeout:
        type: "integer"
        default: 30
        description: "池超时时间（秒）"

  AuthenticationConfig:
    type: "object"
    properties:
      username:
        type: "string"
        description: "用户名"
      password:
        type: "string"
        description: "密码"
      token:
        type: "string"
        description: "认证令牌"

  SSLConfig:
    type: "object"
    properties:
      enabled:
        type: "boolean"
        default: false
        description: "是否启用SSL"
      cert_file:
        type: "string"
        description: "证书文件路径"
      key_file:
        type: "string"
        description: "私钥文件路径"
      ca_file:
        type: "string"
        description: "CA证书文件路径"
      ssl_mode:
        type: "string"
        enum: ["disable", "allow", "prefer", "require", "verify-ca", "verify-full"]
        default: "prefer"
```

#### 3.2 存储配置文件 (`storage_profiles.yaml`)

```yaml
# 存储配置文件
version: "1.0"

# 存储配置文件定义
profiles:
  # Redis开发配置
  redis_dev:
    storage_type: "redis"
    enabled: true
    is_default: true
    environments: ["development"]
    description: "Redis开发环境配置"
    tags: ["redis", "development", "cache"]
    config:
      connection:
        host: "${REDIS_HOST:localhost}"
        port: "${REDIS_PORT:6379}"
        timeout: 30
      pool:
        pool_size: 5
        max_overflow: 10
      serialization_format: "json"
      ttl_strategy: "sliding"
      default_ttl_seconds: 1800
      compression_enabled: false
      metrics_enabled: true

  # Redis生产配置
  redis_prod:
    storage_type: "redis"
    enabled: true
    is_default: false
    environments: ["production"]
    description: "Redis生产环境配置"
    tags: ["redis", "production", "cluster"]
    config:
      cluster_enabled: true
      cluster_nodes:
        - host: "${REDIS_NODE_1_HOST}"
          port: "${REDIS_NODE_1_PORT:6379}"
        - host: "${REDIS_NODE_2_HOST}"
          port: "${REDIS_NODE_2_PORT:6379}"
        - host: "${REDIS_NODE_3_HOST}"
          port: "${REDIS_NODE_3_PORT:6379}"
      pool:
        pool_size: 20
        max_overflow: 40
      serialization_format: "msgpack"
      compression_enabled: true
      compression_algorithm: "lz4"
      ttl_strategy: "absolute"
      default_ttl_seconds: 3600
      metrics_enabled: true
      slow_log_enabled: true
      slow_log_threshold_ms: 100

  # PostgreSQL开发配置
  postgresql_dev:
    storage_type: "postgresql"
    enabled: true
    is_default: false
    environments: ["development"]
    description: "PostgreSQL开发环境配置"
    tags: ["postgresql", "development", "relational"]
    config:
      connection:
        host: "${POSTGRES_HOST:localhost}"
        port: "${POSTGRES_PORT:5432}"
        timeout: 30
      pool:
        pool_size: 5
        max_overflow: 10
      authentication:
        username: "${POSTGRES_USER:postgres}"
        password: "${POSTGRES_PASSWORD:postgres}"
      ssl:
        enabled: false
        ssl_mode: "prefer"
      database: "${POSTGRES_DB:storage_dev}"
      auto_migrate: true
      partitioning_enabled: false
      metrics_enabled: true

  # PostgreSQL生产配置
  postgresql_prod:
    storage_type: "postgresql"
    enabled: true
    is_default: true
    environments: ["production"]
    description: "PostgreSQL生产环境配置"
    tags: ["postgresql", "production", "enterprise"]
    config:
      connection:
        host: "${POSTGRES_HOST}"
        port: "${POSTGRES_PORT:5432}"
        timeout: 30
      pool:
        pool_size: 20
        max_overflow: 40
      authentication:
        username: "${POSTGRES_USER}"
        password: "${POSTGRES_PASSWORD}"
      ssl:
        enabled: true
        ssl_mode: "require"
        cert_file: "${POSTGRES_SSL_CERT_FILE}"
        key_file: "${POSTGRES_SSL_KEY_FILE}"
        ca_file: "${POSTGRES_SSL_CA_FILE}"
      database: "${POSTGRES_DB}"
      auto_migrate: true
      partitioning_enabled: true
      partition_strategy: "range"
      partition_column: "created_at"
      partition_interval: "monthly"
      compression_enabled: true
      metrics_enabled: true
      slow_query_threshold_ms: 500
      backup_enabled: true
      backup_interval_hours: 6
```

#### 3.3 存储策略配置 (`storage_policies.yaml`)

```yaml
# 存储策略配置文件
version: "1.0"

# 策略定义
policies:
  # TTL策略
  ttl_policies:
    default:
      description: "默认TTL策略"
      default_ttl_seconds: 3600
      strategy: "absolute"
      cleanup_interval_hours: 1
    
    session_data:
      description: "会话数据TTL策略"
      default_ttl_seconds: 1800
      strategy: "sliding"
      cleanup_interval_hours: 0.5
    
    cache_data:
      description: "缓存数据TTL策略"
      default_ttl_seconds: 300
      strategy: "absolute"
      cleanup_interval_hours: 0.25
    
    audit_data:
      description: "审计数据TTL策略"
      default_ttl_days: 90
      strategy: "absolute"
      cleanup_interval_hours: 24

  # 备份策略
  backup_policies:
    development:
      description: "开发环境备份策略"
      enabled: false
      interval_hours: 24
      retention_days: 7
      compression: true
      encryption: false
    
    testing:
      description: "测试环境备份策略"
      enabled: false
      interval_hours: 48
      retention_days: 3
      compression: true
      encryption: false
    
    production:
      description: "生产环境备份策略"
      enabled: true
      interval_hours: 6
      retention_days: 30
      compression: true
      encryption: true
      backup_path: "${STORAGE_BACKUP_PATH:/var/backups/storage}"

  # 清理策略
  cleanup_policies:
    conservative:
      description: "保守清理策略"
      enabled: true
      interval_hours: 24
      retention_days: 90
      batch_size: 1000
      dry_run: false
    
    aggressive:
      description: "激进清理策略"
      enabled: true
      interval_hours: 6
      retention_days: 30
      batch_size: 5000
      dry_run: false
    
    disabled:
      description: "禁用清理策略"
      enabled: false

  # 监控策略
  monitoring_policies:
    basic:
      description: "基础监控策略"
      metrics_enabled: true
      health_check_interval_seconds: 60
      slow_query_threshold_ms: 1000
      alert_enabled: false
    
    detailed:
      description: "详细监控策略"
      metrics_enabled: true
      health_check_interval_seconds: 30
      slow_query_threshold_ms: 500
      alert_enabled: true
      alert_webhook_url: "${STORAGE_ALERT_WEBHOOK_URL}"
      log_slow_queries: true
      explain_slow_queries: true
    
    minimal:
      description: "最小监控策略"
      metrics_enabled: false
      health_check_interval_seconds: 300
      slow_query_threshold_ms: 5000
      alert_enabled: false

  # 安全策略
  security_policies:
    development:
      description: "开发环境安全策略"
      encryption_enabled: false
      access_control_enabled: false
      audit_enabled: false
    
    testing:
      description: "测试环境安全策略"
      encryption_enabled: false
      access_control_enabled: true
      audit_enabled: true
    
    production:
      description: "生产环境安全策略"
      encryption_enabled: true
      encryption_algorithm: "AES-256-GCM"
      key_rotation_days: 90
      access_control_enabled: true
      audit_enabled: true
      audit_retention_days: 365
```

#### 3.4 环境特定配置 (`environments/production.yaml`)

```yaml
# 生产环境配置
environment: "production"

# 默认存储类型
default_storage_type: "postgresql"

# 启用的配置文件
enabled_profiles:
  - "redis_prod"
  - "postgresql_prod"

# 启用的策略
enabled_policies:
  ttl: "default"
  backup: "production"
  cleanup: "conservative"
  monitoring: "detailed"
  security: "production"

# 全局设置
global_settings:
  # 性能设置
  performance:
    connection_pool_size: 20
    batch_size: 1000
    cache_enabled: true
    cache_size_mb: 512
  
  # 可用性设置
  availability:
    health_check_enabled: true
    health_check_interval_seconds: 30
    circuit_breaker_enabled: true
    circuit_breaker_threshold: 5
    retry_enabled: true
    retry_max_attempts: 3
  
  # 监控设置
  monitoring:
    metrics_enabled: true
    tracing_enabled: true
    logging_enabled: true
    log_level: "INFO"
  
  # 安全设置
  security:
    encryption_enabled: true
    ssl_enabled: true
    authentication_enabled: true
    authorization_enabled: true

# 环境变量映射
environment_variables:
  REDIS_HOST: "REDIS_PROD_HOST"
  REDIS_PORT: "REDIS_PROD_PORT"
  REDIS_PASSWORD: "REDIS_PROD_PASSWORD"
  POSTGRES_HOST: "POSTGRES_PROD_HOST"
  POSTGRES_PORT: "POSTGRES_PROD_PORT"
  POSTGRES_DB: "POSTGRES_PROD_DB"
  POSTGRES_USER: "POSTGRES_PROD_USER"
  POSTGRES_PASSWORD: "POSTGRES_PROD_PASSWORD"
```

### 4. 配置管理器设计

#### 4.1 配置管理器接口

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class IStorageConfigManager(ABC):
    """存储配置管理器接口"""
    
    @abstractmethod
    async def load_storage_types(self) -> Dict[str, StorageTypeConfig]:
        """加载存储类型配置"""
        pass
    
    @abstractmethod
    async def load_storage_profiles(self, environment: str) -> List[StorageProfileConfig]:
        """加载存储配置文件"""
        pass
    
    @abstractmethod
    async def load_storage_policies(self, environment: str) -> Dict[str, StoragePolicyConfig]:
        """加载存储策略配置"""
        pass
    
    @abstractmethod
    async def get_storage_config(self, profile_name: str, environment: str) -> Dict[str, Any]:
        """获取存储配置"""
        pass
    
    @abstractmethod
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        pass
    
    @abstractmethod
    async def reload_config(self) -> None:
        """重新加载配置"""
        pass
```

#### 4.2 配置管理器实现

```python
class StorageConfigManager(IStorageConfigManager):
    """存储配置管理器实现"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._storage_types: Dict[str, StorageTypeConfig] = {}
        self._profiles: Dict[str, List[StorageProfileConfig]] = {}
        self._policies: Dict[str, Dict[str, StoragePolicyConfig]] = {}
        self._environment_configs: Dict[str, StorageEnvironmentConfig] = {}
    
    async def initialize(self):
        """初始化配置管理器"""
        await self.load_all_configs()
    
    async def load_all_configs(self):
        """加载所有配置"""
        # 加载存储类型
        await self.load_storage_types()
        
        # 加载环境配置
        environments = ["development", "testing", "staging", "production"]
        for env in environments:
            await self.load_environment_config(env)
    
    async def load_storage_types(self) -> Dict[str, StorageTypeConfig]:
        """加载存储类型配置"""
        try:
            config_data = self.config_loader.load_config("storage/storage_types.yaml")
            
            storage_types = {}
            for type_name, type_config in config_data.get("storage_types", {}).items():
                storage_types[type_name] = StorageTypeConfig(**type_config)
            
            self._storage_types = storage_types
            return storage_types
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load storage types: {e}")
    
    async def load_storage_profiles(self, environment: str) -> List[StorageProfileConfig]:
        """加载存储配置文件"""
        try:
            config_data = self.config_loader.load_config("storage/storage_profiles.yaml")
            
            profiles = []
            for profile_name, profile_config in config_data.get("profiles", {}).items():
                profile = StorageProfileConfig(
                    name=profile_name,
                    **profile_config
                )
                
                # 检查环境匹配
                if not profile.environments or environment in profile.environments:
                    profiles.append(profile)
            
            self._profiles[environment] = profiles
            return profiles
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load storage profiles for {environment}: {e}")
    
    async def load_storage_policies(self, environment: str) -> Dict[str, StoragePolicyConfig]:
        """加载存储策略配置"""
        try:
            config_data = self.config_loader.load_config("storage/storage_policies.yaml")
            
            policies = {}
            for policy_category, policy_configs in config_data.get("policies", {}).items():
                for policy_name, policy_config in policy_configs.items():
                    full_name = f"{policy_category}.{policy_name}"
                    policies[full_name] = StoragePolicyConfig(
                        name=full_name,
                        **policy_config
                    )
            
            self._policies[environment] = policies
            return policies
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load storage policies for {environment}: {e}")
    
    async def load_environment_config(self, environment: str) -> StorageEnvironmentConfig:
        """加载环境配置"""
        try:
            config_path = f"storage/environments/{environment}.yaml"
            config_data = self.config_loader.load_config(config_path)
            
            env_config = StorageEnvironmentConfig(**config_data)
            self._environment_configs[environment] = env_config
            
            return env_config
            
        except Exception as e:
            raise ConfigurationError(f"Failed to load environment config for {environment}: {e}")
    
    async def get_storage_config(self, profile_name: str, environment: str) -> Dict[str, Any]:
        """获取存储配置"""
        # 获取配置文件
        profiles = self._profiles.get(environment, [])
        profile = next((p for p in profiles if p.name == profile_name), None)
        
        if not profile:
            raise ValueError(f"Profile '{profile_name}' not found for environment '{environment}'")
        
        # 获取存储类型配置
        storage_type = self._storage_types.get(profile.storage_type.value)
        if not storage_type:
            raise ValueError(f"Storage type '{profile.storage_type}' not found")
        
        # 合并配置
        config = {
            **storage_type.default_config,
            **profile.config
        }
        
        return config
    
    async def validate_config(self, storage_type: str, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        errors = []
        
        # 获取存储类型配置
        type_config = self._storage_types.get(storage_type)
        if not type_config:
            errors.append(f"Unknown storage type: {storage_type}")
            return errors
        
        # 使用JSON Schema验证
        try:
            import jsonschema
            jsonschema.validate(config, type_config.config_schema)
        except Exception as e:
            errors.append(f"Configuration validation failed: {e}")
        
        # 自定义验证逻辑
        if storage_type == "redis":
            errors.extend(self._validate_redis_config(config))
        elif storage_type == "postgresql":
            errors.extend(self._validate_postgresql_config(config))
        
        return errors
    
    def _validate_redis_config(self, config: Dict[str, Any]) -> List[str]:
        """验证Redis配置"""
        errors = []
        
        # 验证连接配置
        connection = config.get("connection", {})
        if not connection.get("host"):
            errors.append("Redis connection host is required")
        
        port = connection.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("Redis connection port must be a valid port number")
        
        # 验证集群配置
        if config.get("cluster_enabled"):
            cluster_nodes = config.get("cluster_nodes", [])
            if len(cluster_nodes) < 3:
                errors.append("Redis cluster requires at least 3 nodes")
        
        return errors
    
    def _validate_postgresql_config(self, config: Dict[str, Any]) -> List[str]:
        """验证PostgreSQL配置"""
        errors = []
        
        # 验证连接配置
        connection = config.get("connection", {})
        if not connection.get("host"):
            errors.append("PostgreSQL connection host is required")
        
        port = connection.get("port")
        if not isinstance(port, int) or port < 1 or port > 65535:
            errors.append("PostgreSQL connection port must be a valid port number")
        
        # 验证认证配置
        auth = config.get("authentication", {})
        if not auth.get("username"):
            errors.append("PostgreSQL username is required")
        
        # 验证数据库配置
        if not config.get("database"):
            errors.append("PostgreSQL database name is required")
        
        return errors
    
    async def reload_config(self) -> None:
        """重新加载配置"""
        await self.load_all_configs()
```

### 5. 配置验证和错误处理

#### 5.1 配置验证器

```python
class StorageConfigValidator:
    """存储配置验证器"""
    
    def __init__(self, config_manager: StorageConfigManager):
        self.config_manager = config_manager
    
    async def validate_all_configs(self, environment: str) -> Dict[str, List[str]]:
        """验证所有配置"""
        validation_results = {}
        
        # 验证存储配置文件
        profiles = await self.config_manager.load_storage_profiles(environment)
        for profile in profiles:
            errors = await self.config_manager.validate_config(
                profile.storage_type.value, 
                profile.config
            )
            if errors:
                validation_results[profile.name] = errors
        
        return validation_results
    
    async def validate_dependencies(self, environment: str) -> List[str]:
        """验证依赖"""
        errors = []
        
        profiles = await self.config_manager.load_storage_profiles(environment)
        
        for profile in profiles:
            storage_type = self.config_manager._storage_types.get(profile.storage_type.value)
            if not storage_type:
                continue
            
            # 检查必需依赖
            for dependency in storage_type.dependencies:
                if not self._is_package_installed(dependency):
                    errors.append(f"Missing required dependency for {profile.name}: {dependency}")
        
        return errors
    
    def _is_package_installed(self, package_spec: str) -> bool:
        """检查包是否已安装"""
        try:
            import importlib.metadata
            import pkg_resources
            
            # 提取包名（去掉版本要求）
            package_name = pkg_resources.Requirement.parse(package_spec).name
            
            # 检查是否已安装
            importlib.metadata.version(package_name)
            return True
            
        except Exception:
            return False
```

## 总结

扩展的存储配置选项架构提供了：

1. **统一配置模型**: 使用Pydantic模型确保类型安全
2. **分层配置结构**: 支持存储类型、配置文件、策略、环境等多层配置
3. **灵活扩展**: 易于添加新的存储类型和配置选项
4. **环境适配**: 支持多环境配置和动态切换
5. **完整验证**: 提供配置验证和依赖检查
6. **向后兼容**: 保持与现有配置系统的兼容性

该架构为存储系统提供了强大而灵活的配置管理能力，支持复杂的部署场景和运维需求。