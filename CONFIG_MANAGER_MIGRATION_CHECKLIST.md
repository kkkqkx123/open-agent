# 配置管理器迁移检查清单

## 迁移完成状态 ✓

### 已创建的文件
- ✓ `src/core/config/managers/__init__.py` - 管理器导出模块
- ✓ `src/core/config/managers/base_config_manager.py` - 基类
- ✓ `src/core/config/managers/storage_config_manager.py` - 存储配置管理器
- ✓ `src/core/config/managers/state_config_manager.py` - 状态配置管理器
- ✓ `src/core/config/managers/tools_config_manager.py` - 工具配置管理器
- ✓ `src/core/config/managers/workflow_config_manager.py` - 工作流配置管理器

### 已删除的文件
- ✓ `src/services/storage/config_service.py`
- ✓ `src/services/state/config_service.py`
- ✓ `src/services/tools/config_service.py`
- ✓ `src/services/workflow/config_service.py`
- ✓ `src/services/config/` (整个目录)

### 已更新的导入
- ✓ `src/core/storage/__init__.py` - 从services改为core导入
- ✓ `src/adapters/repository/state/sqlite_repository.py` - 更新导入
- ✓ `src/services/tools/__init__.py` - 导入改为core层
- ✓ `src/services/workflow/__init__.py` - 导入改为core层

## 使用指南

### 导入方式

**推荐：直接从managers模块导入**
```python
from src.core.config.managers import (
    StorageConfigManager,
    StateConfigManager,
    ToolsConfigManager,
    WorkflowConfigManager,
    get_global_storage_config_manager,
    get_global_state_config_manager,
)
```

**向后兼容别名**
```python
from src.core.config.managers import (
    StorageConfigService,  # = StorageConfigManager
    StateConfigService,    # = StateConfigManager
    ToolsConfigService,    # = ToolsConfigManager
    WorkflowConfigService, # = WorkflowConfigManager
)
```

### 全局实例获取

```python
# 存储配置
manager = get_global_storage_config_manager()
config = manager.get_config("default")

# 状态配置
manager = get_global_state_config_manager()
value = manager.get_config_value("core.debug_mode")

# 工具配置
manager = get_tools_config_manager(config_manager)
tools = manager.load_all_tools()

# 工作流配置
manager = get_workflow_config_manager(config_manager)
graph = manager.load_config("path/to/config")
```

## 后续更新清单

### 需要更新的文件（非紧急）
- [ ] `src/services/tools/__init__.py` - 移除tools导出（可选，保留向后兼容）
- [ ] `src/services/workflow/__init__.py` - 移除workflow导出（可选，保留向后兼容）
- [ ] 更新所有直接导入services层config_service的代码
- [ ] 文档中更新示例导入

### 搜索需要更新的代码
```bash
# 查找仍然使用services层导入的代码
使用grep工具

### 验证清单
- [ ] 运行 `uv run mypy src/core/config/managers/ --follow-imports=silent` 无错误
- [ ] 运行 `uv run pytest` 测试无失败
- [ ] 检查没有循环导入：`grep -r "from src\.services\..*from src\.core"` 无结果

## 架构验证

### 依赖关系检查

✓ **正确的依赖流向**
```
ConfigManager (core/config/managers/)
├── 使用 Core的验证器 ✓
├── 使用 Core的数据模型 ✓
├── 使用 Infrastructure的模型 ✓
└── 使用 Infrastructure的IConfigManager ✓
```

✓ **无反向依赖**
- Core层不再依赖Services层
- Infrastructure层不依赖任何其他层

✓ **Services层的使用**
- `src/services/tools/__init__.py` 导入来自Core ✓
- `src/services/workflow/__init__.py` 导入来自Core ✓
- `src/core/storage/__init__.py` 导入来自Core ✓

## 测试场景

### 基本功能测试
```python
# 测试存储配置管理器
from src.core.config.managers import get_global_storage_config_manager
manager = get_global_storage_config_manager()
assert manager.get_config_collection() is not None

# 测试状态配置管理器
from src.core.config.managers import get_global_state_config_manager
manager = get_global_state_config_manager()
assert manager.get_config_value("core") is not None

# 测试工具配置管理器
from src.core.config.managers import ToolsConfigManager
manager = ToolsConfigManager(config_manager)
assert manager.get_supported_tool_types() is not None

# 测试工作流配置管理器
from src.core.config.managers import WorkflowConfigManager
manager = WorkflowConfigManager(config_manager)
assert manager is not None
```

## 注意事项

1. **避免循环导入**：不要在 `src/core/config/__init__.py` 中导出managers，managers自己的 `__init__.py` 已经导出

2. **向后兼容性**：所有ConfigService别名都保留在managers模块中，便于过渡

3. **全局实例管理**：每个管理器都有全局实例获取函数，遵循单例模式

4. **配置文件路径**：每个管理器的默认配置路径：
   - Storage: `configs/storage.yaml`
   - State: `configs/state_management.yaml`
   - Tools: 动态（通过load_config指定）
   - Workflow: 动态（通过load_config指定）

