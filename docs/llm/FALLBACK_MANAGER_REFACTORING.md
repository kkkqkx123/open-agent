# FallbackManager 架构重构总结

## 问题分析

重构前存在的设计缺陷：

1. **职责划分不清**：Core 层的 `WrapperFallbackManager` 包含了完整的业务编排逻辑，而 Services 层的 `FallbackManager` 只是一个简单的代理，没有增加任何价值

2. **违反分层原则**：Services 层应该负责业务编排，但实现却被放在了 Core 层

3. **代码重复**：Core 层包含了本应由 Services 层处理的编排逻辑

## 重构方案

### Core 层职责（`src/core/llm/wrappers/fallback_manager.py`）
Core 层现在**只定义核心算法和策略**：

- **`GroupBasedFallbackStrategy`**：基于任务组的降级策略算法
  - 解析组引用字符串
  - 判断错误类型（速率限制、失败次数限制）
  - 获取降级目标（同一层级、下一层级、其他组）
  - 记录失败和成功状态

- **`PollingPoolFallbackStrategy`**：基于轮询池的降级策略
  - 轮询池直接轮换，不需要外部降级逻辑

- **`DefaultFallbackLogger`**：日志记录器
  - 记录降级尝试、成功和失败事件

**移除了：** `WrapperFallbackManager` 类（完整的执行编排逻辑）

### Services 层职责（`src/services/llm/fallback_manager.py`）
Services 层现在实现**真正的业务编排**：

- **调用 Core 层的策略**：使用 `GroupBasedFallbackStrategy` 和 `PollingPoolFallbackStrategy` 获取降级目标

- **管理执行流程**：
  1. 判断是任务组还是轮询池
  2. 调用相应的执行方法
  3. 处理具体的 LLM 调用
  4. 根据结果决定是否进行降级重试

- **记录统计和监控**：
  - 跟踪总请求数、成功数、失败数
  - 统计组降级和池降级的次数

- **错误处理和日志**：
  - 调用日志记录器记录关键事件
  - 转换和包装异常

## 分层对比

| 层级 | 重构前 | 重构后 |
|------|--------|--------|
| **Core** | 完整的编排逻辑 + 策略算法 | 只有策略算法 |
| **Services** | 简单代理 | 真实的编排逻辑、统计、日志 |

## 代码结构

### Core 层（算法层）
```python
class GroupBasedFallbackStrategy:
    """策略算法：获取降级目标的逻辑"""
    def get_fallback_targets(self, primary_target, error) -> List[str]
    def record_failure(self, target, error)
    def record_success(self, target)

class PollingPoolFallbackStrategy:
    """轮询池策略"""
    def get_fallback_targets(self, primary_target, error) -> List[str]

class DefaultFallbackLogger:
    """日志记录"""
    def log_fallback_attempt(...)
    def log_fallback_success(...)
    def log_fallback_failure(...)
```

### Services 层（业务编排层）
```python
class FallbackManager(IFallbackManager):
    """完整的编排和执行逻辑"""
    
    async def execute_with_fallback(...):
        # 编排流程：判断类型 -> 调用执行方法 -> 处理错误
        
    async def _execute_with_group_fallback(...):
        # 1. 获取目标模型
        # 2. 创建客户端执行
        # 3. 如果失败，使用 Core 策略获取降级目标
        # 4. 重复直到成功或达到限制
        
    async def _execute_with_pool_fallback(...):
        # 使用轮询池执行，轮询池内部处理轮换
```

## 关键改进

### 1. 清晰的职责分离
- Core 层：**算法定义** - 如何获取降级目标
- Services 层：**业务编排** - 如何使用降级策略执行调用

### 2. 代码复用性提高
Services 层充分利用 Core 层的策略类：
```python
self._group_strategy = GroupBasedFallbackStrategy(task_group_manager)
fallback_targets = self._group_strategy.get_fallback_targets(...)
self._group_strategy.record_failure(...)
```

### 3. 测试性更好
- Core 层策略可独立测试
- Services 层编排可模拟 Core 层的策略进行测试

### 4. 更易维护
- 修改降级算法 → 修改 Core 层的策略类
- 修改执行流程 → 修改 Services 层的编排逻辑
- 修改日志 → 修改 Services 层的日志调用

## 导出变化

### `src/services/llm/__init__.py`
```python
# 旧：
from ...core.llm.wrappers.fallback_manager import WrapperFallbackManager
__all__ = ["WrapperFallbackManager", ...]

# 新：
from .fallback_manager import FallbackManager
__all__ = ["FallbackManager", ...]
```

所有调用方现在应该使用 `src.services.llm.FallbackManager` 而不是 Core 层的 `WrapperFallbackManager`。

## 兼容性

- **IFallbackManager 接口**：保持不变，所有公共方法签名一致
- **行为**：降级逻辑完全相同，只是代码位置重新组织
- **性能**：无性能影响

## 下一步建议

1. 更新所有文档中对架构的描述
2. 在 di_config.py 中检查 FallbackManager 的依赖注入配置
3. 编写单元测试验证策略类的行为
4. 编写集成测试验证编排逻辑
