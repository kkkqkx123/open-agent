# 状态管理器重构方案

## 1. 背景与问题分析

当前代码库中存在两个状态管理器文件：
- `manager.py` - 包含 `EnhancedStateManager`，实际提供冲突检测和解决功能
- `optimized_manager.py` - 包含 `OptimizedStateManager`，提供性能优化功能

### 主要问题
1. **职责混淆**：`EnhancedStateManager` 继承自 `OptimizedStateManager`，但两者的职责边界不清晰
2. **命名误导**：文件名和类名包含 "optimized"、"enhanced" 等描述性词汇，无法准确反映真实职责
3. **接口缺失**：没有统一的状态管理器接口，导致扩展困难
4. **依赖关系复杂**：`EnhancedStateManager` 直接依赖 `OptimizedStateManager`，违反了依赖倒置原则

## 2. 重构目标

1. **清晰职责划分**：将不同功能按单一职责原则分离
2. **合理命名**：文件名和类名准确反映其真实职责
3. **接口统一**：定义标准的状态管理器接口
4. **可扩展性**：支持功能模块的灵活组合

## 3. 新架构设计

### 3.1 文件结构

```
src/infrastructure/graph/states/
├── interface.py              # 状态管理器接口定义
├── base_manager.py           # 基础状态管理器
├── pooling_manager.py        # 对象池管理功能
├── conflict_manager.py       # 冲突检测与解决功能
├── version_manager.py        # 状态版本管理功能
└── composite_manager.py      # 组合完整功能的管理器
```

### 3.2 接口定义

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

class IStateManager(ABC):
    """状态管理器接口"""
    
    @abstractmethod
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态"""
        pass
    
    @abstractmethod
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态"""
        pass
    
    @abstractmethod
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态"""
        pass
    
    @abstractmethod
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异"""
        pass
```

### 3.3 基础管理器

```python
class BaseStateManager(IStateManager):
    """基础状态管理器，提供基本的状态管理功能"""
    
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def create_state(self, state_id: str, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """创建状态"""
        state_copy = initial_state.copy()
        self._states[state_id] = state_copy
        return state_copy
    
    def update_state(self, state_id: str, current_state: Dict[str, Any], updates: Dict[str, Any]) -> Dict[str, Any]:
        """更新状态"""
        new_state = current_state.copy()
        new_state.update(updates)
        self._states[state_id] = new_state
        return new_state
    
    def get_state(self, state_id: str) -> Optional[Dict[str, Any]]:
        """获取状态"""
        return self._states.get(state_id)
    
    def compare_states(self, state1: Dict[str, Any], state2: Dict[str, Any]) -> Dict[str, Any]:
        """比较两个状态的差异"""
        differences = {}
        all_keys = set(state1.keys()) | set(state2.keys())
        
        for key in all_keys:
            value1 = state1.get(key)
            value2 = state2.get(key)
            
            if value1 != value2:
                differences[key] = {
                    "old_value": value1,
                    "new_value": value2,
                    "type_changed": type(value1) != type(value2)
                }
        
        return differences
```

### 3.4 对象池管理器

```python
class PoolingStateManager(BaseStateManager):
    """对象池状态管理器，提供性能优化功能"""
    
    def __init__(self, enable_pooling: bool = True, max_pool_size: int = 100):
        super().__init__()
        self._enable_pooling = enable_pooling
        self._max_pool_size = max_pool_size
        self._state_pool: Dict[str, Dict[str, Any]] = {}
        # 其他性能优化功能...
```

### 3.5 冲突管理器

```python
class ConflictStateManager(BaseStateManager):
    """冲突检测与解决状态管理器"""
    
    def __init__(self, conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS):
        super().__init__()
        self.conflict_resolver = StateConflictResolver(conflict_strategy)
        # 其他冲突管理功能...
```

### 3.6 版本管理器

```python
class VersionStateManager(BaseStateManager):
    """状态版本管理器"""
    
    def __init__(self):
        super().__init__()
        self._state_versions: Dict[str, Dict[str, Any]] = {}
        # 版本管理相关功能...
```

### 3.7 组合管理器

```python
class CompositeStateManager(IStateManager):
    """组合状态管理器，整合所有功能"""
    
    def __init__(
        self,
        enable_pooling: bool = True,
        max_pool_size: int = 100,
        enable_diff_tracking: bool = True,
        conflict_strategy: ConflictResolutionStrategy = ConflictResolutionStrategy.LAST_WRITE_WINS
    ):
        self._pooling_manager = PoolingStateManager(enable_pooling, max_pool_size)
        self._conflict_manager = ConflictStateManager(conflict_strategy)
        self._version_manager = VersionStateManager()
        # 其他功能模块...
```

## 4. 重构步骤

### 步骤1：创建接口定义
- 创建 `interface.py` 文件，定义 `IStateManager` 接口

### 步骤2：重构基础功能
- 创建 `base_manager.py`，提取公共功能
- 保持向后兼容性

### 步骤3：分离功能模块
- 将对象池功能分离到 `pooling_manager.py`
- 将冲突管理功能分离到 `conflict_manager.py`
- 将版本管理功能分离到 `version_manager.py`

### 步骤4：创建组合管理器
- 创建 `composite_manager.py`，整合所有功能
- 提供与原 `EnhancedStateManager` 兼容的接口

### 步骤5：更新依赖关系
- 修改所有依赖状态管理器的代码
- 确保向后兼容性

### 步骤6：测试验证
- 运行所有相关测试
- 验证功能完整性
- 验证性能表现

## 5. 迁移策略

### 5.1 向后兼容
- 保留原类名作为别名，指向新的组合管理器
- 提供迁移指南

### 5.2 逐步迁移
- 先创建新结构
- 逐步替换旧实现
- 最后删除旧文件

## 6. 预期收益

1. **职责清晰**：每个模块职责明确，易于维护
2. **可扩展性**：支持新功能的灵活添加
3. **可测试性**：独立模块易于单元测试
4. **性能优化**：模块化设计支持更精细的性能调优
5. **代码复用**：基础功能可在不同场景复用