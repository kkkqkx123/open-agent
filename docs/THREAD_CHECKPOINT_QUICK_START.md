# Thread检查点快速开始指南

本指南将帮助您快速上手使用新的DDD架构Thread检查点功能。

## 🚀 快速开始

### 1. 安装依赖

确保您的环境已安装必要的依赖：

```bash
# 安装项目依赖
pip install -r requirements.txt

# 或使用uv
uv add -r requirements.txt
```

### 2. 基本使用

#### 2.1 初始化服务

```python
from src.services.container import Container
from src.services.container.thread_checkpoint_bindings import register_thread_checkpoint_test_services

# 创建依赖注入容器
container = Container()

# 注册Thread检查点服务
register_thread_checkpoint_test_services(container)

# 获取服务
storage_orchestrator = container.resolve("StorageOrchestrator")
thread_storage_service = container.resolve("ThreadStorageService")
```

#### 2.2 初始化线程存储

```python
thread_id = "my_thread_001"
initial_state = {
    "step": "initialized",
    "data": {"counter": 0, "messages": []}
}

# 初始化线程存储
init_checkpoint_id = await thread_storage_service.initialize_thread_storage(
    thread_id=thread_id,
    initial_state=initial_state
)
print(f"初始化检查点ID: {init_checkpoint_id}")
```

#### 2.3 创建检查点

```python
# 创建自动检查点
state_data = {"step": "processing", "data": {"counter": 1}}
result = await storage_orchestrator.create_thread_checkpoint_with_backup(
    thread_id=thread_id,
    state_data=state_data
)
print(f"检查点ID: {result['checkpoint_id']}")

# 创建手动检查点
manual_checkpoint = await storage_orchestrator.create_manual_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data,
    title="重要检查点",
    description="用户手动创建的检查点"
)
print(f"手动检查点ID: {manual_checkpoint.id}")
```

#### 2.4 恢复检查点

```python
# 恢复到指定检查点
restored_state = await storage_orchestrator.restore_thread_checkpoint_with_validation(
    thread_id=thread_id,
    checkpoint_id=manual_checkpoint.id
)
print(f"恢复的状态: {restored_state}")
```

#### 2.5 终结线程存储

```python
final_state = {"step": "completed", "data": {"counter": 2}}
final_checkpoint_id = await thread_storage_service.finalize_thread_storage(
    thread_id=thread_id,
    final_state=final_state
)
print(f"最终检查点ID: {final_checkpoint_id}")
```

## 📚 核心概念

### 1. 检查点类型

```python
from src.core.threads.checkpoints.storage import CheckpointType

# 自动检查点 - 系统自动创建
auto_checkpoint = await storage_orchestrator.create_thread_checkpoint_with_backup(
    thread_id=thread_id,
    state_data=state_data,
    checkpoint_type=CheckpointType.AUTO
)

# 手动检查点 - 用户手动创建
manual_checkpoint = await storage_orchestrator.create_manual_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data,
    title="用户检查点"
)

# 错误检查点 - 发生错误时创建
error_checkpoint = await storage_orchestrator.create_error_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data,
    error_message="处理失败",
    error_type="ProcessingError"
)

# 里程碑检查点 - 重要里程碑
milestone_checkpoint = await storage_orchestrator.create_milestone_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data,
    milestone_name="第一阶段完成"
)
```

### 2. 检查点状态

```python
from src.core.threads.checkpoints.storage import CheckpointStatus

# 检查点状态包括：
# - ACTIVE: 活跃状态
# - EXPIRED: 已过期
# - CORRUPTED: 已损坏
# - ARCHIVED: 已归档

checkpoint = await storage_orchestrator.create_manual_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data
)

# 检查状态
print(f"检查点状态: {checkpoint.status}")
print(f"是否有效: {checkpoint.is_valid()}")
print(f"是否可恢复: {checkpoint.can_restore()}")
```

### 3. 检查点元数据

```python
# 创建带元数据的检查点
checkpoint = await storage_orchestrator.create_manual_checkpoint_for_thread(
    thread_id=thread_id,
    state_data=state_data,
    title="重要检查点",
    description="这是一个重要的检查点",
    tags=["important", "manual", "backup"]
)

# 访问元数据
print(f"标题: {checkpoint.metadata.get('title')}")
print(f"描述: {checkpoint.metadata.get('description')}")
print(f"标签: {checkpoint.metadata.get('tags')}")
```

## 🔧 高级功能

### 1. 检查点链

