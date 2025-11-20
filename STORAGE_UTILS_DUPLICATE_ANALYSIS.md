# Storage Utils 重复实现分析

## 总体结论
**✅ 发现严重的功能重复** - 主要在以下几个方面：

---

## 1. 数据压缩功能的重复

### 问题位置
- **common_utils.py** (L26-70): `compress_data()` / `decompress_data()`
- **src/core/state/base.py** (L77-81): `compress_data()` / `decompress_data()`

### 对比分析

| 功能 | common_utils | core/state/base |
|------|-------------|-----------------|
| **压缩算法** | gzip | zlib |
| **输入格式** | Dict → JSON → 压缩 | bytes → 直接压缩 |
| **使用方式** | 静态方法 | 实例方法 |
| **配置** | 无 | 可配置enable/disable |
| **集成** | 本地使用 | 系统级集成 |

### 问题
- **两套实现使用不同的算法**（gzip vs zlib）
- **不一致的压缩参数**
- **无法互相兼容**
- **违反单一职责原则**

### 建议
1. 统一使用 `src/core/state/base.py` 的实现（已是系统级）
2. **删除** `common_utils.py` 中的 `compress_data()` / `decompress_data()`
3. 在 adapters 层创建适配器调用 core 层的序列化器

---

## 2. 数据序列化功能的重复

### 问题位置
- **common_utils.py** (L73-103): `serialize_data()` / `deserialize_data()`
- **src/core/state/base.py** (L28-76): `serialize()` / `deserialize()`

### 对比分析

| 功能 | common_utils | core/state/base |
|------|-------------|-----------------|
| **输入** | Dict | bytes |
| **输出** | JSON 字符串 | bytes |
| **压缩集成** | 无 | 有 |
| **类型检查** | 简单 | 完整 |
| **错误处理** | StorageError | 自定义异常 |

### 问题
- **序列化流程被分割**
- `common_utils` 处理数据⇄字符串
- `base.py` 处理字符串⇄字节+压缩
- **调用链不清晰**

### 建议
1. `common_utils` 应该**删除序列化方法**
2. 创建 **serializer 适配器** 包装 `core/state/base.py`
3. 统一使用 core 层的序列化器

---

## 3. 过滤器匹配逻辑的重复

### 问题位置
- **common_utils.py** (L119-157): `matches_filters()` - 内存/文件存储用
- **sqlite_utils.py** (L109-160): `build_where_clause()` - SQLite 用

### 对比分析

#### common_utils.matches_filters()
```python
支持的操作符:
- $eq   (相等)
- $ne   (不等)
- $in   (包含)
- $nin  (不包含)
- $gt   (大于)
- $gte  (大于等于)
- $lt   (小于)
- $lte  (小于等于)
```

#### sqlite_utils.build_where_clause()
```python
支持的操作符:
- $gt, $lt, $gte, $lte (比较)
- $ne (不等)
- $in (包含)
- $like (模糊匹配)
- 直接相等
```

### 问题
- **操作符定义重复**
- **验证逻辑不统一**
- **$in 等高级操作符没有在两处同时实现**
- **难以扩展新操作符**

### 代码示例 - 冗余
```python
# common_utils.py - 内存检查
if "$eq" in value and data[key] != value["$eq"]:
    return False
elif "$ne" in value and data[key] == value["$ne"]:
    return False

# sqlite_utils.py - SQL生成
elif isinstance(value, dict) and "$ne" in value:
    conditions.append(f"{key} != ?")
    params.append(value["$ne"])
```

### 建议
1. 创建 **统一的 FilterOperator** 枚举在 core 层
2. 创建 **FilterBuilder** 基类定义通用验证逻辑
3. 不同存储后端继承并实现对应操作
   - `MemoryFilterBuilder` 
   - `SQLiteFilterBuilder`
   - `FileFilterBuilder`

---

## 4. 过期数据清理逻辑的重复

### 问题位置
- **common_utils.py** (L160-177): `is_data_expired()` / `calculate_cutoff_time()`
- **file_utils.py** (L405-430): `cleanup_expired_files()`
- **sqlite_utils.py** (L234-249): `cleanup_expired_records()`

### 对比分析

