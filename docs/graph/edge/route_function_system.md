# 路由函数配置系统设计

## 概述

路由函数配置系统是灵活条件边设计的核心组件，负责管理、加载和执行路由函数。本文档详细描述了路由函数配置系统的架构和实现。

## 系统架构

### 1. 核心组件

#### 1.1 路由函数注册表 (RouteFunctionRegistry)

路由函数注册表是系统的核心，负责管理所有可用的路由函数。

```python
from typing import Dict, Any, Callable, Optional, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class RouteFunctionConfig:
    """路由函数配置"""
    name: str
    description: str
    parameters: Dict[str, Any]  # 参数配置
    return_values: List[str]   # 可能的返回值列表
    category: str = "general"   # 路由函数分类
    implementation: str = ""    # 实现方式：builtin, config, custom
    metadata: Dict[str, Any] = None  # 元数据

class RouteFunctionRegistry:
    """路由函数注册表"""
    
    def __init__(self):
        self._route_functions: Dict[str, Callable] = {}
        self._route_configs: Dict[str, RouteFunctionConfig] = {}
        self._categories: Dict[str, List[str]] = {}
    
    def register_route_function(
        self, 
        name: str, 
        function: Callable, 
        config: RouteFunctionConfig
    ) -> None:
        """注册路由函数"""
        self._route_functions[name] = function
        self._route_configs[name] = config
        
        # 更新分类索引
        if config.category not in self._categories:
            self._categories[config.category] = []
        if name not in self._categories[config.category]:
            self._categories[config.category].append(name)
        
        logger.debug(f"注册路由函数: {name} (分类: {config.category})")
    
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数"""
        return self._route_functions.get(name)
    
    def get_route_config(self, name: str) -> Optional[RouteFunctionConfig]:
        """获取路由函数配置"""
        return self._route_configs.get(name)
    
    def list_route_functions(self, category: Optional[str] = None) -> List[str]:
        """列出路由函数"""
        if category:
            return self._categories.get(category, [])
        return list(self._route_functions.keys())
    
    def list_categories(self) -> List[str]:
        """列出所有分类"""
        return list(self._categories.keys())
    
    def unregister(self, name: str) -> bool:
        """注销路由函数"""
        if name in self._route_functions:
            config = self._route_configs[name]
            
            # 从分类中移除
            if config.category in self._categories:
                if name in self._categories[config.category]:
                    self._categories[config.category].remove(name)
                
                # 如果分类为空，移除分类
                if not self._categories[config.category]:
                    del self._categories[config.category]
            
            del self._route_functions[name]
            del self._route_configs[name]
            
            logger.debug(f"注销路由函数: {name}")
            return True
        return False
```

#### 1.2 路由函数加载器 (RouteFunctionLoader)

路由函数加载器负责从配置文件和代码中加载路由函数。

