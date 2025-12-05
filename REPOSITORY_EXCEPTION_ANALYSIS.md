# Repository异常定义分析报告

## 现状分析

### 1. 当前文件结构

**文件位置**: `src/core/common/exceptions/repository.py`

**当前定义**:
```python
# 6个异常类
- RepositoryError           # 基础异常
- RepositoryNotFoundError   # 记录未找到
- RepositoryAlreadyExistsError  # 记录已存在
- RepositoryOperationError  # 操作异常
- RepositoryConnectionError # 数据库连接异常
- RepositoryTransactionError # 事务异常
```

### 2. 存在的问题

#### 问题1: 架构分层违反
- **定义位置**: Core层中 (`src/core/common/exceptions/`)
- **使用位置**: 接口层、Core层、Adapter层都在使用
- **问题**: 根据AGENTS.md，所有**接口定义应该在接口层集中化管理**，但Repository异常定义在Core层

#### 问题2: 与Storage异常体系不一致
**存储异常** (在`src/interfaces/storage/exceptions.py`):
- 16个细分异常类
- 包含`error_code`字段用于错误追踪
- 覆盖更多场景: 压缩、加密、索引、一致性等
- 支持`details: Dict[str, Any]`结构化错误信息

**Repository异常** (当前):
- 仅6个异常类
- 缺少`error_code`识别
- 仅支持简单message和details
- 不够细粒度化

#### 问题3: 缺少错误代码体系
Storage异常通过`error_code`字段支持精确的错误识别:
```python
StorageError(message, error_code="CONN_001", details={...})
```

Repository异常无此机制，导致:
- 难以进行错误恢复和重试策略
- 无法进行细粒度的监控告警
- 错误上报信息不够结构化

#### 问题4: 接口层无异常定义
与Storage对比:
- **Storage**: 异常定义在`src/interfaces/storage/exceptions.py`，导出于接口模块
- **Repository**: 异常定义在Core层，未在接口层定义

## 推荐方案

### 方案A: 将Repository异常迁移到接口层（推荐）

**优点**:
- 遵循架构规范：接口层集中化管理异常定义
- 与Storage异常体系保持一致性
- 支持error_code错误代码体系
- Core/Service/Adapter层都可从接口层导入

**实施步骤**:

#### 1. 创建接口层异常定义
创建文件: `src/interfaces/repository/exceptions.py`
```python
"""Repository异常定义

定义数据访问层相关的异常类型，提供统一的错误处理机制。
"""

from typing import Optional, Dict, Any


class RepositoryError(Exception):
    """Repository基础异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class RepositoryNotFoundError(RepositoryError):
    """记录未找到异常"""
    pass


class RepositoryAlreadyExistsError(RepositoryError):
    """记录已存在异常"""
    pass


class RepositoryOperationError(RepositoryError):
    """Repository操作异常"""
    pass


class RepositoryConnectionError(RepositoryError):
    """数据库连接异常"""
    pass


class RepositoryTransactionError(RepositoryError):
    """事务异常"""
    pass


class RepositoryValidationError(RepositoryError):
    """仓储验证异常"""
    pass


class RepositoryTimeoutError(RepositoryError):
    """仓储超时异常"""
    pass


__all__ = [
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]
```

#### 2. 更新接口层导出
修改: `src/interfaces/repository/__init__.py`
```python
"""Repository接口层

定义数据访问层的Repository接口，实现状态与存储的解耦。
"""

from .state import IStateRepository
from .history import IHistoryRepository  
from .snapshot import ISnapshotRepository
from .checkpoint import ICheckpointRepository
from .session import ISessionRepository
from .exceptions import (
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)

__all__ = [
    # 接口
    "IStateRepository",
    "IHistoryRepository", 
    "ISnapshotRepository",
    "ICheckpointRepository",
    "ISessionRepository",
    # 异常
    "RepositoryError",
    "RepositoryNotFoundError",
    "RepositoryAlreadyExistsError",
    "RepositoryOperationError",
    "RepositoryConnectionError",
    "RepositoryTransactionError",
    "RepositoryValidationError",
    "RepositoryTimeoutError",
]
```

