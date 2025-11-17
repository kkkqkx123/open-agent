# ToolFactory 职责分析报告

## 概述

本报告分析了 `src/core/tools/factory.py` 中 `ToolFactory` 类的职责分配，评估其设计合理性，并提出改进建议。

## 当前职责分析

### 1. 核心职责（合理）

#### 1.1 工具实例创建
- **职责**: 根据配置创建不同类型的工具实例
- **实现**: `create_tool()` 方法
- **评估**: ✅ 合理，这是工厂模式的核心职责

#### 1.2 工具类型注册
- **职责**: 注册和管理支持的工具类型
- **实现**: `register_tool_type()`, `get_supported_types()` 方法
- **评估**: ✅ 合理，工厂需要知道如何创建哪些类型的工具

#### 1.3 配置解析
- **职责**: 解析和验证工具配置
- **实现**: `_parse_config()` 方法
- **评估**: ✅ 合理，工厂需要理解配置格式

### 2. 扩展职责（部分合理）

#### 2.1 工具实例缓存
- **职责**: 缓存已创建的工具实例
- **实现**: `_tool_cache`, `clear_cache()`, `get_cache_info()` 方法
- **评估**: ⚠️ 部分合理，但可能违反单一职责原则
- **问题**: 缓存逻辑与工厂创建逻辑混合

#### 2.2 注册表集成
- **职责**: 与模块注册管理器集成
- **实现**: `_initialize_from_registry()`, `create_tool_from_registry()` 等方法
- **评估**: ⚠️ 部分合理，但增加了复杂性
- **问题**: 工厂直接依赖外部注册系统，增加了耦合度

### 3. 超出职责（不合理）

#### 3.1 工具集管理
- **职责**: 从工具集创建多个工具实例
- **实现**: `create_tools_from_set()` 方法
- **评估**: ❌ 不合理，这应该是工具管理器的职责
- **问题**: 工厂不应该了解工具集的概念

#### 3.2 工具查找
- **职责**: 根据名称查找工具实例
- **实现**: `get_tool()` 方法
- **评估**: ❌ 不合理，这应该是注册表或管理器的职责
- **问题**: 工厂不应该维护工具实例的查找逻辑

#### 3.3 批量创建
- **职责**: 从配置列表创建多个工具实例
- **实现**: `create_tools_from_config()` 方法
- **评估**: ❌ 不合理，这应该是工具管理器的职责
- **问题**: 工厂应该专注于单个工具的创建

## 代码质量问题

### 1. 重复代码
```python
# 第78-87行和第84-88行重复注册RestTool
try:
    from .types.rest_tool import RestTool
    self._tool_types["rest"] = RestTool
except ImportError:
    logger.warning("无法导入 RestTool")

try:
    from .types.rest_tool import RestTool
    self._tool_types["rest"] = RestTool
except ImportError:
    logger.warning("无法导入 RestTool")
```

### 2. 硬编码配置创建
```python
# 第265-292行硬编码创建配置对象
rest_config = type('RestToolConfig', (), {
    'name': config.name,
    'description': config.description,
    # ...
})()
```

### 3. 配置类型不一致
- 工厂接受多种配置类型：`Dict[str, Any]`, `ToolConfig`, `NativeToolConfig`, `RestToolConfig`, `MCPToolConfig`
- 缺乏统一的配置接口，增加了复杂性

## 架构问题

### 1. 违反单一职责原则
工厂类承担了太多职责：
- 工具创建
- 类型注册
- 实例缓存
- 注册表集成
- 工具集管理
- 工具查找

### 2. 过度依赖外部系统
- 直接依赖 `ModuleRegistryManager` 和 `DynamicImporter`
- 与注册表系统紧密耦合

### 3. 全局状态管理
```python
# 第524-560行全局工厂实例
_global_factory: Optional[ToolFactory] = None

def get_global_factory() -> ToolFactory:
    # ...
```

## 改进建议

### 1. 职责分离

#### 1.1 纯工厂类
```python
class PureToolFactory(IToolFactory):
    """纯工具工厂，只负责创建工具实例"""
    
    def __init__(self, type_registry: IToolTypeRegistry):
        self._type_registry = type_registry
    
    def create_tool(self, config: ToolConfig) -> ITool:
        # 只负责创建逻辑
        pass
```

#### 1.2 工具类型注册表
```python
class ToolTypeRegistry(IToolTypeRegistry):
    """工具类型注册表，管理工具类型"""
    
    def register_type(self, tool_type: str, tool_class: Type[ITool]) -> None:
        # 类型注册逻辑
        pass
```

#### 1.3 工具缓存管理器
```python
class ToolCacheManager:
    """工具缓存管理器，负责工具实例缓存"""
    
    def get_or_create(self, key: str, factory: Callable[[], ITool]) -> ITool:
        # 缓存逻辑
        pass
```

### 2. 配置统一化

#### 2.1 统一配置接口
```python
class IToolConfig(ABC):
    """工具配置统一接口"""
    
    @property
    @abstractmethod
    def tool_type(self) -> str:
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        pass
```

#### 2.2 配置工厂
```python
class ToolConfigFactory:
    """配置工厂，负责创建配置对象"""
    
    @staticmethod
    def create_from_dict(config_dict: Dict[str, Any]) -> IToolConfig:
        # 配置创建逻辑
        pass
```

### 3. 依赖注入

#### 3.1 构造函数注入
```python
class ToolFactory(IToolFactory):
    def __init__(
        self,
        type_registry: IToolTypeRegistry,
        config_factory: ToolConfigFactory,
        cache_manager: Optional[ToolCacheManager] = None
    ):
        self._type_registry = type_registry
        self._config_factory = config_factory
        self._cache_manager = cache_manager
```

### 4. 移除全局状态

#### 4.1 依赖注入容器
```python
# 在容器中注册工厂
container.register(IToolFactory, ToolFactory)
container.register(IToolTypeRegistry, ToolTypeRegistry)
container.register(ToolCacheManager, ToolCacheManager)
```

## 重构后的架构

```
ToolFactory (纯工厂)
    ↓
ToolTypeRegistry (类型管理)
    ↓
ToolConfigFactory (配置创建)
    ↓
ToolCacheManager (缓存管理)
    ↓
ToolManager (工具管理)
```

## 总结

当前的 `ToolFactory` 类承担了过多职责，违反了单一职责原则，导致代码复杂且难以维护。建议进行以下重构：

1. **职责分离**: 将工厂拆分为多个专门的类
2. **配置统一**: 使用统一的配置接口和工厂
3. **依赖注入**: 通过构造函数注入依赖，减少耦合
4. **移除全局状态**: 使用依赖注入容器管理实例

这样的重构将使代码更加清晰、可维护，并且符合SOLID原则。