# Redis缓存提供者实施计划

## 1. 项目概述

本计划详细说明如何在Modular Agent Framework中新增Redis缓存提供者，包括架构设计、依赖管理、配置系统和测试策略。

## 2. 当前架构分析

### 2.1 现有缓存架构
- **接口层**: [`ICacheProvider`](src/interfaces/llm/cache.py) 定义缓存提供者契约
- **基础设施层**: [`MemoryCacheProvider`](src/infrastructure/cache/providers/memory/memory_provider.py) 当前唯一实现
- **配置系统**: [`BaseCacheConfig`](src/infrastructure/cache/config/cache_config.py) 提供通用配置结构

### 2.2 接口定义
```python
class ICacheProvider(ABC):
    def get(self, key: str) -> Optional[Any]
    def set(self, key: str, value: Any, ttl: Optional[int] = None)
    def delete(self, key: str) -> bool
    def clear(self) -> None
    def exists(self, key: str) -> bool
    def get_size(self) -> int
    def cleanup_expired(self) -> int
    async def get_async(self, key: str) -> Optional[Any]
    async def set_async(self, key: str, value: Any, ttl: Optional[int] = None)
    def get_stats(self) -> Dict[str, Any]
```

## 3. Redis库选择与依赖

### 3.1 推荐库
- **主要库**: `redis[hiredis]` (推荐安装hiredis支持以获得更好性能)
- **版本要求**: Python 3.13+ 兼容
- **异步支持**: 使用 `redis.asyncio` 模块

### 3.2 依赖配置
在 [`pyproject.toml`](pyproject.toml) 中添加:
```toml
dependencies = [
    # 现有依赖...
    "redis[hiredis] >= 5.2.0",  # Redis客户端库，支持异步操作
]
```

## 4. Redis缓存提供者设计

### 4.1 类结构
```python
class RedisCacheProvider(ICacheProvider):
    """Redis缓存提供者实现"""
    
    def __init__(self, config: RedisCacheConfig):
        self._config = config
        self._client: Optional[redis.Redis] = None
        self._async_client: Optional[redis.asyncio.Redis] = None
```

### 4.2 配置类设计
```python
@dataclass
class RedisCacheConfig:
    """Redis缓存配置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    decode_responses: bool = True
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    retry_on_timeout: bool = True
    health_check_interval: int = 30
```

### 4.3 核心功能实现
- **连接管理**: 使用连接池管理Redis连接
- **序列化**: 使用JSON序列化复杂对象
- **错误处理**: 实现重试机制和连接恢复
- **异步支持**: 完整的异步操作实现

## 5. 配置系统集成

### 5.1 全局配置扩展
在 [`configs/global.yaml`](configs/global.yaml) 中添加Redis配置节:

```yaml
# Redis缓存配置
redis:
  enabled: true
  host: "${REDIS_HOST:localhost}"
  port: "${REDIS_PORT:6379}"
  db: "${REDIS_DB:0}"
  password: "${REDIS_PASSWORD:}"
  ssl: "${REDIS_SSL:false}"
  max_connections: 20
  default_ttl: 3600
```

### 5.2 缓存提供者配置
```yaml
cache:
  default_provider: "memory"  # 或 "redis"
  providers:
    memory:
      enabled: true
      max_size: 1000
      default_ttl: 3600
    
    redis:
      enabled: true
      host: "localhost"
      port: 6379
      db: 0
      key_prefix: "agent:cache:"
      default_ttl: 3600
      connection_pool:
        max_connections: 20
        timeout: 5
```

## 6. 依赖注入集成

### 6.1 创建缓存绑定模块
创建 [`src/services/container/bindings/cache_bindings.py`](src/services/container/bindings/cache_bindings.py):

```python
class CacheServiceBindings(BaseServiceBindings):
    """缓存服务绑定配置"""
    
    def _do_register_services(self, container, config, environment):
        # 注册缓存提供者工厂
        cache_config = config.get("cache", {})
        provider_config = cache_config.get("providers", {})
        
        # 注册Redis缓存提供者
        if provider_config.get("redis", {}).get("enabled", False):
            container.register_factory(
                ICacheProvider,
                self._create_redis_provider,
                name="redis"
            )
```

### 6.2 服务发现集成
在解析器中支持Redis缓存发现:
```python
# 在 src/interfaces/container/resolver.py 中
cache = resolver.try_get_named(ICache, "redis")
```

## 7. 测试策略

### 7.1 单元测试
- **位置**: `tests/infrastructure/cache/providers/test_redis_provider.py`
- **覆盖范围**: 所有ICacheProvider接口方法
- **Mock策略**: 使用mock-redis或Redis容器进行测试

### 7.2 集成测试
- **Redis容器测试**: 使用Docker运行Redis实例
- **配置测试**: 测试不同配置下的行为
- **性能测试**: 对比内存和Redis性能

### 7.3 测试依赖
```python
# tests/conftest.py 中添加Redis fixture
@pytest.fixture
def redis_server():
    """启动Redis测试服务器"""
    # 使用testcontainers或mock-redis
    pass
```

## 8. 实施路线图

### 阶段1: 基础实现 (2天)
1. ✅ 分析现有架构和接口
2. ✅ 研究Redis库最佳实践
3. 创建RedisCacheProvider基础实现
4. 实现配置类和数据序列化

### 阶段2: 集成配置 (2天)
1. 扩展全局配置系统
2. 创建缓存绑定配置
3. 集成依赖注入容器
4. 添加环境变量支持

### 阶段3: 测试验证 (2天)
1. 编写单元测试
2. 设置集成测试环境
3. 性能基准测试
4. 错误处理和恢复测试

### 阶段4: 文档和部署 (1天)
1. 编写使用文档
2. 更新配置示例
3. 创建部署指南
4. 性能优化建议

## 9. 性能考虑

### 9.1 连接池优化
- 使用连接池避免频繁连接建立
- 配置合理的最大连接数
- 实现连接健康检查

### 9.2 序列化优化
- 使用MessagePack或Protocol Buffers替代JSON
- 实现压缩选项
- 批量操作支持

### 9.3 监控指标
- 连接池使用率
- 命令执行时间
- 缓存命中率统计

## 10. 错误处理与恢复

### 10.1 连接故障处理
- 自动重连机制
- 故障转移支持
- 优雅降级到内存缓存

### 10.2 资源清理
- 连接池正确关闭
- 异步操作取消支持
- 内存泄漏预防

## 11. 扩展性考虑

### 11.1 集群支持
- Redis Cluster配置
- 分片策略
- 数据分布优化

### 11.2 高级特性
- Pub/Sub 集成
- 流水线操作
- 事务支持
- Lua脚本执行

## 12. 文档计划

### 12.1 开发文档
- API参考文档
- 配置选项说明
- 性能调优指南

### 12.2 用户文档
- 快速开始指南
- 常见问题解答
- 故障排除指南

---

**实施状态**: ✅ 计划完成  
**下一步**: 切换到Code模式开始实现