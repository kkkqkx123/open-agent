# 缓存键生成器统一迁移

## 迁移完成日期
2025-12-05

## 概述
完成了缓存键生成器的统一化重构，将多个分散的实现合并为单一的规范实现。

## 变更内容

### 1. 核心合并
- **目标文件**: `src/infrastructure/cache/core/key_generator.py`
- **合并来源**: `src/infrastructure/cache/cache_key_generator.py`
- **核心类**:
  - `DefaultCacheKeyGenerator` - 实现 `ICacheKeyGenerator` 接口
  - `BaseKeySerializer` - 序列化工具

### 2. 新增功能

在 `DefaultCacheKeyGenerator` 中添加了8个专用方法：

| 方法 | 功能 | 参数 |
|------|------|------|
| `generate_content_key()` | 基于内容的哈希 | content, salt, algorithm |
| `generate_params_key()` | 基于参数的哈希 | params, salt, algorithm |
| `generate_layered_key()` | 分层键生成 | prefix, identifier, layer, algorithm |
| `generate_versioned_key()` | 版本化键生成 | base_key, version |
| `generate_composite_key()` | 组合键生成 | components, separator, algorithm |
| `generate_reference_key()` | 提示词引用键 | prompt_ref, variables, context, algorithm |
| `generate_node_key()` | 节点配置键 | node_id, config, state_data, algorithm |
| `validate_cache_key()` | 验证缓存键 | key |
| `parse_cache_key()` | 解析缓存键 | key |
| `generate_key_stats()` | 统计缓存键 | keys |

### 3. 算法支持

支持多种哈希算法：
- **SHA256** (默认): 生产环境推荐，安全性高
- **MD5**: 保留用于兼容性

### 4. 导入迁移

#### 旧导入 (已弃用)
```python
from src.core.common.utils.cache_key_generator import CacheKeyGenerator
from src.infrastructure.cache.cache_key_generator import CacheKeyGenerator
```

#### 新导入 (推荐)
```python
# 方式1：直接导入实现类
from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator

# 方式2：通过别名保持兼容性
from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator as CacheKeyGenerator

# 方式3：通过 __init__ 导入
from src.infrastructure.cache.core import DefaultCacheKeyGenerator
```

### 5. 文件变更

| 文件 | 状态 | 说明 |
|------|------|------|
| `src/infrastructure/cache/core/key_generator.py` | ✅ 修改 | 合并所有功能 |
| `src/infrastructure/cache/cache_key_generator.py` | ⚠️ 重定向 | 现为兼容性别名模块 |
| `src/infrastructure/cache/core/__init__.py` | ✅ 修改 | 导出更新 |
| `src/infrastructure/cache/__init__.py` | ✅ 保持 | 无需修改 |
| `src/services/prompts/cache_manager.py` | ✅ 修改 | 更新导入 |
| `src/services/llm/utils/config_extractor.py` | ✅ 修改 | 更新导入 |
| `src/infrastructure/common/cache.py` | ✅ 修改 | 更新导入 |
| `src/core/workflow/graph/nodes/llm_node.py` | ✅ 修改 | 更新导入 |

### 6. 改进

#### 日志记录
- 添加完整的日志支持，记录所有生成和验证操作
- 提供了详细的错误信息和回退机制

#### 错误处理
- 完整的异常处理和回退机制
- 所有方法都有充分的文档说明
- 参数验证和类型检查

#### 性能优化
- 参数规范化，防止栈溢出 (`MAX_RECURSION_DEPTH = 50`)
- JSON 序列化缓存
- 哈希计算优化

## 向后兼容性

已通过别名模块 `src/infrastructure/cache/cache_key_generator.py` 提供向后兼容性：

```python
# 旧代码仍然可以工作
from src.infrastructure.cache.cache_key_generator import CacheKeyGenerator
# 内部已重定向到新实现
```

## 架构对齐

本次迁移符合框架分层架构：
- **Infrastructure Layer**: 缓存键生成实现（`src/infrastructure/cache/core/key_generator.py`）
- **Interface Layer**: 缓存接口定义（`src/interfaces/llm/cache.py`）
- **Service Layer**: 缓存管理服务
- **Adapter Layer**: 缓存适配器

## 验证步骤

✅ 类型检查: 通过 mypy 验证
✅ 导入检查: 所有导入已更新
✅ 代码审查: 所有修改已验证

## 迁移指南

### 如果您的代码导入了旧路径
1. **立即**: 代码继续工作（向后兼容）
2. **逐步**: 更新导入到新路径
3. **新代码**: 直接使用新路径

### 推荐的导入方式
```python
# 推荐：从 core 模块直接导入
from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator

# 或通过 __init__ 导入
from src.infrastructure.cache.core import DefaultCacheKeyGenerator

# 需要别名时
from src.infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator as CacheKeyGenerator
```

## 后续改进

可考虑的后续优化：
1. 将 `src/core/common/cache.py` 统一迁移到 infrastructure 层
2. 添加更多的缓存策略（LRU, LFU 等）
3. 缓存键的加密支持
4. 缓存键的统计分析功能增强
