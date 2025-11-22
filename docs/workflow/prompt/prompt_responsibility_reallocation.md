# 提示词模块职责重新划分

## 问题分析

在重构过程中发现以下冗余问题：

### 1. 配置预处理重复
- `builder_service.py` 的 `_preprocess_config_async`
- `loader_service.py` 的 `_preprocess_prompt_config_async`
- 两者都在处理节点配置中的提示词内容

### 2. 验证逻辑重复
- `builder_service.py` 的 `_validate_prompt_config`
- `workflow_validator.py` 的 `_validate_prompt_config`
- `llm_node.py` 的 `validate_prompt_configuration`

### 3. 上下文处理重复
- `orchestrator.py` 的 `_prepare_execution_config_async`
- `prompt_service.py` 的 `_prepare_node_context`
- 两者都在准备类似的上下文信息

## 重新划分的职责

### 1. 核心提示词服务 (`prompt_service.py`)

**职责**：统一的提示词处理中心

**新增方法**：
```python
# 工作流配置预处理
async def preprocess_workflow_config(self, config: Dict[str, Any]) -> Dict[str, Any]

# 工作流节点配置
async def configure_workflow_nodes(self, graph, config: Dict[str, Any]) -> None

# 工作流结构验证
async def validate_workflow_structure(self, config: Dict[str, Any]) -> List[str]

# 执行上下文准备
async def prepare_execution_context(self, config, workflow_id: str, initial_state) -> Dict[str, Any]

# 上下文准备工具
def _prepare_workflow_context(self, config: Dict[str, Any], node_id: Optional[str]) -> Dict[str, Any]

# 节点配置查找
def _find_node_config(self, node_id: str, config: Dict[str, Any]) -> Optional[Dict[str, Any]]
```

### 2. 构建服务 (`builder_service.py`)

**职责**：工作流构建，委托提示词处理给核心服务

**简化后的方法**：
```python
def _preprocess_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
    # 委托给 prompt_service.preprocess_workflow_config

def _validate_prompt_config(self, config: Dict[str, Any]) -> List[str]:
    # 委托给 prompt_service.validate_prompt_configuration

async def _configure_node_prompts(self, graph, config: Dict[str, Any]):
    # 委托给 prompt_service.configure_workflow_nodes
```

### 3. 加载服务 (`loader_service.py`)

**职责**：工作流加载，委托提示词预处理给核心服务

**简化后的方法**：
```python
def _preprocess_prompt_config(self, config: GraphConfig) -> GraphConfig:
    # 委托给 prompt_service.preprocess_workflow_config
```

### 4. 验证器 (`workflow_validator.py`)

**职责**：工作流验证，委托提示词验证给核心服务

**增强后的方法**：
```python
def _validate_prompt_config(self, config_data: Dict[str, Any], config_path: str):
    # 基本配置验证：委托给 prompt_service.validate_prompt_configuration
    # 结构验证：委托给 prompt_service.validate_workflow_structure
```

### 5. 编排器 (`orchestrator.py`)

**职责**：工作流编排，委托上下文准备给核心服务

**简化后的方法**：
```python
def _prepare_execution_config(self, config, workflow_id: str, initial_state):
    # 委托给 prompt_service.prepare_execution_context
```

## 新架构的优势

### 1. 单一职责原则
- **核心服务**：专注于提示词处理逻辑
- **各模块**：专注于自己的核心业务，委托提示词处理

### 2. 消除重复代码
- 所有提示词处理逻辑集中在 `prompt_service.py`
- 其他模块通过委托模式复用功能

### 3. 统一的接口
- 所有模块使用相同的提示词处理接口
- 保证处理逻辑的一致性

### 4. 易于维护
- 提示词处理逻辑的修改只需在一个地方进行
- 新功能的添加集中在核心服务

## 数据流图

```
配置输入
    ↓
Builder Service → Loader Service → Validator → Orchestrator
    ↓                ↓              ↓           ↓
Prompt Service ← Prompt Service ← Prompt Service ← Prompt Service
    ↓                ↓              ↓           ↓
处理后的配置/验证结果/上下文
```

## 使用示例

### 1. 构建工作流
```python
builder = WorkflowBuilderService()
workflow = builder.build_workflow(config)
# 内部调用：prompt_service.preprocess_workflow_config()
```

### 2. 加载工作流
```python
loader = UniversalLoaderService()
workflow = loader.load_from_file(config_path)
# 内部调用：prompt_service.preprocess_workflow_config()
```

### 3. 验证配置
```python
validator = WorkflowValidator(prompt_service)
issues = validator.validate_config_file(config_path)
# 内部调用：prompt_service.validate_prompt_configuration()
#         prompt_service.validate_workflow_structure()
```

### 4. 执行工作流
```python
orchestrator = WorkflowOrchestrator(prompt_service=prompt_service)
result = orchestrator.execute_workflow(workflow_id, initial_state)
# 内部调用：prompt_service.prepare_execution_context()
```

## 迁移指南

### 1. 从重复代码迁移

**旧代码**：
```python
# 在多个地方重复的预处理逻辑
async def _preprocess_config_async(self, config):
    # 重复的提示词处理逻辑
    for node in config.get("nodes", []):
        # 处理逻辑...
```

**新代码**：
```python
# 统一委托给核心服务
def _preprocess_config(self, config):
    return await self._prompt_service.preprocess_workflow_config(config)
```

### 2. 从分散验证迁移

**旧代码**：
```python
# 在多个地方重复的验证逻辑
def _validate_prompt_config(self, config):
    # 重复的验证逻辑...
```

**新代码**：
```python
# 统一委托给核心服务
def _validate_prompt_config(self, config):
    return await self._prompt_service.validate_prompt_configuration(config)
```

## 性能优化

### 1. 缓存集中化
- 所有缓存逻辑集中在 `prompt_service.py`
- 避免多处缓存的重复和不一致

### 2. 批量处理
- 支持批量处理多个配置
- 减少重复的初始化开销

### 3. 懒加载
- 按需加载提示词服务
- 避免不必要的资源消耗

## 测试策略

### 1. 单元测试
- `prompt_service.py` 的完整测试覆盖
- 各模块的委托逻辑测试

### 2. 集成测试
- 端到端的工作流处理测试
- 各模块协作的集成测试

### 3. 性能测试
- 大量配置的处理性能测试
- 缓存效果验证测试

## 总结

通过重新划分职责，我们实现了：

1. **消除冗余**：移除了重复的提示词处理逻辑
2. **明确职责**：每个模块专注于自己的核心功能
3. **统一接口**：所有提示词处理通过统一的服务接口
4. **易于维护**：提示词逻辑集中管理，便于修改和扩展

新的架构更加清晰、高效，符合单一职责原则和DRY原则。