现在我来详细设计各个配置驱动的系统。让我先设计基于配置的内置函数加载系统：

## 基于配置的内置函数加载系统详细设计

### 1. 内置函数注册表配置

```yaml
# configs/builtin_functions/__registry__.yaml
metadata:
  name: "builtin_functions_registry"
  version: "1.0.0"
  description: "内置函数注册表配置"
  author: "system"

# 函数类型定义
function_types:
  node_functions:
    description: "节点函数类型"
    config_directory: "node_functions"
    default_enabled: true
    
  condition_functions:
    description: "条件函数类型"
    config_directory: "condition_functions"
    default_enabled: true
    
  edge_functions:
    description: "边函数类型"
    config_directory: "edge_functions"
    default_enabled: false

# 自动发现配置
auto_discovery:
  enabled: true
  scan_directories:
    - "configs/builtin_functions/node_functions"
    - "configs/builtin_functions/condition_functions"
    - "configs/builtin_functions/edge_functions"
  file_patterns:
    - "*.yaml"
    - "*.yml"
  exclude_patterns:
    - "__*"
    - "_*"
    - "test_*"

# 缓存配置
caching:
  enabled: true
  cache_size: 1000
  ttl: 3600  # 1小时

# 验证规则
validation_rules:
  - field: "function_types.*.config_directory"
    rule_type: "required"
    message: "函数类型必须指定配置目录"
  - field: "functions.*.class_path"
    rule_type: "required"
    message: "函数必须指定类路径"
```

### 2. 节点函数配置

```yaml
# configs/builtin_functions/node_functions.yaml
metadata:
  name: "node_functions_config"
  version: "1.0.0"
  description: "节点函数配置"

# 节点函数定义
node_functions:
  llm_node:
    description: "LLM节点函数"
    class_path: "src.core.workflow.graph.builtin.nodes.llm_node:LLMNode"
    config_file: "configs/nodes/llm_node.yaml"
    enabled: true
    fallback_enabled: true
    priority: 100
    tags: ["llm", "ai", "processing"]
    dependencies:
      - "llm_manager"
      - "prompt_service"
    parameters:
      model: "${DEFAULT_LLM_MODEL:gpt-4}"
      temperature: 0.7
      max_tokens: 2000
    metadata:
      author: "system"
      version: "1.0.0"
      category: "ai_processing"
      
  tool_node:
    description: "工具节点函数"
    class_path: "src.core.workflow.graph.builtin.nodes.tool_node:ToolNode"
    config_file: "configs/nodes/tool_node.yaml"
    enabled: true
    fallback_enabled: true
    priority: 90
    tags: ["tool", "execution", "external"]
    dependencies:
      - "tool_manager"
    parameters:
      timeout: 30
      max_parallel_calls: 1
      retry_on_failure: false
    metadata:
      author: "system"
      version: "1.0.0"
      category: "tool_execution"
      
  analysis_node:
    description: "分析节点函数"
    class_path: "src.core.workflow.graph.builtin.nodes.analysis_node:AnalysisNode"
    config_file: "configs/nodes/analysis_node.yaml"
    enabled: true
    fallback_enabled: true
    priority: 80
    tags: ["analysis", "processing", "evaluation"]
    dependencies: []
    parameters:
      analysis_type: "comprehensive"
      include_metrics: true
    metadata:
      author: "system"
      version: "1.0.0"
      category: "data_analysis"
      
  condition_node:
    description: "条件节点函数"
    class_path: "src.core.workflow.graph.builtin.nodes.condition_node:ConditionNode"
    config_file: "configs/nodes/condition_node.yaml"
    enabled: true
    fallback_enabled: true
    priority: 70
    tags: ["condition", "logic", "control"]
    dependencies: []
    parameters:
      evaluation_mode: "strict"
      default_result: "false"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "control_flow"
      
  wait_node:
    description: "等待节点函数"
    class_path: "src.core.workflow.graph.builtin.nodes.wait_node:WaitNode"
    config_file: "configs/nodes/wait_node.yaml"
    enabled: true
    fallback_enabled: true
    priority: 60
    tags: ["wait", "delay", "timing"]
    dependencies: []
    parameters:
      default_wait_time: 1
      max_wait_time: 300
    metadata:
      author: "system"
      version: "1.0.0"
      category: "timing_control"

# 函数组定义
function_groups:
  basic_nodes:
    description: "基础节点组"
    functions:
      - "start_node"
      - "end_node"
      - "passthrough_node"
      
  ai_nodes:
    description: "AI相关节点组"
    functions:
      - "llm_node"
      - "analysis_node"
      
  tool_nodes:
    description: "工具相关节点组"
    functions:
      - "tool_node"
      
  control_nodes:
    description: "控制相关节点组"
    functions:
      - "condition_node"
      - "wait_node"

# 默认配置
defaults:
  enabled: true
  fallback_enabled: true
  priority: 50
  dependencies: []
  parameters: {}
```

