# Infrastructure Common 迁移计划

## 概述

本文档提供了将 `src/infrastructure/common` 目录迁移到新架构的详细方案和文件移动列表。新架构遵循 Core + Services + Adapters 的扁平化设计，其中 `src/core/common` 作为核心公共组件层。

## 现有基础设施公共组件 (`src/infrastructure/common`)

- **功能完整度**: 高，包含完整的缓存、序列化、ID生成、元数据管理、监控、存储和时间管理功能
- **架构复杂度**: 高，包含多层嵌套结构和复杂功能实现
- **文件数量**: 约20个文件，分布在多个子目录中
- **依赖关系**: 与基础设施层紧密耦合，包含大量基础设施特定实现

## 迁移目标

将 `src/infrastructure/common` 中的公共组件迁移到 `src/core/common`，整合现有功能并消除重复实现。

## 文件迁移总览

| 原文件路径 | 新文件路径 | 迁移类型 | 优先级 | 说明 |
|------------|------------|----------|---------|------|
| `interfaces.py` | `src/core/common/interfaces.py` | 移动 | 高 | 基础接口定义，需要整合到核心接口 |
| `cache/cache_manager.py` | `src/core/common/cache.py` | 整合 | 高 | 统一缓存管理器，与现有缓存系统整合 |
| `cache/cache_entry.py` | `src/core/common/cache.py` | 整合 | 高 | 缓存条目定义，合并到缓存模块 |
| `serialization/serializer.py` | `src/core/common/serialization.py` | 移动 | 高 | 功能丰富的序列化器 |
| `serialization/state_serializer.py` | `src/core/common/serialization.py` | 整合 | 高 | 状态序列化器，合并到序列化模块 |
| `temporal/temporal_manager.py` | `src/core/common/utils/temporal.py` | 移动 | 中 | 统一时间管理器，作为工具类 |
| `id_generator/id_generator.py` | `src/core/common/utils/id_generator.py` | 移动 | 中 | 统一ID生成器，作为工具类 |
| `metadata/metadata_manager.py` | `src/core/common/utils/metadata.py` | 移动 | 中 | 统一元数据管理器，作为工具类 |
| `monitoring/performance_monitor.py` | `src/core/common/monitoring.py` | 移动 | 低 | 性能监控器 |
| `storage/base_storage.py` | `src/core/common/storage.py` | 移动 | 低 | 基础存储实现 |
| `storage/history_storage_adapter.py` | `src/core/common/storage.py` | 整合 | 低 | History存储适配器，合并到存储模块 |

## 详细迁移方案

### 第一阶段：核心接口和基础功能迁移

#### 1. 接口定义迁移
- **原文件**: `src/infrastructure/common/interfaces.py`
- **新路径**: `src/core/common/interfaces.py`
- **说明**: 将基础接口定义整合到核心接口文件中
- **依赖**: 无
- **优先级**: 高
- **风险**: 低

#### 2. 缓存系统整合
- **原文件**: `src/infrastructure/common/cache/cache_manager.py` 和 `src/infrastructure/common/cache/cache_entry.py`
- **新路径**: `src/core/common/cache.py`
- **说明**: 将基础设施层的缓存管理器与现有的 `src/core/common/cache.py` 进行整合
- **整合方案**:
  - 保留 `src/core/common/cache.py` 中基于 `cachetools` 的实现作为主要缓存系统
  - 将 `cache_manager.py` 中的高级功能（如序列化支持、统计信息、批量操作等）作为增强功能添加
  - 将 `cache_entry.py` 中的缓存条目定义整合到新的缓存实现中
- **依赖**: 需要安装 `cachetools` 依赖
- **优先级**: 高
- **风险**: 中等（需要确保兼容性）

### 第二阶段：序列化和时间管理功能迁移

#### 3. 序列化器迁移
- **原文件**: `src/infrastructure/common/serialization/serializer.py` 和 `src/infrastructure/common/serialization/state_serializer.py`
- **新路径**: `src/core/common/serialization.py`
- **说明**: 创建新的序列化模块，包含功能丰富的序列化和反序列化功能
- **功能**:
  - JSON、Pickle和Compact JSON格式支持
  - 轻量级缓存机制
  - 性能统计
  - 特殊类型处理（日期时间、枚举等）
  - 线程安全
- **优先级**: 高
- **风险**: 低

#### 4. 时间管理器迁移
- **原文件**: `src/infrastructure/common/temporal/temporal_manager.py`
- **新路径**: `src/core/common/utils/temporal.py`
- **说明**: 将时间管理功能作为工具类添加到utils目录
- **功能**:
  - 当前时间获取（本地和UTC）
  - 时间戳格式化和解析
 - 时间差计算
  - 时区转换
  - 过期检查
- **优先级**: 中
- **风险**: 低

### 第三阶段：工具类迁移

#### 5. ID生成器迁移
- **原文件**: `src/infrastructure/common/id_generator/id_generator.py`
- **新路径**: `src/core/common/utils/id_generator.py`
- **说明**: 将ID生成功能作为工具类添加到utils目录
- **功能**:
  - UUID生成
  - 时间戳ID生成
  - 哈希ID生成
  - NanoID生成
  - 专用ID生成（会话、线程、检查点、工作流等）
- **优先级**: 中
- **风险**: 低

#### 6. 元数据管理器迁移
- **原文件**: `src/infrastructure/common/metadata/metadata_manager.py`
- **新路径**: `src/core/common/utils/metadata.py`
- **说明**: 将元数据管理功能作为工具类添加到utils目录
- **功能**:
  - 元数据标准化
  - 元数据合并
  - 元数据验证
  - 字段提取和设置
