# 通用工作流配置加载器 API 参考

## 概述

本文档详细描述通用工作流配置加载器的API接口设计，包括类定义、方法签名和使用示例。

## 核心接口

### FunctionType 枚举

```python
from enum import Enum

class FunctionType(Enum):
    """函数类型枚举"""
    NODE_FUNCTION = "node_function"      # 节点函数
    CONDITION_FUNCTION = "condition_function"  # 条件函数
```

### FunctionRegistry 类

#### 构造函数
```python
class FunctionRegistry:
    def __init__(self, enable_auto_discovery: bool = False):
        """
        初始化函数注册表
        
        Args:
            enable_auto_discovery: 是否启用自动发现功能
        """
```

#### 核心方法

**register**
```python
def register(self, name: str, function: Callable, function_type: FunctionType) -> None:
    """
    注册函数
    
    Args:
        name: 函数名称（配置文件中使用的名称）
        function: 函数对象
        function_type: 函数类型
        
    Raises:
        ValueError: 函数名称已存在或函数类型无效
    """
```

**get_node_function**
```python
def get_node_function(self, name: str) -> Optional[Callable]:
    """
    获取节点函数
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 节点函数，如果不存在返回None
    """
```

**get_condition_function**
```python
def get_condition_function(self, name: str) -> Optional[Callable]:
    """
    获取条件函数
    
    Args:
        name: 函数名称
        
    Returns:
        Optional[Callable]: 条件函数，如果不存在返回None
    """
```

**discover_functions**
```python
def discover_functions(self, module_paths: List[str] = None) -> Dict[str, List[str]]:
    """
    自动发现并注册函数
    
    Args:
        module_paths: 要扫描的模块路径列表，如果为None则使用默认路径
        
    Returns:
        Dict[str, List[str]]: 发现的函数统计信息
    """
```

**list_functions**
```python
def list_functions(self, function_type: Optional[FunctionType] = None) -> Dict[str, List[str]]:
    """
    列出已注册的函数
    
    Args:
        function_type: 函数类型过滤器，如果为None则返回所有函数
        
    Returns:
        Dict[str, List[str]]: 函数分类列表
    """
```

### EnhancedGraphBuilder 类

#### 构造函数
```python
class EnhancedGraphBuilder(GraphBuilder):
    def __init__(
        self, 
        node_registry: Optional[NodeRegistry] = None,
        function_registry: Optional[FunctionRegistry] = None,
        enable_function_fallback: bool = True
    ):
        """
        初始化增强图构建器
        
        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
        """
```

#### 重写方法

**_get_node_function**
```python
def _get_node_function(self, node_config: NodeConfig, state_manager: Optional[IStateCollaborationManager] = None) -> Optional[Callable]:
    """
    获取节点函数（重写父类方法）
    
    优先级：函数注册表 -> 节点注册表 -> 内置函数 -> 父类方法
    
    Args:
        node_config: 节点配置
        state_manager: 状态管理器
        
    Returns:
        Optional[Callable]: 节点函数
    """
```

**_get_condition_function**
```python
def _get_condition_function(self, condition_name: str) -> Optional[Callable]:
    """
    获取条件函数（重写父类方法）
    
    优先级：函数注册表 -> 内置条件 -> 父类方法
    
    Args:
        condition_name: 条件函数名称
        
    Returns:
        Optional[Callable]: 条件函数
    """
```

### UniversalWorkflowLoader 类

#### 构造函数
```python
class UniversalWorkflowLoader:
    def __init__(
        self,
        config_loader: Optional[IConfigLoader] = None,
        container: Optional[IDependencyContainer] = None,
        enable_auto_registration: bool = True
    ):
        """
        初始化通用工作流加载器
        
        Args:
            config_loader: 配置加载器
            container: 依赖注入容器
            enable_auto_registration: 是否启用自动函数注册
        """
```

#### 核心方法

**load_from_file**
```python
def load_from_file(
    self, 
    config_path: str, 
    initial_state_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> WorkflowInstance:
    """
    从文件加载工作流
    
    Args:
        config_path: 配置文件路径
        initial_state_data: 初始状态数据
        **kwargs: 其他参数
        
    Returns:
        WorkflowInstance: 工作流实例
        
    Raises:
        FileNotFoundError: 配置文件不存在
        ConfigValidationError: 配置验证失败
    """
```

