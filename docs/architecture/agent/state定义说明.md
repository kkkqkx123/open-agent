应当使用 src/domain/agent/state.py 中的域层状态定义，并使用 src/infrastructure/graph/adapters/ 中的适配器进行状态转换

旧的agent定义已弃用，统一基于doamin/agent中的state，使用适配器转换。参考文档：
docs\architecture\agent\state-definition-conflict-analysis.md
docs\architecture\agent\state定义说明.md