# 模板变量扩展机制

## 概述

当前项目中的模板变量系统较为基础，仅支持有限的几个变量（如 `max_iterations`, `current_step`, `tool_results_count`, `messages_count`）。本文档详细说明了如何扩展模板变量系统，以支持更多样化和灵活的上下文控制。

## 当前实现分析

### LLM节点中的模板变量处理

当前在 `LLMNode` 中的 `_process_prompt_template` 方法实现如下：

```python
def _process_prompt_template(self, template: str, state: WorkflowState, config: Dict[str, Any]) -> str:
    # 简单的模板变量替换
    variables = {
        "max_iterations": str(state.get("max_iterations", 10)),
        "current_step": state.get("current_step", ""),
        "tool_results_count": str(len(state.get("tool_results", []))),
        "messages_count": str(len(state.get("messages", []))),
    }
    
    result = template
    for key, value in variables.items():
        result = result.replace(f"{{{key}}}", str(value))
    
    return result
```

### 当前局限性

1. **变量数量有限**：仅支持4个基本变量
2. **硬编码实现**：变量逻辑硬编码在方法内部
3. **扩展困难**：无法轻松添加新的变量类型
4. **缺乏灵活性**：无法根据不同的节点类型或配置提供不同的变量

## 扩展设计与实现方案

### 方案1：可插拔模板变量解析器

创建一个可插拔的模板变量解析器系统，允许不同模块提供自己的变量解析器。

#### 1.1 定义接口和基类

```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Protocol
from ..states import WorkflowState

class ITemplateVariableResolver(ABC):
    """模板变量解析器接口"""
    
    @abstractmethod
    def get_variables(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取变量字典"""
        pass
    
    @abstractmethod
    def get_supported_variables(self) -> List[str]:
        """获取支持的变量列表"""
        pass
```

#### 1.2 实现默认变量解析器

```python
class DefaultVariableResolver(ITemplateVariableResolver):
    """默认变量解析器 - 支持基础工作流变量"""
    
    def get_variables(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "max_iterations": str(state.get("max_iterations", 10)),
            "current_step": state.get("current_step", ""),
            "tool_results_count": str(len(state.get("tool_results", []))),
            "messages_count": str(len(state.get("messages", []))),
            "agent_id": state.get("agent_id", ""),
            "current_time": datetime.now().isoformat(),
            "execution_count": state.get("iteration_count", 0),
            "has_errors": str(bool(state.get("errors", []))),
        }
    
    def get_supported_variables(self) -> List[str]:
        return ["max_iterations", "current_step", "tool_results_count", 
                "messages_count", "agent_id", "current_time", 
                "execution_count", "has_errors"]
```

#### 1.3 实现消息相关变量解析器

```python
class MessageVariableResolver(ITemplateVariableResolver):
    """消息相关变量解析器"""
    
    def get_variables(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        messages = state.get("messages", [])
        variables = {
            "last_message": messages[-1].content if messages else "",
            "first_message": messages[0].content if messages else "",
            "last_ai_message": self._get_last_by_type(messages, "ai"),
            "last_human_message": self._get_last_by_type(messages, "human"),
            "last_system_message": self._get_last_by_type(messages, "system"),
            "last_tool_message": self._get_last_by_type(messages, "tool"),
        }
        return variables
    
    def _get_last_by_type(self, messages: List, msg_type: str) -> str:
        """获取最后一条指定类型的消息"""
        for msg in reversed(messages):
            if (hasattr(msg, 'type') and msg.type == msg_type) or \
               (isinstance(msg, dict) and msg.get('type') == msg_type):
                return getattr(msg, 'content', msg.get('content', ''))
        return ""
    
    def get_supported_variables(self) -> List[str]:
        return ["last_message", "first_message", "last_ai_message", 
                "last_human_message", "last_system_message", "last_tool_message"]
```

#### 1.4 实现工具结果相关变量解析器

