# common_infra.py 接口重构迁移方案

## 🎯 迁移目标

将 `src/interfaces/common_infra.py` 中的接口拆分到各自的专门模块中，同时将相关实现迁移到基础设施层，实现更清晰的架构分层。

## 📊 当前状态分析

### 现有接口目录结构
```
src/interfaces/
├── storage/
│   ├── __init__.py
│   ├── base.py          # 已有 IStorage 接口
│   ├── exceptions.py
│   ├── migration.py
│   ├── monitoring.py
│   └── transaction.py
├── container/
│   ├── __init__.py
│   ├── core.py          # 已有 IDependencyContainer 接口
│   ├── exceptions.py
│   ├── lifecycle.py
│   ├── monitoring.py
│   ├── registry.py
│   ├── resolver.py
│   ├── scoping.py
│   └── testing.py
├── config/
│   ├── __init__.py
│   └── interfaces.py    # 已有配置相关接口
└── common_infra.py      # 需要拆分的文件
```

### 接口映射关系

| common_infra.py 中的接口 | 目标位置 | 现有状态 |
|--------------------------|----------|----------|
| `ServiceLifetime` | `src/interfaces/container/core.py` | 已存在引用 |
| `IStorage` | `src/interfaces/storage/base.py` | ✅ 已存在 |
| `IDependencyContainer` | `src/interfaces/container/core.py` | ✅ 已存在 |
| `IConfigLoader` | `src/interfaces/config/interfaces.py` | ❌ 需要添加 |
| `IConfigInheritanceHandler` | `src/interfaces/config/interfaces.py` | ❌ 需要添加 |

## 🚀 重构迁移计划

### 第一阶段：接口拆分和整合 (2天)

#### 1.1 ServiceLifetime 枚举迁移
**目标**: 将 `ServiceLifetime` 从 `common_infra.py` 迁移到 `container/core.py`

**任务清单**:
- [ ] 检查 `src/interfaces/container/core.py` 中是否已有 `ServiceLifetime` 定义
- [ ] 如果没有，将 `ServiceLifetime` 添加到 `container/core.py`
- [ ] 更新 `common_infra.py` 中的导入，改为从 `container.core` 导入
- [ ] 更新所有直接从 `common_infra` 导入 `ServiceLifetime` 的文件

**影响文件**:
```
src/interfaces/container/core.py
src/interfaces/common_infra.py
所有导入 ServiceLifetime 的文件
```

#### 1.2 IConfigLoader 和 IConfigInheritanceHandler 迁移
**目标**: 将配置相关接口迁移到 `config/interfaces.py`

**任务清单**:
- [ ] 将 `IConfigLoader` 接口添加到 `src/interfaces/config/interfaces.py`
- [ ] 将 `IConfigInheritanceHandler` 接口添加到 `src/interfaces/config/interfaces.py`
- [ ] 更新 `common_infra.py` 中的导入，改为从 `config.interfaces` 导入
- [ ] 更新所有直接从 `common_infra` 导入这些接口的文件

**影响文件**:
```
src/interfaces/config/interfaces.py
src/interfaces/common_infra.py
所有导入 IConfigLoader 和 IConfigInheritanceHandler 的文件
```

#### 1.3 IStorage 接口整合
**目标**: 确保 `IStorage` 接口在 `storage/base.py` 中正确定义

**任务清单**:
- [ ] 验证 `src/interfaces/storage/base.py` 中的 `IStorage` 接口完整性
- [ ] 如果 `common_infra.py` 中有额外的 `IStorage` 定义，进行合并
- [ ] 更新 `common_infra.py` 中的导入，改为从 `storage.base` 导入

#### 1.4 IDependencyContainer 接口整合
**目标**: 确保 `IDependencyContainer` 接口在 `container/core.py` 中正确定义

**任务清单**:
- [ ] 验证 `src/interfaces/container/core.py` 中的 `IDependencyContainer` 接口完整性
- [ ] 如果 `common_infra.py` 中有额外的定义，进行合并
- [ ] 更新 `common_infra.py` 中的导入，改为从 `container.core` 导入

### 第二阶段：实现迁移到基础设施层 (5天)

#### 2.1 配置加载器实现迁移
**目标**: 将配置加载器实现迁移到基础设施层

