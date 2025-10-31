# 通用工作流配置加载器使用指南

## 概述

通用工作流配置加载器是一个强大的工具，旨在简化工作流的加载、配置和执行过程。它提供了统一的接口来管理节点函数和条件函数，自动处理状态初始化，并支持多种执行模式。

## 核心特性

- **统一配置加载**：从YAML文件或字典加载工作流配置
- **函数注册管理**：动态注册和管理节点函数、条件函数
- **自动状态初始化**：根据配置自动创建初始状态
- **配置验证**：全面的配置验证和错误报告
- **多种执行模式**：同步、异步、流式执行
- **批量处理**：支持批量执行多个工作流
- **错误处理**：完善的错误处理和重试机制

## 快速开始

### 基础用法

```python
from src.application.workflow.universal_loader import UniversalWorkflowLoader, FunctionType

# 创建加载器
loader = UniversalWorkflowLoader()

# 注册自定义函数
def my_condition(state) -> str:
    return "continue" if not state.get("complete") else "end"

loader.register_function("my_condition", my_condition, FunctionType.CONDITION_FUNCTION)

# 加载工作流
workflow = loader.load_from_file("configs/workflows/my_workflow.yaml")

# 运行工作流
result = workflow.run({"input": "Hello, World!"})
print(f"结果: {result}")
```

### 使用工作流运行器

```python
from src.application.workflow.runner import WorkflowRunner

# 创建运行器
runner = WorkflowRunner()

# 注册函数
runner.loader.register_function("my_condition", my_condition, FunctionType.CONDITION_FUNCTION)

# 运行工作流
result = runner.run_workflow("configs/workflows/my_workflow.yaml", {"input": "Hello"})
if result.success:
    print(f"执行成功: {result.result}")
else:
    print(f"执行失败: {result.error}")
```

### 便捷函数

```python
from src.application.workflow.runner import run_workflow

# 一行代码运行工作流
result = run_workflow("configs/workflows/my_workflow.yaml", {"input": "Hello"})
```

## 详细使用指南

### 1. 函数注册

#### 注册节点函数

```python
def my_node_function(state) -> Dict[str, Any]:
    """自定义节点函数"""
    return {"result": "处理完成", "timestamp": time.time()}

loader.register_function("my_node", my_node_function, FunctionType.NODE_FUNCTION)
```

#### 注册条件函数

```python
def my_router_function(state) -> str:
    """自定义条件函数"""
    if state.get("error"):
        return "error_handler"
    elif state.get("complete"):
        return "end"
    else:
        return "continue"

loader.register_function("my_router", my_router_function, FunctionType.CONDITION_FUNCTION)
```

#### 从模块批量注册

```python
# 从模块自动发现并注册函数
discovered = loader.register_functions_from_module("src.custom.functions")
print(f"发现函数: {discovered}")
```

### 2. 配置文件格式

#### 基本配置结构

```yaml
name: my_workflow
description: 我的工作流
version: 1.0

state_schema:
  name: MyWorkflowState
  fields:
    messages:
      type: List[dict]
      default: []
    input:
      type: str
      default: ""
    result:
      type: str
      default: ""

nodes:
  start_node:
    type: llm_node
    config:
      system_prompt: "你是一个AI助手"
      max_tokens: 1000

  process_node:
    type: my_node
    config:
      processing_mode: "fast"

edges:
  - from: start_node
    to: process_node
    type: simple

entry_point: start_node
```

#### 函数注册配置

```yaml
function_registrations:
  nodes:
    my_node: "src.custom.nodes.my_node_function"
    analysis_node: "src.custom.nodes.analysis"
  
  conditions:
    my_router: "src.custom.conditions.my_router"
    plan_execute_router: "src.custom.conditions.plan_execute"
  
  auto_discovery:
    enabled: true
    module_paths:
      - "src.workflow.nodes"
      - "src.workflow.conditions"
```

#### 状态模板配置

