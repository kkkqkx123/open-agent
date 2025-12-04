# 日志系统架构改进分析

## 当前状态分析

### 1. 现状问题

**导入模式（来自 legacy_usage.md）**：
```python
# 服务层直接导入并使用
from src.services.logger import get_logger
logger = get_logger(__name__)
```

**存在的问题**：
- ❌ 服务层直接导入 logger 服务模块（耦合到具体实现）
- ❌ 没有利用依赖注入容器的生命周期管理
- ❌ logger_bindings.py 定义了注册但没有便利的获取方式
- ❌ 容器.py 中存在延迟导入来避免循环依赖（第32-41行）
- ❌ 无法灵活替换 logger 实现（如测试时）

### 2. 架构分层现状

```
interfaces/logger.py          (ILogger, IBaseHandler, ILogRedactor)
    ↑
infrastructure/logger/        (LoggerFactory, RedactorImpl, etc.)
    ↑
services/logger/             (LoggerService 实现 ILogger)
    ↑
services/container/logger_bindings.py  (注册逻辑)
```

**问题**：
- 每个服务都直接导入 logger 服务，形成多点耦合
- 没有通过容器来获取 logger 实例

---

## 推荐方案

### 方案选择：**依赖注入 + 便利层**

#### 原则
1. **Core 层**：导入接口只（ILogger 等）- 避免对实现的依赖
2. **Services 层**：通过容器获取日志 OR 构造函数注入
3. **Infrastructure 层**：提供具体实现，仅依赖接口
4. **Container 层**：提供便利函数，同时保持依赖注入优势

---

## 具体改进方案

### 方案 A：优先级 ★★★★★（推荐）
**使用依赖注入 + 便利函数混合**

#### 1. 创建 logger 便利模块
**文件**: `src/services/logger/injection.py`
```python
"""日志依赖注入便利层"""
from typing import Optional
from src.interfaces.logger import ILogger

_logger_instance: Optional[ILogger] = None

def set_logger_instance(logger: ILogger) -> None:
    """在应用启动时设置全局 logger 实例（由容器调用）"""
    global _logger_instance
    _logger_instance = logger

def get_logger(module_name: str = __name__) -> ILogger:
    """
    获取日志记录器 - 优先使用依赖注入容器
    
    使用场景：
    1. 模块级别使用：logger = get_logger(__name__)
    2. 注入使用：def __init__(self, logger: ILogger)
    """
    global _logger_instance
    if _logger_instance is not None:
        return _logger_instance
    
    # 后备方案：尝试从容器获取
    try:
        from src.services.container import get_global_container
        return get_global_container().get(ILogger)
    except:
        # 极端情况：返回空实现
        from src.infrastructure.logger.null_logger import NullLogger
        return NullLogger()
```

#### 2. 更新 logger_bindings.py
**关键改动**（logger_bindings.py 第268行后）：
```python
def register_logger_service(container, config: Dict[str, Any], environment: str = "default") -> None:
    """注册Logger服务"""
    
    def logger_factory() -> ILogger:
        # ... 现有逻辑 ...
        return LoggerService(logger_name, infra_logger, business_config)
    
    # 注册LoggerService为单例
    container.register_factory(
        ILogger,
        logger_factory,
        environment=environment,
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # ✨ 新增：设置全局 logger 实例
    logger_instance = container.get(ILogger)
    from src.services.logger.injection import set_logger_instance
    set_logger_instance(logger_instance)
```

#### 3. Core 层导入规范
**src/core/config/config_manager.py** 等模块：
```python
# ✓ 推荐：导入接口
from src.interfaces.logger import ILogger

# ✗ 禁止：导入具体实现
# from src.services.logger import LoggerService
# from src.services.logger import get_logger

class ConfigManager:
    def __init__(self, logger: Optional[ILogger] = None):
        self.logger = logger
```

#### 4. Services 层导入规范
**两种推荐用法**：

