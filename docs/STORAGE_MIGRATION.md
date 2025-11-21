# 存储模块迁移总结

## 迁移完成

`src/domain/storage/` 模块已成功迁移到新的扁平化架构。

## 迁移映射

### 1. 异常（Exceptions）
**从：** `src/domain/storage/exceptions.py`
**到：** `src/core/common/exceptions.py`

所有存储异常已整合到核心通用异常模块：
- `StorageError` - 基础存储异常
- `StorageConnectionError` - 连接异常
- `StorageTransactionError` - 事务异常
- `StorageValidationError` - 验证异常
- `StorageNotFoundError` - 数据不存在异常
- `StoragePermissionError` - 权限异常
- `StorageTimeoutError` - 超时异常
- `StorageCapacityError` - 容量异常
- `StorageIntegrityError` - 完整性异常
- `StorageConfigurationError` - 配置异常
- `StorageMigrationError` - 迁移异常

辅助函数：
- `create_storage_error()` - 根据错误代码创建异常
- `EXCEPTION_MAP` - 错误代码映射字典

### 2. 接口（Interfaces）
**从：** `src/domain/storage/interfaces.py`
**到：** `src/interfaces/storage.py`

所有存储接口已移至集中式接口层：
- `IUnifiedStorage` - 统一存储接口（CRUD、查询、高级操作等）
- `IStorageFactory` - 存储工厂接口

### 3. 模型（Models）
**从：** `src/domain/storage/models.py`
**到：** `src/core/storage/models.py`

所有数据模型已移至核心存储模块：
- `DataType` - 数据类型枚举
- `StorageData` - 存储数据模型
- `StorageQuery` - 查询模型
- `StorageTransaction` - 事务模型
- `StorageStatistics` - 统计模型
- `StorageHealth` - 健康状态模型
- `StorageConfig` - 配置模型
- `StorageBatch` - 批处理模型
- `StorageMigration` - 迁移模型

## 架构位置

```
新架构位置：
├── src/interfaces/storage.py          # 接口定义（IUnifiedStorage, IStorageFactory）
├── src/core/common/exceptions.py      # 存储异常定义
├── src/core/common/__init__.py        # 通用模块导出
├── src/core/storage/
│   ├── __init__.py                    # 存储模块导出
│   └── models.py                      # 存储数据模型
├── src/adapters/storage/              # 存储适配器实现
└── src/interfaces/__init__.py         # 接口层统一导出（包含存储接口）

向后兼容性：
└── src/domain/storage/__init__.py     # 兼容性重定向（已弃用）
```

## 导入更新

### 异常导入
```python
# 旧（已弃用）
from src.domain.storage.exceptions import StorageError

# 新
from src.core.common.exceptions import StorageError
# 或
from src.core.common import StorageError
```

### 接口导入
```python
# 旧（已弃用）
from src.domain.storage.interfaces import IUnifiedStorage

# 新
from src.interfaces.storage import IUnifiedStorage
# 或
from src.interfaces import IUnifiedStorage
```

### 模型导入
```python
# 旧（已弃用）
from src.domain.storage.models import StorageData

# 新
from src.core.storage.models import StorageData
# 或
from src.core.storage import StorageData
```

## 向后兼容性

为了支持现有代码，`src/domain/storage/__init__.py` 已更新为兼容性适配层，
重定向到新位置。此文件在导入时发出 `DeprecationWarning`，并在未来版本中移除。

### 兼容性导入（将触发警告）
```python
# 这仍然可以工作，但会显示弃用警告
from src.domain.storage import StorageError, IUnifiedStorage, StorageData
```

## 迁移检查清单

- [x] 异常移至 `src/core/common/exceptions.py`
- [x] 接口移至 `src/interfaces/storage.py`
- [x] 模型移至 `src/core/storage/models.py`
- [x] 更新 `src/core/common/__init__.py` 导出异常
- [x] 更新 `src/core/storage/__init__.py` 导出模型
- [x] 更新 `src/interfaces/__init__.py` 导出存储接口
- [x] 创建向后兼容性适配层
- [x] 类型检查验证（mypy）
- [x] 文档更新

## 接下来的步骤

1. **更新所有导入语句**：逐步更新代码库中的所有导入语句，使用新位置
2. **删除旧文件**：在确认没有代码依赖后，删除以下文件：
   - `src/domain/storage/exceptions.py`
   - `src/domain/storage/interfaces.py`
   - `src/domain/storage/models.py`
3. **删除 domain 目录**：如果所有模块都已迁移，可删除整个 `src/domain/` 目录

## 版本信息

- 迁移日期：2025-11-21
- 新架构版本：Flattened (Core + Services + Adapters)
- 兼容性保证：版本 1.x 支持，版本 2.x 移除旧导入

## 相关文档

- [架构指南](./AGENTS.md) - 扁平化架构详细说明
- [存储适配器](../src/adapters/storage/) - 存储实现细节
- [类型系统](./TYPE_SYSTEM.md) - 类型检查和验证
