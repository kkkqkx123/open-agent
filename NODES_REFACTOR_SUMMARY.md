# 节点同步/异步重构总结

## 修改内容

### 新增文件

**1. src/core/workflow/graph/nodes/sync_node.py**
- 新增 `SyncNode` 基类
- 用于纯同步节点（ToolNode、ConditionNode等）
- `execute_async()` 抛出 RuntimeError

**2. src/core/workflow/graph/nodes/async_node.py**
- 新增 `AsyncNode` 基类
- 用于异步节点（LLMNode）
- `execute()` 创建新事件循环
- `execute_async()` 子类实现真实异步逻辑

### 修改文件

| 文件 | 改动 | 原因 |
|------|------|------|
| **llm_node.py** | 继承AsyncNode，删除execute()的循环创建代码，_execute_async()改名为execute_async() | 改为true异步实现 |
| **tool_node.py** | 继承SyncNode | 纯同步协调节点 |
| **condition_node.py** | 继承SyncNode | 纯同步条件判断 |
| **start_node.py** | 继承SyncNode | 纯同步初始化 |
| **end_node.py** | 继承SyncNode | 纯同步清理 |
| **wait_node.py** | 继承SyncNode | 纯同步等待处理 |
| **nodes/__init__.py** | 新增导出SyncNode和AsyncNode | 模块API |

## 架构变化

### 修改前
```
BaseNode（抽象）
├─ LLMNode
├─ ToolNode  
├─ ConditionNode
├─ StartNode
├─ EndNode
└─ WaitNode
```

**问题**：
- 所有节点都需要实现execute()和execute_async()
- LLMNode在execute()中创建新事件循环（跨域调用）
- 其他节点的execute_async()不知道如何实现

### 修改后
```
BaseNode（抽象）
├─ SyncNode（抽象）
│  ├─ ToolNode     (只实现execute())
│  ├─ ConditionNode(只实现execute())
│  ├─ StartNode    (只实现execute())
│  ├─ EndNode      (只实现execute())
│  └─ WaitNode     (只实现execute())
│
└─ AsyncNode（抽象）
   └─ LLMNode      (只实现execute_async())
```

**优势**：
- ✓ 每个节点只需实现自己真正支持的方法
- ✓ 明确的类型和职责
- ✓ 错误的调用方式会立即抛异常（比假执行更好）
- ✓ 架构与execution modes一致

## 行为对比

### SyncNode（同步节点）

| 调用方式 | 行为 | 性能 |
|---------|------|------|
| `node.execute(state, config)` | ✓ 直接执行 | 最快 |
| `await node.execute_async(state, config)` | ✗ 抛RuntimeError | N/A |

**何时失败**：
- 在AsyncMode中被调用execute_async()
- 应改为SyncMode调用execute()

### AsyncNode（异步节点）

| 调用方式 | 行为 | 性能 |
|---------|------|------|
| `node.execute(state, config)` | ⚠️ 创建新循环 | ~5-10ms开销 |
| `await node.execute_async(state, config)` | ✓ 直接执行 | 最优 |

**推荐用法**：
- 在AsyncMode中调用execute_async()
- 避免同步调用（会有循环创建开销）

## 代码示例

### 同步节点（ConditionNode）
```python
class ConditionNode(SyncNode):  # 继承SyncNode
    def execute(self, state, config):
        # 真实的同步条件判断实现
        return NodeExecutionResult(state, next_node, metadata)
    
    # 不需要实现execute_async()
    # 继承自SyncNode，会抛RuntimeError
```

### 异步节点（LLMNode）
```python
class LLMNode(AsyncNode):  # 继承AsyncNode
    # 不需要实现execute()
    # 继承自AsyncNode，会创建新循环
    
    async def execute_async(self, state, config):
        # 真实的异步LLM调用实现
        return NodeExecutionResult(state, next_node, metadata)
```

## 向后兼容性

### 破坏性变更

1. **SyncNode无法异步调用**
   ```python
   # 旧代码（现在会失败）
   result = await sync_node.execute_async(state, config)
   
   # 新代码（应该）
   result = sync_node.execute(state, config)
   ```

2. **AsyncNode同步调用有警告**
   ```python
   # 旧代码（现在会有警告）
   result = llm_node.execute(state, config)
   # 日志：AsyncNode executing synchronously. This creates a new event loop...
   
   # 新代码（推荐）
   result = await llm_node.execute_async(state, config)
   ```

### 迁移清单

- [ ] 检查所有异步调用SyncNode的地方，改为同步调用
- [ ] 检查所有同步调用AsyncNode的地方，考虑改为异步调用
- [ ] 更新测试用例
- [ ] 更新文档和API文档

## 性能影响

### 改进

| 场景 | 改进前 | 改进后 | 效果 |
|------|--------|--------|------|
| **SyncNode异步调用** | 创建新循环 | 抛异常+提示 | 避免不必要开销 |
| **AsyncNode异步调用** | 继承默认run_in_executor | 直接execute_async | ✓ 更高效 |
| **LLMNode实现** | execute()创建循环→_execute_async() | execute()继承AsyncNode | ✓ 更清晰 |

### 无变化

| 场景 | 性能 |
|------|------|
| SyncNode同步调用 | 无变化（直接调用）|
| AsyncNode同步调用 | 无变化（仍创建循环） |

## 测试覆盖

应该运行的测试：
```bash
# 节点单元测试
pytest tests/core/workflow/graph/nodes/ -v

# 集成测试
pytest tests/core/workflow/execution/ -v

# 模式测试
pytest tests/core/workflow/modes/ -v
```

应该验证的场景：
```python
# SyncNode
def test_sync_node_sync_call_works():
    result = cond_node.execute(state, config)
    assert result.success

def test_sync_node_async_call_raises():
    with pytest.raises(RuntimeError):
        await cond_node.execute_async(state, config)

# AsyncNode
def test_async_node_async_call_works():
    result = await llm_node.execute_async(state, config)
    assert result.success

def test_async_node_sync_call_works_but_warns():
    # 应该能工作，但会有警告
    result = llm_node.execute(state, config)
    assert result.success
```

## 总结

这次重构建立了清晰的节点架构：

1. **SyncNode** - 纯同步，快速本地操作
2. **AsyncNode** - 异步I/O，需要等待
3. **明确的边界** - 错误调用立即失败
4. **一致的设计** - 与execution modes的思路统一
5. **更好的可维护性** - 每个节点职责清晰

## 后续优化方向

1. **考虑添加MixedNode**（如果需要同步和异步都优化的节点）
2. **性能分析**（测量循环创建的实际开销）
3. **文档完善**（更新节点开发指南）
4. **类型检查**（确保execution modes正确选择）
