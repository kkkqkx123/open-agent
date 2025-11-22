# ToolFactory 职责分析报告（更新版）

## 概述

本报告分析了 `src/core/tools/factory.py` 中 `ToolFactory` 类的职责分配，评估其设计合理性，并结合 services 层已有实现提出改进建议。

## 当前架构概览

### Core 层（核心层）
- `src/core/tools/factory.py` - 工具工厂
- `src/core/tools/manager.py` - 工具管理器（实现 IToolRegistry）
- `src/core/tools/executor.py` - 工具执行器
- `src/core/tools/types/` - 工具类型实现

### Services 层（服务层）
- `src/services/tools/manager.py` - 工具管理服务（实现 IToolManager）
- `src/services/tools/validation/` - 工具验证服务
- `src/services/tools/utils/` - 工具工具类（Schema生成器等）

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

### 2. 重复职责（与 Core/ToolManager 重叠）

#### 2.1 工具创建逻辑
- **Core/ToolManager**: `_create_tool()` 方法（第170-207行）
- **Core/ToolFactory**: `_create_tool_instance()` 方法（第252-312行）
- **问题**: 两处都有工具创建逻辑，存在重复和不一致

#### 2.2 工具缓存
- **Core/ToolManager**: `DefaultToolCache` 类（第439-497行）
- **Core/ToolFactory**: `_tool_cache` 属性和相关方法
- **问题**: 缓存逻辑分散在两处

### 3. 超出职责（应在 Services 层）

#### 3.1 工具集管理
- **当前实现**: `create_tools_from_set()` 方法
- **问题**: 工厂不应该了解工具集的概念
- **建议**: 移至 `src/services/tools/manager.py`

#### 3.2 批量创建
- **当前实现**: `create_tools_from_config()` 方法
- **问题**: 工厂应该专注于单个工具的创建
- **建议**: 移至 `src/services/tools/manager.py`

#### 3.3 注册表集成
- **当前实现**: 与 `ModuleRegistryManager` 集成
- **问题**: 工厂直接依赖外部注册系统
- **建议**: 通过 Services 层进行集成

## Services 层已有功能分析

### 1. 工具管理服务 (`src/services/tools/manager.py`)
- **已实现**: `ToolManager` 类，实现 `IToolManager` 接口
- **功能**: 工具注册、加载、执行和生命周期管理
- **问题**: 仍然依赖 Core 层的 `ToolFactory`

### 2. 工具验证服务 (`src/services/tools/validation/`)
- **已实现**: `ToolValidationManager` 和各种验证器
- **功能**: 配置验证、加载验证、类型特定验证
- **优势**: 良好的职责分离和模块化设计

### 3. 工具工具类 (`src/services/tools/utils/`)
- **已实现**: `SchemaGenerator` 和 `ToolValidator`
- **功能**: Schema生成和验证
- **优势**: 可复用的工具类

## 改进建议

### 1. 职责重新分配

#### 1.1 Core 层 - 纯工厂
```python
# src/core/tools/factory.py
class PureToolFactory(IToolFactory):
    """纯工具工厂，只负责创建工具实例"""
    
    def __init__(self, type_registry: IToolTypeRegistry):
        self._type_registry = type_registry
    
    def create_tool(self, config: IToolConfig) -> ITool:
        # 只负责创建逻辑，不涉及缓存、注册表等
        pass
    
    def register_tool_type(self, tool_type: str, tool_class: Type[ITool]) -> None:
        # 类型注册逻辑
        pass
```

#### 1.2 Core 层 - 工具类型注册表
```python
# src/core/tools/type_registry.py
class ToolTypeRegistry:
    """工具类型注册表，管理工具类型"""
    
    def register_type(self, tool_type: str, tool_class: Type[ITool]) -> None:
        # 类型注册逻辑
        pass
    
    def get_type(self, tool_type: str) -> Type[ITool]:
        # 类型获取逻辑
        pass
```

#### 1.3 Services 层 - 工具创建服务
```python
# src/services/tools/creation_service.py
class ToolCreationService:
    """工具创建服务，协调工厂和缓存"""
    
    def __init__(
        self,
        factory: IToolFactory,
        cache_manager: Optional[IToolCacheManager] = None,
        validator: Optional[IToolValidator] = None
    ):
        self._factory = factory
        self._cache_manager = cache_manager
        self._validator = validator
    
    def create_tool(self, config: IToolConfig) -> ITool:
        # 协调创建、验证、缓存
        pass
    
    def create_tools_from_config(self, configs: List[IToolConfig]) -> List[ITool]:
        # 批量创建逻辑
        pass
    
    def create_tools_from_set(self, set_name: str) -> List[ITool]:
        # 工具集创建逻辑
        pass
```