#### 3. 更新全局接口导出
修改: `src/interfaces/__init__.py` (第125行)
```python
# Repository异常
from .repository import (
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)
```

#### 4. 更新Core层导出（向后兼容）
修改: `src/core/common/exceptions/__init__.py`
```python
# Repository异常 - 从接口层导入以实现向后兼容
from src.interfaces.repository.exceptions import (
    RepositoryError,
    RepositoryNotFoundError,
    RepositoryAlreadyExistsError,
    RepositoryOperationError,
    RepositoryConnectionError,
    RepositoryTransactionError,
    RepositoryValidationError,
    RepositoryTimeoutError,
)
```

#### 5. 删除原文件
删除: `src/core/common/exceptions/repository.py`

#### 6. 更新导入路径
所有导入改为：
```python
# 旧: from src.core.common.exceptions import RepositoryError
# 新（推荐）: from src.interfaces.repository import RepositoryError
# 或（兼容）: from src.core.common.exceptions import RepositoryError
```

### 方案B: 保持现状但扩展功能

若出于某些原因不能迁移，则对现有文件进行增强：

```python
"""Repository相关异常定义"""

from typing import Optional, Dict, Any


class RepositoryError(Exception):
    """Repository基础异常"""
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code  # 新增
        self.details = details or {}


class RepositoryNotFoundError(RepositoryError):
    """记录未找到异常"""
    pass


class RepositoryAlreadyExistsError(RepositoryError):
    """记录已存在异常"""
    pass


class RepositoryOperationError(RepositoryError):
    """Repository操作异常"""
    pass


class RepositoryConnectionError(RepositoryError):
    """数据库连接异常"""
    pass


class RepositoryTransactionError(RepositoryError):
    """事务异常"""
    pass


# 新增异常类
class RepositoryValidationError(RepositoryError):
    """仓储验证异常"""
    pass


class RepositoryTimeoutError(RepositoryError):
    """仓储超时异常"""
    pass
```

## 决策建议

### 强烈推荐: 方案A（接口层迁移）

**原因**:
1. **遵循架构规范**: AGENTS.md明确指出"所有接口定义必须在接口层集中化管理"
2. **保持体系一致性**: Repository异常与Storage异常能够统一管理
3. **支持Infrastructure隔离**: Infrastructure组件只依赖接口层，避免循环依赖
4. **降低维护成本**: 单一异常定义点，避免重复定义

**迁移成本**:
- 低: 仅改动导入路径，无逻辑变更
- Core层可通过从接口层再导入保持向后兼容性

**后续改进**:
1. 在Repository接口中声明可能抛出的异常
2. 在各实现类中使用error_code提供细粒度错误识别
3. 建立Repository异常文档和错误码参考表

## 文件清单

需要修改的文件:
- [ ] 创建 `src/interfaces/repository/exceptions.py`
- [ ] 修改 `src/interfaces/repository/__init__.py`
- [ ] 修改 `src/interfaces/__init__.py`
- [ ] 修改 `src/core/common/exceptions/__init__.py`
- [ ] 删除 `src/core/common/exceptions/repository.py`

需要验证的导入点:
- [ ] `src/adapters/repository/base.py` - 验证导入来源
- [ ] `src/core/threads/checkpoints/` - 验证导入来源
- [ ] `src/services/sessions/repository.py` - 验证导入来源
- [ ] 其他使用Repository异常的地方

## 总结

当前Repository异常定义存在的根本问题是**架构分层违反** - 异常定义应该在接口层，而不是Core层。通过将异常迁移到接口层，不仅能遵循AGENTS.md的规范要求，还能实现与Storage异常体系的统一，提供更好的可维护性和扩展性。
