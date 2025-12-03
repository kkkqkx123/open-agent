# 缓存系统架构设计文档

## 📋 概述

本文档详细说明了重构后的 `src/infrastructure/cache/` 目录的架构设计，以及相比初期设计的改进点。这是为了支持未来多种缓存提供者的扩展和更好的代码组织。

## 🎯 设计目标

1. **模块化**：清晰分离缓存核心框架和具体提供者实现
2. **可扩展性**：易于添加新的缓存提供者（Redis、SQLite、Memcached等）
3. **依赖隔离**：不同提供者的依赖独立管理
4. **可维护性**：清晰的职责划分和代码组织
5. **可测试性**：每个模块可独立单元测试

## 📁 改进的目录结构

### 初期设计（存在的问题）

```
src/infrastructure/cache/
├── __init__.py
├── cache_manager.py         # 缓存管理核心
├── key_generator.py         # 缓存键生成
└── providers/               # ❌ 所有提供者平铺在一个目录
    ├── __init__.py
    ├── memory_provider.py
    └── gemini_cache_manager.py
```

**存在的问题：**
- Providers目录会快速膨胀（当前2个，未来可能5+）
- 不同提供者的依赖混在一起
- 无法清晰表达提供者之间的差异
- 难以维护特定提供者的配置和文档

### 改进后的设计（推荐）

```
src/infrastructure/cache/
├── __init__.py
├── interfaces.py            # 缓存接口定义（从 src/interfaces/ 迁移）
├── core/                    # 缓存核心框架
│   ├── __init__.py
│   ├── cache_manager.py     # 缓存管理器核心逻辑
│   ├── key_generator.py     # 缓存键生成工具
│   └── exceptions.py        # 缓存相关异常
├── providers/               # 缓存提供者实现
│   ├── __init__.py
│   ├── base.py              # 基础提供者接口
│   ├── memory/              # 内存缓存提供者
│   │   ├── __init__.py
│   │   ├── memory_provider.py
│   │   └── README.md        # 内存提供者说明
│   ├── gemini/              # Google Gemini缓存提供者
│   │   ├── __init__.py
│   │   ├── gemini_cache_manager.py
│   │   ├── server_interfaces.py
│   │   └── README.md        # Gemini提供者说明
│   ├── redis/               # Redis缓存提供者（预留）
│   │   ├── __init__.py
│   │   ├── redis_provider.py
│   │   └── README.md
│   └── sqlite/              # SQLite缓存提供者（预留）
│       ├── __init__.py
│       ├── sqlite_provider.py
│       └── README.md
├── utils/                   # 缓存工具函数
│   ├── __init__.py
│   ├── decorators.py        # 缓存装饰器
│   └── serializers.py       # 序列化工具
├── config/                  # 缓存配置
│   ├── __init__.py
│   └── cache_config.py      # 缓存配置模型
└── README.md                # 总体说明文档
```

## 🏗️ 模块职责

### 1. Core模块 - 缓存核心框架

**位置**：`src/infrastructure/cache/core/`

**职责**：
- 定义缓存管理的基础接口和抽象
- 实现提供者无关的缓存逻辑
- 提供缓存键生成策略
- 异常处理和错误报告

**包含文件**：
```python
# cache_manager.py
class CacheManager:
    """缓存管理器
    
    - 管理多个缓存提供者
    - 提供统一的缓存接口
    - 支持提供者切换和回退
    """
    
# key_generator.py
class CacheKeyGenerator:
    """缓存键生成器
    
    - 生成一致的缓存键
    - 支持多种键生成策略
    - 处理键冲突
    """

# exceptions.py
class CacheError(Exception):
    """缓存异常基类"""
    
class CacheKeyError(CacheError):
    """缓存键错误"""
    
class CacheProviderError(CacheError):
    """缓存提供者错误"""
```

### 2. Providers模块 - 缓存提供者实现

**位置**：`src/infrastructure/cache/providers/`

**职责**：
- 实现具体的缓存提供者
- 处理特定存储介质的细节
- 提供提供者特定的优化

**提供者结构**：

```python
# providers/base.py
class BaseCacheProvider(ABC):
    """缓存提供者基类
    
    所有缓存提供者必须实现的接口
    """
    
    @abstractmethod
    async def get(self, key: str) -> Any:
        """获取缓存"""
        
    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        
    @abstractmethod
    async def delete(self, key: str) -> None:
        """删除缓存"""
        
    @abstractmethod
    async def clear(self) -> None:
        """清空所有缓存"""
```