**任务清单**:
- [ ] 创建 `src/infrastructure/config/` 目录（如果不存在）
- [ ] 迁移 `src/core/config/config_loader.py` 到 `src/infrastructure/config/config_loader.py`
- [ ] 迁移 `src/core/common/utils/inheritance_handler.py` 中的配置相关实现
- [ ] 更新所有导入路径
- [ ] 更新服务绑定配置

**影响文件**:
```
src/infrastructure/config/config_loader.py
src/infrastructure/config/inheritance_handler.py
所有导入配置加载器的文件
```

#### 2.2 存储实现迁移
**目标**: 将存储实现迁移到基础设施层

**任务清单**:
- [ ] 创建 `src/infrastructure/storage/` 目录（如果不存在）
- [ ] 迁移 `src/core/common/storage.py` 到 `src/infrastructure/storage/base_storage.py`
- [ ] 更新所有导入路径
- [ ] 更新服务绑定配置

**影响文件**:
```
src/infrastructure/storage/base_storage.py
所有导入 BaseStorage 的文件
```

#### 2.3 依赖注入容器实现迁移
**目标**: 将依赖注入容器实现迁移到基础设施层

**任务清单**:
- [ ] 创建 `src/infrastructure/container/` 目录（如果不存在）
- [ ] 迁移 `src/services/container/core/container.py` 到 `src/infrastructure/container/dependency_container.py`
- [ ] 更新所有导入路径
- [ ] 更新服务绑定配置

**影响文件**:
```
src/infrastructure/container/dependency_container.py
所有导入 DependencyContainer 的文件
```

### 第三阶段：向后兼容性和清理 (2天)

#### 3.1 更新 common_infra.py
**目标**: 将 `common_infra.py` 转换为重新导出模块

**任务清单**:
- [ ] 重写 `src/interfaces/common_infra.py` 为重新导出模块
- [ ] 添加废弃警告
- [ ] 确保向后兼容性

**新的 common_infra.py 结构**:
```python
"""
通用基础设施接口重新导出模块

此模块提供向后兼容性，建议直接从专门的接口模块导入。
将在未来版本中废弃。
"""

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# 废弃警告
def _deprecation_warning(name: str, new_location: str):
    warnings.warn(
        f"Import '{name}' from src.interfaces.common_infra is deprecated. "
        f"Please import from '{new_location}' instead.",
        DeprecationWarning,
        stacklevel=3
    )

# 重新导出 ServiceLifetime
from src.interfaces.container.core import ServiceLifetime

# 重新导出 IStorage
from src.interfaces.storage.base import IStorage

# 重新导出 IDependencyContainer
from src.interfaces.container.core import IDependencyContainer

# 重新导出配置接口
from src.interfaces.config.interfaces import IConfigLoader, IConfigInheritanceHandler

# 更新 __all__ 列表
__all__ = [
    "ServiceLifetime",
    "IStorage", 
    "IDependencyContainer",
    "IConfigLoader",
    "IConfigInheritanceHandler"
]
```

#### 3.2 更新各模块的 __init__.py
**目标**: 确保各接口模块正确导出接口

**任务清单**:
- [ ] 更新 `src/interfaces/storage/__init__.py`
- [ ] 更新 `src/interfaces/container/__init__.py`
- [ ] 更新 `src/interfaces/config/__init__.py`
- [ ] 更新主 `src/interfaces/__init__.py`

#### 3.3 测试和验证
**任务清单**:
- [ ] 运行所有测试确保功能正常
- [ ] 验证导入路径正确
- [ ] 检查性能无回归
- [ ] 验证向后兼容性

## 📁 目标目录结构

### 接口层结构
```
src/interfaces/
├── storage/
│   ├── __init__.py          # 导出 IStorage, IStorageFactory 等
│   ├── base.py              # IStorage, IStorageFactory 接口
│   ├── exceptions.py        # 存储异常
│   ├── migration.py         # 存储迁移接口
│   ├── monitoring.py        # 存储监控接口
│   └── transaction.py       # 存储事务接口
├── container/
│   ├── __init__.py          # 导出 IDependencyContainer, ServiceLifetime 等
│   ├── core.py              # IDependencyContainer, ServiceLifetime 等
│   ├── exceptions.py        # 容器异常
│   ├── lifecycle.py         # 生命周期接口
│   ├── monitoring.py        # 容器监控接口
│   ├── registry.py          # 注册表接口
│   ├── resolver.py          # 解析器接口
│   ├── scoping.py           # 作用域接口
│   └── testing.py           # 测试接口
├── config/
│   ├── __init__.py          # 导出所有配置接口
│   └── interfaces.py        # IConfigLoader, IConfigInheritanceHandler 等
└── common_infra.py          # 向后兼容性重新导出模块
```

