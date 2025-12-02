# LangGraph 缓存系统功能说明

## 概述

LangGraph 缓存系统提供了一个灵活、可扩展的缓存机制，用于在LangGraph框架中缓存数据。该系统支持多种存储后端，包括内存、Redis和SQLite，满足不同场景下的缓存需求。

## 架构设计

### BaseCache 抽象基类

BaseCache是缓存系统的核心抽象类，定义了统一的缓存接口：

- **泛型支持**：继承自Generic[ValueT]，支持任意类型的数据
- **序列化**：使用JsonPlusSerializer作为默认序列化器，支持pickle回退
- **命名空间**：使用Namespace类型（tuple[str, ...]）组织缓存键
- **完整键**：使用FullKey类型（tuple[Namespace, str]）表示完整的缓存键

### 核心接口

所有缓存实现都必须实现以下接口：

- `get()` / `aget()`：获取缓存值（同步/异步）
- `set()` / `aset()`：设置缓存值（同步/异步），支持TTL
- `clear()` / `aclear()`：清除缓存（同步/异步）

## 缓存实现

### 1. InMemoryCache（内存缓存）

#### 特点
- **存储位置**：进程内存
- **性能**：最快的访问速度
- **持久化**：非持久化，进程重启后数据丢失
- **容量**：受内存限制
- **并发**：使用threading.RLock()保证线程安全

#### 适用场景
- 单机应用
- 小容量缓存
- 对性能要求极高的场景

### 2. RedisCache（Redis缓存）

#### 特点
- **存储位置**：Redis服务器
- **性能**：高速访问，支持网络访问
- **持久化**：可配置持久化选项
- **容量**：可扩展，支持分布式
- **并发**：利用Redis服务器的并发处理能力

#### 适用场景
- 分布式应用
- 大容量缓存
- 需要跨进程/跨机器共享缓存的场景

### 3. SqliteCache（SQLite缓存）

#### 特点
- **存储位置**：SQLite数据库文件
- **性能**：良好的本地访问性能
- **持久化**：文件级持久化
- **容量**：受磁盘空间限制
- **并发**：使用WAL模式和锁机制处理并发

#### 适用场景
- 单机应用
- 需要持久化的缓存
- 中等容量的缓存需求

## 使用方法

### 基本用法

```python
from langgraph.cache.memory import InMemoryCache
from langgraph.cache.redis import RedisCache
from langgraph.cache.sqlite import SqliteCache

# 创建内存缓存实例
memory_cache = InMemoryCache()

# 创建Redis缓存实例
import redis
redis_client = redis.Redis(host='localhost', port=6379, db=0)
redis_cache = RedisCache(redis_client)

# 创建SQLite缓存实例
sqlite_cache = SqliteCache(path="cache.db")

# 使用缓存
namespace = ("graph_name", "node_name")
cache_key = "result_123"

# 设置缓存值（带TTL，单位秒）
cache.set({(namespace, cache_key): (data, 3600)})  # 1小时TTL

# 获取缓存值
values = cache.get([(namespace, cache_key)])

# 异步操作
await cache.aset({(namespace, cache_key): (data, 3600)})
values = await cache.aget([(namespace, cache_key)])

# 清除特定命名空间的缓存
cache.clear([namespace])

# 清除所有缓存
cache.clear()
```

### 序列化

所有缓存实现都使用LangGraph的序列化系统，支持多种数据类型：
- 基本数据类型（int, str, float, bool等）
- 复杂数据结构（list, dict, tuple等）
- 自定义对象（通过pickle序列化）

## 设计优势

1. **统一接口**：所有缓存实现都遵循相同的接口，便于切换
2. **灵活选择**：根据应用需求选择最适合的缓存后端
3. **线程安全**：所有实现都保证线程安全
4. **异步支持**：提供同步和异步操作接口
5. **容错处理**：Redis实现具有容错机制，Redis不可用时不会影响主程序
6. **TTL支持**：所有实现都支持缓存项的自动过期

## 选择建议

- **开发/测试环境**：使用InMemoryCache，简单高效
- **生产环境单机应用**：使用SqliteCache，兼顾性能和持久化
- **生产环境分布式应用**：使用RedisCache，支持高并发和分布式部署