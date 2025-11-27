# 服务层同步/异步重构详细计划

## 概述

本文档详细描述了服务层模块的同步/异步重构计划，基于 `sync_async_refactoring_steps.md` 中的子任务1要求。

## 重构目标

1. 将服务层中的同步方法重构为异步方法
2. 保留同步方法作为适配器（临时兼容性）
3. 简化事件循环处理逻辑
4. 统一异步接口

## 1. StateSnapshotService 重构计划

### 1.1 需要重构的方法

#### 同步方法 → 异步方法映射

| 同步方法 | 异步方法 | 文件行号 |
|---------|---------|---------|
| `create_snapshot()` | `create_snapshot_async()` | 47-87 |
| `restore_snapshot()` | `restore_snapshot_async()` | 89-133 |
| `get_snapshots_by_agent()` | `get_snapshots_by_agent_async()` | 135-214 |
| `cleanup_old_snapshots()` | `cleanup_old_snapshots_async()` | 216-249 |
| `delete_snapshot()` | `delete_snapshot_async()` | 251-275 |
| `get_snapshot_statistics()` | `get_snapshot_statistics_async()` | 277-297 |
| `find_snapshots_by_name()` | `find_snapshots_by_name_async()` | 299-324 |
| `get_snapshots_in_time_range()` | `get_snapshots_in_time_range_async()` | 326-353 |
| `create_auto_snapshot()` | `create_auto_snapshot_async()` | 355-374 |

### 1.2 重构示例

#### 原始同步方法
```python
def create_snapshot(self, agent_id: str, state_data: Dict[str, Any],
                   snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
    """创建状态快照"""
    try:
        # 创建快照对象
        snapshot = self._create_snapshot(agent_id, state_data, snapshot_name, metadata)
        
        # 转换为字典格式保存到Repository
        snapshot_dict = {
            "snapshot_id": snapshot.snapshot_id,
            "agent_id": snapshot.agent_id,
            "domain_state": snapshot.domain_state,
            "timestamp": snapshot.timestamp,
            "snapshot_name": snapshot.snapshot_name,
            "metadata": snapshot.metadata or {},
            "compressed_data": getattr(snapshot, 'compressed_data', None),
            "size_bytes": getattr(snapshot, 'size_bytes', 0)
        }
        
        # 保存到Repository
        snapshot_id = asyncio.run(self._snapshot_repository.save_snapshot(snapshot_dict))
        
        # 更新缓存
        self._update_cache(snapshot)
        
        # 清理旧快照
        self.cleanup_old_snapshots(agent_id)
        
        logger.debug(f"快照创建成功: {snapshot_id}")
        return snapshot_id
        
    except Exception as e:
        logger.error(f"创建快照失败: {e}")
        raise
```

#### 重构后的异步方法
```python
async def create_snapshot_async(self, agent_id: str, state_data: Dict[str, Any],
                               snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
    """异步创建状态快照"""
    try:
        # 创建快照对象
        snapshot = self._create_snapshot(agent_id, state_data, snapshot_name, metadata)
        
        # 序列化和压缩状态数据
        if self._serializer:
            serialized_data = self._serializer.serialize_state(state_data)
            compressed_data = self._serializer.compress_data(serialized_data)
            snapshot.compressed_data = compressed_data
            snapshot.size_bytes = len(compressed_data)
        
        # 转换为字典格式保存到Repository
        snapshot_dict = {
            "snapshot_id": snapshot.snapshot_id,
            "agent_id": snapshot.agent_id,
            "domain_state": snapshot.domain_state,
            "timestamp": snapshot.timestamp,
            "snapshot_name": snapshot.snapshot_name,
            "metadata": snapshot.metadata or {},
            "compressed_data": getattr(snapshot, 'compressed_data', None),
            "size_bytes": getattr(snapshot, 'size_bytes', 0)
        }
        
        # 直接异步调用，无需转换
        snapshot_id = await self._snapshot_repository.save_snapshot(snapshot_dict)
        
        # 更新缓存
        self._update_cache(snapshot)
        
        # 清理旧快照
        await self.cleanup_old_snapshots_async(agent_id)
        
        logger.debug(f"快照创建成功: {snapshot_id}")
        return snapshot_id
        
    except Exception as e:
        logger.error(f"创建快照失败: {e}")
        raise
```

#### 保留的同步适配器方法
```python
def create_snapshot(self, agent_id: str, state_data: Dict[str, Any],
                   snapshot_name: str = "", metadata: Optional[Dict[str, Any]] = None) -> str:
    """同步创建快照（适配器方法）"""
    # 添加弃用警告
    import warnings
    warnings.warn(
        "create_snapshot is deprecated, use create_snapshot_async instead",
        DeprecationWarning,
        stacklevel=2
    )
    
    # 调用异步版本
    return asyncio.run(self.create_snapshot_async(agent_id, state_data, snapshot_name, metadata))
```

## 2. StatePersistenceService 重构计划

### 2.1 需要重构的方法

