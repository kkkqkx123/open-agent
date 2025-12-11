# 全模块配置系统整合设计文档

## 概述

本文档设计一个统一的全模块配置系统，整合所有核心模块（workflow、llm、tools、state、storage、sessions）的配置功能，基于三层架构模式提供一致、可扩展的配置管理解决方案。

## 当前模块配置现状分析

### 1. Workflow模块配置

#### 现状
- **配置映射器**：`src/core/workflow/mappers/config_mapper.py`
- **业务实体**：`src/core/workflow/graph_entities.py`
- **配置验证**：`src/core/workflow/validation.py`
- **模板系统**：`src/core/workflow/templates/`

#### 配置特点
- 复杂的图结构配置（节点、边、状态）
- 多种模板支持（状态机、组合工作流）
- 动态配置验证和转换

### 2. LLM模块配置

#### 现状
- **配置处理器**：`src/core/llm/llm_config_processor.py`
- **客户端工厂**：`src/core/llm/factory.py`
- **包装器系统**：`src/core/llm/wrappers/`
- **多种客户端**：OpenAI、Anthropic、Gemini、Mock等

#### 配置特点
- 多提供商支持（OpenAI、Anthropic、Gemini等）
- 客户端缓存和池化
- 降级和容错机制
- 动态模型切换

### 3. Tools模块配置

#### 现状
- **配置类**：`src/core/tools/config.py`
- **加载器**：`src/core/tools/loaders.py`
- **工厂**：`src/core/tools/factory.py`
- **管理器**：`src/core/tools/manager.py`

#### 配置特点
- 多种工具类型（Builtin、Native、REST、MCP）
- 状态管理配置
- 动态工具注册
- 工具链配置

### 4. 其他模块配置

#### State模块
- 状态管理器配置
- 快照策略配置
- 缓存配置

#### Storage模块
- 存储适配器配置
- 连接池配置
- 备份策略配置

#### Sessions模块
- 会话管理配置
- 线程管理配置
- 检查点配置

## 统一配置系统架构设计

### 1. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Services Layer (服务层)                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │WorkflowConfig   │  │LLMConfigService │  │ToolsConfigService│ │
│  │Service          │  │                 │  │                 │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │StateConfig      │  │StorageConfig   │  │SessionConfig    │ │
│  │Service          │  │Service         │  │Service          │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer (核心层)                     │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │UnifiedConfig    │  │ModuleConfig    │  │ConfigMapper     │ │
│  │Manager          │  │Registry        │  │Registry         │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │WorkflowMapper   │  │LLMMapper        │  │ToolsMapper      │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │StateMapper      │  │StorageMapper   │  │SessionMapper    │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer (基础设施层)             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ConfigLoader     │  │ProcessorChain  │  │ConfigValidator  │ │
│  │(Enhanced)       │  │(Enhanced)      │  │(Enhanced)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ModuleConfig     │  │CrossModule     │  │ConfigCache      │ │
│  │Providers       │  │Resolver        │  │(Enhanced)       │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### 2. 核心组件设计

#### 2.1 Services Layer - 统一配置服务

**UnifiedConfigService** (新增)
```python
class UnifiedConfigService:
    """统一配置服务 - 所有模块配置的统一入口"""
    
    def __init__(self, 
                 config_manager: IUnifiedConfigManager,
                 module_services: Dict[str, IModuleConfigService]):
        self.config_manager = config_manager
        self.module_services = module_services
    
    def load_module_config(self, module_type: str, config_path: str) -> Any:
        """加载模块配置"""
        service = self.module_services.get(module_type)
        if not service:
            raise ValueError(f"不支持的模块类型: {module_type}")
        return service.load_config(config_path)
    
    def save_module_config(self, module_type: str, config: Any, config_path: str) -> None:
        """保存模块配置"""
        service = self.module_services.get(module_type)
        if not service:
            raise ValueError(f"不支持的模块类型: {module_type}")
        service.save_config(config, config_path)
    
    def validate_module_config(self, module_type: str, config: Any) -> ValidationResult:
        """验证模块配置"""
        service = self.module_services.get(module_type)
        if not service:
            raise ValueError(f"不支持的模块类型: {module_type}")
        return service.validate_config(config)
```