#### 1.4 Services 层 - 工具缓存管理器
```python
# src/services/tools/cache_manager.py
class ToolCacheManager:
    """工具缓存管理器，统一管理工具缓存"""
    
    def get_or_create(self, key: str, factory: Callable[[], ITool]) -> ITool:
        # 缓存逻辑
        pass
    
    def invalidate(self, key: str) -> bool:
        # 缓存失效
        pass
    
    def clear(self) -> None:
        # 清除缓存
        pass
```

### 2. 配置统一化

#### 2.1 统一配置接口
```python
# src/core/tools/config/interfaces.py
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

#### 2.2 配置工厂（Services 层）
```python
# src/services/tools/config_factory.py
class ToolConfigFactory:
    """配置工厂，负责创建配置对象"""
    
    @staticmethod
    def create_from_dict(config_dict: Dict[str, Any]) -> IToolConfig:
        # 配置创建逻辑
        pass
    
    @staticmethod
    def create_from_file(file_path: str) -> IToolConfig:
        # 从文件创建配置
        pass
```

### 3. 依赖注入重构

#### 3.1 更新 Services/ToolManager
```python
# src/services/tools/manager.py
class ToolManager(IToolManager):
    def __init__(
        self,
        creation_service: ToolCreationService,
        validation_manager: ToolValidationManager,
        executor: IToolExecutor,
        config: Optional[ToolRegistryConfig] = None
    ):
        self._creation_service = creation_service
        self._validation_manager = validation_manager
        self._executor = executor
        self._config = config or ToolRegistryConfig()
        self._tools: Dict[str, ITool] = {}
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化工具管理器"""
        # 使用创建服务加载工具
        tool_configs = self._load_tool_configs()
        for config in tool_configs:
            tool = await self._creation_service.create_tool(config)
            await self.register_tool(tool)
```

#### 3.2 依赖注入配置
```python
# src/infrastructure/di/config/tools_config.py
def configure_tools(container: Container) -> None:
    # 核心层组件
    container.register(IToolTypeRegistry, ToolTypeRegistry)
    container.register(IToolFactory, PureToolFactory)
    
    # 服务层组件
    container.register(ToolConfigFactory)
    container.register(ToolCacheManager)
    container.register(ToolCreationService)
    container.register(ToolValidationManager)
    
    # 工具管理器
    container.register(IToolManager, ToolManager)
    container.register(IToolRegistry, lambda c: c.get(IToolManager))
```

### 4. 移除全局状态

#### 4.1 移除全局工厂
```python
# 删除 src/core/tools/factory.py 中的全局工厂实例
# 删除 get_global_factory() 和 set_global_factory() 函数
# 删除 create_tool() 便捷函数
```

#### 4.2 使用依赖注入
```python
# 通过容器获取工具管理器
tool_manager = container.get(IToolManager)

# 通过工具管理器获取工具
tool = await tool_manager.get_tool("tool_name")
```

## 重构后的架构

```
Services Layer (服务层)
├── ToolManager (工具管理服务)
├── ToolCreationService (工具创建服务)
├── ToolValidationManager (工具验证服务)
├── ToolCacheManager (工具缓存管理器)
├── ToolConfigFactory (配置工厂)
└── SchemaGenerator (Schema生成器)

Core Layer (核心层)
├── PureToolFactory (纯工厂)
├── ToolTypeRegistry (类型注册表)
├── ToolManager (工具注册表实现)
├── AsyncToolExecutor (工具执行器)
└── Tool Types (工具类型实现)
```

## 迁移计划

### 阶段1: 创建新的服务层组件
1. 创建 `ToolCreationService`
2. 创建 `ToolCacheManager`
3. 创建 `ToolConfigFactory`

### 阶段2: 重构 Core 层
1. 简化 `ToolFactory` 为 `PureToolFactory`
2. 创建 `ToolTypeRegistry`
3. 移除 `ToolManager` 中的重复逻辑

### 阶段3: 更新 Services 层
1. 更新 `ToolManager` 使用新的服务组件
2. 更新依赖注入配置
3. 移除全局状态

### 阶段4: 测试和验证
1. 更新单元测试
2. 集成测试
3. 性能测试

## 总结

当前的 `ToolFactory` 类承担了过多职责，与 Core 层的 `ToolManager` 存在职责重叠。通过以下重构可以解决这些问题：

1. **职责分离**: 将工厂拆分为纯工厂和多个专门的服务组件
2. **层级清晰**: Core 层负责核心逻辑，Services 层负责业务服务
3. **依赖注入**: 通过构造函数注入依赖，减少耦合
4. **移除全局状态**: 使用依赖注入容器管理实例

这样的重构将使代码更加清晰、可维护，并且符合项目的扁平化架构原则。