### 3. 条件函数配置

```yaml
# configs/builtin_functions/condition_functions.yaml
metadata:
  name: "condition_functions_config"
  version: "1.0.0"
  description: "条件函数配置"

# 条件函数定义
condition_functions:
  has_tool_calls:
    description: "检查是否有工具调用"
    class_path: "src.core.workflow.graph.builtin.conditions.tool_conditions:HasToolCalls"
    config_file: "configs/conditions/has_tool_calls.yaml"
    enabled: true
    fallback_enabled: true
    priority: 100
    tags: ["tool", "condition", "check"]
    dependencies: []
    parameters:
      check_message_content: true
      check_metadata: true
      keywords: ["tool_call", "调用工具"]
    return_values:
      - "continue"
      - "end"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "tool_checking"
      
  needs_more_info:
    description: "检查是否需要更多信息"
    class_path: "src.core.workflow.graph.builtin.conditions.info_conditions:NeedsMoreInfo"
    config_file: "configs/conditions/needs_more_info.yaml"
    enabled: true
    fallback_enabled: true
    priority: 90
    tags: ["info", "condition", "analysis"]
    dependencies: []
    parameters:
      question_indicators: ["?", "？", "需要", "请提供", "告诉我"]
      check_errors: true
      check_completion: true
    return_values:
      - "continue"
      - "end"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "info_analysis"
      
  is_complete:
    description: "检查是否完成"
    class_path: "src.core.workflow.graph.builtin.conditions.completion_conditions:IsComplete"
    config_file: "configs/conditions/is_complete.yaml"
    enabled: true
    fallback_enabled: true
    priority: 80
    tags: ["completion", "condition", "check"]
    dependencies: []
    parameters:
      max_message_count: 10
      end_indicators: ["结束", "完成", "finish", "done", "结束对话"]
      check_errors: true
    return_values:
      - "end"
      - "error"
      - "continue"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "completion_checking"
      
  always_true:
    description: "总是返回true"
    class_path: "src.core.workflow.graph.builtin.conditions.basic_conditions:AlwaysTrue"
    config_file: "configs/conditions/always_true.yaml"
    enabled: true
    fallback_enabled: true
    priority: 10
    tags: ["basic", "condition", "constant"]
    dependencies: []
    parameters:
      return_value: "true"
    return_values:
      - "true"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "basic_conditions"
      
  always_false:
    description: "总是返回false"
    class_path: "src.core.workflow.graph.builtin.conditions.basic_conditions:AlwaysFalse"
    config_file: "configs/conditions/always_false.yaml"
    enabled: true
    fallback_enabled: true
    priority: 10
    tags: ["basic", "condition", "constant"]
    dependencies: []
    parameters:
      return_value: "false"
    return_values:
      - "false"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "basic_conditions"
      
  has_messages:
    description: "检查是否有消息"
    class_path: "src.core.workflow.graph.builtin.conditions.message_conditions:HasMessages"
    config_file: "configs/conditions/has_messages.yaml"
    enabled: true
    fallback_enabled: true
    priority: 20
    tags: ["message", "condition", "check"]
    dependencies: []
    parameters:
      min_message_count: 1
      check_message_content: false
    return_values:
      - "true"
      - "false"
    metadata:
      author: "system"
      version: "1.0.0"
      category: "message_checking"

# 条件函数组定义
function_groups:
  basic_conditions:
    description: "基础条件组"
    functions:
      - "always_true"
      - "always_false"
      - "has_messages"
      
  tool_conditions:
    description: "工具相关条件组"
    functions:
      - "has_tool_calls"
      
  analysis_conditions:
    description: "分析相关条件组"
    functions:
      - "needs_more_info"
      - "is_complete"

# 默认配置
defaults:
  enabled: true
  fallback_enabled: true
  priority: 50
  dependencies: []
  parameters: {}
  return_values: ["true", "false"]
```

