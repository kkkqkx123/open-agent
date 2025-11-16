# 基础设施层缓存模块

本模块提供基础设施层的缓存功能，通过协议接口和适配器模式实现依赖注入，避免基础设施层直接依赖展示层。

## 模块结构

### 1. 缓存管理器协议 (`cache_manager_protocol.py`)

**职责**：定义缓存管理器的基本接口协议

**核心功能**：
- 定义 `CacheManagerProtocol` 协议接口
- 提供异步缓存操作：get、set、delete、clear
- 提供缓存统计信息：get_stats
- 使用 Python Protocol 类型，支持结构化类型检查

**设计目的**：
- 避免基础设施层直接依赖展示层的具体实现
- 支持依赖注入，提高模块的可测试性和灵活性
- 符合依赖倒置原则（高层模块不依赖低层模块，二者都依赖抽象）

### 2. 内存缓存管理器 (`memory_cache_manager.py`)

**职责**：提供基础设施层内部的默认缓存实现

**核心功能**：
- 实现 `CacheManagerProtocol` 协议接口
- 提供基于内存的键值缓存存储
- 支持 TTL（生存时间）过期机制
- 实现 LRU（最近最少使用）淘汰策略
- 提供线程安全的异步操作
- 支持缓存统计信息

**技术特性**：
- 使用 `asyncio.Lock` 保证线程安全
- 使用字典存储缓存数据和过期时间
- 使用访问时间记录实现 LRU 策略
- 默认 TTL：300秒，最大容量：1000项

**使用场景**：
- 作为 `ServiceCacheAdapter` 的默认缓存实现
- 在依赖注入未提供缓存管理器时使用
- 适用于开发和测试环境

### 3. 服务缓存适配器 (`service_cache_adapter.py`)

**职责**：将统一缓存管理器适配为 `IServiceCache` 接口

**核心功能**：
- 实现 `IServiceCache` 接口，提供同步缓存操作
- 将 Python 类型转换为字符串缓存键
- 包装异步调用为同步接口
- 支持依赖注入缓存管理器
- 提供缓存统计和优化功能

**适配功能**：
- 类型键转换：`service:{module}.{classname}`
- 异步转同步：使用事件循环或线程池执行异步操作
- 异常处理：提供降级和错误恢复机制
- 统计转发：将统计信息从底层缓存管理器传递出来

**依赖注入**：
- 构造函数接受 `CacheManagerProtocol` 实例
- 如果未提供，自动创建 `MemoryCacheManager` 默认实例
- 避免直接导入展示层的 `CacheManager`，符合架构原则

## 使用方式

### 基本使用

```python
from src.infrastructure.cache import ServiceCacheAdapter

# 使用默认内存缓存
adapter = ServiceCacheAdapter()

# 使用自定义缓存管理器
from src.infrastructure.cache import MemoryCacheManager

cache_manager = MemoryCacheManager(default_ttl=600, max_size=500)
adapter = ServiceCacheAdapter(cache_manager)

# 缓存服务实例
adapter.put(MyService, service_instance)

# 获取缓存的服务实例
cached_service = adapter.get(MyService)

# 移除缓存
adapter.remove(MyService)
```

### 在依赖注入容器中使用

```python
from src.infrastructure.container import EnhancedContainer
from src.infrastructure.cache import ServiceCacheAdapter

# 创建带缓存的容器
container = EnhancedContainer(service_cache=ServiceCacheAdapter())

# 容器会自动使用缓存来管理服务实例
service = container.resolve(MyService)  # 第一次创建
service2 = container.resolve(MyService)  # 第二次从缓存获取
```

## 架构价值

### 1. 分层解耦
- 基础设施层不直接依赖展示层
- 通过协议接口实现依赖倒置
- 支持多种缓存实现

### 2. 可测试性
- 可以轻松注入 Mock 缓存管理器
- 支持单元测试和集成测试
- 提供测试友好的默认实现

### 3. 灵活性
- 支持不同的缓存策略（内存、Redis、文件等）
- 可配置的 TTL 和容量限制
- 支持缓存统计和监控

### 4. 性能优化
- 异步操作避免阻塞
- LRU 淘汰策略保证内存使用
- 线程安全的并发访问

## 扩展性

### 自定义缓存管理器
实现 `CacheManagerProtocol` 协议即可创建自定义缓存管理器：

```python
from src.infrastructure.cache import CacheManagerProtocol

class RedisCacheManager(CacheManagerProtocol):
    async def get(self, key: str) -> Optional[Any]:
        # Redis 实现
        ...
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        # Redis 实现
        ...
    
    # 实现其他必需的方法...
```

### 高级缓存策略
可以通过组合模式实现更复杂的缓存策略：

```python
class TieredCacheManager(CacheManagerProtocol):
    """多级缓存管理器"""
    
    def __init__(self, l1_cache: CacheManagerProtocol, l2_cache: CacheManagerProtocol):
        self.l1_cache = l1_cache  # 内存缓存
        self.l2_cache = l2_cache  # Redis缓存
    
    async def get(self, key: str) -> Optional[Any]:
        # L1 -> L2 的缓存查找策略
        value = await self.l1_cache.get(key)
        if value is None:
            value = await self.l2_cache.get(key)
            if value is not None:
                await self.l1_cache.set(key, value, ttl=300)  # 回填L1
        return value
    
    # 实现其他方法...
```

## 注意事项

1. **线程安全**：内存缓存管理器使用异步锁保证线程安全，但在多线程环境中使用时需要注意事件循环的管理

2. **内存使用**：默认内存缓存适用于中小规模数据，大量数据建议使用外部缓存（如Redis）

3. **事件循环**：服务缓存适配器会自动处理事件循环，但在特殊环境中可能需要手动配置

4. **性能考虑**：异步转同步操作有一定性能开销，高频操作建议使用原生异步接口