**load_from_dict**
```python
def load_from_dict(
    self, 
    config_dict: Dict[str, Any], 
    initial_state_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> WorkflowInstance:
    """
    从字典加载工作流
    
    Args:
        config_dict: 配置字典
        initial_state_data: 初始状态数据
        **kwargs: 其他参数
        
    Returns:
        WorkflowInstance: 工作流实例
    """
```

**register_function**
```python
def register_function(
    self, 
    name: str, 
    function: Callable, 
    function_type: FunctionType
) -> None:
    """
    注册函数
    
    Args:
        name: 函数名称
        function: 函数对象
        function_type: 函数类型
    """
```

**register_functions_from_module**
```python
def register_functions_from_module(self, module_path: str) -> Dict[str, List[str]]:
    """
    从模块注册函数
    
    Args:
        module_path: 模块路径
        
    Returns:
        Dict[str, List[str]]: 注册的函数统计信息
    """
```

**validate_config**
```python
def validate_config(self, config: Union[str, Dict[str, Any]]) -> ValidationResult:
    """
    验证配置
    
    Args:
        config: 配置路径或配置字典
        
    Returns:
        ValidationResult: 验证结果
    """
```

### WorkflowInstance 类

#### 核心方法

**run**
```python
def run(
    self, 
    initial_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> WorkflowState:
    """
    运行工作流
    
    Args:
        initial_data: 初始数据
        config: 运行配置
        
    Returns:
        WorkflowState: 最终状态
    """
```

**run_async**
```python
async def run_async(
    self, 
    initial_data: Optional[Dict[str, Any]] = None,
    config: Optional[Dict[str, Any]] = None
) -> WorkflowState:
    """
    异步运行工作流
    
    Args:
        initial_data: 初始数据
        config: 运行配置
        
    Returns:
        WorkflowState: 最终状态
    """
```

**get_config**
```python
def get_config(self) -> GraphConfig:
    """
    获取工作流配置
    
    Returns:
        GraphConfig: 工作流配置
    """
```

**get_visualization**
```python
def get_visualization(self) -> Dict[str, Any]:
    """
    获取工作流可视化数据
    
    Returns:
        Dict[str, Any]: 可视化数据
    """
```

### WorkflowRunner 类

#### 构造函数
```python
class WorkflowRunner:
    def __init__(self, loader: Optional[UniversalWorkflowLoader] = None):
        """
        初始化工作流运行器
        
        Args:
            loader: 通用加载器实例
        """
```

#### 核心方法

**run_workflow**
```python
def run_workflow(
    self, 
    config_path: str, 
    initial_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> WorkflowExecutionResult:
    """
    运行工作流
    
    Args:
        config_path: 配置文件路径
        initial_data: 初始数据
        **kwargs: 其他参数
        
    Returns:
        WorkflowExecutionResult: 执行结果
    """
```

**run_workflow_async**
```python
async def run_workflow_async(
    self, 
    config_path: str, 
    initial_data: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> WorkflowExecutionResult:
    """
    异步运行工作流
    
    Args:
        config_path: 配置文件路径
        initial_data: 初始数据
        **kwargs: 其他参数
        
    Returns:
        WorkflowExecutionResult: 执行结果
    """
```

**batch_run_workflows**
```python
def batch_run_workflows(
    self, 
    config_paths: List[str], 
    initial_data_list: Optional[List[Dict[str, Any]]] = None,
    max_workers: int = 3
) -> List[WorkflowExecutionResult]:
    """
    批量运行工作流
    
    Args:
        config_paths: 配置文件路径列表
        initial_data_list: 初始数据列表
        max_workers: 最大并发数
        
    Returns:
        List[WorkflowExecutionResult]: 执行结果列表
    """
```

## 配置格式扩展

### 函数注册配置

```yaml
# 在现有配置基础上添加
function_registrations:
  # 节点函数注册
  nodes:
    plan_execute_agent_node: "src.workflow.nodes.plan_execute_agent_node"
    custom_analysis_node: "src.custom.nodes.analysis_node"
    
  # 条件函数注册  
  conditions:
    plan_execute_router: "src.workflow.conditions.plan_execute_router"
    custom_condition: "src.custom.conditions.my_condition"
    
  # 自动发现配置
  auto_discovery:
    enabled: true
    module_paths:
      - "src.workflow.nodes"
      - "src.workflow.conditions"
    exclude_patterns:
      - "*_test.py"
      - "*_mock.py"
```

### 状态模板配置