#### 2.1 内存提供者 (Memory Provider)

**位置**：`src/infrastructure/cache/providers/memory/`

**特点**：
- 快速访问
- 进程内存储
- 重启丢失
- 无序列化开销

**使用场景**：
- 开发和测试
- 单进程应用
- 短期缓存

```python
# providers/memory/memory_provider.py
class MemoryCacheProvider(BaseCacheProvider):
    """内存缓存提供者"""
    
    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self._cache: Dict[str, Tuple[Any, float]] = {}
        self._max_size = max_size
        self._ttl = ttl
```

#### 2.2 Gemini提供者 (Gemini Cache Provider)

**位置**：`src/infrastructure/cache/providers/gemini/`

**特点**：
- Google Gemini API集成
- 支持服务端缓存
- 需要API密钥
- 适合大规模LLM调用

**使用场景**：
- Gemini LLM调用缓存
- 高并发场景
- 需要持久化

```python
# providers/gemini/gemini_cache_manager.py
class GeminiCacheManager(BaseCacheProvider):
    """Google Gemini缓存管理器
    
    集成Google Gemini API的缓存功能
    """
    
    def __init__(self, api_key: str, cache_config: GeminiCacheConfig):
        self._api_key = api_key
        self._cache_config = cache_config
```

#### 2.3 Redis提供者 (Redis Provider - 预留)

**位置**：`src/infrastructure/cache/providers/redis/`

**特点**：
- 分布式缓存
- 支持多进程/多服务器
- 需要Redis服务器
- 支持丰富的数据结构

**使用场景**：
- 分布式系统
- 多实例部署
- 需要共享缓存
- 高性能需求

```python
# providers/redis/redis_provider.py
class RedisCacheProvider(BaseCacheProvider):
    """Redis缓存提供者
    
    基于Redis的分布式缓存实现
    """
    
    def __init__(self, url: str, ttl: int = 3600):
        self._redis = redis.from_url(url)
        self._ttl = ttl
```

#### 2.4 SQLite提供者 (SQLite Provider - 预留)

**位置**：`src/infrastructure/cache/providers/sqlite/`

**特点**：
- 本地持久化
- 无需外部依赖
- 适合轻量级应用
- 支持结构化查询

**使用场景**：
- 桌面应用
- 本地开发
- 轻量级服务
- 需要持久化但无Redis

```python
# providers/sqlite/sqlite_provider.py
class SQLiteCacheProvider(BaseCacheProvider):
    """SQLite缓存提供者
    
    基于SQLite的本地持久化缓存实现
    """
    
    def __init__(self, db_path: str = "cache.db"):
        self._db_path = db_path
```

### 3. Utils模块 - 缓存工具函数

**位置**：`src/infrastructure/cache/utils/`

**职责**：
- 提供缓存装饰器
- 序列化/反序列化工具
- 缓存统计和监控

**包含文件**：
```python
# decorators.py
@cache(ttl=3600)
async def expensive_function():
    """缓存装饰器示例"""
    pass

# serializers.py
class CacheSerializer:
    """缓存序列化器"""
    
    def serialize(self, obj: Any) -> str:
        """序列化对象"""
        
    def deserialize(self, data: str) -> Any:
        """反序列化对象"""
```

### 4. Config模块 - 缓存配置

**位置**：`src/infrastructure/cache/config/`

**职责**：
- 定义缓存配置模型
- 支持多环境配置
- 配置验证

```python
# cache_config.py
class CacheConfig(BaseModel):
    """缓存配置"""
    provider: str  # memory, gemini, redis, sqlite
    ttl: int = 3600
    max_size: Optional[int] = None
    
class MemoryCacheConfig(CacheConfig):
    max_size: int = 1000
    
class RedisCacheConfig(CacheConfig):
    url: str
    password: Optional[str] = None
```

## 🔄 迁移路径

### 第1步：创建新的目录结构

```bash
# 创建core模块
mkdir -p src/infrastructure/cache/core
mkdir -p src/infrastructure/cache/providers/{memory,gemini}
mkdir -p src/infrastructure/cache/utils
mkdir -p src/infrastructure/cache/config
```

### 第2步：迁移core模块

```python
# 从 src/core/llm/cache/ 迁移
src/core/llm/cache/cache_manager.py → src/infrastructure/cache/core/cache_manager.py
src/core/llm/cache/key_generator.py → src/infrastructure/cache/core/key_generator.py

# 新增
src/infrastructure/cache/core/exceptions.py (新文件)
src/infrastructure/cache/core/interfaces.py (从 src/interfaces/ 迁移)
```

