# 日志系统迁移指南

## 概述

本指南说明如何从直接导入日志（`from src.services.logger import get_logger`）迁移到基于依赖注入的日志架构。

---

## 迁移方案

### 新的日志便利层
**文件**: `src/services/logger/injection.py`

提供统一的日志获取方式：
```python
from src.services.logger import get_logger

logger = get_logger(__name__)
logger.info("应用启动")
```

**特点**：
- ✅ 导入接口而非具体实现（解耦）
- ✅ 由容器在启动时自动注入
- ✅ 支持多环境（生产、开发、测试）
- ✅ 便于单元测试 mock

---

## 使用方式

### 方式 1：模块级别使用（推荐，90%场景）

**Before** (旧方式)：
```python
from src.services.logger import LoggerService

class WorkflowService:
    def __init__(self):
        self.logger = LoggerService("workflow")
    
    def execute(self):
        self.logger.info("执行工作流")
```

**After** (新方式)：
```python
from src.services.logger import get_logger

logger = get_logger(__name__)

class WorkflowService:
    def execute(self):
        logger.info("执行工作流")
```

### 方式 2：构造函数注入（更优雅，关键服务）

```python
from src.interfaces.logger import ILogger

class WorkflowService:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def execute(self):
        self.logger.info("执行工作流")

# 在容器中注册
def register_workflow_service(container, config, environment="default"):
    def workflow_factory() -> IWorkflowService:
        logger = container.get(ILogger)
        return WorkflowService(logger)
    
    container.register_factory(
        IWorkflowService,
        workflow_factory,
        environment=environment
    )
```

---

## 架构改进

### 问题解决

| 问题 | 旧方式 | 新方式 |
|------|-------|--------|
| **耦合度** | 高（导入具体实现） | 低（导入接口） |
| **循环依赖** | 容器需要延迟导入 | 解决（无循环） |
| **多环境** | 困难 | 原生支持 |
| **单元测试** | 难以 mock | 容器支持替换 |

### 依赖关系

**Before**:
```
Services/Core 
    ↓ (直接导入)
services.logger (具体实现)
    ↓
interfaces.logger (接口)
```

**After**:
```
Services/Core
    ↓ (导入接口)
interfaces.logger (ILogger)
    ↑
services.logger.injection (便利层)
    ↑
services.container.logger_bindings (注册)
```

---

## 迁移步骤

### Step 1：更新模块导入

**变更列表**：
- `src/services/workflow/function_registry.py`
- `src/services/workflow/execution_service.py`
- `src/services/workflow/building/builder_service.py`
- `src/services/tools/manager.py`
- 其他导入 logger 的服务模块

**操作**：
```bash
# 查找所有需要更改的文件
grep -r "from src.services.logger import get_logger" src/services/
grep -r "from src.services.logger import LoggerService" src/services/
```

### Step 2：替换导入语句

**从**：
```python
from src.services.logger import get_logger
logger = get_logger(__name__)
```

**改为** (不变，inject.py 已包含在 __init__.py 导出中)：
```python
from src.services.logger import get_logger
logger = get_logger(__name__)
```

**或使用接口**（推荐关键服务）：
```python
from src.interfaces.logger import ILogger

class MyService:
    def __init__(self, logger: ILogger):
        self.logger = logger
```

### Step 3：Core 层添加可选 logger

**示例**：`src/core/config/config_manager.py`

```python
from typing import Optional
from src.interfaces.logger import ILogger

class ConfigManager:
    def __init__(self, logger: Optional[ILogger] = None):
        self.logger = logger
    
    def load(self, path: str):
        if self.logger:
            self.logger.debug(f"加载配置: {path}")
        # ... 逻辑
```

### Step 4：容器自动集成

容器启动时自动：
1. 注册 ILogger 接口
2. 创建 LoggerService 实例
3. 设置全局 logger 便利函数

**无需手动修改**，logger_bindings.py 已更新。

---

## 测试中的使用

### 单元测试