```python
class ToolResultVariableResolver(ITemplateVariableResolver):
    """工具结果相关变量解析器"""
    
    def get_variables(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        tool_results = state.get("tool_results", [])
        variables = {
            "last_tool_result": self._get_last_tool_result(tool_results),
            "last_tool_name": self._get_last_tool_name(tool_results),
            "successful_tool_calls": str(self._count_successful_calls(tool_results)),
            "failed_tool_calls": str(self._count_failed_calls(tool_results)),
        }
        
        # 添加特定工具结果
        for result in tool_results:
            tool_name = result.get("tool_name", "unknown")
            if tool_name:
                variables[f"last_{tool_name}_result"] = str(result.get("output", ""))
                variables[f"{tool_name}_status"] = "success" if result.get("success") else "failed"
        
        return variables
    
    def _get_last_tool_result(self, tool_results: List) -> str:
        """获取最后一条工具结果"""
        return str(tool_results[-1].get("output", "")) if tool_results else ""
    
    def _get_last_tool_name(self, tool_results: List) -> str:
        """获取最后执行的工具名称"""
        return tool_results[-1].get("tool_name", "") if tool_results else ""
    
    def _count_successful_calls(self, tool_results: List) -> int:
        """统计成功调用数量"""
        return len([r for r in tool_results if r.get("success", False)])
    
    def _count_failed_calls(self, tool_results: List) -> int:
        """统计失败调用数量"""
        return len([r for r in tool_results if not r.get("success", True)])
    
    def get_supported_variables(self) -> List[str]:
        return ["last_tool_result", "last_tool_name", "successful_tool_calls", 
                "failed_tool_calls"]
```

### 方案2：模板引擎集成

使用专门的模板引擎（如 Jinja2）来支持更复杂的模板功能。

#### 2.1 集成Jinja2模板引擎

```python
from jinja2 import Template, Environment, DictLoader
from datetime import datetime

class Jinja2TemplateProcessor:
    """Jinja2模板处理器"""
    
    def __init__(self):
        self.env = Environment()
    
    def process_template(self, template_str: str, state: WorkflowState, config: Dict[str, Any]) -> str:
        """处理Jinja2模板"""
        template = Template(template_str)
        
        # 准备上下文数据
        context = self._build_context(state, config)
        
        return template.render(**context)
    
    def _build_context(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """构建模板上下文"""
        context = {}
        
        # 基础变量
        context.update({
            "state": state,
            "config": config,
            "now": datetime.now(),
            "current_time": datetime.now().isoformat(),
        })
        
        # 消息相关
        messages = state.get("messages", [])
        context.update({
            "messages": messages,
            "message_count": len(messages),
            "last_message": messages[-1] if messages else None,
            "first_message": messages[0] if messages else None,
        })
        
        # 工具结果相关
        tool_results = state.get("tool_results", [])
        context.update({
            "tool_results": tool_results,
            "tool_result_count": len(tool_results),
            "last_tool_result": tool_results[-1] if tool_results else None,
        })
        
        # 执行相关
        context.update({
            "current_step": state.get("current_step", ""),
            "iteration_count": state.get("iteration_count", 0),
            "max_iterations": state.get("max_iterations", 10),
        })
        
        return context
```

### 方案3：配置驱动的变量系统

通过配置文件定义模板变量，支持动态扩展。

#### 3.1 定义配置结构

```yaml
# configs/template_variables.yaml
variables:
  basic:
    - name: "max_iterations"
      path: "max_iterations"
      default: 10
      description: "最大迭代次数"
    - name: "current_step" 
      path: "current_step"
      default: ""
      description: "当前步骤"
  
  messages:
    - name: "last_message"
      function: "get_last_message"
      description: "最后一条消息"
    - name: "message_count"
      path: "messages|length"
      description: "消息数量"
  
  tools:
    - name: "tool_result_count"
      path: "tool_results|length"
      description: "工具结果数量"
    - name: "last_tool_result"
      function: "get_last_tool_result"
      description: "最后工具结果"
```

#### 3.2 配置驱动解析器

```python
class ConfigDrivenVariableResolver(ITemplateVariableResolver):
    """配置驱动的变量解析器"""
    
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader
        self._variable_config = self._load_variable_config()
    
    def _load_variable_config(self):
        """从配置文件加载变量定义"""
        try:
            return self.config_loader.load("template_variables.yaml")
        except:
            # 默认配置
            return {
                "basic": [
                    {"name": "max_iterations", "path": "max_iterations", "default": 10},
                    {"name": "current_step", "path": "current_step", "default": ""},
                    {"name": "tool_results_count", "path": "tool_results|length", "default": 0},
                    {"name": "messages_count", "path": "messages|length", "default": 0}
                ]
            }
    
    def get_variables(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """根据配置构建变量字典"""
        variables = {}
        
        for category, var_list in self._variable_config.items():
            for var_def in var_list:
                var_name = var_def["name"]
                var_path = var_def["path"]
                var_default = var_def.get("default", "")
                
                # 解析变量路径
                if "|" in var_path:  # 使用管道符表示操作，如 length
                    path_parts = var_path.split("|")
                    value = self._get_nested_value(state, path_parts[0])
                    if path_parts[1] == "length":
                        value = len(value) if value else 0
                else:
                    value = self._get_nested_value(state, var_path)
                
                variables[var_name] = str(value if value is not None else var_default)
        
        return variables
    
    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """获取嵌套对象的值"""
        keys = path.split(".")
        current = obj
        
        for key in keys:
            if isinstance(current, dict):
                current = current.get(key)
            elif hasattr(current, key):
                current = getattr(current, key)
            else:
                return None
        
        return current
    
    def get_supported_variables(self) -> List[str]:
        """获取支持的变量列表"""
        variables = []
        for category, var_list in self._variable_config.items():
            for var_def in var_list:
                variables.append(var_def["name"])
        return variables
```