### 基础设施层结构
```
src/infrastructure/
├── config/
│   ├── __init__.py
│   ├── config_loader.py     # ConfigLoader 实现
│   └── inheritance_handler.py  # ConfigInheritanceHandler 实现
├── storage/
│   ├── __init__.py
│   └── base_storage.py      # BaseStorage 实现
└── container/
    ├── __init__.py
    └── dependency_container.py  # DependencyContainer 实现
```

## 🔄 导入路径变更

### 主要变更
```python
# 旧的导入方式
from src.interfaces.common_infra import ServiceLifetime
from src.interfaces.common_infra import IStorage
from src.interfaces.common_infra import IDependencyContainer
from src.interfaces.common_infra import IConfigLoader
from src.interfaces.common_infra import IConfigInheritanceHandler

# 新的推荐导入方式
from src.interfaces.container.core import ServiceLifetime
from src.interfaces.storage.base import IStorage
from src.interfaces.container.core import IDependencyContainer
from src.interfaces.config.interfaces import IConfigLoader, IConfigInheritanceHandler

# 实现导入变更
from src.core.config.config_loader import ConfigLoader  # 旧
from src.infrastructure.config.config_loader import ConfigLoader  # 新

from src.core.common.storage import BaseStorage  # 旧
from src.infrastructure.storage.base_storage import BaseStorage  # 新

from src.services.container.core.container import DependencyContainer  # 旧
from src.infrastructure.container.dependency_container import DependencyContainer  # 新
```

## 🧪 测试策略

### 测试层级
1. **接口兼容性测试**: 确保重新导出的接口功能正常
2. **实现迁移测试**: 验证迁移到基础设施层的实现功能正常
3. **集成测试**: 验证整个系统的集成功能
4. **向后兼容性测试**: 确保现有代码无需修改即可工作

### 测试计划
- 每个阶段完成后运行相关测试
- 重点测试导入路径变更
- 验证服务绑定配置正确
- 性能基准测试

## 🚨 风险缓解

### 主要风险
1. **导入路径破坏**: 大量现有代码使用旧导入路径
2. **循环依赖**: 新的导入结构可能引入循环依赖
3. **实现迁移问题**: 实现迁移可能破坏现有功能

### 缓解措施
1. **向后兼容性**: 保持 `common_infra.py` 作为重新导出模块
2. **渐进式迁移**: 分阶段实施，每个阶段都进行充分测试
3. **废弃警告**: 提供明确的迁移路径和时间表

## 📅 时间表

| 阶段 | 任务 | 预计时间 | 开始日期 | 结束日期 |
|------|------|----------|----------|----------|
| 1 | 接口拆分和整合 | 2天 | Week 1 Day 1 | Week 1 Day 2 |
| 2 | 实现迁移到基础设施层 | 5天 | Week 1 Day 3 | Week 2 Day 2 |
| 3 | 向后兼容性和清理 | 2天 | Week 2 Day 3 | Week 2 Day 4 |
| 4 | 测试和验证 | 1天 | Week 2 Day 5 | Week 2 Day 5 |

**总计**: 10天 (约2周)

## 🎯 成功指标

### 技术指标
- [ ] 所有测试通过 (100%)
- [ ] 性能无回归 (<5%)
- [ ] 无循环依赖
- [ ] 向后兼容性保持

### 架构指标
- [ ] 接口职责清晰分离
- [ ] 实现正确迁移到基础设施层
- [ ] 导入路径逻辑清晰
- [ ] 代码组织改善

## 📝 总结

这个重构方案遵循了用户的要求：
1. **接口保留在 interfaces 层**: 将接口拆分到专门的模块中
2. **实现迁移到 infrastructure 层**: 将具体实现迁移到基础设施层
3. **利用现有目录结构**: 充分利用已有的 `storage`、`container`、`config` 目录

通过这种方式，我们实现了更清晰的架构分层，同时保持了向后兼容性，为未来的架构优化奠定了基础。