```python
# 创建检查点链
state_data_list = [
    {"step": 1, "data": {"value": "step1"}},
    {"step": 2, "data": {"value": "step2"}},
    {"step": 3, "data": {"value": "step3"}}
]

chain_metadata = {
    "description": "处理链",
    "total_steps": len(state_data_list)
}

checkpoint_ids = await storage_orchestrator.create_thread_checkpoint_chain(
    thread_id=thread_id,
    state_data_list=state_data_list,
    chain_metadata=chain_metadata
)
print(f"检查点链包含 {len(checkpoint_ids)} 个检查点")
```

### 2. 检查点备份

```python
# 创建备份
backup_id = await storage_orchestrator.create_checkpoint_backup(
    checkpoint_id=checkpoint.id
)
print(f"备份ID: {backup_id}")

# 从备份恢复
restored_state = await storage_orchestrator.restore_from_checkpoint_backup(
    backup_id=backup_id
)
```

### 3. 检查点时间线

```python
# 获取检查点时间线
timeline = await storage_orchestrator.get_thread_checkpoint_timeline(
    thread_id=thread_id,
    include_backups=True
)

for item in timeline:
    print(f"检查点: {item['id']}")
    print(f"类型: {item['type']}")
    print(f"创建时间: {item['created_at']}")
    print(f"大小: {item['size_bytes']} 字节")
    print(f"恢复次数: {item['restore_count']}")
    if item.get('backups'):
        print(f"备份数量: {len(item['backups'])}")
    print("---")
```

### 4. 存储优化

```python
# 优化检查点存储
optimization_results = await storage_orchestrator.optimize_thread_checkpoint_storage(
    thread_id=thread_id,
    max_checkpoints=50,    # 最大检查点数量
    archive_days=30        # 归档天数
)

print(f"归档数量: {optimization_results['archived']}")
print(f"删除数量: {optimization_results['deleted']}")
print(f"创建备份数量: {optimization_results['backups_created']}")
```

### 5. 统计信息

```python
# 获取综合统计信息
stats = await storage_orchestrator.get_comprehensive_checkpoint_statistics(
    thread_id=thread_id
)

print(f"总检查点数: {stats['total_checkpoints']}")
print(f"活跃检查点数: {stats['active_checkpoints']}")
print(f"类型分布: {stats['type_distribution']}")
print(f"平均大小: {stats['average_size_bytes']} 字节")
print(f"平均恢复次数: {stats['average_restores']:.2f}")
```

## 🛠️ 配置

### 1. 基本配置

```python
from src.services.container.thread_checkpoint_bindings import get_thread_checkpoint_service_config

# 获取默认配置
config = get_thread_checkpoint_service_config()

# 自定义配置
custom_config = {
    "storage_backend": "memory",  # 或 "langgraph"
    "checkpoint_limits": {
        "max_checkpoints_per_thread": 100,
        "default_expiration_hours": 24,
        "max_checkpoint_size_mb": 100
    },
    "cleanup_settings": {
        "cleanup_interval_hours": 1,
        "archive_days": 30
    }
}

# 注册自定义配置
from src.services.container import Container
from src.services.container.thread_checkpoint_bindings import register_thread_checkpoint_services

container = Container()
register_thread_checkpoint_services(container, custom_config)
```

### 2. LangGraph集成

```python
from langgraph.checkpoint.memory import MemorySaver
from src.adapters.threads.checkpoints import LangGraphCheckpointAdapter

# 创建LangGraph检查点保存器
langgraph_saver = MemorySaver()

# 创建适配器
adapter = LangGraphCheckpointAdapter(langgraph_saver)

# 使用适配器创建仓储
from src.core.threads.checkpoints.storage import ThreadCheckpointRepository
repository = ThreadCheckpointRepository(adapter._checkpointer)
```

## 🧪 测试

### 1. 运行测试

```bash
# 运行所有测试
pytest tests/test_thread_checkpoint_ddd.py -v

# 运行特定测试
pytest tests/test_thread_checkpoint_ddd.py::TestThreadCheckpoint::test_checkpoint_creation -v

# 运行性能测试
pytest tests/test_thread_checkpoint_ddd.py::TestIntegration::test_full_checkpoint_workflow -v
```

### 2. 测试示例

