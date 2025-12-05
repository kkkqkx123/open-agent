# Core层异常全面迁移分析

## 概述

分析了`src/core/common/exceptions/`目录下的所有异常模块（共10个），评估它们是否应该迁移到接口层。

## 目录结构

当前Core异常目录包含：
```
src/core/common/exceptions/
├── __init__.py              # 统一导出
├── config.py                # 配置异常
├── checkpoint.py            # 检查点异常
├── history.py               # 历史管理异常
├── llm.py                   # LLM模块异常
├── llm_wrapper.py           # LLM包装器异常
├── prompt.py                # 提示词异常
├── session_thread.py        # Session-Thread异常
├── state.py                 # 状态管理异常（包含Storage异常重复定义）
├── tool.py                  # 工具异常
├── workflow.py              # 工作流异常
└── repository.py            # ✅ 已迁移到接口层
```

## 详细分析

### 1. **Workflow异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/workflow.py`

**特点**:
- 14个细分异常类 + 1个基类
- 支持error_code体系
- 包含WORKFLOW_EXCEPTION_MAP映射表
- 提供create_workflow_exception工厂函数
- 提供handle_workflow_exception装饰器

**为什么迁移**:
- 工作流是顶级系统组件，异常定义应在接口层
- `src/interfaces/workflow/`已存在接口定义
- Infrastructure组件（执行引擎）只应依赖接口层异常
- 所有层（Service/Adapter/Infrastructure）都需要使用这些异常

**迁移目标**: `src/interfaces/workflow/exceptions.py`

---

### 2. **Tool异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/tool.py`

**特点**:
- 3个异常类（过于简单）
- 缺少error_code支持
- 缺少详细的上下文信息

**为什么迁移**:
- Tool是系统的核心组件，已有`src/interfaces/tool/`接口定义
- Service层的Tool Manager需要使用这些异常
- Infrastructure的Tool执行引擎只应依赖接口层
- 需要增强异常信息（error_code、details等）

**迁移目标**: `src/interfaces/tool/exceptions.py`

**建议增强**:
```python
class ToolError(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class ToolRegistrationError(ToolError):
    """工具注册错误异常"""
    pass

class ToolExecutionError(ToolError):
    """工具执行错误异常"""
    pass

class ToolValidationError(ToolError):
    """工具验证错误异常"""
    pass

class ToolNotFoundError(ToolError):
    """工具未找到异常"""
    pass

class ToolConfigurationError(ToolError):
    """工具配置错误异常"""
    pass
```

---

### 3. **State异常** ⚠️ 需要拆分迁移

**当前位置**: `src/core/common/exceptions/state.py`

**问题**:
- 混合了State异常和Storage异常（重复定义）
- Storage异常已在`src/interfaces/storage/exceptions.py`定义
- 需要拆分处理

**拆分方案**:

**3.1 State异常** → `src/interfaces/state/exceptions.py`
```python
class StateError(Exception):
    """状态管理基础异常"""
    pass

class StateValidationError(StateError):
    """状态验证异常"""
    pass

class StateNotFoundError(StateError):
    """状态未找到异常"""
    pass

class StateTimeoutError(StateError):
    """状态操作超时异常"""
    pass

class StateCapacityError(StateError):
    """状态容量超限异常"""
    pass
```

**3.2 Storage异常** → 保留在`src/interfaces/storage/exceptions.py`（已存在）

**为什么迁移**:
- State是系统核心组件，异常应在接口层
- `src/interfaces/state/`已存在相关接口定义
- 避免异常定义分散

---

### 4. **LLM异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/llm.py`

**特点**:
- 11个细分异常类
- 支持error_code和可重试机制
- 包含原始错误和上下文信息

**为什么迁移**:
- LLM是系统核心组件，异常应在接口层
- `src/interfaces/llm/`已有LLM接口定义
- Service和Infrastructure的LLM实现都需要这些异常
- 避免循环依赖问题

**迁移目标**: `src/interfaces/llm/exceptions.py`

---

### 5. **LLM Wrapper异常** ❌ 应该删除（整合到LLM异常）

**当前位置**: `src/core/common/exceptions/llm_wrapper.py`

**问题**:
- 只有5个简单异常类，功能不完整
- 命名与LLM模块重复（wrapper概念模糊）
- 可以整合到LLM异常体系中

**处理方案**:
- 将这些异常整合到`src/interfaces/llm/exceptions.py`
- 删除llm_wrapper.py
- 在LLM异常中提供wrapper相关的异常子类

---

### 6. **Checkpoint异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/checkpoint.py`

**特点**:
- 4个异常类（简洁）
- 需要增强error_code支持

**为什么迁移**:
- Checkpoint是系统的持久化机制
- `src/interfaces/checkpoint.py`已有接口定义
- Service和Infrastructure都需要使用这些异常

**迁移目标**: `src/interfaces/checkpoint.py`或新增`src/interfaces/checkpoint/exceptions.py`

**建议增强**:
```python
class CheckpointError(Exception):
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}

class CheckpointNotFoundError(CheckpointError):
    pass

class CheckpointStorageError(CheckpointError):
    pass

class CheckpointValidationError(CheckpointError):
    pass

class CheckpointSerializationError(CheckpointError):
    pass

class CheckpointTimeoutError(CheckpointError):
    pass
```

---

### 7. **History异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/history.py`