- **优先级**: 中
- **风险**: 低

### 第四阶段：监控和存储功能迁移

#### 7. 性能监控器迁移
- **原文件**: `src/infrastructure/common/monitoring/performance_monitor.py`
- **新路径**: `src/core/common/monitoring.py`
- **说明**: 创建监控模块，包含性能监控功能
- **功能**:
  - 操作计时
  - 性能统计
  - 慢操作检测
  - 错误率趋势分析
- **优先级**: 低
- **风险**: 低

#### 8. 存储功能迁移
- **原文件**: `src/infrastructure/common/storage/base_storage.py` 和 `src/infrastructure/common/storage/history_storage_adapter.py`
- **新路径**: `src/core/common/storage.py`
- **说明**: 创建存储模块，包含基础存储实现和适配器
- **功能**:
 - 基础存储接口实现
  - 元数据处理
  - 缓存集成
 - 历史记录适配
- **优先级**: 低
- **风险**: 中等（涉及存储适配器的兼容性）

## 迁移实施步骤

### 步骤1.1: 准备工作
```bash
# 确保备份现有代码
cp -r src/infrastructure/common src/infrastructure/common_backup
```

### 步骤1.2: 创建新架构目录结构
```bash
mkdir -p src/core/common/utils
```

### 步骤1.3: 第一阶段迁移（核心接口和缓存系统）

#### 1.3.1: 接口定义迁移
1. 将 `src/infrastructure/common/interfaces.py` 的内容整合到 `src/core/common/interfaces.py`
2. 检查并解决与现有接口的冲突

#### 1.3.2: 缓存系统整合
1. 扩展 `src/core/common/cache.py` 以包含基础设施层缓存管理器的功能
2. 保持与现有 `cachetools` 基础的兼容性
3. 将缓存条目定义整合到缓存模块中

### 步骤1.4: 第二阶段迁移（序列化和时间管理）

#### 1.4.1: 创建序列化模块
1. 创建 `src/core/common/serialization.py`
2. 实现功能丰富的序列化和反序列化功能

#### 1.4.2: 创建时间管理工具
1. 创建 `src/core/common/utils/temporal.py`
2. 实现时间管理功能

### 步骤1.5: 第三阶段迁移（工具类）

#### 1.5.1: 创建ID生成工具
1. 创建 `src/core/common/utils/id_generator.py`
2. 实现ID生成功能

#### 1.5.2: 创建元数据管理工具
1. 创建 `src/core/common/utils/metadata.py`
2. 实现元数据管理功能

### 步骤1.6: 第四阶段迁移（监控和存储）

#### 1.6.1: 创建监控模块
1. 创建 `src/core/common/monitoring.py`
2. 实现性能监控功能

#### 1.6.2: 创建存储模块
1. 创建 `src/core/common/storage.py`
2. 实现基础存储和适配器功能

## 风险评估和缓解措施

### 高风险项
1. **缓存系统整合** - 需要确保与现有 `cachetools` 基础的兼容性
   - **缓解措施**: 逐步整合功能，保留原有API接口

2. **存储适配器兼容性** - 历史存储适配器可能依赖旧接口
   - **缓解措施**: 在迁移前确保所有依赖项都已更新

### 中风险项
1. **依赖更新** - 需要更新所有引用旧路径的模块
   - **缓解措施**: 使用搜索和替换工具批量更新导入路径

### 低风险项
1. **工具类迁移** - 相对独立，影响范围小
   - **缓解措施**: 标准化迁移流程

## 测试策略

### 单元测试
- 为每个迁移的模块编写单元测试
- 确保新实现的功能与原实现一致

### 集成测试
- 测试迁移后的组件与现有系统的集成
- 确保所有依赖项正确引用新路径

### 性能测试
- 对缓存和序列化功能进行性能对比测试
- 确保新实现的性能不低于原实现

## 迁移后清理

### 步骤1: 验证功能完整性
- 确保所有功能在新位置正常工作
- 运行完整的测试套件

### 步骤2: 更新文档
- 更新所有相关文档中的导入路径
- 修正API文档和使用示例

### 步骤3: 删除旧文件
```bash
rm -rf src/infrastructure/common
```

## 迁移验证清单

- [ ] 所有接口定义正确迁移
- [ ] 缓存系统功能完整
- [ ] 序列化功能正常工作
- [ ] 时间管理功能正常工作
- [ ] ID生成功能正常工作
- [ ] 元数据管理功能正常工作
- [ ] 监控功能正常工作
- [ ] 存储功能正常工作
- [ ] 所有依赖项正确更新
- [ ] 测试套件全部通过
- [ ] 性能不低于原实现

## 时间估算

- **准备阶段**: 1天
- **第一阶段迁移**: 2天
- **第二阶段迁移**: 2天
- **第三阶段迁移**: 1天
- **第四阶段迁移**: 2天
- **测试和验证**: 2天
- **清理和文档更新**: 1天

**总计**: 11天

## 依赖关系

1. 完成接口定义迁移后才能开始缓存系统整合
2. 缓存系统整合完成后才能进行存储功能迁移（因为存储依赖缓存）
3. 序列化模块完成后才能完全整合存储功能
4. 所有基础功能迁移完成后才能进行全面测试

## 回滚计划

如果迁移过程中出现问题，可以执行以下回滚步骤：

```bash
# 恢复备份
rm -rf src/core/common
cp -r src/infrastructure/common_backup src/infrastructure/common

# 重新激活原基础设施公共组件
# 更新所有导入路径回原位置