**用法 1：模块级别（最简单，用于 90% 的场景）**
```python
from src.services.logger.injection import get_logger

logger = get_logger(__name__)

class WorkflowService:
    def execute(self):
        logger.info("执行工作流")
```

**用法 2：构造函数注入（更优雅，用于关键服务）**
```python
from src.interfaces.logger import ILogger

class WorkflowService:
    def __init__(self, logger: ILogger):
        self.logger = logger
    
    def execute(self):
        self.logger.info("执行工作流")

# 在容器中注册时
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

### 方案 B：纯依赖注入（可选）
**适合严格追求无依赖的项目**

所有模块使用构造函数注入，不使用全局 logger。

```python
class WorkflowService:
    def __init__(self, logger: ILogger):
        self.logger = logger
```

**缺点**：每个需要 logger 的类都要修改构造函数，工作量大。

---

## 改进步骤

### Step 1：创建便利层
```bash
# 创建 injection.py
src/services/logger/injection.py
```

### Step 2：更新 logger_bindings.py
- 添加 `set_logger_instance()` 调用
- 确保在注册后设置全局实例

### Step 3：逐步迁移现有代码
**优先级顺序**：
1. Core 层：添加 Optional[ILogger] 参数
2. Services 层：从 `src.services.logger.injection` 导入
3. Infrastructure 层：保持不变

### Step 4：测试与验证
```python
# tests/services/test_logger_injection.py
def test_logger_injection():
    # 验证通过容器获取 logger
    container = DependencyContainer()
    register_logger_services(container, test_config)
    
    logger = container.get(ILogger)
    assert logger is not None
    assert isinstance(logger, ILogger)
```

---

## 对比分析

| 方面 | 当前方案 | 方案 A（推荐） | 方案 B |
|------|--------|-----------|--------|
| **耦合度** | 高（直接导入实现） | 低（通过接口） | 最低（纯注入） |
| **灵活性** | 低 | 高 | 高 |
| **易用性** | 高 | 高 | 中 |
| **测试支持** | 差（难以模拟） | 优（容器支持） | 优 |
| **迁移成本** | - | 中等 | 高 |
| **性能** | 好 | 好 | 好 |
| **代码简洁性** | 简洁 | 简洁 | 繁琐 |

---

## 关键改进点

### 1. 解决循环依赖
**Before** (container.py 32-41)：
```python
def _get_logger():
    try:
        from src.services.logger import get_logger
        return get_logger(__name__)
    except:
        return None
```

**After**：
```python
# 容器中直接使用 ILogger 接口（无循环风险）
def get(self, service_type: Type[T]) -> T:
    if service_type == ILogger:
        # 从已注册的实例获取
        ...
```

### 2. 支持多环境
```python
# 生产环境
register_logger_services(container, prod_config, environment="production")

# 测试环境
register_logger_services(container, test_config, environment="test")

# 获取当前环境的 logger
logger = container.get(ILogger)  # 自动获取当前环境的实例
```

### 3. 便于单元测试
```python
# 测试中替换 logger
mock_logger = MockLogger()
set_logger_instance(mock_logger)

# 或者在容器中替换
test_container.register_instance(ILogger, mock_logger)
```

---

## 实施检查清单

- [ ] 创建 `src/services/logger/injection.py`
- [ ] 更新 `src/services/container/logger_bindings.py` 添加设置全局实例
- [ ] 更新 `src/services/logger/__init__.py` 导出新的便利层
- [ ] 创建 `src/infrastructure/logger/null_logger.py`（空实现）
- [ ] 更新 Core 层模块添加可选 logger 参数
- [ ] 迁移 Services 层的日志导入
- [ ] 添加单元测试
- [ ] 更新文档（AGENTS.md）

---

## 推荐总结

✅ **采用方案 A（依赖注入 + 便利层）**

**理由**：
1. 兼顾易用性和架构纯正性
2. 解决循环依赖问题
3. 支持灵活的日志替换（测试、多环境）
4. 迁移成本合理
5. 符合现有架构的分层原则