**模块特定服务**
```python
class WorkflowConfigService:
    """工作流配置服务"""
    
    def load_config(self, config_path: str) -> Graph:
        """加载工作流配置"""
        config_data = self.config_manager.load_config(config_path, "workflow")
        return self.mapper.dict_to_graph(config_data)
    
    def save_config(self, graph: Graph, config_path: str) -> None:
        """保存工作流配置"""
        config_data = self.mapper.graph_to_dict(graph)
        self.config_manager.save_config(config_data, config_path)

class LLMConfigService:
    """LLM配置服务"""
    
    def load_config(self, config_path: str) -> LLMClientConfig:
        """加载LLM配置"""
        config_data = self.config_manager.load_config(config_path, "llm")
        return self.mapper.dict_to_client_config(config_data)
    
    def create_client(self, config_path: str) -> ILLMClient:
        """创建LLM客户端"""
        config = self.load_config(config_path)
        return self.factory.create_client(config)

class ToolsConfigService:
    """工具配置服务"""
    
    def load_config(self, config_path: str) -> List[ToolConfig]:
        """加载工具配置"""
        config_data = self.config_manager.load_config(config_path, "tools")
        return self.mapper.dict_to_tool_configs(config_data)
    
    def create_tools(self, config_path: str) -> List[ITool]:
        """创建工具实例"""
        configs = self.load_config(config_path)
        return [self.factory.create_tool(config) for config in configs]
```

#### 2.2 Core Layer - 统一配置管理

**UnifiedConfigManager** (增强现有)
```python
class UnifiedConfigManager(IUnifiedConfigManager):
    """统一配置管理器 - 支持所有模块的配置管理"""
    
    def __init__(self, 
                 config_loader: IConfigLoader,
                 processor_factory: IProcessorFactory,
                 validator_registry: IValidatorRegistry,
                 module_registry: IModuleConfigRegistry):
        self.config_loader = config_loader
        self.processor_factory = processor_factory
        self.validator_registry = validator_registry
        self.module_registry = module_registry
    
    def load_config(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置 - 支持模块特定处理"""
        # 1. 加载原始配置
        raw_config = self.config_loader.load(config_path)
        
        # 2. 获取模块特定的处理器链
        processor_chain = self.processor_factory.create_chain(module_type)
        
        # 3. 处理配置
        processed_config = processor_chain.process(raw_config, config_path)
        
        # 4. 获取模块特定的验证器
        validator = self.validator_registry.get_validator(module_type)
        
        # 5. 验证配置
        validation_result = validator.validate(processed_config)
        if not validation_result.is_valid:
            raise ConfigValidationError(f"配置验证失败: {validation_result.errors}")
        
        # 6. 应用模块特定的后处理
        if module_type:
            processed_config = self.module_registry.post_process(module_type, processed_config)
        
        return processed_config
    
    def register_module_config(self, module_type: str, config: ModuleConfig) -> None:
        """注册模块配置"""
        self.module_registry.register_module(module_type, config)
        self.processor_factory.register_processors(module_type, config.processors)
        self.validator_registry.register_validator(module_type, config.validator)
```

**ModuleConfigRegistry** (新增)
```python
class ModuleConfigRegistry:
    """模块配置注册表"""
    
    def __init__(self):
        self._modules: Dict[str, ModuleConfig] = {}
        self._cross_module_resolvers: List[ICrossModuleResolver] = []
    
    def register_module(self, module_type: str, config: ModuleConfig) -> None:
        """注册模块配置"""
        self._modules[module_type] = config
    
    def get_module_config(self, module_type: str) -> Optional[ModuleConfig]:
        """获取模块配置"""
        return self._modules.get(module_type)
    
    def post_process(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """模块特定后处理"""
        module_config = self._modules.get(module_type)
        if module_config and module_config.post_processor:
            return module_config.post_processor.process(config)
        return config
    
    def register_cross_module_resolver(self, resolver: ICrossModuleResolver) -> None:
        """注册跨模块解析器"""
        self._cross_module_resolvers.append(resolver)
    
    def resolve_cross_module_references(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析跨模块引用"""
        for resolver in self._cross_module_resolvers:
            config = resolver.resolve(module_type, config)
        return config
```

**ConfigMapperRegistry** (新增)
```python
class ConfigMapperRegistry:
    """配置映射器注册表"""
    
    def __init__(self):
        self._mappers: Dict[str, IConfigMapper] = {}
    
    def register_mapper(self, module_type: str, mapper: IConfigMapper) -> None:
        """注册配置映射器"""
        self._mappers[module_type] = mapper
    
    def get_mapper(self, module_type: str) -> Optional[IConfigMapper]:
        """获取配置映射器"""
        return self._mappers.get(module_type)
    
    def dict_to_entity(self, module_type: str, config_data: Dict[str, Any]) -> Any:
        """将配置字典转换为业务实体"""
        mapper = self.get_mapper(module_type)
        if not mapper:
            raise ValueError(f"未找到模块 {module_type} 的配置映射器")
        return mapper.dict_to_entity(config_data)
    
    def entity_to_dict(self, module_type: str, entity: Any) -> Dict[str, Any]:
        """将业务实体转换为配置字典"""
        mapper = self.get_mapper(module_type)
        if not mapper:
            raise ValueError(f"未找到模块 {module_type} 的配置映射器")
        return mapper.entity_to_dict(entity)
```