```python
import yaml
import importlib
import inspect
from pathlib import Path
from typing import Dict, Any, Callable

class RouteFunctionLoader:
    """路由函数加载器"""
    
    def __init__(self, registry: RouteFunctionRegistry):
        self.registry = registry
        self._builtin_functions: Dict[str, Callable] = {}
    
    def load_from_config_directory(self, config_dir: str) -> None:
        """从配置目录加载路由函数"""
        config_path = Path(config_dir)
        if not config_path.exists():
            logger.warning(f"路由函数配置目录不存在: {config_dir}")
            return
        
        # 加载路由函数配置
        route_functions_dir = config_path / "route_functions"
        if route_functions_dir.exists():
            self._load_route_functions_from_directory(route_functions_dir)
    
    def _load_route_functions_from_directory(self, dir_path: Path) -> None:
        """从目录加载路由函数配置"""
        for config_file in dir_path.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                self._process_route_functions_config(config_data, config_file)
                logger.debug(f"加载路由函数配置: {config_file}")
                
            except Exception as e:
                logger.error(f"加载路由函数配置失败 {config_file}: {e}")
    
    def _process_route_functions_config(self, config_data: Dict[str, Any], config_file: Path) -> None:
        """处理路由函数配置"""
        route_functions = config_data.get("route_functions", {})
        category = config_data.get("category", "general")
        
        for name, func_config in route_functions.items():
            # 创建路由函数配置
            route_config = RouteFunctionConfig(
                name=name,
                description=func_config.get("description", ""),
                parameters=func_config.get("parameters", {}),
                return_values=func_config.get("return_values", []),
                category=category,
                implementation=func_config.get("implementation", "config"),
                metadata=func_config.get("metadata", {})
            )
            
            # 根据实现方式创建路由函数
            route_function = self._create_route_function(name, func_config)
            
            if route_function:
                self.registry.register_route_function(name, route_function, route_config)
    
    def _create_route_function(self, name: str, config: Dict[str, Any]) -> Optional[Callable]:
        """根据配置创建路由函数"""
        implementation = config.get("implementation", "config")
        
        if implementation == "builtin":
            return self._get_builtin_function(name)
        elif implementation == "config":
            return self._create_config_based_function(config)
        elif implementation.startswith("custom."):
            # 自定义函数，从模块加载
            module_path = implementation[7:]  # 移除 "custom." 前缀
            return self._load_custom_function(module_path)
        else:
            logger.warning(f"未知的实现方式: {implementation}")
            return None
    
    def _create_config_based_function(self, config: Dict[str, Any]) -> Callable:
        """创建基于配置的路由函数"""
        func_type = config.get("type", "state_check")
        
        if func_type == "state_check":
            return self._create_state_check_function(config)
        elif func_type == "message_check":
            return self._create_message_check_function(config)
        elif func_type == "tool_check":
            return self._create_tool_check_function(config)
        elif func_type == "multi_condition":
            return self._create_multi_condition_function(config)
        else:
            logger.warning(f"未知的配置函数类型: {func_type}")
            return lambda state: "default"
    
    def _create_state_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建状态检查函数"""
        state_key = config["state_key"]
        value_mapping = config["value_mapping"]
        default_target = config.get("default", "default")
        
        def state_check_function(state: Dict[str, Any]) -> str:
            state_value = state.get(state_key)
            return value_mapping.get(str(state_value), default_target)
        
        return state_check_function
    
    def _create_message_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建消息检查函数"""
        keywords = config.get("keywords", [])
        case_sensitive = config.get("case_sensitive", False)
        return_true = config.get("return_true", "matched")
        return_false = config.get("return_false", "not_matched")
        
        def message_check_function(state: Dict[str, Any]) -> str:
            messages = state.get("messages", [])
            if not messages:
                return return_false
            
            last_message = messages[-1]
            if hasattr(last_message, 'content'):
                content = str(getattr(last_message, 'content', ''))
                if not case_sensitive:
                    content = content.lower()
                    keywords = [kw.lower() for kw in keywords]
                
                if any(keyword in content for keyword in keywords):
                    return return_true
            
            return return_false
        
        return message_check_function
    
    def _create_tool_check_function(self, config: Dict[str, Any]) -> Callable:
        """创建工具检查函数"""
        has_tool_calls = config.get("has_tool_calls", True)
        has_tool_results = config.get("has_tool_results", False)
        return_true = config.get("return_true", "continue")
        return_false = config.get("return_false", "end")
        
        def tool_check_function(state: Dict[str, Any]) -> str:
            # 检查工具调用
            if has_tool_calls:
                messages = state.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
                        return return_true
            
            # 检查工具结果
            if has_tool_results:
                tool_results = state.get("tool_results", [])
                if tool_results:
                    return return_true
            
            return return_false
        
        return tool_check_function
    
    def _create_multi_condition_function(self, config: Dict[str, Any]) -> Callable:
        """创建多条件函数"""
        conditions = config["conditions"]
        default_target = config.get("default_target", "default")
        
        def multi_condition_function(state: Dict[str, Any]) -> str:
            for condition in conditions:
                condition_type = condition["type"]
                
                if condition_type == "state_check":
                    state_key = condition["state_key"]
                    operator = condition["operator"]
                    value = condition["value"]
                    
                    state_value = state.get(state_key)
                    if self._evaluate_condition(state_value, operator, value):
                        return condition["target"]
                
                elif condition_type == "tool_check":
                    has_tool_calls = condition.get("has_tool_calls", False)
                    if has_tool_calls:
                        messages = state.get("messages", [])
                        if messages:
                            last_message = messages[-1]
                            if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
                                return condition["target"]
                
                elif condition_type == "message_check":
                    keywords = condition.get("message_contains", [])
                    messages = state.get("messages", [])
                    if messages:
                        last_message = messages[-1]
                        if hasattr(last_message, 'content'):
                            content = str(getattr(last_message, 'content', '')).lower()
                            if any(keyword.lower() in content for keyword in keywords):
                                return condition["target"]
            
            return default_target
        
        return multi_condition_function
    
    def _evaluate_condition(self, left_value: Any, operator: str, right_value: Any) -> bool:
        """评估条件"""
        try:
            if operator == "==":
                return left_value == right_value
            elif operator == "!=":
                return left_value != right_value
            elif operator == ">":
                return left_value > right_value
            elif operator == ">=":
                return left_value >= right_value
            elif operator == "<":
                return left_value < right_value
            elif operator == "<=":
                return left_value <= right_value
            elif operator == "in":
                return left_value in right_value
            elif operator == "not_in":
                return left_value not in right_value
            else:
                return False
        except Exception:
            return False
    
    def register_builtin_functions(self) -> None:
        """注册内置路由函数"""
        builtin_functions = {
            "has_tool_calls": self._builtin_has_tool_calls,
            "no_tool_calls": self._builtin_no_tool_calls,
            "has_tool_results": self._builtin_has_tool_results,
            "max_iterations_reached": self._builtin_max_iterations_reached,
            "has_errors": self._builtin_has_errors,
            "no_errors": self._builtin_no_errors,
        }
        
        for name, func in builtin_functions.items():
            self._builtin_functions[name] = func
            
            # 创建配置
            config = RouteFunctionConfig(
                name=name,
                description=f"内置路由函数: {name}",
                parameters={},
                return_values=["continue", "end"],
                category="builtin",
                implementation="builtin"
            )
            
            self.registry.register_route_function(name, func, config)
    
    # 内置路由函数实现
    def _builtin_has_tool_calls(self, state: Dict[str, Any]) -> str:
        """检查是否有工具调用"""
        messages = state.get("messages", [])
        if not messages:
            return "end"
        
        last_message = messages[-1]
        if hasattr(last_message, 'tool_calls') and getattr(last_message, 'tool_calls', None):
            return "continue"
        
        return "end"
    
    def _builtin_no_tool_calls(self, state: Dict[str, Any]) -> str:
        """检查是否没有工具调用"""
        return "continue" if self._builtin_has_tool_calls(state) == "end" else "end"
    
    def _builtin_has_tool_results(self, state: Dict[str, Any]) -> str:
        """检查是否有工具结果"""
        return "continue" if len(state.get("tool_results", [])) > 0 else "end"
    
    def _builtin_max_iterations_reached(self, state: Dict[str, Any]) -> str:
        """检查是否达到最大迭代次数"""
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", 10)
        return "end" if iteration_count >= max_iterations else "continue"
    
    def _builtin_has_errors(self, state: Dict[str, Any]) -> str:
        """检查是否有错误"""
        for result in state.get("tool_results", []):
            if isinstance(result, dict) and not result.get("success", True):
                return "error"
        return "continue"
    
    def _builtin_no_errors(self, state: Dict[str, Any]) -> str:
        """检查是否没有错误"""
        return "continue" if self._builtin_has_errors(state) == "continue" else "error"
```