```yaml
state_templates:
  base_state:
    messages: []
    tool_calls: []
    iteration_count: 0
    max_iterations: 10

  plan_execute_state:
    inherits_from: "base_state"
    context:
      current_plan: []
      current_step_index: 0
      plan_completed: false

# 使用状态模板
state_template: "plan_execute_state"
state_overrides:
  max_iterations: 15
```

### 3. 执行模式

#### 同步执行

```python
# 基本同步执行
result = workflow.run({"input": "数据"})

# 带配置的执行
result = workflow.run(
    {"input": "数据"},
    config={"recursion_limit": 20}
)
```

#### 异步执行

```python
import asyncio

async def run_async():
    result = await workflow.run_async({"input": "数据"})
    return result

# 运行异步函数
result = asyncio.run(run_async())
```

#### 流式执行

```python
# 流式执行，获取中间结果
for chunk in workflow.stream({"input": "数据"}):
    print(f"中间结果: {chunk}")
```

#### 批量执行

```python
# 批量执行多个工作流
config_paths = [
    "configs/workflows/workflow1.yaml",
    "configs/workflows/workflow2.yaml",
    "configs/workflows/workflow3.yaml"
]

initial_data = [
    {"input": "数据1"},
    {"input": "数据2"},
    {"input": "数据3"}
]

results = runner.batch_run_workflows(config_paths, initial_data, max_workers=3)

for i, result in enumerate(results):
    print(f"工作流 {i+1}: {'成功' if result.success else '失败'}")
```

### 4. 配置验证

#### 验证配置文件

```python
# 验证配置
validation_result = loader.validate_config("configs/workflows/my_workflow.yaml")

if validation_result.is_valid:
    print("配置验证通过")
else:
    print("配置验证失败:")
    for error in validation_result.errors:
        print(f"  错误: {error}")
    for suggestion in validation_result.suggestions:
        print(f"  建议: {suggestion}")
```

#### 获取验证规则

```python
from src.infrastructure.graph.config_validator import WorkflowConfigValidator

validator = WorkflowConfigValidator()
rules = validator.get_validation_rules()
print(f"验证规则: {rules}")
```

### 5. 函数管理

#### 列出已注册函数

```python
# 列出所有函数
functions = loader.list_registered_functions()
print(f"节点函数: {functions['nodes']}")
print(f"条件函数: {functions['conditions']}")

# 列出特定类型函数
node_functions = loader.list_registered_functions(FunctionType.NODE_FUNCTION)
print(f"节点函数: {node_functions['nodes']}")
```

#### 获取函数信息

```python
# 获取函数详细信息
func_info = loader.get_function_info("my_condition", FunctionType.CONDITION_FUNCTION)
print(f"函数信息: {func_info}")
```

#### 获取函数统计

```python
# 获取函数统计信息
stats = loader.get_function_statistics()
print(f"统计信息: {stats}")
```

### 6. 错误处理

#### 基本错误处理

```python
try:
    result = workflow.run({"input": "数据"})
except ConfigValidationError as e:
    print(f"配置验证失败: {e}")
except WorkflowExecutionError as e:
    print(f"工作流执行失败: {e}")
except Exception as e:
    print(f"未知错误: {e}")
```

#### 使用运行器的错误处理

```python
result = runner.run_workflow("configs/workflows/my_workflow.yaml", {"input": "数据"})

if result.success:
    print(f"执行成功: {result.result}")
else:
    print(f"执行失败: {result.error}")
    print(f"错误类型: {result.metadata.get('error_type')}")
```

#### 重试机制

```python
# 创建带重试的运行器
runner = WorkflowRunner(max_retries=3)

# 运行工作流（自动重试）
result = runner.run_workflow("configs/workflows/my_workflow.yaml", {"input": "数据"})
```

### 7. 状态模板

#### 使用内置状态模板

```python
from src.application.workflow.state_templates import create_state_from_template

# 使用内置模板创建状态
state = create_state_from_template("plan_execute_state", {
    "current_task": "分析数据"
})
```

#### 创建自定义状态模板