#### 2.3 Infrastructure Layer - 增强基础设施

**EnhancedConfigLoader** (增强现有)
```python
class EnhancedConfigLoader(IConfigLoader):
    """增强的配置加载器 - 支持模块特定加载策略"""
    
    def __init__(self, 
                 base_path: Path,
                 module_loaders: Dict[str, IModuleConfigLoader]):
        self.base_path = base_path
        self.module_loaders = module_loaders
    
    def load(self, config_path: str, module_type: Optional[str] = None) -> Dict[str, Any]:
        """加载配置 - 支持模块特定加载"""
        if module_type and module_type in self.module_loaders:
            return self.module_loaders[module_type].load(config_path)
        return self._default_load(config_path)
    
    def register_module_loader(self, module_type: str, loader: IModuleConfigLoader) -> None:
        """注册模块特定加载器"""
        self.module_loaders[module_type] = loader
```

**CrossModuleResolver** (新增)
```python
class CrossModuleResolver(ICrossModuleResolver):
    """跨模块引用解析器"""
    
    def __init__(self, config_manager: IUnifiedConfigManager):
        self.config_manager = config_manager
    
    def resolve(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析跨模块引用"""
        # 解析 ${module.reference} 格式的引用
        import re
        
        def replace_reference(match):
            ref_module = match.group(1)
            ref_path = match.group(2)
            
            # 加载引用的配置
            ref_config = self.config_manager.load_config(ref_path, ref_module)
            
            # 获取引用值
            keys = ref_path.split('.')
            value = ref_config
            for key in keys:
                value = value.get(key, {})
            
            return str(value)
        
        # 递归解析所有引用
        pattern = r'\$\{([^\.]+)\.([^}]+)\}'
        config_str = json.dumps(config)
        
        while re.search(pattern, config_str):
            config_str = re.sub(pattern, replace_reference, config_str)
        
        return json.loads(config_str)
```

### 3. 模块配置标准化

#### 3.1 统一配置接口

**IConfigMapper** (新增接口)
```python
class IConfigMapper(ABC):
    """配置映射器接口"""
    
    @abstractmethod
    def dict_to_entity(self, config_data: Dict[str, Any]) -> Any:
        """将配置字典转换为业务实体"""
        pass
    
    @abstractmethod
    def entity_to_dict(self, entity: Any) -> Dict[str, Any]:
        """将业务实体转换为配置字典"""
        pass
    
    @abstractmethod
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证配置数据"""
        pass
```

**IModuleConfigService** (新增接口)
```python
class IModuleConfigService(ABC):
    """模块配置服务接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> Any:
        """加载模块配置"""
        pass
    
    @abstractmethod
    def save_config(self, config: Any, config_path: str) -> None:
        """保存模块配置"""
        pass
    
    @abstractmethod
    def validate_config(self, config: Any) -> ValidationResult:
        """验证模块配置"""
        pass
```

#### 3.2 模块配置规范

**Workflow模块配置规范**
```python
class WorkflowConfigMapper(IConfigMapper):
    """工作流配置映射器"""
    
    def dict_to_entity(self, config_data: Dict[str, Any]) -> Graph:
        """转换为Graph实体"""
        return self.dict_to_graph(config_data)
    
    def entity_to_dict(self, entity: Graph) -> Dict[str, Any]:
        """转换为配置字典"""
        return self.graph_to_dict(entity)
    
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证工作流配置"""
        # 使用现有的验证逻辑
        validator = WorkflowValidator()
        return validator.validate_config(config_data)
```