#### 1.3 路由函数管理器 (RouteFunctionManager)

路由函数管理器是系统的入口点，提供统一的路由函数管理接口。

```python
class RouteFunctionManager:
    """路由函数管理器"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.registry = RouteFunctionRegistry()
        self.loader = RouteFunctionLoader(self.registry)
        
        # 注册内置函数
        self.loader.register_builtin_functions()
        
        # 从配置目录加载
        if config_dir:
            self.loader.load_from_config_directory(config_dir)
    
    def get_route_function(self, name: str) -> Optional[Callable]:
        """获取路由函数"""
        return self.registry.get_route_function(name)
    
    def list_route_functions(self, category: Optional[str] = None) -> List[str]:
        """列出路由函数"""
        return self.registry.list_route_functions(category)
    
    def get_route_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取路由函数信息"""
        config = self.registry.get_route_config(name)
        if not config:
            return None
        
        return {
            "name": config.name,
            "description": config.description,
            "category": config.category,
            "parameters": config.parameters,
            "return_values": config.return_values,
            "implementation": config.implementation,
            "metadata": config.metadata
        }
    
    def validate_route_function(self, name: str, parameters: Dict[str, Any]) -> List[str]:
        """验证路由函数参数"""
        config = self.registry.get_route_config(name)
        if not config:
            return [f"路由函数不存在: {name}"]
        
        errors = []
        param_config = config.parameters
        
        # 检查必需参数
        if isinstance(param_config, dict) and "type" in param_config:
            # JSON Schema 风格的参数验证
            required = param_config.get("required", [])
            properties = param_config.get("properties", {})
            
            for req_param in required:
                if req_param not in parameters:
                    errors.append(f"缺少必需参数: {req_param}")
            
            # 检查参数类型
            for param_name, param_value in parameters.items():
                if param_name in properties:
                    expected_type = properties[param_name].get("type")
                    if expected_type and not self._check_type(param_value, expected_type):
                        errors.append(f"参数 {param_name} 类型错误，期望 {expected_type}")
        
        return errors
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """检查参数类型"""
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True
```