```yaml
# 状态模板定义
state_templates:
  # 基础状态模板
  base_state:
    workflow_messages: []
    workflow_tool_calls: []
    workflow_tool_results: []
    workflow_iteration_count: 0
    workflow_max_iterations: 10
    
  # 计划执行状态模板
  plan_execute_state:
    inherits_from: "base_state"
    context:
      current_plan: []
      current_step_index: 0
      plan_completed: false
    current_task: ""
    
# 工作流特定状态配置
state_template: "plan_execute_state"
state_overrides:
  workflow_max_iterations: 15
  context:
    plan_max_steps: 5
```

## 使用示例

### 基础用法

```python
from src.application.workflow.universal_loader import UniversalWorkflowLoader

# 创建加载器
loader = UniversalWorkflowLoader()

# 加载工作流
workflow = loader.load_from_file("configs/workflows/plan_execute_agent_workflow.yaml")

# 运行工作流
result = workflow.run({
    "current_task": "分析用户行为数据，找出最受欢迎的产品类别"
})

print(f"执行结果: {result}")
```

### 注册自定义函数

```python
from src.application.workflow.universal_loader import UniversalWorkflowLoader, FunctionType

def my_custom_condition(state) -> str:
    """自定义条件函数"""
    if state.get("needs_review", False):
        return "review"
    return "continue"

def my_custom_node(state) -> Dict[str, Any]:
    """自定义节点函数"""
    return {"result": "自定义节点执行完成"}

# 创建加载器并注册函数
loader = UniversalWorkflowLoader()
loader.register_function("my_condition", my_custom_condition, FunctionType.CONDITION_FUNCTION)
loader.register_function("my_node", my_custom_node, FunctionType.NODE_FUNCTION)

# 使用自定义函数的工作流
workflow = loader.load_from_file("configs/workflows/custom_workflow.yaml")
```

### 使用工作流运行器

```python
from src.application.workflow.runner import WorkflowRunner

# 创建运行器
runner = WorkflowRunner()

# 运行单个工作流
result = runner.run_workflow(
    "configs/workflows/plan_execute_agent_workflow.yaml",
    {"current_task": "分析任务"}
)

# 批量运行工作流
results = runner.batch_run_workflows([
    "configs/workflows/workflow1.yaml",
    "configs/workflows/workflow2.yaml"
], max_workers=2)
```

### 配置验证

```python
from src.application.workflow.universal_loader import UniversalWorkflowLoader

loader = UniversalWorkflowLoader()

# 验证配置
validation_result = loader.validate_config("configs/workflows/my_workflow.yaml")

if validation_result.is_valid:
    print("配置验证通过")
else:
    print(f"配置验证失败: {validation_result.errors}")
    print(f"修复建议: {validation_result.suggestions}")
```

## 错误处理

### 自定义异常

```python
class UniversalLoaderError(Exception):
    """通用加载器基础异常"""
    pass

class ConfigValidationError(UniversalLoaderError):
    """配置验证异常"""
    pass

class FunctionRegistrationError(UniversalLoaderError):
    """函数注册异常"""
    pass

class WorkflowExecutionError(UniversalLoaderError):
    """工作流执行异常"""
    pass
```

### 错误处理示例

```python
from src.application.workflow.universal_loader import UniversalWorkflowLoader, ConfigValidationError

loader = UniversalWorkflowLoader()

try:
    workflow = loader.load_from_file("invalid_config.yaml")
    result = workflow.run()
except ConfigValidationError as e:
    print(f"配置验证失败: {e}")
    # 处理配置错误
except WorkflowExecutionError as e:
    print(f"工作流执行失败: {e}")
    # 处理执行错误
except Exception as e:
    print(f"未知错误: {e}")
    # 处理其他错误
```

## 性能优化建议

### 懒加载模式

```python
# 启用懒加载可以减少启动时间
loader = UniversalWorkflowLoader(enable_lazy_loading=True)
```

### 缓存配置

```python
# 启用配置缓存可以提升重复加载性能
loader = UniversalWorkflowLoader(enable_config_caching=True)
```

### 预编译工作流

```python
# 对于频繁使用的工作流，可以预编译
workflow = loader.load_from_file("frequent_workflow.yaml")
compiled_workflow = workflow.compile()  # 预编译优化
```

这个API参考文档提供了完整的接口定义和使用指南，确保开发者能够正确使用通用工作流配置加载器。