**LLM模块配置规范**
```python
class LLMConfigMapper(IConfigMapper):
    """LLM配置映射器"""
    
    def dict_to_entity(self, config_data: Dict[str, Any]) -> LLMClientConfig:
        """转换为LLM客户端配置"""
        # 根据model_type创建相应的配置对象
        model_type = config_data.get("model_type")
        if model_type == "openai":
            return OpenAIConfig(**config_data)
        elif model_type == "anthropic":
            return AnthropicConfig(**config_data)
        elif model_type == "gemini":
            return GeminiConfig(**config_data)
        else:
            return LLMClientConfig(**config_data)
    
    def entity_to_dict(self, entity: LLMClientConfig) -> Dict[str, Any]:
        """转换为配置字典"""
        return asdict(entity)
    
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证LLM配置"""
        # 验证必需字段
        required_fields = ["model_type", "model_name"]
        errors = []
        
        for field in required_fields:
            if field not in config_data:
                errors.append(f"缺少必需字段: {field}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

**Tools模块配置规范**
```python
class ToolsConfigMapper(IConfigMapper):
    """工具配置映射器"""
    
    def dict_to_entity(self, config_data: Dict[str, Any]) -> List[ToolConfig]:
        """转换为工具配置列表"""
        tools = []
        
        if "tools" in config_data:
            for tool_config in config_data["tools"]:
                tool_type = tool_config.get("tool_type")
                if tool_type == "rest":
                    tools.append(RestToolConfig(**tool_config))
                elif tool_type == "native":
                    tools.append(NativeToolConfig(**tool_config))
                elif tool_type == "mcp":
                    tools.append(MCPToolConfig(**tool_config))
                elif tool_type == "builtin":
                    tools.append(BuiltinToolConfig(**tool_config))
        
        return tools
    
    def entity_to_dict(self, entity: List[ToolConfig]) -> Dict[str, Any]:
        """转换为配置字典"""
        return {"tools": [asdict(tool) for tool in entity]}
    
    def validate_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """验证工具配置"""
        errors = []
        
        if "tools" not in config_data:
            errors.append("缺少tools字段")
            return ValidationResult(is_valid=False, errors=errors)
        
        for i, tool_config in enumerate(config_data["tools"]):
            if "tool_type" not in tool_config:
                errors.append(f"工具 {i} 缺少tool_type字段")
            if "name" not in tool_config:
                errors.append(f"工具 {i} 缺少name字段")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
```

### 4. 跨模块配置支持

#### 4.1 跨模块引用

**配置引用格式**
```yaml
# workflow配置中引用LLM配置
workflow:
  name: "example_workflow"
  llm_client: "${llm.default_client}"
  tools: "${tools.enabled_tools}"

# llm配置
llm:
  default_client:
    model_type: "openai"
    model_name: "gpt-4"
    api_key: "${env.OPENAI_API_KEY}"

# tools配置
tools:
  enabled_tools:
    - name: "calculator"
      tool_type: "builtin"
    - name: "search"
      tool_type: "rest"
      api_url: "https://api.example.com/search"
```

#### 4.2 模块依赖管理

**ModuleDependency** (新增)
```python
@dataclass
class ModuleDependency:
    """模块依赖"""
    module_type: str
    config_path: str
    required_fields: List[str]
    optional_fields: List[str] = field(default_factory=list)

