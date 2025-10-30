## Hook代码逻辑具体实现位置分析

基于对代码库的全面分析，hook系统的代码逻辑在以下位置实现：

### 1. 核心接口定义 ([`src/infrastructure/graph/hooks/interfaces.py`](src/infrastructure/graph/hooks/interfaces.py))
- **Hook接口** ([`INodeHook`](src/infrastructure/graph/hooks/interfaces.py:65))：定义Hook的基本行为
- **Hook管理器接口** ([`IHookManager`](src/infrastructure/graph/hooks/interfaces.py:197))：管理Hook的注册和执行
- **Hook执行服务接口** ([`IHookExecutionService`](src/infrastructure/graph/hooks/interfaces.py:153))：提供执行计数和性能统计
- **Hook配置加载器接口** ([`IHookConfigLoader`](src/infrastructure/graph/hooks/interfaces.py:302))：加载Hook配置

### 2. 配置管理 ([`src/infrastructure/graph/hooks/config.py`](src/infrastructure/graph/hooks/config.py))
- **Hook配置模型** ([`HookConfig`](src/infrastructure/graph/hooks/config.py:21))：包含优先级等配置属性
- **配置合并逻辑** ([`merge_hook_configs`](src/infrastructure/graph/hooks/config.py:216))：合并全局和节点配置并按优先级排序

### 3. Hook管理器实现 ([`src/infrastructure/graph/hooks/manager.py`](src/infrastructure/graph/hooks/manager.py))
- **Hook注册和管理** ([`NodeHookManager`](src/infrastructure/graph/hooks/manager.py:76))：管理Hook的生命周期
- **Hook执行逻辑** ([`execute_hooks`](src/infrastructure/graph/hooks/manager.py:157))：按优先级执行Hook
- **配置加载** ([`HookConfigLoader`](src/infrastructure/graph/hooks/manager.py:25))：从YAML文件加载配置

### 4. 内置Hook实现 ([`src/infrastructure/graph/hooks/builtin.py`](src/infrastructure/graph/hooks/builtin.py))
- **死循环检测Hook** ([`DeadLoopDetectionHook`](src/infrastructure/graph/hooks/builtin.py:18))：检测和防止死循环
- **性能监控Hook** ([`PerformanceMonitoringHook`](src/infrastructure/graph/hooks/builtin.py:84))：监控执行时间和性能
- **错误恢复Hook** ([`ErrorRecoveryHook`](src/infrastructure/graph/hooks/builtin.py:175))：错误处理和重试机制
- **日志Hook** ([`LoggingHook`](src/infrastructure/graph/hooks/builtin.py:292))：结构化日志记录
- **指标收集Hook** ([`MetricsCollectionHook`](src/infrastructure/graph/hooks/builtin.py:406))：收集性能指标

### 5. 节点集成 ([`src/infrastructure/graph/hooks/decorators.py`](src/infrastructure/graph/hooks/decorators.py))
- **装饰器集成** ([`with_hooks`](src/infrastructure/graph/hooks/decorators.py:14))：通过装饰器为节点添加Hook支持
- **Hookable节点基类** ([`HookableNode`](src/infrastructure/graph/hooks/decorators.py:172))：支持Hook的节点基类

### 6. Hookable节点包装器 ([`src/infrastructure/graph/nodes/hookable_node.py`](src/infrastructure/graph/nodes/hookable_node.py))
- **节点包装器** ([`make_node_hookable`](src/infrastructure/graph/nodes/hookable_node.py:138))：将普通节点转换为支持Hook的节点
- **Hook执行流程** ([`HookableNode.execute`](src/infrastructure/graph/nodes/hookable_node.py:31))：完整的Hook执行流程

### 7. Graph构建器集成 ([`src/infrastructure/graph/hook_aware_builder.py`](src/infrastructure/graph/hook_aware_builder.py))
- **Hook感知构建器** ([`HookAwareGraphBuilder`](src/infrastructure/graph/hook_aware_builder.py:26))：构建支持Hook的Graph
- **配置加载时机** ([`_get_node_function`](src/infrastructure/graph/hook_aware_builder.py:65))：在构建时为节点加载Hook配置

### 8. Hook与Trigger协调 ([`src/infrastructure/graph/hooks/trigger_coordinator.py`](src/infrastructure/graph/hooks/trigger_coordinator.py))
- **功能协调** ([`HookTriggerCoordinator`](src/infrastructure/graph/hooks/trigger_coordinator.py:18))：协调Hook和Trigger系统的执行
- **优先级功能过滤** ([`_filter_hooks_for_coordination`](src/infrastructure/graph/hooks/trigger_coordinator.py:198))：避免功能重复

### 9. 配置文件 ([`configs/hooks/`](configs/hooks/))
- **全局Hook配置** ([`global_hooks.yaml`](configs/hooks/global_hooks.yaml))：适用于所有节点的Hook
- **节点特定Hook配置** ([`agent_execution_node_hooks.yaml`](configs/hooks/agent_execution_node_hooks.yaml)等)：特定节点的Hook配置

### 执行流程总结
1. **配置加载**：从YAML文件加载Hook配置
2. **配置合并**：合并全局和节点配置，按优先级排序
3. **Hook注册**：创建Hook实例并注册到管理器
4. **节点包装**：将普通节点包装为支持Hook的节点
5. **Hook执行**：在节点执行前后按优先级执行Hook
6. **结果处理**：应用Hook的执行结果到节点执行流程

Hook系统的代码逻辑完整实现了从配置管理到实际执行的完整流程，支持灵活的优先级控制和功能扩展。