```python
import pytest
from src.services.logger.injection import set_logger_instance, clear_logger_instance
from src.interfaces.logger import ILogger

class MockLogger(ILogger):
    def __init__(self):
        self.messages = []
    
    def info(self, message: str, **kwargs):
        self.messages.append(("info", message))
    
    def error(self, message: str, **kwargs):
        self.messages.append(("error", message))
    
    # ... 其他方法

@pytest.fixture
def mock_logger():
    logger = MockLogger()
    set_logger_instance(logger)
    yield logger
    clear_logger_instance()

def test_workflow_logging(mock_logger):
    service = WorkflowService()
    service.execute()
    
    # 验证日志调用
    assert any("执行工作流" in msg for level, msg in mock_logger.messages)
```

### 集成测试

```python
def test_with_test_logger(container):
    # 容器自动提供测试 logger
    logger = container.get(ILogger)
    assert logger is not None
    
    # 使用 logger
    logger.info("测试日志")
```

---

## 特殊场景

### 应用启动流程

```python
from src.services.container import DependencyContainer
from src.services.container.logger_bindings import register_logger_services
from src.services.logger import get_logger

# 1. 创建容器
container = DependencyContainer()

# 2. 注册 logger 服务（自动设置全局实例）
config = load_config()
register_logger_services(container, config["logger"], environment="production")

# 3. 现在可以在任何地方使用便利函数
logger = get_logger(__name__)
logger.info("应用已启动")
```

### 多环境切换

```python
# 开发环境
register_logger_services(container, dev_config, environment="development")

# 测试环境
register_logger_services(container, test_config, environment="test")

# 生产环境
register_logger_services(container, prod_config, environment="production")

# 自动获取当前环境的 logger
logger = get_logger()
```

### 禁用日志（测试）

```python
from src.services.logger.injection import clear_logger_instance

# 禁用全局 logger
clear_logger_instance()

# 现在 get_logger() 会返回临时实现（无操作）
logger = get_logger()
logger.info("这条消息被忽略")
```

---

## 验证迁移

### 运行测试
```bash
uv run pytest tests/ -v
```

### 检查导入
```bash
# 不应该有直接导入具体实现的情况
grep -r "from src.infrastructure.logger" src/services/
grep -r "from src.services.logger.logger_service" src/services/

# 应该使用接口
grep -r "from src.interfaces.logger import ILogger" src/
```

### 性能验证
```bash
# 验证日志记录不会引入额外开销
uv run pytest tests/ --profile
```

---

## 常见问题

### Q1: 为什么要从 `get_logger` 改为注入？
**A**: 
- 更容易进行单元测试和 mock
- 遵循依赖注入原则
- 支持多环境灵活切换
- 减少全局状态依赖

### Q2: 现有代码需要全部改动吗？
**A**: 不需要。新旧方式兼容，可以逐步迁移。优先级：
1. Core 层（添加可选参数）
2. 关键 Services（使用构造函数注入）
3. 其他 Services（保持 `get_logger()` 方式）

### Q3: 如何处理循环导入问题？
**A**: 
- 导入接口而非具体实现
- 使用类型注解时使用 `TYPE_CHECKING`
- 容器在启动时注入，不在模块导入时

### Q4: 日志系统初始化失败怎么办？
**A**: 
- `get_logger()` 有三层降级策略
- 1. 全局实例（最快）
- 2. 容器获取（标准）
- 3. 临时实现（最后手段，不记录日志但不崩溃）

---

## 检查清单

- [ ] 创建 `src/services/logger/injection.py` ✓
- [ ] 更新 `src/services/logger/__init__.py` ✓
- [ ] 更新 `logger_bindings.py` ✓
- [ ] Core 层添加可选 logger 参数
- [ ] Services 层逐步迁移导入
- [ ] 添加单元测试覆盖
- [ ] 运行完整测试套件
- [ ] 更新 AGENTS.md 文档
- [ ] 代码审查

---

## 相关文档

- [Logger 架构分析](./logger_architecture_analysis.md)
- [AGENTS.md](./AGENTS.md) - 开发指南
- [Logger 接口定义](./src/interfaces/logger.py)
