# 统一存储架构实现计划（更新版）

## 实现任务清单

基于对各模块存储需求和适配器必要性的详细分析，更新实现计划以反映最新的设计决策。

### 1. 创建统一存储基础设施

- [ ] 1.1 创建统一存储领域接口
  - 创建 `src/domain/storage/interfaces.py` 文件
  - 实现 `IUnifiedStorage` 接口，定义所有存储操作方法
  - 实现 `IStorageFactory` 接口，定义存储工厂方法
  - 添加适当的类型注解和文档字符串
  - 参考需求：1.1, 1.2, 1.3

- [ ] 1.2 创建统一存储领域模型
  - 创建 `src/domain/storage/models.py` 文件
  - 实现 `StorageData` 模型，定义统一数据结构
  - 添加数据验证和序列化支持
  - 参考需求：1.1, 1.3

- [ ] 1.3 创建统一存储领域异常
  - 创建 `src/domain/storage/exceptions.py` 文件
  - 实现存储异常层次结构
  - 添加适当的错误代码和消息
  - 参考需求：1.5

- [ ] 1.4 创建基础存储实现
  - 创建 `src/infrastructure/storage/base_storage.py` 文件
  - 实现 `BaseStorage` 基类，提供通用存储功能
  - 集成序列化、时间管理、元数据管理和缓存组件
  - 添加性能监控支持
  - 参考需求：1.1, 6.1, 6.2

### 2. 实现存储后端

- [ ] 2.1 实现内存存储
  - 创建 `src/infrastructure/storage/memory/memory_storage.py` 文件
  - 实现 `MemoryStorage` 类，继承自 `BaseStorage`
  - 添加线程安全支持（使用 asyncio.Lock）
  - 实现所有 `IUnifiedStorage` 接口方法
  - 参考需求：2.1, 4.1, 4.2

- [ ] 2.2 创建内存存储配置
  - 创建 `src/infrastructure/storage/memory/memory_config.py` 文件
  - 实现内存存储配置类
  - 添加配置验证和默认值
  - 参考需求：2.4

- [ ] 2.3 实现SQLite存储
  - 创建 `src/infrastructure/storage/sqlite/sqlite_storage.py` 文件
  - 实现 `SQLiteStorage` 类，继承自 `BaseStorage`
  - 添加连接池管理和事务支持
  - 实现数据库表初始化和迁移机制
  - 参考需求：2.2, 4.3, 4.4

- [ ] 2.4 创建SQLite存储配置
  - 创建 `src/infrastructure/storage/sqlite/sqlite_config.py` 文件
  - 实现SQLite存储配置类
  - 添加数据库路径和连接参数配置
  - 参考需求：2.4

- [ ] 2.5 实现文件存储
  - 创建 `src/infrastructure/storage/file/file_storage.py` 文件
  - 实现 `FileStorage` 类，继承自 `BaseStorage`
  - 添加文件系统操作和目录管理
  - 实现数据序列化和文件锁定
  - 参考需求：2.3

- [ ] 2.6 创建文件存储配置
  - 创建 `src/infrastructure/storage/file/file_config.py` 文件
  - 实现文件存储配置类
  - 添加文件路径和格式配置
  - 参考需求：2.4

### 3. 实现存储工厂和注册表

- [ ] 3.1 实现存储工厂
  - 创建 `src/infrastructure/storage/factory.py` 文件
  - 实现 `StorageFactory` 类，实现 `IStorageFactory` 接口
  - 添加存储类型注册和创建逻辑
  - 支持配置驱动的存储创建
  - 参考需求：1.2, 2.4, 9.4

- [ ] 3.2 实现存储注册表
  - 创建 `src/infrastructure/storage/registry.py` 文件
  - 实现存储类型注册表
  - 添加动态注册和发现机制
  - 支持插件式存储扩展
  - 参考需求：9.1, 9.2

### 4. 实现存储适配器（基于详细分析）

- [ ] 4.1 实现Session存储适配器（简化实现）
  - 创建 `src/infrastructure/storage/adapters/session_adapter.py` 文件
  - 实现 `SessionStorageAdapter` 类，直接使用统一存储接口
  - 处理会话元数据的格式转换
  - 添加批量操作支持
  - 参考需求：3.1, 3.6

- [ ] 4.2 实现Thread统一存储适配器（合并实现）
  - 创建 `src/infrastructure/storage/adapters/thread_adapter.py` 文件
  - 实现 `ThreadUnifiedAdapter` 类，合并Thread、Branch、Snapshot存储
  - 处理复杂的关系查询和事务操作
  - 添加复合查询方法（get_thread_with_branches等）
  - 参考需求：3.2, 3.6

- [ ] 4.3 实现History存储适配器（完整实现）
  - 创建 `src/infrastructure/storage/adapters/history_adapter.py` 文件
  - 实现 `HistoryStore` 类，提供完整的历史记录功能
  - 处理多种记录类型的存储和统计查询
  - 添加数据管理和归档功能
  - 参考需求：3.3, 3.6

