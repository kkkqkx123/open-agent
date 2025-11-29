# 元素构建器工厂使用指南

## 📋 概述

本文档展示了如何正确使用修复后的元素构建器工厂，包括类型安全的节点和边构建器创建、注册和使用。

## 🔧 修复内容

### 问题分析
原始的 `element_builder_factory.py` 存在以下问题：
1. **未使用的导入**：`INodeBuilder`, `IEdgeBuilder`, `NodeConfig`, `EdgeConfig` 被导入但未使用
2. **类型安全性缺失**：没有区分节点和边构建器的类型
3. **功能不完整**：缺少针对特定元素类型的专门处理

### 修复内容
1. **添加专门的构建器注册方法**：
   - `register_node_builder()` - 注册节点构建器
   - `register_edge_builder()` - 注册边构建器

2. **添加类型安全的创建方法**：
   - `create_node_builder()` - 创建节点构建器，返回 `INodeBuilder`
   - `create_edge_builder()` - 创建边构建器，返回 `IEdgeBuilder`

3. **增强的类型检查**：
   - 确保节点构建器实现 `INodeBuilder` 接口
   - 确保边构建器实现 `IEdgeBuilder` 接口

4. **便捷函数**：
   - `register_node_builder()` - 全局注册节点构建器
   - `register_edge_builder()` - 全局注册边构建器
   - `create_node_builder()` - 全局创建节点构建器
   - `create_edge_builder()` - 全局创建边构建器

## 📖 使用示例

### 1. 基本使用

```python
from src.core.workflow.graph.builder.element_builder_factory import (
    get_builder_factory, create_node_builder, create_edge_builder
)
from src.interfaces.workflow.element_builder import BuildContext
from src.core.workflow.config.config import NodeConfig, EdgeConfig

# 创建构建上下文
context = BuildContext(
    graph_config=graph_config,
    function_resolver=function_resolver,
    logger=logger
)

# 创建节点构建器（类型安全）
node_builder = create_node_builder("node", context)
# 返回类型：INodeBuilder

# 创建边构建器（类型安全）
edge_builder = create_edge_builder("edge", context)
# 返回类型：IEdgeBuilder

# 使用构建器
node_function = node_builder.build_element(node_config, context)
edge_data = edge_builder.build_element(edge_config, context)
```

### 2. 注册自定义构建器

```python
from src.core.workflow.graph.builder.element_builder_factory import (
    register_node_builder, register_edge_builder
)
from src.core.workflow.graph.builder.base_element_builder import BaseNodeBuilder, BaseEdgeBuilder

# 自定义节点构建器
class CustomNodeBuilder(BaseNodeBuilder):
    def _build_element_impl(self, config: NodeConfig, context: BuildContext):
        # 自定义节点构建逻辑
        return lambda state: state

# 自定义边构建器
class CustomEdgeBuilder(BaseEdgeBuilder):
    def _build_element_impl(self, config: EdgeConfig, context: BuildContext):
        # 自定义边构建逻辑
        return {"config": config}

# 注册自定义构建器
register_node_builder("custom_node", CustomNodeBuilder)
register_edge_builder("custom_edge", CustomEdgeBuilder)

# 使用自定义构建器
custom_node_builder = create_node_builder("custom_node", context)
custom_edge_builder = create_edge_builder("custom_edge", context)
```

### 3. 工厂直接使用

```python
from src.core.workflow.graph.builder.element_builder_factory import get_builder_factory

# 获取工厂实例
factory = get_builder_factory()

# 查看支持的类型
print("支持的节点类型:", factory.get_supported_node_types())
print("支持的边类型:", factory.get_supported_edge_types())
print("所有支持的类型:", factory.get_supported_types())

# 创建构建器
node_builder = factory.create_node_builder("node", context)
edge_builder = factory.create_edge_builder("edge", context)

# 注册新的构建器
factory.register_node_builder("another_node", AnotherNodeBuilder)
factory.register_edge_builder("another_edge", AnotherEdgeBuilder)
```

### 4. 多环境工厂使用

```python
from src.core.workflow.graph.builder.element_builder_factory import get_builder_manager

# 获取构建器管理器
manager = get_builder_manager()

# 创建开发环境工厂
dev_factory = manager.create_factory("development", {
    "custom_builders": {
        "dev_node": "myapp.builders.DevNodeBuilder",
        "dev_edge": "myapp.builders.DevEdgeBuilder"
    },
    "validation": {
        "enabled": True,
        "strict_mode": False
    }
})

# 创建生产环境工厂
prod_factory = manager.create_factory("production", {
    "custom_builders": {
        "prod_node": "myapp.builders.ProdNodeBuilder",
        "prod_edge": "myapp.builders.ProdEdgeBuilder"
    },
    "validation": {
        "enabled": True,
        "strict_mode": True
    }
})

# 使用特定环境的工厂
dev_node_builder = manager.get_factory("development").create_node_builder("dev_node", context)
prod_node_builder = manager.get_factory("production").create_node_builder("prod_node", context)
```

### 5. 类型安全的构建器实现

