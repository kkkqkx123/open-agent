基于对 `src/core/workflow/entities.py` 的分析，我重新评估了 Core 层的职责：

**Core 层应该仅保留纯实体定义**：
参考 `entities.py` 的模式，Core 层应该只包含：
1. **纯领域数据结构**：GraphConfig、NodeConfig、EdgeConfig 等
2. **业务方法**：如 get_node_count()、get_edge_count() 等
3. **简单序列化**：保留 to_dict() 和 from_dict() 方法（参考 entities.py 模式）
4. **移除所有配置处理逻辑**：验证、加载、转换等

**Schema Generator 应该在 Infrastructure 层实现**：
- `src/core/workflow/config/schema_generator.py` 是技术实现组件
- 功能：从配置文件动态生成 JSON Schema
- 职责：配置验证和模式生成
- 应迁移至 `src/infrastructure/config/schema/workflow_schema_generator.py`

**最终重构方案**：
1. **Core 层**：将图配置实体移至 `entities.py` 或新建 `graph_entities.py`，只保留纯业务逻辑
2. **Infrastructure 层**：新增 `converters/` 目录和 `workflow_schema_generator.py`
3. **适配器**：在 Core 层创建 `GraphConfigAdapter` 桥接两层
4. **保留**：`builder_config.py`（构建器配置属于业务逻辑）

这样的重构使 Core 层专注于业务逻辑，Infrastructure 层专注于技术实现，符合清晰的分层架构原则。