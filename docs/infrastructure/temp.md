## `src/infrastructure` 目录功能分析及与 Core 层重复功能对比

### `src/infrastructure` 目录已实现的功能

1. **缓存系统 (`src/infrastructure/cache/`)**
   - 通用缓存管理器 (`CacheManager`)：提供基础的缓存功能，支持客户端和服务器端缓存策略
   - LLM专用缓存管理器 (`LLMCacheManager`)：为LLM请求提供专门的缓存管理
   - 缓存键生成器：为不同类型的消息和请求生成缓存键
   - 内存缓存提供者：基于内存的缓存实现
   - 服务器端缓存提供者接口及实现（如Gemini服务器端缓存）
   - 缓存配置模型：定义缓存行为的配置

2. **消息系统 (`src/infrastructure/messages/`)**
   - 消息类型定义：`HumanMessage`, `AIMessage`, `SystemMessage`, `ToolMessage`等
   - 消息转换器：在不同消息格式之间进行转换
   - 消息工厂：创建消息实例
   - 消息基类：定义消息的基本结构和行为

3. **工具系统 (`src/infrastructure/tools/`)**
   - 工具格式化器：处理工具的输入输出格式

4. **LLM模块 (`src/infrastructure/llm/`)**
   - 消息模型：定义LLM交互的消息格式
   - 消息转换器：在不同消息格式间转换
   - LLM模型：定义LLM交互的数据结构

### Core层与Infrastructure层重复的功能

1. **缓存功能重复**
   - `src/core/common/cache.py`：核心层的通用缓存实现，提供基于 `cachetools` 的缓存功能，包括 `CacheManager`、`CacheEntry`、`CacheStats` 等
   - `src/core/llm/cache/`：LLM专用的缓存系统，但根据 `__init__.py` 文件的注释，这个模块已迁移到 `src/infrastructure/cache/`，当前仅作为向后兼容层保留
   - `src/infrastructure/cache/`：完整的缓存系统实现，包括通用缓存和LLM专用缓存

2. **消息转换功能重复**
   - `src/core/llm/utils/message_converters.py`：核心层的消息转换器，但依赖 `src/infrastructure/messages` 和 `src/infrastructure/llm/models`
   - `src/infrastructure/messages/converters.py`：基础设施层的消息转换器实现

### 分析结论

1. **架构迁移**：根据 `src/core/llm/cache/__init__.py` 文件中的注释，缓存系统已经从 `core` 层迁移到 `infrastructure` 层，原 `core` 层的缓存模块现在仅作为向后兼容层保留。

2. **依赖关系**：核心层的消息转换器 (`src/core/llm/utils/message_converters.py`) 实际上依赖于基础设施层的消息定义和转换器，这表明基础设施层的消息系统是主要实现。

3. **职责划分**：
   - `infrastructure` 层：包含具体的实现和基础设施组件
   - `core` 层：包含领域逻辑和对基础设施层的抽象封装

4. **重复功能**：尽管有架构迁移，但仍然存在一些重复的功能定义，特别是缓存相关的功能，其中 `core` 层保留了向后兼容的接口，而实际实现在 `infrastructure` 层。

### 建议

1. 完成缓存系统的完全迁移，移除 `core` 层中已废弃的缓存实现，只保留 `infrastructure` 层的实现
2. 明确消息系统的依赖关系，确保所有消息转换功能都统一在 `infrastructure` 层实现
3. 考虑将 `core` 层的 `src/core/llm/utils/message_converters.py` 转换为对 `infrastructure` 层消息转换器的适配器，而不是直接实现转换逻辑