- [ ] 4.4 实现Checkpoint存储适配器（独立实现）
  - 创建 `src/infrastructure/storage/adapters/checkpoint_adapter.py` 文件
  - 实现 `CheckpointStore` 类，完全独立于LangGraph
  - 处理复杂的状态序列化和压缩
  - 添加版本管理和维护功能
  - 参考需求：3.4, 3.6

### 5. 重构现有存储实现

- [ ] 5.1 重构检查点存储实现
  - 修改 `src/infrastructure/checkpoint/memory_store.py` 文件
  - 完全移除LangGraph依赖，使用新的CheckpointStore
  - 保持现有API兼容性
  - 添加迁移支持
  - 参考需求：7.1, 7.2

- [ ] 5.2 重构SQLite检查点存储
  - 修改 `src/infrastructure/checkpoint/sqlite_store.py` 文件
  - 完全移除LangGraph依赖，使用新的CheckpointStore
  - 保持现有API兼容性
  - 添加迁移支持
  - 参考需求：7.1, 7.2

- [ ] 5.3 合并Thread存储实现
  - 删除 `src/infrastructure/threads/branch_store.py` 文件
  - 删除 `src/infrastructure/threads/snapshot_store.py` 文件
  - 删除 `src/infrastructure/threads/metadata_store.py` 文件
  - 使用新的ThreadUnifiedAdapter替代
  - 参考需求：7.1, 7.2

- [ ] 5.4 重构历史存储实现
  - 修改 `src/infrastructure/history/token_tracker.py` 文件
  - 使用新的HistoryStore替代
  - 实现缺失的存储功能
  - 参考需求：7.1, 7.2

### 6. 实现存储应用服务

- [ ] 6.1 创建存储服务
  - 创建 `src/application/storage/storage_service.py` 文件
  - 实现 `StorageService` 类，提供高级存储操作
  - 添加数据验证和转换逻辑
  - 实现批量操作和事务支持
  - 参考需求：4.2, 4.3

- [ ] 6.2 创建迁移服务
  - 创建 `src/application/storage/migration_service.py` 文件
  - 实现 `MigrationService` 类，处理数据迁移
  - 添加从旧格式到新格式的转换逻辑
  - 实现增量迁移和回滚机制
  - 参考需求：7.1, 7.3, 7.4, 7.5

- [ ] 6.3 创建配置服务
  - 创建 `src/application/storage/config_service.py` 文件
  - 实现 `StorageConfigService` 类，管理存储配置
  - 添加配置验证和热重载支持
  - 实现环境特定的配置覆盖
  - 参考需求：2.4, 9.4

### 7. 更新依赖注入配置

- [ ] 7.1 创建存储模块配置
  - 创建 `src/infrastructure/storage/di_config.py` 文件
  - 实现存储服务的依赖注入配置
  - 添加存储工厂和适配器的注册
  - 支持环境特定的存储配置
  - 参考需求：1.2, 2.4

- [ ] 7.2 更新领域配置
  - 修改 `src/domain/di/domain_config.py` 文件
  - 更新存储相关的领域服务注册
  - 添加新的存储接口绑定
  - 参考需求：1.2

- [ ] 7.3 更新应用配置
  - 修改 `src/application/di/application_config.py` 文件
  - 更新应用层的存储服务注册
  - 添加存储应用服务的绑定
  - 参考需求：1.2

### 8. 实现LangGraph兼容层

- [ ] 8.1 重构LangGraph适配器
  - 修改 `src/infrastructure/langgraph/adapter.py` 文件
  - 将LangGraph适配器重构为兼容层
  - 使用新的CheckpointStore作为底层存储
  - 保持LangGraph API兼容性
  - 参考需求：7.2

- [ ] 8.2 创建LangGraph存储桥接
  - 创建 `src/infrastructure/langgraph/storage_bridge.py` 文件
  - 实现LangGraph checkpoint与统一存储的桥接
  - 处理LangGraph特定的数据格式转换
  - 参考需求：7.2

### 9. 实现测试套件

- [ ] 9.1 创建单元测试
  - 创建 `tests/infrastructure/storage/test_base_storage.py` 文件
  - 测试基础存储实现的所有功能
  - 使用pytest和pytest-asyncio进行异步测试
  - 参考需求：8.1, 8.2

- [ ] 9.2 创建存储实现测试
  - 创建 `tests/infrastructure/storage/memory/test_memory_storage.py` 文件
  - 创建 `tests/infrastructure/storage/sqlite/test_sqlite_storage.py` 文件
  - 创建 `tests/infrastructure/storage/file/test_file_storage.py` 文件
  - 测试各种存储实现的功能和性能
  - 参考需求：8.1, 8.2

- [ ] 9.3 创建适配器测试
  - 创建 `tests/infrastructure/storage/adapters/test_session_adapter.py` 文件
  - 创建 `tests/infrastructure/storage/adapters/test_thread_adapter.py` 文件
  - 创建 `tests/infrastructure/storage/adapters/test_history_adapter.py` 文件
  - 创建 `tests/infrastructure/storage/adapters/test_checkpoint_adapter.py` 文件
  - 测试适配器的正确性和兼容性
  - 参考需求：8.1, 8.2