```python
import pytest
from src.core.threads.checkpoints.storage import ThreadCheckpoint, CheckpointType

def test_checkpoint_creation():
    """测试检查点创建"""
    checkpoint = ThreadCheckpoint(
        thread_id="test_thread",
        state_data={"key": "value"},
        checkpoint_type=CheckpointType.MANUAL
    )
    
    assert checkpoint.thread_id == "test_thread"
    assert checkpoint.state_data == {"key": "value"}
    assert checkpoint.checkpoint_type == CheckpointType.MANUAL
    assert checkpoint.is_valid()
```

## 🔄 迁移

### 1. 从旧架构迁移

```bash
# 试运行迁移
python scripts/migrate_storage_architecture.py --dry-run

# 执行实际迁移
python scripts/migrate_storage_architecture.py

# 使用自定义配置
python scripts/migrate_storage_architecture.py --config custom_config.json
```

### 2. 迁移配置

```json
{
  "source_storage": {
    "type": "sqlite",
    "path": "history.db"
  },
  "target_storage": {
    "type": "memory",
    "backup_path": "backups/migration"
  },
  "migration_settings": {
    "batch_size": 100,
    "create_backups": true,
    "validate_after_migration": true,
    "dry_run": false
  }
}
```

## 🚨 错误处理

### 1. 常见错误

```python
from src.core.threads.checkpoints.storage.exceptions import (
    CheckpointNotFoundError,
    CheckpointValidationError,
    CheckpointStorageError
)

try:
    await storage_orchestrator.restore_thread_checkpoint_with_validation(
        thread_id="nonexistent_thread",
        checkpoint_id="nonexistent_checkpoint"
    )
except CheckpointNotFoundError as e:
    print(f"检查点未找到: {e}")
except CheckpointValidationError as e:
    print(f"检查点验证失败: {e}")
except CheckpointStorageError as e:
    print(f"存储错误: {e}")
```

### 2. 错误恢复

```python
# 创建错误检查点
try:
    # 一些可能失败的操作
    result = await some_risky_operation()
except Exception as e:
    # 创建错误检查点
    error_checkpoint = await storage_orchestrator.create_error_checkpoint_for_thread(
        thread_id=thread_id,
        state_data={"error": str(e), "context": "risky_operation"},
        error_message=str(e),
        error_type=type(e).__name__
    )
    print(f"已创建错误检查点: {error_checkpoint.id}")
```

## 📈 性能优化

### 1. 批量操作

```python
# 批量创建检查点
checkpoint_ids = []
for i in range(100):
    state_data = {"batch_index": i, "data": f"item_{i}"}
    result = await storage_orchestrator.create_thread_checkpoint_with_backup(
        thread_id=thread_id,
        state_data=state_data,
        create_backup=False  # 不创建备份以提高性能
    )
    checkpoint_ids.append(result["checkpoint_id"])
```

### 2. 异步操作

```python
import asyncio

# 并发创建多个检查点
async def create_checkpoints_concurrently():
    tasks = []
    for i in range(10):
        state_data = {"concurrent_index": i}
        task = storage_orchestrator.create_thread_checkpoint_with_backup(
            thread_id=f"thread_{i}",
            state_data=state_data
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return results

results = await create_checkpoints_concurrently()
print(f"并发创建了 {len(results)} 个检查点")
```

## 🔍 监控和调试

### 1. 日志记录

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.INFO)

# 查看详细日志
logger = logging.getLogger("src.core.threads.checkpoints")
logger.setLevel(logging.DEBUG)
```

### 2. 性能监控

```python
import time

start_time = time.time()
result = await storage_orchestrator.create_thread_checkpoint_with_backup(
    thread_id=thread_id,
    state_data=state_data
)
end_time = time.time()

print(f"操作耗时: {(end_time - start_time) * 1000:.2f} 毫秒")
```

## 📖 更多资源

- [完整API文档](../api/thread_checkpoint_api.md)
- [架构设计文档](../architecture/STORAGE_ARCHITECTURE_REFACTOR_PLAN.md)
- [DDD架构验证](../architecture/DDD_ARCHITECTURE_VALIDATION.md)
- [使用示例](../examples/thread_checkpoint_usage.py)

## 🤝 贡献

欢迎贡献代码和文档！请遵循以下步骤：

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 创建 Pull Request

## 📞 支持

如果您遇到问题或有疑问，请：

1. 查看 [FAQ](../faq/thread_checkpoint_faq.md)
2. 搜索 [Issues](https://github.com/your-repo/issues)
3. 创建新的 Issue

---

🎉 **恭喜！您已经掌握了Thread检查点DDD架构的基本使用方法！**