### 第3步：迁移提供者

```python
# Memory提供者
src/core/llm/cache/memory_provider.py → src/infrastructure/cache/providers/memory/memory_provider.py

# Gemini提供者
src/core/llm/cache/gemini_cache_manager.py → src/infrastructure/cache/providers/gemini/gemini_cache_manager.py
src/core/llm/cache/server_interfaces.py → src/infrastructure/cache/providers/gemini/server_interfaces.py
```

### 第4步：配置和工具

```python
# 配置
src/core/llm/cache/cache_config.py → src/infrastructure/cache/config/cache_config.py

# 工具（可选）
src/infrastructure/cache/utils/decorators.py (新文件)
src/infrastructure/cache/utils/serializers.py (新文件)
```

### 第5步：更新导入

```python
# 旧导入
from src.core.llm.cache.cache_manager import CacheManager
from src.core.llm.cache.memory_provider import MemoryCacheProvider

# 新导入
from src.infrastructure.cache.core.cache_manager import CacheManager
from src.infrastructure.cache.providers.memory.memory_provider import MemoryCacheProvider
```

## 🚀 扩展指南

### 添加新的缓存提供者

#### 1. 创建提供者目录

```bash
mkdir -p src/infrastructure/cache/providers/new_provider
touch src/infrastructure/cache/providers/new_provider/__init__.py
touch src/infrastructure/cache/providers/new_provider/new_provider.py
touch src/infrastructure/cache/providers/new_provider/README.md
```

#### 2. 实现提供者接口

```python
# src/infrastructure/cache/providers/new_provider/new_provider.py
from src.infrastructure.cache.providers.base import BaseCacheProvider

class NewCacheProvider(BaseCacheProvider):
    """新缓存提供者"""
    
    async def get(self, key: str) -> Any:
        # 实现获取逻辑
        pass
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        # 实现设置逻辑
        pass
```

#### 3. 注册提供者

```python
# src/infrastructure/cache/__init__.py
from src.infrastructure.cache.providers.new_provider.new_provider import NewCacheProvider

__all__ = [
    'CacheManager',
    'MemoryCacheProvider',
    'GeminiCacheManager',
    'NewCacheProvider',  # 新增
]
```

#### 4. 编写提供者文档

```markdown
# New Cache Provider

## 概述
关于新缓存提供者的说明

## 安装依赖
pip install new-provider

## 使用示例
...

## 配置说明
...

## 性能特性
...
```

## 📊 架构对比

| 特性 | 初期设计 | 改进后设计 |
|------|--------|----------|
| 提供者组织 | 平铺 | 分类管理 |
| 可扩展性 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 依赖隔离 | ❌ | ✅ |
| 模块清晰度 | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| 维护成本 | 高 | 低 |
| 测试能力 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## 🎯 设计原则

### 1. 单一职责原则 (SRP)
- Core模块：通用缓存逻辑
- 各提供者：特定存储实现
- Utils模块：辅助工具函数

### 2. 开闭原则 (OCP)
- 对扩展开放：易于添加新提供者
- 对修改关闭：现有提供者不需修改

### 3. 依赖倒置原则 (DIP)
- 依赖抽象接口 `BaseCacheProvider`
- 不依赖具体实现

### 4. 接口隔离原则 (ISP)
- 每个提供者只实现必要的方法
- 支持提供者特定的扩展方法

## 📈 可维护性考虑

### 1. 文档完整性
- 每个提供者有独立的README
- 包含使用示例和配置说明
- 性能特性和限制说明

### 2. 测试覆盖
- 核心逻辑：>90%覆盖率
- 每个提供者：>80%覆盖率
- 集成测试：关键场景覆盖

### 3. 性能监控
- 支持缓存命中率统计
- 提供者性能基准测试
- 内存使用监控

### 4. 向后兼容
- 保留旧导入路径的过渡期
- 提供迁移指南
- 逐步淘汰旧代码

## 🔗 相关文档

- [缓存系统使用指南](./cache_usage_guide.md)（待编写）
- [提供者选择指南](./cache_provider_selection.md)（待编写）
- [性能优化建议](./cache_performance.md)（待编写）

## 📝 总结

改进后的设计：
- ✅ 清晰的模块划分
- ✅ 易于扩展新提供者
- ✅ 依赖隔离
- ✅ 更好的可维护性
- ✅ 支持多种缓存策略

这个设计为未来的缓存系统扩展奠定了坚实的基础。