- [ ] 9.4 创建集成测试
  - 创建 `tests/integration/test_unified_storage.py` 文件
  - 测试整个存储架构的集成
  - 测试多工作流并发场景
  - 测试数据迁移和兼容性
  - 参考需求：5.1, 5.2, 5.3, 5.4, 5.5

- [ ] 9.5 创建性能测试
  - 创建 `tests/performance/test_storage_performance.py` 文件
  - 测试各种存储实现的性能特征
  - 使用pytest-benchmark进行基准测试
  - 测试并发和批量操作性能
  - 参考需求：6.1, 6.2, 6.3

### 10. 实现监控和日志

- [ ] 10.1 添加存储监控
  - 修改 `src/infrastructure/storage/base_storage.py` 文件
  - 集成性能监控组件
  - 添加操作延迟、吞吐量和错误率监控
  - 实现资源使用监控
  - 参考需求：6.5

- [ ] 10.2 添加存储日志
  - 修改所有存储实现文件
  - 添加结构化日志记录
  - 记录操作、错误和性能数据
  - 实现审计日志功能
  - 参考需求：8.1, 8.2, 8.3, 8.4

### 11. 实现安全功能

- [ ] 11.1 添加数据加密
  - 修改 `src/infrastructure/storage/base_storage.py` 文件
  - 集成数据加密组件
  - 实现敏感数据的加密存储
  - 添加密钥管理功能
  - 参考需求：10.1, 10.5

- [ ] 11.2 添加访问控制
  - 创建 `src/infrastructure/storage/security.py` 文件
  - 实现基于角色的访问控制
  - 添加身份验证和授权机制
  - 实现访问审计功能
  - 参考需求：10.2, 10.3

### 12. 创建文档和示例

- [ ] 12.1 创建API文档
  - 创建 `docs/storage/api.md` 文件
  - 文档化所有存储接口和方法
  - 添加使用示例和最佳实践
  - 参考需求：1.1, 1.2, 1.3

- [ ] 12.2 创建迁移指南
  - 创建 `docs/storage/migration_guide.md` 文件
  - 提供从旧存储系统到新系统的迁移指南
  - 添加常见问题和解决方案
  - 参考需求：7.1, 7.2, 7.3, 7.4, 7.5

- [ ] 12.3 创建配置指南
  - 创建 `docs/storage/configuration.md` 文件
  - 提供存储配置的详细指南
  - 添加不同环境的配置示例
  - 参考需求：2.4, 9.4

### 13. 清理和优化

- [ ] 13.1 删除旧的存储实现
  - 删除不再需要的存储文件
  - 清理旧的依赖注入配置
  - 移除过时的测试文件
  - 参考需求：7.2

- [ ] 13.2 优化性能
  - 分析性能瓶颈并进行优化
  - 优化数据库查询和索引
  - 优化缓存策略和连接池配置
  - 参考需求：6.1, 6.2, 6.3, 6.4

- [ ] 13.3 代码审查和重构
  - 进行全面的代码审查
  - 重构复杂的逻辑和重复代码
  - 改进错误处理和异常管理
  - 确保代码质量和一致性
  - 参考需求：8.1, 8.2

## 实现优先级（基于详细分析）

### 第一阶段：核心基础设施（高优先级）
1. 创建统一存储基础设施（任务1.1-1.4）
2. 实现存储后端（任务2.1-2.6）
3. 实现存储工厂和注册表（任务3.1-3.2）
4. 实现Checkpoint存储适配器（任务4.4）- 完全移除LangGraph依赖
5. 实现History存储适配器（任务4.3）- 实现缺失功能

### 第二阶段：模块集成（中优先级）
1. 实现Thread统一存储适配器（任务4.2）- 合并多个存储
2. 实现Session存储适配器（任务4.1）- 简化实现
3. 重构现有存储实现（任务5.1-5.4）
4. 实现存储应用服务（任务6.1-6.3）
5. 更新依赖注入配置（任务7.1-7.3）

### 第三阶段：兼容性和优化（低优先级）
1. 实现LangGraph兼容层（任务8.1-8.2）
2. 实现测试套件（任务9.1-9.5）
3. 实现监控和日志（任务10.1-10.2）
4. 实现安全功能（任务11.1-11.2）
5. 创建文档和示例（任务12.1-12.3）
6. 清理和优化（任务13.1-13.3）

## 关键决策说明

1. **Checkpoint模块优先级最高**：因为需要完全移除LangGraph依赖，这是最关键和最复杂的任务
2. **History模块次之**：因为目前缺少实现，需要从零开始构建完整功能
3. **Thread模块合并**：将多个分散的存储合并为一个统一适配器，简化架构
4. **Session模块简化**：因为需求相对简单，可以直接使用统一存储接口

这种优先级安排确保了最关键的功能（移除LangGraph依赖和实现缺失功能）优先完成，同时保持了系统的稳定性和向后兼容性。