## 配置文件结构

### 1. 路由函数组配置

```yaml
# configs/edges/route_functions/_group.yaml
name: "路由函数组配置"
description: "路由函数组的全局配置"

categories:
  - name: "builtin"
    description: "内置路由函数"
  - name: "tool"
    description: "基于工具的路由函数"
  - name: "state"
    description: "基于状态的路由函数"
  - name: "message"
    description: "基于消息的路由函数"
  - name: "custom"
    description: "自定义路由函数"

global_settings:
  enable_validation: true
  strict_mode: false
  cache_functions: true
```

### 2. 基于工具的路由函数

```yaml
# configs/edges/route_functions/tool_based.yaml
name: "基于工具的路由函数"
description: "基于工具调用状态的路由函数集合"
category: "tool"

route_functions:
  has_tool_calls:
    description: "检查是否有工具调用"
    parameters: {}
    return_values: ["continue", "end"]
    implementation: "builtin"
    
  tool_call_count:
    description: "基于工具调用数量的路由"
    parameters:
      type: "object"
      properties:
        threshold:
          type: "integer"
          description: "阈值"
          default: 1
      required: ["threshold"]
    return_values: ["single", "multiple", "none"]
    implementation: "config"
    type: "tool_check"
    has_tool_calls: true
    return_true: "multiple"
    return_false: "single"
    
  tool_result_check:
    description: "检查工具执行结果"
    parameters:
      type: "object"
      properties:
        check_success:
          type: "boolean"
          description: "是否检查成功状态"
          default: true
    return_values: ["success", "error", "no_results"]
    implementation: "config"
    type: "tool_check"
    has_tool_results: true
    return_true: "success"
    return_false: "error"
```

### 3. 基于状态的路由函数