```python
# common_utils - 底层判断
def is_data_expired(data, current_time=None):
    expires_at = data.get("expires_at")
    return expires_at and expires_at < current_time

# file_utils - 文件清理
def cleanup_expired_files(dir_path, current_time):
    for file_path in list_files:
        data = load_data_from_file(file_path)
        if data and data["expires_at"] < current_time:
            delete_file(file_path)

# sqlite_utils - 数据库清理
def cleanup_expired_records(conn):
    query = "DELETE FROM state_storage WHERE expires_at < ?"
    execute_update(conn, query, [time.time()])
```

### 问题
- **过期检查逻辑在三个地方**
- **清理策略无法统一管理**
- **难以改变过期判断规则**
- **时间获取方式不一致**

### 建议
1. 创建 **ExpirationPolicy** 接口在 core 层
2. 创建 **ExpirationChecker** 单一逻辑源
3. 各存储适配器调用该检查器

---

## 5. 备份/恢复功能的重复

### 问题位置
- **common_utils.py** (L223-264): `cleanup_old_backups()`
- **file_utils.py** (L460-505): `backup_directory()` / `restore_directory()`
- **sqlite_utils.py** (L307-348): `backup_database()` / `restore_database()`

### 问题
- **三套独立的备份实现**
- **没有统一的备份策略接口**
- **无法跨存储类型管理备份**
- **清理旧备份的逻辑分散**

### 建议
1. 创建 **BackupStrategy** 接口
2. 各存储类型实现具体策略
3. 统一备份管理器协调

---

## 6. 元数据管理的重复

### 问题位置
- **common_utils.py** (L267-299):
  - `validate_data_id()` 
  - `add_metadata_timestamps()`
- **memory_utils.py** (L164-184):
  - `prepare_persistence_data()` - 构建元数据

### 问题
- **元数据字段定义不统一**
  - `created_at`, `updated_at`, `expires_at`
  - vs `access_count`, `last_accessed`, `size`
- **TTL/过期时间的计算分散**
- **ID生成逻辑有重复**

### 建议
1. 创建 **StorageMetadata** 模型
2. 创建 **MetadataManager** 统一管理
3. 定义标准的元数据字段集合

---

## 7. 健康检查和统计信息的重复

### 问题位置
- **common_utils.py** (L302-328): `prepare_health_check_response()`
- **sqlite_utils.py** (L417-521):
  - `get_database_stats()`
  - `get_database_info()`
- **file_utils.py** (L507-534): `get_storage_info()`

### 问题
- **每个存储类型有自己的统计方法**
- **响应格式不统一**
- **无法跨存储类型收集统计信息**

### 建议
1. 创建 **StorageStatistics** 数据类
2. 创建 **StatisticsCollector** 接口
3. 统一的健康检查端点

---

## 8. 目录操作工具的重复

### 问题位置
- **common_utils.py** (L195-202): `ensure_directory_exists()`
- **file_utils.py** (L95-151): 
  - `list_files_in_directory()`
  - `calculate_directory_size()`
  - `count_files_in_directory()`
  - `validate_directory_structure()`
- **sqlite_utils.py** (L27-43): 在 `create_connection()` 中重复创建目录

### 问题
- **`ensure_directory_exists()` 在两处调用**
- **目录操作逻辑不集中**
- **可能的权限问题处理不一致**

### 建议
1. 创建 **DirectoryManager** 工具类
2. 集中所有目录操作
3. 统一错误处理和日志

---

## 总体架构问题

```
❌ 当前结构（问题）:
common_utils
├─ compress/decompress
├─ serialize/deserialize  
├─ filter_matching
├─ expiration_check
├─ metadata_handling
└─ health_check

├─ file_utils
│  ├─ file_operations
│  ├─ cleanup_expired_files [重复]
│  ├─ backup_directory [重复]
│  └─ storage_info [重复]

├─ sqlite_utils
│  ├─ database_operations
│  ├─ build_where_clause [重复]
│  ├─ cleanup_expired_records [重复]
│  ├─ backup_database [重复]
│  └─ database_stats [重复]

└─ memory_utils
   ├─ persistence_operations
   ├─ memory_calculation
   └─ prepare_persistence_data [重复]
```