```python
from src.application.workflow.state_templates import StateTemplate, get_global_template_manager

# 创建自定义模板
custom_template = StateTemplate(
    name="my_custom_state",
    description="自定义状态模板",
    fields={
        "messages": [],
        "custom_field": "default_value",
        "counter": 0
    }
)

# 注册模板
template_manager = get_global_template_manager()
template_manager.register_template(custom_template)

# 使用模板
state = template_manager.create_state_from_template("my_custom_state", {
    "custom_field": "override_value"
})
```

## 最佳实践

### 1. 函数命名规范

- **节点函数**：使用描述性名称，以 `_node` 或 `_function` 结尾
- **条件函数**：使用描述性名称，以 `_condition` 或 `_router` 结尾

```python
# 好的命名
def data_analysis_node(state) -> Dict[str, Any]:
    pass

def completion_check_condition(state) -> str:
    pass

# 避免的命名
def func1(state):
    pass

def check(state):
    pass
```

### 2. 配置组织

- **模块化配置**：将复杂工作流分解为多个配置文件
- **使用继承**：通过 `inherits_from` 复用配置
- **环境变量**：使用环境变量进行配置定制

```yaml
# base_workflow.yaml
name: base_workflow
description: 基础工作流
state_schema:
  name: BaseState
  fields:
    messages: []

# specific_workflow.yaml
inherits_from: "base_workflow.yaml"
name: specific_workflow
description: 特定工作流
nodes:
  specific_node:
    type: custom_node
```

### 3. 错误处理

- **验证配置**：在执行前验证配置
- **捕获异常**：使用适当的异常处理
- **日志记录**：记录执行过程和错误

```python
import logging

logger = logging.getLogger(__name__)

def run_workflow_safely(config_path: str, initial_data: Dict[str, Any]):
    try:
        # 验证配置
        validation_result = loader.validate_config(config_path)
        if not validation_result.is_valid:
            logger.error(f"配置验证失败: {validation_result.errors}")
            return None
        
        # 执行工作流
        result = workflow.run(initial_data)
        logger.info(f"工作流执行成功: {workflow.config.name}")
        return result
        
    except Exception as e:
        logger.error(f"工作流执行失败: {e}")
        return None
```

### 4. 性能优化

- **缓存配置**：启用配置缓存减少加载时间
- **批量执行**：使用批量执行提高效率
- **异步执行**：对于I/O密集型工作流使用异步执行

```python
# 启用缓存的加载器
loader = UniversalWorkflowLoader()
# 配置会自动缓存

# 批量执行
results = runner.batch_run_workflows(config_paths, initial_data_list)

# 异步执行
result = await workflow.run_async(initial_data)
```

## 故障排除

### 常见问题

#### 1. 函数未找到错误

```
错误: 节点 'my_node' 引用的函数 'my_function' 不存在
```

**解决方案**：
- 确保函数已正确注册
- 检查函数名称拼写
- 验证函数类型是否正确

```python
# 检查函数是否已注册
functions = loader.list_registered_functions()
if "my_function" not in functions['nodes']:
    print("函数未注册，请先注册函数")
    loader.register_function("my_function", my_function, FunctionType.NODE_FUNCTION)
```

#### 2. 配置验证失败

```
错误: 配置验证失败: 工作流名称不能为空
```

**解决方案**：
- 检查配置文件格式
- 确保必需字段存在
- 查看验证建议

```python
# 获取详细的验证信息
validation_result = loader.validate_config(config_path)
print(f"错误: {validation_result.errors}")
print(f"建议: {validation_result.suggestions}")
```

#### 3. 状态初始化失败

```
错误: 状态字段类型转换失败
```

**解决方案**：
- 检查状态字段类型定义
- 验证初始数据类型
- 使用状态模板

```python
# 使用状态模板确保正确的状态结构
state = template_manager.create_state_from_config(config, initial_data)
```

### 调试技巧

#### 1. 启用详细日志

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("src.application.workflow")
logger.setLevel(logging.DEBUG)
```

#### 2. 检查函数注册

```python
# 检查所有已注册的函数
functions = loader.list_registered_functions()
print("已注册的函数:")
for func_type, func_list in functions.items():
    print(f"  {func_type}: {func_list}")