```yaml
# configs/edges/route_functions/state_based.yaml
name: "基于状态的路由函数"
description: "基于工作流状态的路由函数集合"
category: "state"

route_functions:
  iteration_check:
    description: "基于迭代次数的路由"
    parameters:
      type: "object"
      properties:
        max_iterations:
          type: "integer"
          description: "最大迭代次数"
          default: 10
    return_values: ["continue", "max_reached"]
    implementation: "config"
    type: "state_check"
    state_key: "iteration_count"
    value_mapping:
      "10": "max_reached"
    default: "continue"
    
  status_check:
    description: "基于状态值的路由"
    parameters:
      type: "object"
      properties:
        status_mapping:
          type: "object"
          description: "状态值映射"
          default:
            "success": "complete"
            "error": "error_handler"
            "pending": "continue"
    return_values: ["complete", "error_handler", "continue"]
    implementation: "config"
    type: "state_check"
    state_key: "status"
    value_mapping:
      "success": "complete"
      "error": "error_handler"
      "pending": "continue"
    default: "continue"
```

### 4. 基于消息的路由函数

```yaml
# configs/edges/route_functions/message_based.yaml
name: "基于消息的路由函数"
description: "基于消息内容的路由函数集合"
category: "message"

route_functions:
  keyword_match:
    description: "基于关键词匹配的路由"
    parameters:
      type: "object"
      properties:
        keywords:
          type: "array"
          items:
            type: "string"
          description: "关键词列表"
        case_sensitive:
          type: "boolean"
          description: "是否区分大小写"
          default: false
    return_values: ["matched", "not_matched"]
    implementation: "config"
    type: "message_check"
    return_true: "matched"
    return_false: "not_matched"
    
  sentiment_analysis:
    description: "基于情感分析的路由"
    parameters:
      type: "object"
      properties:
        sentiment_threshold:
          type: "number"
          description: "情感阈值"
          default: 0.5
    return_values: ["positive", "negative", "neutral"]
    implementation: "custom.sentiment_router"
```

### 5. 自定义路由函数

```yaml
# configs/edges/route_functions/custom.yaml
name: "自定义路由函数"
description: "用户自定义的路由函数集合"
category: "custom"

route_functions:
  complex_business_logic:
    description: "复杂业务逻辑路由"
    parameters:
      type: "object"
      properties:
        business_rules:
          type: "array"
          items:
            type: "object"
          description: "业务规则列表"
    return_values: ["approve", "reject", "review"]
    implementation: "custom.business_logic_router"
    
  ml_model_prediction:
    description: "基于机器学习模型预测的路由"
    parameters:
      type: "object"
      properties:
        model_name:
          type: "string"
          description: "模型名称"
        confidence_threshold:
          type: "number"
          description: "置信度阈值"
          default: 0.8
    return_values: ["high_confidence", "low_confidence", "error"]
    implementation: "custom.ml_model_router"
```

## 使用示例

### 1. 基本使用

```python
# 初始化路由函数管理器
route_manager = RouteFunctionManager(config_dir="configs/edges")

# 获取路由函数
route_function = route_manager.get_route_function("has_tool_calls")

# 在工作流中使用
def route_decision(state: WorkflowState) -> str:
    return route_function(state)

# 添加条件边
builder.add_conditional_edges(
    "agent_node",
    route_decision,
    {
        "continue": "tool_executor",
        "end": "__end__"
    }
)
```

### 2. 配置验证

```python
# 验证路由函数参数
errors = route_manager.validate_route_function(
    "tool_call_count",
    {"threshold": 5}
)

if errors:
    for error in errors:
        print(f"参数验证错误: {error}")
```

### 3. 获取路由函数信息

```python
# 获取路由函数信息
info = route_manager.get_route_info("has_tool_calls")
print(f"路由函数: {info['name']}")
print(f"描述: {info['description']}")
print(f"返回值: {info['return_values']}")
```

## 总结

路由函数配置系统通过注册表、加载器和管理器的分层设计，实现了灵活、可扩展的路由函数管理。支持内置函数、配置驱动函数和自定义函数三种实现方式，满足了不同场景的需求。同时，通过配置文件管理路由函数，使得系统更加模块化和可维护。