```
✅ 建议结构：
src/core/state/
├─ serializers/
│  ├─ base_serializer.py          [已有]
│  └─ compression_policy.py       [新建]
├─ filters/
│  ├─ filter_operator.py          [新建 - 枚举]
│  ├─ filter_builder.py           [新建 - 基类]
│  └─ implementations/
│     ├─ memory_filter_builder.py
│     ├─ sqlite_filter_builder.py
│     └─ file_filter_builder.py
├─ policies/
│  ├─ expiration_policy.py        [新建]
│  ├─ backup_policy.py            [新建]
│  └─ metadata_policy.py          [新建]
└─ statistics/
   ├─ storage_statistics.py       [新建]
   └─ statistics_collector.py     [新建]

src/adapters/storage/utils/
├─ common_utils.py               [精简版]
├─ file_utils.py                [移除重复]
├─ memory_utils.py              [移除重复]
└─ sqlite_utils.py              [移除重复]
```

---

## 优先级修复计划

### 🔴 高优先级（影响系统一致性）
1. **统一压缩算法** - gzip vs zlib
2. **统一过滤器逻辑** - 创建 FilterBuilder 接口
3. **统一过期检查** - 创建 ExpirationPolicy

### 🟡 中优先级（代码质量）
1. **统一备份策略** - 创建 BackupStrategy
2. **统一统计信息** - 创建 StorageStatistics
3. **统一序列化** - 删除 utils 中的重复

### 🟢 低优先级（可以逐步改进）
1. **元数据管理** - 创建 MetadataManager
2. **目录操作** - 创建 DirectoryManager

---

## 具体修改建议

### 步骤1: 删除 common_utils.py 中的冗余方法
```python
# ❌ 删除这些（core/state/base.py 已有）:
- compress_data()
- decompress_data()
- serialize_data()
- deserialize_data()

# ✅ 保留这些（adapters 特定）:
- matches_filters()  → 将被新的 FilterBuilder 替换
- is_data_expired()  → 将被新的 ExpirationPolicy 替换
- ensure_directory_exists()  → 迁移到 DirectoryManager
- add_metadata_timestamps()  → 保留，作为辅助函数
- generate_timestamp_filename()  → 保留
- prepare_health_check_response()  → 保留
```

### 步骤2: 在 core 层创建新接口

**src/core/state/filters.py**
```python
from enum import Enum
from typing import Dict, Any, Protocol

class FilterOperator(Enum):
    EQ = "$eq"
    NE = "$ne"
    IN = "$in"
    NIN = "$nin"
    GT = "$gt"
    GTE = "$gte"
    LT = "$lt"
    LTE = "$lte"
    LIKE = "$like"

class FilterBuilder(Protocol):
    """过滤器构建器基类"""
    
    def validate_operators(self, filters: Dict[str, Any]) -> bool:
        """验证操作符"""
        ...
    
    def matches(self, data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器"""
        ...
```

**src/core/state/expiration.py**
```python
from typing import Dict, Any, Optional

class ExpirationPolicy:
    """过期策略"""
    
    @staticmethod
    def is_expired(data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """统一的过期检查"""
        ...
    
    @staticmethod
    def calculate_cutoff_time(retention_days: int, current_time: Optional[float] = None) -> float:
        """统一的截止时间计算"""
        ...
```

### 步骤3: 更新 adapters 中的 utils
```python
# file_utils.py
from src.core.state.filters import FilterBuilder
from src.core.state.expiration import ExpirationPolicy

class FileStorageUtils:
    @staticmethod
    def cleanup_expired_files(dir_path: str, current_time: float) -> int:
        # 使用 ExpirationPolicy.is_expired() 而不是重复实现
        ...
```

---

## 预期改进

| 指标 | 当前 | 改进后 |
|------|------|--------|
| 代码重复度 | 高 | 低 |
| 维护成本 | 高（6+个位置） | 低（1个位置） |
| 一致性 | 低（多种实现） | 高（单一源） |
| 可测试性 | 困难 | 容易 |
| 可扩展性 | 困难 | 容易 |

---

## 相关文件映射

```
修改影响范围:
- src/adapters/storage/utils/common_utils.py       [删除4个方法]
- src/adapters/storage/utils/file_utils.py         [删除3个方法，调用新接口]
- src/adapters/storage/utils/sqlite_utils.py       [删除2个方法，调用新接口]
- src/adapters/storage/utils/memory_utils.py       [删除1个方法]

新创建:
- src/core/state/filters.py                        [新建]
- src/core/state/expiration.py                     [新建]
- src/core/state/backup_policy.py                  [新建]
- src/core/state/statistics.py                     [新建]
- src/adapters/storage/builders/              [新建目录]
  ├─ memory_filter_builder.py
  ├─ sqlite_filter_builder.py
  └─ file_filter_builder.py
```