**特点**:
- 6个异常类
- 支持error_code体系
- 包含to_dict()转换方法
- 细粒度的字段支持（model、pricing_info等）

**为什么迁移**:
- History是系统的查询和统计模块
- `src/interfaces/history.py`已有接口定义
- Service层的History Manager需要这些异常
- 需要在Infrastructure中使用

**迁移目标**: 新增`src/interfaces/history/exceptions.py`或在`src/interfaces/history.py`中定义

---

### 8. **Prompt异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/prompt.py`

**特点**:
- 9个异常类
- 支持error_code体系
- 包含详细的上下文信息
- 覆盖加载、注册、缓存、类型等多个场景

**为什么迁移**:
- Prompt是系统的配置和管理模块
- `src/interfaces/prompts/`已有接口定义
- Service和Adapter都需要使用这些异常

**迁移目标**: `src/interfaces/prompts/exceptions.py`

---

### 9. **Session-Thread异常** ✅ 应该迁移

**当前位置**: `src/core/common/exceptions/session_thread.py`

**特点**:
- 9个异常类
- 基类包含session_id、thread_id、details、cause等字段
- 包含to_dict()转换方法
- 细粒度的错误场景

**为什么迁移**:
- Session和Thread是系统的核心管理模块
- `src/interfaces/sessions/`和`src/interfaces/threads/`已有接口定义
- 需要避免Core层依赖

**迁移目标**: 
- 新增`src/interfaces/sessions/exceptions.py`
- 或在现有会话接口中定义

---

### 10. **Config异常** ❓ 需要特殊处理

**当前位置**: `src/core/common/exceptions/config.py`

**特点**:
- 配置相关异常
- 由ConfigurationError继承

**分析**:
- 配置系统设计文档建议配置异常可能需要特殊处理
- 需要检查现有配置异常的定义位置
- 可能需要在`src/interfaces/configuration.py`中定义

---

## 迁移优先级和建议方案

### Phase 1: 高优先级（立即迁移）✅
1. **Repository异常** → `src/interfaces/repository/exceptions.py` （已完成）
2. **Workflow异常** → `src/interfaces/workflow/exceptions.py`
3. **LLM异常** → `src/interfaces/llm/exceptions.py`
4. **Tool异常** → `src/interfaces/tool/exceptions.py`

### Phase 2: 中优先级（下一步迁移）
1. **State异常** → `src/interfaces/state/exceptions.py`（拆分出Storage异常）
2. **History异常** → `src/interfaces/history/exceptions.py`
3. **Checkpoint异常** → `src/interfaces/checkpoint.py`或新增`checkpoint/exceptions.py`
4. **Prompt异常** → `src/interfaces/prompts/exceptions.py`
5. **Session-Thread异常** → `src/interfaces/sessions/exceptions.py`

### Phase 3: 需要进一步分析
1. **LLM Wrapper异常** → 整合到LLM异常
2. **Config异常** → 需要检查现有配置异常定义

---

## 迁移指导原则

### 1. **一致的异常设计**
所有迁移的异常应遵循统一的设计模式：
```python
class DomainError(Exception):
    """基础异常"""
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
```

### 2. **文件结构**
```
src/interfaces/
├── workflow/
│   ├── exceptions.py      # Workflow异常
│   └── ...
├── tool/
│   ├── exceptions.py      # Tool异常
│   └── ...
├── llm/
│   ├── exceptions.py      # LLM异常
│   └── ...
├── state/
│   ├── exceptions.py      # State异常
│   └── ...
├── checkpoint.py          # Checkpoint接口和异常
├── history.py             # History接口和异常
├── prompts/
│   ├── exceptions.py      # Prompt异常
│   └── ...
└── sessions/
    ├── exceptions.py      # Session异常
    └── ...
```

### 3. **向后兼容性**
Core层通过从接口层re-export来保持向后兼容：
```python
# src/core/common/exceptions/__init__.py
from src.interfaces.workflow import (
    WorkflowError,
    WorkflowExecutionError,
    # ...
)
```

### 4. **删除重复定义**
- Storage异常：保留在`src/interfaces/storage/exceptions.py`，从`src/core/common/exceptions/state.py`删除
- LLM Wrapper异常：整合到LLM异常后删除此文件

---

## 总结

### 需要迁移的异常模块
1. ✅ **Repository** - 已完成
2. ✅ **Workflow** - 高优先级
3. ✅ **Tool** - 高优先级
4. ✅ **LLM** - 高优先级
5. ✅ **State** - 中优先级（拆分）
6. ✅ **History** - 中优先级
7. ✅ **Checkpoint** - 中优先级
8. ✅ **Prompt** - 中优先级
9. ✅ **Session-Thread** - 中优先级
10. ❌ **LLM Wrapper** - 删除（整合到LLM）
11. ❓ **Config** - 需要进一步分析

### 核心原则
- **接口层集中管理**：所有异常定义应集中在接口层
- **避免循环依赖**：Infrastructure组件只依赖接口层
- **统一设计**：所有异常遵循consistent的设计模式
- **向后兼容**：Core层通过re-export保持兼容性

### 预期收益
1. 遵循AGENTS.md架构规范
2. 消除循环依赖风险
3. 提供统一的异常体系
4. 支持error_code追踪
5. 便于Infrastructure实现替换
6. 改善代码组织和可维护性
