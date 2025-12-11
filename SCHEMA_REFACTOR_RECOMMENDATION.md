# Schema 架构问题诊断与重构建议

## 问题分析

### 1. **命名和结构不一致**

**当前状况：**
- `edge_schema.py`, `graph_schema.py`, `node_schema.py`, `workflow_schema.py` 继承 `ConfigSchema`（来自 `impl.base_impl`）
- `tools_schema.py`, `llm_schema.py` 继承 `IConfigSchema`（接口类）
- 这违反了依赖倒置原则：Schema 层应该依赖接口，而不是实现

### 2. **重复的 Schema 定义**

- `IConfigSchema` 接口在 `src/interfaces/config/schema.py` 中定义
- `IConfigSchema` 抽象类在 `src/infrastructure/config/impl/base_impl.py` 中重新定义（重复）
- `ConfigSchema` 实现类也在 `src/infrastructure/config/impl/base_impl.py` 中

这导致：
- 同一接口有多个定义
- 混淆了接口和实现
- 违反了分层架构原则

### 3. **架构层级混乱**

**正确的分层应该是：**
```
Interfaces Layer: IConfigSchema (接口定义)
              ↓
Infrastructure Layer: ConfigSchema (基础实现)
              ↓
Schema Layer: EdgeSchema, GraphSchema 等（具体实现）
```

**当前混乱：**
- Impl 文件夹既有接口定义也有实现
- Schema 继承关系不明确
- 导入路径混乱（有的导 `IConfigSchema`，有的导 `ConfigSchema`）

## 重构方案

### 方案 A：使用统一接口（推荐）

**步骤 1：确认接口定义位置**
```python
# src/interfaces/config/schema.py - 唯一的接口定义
class IConfigSchema(ABC):
    @abstractmethod
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        pass
```

**步骤 2：创建 Schema 基类（在 Infrastructure 层）**
```python
# src/infrastructure/config/schema/base_schema.py
from src.interfaces.config.schema import IConfigSchema

class BaseSchema(IConfigSchema):
    """所有具体 Schema 的基类"""
    def __init__(self, schema_definition: Optional[Dict[str, Any]] = None):
        self.schema_definition = schema_definition or {}
    
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        """基础验证逻辑"""
        # 实现共同的验证逻辑
        pass
```

**步骤 3：所有具体 Schema 继承 BaseSchema**
```python
# src/infrastructure/config/schema/tools_schema.py
from .base_schema import BaseSchema

class ToolsSchema(BaseSchema):
    def validate(self, config: Dict[str, Any]) -> ValidationResult:
        # 实现工具特定验证
        pass
```

### 方案 B：删除重复的 impl 定义

**删除：** `src/infrastructure/config/impl/base_impl.py` 中的 `IConfigSchema` 抽象类定义

**保留：**
- `ConfigSchema` 实现类改名为 `BaseSchema` 并移到 `schema/base_schema.py`
- 移除 impl 中的 schema 相关定义

## 实施步骤

### 1. 新建 base_schema.py
```python
# src/infrastructure/config/schema/base_schema.py
from typing import Dict, Any
from src.interfaces.config.schema import IConfigSchema
from src.interfaces.common_domain import ValidationResult

class BaseSchema(IConfigSchema):
    """配置模式基类实现"""
    # 从 base_impl.py 复制 ConfigSchema 的实现
```

### 2. 修改现有 Schema 文件
```python
# 修改 edge_schema.py 等
from .base_schema import BaseSchema  # 改为这个

class EdgeSchema(BaseSchema):  # 改为继承 BaseSchema
    pass
```

### 3. 清理 base_impl.py
```python
# 删除 IConfigSchema 接口定义（重复）
# 删除 ConfigSchema 实现类（已迁移）
```

### 4. 更新导入
- 所有 `from ..impl.base_impl import IConfigSchema` → 删除，使用接口
- 所有 `from ..impl.base_impl import ConfigSchema` → `from .base_schema import BaseSchema`

## 导入规则（修复后）

| 文件位置 | 应该导入 | 不应该导入 |
|---------|---------|-----------|
| `tools_schema.py` | `IConfigSchema` (接口) | `ConfigSchema` |
| `edge_schema.py` | `BaseSchema` (基类) | `ConfigSchema` from impl |
| `impl/` | `IConfigSchema` (接口) | 无 |

## 验证清单

- [ ] 删除 `impl/base_impl.py` 中重复的 `IConfigSchema` 定义
- [ ] 创建 `schema/base_schema.py` 包含 `BaseSchema`
- [ ] 所有 Schema 文件导入 `BaseSchema` 而非 impl 的类
- [ ] `tools_schema.py` 和 `llm_schema.py` 改为继承 `BaseSchema`
- [ ] 所有导入语句一致性检查
- [ ] 运行 mypy 验证无错误
- [ ] 运行测试确保功能正常

## 收益

✓ 清晰的架构层级（接口 → 实现 → 具体）  
✓ 遵循 DIP（依赖倒置原则）  
✓ 消除重复定义  
✓ 统一的继承体系  
✓ 更好的代码可维护性  
