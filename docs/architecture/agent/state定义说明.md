应当使用 src/domain/agent/state.py 中的域层状态定义，并使用 src/infrastructure/graph/adapters/ 中的适配器进行状态转换

旧的agent定义已弃用，统一基于doamin/agent中的state，使用适配器转换。参考文档：
docs\architecture\agent\state-definition-conflict-analysis.md
docs\architecture\agent\state定义说明.md

graph中的使用：
1. **TypedDict的正确使用**: `AgentState` 继承自 `BaseGraphState(TypedDict)`，应该作为字典使用，但需要遵循TypedDict的类型约束
2. **metadata字段的用途**: `BaseGraphState` 已经定义了 `metadata: dict[str, Any]` 字段，这是存储自定义数据的正确位置
3. **类型转换的必要性**: 将TypedDict转换为普通字典虽然解决了类型问题，但不是最佳实践