### 方案4：统一模板处理系统

结合以上方案，创建一个统一的模板处理系统：

#### 4.1 模板处理器接口

```python
class ITemplateProcessor(ABC):
    """模板处理器接口"""
    
    @abstractmethod
    def process(self, template: str, state: WorkflowState, config: Dict[str, Any]) -> str:
        """处理模板"""
        pass
```

#### 4.2 统一处理器实现

```python
class UnifiedTemplateProcessor(ITemplateProcessor):
    """统一模板处理器"""
    
    def __init__(self, variable_resolvers: List[ITemplateVariableResolver] = None):
        self.variable_resolvers = variable_resolvers or []
    
    def add_resolver(self, resolver: ITemplateVariableResolver):
        """添加变量解析器"""
        self.variable_resolvers.append(resolver)
    
    def process(self, template: str, state: WorkflowState, config: Dict[str, Any]) -> str:
        """处理模板"""
        # 收集所有变量
        all_variables = {}
        for resolver in self.variable_resolvers:
            all_variables.update(resolver.get_variables(state, config))
        
        # 执行变量替换
        result = template
        for key, value in all_variables.items():
            result = result.replace(f"{{{key}}}", str(value))
        
        return result
```

## 实现建议

### 1. 重构LLMNode的模板处理

将当前硬编码的实现替换为使用统一模板处理器：

```python
# 在LLMNode中
def __init__(self, llm_client: ILLMClient, template_processor: ITemplateProcessor = None):
    self._llm_client = llm_client
    self._template_processor = template_processor or self._create_default_processor()

def _create_default_processor(self) -> ITemplateProcessor:
    """创建默认模板处理器"""
    processor = UnifiedTemplateProcessor()
    
    # 添加默认解析器
    processor.add_resolver(DefaultVariableResolver())
    processor.add_resolver(MessageVariableResolver())
    processor.add_resolver(ToolResultVariableResolver())
    
    return processor

def _process_prompt_template(self, template: str, state: WorkflowState, config: Dict[str, Any]) -> str:
    """处理提示词模板 - 使用统一处理器"""
    return self._template_processor.process(template, state, config)
```

### 2. 扩展支持的变量类型

以下是一些推荐的扩展变量类型：

#### 时间相关变量
- `current_timestamp`: 当前时间戳
- `workflow_start_time`: 工作流开始时间
- `execution_duration`: 执行时长

#### 统计相关变量
- `token_usage`: 令牌使用情况
- `cost_estimate`: 成本估算
- `iteration_percentage`: 迭代进度百分比

#### 状态相关变量
- `is_error_state`: 是否错误状态
- `pending_tasks`: 待处理任务数
- `completion_status`: 完成状态

#### 上下文相关变量
- `context_summary`: 上下文摘要
- `key_entities`: 关键实体
- `relevant_history`: 相关历史记录

## 扩展实现步骤

1. **创建变量解析器接口和基础实现**
2. **重构现有节点以使用新系统**
3. **添加配置文件支持（可选）**
4. **为其他节点类型添加模板支持**
5. **添加测试覆盖**
6. **提供使用文档和示例**

## 向后兼容性

为了保持向后兼容性：
- 保留现有的变量名和行为
- 新的扩展变量使用新命名约定
- 提供迁移路径说明

## 总结

通过实现可插拔的模板变量系统，可以大大增强项目中上下文控制的灵活性。建议采用统一处理器结合多种解析器的方式，既保持了灵活性又便于维护。同时，通过配置驱动的方案，可以支持用户自定义变量而无需修改代码。