class ModuleDependencyManager:
    """模块依赖管理器"""
    
    def __init__(self):
        self._dependencies: Dict[str, List[ModuleDependency]] = {}
    
    def register_dependency(self, module_type: str, dependency: ModuleDependency) -> None:
        """注册模块依赖"""
        if module_type not in self._dependencies:
            self._dependencies[module_type] = []
        self._dependencies[module_type].append(dependency)
    
    def resolve_dependencies(self, module_type: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """解析模块依赖"""
        resolved_config = config.copy()
        
        if module_type in self._dependencies:
            for dependency in self._dependencies[module_type]:
                dep_config = self._load_dependency_config(dependency)
                resolved_config = self._merge_dependency(resolved_config, dep_config, dependency)
        
        return resolved_config
```

### 5. 配置热重载和监控

#### 5.1 配置监控

**ConfigMonitor** (新增)
```python
class ConfigMonitor:
    """配置监控器"""
    
    def __init__(self, config_manager: IUnifiedConfigManager):
        self.config_manager = config_manager
        self._watchers: Dict[str, IConfigWatcher] = {}
        self._listeners: List[IConfigChangeListener] = []
    
    def start_watching(self, module_type: str, config_path: str) -> None:
        """开始监控配置文件"""
        watcher = FileConfigWatcher(config_path)
        watcher.add_change_listener(lambda: self._on_config_change(module_type, config_path))
        watcher.start()
        self._watchers[f"{module_type}:{config_path}"] = watcher
    
    def add_change_listener(self, listener: IConfigChangeListener) -> None:
        """添加配置变更监听器"""
        self._listeners.append(listener)
    
    def _on_config_change(self, module_type: str, config_path: str) -> None:
        """配置变更处理"""
        try:
            # 重新加载配置
            new_config = self.config_manager.load_config(config_path, module_type)
            
            # 通知监听器
            event = ConfigChangeEvent(
                module_type=module_type,
                config_path=config_path,
                new_config=new_config
            )
            
            for listener in self._listeners:
                listener.on_config_changed(event)
                
        except Exception as e:
            logger.error(f"配置重载失败 {module_type}:{config_path}: {e}")
```

#### 5.2 配置版本管理

**ConfigVersionManager** (新增)
```python
class ConfigVersionManager:
    """配置版本管理器"""
    
    def __init__(self, storage: IConfigStorage):
        self.storage = storage
    
    def save_version(self, module_type: str, config_path: str, config: Dict[str, Any], 
                    version: str, comment: str = "") -> None:
        """保存配置版本"""
        version_info = ConfigVersion(
            module_type=module_type,
            config_path=config_path,
            version=version,
            config=config,
            comment=comment,
            timestamp=datetime.now()
        )
        self.storage.save_version(version_info)
    
    def load_version(self, module_type: str, config_path: str, version: str) -> Dict[str, Any]:
        """加载指定版本的配置"""
        version_info = self.storage.load_version(module_type, config_path, version)
        return version_info.config
    
    def list_versions(self, module_type: str, config_path: str) -> List[ConfigVersion]:
        """列出配置版本"""
        return self.storage.list_versions(module_type, config_path)
    
    def rollback(self, module_type: str, config_path: str, version: str) -> None:
        """回滚到指定版本"""
        config = self.load_version(module_type, config_path, version)
        # 保存回滚后的配置作为新版本
        self.save_version(module_type, config_path, config, f"rollback_to_{version}")
```

### 6. 实施计划

#### 阶段1：基础设施增强（2周）
1. **增强ConfigLoader**：添加模块特定加载支持
2. **实现CrossModuleResolver**：支持跨模块引用
3. **创建ConfigMapperRegistry**：统一映射器管理
4. **实现ModuleConfigRegistry**：模块配置注册

#### 阶段2：核心层重构（3周）
1. **重构UnifiedConfigManager**：支持多模块配置
2. **实现模块特定ConfigService**：Workflow、LLM、Tools
3. **创建UnifiedConfigService**：统一配置入口
4. **实现配置验证标准化**

#### 阶段3：服务层完善（2周）
1. **完善模块配置服务**：State、Storage、Sessions
2. **实现配置监控**：热重载支持
3. **添加版本管理**：配置版本控制
4. **实现依赖管理**：模块依赖解析

#### 阶段4：集成测试（1周）
1. **端到端测试**：完整配置流程测试
2. **性能测试**：配置加载性能验证
3. **兼容性测试**：向后兼容性验证
4. **文档完善**：API文档和使用指南

### 7. 使用示例

#### 7.1 基本使用

```python
# 创建统一配置服务
config_service = create_unified_config_service()

# 加载工作流配置
workflow = config_service.load_module_config("workflow", "my_workflow.yaml")

# 加载LLM客户端
llm_client = config_service.load_module_config("llm", "openai_client.yaml")

# 加载工具列表
tools = config_service.load_module_config("tools", "tool_set.yaml")

# 执行工作流
result = workflow.execute({
    "llm_client": llm_client,
    "tools": tools
})
```

#### 7.2 跨模块引用

```python
# 配置文件中引用其他模块配置
# workflow.yaml
workflow:
  name: "data_processing"
  llm_config: "${llm.data_processing_llm}"
  tool_configs: "${tools.data_processing_tools}"

# 自动解析跨模块引用
workflow = config_service.load_module_config("workflow", "workflow.yaml")
```

#### 7.3 配置监控

```python
# 添加配置变更监听器
class MyConfigListener(IConfigChangeListener):
    def on_config_changed(self, event: ConfigChangeEvent):
        print(f"配置已变更: {event.module_type}:{event.config_path}")
        # 重新加载相关组件
        reload_components(event.module_type)

config_service.add_change_listener(MyConfigListener())

# 开始监控配置文件
config_service.start_watching("workflow", "my_workflow.yaml")
```

## 总结

通过这个统一配置系统设计，我们实现了：

1. **统一接口**：所有模块使用一致的配置接口
2. **模块化设计**：每个模块保持独立性和可扩展性
3. **跨模块支持**：支持模块间的配置引用和依赖
4. **热重载**：支持配置文件变更的实时监控和重载
5. **版本管理**：配置版本控制和回滚功能
6. **向后兼容**：保持现有配置系统的兼容性

这个设计既保持了各模块的独立性，又提供了统一的配置管理体验，是一个可扩展、可维护的企业级配置解决方案。