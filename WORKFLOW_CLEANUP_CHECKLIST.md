# 工作流模块清理清单

## 已迁移到 Core 层的模块

### Configuration 模块
- [x] `src/services/workflow/configuration/config_manager.py` → `src/core/workflow/config/config_manager.py`
- [x] `src/services/workflow/configuration/node_config_loader.py` → `src/core/workflow/config/node_config_loader.py`

### Execution 模块
- [x] `src/services/workflow/execution/async_executor.py` → `src/core/workflow/execution/async_executor.py`
- [x] `src/services/workflow/execution/batch_executor.py` → `src/core/workflow/execution/batch_executor.py`
- [x] `src/services/workflowexecution/collaboration_executor.py` → `src/core/workflow/execution/collaboration_executor.py`
- [x] `src/services/workflow/execution/retry_executor.py` → `src/core/workflow/execution/retry_executor.py`
- [x] `src/services/workflow/execution/runner.py` → `src/core/workflow/execution/runner.py`

### Loading 模块
- [x] `src/services/workflow/loading/loader_service.py` → `src/core/workflow/loading/loader_service.py`

### Orchestration 模块
- [x] `src/services/workflow/orchestration/orchestrator.py` → `src/core/workflow/orchestration/orchestrator.py`
- [x] `src/services/workflow/orchestration/manager.py` → `src/core/workflow/orchestration/manager.py`

### Registry 模块
- [x] `src/services/workflow/registry/registry.py` → `src/core/workflow/registry/registry.py`
- [x] `src/services/workflow/registry/registry_service.py` → `src/core/workflow/registry/registry_service.py`
- [x] `src/services/workflow/function_registry.py` → `src/core/workflow/registry/function_registry.py`
- [x] `src/services/workflow/graph_cache.py` → `src/core/workflow/registry/graph_cache.py`

## 需要删除的 Services 层文件

### Configuration 模块
- [ ] `src/services/workflow/configuration/config_manager.py`
- [ ] `src/services/workflow/configuration/node_config_loader.py`

### Execution 模块
- [ ] `src/services/workflow/execution/async_executor.py`
- [ ] `src/services/workflow/execution/batch_executor.py`
- [ ] `src/services/workflow/execution/collaboration_executor.py`
- [ ] `src/services/workflow/execution/retry_executor.py`
- [ ] `src/services/workflow/execution/runner.py`
- [ ] `src/services/workflow/execution/executor.py`

### Loading 模块
- [ ] `src/services/workflow/loading/loader_service.py`

### Orchestration 模块
- [ ] `src/services/workflow/orchestration/orchestrator.py`
- [ ] `src/services/workflow/orchestration/manager.py`

### Registry 模块
- [ ] `src/services/workflow/registry/registry.py`
- [ ] `src/services/workflow/registry/registry_service.py`

### 根目录文件
- [ ] `src/services/workflow/function_registry.py`
- [ ] `src/services/workflow/graph_cache.py`
- [ ] `src/services/workflow/interfaces.py`
- [ ] `src/services/workflow/state_converter.py`

## 需要更新的导入引用

### 更新 Core 层导入
- [x] 更新 `src/core/workflow/config/__init__.py`
- [x] 更新 `src/core/workflow/execution/__init__.py`
- [x] 更新 `src/core/workflow/loading/__init__.py`
- [x] 更新 `src/core/workflow/orchestration/__init__.py`
- [x] 更新 `src/core/workflow/registry/__init__.py`

### 更新 Services 层导入
- [ ] 更新 `src/services/workflow/__init__.py`
- [ ] 更新 `src/services/workflow/di_config.py`
- [ ] 更新 `src/services/workflow/execution/executor.py`
- [ ] 更新 `src/services/workflow/orchestration/manager.py`
- [ ] 更新 `src/services/workflow/registry/registry.py`

## 需要修复的导入问题

### Core 层导入修复
- [ ] 修复 `src/core/workflow/orchestration/manager.py` 中的 `WorkflowExecutorService` 导入
- [ ] 修复 `src/core/workflow/execution/async_executor.py` 中的依赖导入
- [ ] 修复 `src/core/workflow/execution/batch_executor.py` 中的依赖导入
- [ ] 修复 `src/core/workflow/execution/retry_executor.py` 中的 ABC 导入
- [ ] 修复 `src/core/workflow/execution/collaboration_executor.py` 中的 ABC 导入
- [ ] 修复 `src/core/workflow/loading/loader_service.py` 中的依赖导入
- [ ] 修复 `src/core/workflow/registry/function_registry.py` 中的 ABC 导入
- [ ] 修复 `src/core/workflow/registry/graph_cache.py` 中的 ABC 导入

### Services 层导入修复
- [ ] 更新 `src/services/workflow/execution/executor.py` 中的导入路径
- [ ] 更新 `src/services/workflow/orchestration/manager.py` 中的导入路径
- [ ] 更新 `src/services/workflow/registry/registry.py` 中的导入路径

## 验证步骤

1. 检查所有 Core 层模块的导入是否正确
2. 检查 Services 层模块的导入是否指向 Core 层
3. 运行测试确保功能完整性
4. 检查是否有遗漏的导入或文件

## 注意事项

1. 保留 `src/services/workflow/__init__.py` 和 `src/services/workflow/di_config.py` 作为服务层的入口点
2. 确保所有依赖关系正确更新
3. 测试每个模块的功能是否正常工作
4. 备份重要文件后再进行删除操作