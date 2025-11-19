基于我对这些存储后端文件的分析，我来详细分析哪些应该作为基类，哪些静态方法应该作为工具类：

## 分析结果

### 1. 基类分析

**现有的基类结构已经很合理：**

- [`BaseStorageBackend`](src/adapters/storage/base.py:263) - 存储后端基类，包含通用统计信息更新、过滤器匹配等通用功能
- [`BaseStateStorageAdapter`](src/adapters/storage/base.py:18) - 状态存储适配器基类，提供同步接口包装异步后端方法

**应该作为基类的部分：**

1. **连接管理基类** - 三个后端都有类似的连接池管理逻辑，可以提取为基类
2. **清理任务基类** - 都有TTL清理和备份任务的共同模式
3. **统计信息基类** - 都有类似的统计信息收集逻辑

### 2. 工具类分析

**现有的工具类结构良好：**

- [`MemoryStorageUtils`](src/adapters/storage/memory_utils.py:16) - 内存存储工具类
- [`SQLiteStorageUtils`](src/adapters/storage/sqlite_utils.py:20) - SQLite存储工具类  
- [`FileStorageUtils`](src/adapters/storage/file_utils.py:21) - 文件存储工具类

**应该提取为工具类的静态方法：**

#### 从后端类中提取的通用工具方法：

1. **数据压缩/解压缩工具方法**：
   - 三个后端都有类似的压缩逻辑，可以提取到通用的 `CompressionUtils`

2. **过滤器匹配工具方法**：
   - [`BaseStorageBackend._matches_filters`](src/adapters/storage/base.py:298) 已经是基类方法，很好

3. **容量验证工具方法**：
   - [`MemoryStorageUtils.validate_capacity`](src/adapters/storage/memory_utils.py:229) 已经是工具类方法

4. **时间戳和TTL处理工具方法**：
   - 各后端都有类似的过期时间处理逻辑

#### 具体应该移动的静态方法：

**从 MemoryStorageBackend 移动到 MemoryStorageUtils：**
- 压缩相关的逻辑已经在工具类中
- 持久化数据准备和恢复逻辑已经在工具类中

**从 SQLiteStorageBackend 移动到 SQLiteStorageUtils：**
- 连接配置逻辑 `_configure_connection` 应该移动到工具类
- 数据库信息获取逻辑已经在工具类中

**从 FileStorageBackend 移动到 FileStorageUtils：**
- 目录结构相关的路径计算逻辑应该移动到工具类
- 容量检查逻辑应该移动到工具类

### 3. 架构建议

**当前架构的优点：**
- 已经很好地分离了基类和工具类
- 每个存储类型都有专门的工具类
- 基类提供了良好的通用功能

**可以改进的地方：**

1. **提取通用工具类**：
   - 创建 `StorageCommonUtils` 包含跨存储类型的通用工具方法
   - 如：压缩/解压缩、序列化/反序列化、时间戳处理等

2. **优化基类层次**：
   - 可以考虑创建 `AsyncStorageBackend` 和 `SyncStorageBackend` 中间基类
   - 提取连接管理、任务调度等通用模式

3. **工具类方法标准化**：
   - 确保相似功能在工具类中有统一的接口
   - 如：所有存储类型的压缩方法应该有相同的签名

### 4. 总结

现有的架构已经很合理，主要的后端逻辑应该保持在具体的后端类中，而：
- **数据处理、压缩、序列化等辅助功能** → 工具类
- **连接管理、任务调度、统计收集等通用模式** → 基类
- **特定存储类型的核心业务逻辑** → 具体后端类

这种分离方式保持了代码的清晰性和可维护性，符合框架的扁平化架构原则。