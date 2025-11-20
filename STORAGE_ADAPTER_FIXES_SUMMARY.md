# 存储适配器类型错误修复总结

## 问题分析

在 `/src/adapters/storage/` 目录中发现了多个相关的类型错误，原因是代码试图调用已经移到 `src/core/state/` 层或不存在的工具方法。这些方法已在架构重构中集中管理，需要更新调用方式。

## 修复的问题清单

### 1. 压缩/解压缩数据（已移至 `src/core/state/base.py`）

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `base.py:134` | `StorageCommonUtils.should_compress_data()` | 使用直接size比对 |
| `base.py:135` | `StorageCommonUtils.compress_data()` | 使用 `BaseStateSerializer(compression=True).serialize_state()` |
| `file_backend.py:150-151` | 同上 | 同上 |
| `file_backend.py:217` | `StorageCommonUtils.decompress_data()` | 使用 `BaseStateSerializer(compression=True).deserialize_state()` |
| `memory_backend.py:194` | 同上 | 同上 |
| `memory_backend.py:246` | 同上 | 同上 |

**修复代码示例：**
```python
# 旧方式（错误）
data = StorageCommonUtils.compress_data(data)

# 新方式（正确）
from src.core.state.base import BaseStateSerializer
serializer = BaseStateSerializer(compression=True)
data = serializer.serialize_state(data)
```

### 2. 健康检查响应（已移至 `src/core/state/statistics.py`）

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `file_backend.py:354` | `StorageCommonUtils.prepare_health_check_response()` | 使用 `HealthCheckHelper.prepare_health_check_response()` |
| `memory_backend.py:282` | 同上 | 同上 |
| `sqlite_backend.py:424` | 同上 | 同上 |

**修复代码示例：**
```python
# 旧方式（错误）
return StorageCommonUtils.prepare_health_check_response(
    status="healthy",
    config={...},
    stats=self._stats,
    ...
)

# 新方式（正确）
from src.core.state.statistics import FileStorageStatistics, HealthCheckHelper
stats = FileStorageStatistics(...)
return HealthCheckHelper.prepare_health_check_response(
    status="healthy",
    stats=stats,
    config={...},
    ...
)
```

### 3. 备份策略（已移至 `src/core/state/backup_policy.py`）

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `sqlite.py:423` | `SQLiteStorageUtils.backup_database()` | 使用 `DatabaseBackupStrategy().backup()` |
| `sqlite.py:450` | `SQLiteStorageUtils.restore_database()` | 使用 `DatabaseBackupStrategy().restore()` |
| `file.py:416` | `FileStorageUtils.backup_directory()` | 使用 `FileBackupStrategy().backup()` |
| `file.py:447` | `FileStorageUtils.restore_directory()` | 使用 `FileBackupStrategy().restore()` |
| `file_backend.py:436` | 同上 | 同上 |

**修复代码示例：**
```python
# 旧方式（错误）
success = FileStorageUtils.backup_directory(source, dest)

# 新方式（正确）
from src.core.state.backup_policy import FileBackupStrategy
backup_strategy = FileBackupStrategy()
success = backup_strategy.backup(source, dest)
```

### 4. 备份清理（已移至 `src/core/state/backup_policy.py`）

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `sqlite_backend.py:672` | `StorageCommonUtils.cleanup_old_backups()` | 使用 `FileBackupStrategy().cleanup_old_backups()` |
| `file_backend.py:444` | 同上 | 同上 |

**修复代码示例：**
```python
# 旧方式（错误）
StorageCommonUtils.cleanup_old_backups(backup_dir, max_files, pattern)

# 新方式（正确）
from src.core.state.backup_policy import FileBackupStrategy
backup_strategy = FileBackupStrategy()
backup_strategy.cleanup_old_backups(backup_dir, max_files)
```

### 5. 文件存储工具方法（不存在于 `FileStorageUtils`）

这些方法不存在于 `FileStorageUtils`，需要使用现有方法组合实现：

| 文件 | 问题 | 修复方式 |
|------|------|---------|
| `file_backend.py:342` | `FileStorageUtils.cleanup_expired_files()` | 使用 `list_files_in_directory()` + `get_file_modified_time()` + `delete_file()` 组合 |
| `file_backend.py:383` | `FileStorageUtils.cleanup_old_files()` | 使用同上组合 |
| `file.py:479` | `FileStorageUtils.cleanup_expired_files()` | 同上 |
| `file.py:499` | `FileStorageUtils.get_storage_info()` | 使用 `get_directory_structure_info()` + `calculate_directory_size()` + `count_files_in_directory()` |

**修复代码示例：**
```python
# 旧方式（错误）
expired_count = FileStorageUtils.cleanup_expired_files(base_path, current_time)

# 新方式（正确）
all_files = FileStorageUtils.list_files_in_directory(
    base_path,
    pattern="*.json",
    recursive=True
)
expired_count = 0
for file_path in all_files:
    modified_time = FileStorageUtils.get_file_modified_time(file_path)
    if current_time - modified_time > ttl_seconds:
        if FileStorageUtils.delete_file(file_path):
            expired_count += 1
```

## 修复文件清单

1. ✅ `/src/adapters/storage/sqlite.py`
   - 修复 `backup_database()` 第423行
   - 修复 `restore_database()` 第450行

2. ✅ `/src/adapters/storage/sqlite_backend.py`
   - 修复 `health_check_impl()` 第424行
   - 修复 `_create_backup_impl()` 第672行

3. ✅ `/src/adapters/storage/memory_backend.py`
   - 修复 `load_impl()` 第194行
   - 修复 `list_impl()` 第246行
   - 修复 `health_check_impl()` 第282行

4. ✅ `/src/adapters/storage/file.py`
   - 修复 `backup_storage()` 第416行
   - 修复 `restore_storage()` 第447行
   - 修复 `compact_storage()` 第479行
   - 修复 `get_storage_info()` 第499行

5. ✅ `/src/adapters/storage/file_backend.py`
   - 修复 `save_impl()` 第150-151行
   - 修复 `load_impl()` 第217行
   - 修复 `health_check_impl()` 第334-370行
   - 修复 `cleanup_old_data_impl()` 第379-390行
   - 修复 `_create_backup_impl()` 第436-444行

6. ✅ `/src/adapters/storage/base.py`
   - 修复 `save()` 第133-135行

## 架构依赖规则

所有修复遵循以下核心原则：

1. **序列化/压缩** → `src/core/state/base.py::BaseStateSerializer`
2. **健康检查** → `src/core/state/statistics.py::HealthCheckHelper`
3. **备份策略** → `src/core/state/backup_policy.py::BackupStrategy`
4. **文件操作** → `src/adapters/storage/utils/file_utils.py::FileStorageUtils`

## 验证

所有修复已通过 Pylance 诊断检查，无类型错误：

```bash
# 检查诊断结果
get_diagnostics /d:/项目/agent/open-agent/src/adapters/storage/
```

结果：无错误返回，表示所有问题已解决。

## 注意事项

1. **导入方式**：所有新增导入都在使用处内部进行，避免循环依赖
2. **向后兼容性**：StorageCommonUtils 仍然保留了 `serialize_data()` 和 `deserialize_data()` 等JSON级别的方法供适配器层使用
3. **异步处理**：文件清理操作在同步方法中实现，可按需转换为异步
4. **错误处理**：所有修复保留了原有的异常处理机制