| 同步方法 | 异步方法 | 文件行号 |
|---------|---------|---------|
| `save_state_with_history()` | `save_state_with_history_async()` | 41-123 |
| `restore_state_from_snapshot()` | `restore_state_from_snapshot_async()` | 125-182 |
| `batch_save_history_entries()` | `batch_save_history_entries_async()` | 184-215 |
| `batch_save_snapshots()` | `batch_save_snapshots_async()` | 217-248 |
| `cleanup_agent_data()` | `cleanup_agent_data_async()` | 250-298 |
| `get_comprehensive_statistics()` | `get_comprehensive_statistics_async()` | 300-322 |
| `export_agent_data()` | `export_agent_data_async()` | 324-358 |
| `import_agent_data()` | `import_agent_data_async()` | 360-406 |

### 2.2 重构注意事项

1. 事务上下文管理器需要支持异步
2. 批量操作需要使用异步并发处理
3. 统计信息获取需要合并多个异步调用

## 3. StateHistoryService 重构计划

### 3.1 需要重构的方法

| 同步方法 | 异步方法 | 文件行号 |
|---------|---------|---------|
| `record_state_change()` | `record_state_change_async()` | 61-97 |
| `get_state_history()` | `get_state_history_async()` | 99-134 |
| `cleanup_old_entries()` | `cleanup_old_entries_async()` | 162-190 |
| `get_history_statistics()` | `get_history_statistics_async()` | 192-209 |
| `clear_history()` | `clear_history_async()` | 211-228 |
| `get_state_at_time()` | `get_state_at_time_async()` | 230-251 |

### 3.2 重构注意事项

1. 历史记录重放逻辑需要保持同步（CPU密集型）
2. 缓存更新需要线程安全
3. 状态差异计算可以保持同步

## 4. PromptLoader 重构计划

### 4.1 需要重构的方法

| 同步方法 | 异步方法 | 文件行号 |
|---------|---------|---------|
| `load_prompt()` | `load_prompt_async()` | 33-77 |
| `load_simple_prompt()` | `load_simple_prompt_async()` | 79-110 |
| `load_composite_prompt()` | `load_composite_prompt_async()` | 112-163 |
| `load_prompts()` | `load_prompts_async()` | 187-230 |
| `list_prompts()` | `list_prompts_async()` | 460-488 |

### 4.2 重构注意事项

1. 移除复杂的事件循环检测逻辑
2. 简化异步文件读取
3. 统一使用异步文件操作

## 5. FallbackSystem 重构计划

### 5.1 需要重构的方法

| 同步方法 | 异步方法 | 文件行号 |
|---------|---------|---------|
| `call_client()` (内部方法) | `call_client_async()` | 438-450 |

### 5.2 重构注意事项

1. 简化并行降级策略中的同步/异步混用
2. 统一使用异步客户端调用
3. 移除不必要的线程池包装

## 6. 实施步骤

### 步骤1：创建异步方法
1. 为每个同步方法创建对应的异步版本
2. 将 `asyncio.run()` 调用替换为直接 `await`
3. 更新方法签名添加 `async` 关键字

### 步骤2：保留同步适配器
1. 保留原始同步方法
2. 添加弃用警告
3. 在同步方法中调用异步版本

### 步骤3：更新调用方
1. 搜索所有调用同步方法的地方
2. 逐步更新为异步调用
3. 确保调用方上下文支持异步

### 步骤4：验证和测试
1. 运行单元测试
2. 进行集成测试
3. 性能基准测试

## 7. 代码质量保证

### 7.1 类型注解
- 所有异步方法需要正确的类型注解
- 返回类型需要包含 `Awaitable` 或具体类型

### 7.2 错误处理
- 保持原有的错误处理逻辑
- 异步方法中的异常处理需要正确使用 `await`

### 7.3 日志记录
- 保持原有的日志记录
- 在异步方法中添加适当的调试信息

## 8. 性能优化

### 8.1 并发处理
- 批量操作使用 `asyncio.gather()` 并发执行
- 避免串行等待多个异步操作

### 8.2 资源管理
- 使用异步上下文管理器
- 正确管理异步资源生命周期

## 9. 向后兼容性

### 9.1 弃用策略
- 同步方法添加 `DeprecationWarning`
- 在文档中明确标注弃用信息
- 提供迁移指南

### 9.2 版本管理
- 在下一个主版本中移除同步方法
- 提供足够的过渡期

## 10. 测试策略

### 10.1 单元测试
- 为每个异步方法创建对应的测试
- 使用 `pytest-asyncio` 进行异步测试

### 10.2 集成测试
- 测试异步方法的端到端功能
- 验证与现有系统的兼容性

### 10.3 性能测试
- 对比重构前后的性能
- 确保异步版本性能提升

## 11. 风险评估

### 11.1 技术风险
- 异步/同步混用可能导致死锁
- 事件循环管理复杂性

### 11.2 缓解措施
- 逐步重构，避免大规模变更
- 充分的测试覆盖
- 保留同步适配器作为备选方案

## 12. 时间计划

| 阶段 | 任务 | 预计时间 |
|------|------|---------|
| 1 | StateSnapshotService 重构 | 2天 |
| 2 | StatePersistenceService 重构 | 3天 |
| 3 | StateHistoryService 重构 | 2天 |
| 4 | PromptLoader 重构 | 2天 |
| 5 | FallbackSystem 重构 | 1天 |
| 6 | 测试和验证 | 2天 |
| 7 | 文档更新 | 1天 |

总计：13天

## 13. 成功标准

1. 所有同步方法都有对应的异步版本
2. 同步方法作为适配器正常工作
3. 所有测试通过
4. 性能提升达到预期
5. 代码质量符合项目标准