```python
from src.interfaces.workflow.element_builder import INodeBuilder, IEdgeBuilder
from src.core.workflow.config.config import NodeConfig, EdgeConfig

class TypedNodeBuilder(INodeBuilder):
    """类型安全的节点构建器"""
    
    def get_element_type(self) -> str:
        return "typed_node"
    
    def can_build(self, config: NodeConfig) -> bool:
        return isinstance(config, NodeConfig) and config.function_name.startswith("typed_")
    
    def validate_config(self, config: NodeConfig, context: BuildContext) -> List[str]:
        errors = []
        if not config.function_name.startswith("typed_"):
            errors.append("函数名必须以 'typed_' 开头")
        return errors
    
    def build_element(self, config: NodeConfig, context: BuildContext):
        # 类型安全的节点构建逻辑
        def typed_node_function(state):
            # 实现特定的节点逻辑
            return state
        return typed_node_function
    
    def add_to_graph(self, element, builder, config: NodeConfig, context: BuildContext):
        builder.add_node(config.name, element)
    
    def get_node_function(self, config: NodeConfig, context: BuildContext):
        return self.build_element(config, context)

class TypedEdgeBuilder(IEdgeBuilder):
    """类型安全的边构建器"""
    
    def get_element_type(self) -> str:
        return "typed_edge"
    
    def can_build(self, config: EdgeConfig) -> bool:
        return isinstance(config, EdgeConfig) and hasattr(config, 'typed_property')
    
    def validate_config(self, config: EdgeConfig, context: BuildContext) -> List[str]:
        errors = []
        if not hasattr(config, 'typed_property'):
            errors.append("缺少 typed_property 属性")
        return errors
    
    def build_element(self, config: EdgeConfig, context: BuildContext):
        # 类型安全的边构建逻辑
        return {
            "config": config,
            "typed_property": config.typed_property
        }
    
    def add_to_graph(self, element, builder, config: EdgeConfig, context: BuildContext):
        # 添加边到图的逻辑
        pass
    
    def get_edge_function(self, config: EdgeConfig, context: BuildContext):
        if config.condition:
            return context.function_resolver.get_condition_function(config.condition)
        return None

# 注册类型安全的构建器
register_node_builder("typed_node", TypedNodeBuilder)
register_edge_builder("typed_edge", TypedEdgeBuilder)
```

## 🎯 优势

### 1. 类型安全性
```python
# 之前：返回类型不明确
builder = factory.create_builder("node", context)  # 返回 IElementBuilder
# 无法确保 builder 有节点特定的方法

# 现在：类型安全
node_builder = factory.create_node_builder("node", context)  # 返回 INodeBuilder
# 确保 node_builder 有 get_node_function() 等节点特定方法
```

### 2. 接口一致性
```python
# 所有节点构建器都实现 INodeBuilder
# 所有边构建器都实现 IEdgeBuilder
# 确保接口的一致性和可预测性
```

### 3. 扩展性
```python
# 可以轻松添加新的元素类型
factory.register_node_builder("new_node_type", NewNodeBuilder)
factory.register_edge_builder("new_edge_type", NewEdgeBuilder)
```

### 4. 错误检查
```python
# 类型检查在注册时进行
try:
    factory.register_node_builder("invalid", InvalidBuilder)  # 不实现 INodeBuilder
except ValueError as e:
    print(f"注册失败: {e}")
```

## 📋 最佳实践

### 1. 使用类型注解
```python
def create_custom_node(context: BuildContext) -> INodeBuilder:
    """创建自定义节点构建器"""
    return create_node_builder("custom_node", context)
```

### 2. 验证构建器类型
```python
def validate_builder(builder: IElementBuilder, expected_type: type) -> bool:
    """验证构建器类型"""
    return isinstance(builder, expected_type)
```

### 3. 使用工厂管理器进行多环境配置
```python
# 为不同环境创建不同的工厂配置
configs = {
    "development": {"validation": {"strict_mode": False}},
    "testing": {"validation": {"strict_mode": True}},
    "production": {"validation": {"strict_mode": True, "fail_on_warning": True}}
}

for env, config in configs.items():
    manager.create_factory(env, config)
```

### 4. 错误处理
```python
try:
    builder = create_node_builder("unknown_type", context)
except ValueError as e:
    logger.error(f"创建构建器失败: {e}")
    # 使用默认构建器或回退逻辑
    builder = create_node_builder("node", context)
```

## 🔍 故障排除

### 常见问题

1. **导入错误**
   ```python
   # 错误：导入未使用的接口
   from src.interfaces.workflow.element_builder import INodeBuilder, IEdgeBuilder
   
   # 正确：只导入需要的接口
   from src.interfaces.workflow.element_builder import INodeBuilder
   ```

2. **类型不匹配**
   ```python
   # 错误：将边构建器注册为节点构建器
   register_node_builder("edge", EdgeBuilder)  # 会抛出 ValueError
   
   # 正确：使用正确的注册方法
   register_edge_builder("edge", EdgeBuilder)
   ```

3. **工厂不存在**
   ```python
   # 错误：访问不存在的工厂
   factory = manager.get_factory("nonexistent")  # 会抛出 ValueError
   
   # 正确：检查工厂是否存在或使用默认工厂
   factory = manager.get_factory("default")
   ```

## 📊 性能考虑

1. **缓存机制**：工厂会缓存构建器实例，避免重复创建
2. **延迟加载**：构建器只在需要时创建
3. **类型检查开销**：注册时的类型检查是一次性的，运行时开销很小

通过这些修复和改进，元素构建器工厂现在提供了完整的类型安全性和更好的用户体验。