# 检查特定函数信息
if "my_function" in functions['nodes']:
    info = loader.get_function_info("my_function", FunctionType.NODE_FUNCTION)
    print(f"函数信息: {info}")
```

#### 3. 验证配置步骤

```python
# 步骤1：检查文件是否存在
import os
if not os.path.exists(config_path):
    print(f"配置文件不存在: {config_path}")

# 步骤2：验证YAML格式
import yaml
try:
    with open(config_path, 'r') as f:
        config_data = yaml.safe_load(f)
    print("YAML格式正确")
except yaml.YAMLError as e:
    print(f"YAML格式错误: {e}")

# 步骤3：验证配置结构
validation_result = loader.validate_config(config_path)
if not validation_result.is_valid:
    print(f"配置验证失败: {validation_result.errors}")
```

## 进阶用法

### 1. 自定义加载器

```python
class CustomWorkflowLoader(UniversalWorkflowLoader):
    """自定义工作流加载器"""
    
    def __init__(self, custom_config=None):
        super().__init__()
        self.custom_config = custom_config or {}
        # 注册自定义函数
        self._register_custom_functions()
    
    def _register_custom_functions(self):
        """注册自定义函数"""
        # 注册自定义节点函数
        self.register_function("custom_node", self._custom_node, FunctionType.NODE_FUNCTION)
        
        # 注册自定义条件函数
        self.register_function("custom_condition", self._custom_condition, FunctionType.CONDITION_FUNCTION)
    
    def _custom_node(self, state) -> Dict[str, Any]:
        """自定义节点函数"""
        return {"result": "自定义节点处理完成"}
    
    def _custom_condition(self, state) -> str:
        """自定义条件函数"""
        return "next" if not state.get("done") else "end"
```

### 2. 插件系统

```python
class WorkflowPlugin:
    """工作流插件基类"""
    
    def register_functions(self, loader: UniversalWorkflowLoader):
        """注册插件函数"""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
        return []

class AnalysisPlugin(WorkflowPlugin):
    """分析插件"""
    
    def register_functions(self, loader: UniversalWorkflowLoader):
        loader.register_function("analysis_node", self._analysis_node, FunctionType.NODE_FUNCTION)
        loader.register_function("analysis_condition", self._analysis_condition, FunctionType.CONDITION_FUNCTION)
    
    def _analysis_node(self, state) -> Dict[str, Any]:
        return {"analysis": "分析完成"}
    
    def _analysis_condition(self, state) -> str:
        return "continue" if not state.get("analysis") else "end"

# 使用插件
def load_workflow_with_plugins(config_path: str, plugins: List[WorkflowPlugin]):
    loader = UniversalWorkflowLoader()
    
    # 注册插件函数
    for plugin in plugins:
        plugin.register_functions(loader)
    
    # 加载工作流
    return loader.load_from_file(config_path)
```

### 3. 配置热重载

```python
import asyncio
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ConfigReloadHandler(FileSystemEventHandler):
    """配置文件重载处理器"""
    
    def __init__(self, loader: UniversalWorkflowLoader, config_path: str):
        self.loader = loader
        self.config_path = config_path
        self.last_workflow = None
    
    def on_modified(self, event):
        if event.src_path == self.config_path:
            print(f"检测到配置文件变更: {self.config_path}")
            try:
                # 清除缓存
                self.loader.clear_cache()
                # 重新加载工作流
                self.last_workflow = self.loader.load_from_file(self.config_path)
                print("工作流重新加载完成")
            except Exception as e:
                print(f"重新加载失败: {e}")

def setup_config_watcher(config_path: str):
    """设置配置文件监控"""
    loader = UniversalWorkflowLoader()
    handler = ConfigReloadHandler(loader, config_path)
    observer = Observer()
    observer.schedule(handler, path=os.path.dirname(config_path), recursive=False)
    observer.start()
    
    try:
        while True:
            asyncio.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
```

这个使用指南提供了全面的通用工作流配置加载器使用说明，从基础用法到高级技巧，帮助用户充分利用这个强大的工具。