### 4. 函数加载器接口设计

```python
# src/core/workflow/functions/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List

class IFunctionLoader(ABC):
    """函数加载器接口"""
    
    @abstractmethod
    def load_function(self, function_name: str, function_type: str, **kwargs) -> Optional[Callable]:
        """加载函数"""
        pass
    
    @abstractmethod
    def list_functions(self, function_type: str) -> List[str]:
        """列出函数"""
        pass
    
    @abstractmethod
    def is_function_available(self, function_name: str, function_type: str) -> bool:
        """检查函数是否可用"""
        pass

class IFunctionRegistry(ABC):
    """函数注册表接口"""
    
    @abstractmethod
    def register_function(self, name: str, function: Callable, function_type: str, **metadata) -> None:
        """注册函数"""
        pass
    
    @abstractmethod
    def get_function(self, name: str, function_type: str) -> Optional[Callable]:
        """获取函数"""
        pass
    
    @abstractmethod
    def unregister_function(self, name: str, function_type: str) -> bool:
        """注销函数"""
        pass
```

### 5. 配置驱动的函数加载器实现

```python
# src/core/workflow/functions/configurable_loader.py
class ConfigurableFunctionLoader(IFunctionLoader):
    """配置驱动的函数加载器"""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self._function_cache: Dict[str, Callable] = {}
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        
    def load_function(self, function_name: str, function_type: str, **kwargs) -> Optional[Callable]:
        """根据配置加载函数"""
        cache_key = f"{function_type}:{function_name}"
        
        # 检查缓存
        if cache_key in self._function_cache:
            return self._function_cache[cache_key]
        
        # 获取函数配置
        function_config = self._get_function_config(function_name, function_type)
        if not function_config:
            return None
        
        # 检查是否启用
        if not function_config.get("enabled", True):
            return None
        
        try:
            # 动态导入类
            class_path = function_config["class_path"]
            function_class = self._import_class(class_path)
            
            # 获取配置文件
            config_file = function_config.get("config_file")
            function_specific_config = {}
            if config_file:
                function_specific_config = self.config_manager.load_config(config_file)
            
            # 合并参数
            parameters = {
                **function_config.get("parameters", {}),
                **function_specific_config,
                **kwargs
            }
            
            # 创建函数实例
            if hasattr(function_class, "create"):
                # 工厂方法
                function_instance = function_class.create(**parameters)
            else:
                # 直接实例化
                function_instance = function_class(**parameters)
            
            # 缓存函数
            self._function_cache[cache_key] = function_instance
            
            return function_instance
            
        except Exception as e:
            logger.error(f"加载函数失败 {function_name} ({function_type}): {e}")
            return None
    
    def _get_function_config(self, function_name: str, function_type: str) -> Optional[Dict[str, Any]]:
        """获取函数配置"""
        config_key = f"{function_type}:{function_name}"
        
        if config_key in self._config_cache:
            return self._config_cache[config_key]
        
        # 加载配置文件
        config_file = f"configs/builtin_functions/{function_type}.yaml"
        try:
            config_data = self.config_manager.load_config(config_file)
            functions = config_data.get(f"{function_type}", {})
            function_config = functions.get(function_name)
            
            if function_config:
                self._config_cache[config_key] = function_config
                return function_config
        except Exception as e:
            logger.error(f"加载函数配置失败 {function_name} ({function_type}): {e}")
        
        return None
    
    def _import_class(self, class_path: str) -> type:
        """动态导入类"""
        module_path, class_name = class_path.rsplit(":", 1)
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
```

这个设计提供了：

1. **完全配置驱动**：所有内置函数都通过配置文件定义
2. **动态加载**：运行时根据配置动态加载函数
3. **缓存优化**：支持函数实例缓存
4. **参数合并**：支持配置文件参数和运行时参数合并
5. **错误处理**：完善的错误处理和日志记录
6. **类型安全**：通过接口定义确保类型安全
