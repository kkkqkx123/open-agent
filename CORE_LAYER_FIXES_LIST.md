# 📋 Core层架构修复清单

## 🎯 修复优先级分类

### 🔴 高优先级 (立即修复)
- 核心业务逻辑模块，影响系统稳定性
- 包含依赖注入容器调用，严重违反架构原则

### 🟡 中优先级 (近期修复)
- 支撑功能模块，影响开发效率
- 大量日志依赖，需要系统性重构

### 🟢 低优先级 (后续优化)
- 辅助功能模块，影响较小
- 可以逐步优化

---

## 🔴 高优先级修复清单

### 1. Workflow核心模块

#### `src/core/workflow/error_handler.py`
**问题**: 直接使用依赖注入容器和ILogger接口
**修复内容**:
- 移除 `from src.services.container import get_global_container`
- 移除 `from src.interfaces.common_infra import ILogger`
- 移除 `_get_logger_from_container()` 方法
- 创建纯业务逻辑的 `WorkflowErrorCore` 类
- 将日志记录逻辑移到Service层

#### `src/core/workflow/config/node_config_loader.py`
**问题**: 使用依赖注入容器获取配置加载器
**修复内容**:
- 移除 `from src.services.container import get_global_container`
- 移除 `from src.interfaces.common_infra import IConfigLoader`
- 移除容器调用逻辑
- 通过构造函数参数传入配置加载器

### 2. Config核心模块

#### `src/core/config/config_manager_factory.py`
**问题**: 混合使用依赖注入容器和全局工厂
**修复内容**:
- 移除 `from src.services.container import get_global_container`
- 移除全局容器调用
- 创建纯配置管理逻辑
- 分离工厂逻辑到Service层

---

## 🟡 中优先级修复清单

### 3. Workflow子模块 (80+文件)

#### 节点执行模块
- `src/core/workflow/graph/nodes/llm_node.py`
  - 移除 `from src.services.logger import get_logger`
  - 移除 `from src.services.llm.scheduling.task_group_manager import TaskGroupManager`
  - 纯化节点执行逻辑

- `src/core/workflow/graph/nodes/tool_node.py`
  - 移除多处 `from src.services.logger import get_logger`
  - 纯化工具调用逻辑

- `src/core/workflow/graph/nodes/*.py` (所有节点文件)
  - 移除 `from src.services.logger import get_logger`
  - 纯化节点业务逻辑

#### 执行管理模块
- `src/core/workflow/execution/executor.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化执行逻辑

- `src/core/workflow/execution/services/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化服务逻辑

#### 注册表模块
- `src/core/workflow/registry/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化注册逻辑

#### 图构建模块
- `src/core/workflow/graph/**/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化图构建逻辑

### 4. State管理模块 (20+文件)

#### 状态实现
- `src/core/state/implementations/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化状态管理逻辑

#### 状态工厂
- `src/core/state/factories/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 移除Service层依赖调用
  - 纯化工厂逻辑

#### 状态历史
- `src/core/state/history/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化历史管理逻辑

### 5. Tools管理模块 (15+文件)

#### 工具管理
- `src/core/tools/manager.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化工具管理逻辑

- `src/core/tools/executor.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化工具执行逻辑

- `src/core/tools/factory.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化工具工厂逻辑

#### 工具类型
- `src/core/tools/types/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化工具类型逻辑

---

## 🟢 低优先级修复清单

### 6. LLM模块 (10+文件)

#### LLM包装器
- `src/core/llm/wrappers/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化LLM包装逻辑

#### LLM缓存
- `src/core/llm/cache/*.py`
  - 移除异常处理中的日志调用
  - 纯化缓存逻辑

### 7. Storage模块 (5+文件)

- `src/core/storage/error_handler.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化错误处理逻辑

- `src/core/storage/config.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化配置逻辑

### 8. History模块 (5+文件)

- `src/core/history/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化历史管理逻辑

### 9. 其他辅助模块

#### Common工具
- `src/core/common/utils/*.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化工具逻辑

- `src/core/common/async_utils.py`
  - 移除 `from src.services.logger import get_logger`
  - 纯化异步工具逻辑

---

## 🔧 通用修复模式

### 模式1: 移除日志依赖
```python
# 修复前
from src.services.logger import get_logger

logger = get_logger(__name__)

def process_data(data):
    logger.info("处理开始")
    result = data * 2
    logger.info("处理完成")
    return result

# 修复后
def process_data(data):
    # 纯业务逻辑，无日志
    return data * 2
```

### 模式2: 移除依赖注入
```python
# 修复前
from src.services.container import get_global_container

class ConfigManager:
    def __init__(self):
        self.config_loader = get_global_container().get(IConfigLoader)

# 修复后
class ConfigCore:
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
```

### 模式3: 分离业务逻辑
```python
# 修复前 (混合逻辑)
class WorkflowProcessor:
    def process(self):
        logger.info("开始处理")
        # 业务逻辑
        logger.info("处理完成")

# 修复后 (纯Core层)
class WorkflowCore:
    def process(self):
        # 纯业务逻辑
        pass

# 新增Service层
class WorkflowService:
    def __init__(self, core: WorkflowCore, logger: ILogger):
        self._core = core
        self._logger = logger
    
    def process(self):
        self._logger.info("开始处理")
        result = self._core.process()
        self._logger.info("处理完成")
        return result
```

---

## 📊 修复统计

| 模块 | 文件数量 | 主要问题 | 修复复杂度 |
|------|----------|----------|------------|
| workflow | 80+ | 日志依赖、依赖注入 | 高 |
| state | 20+ | 日志依赖、Service调用 | 中 |
| tools | 15+ | 日志依赖 | 中 |
| llm | 10+ | 日志依赖 | 低 |
| config | 15+ | 日志依赖、依赖注入 | 高 |
| storage | 5+ | 日志依赖 | 低 |
| history | 5+ | 日志依赖 | 低 |
| common | 10+ | 日志依赖 | 低 |

**总计**: 148个文件需要修复

---

## ⚡ 快速修复建议

### 第一批 (立即修复)
1. `src/core/workflow/error_handler.py` - 核心错误处理
2. `src/core/workflow/config/node_config_loader.py` - 配置加载
3. `src/core/config/config_manager_factory.py` - 配置管理工厂

### 第二批 (本周内)
1. 所有workflow核心执行文件
2. state管理核心文件
3. tools管理核心文件

### 第三批 (下周)
1. 剩余workflow文件
2. llm和storage文件
3. 其他辅助文件

---

## 🎯 修复验证标准

### 文件级验证
- [ ] 无 `from src.services` 导入
- [ ] 无 `get_global_container()` 调用
- [ ] 无 `get_logger()` 调用
- [ ] 只包含纯业务逻辑

### 模块级验证
- [ ] 可以独立导入和测试
- [ ] 无外部依赖
- [ ] 接口设计清晰

### 系统级验证
- [ ] 所有功能正常工作
- [ ] 性能无明显下降
- [ ] 测试覆盖率达标

这个修复清单提供了精确到文件的修复指导，可以系统性地解决Core层的架构问题。