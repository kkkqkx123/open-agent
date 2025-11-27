# src/interfaces 接口设计优化建议

## 1. 架构重构建议

### 1.1 明确接口层次结构

#### 1.1.1 建议的三层架构
```
┌─────────────────────────────────────┐
│           应用层接口                 │
│  (Application Layer Interfaces)     │
│  - ISessionService                  │
│  - IWorkflowManager                 │
│  - IToolManager                     │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│           领域层接口                 │
│  (Domain Layer Interfaces)          │
│  - ISession                         │
│  - IWorkflow                        │
│  - ITool                            │
└─────────────────────────────────────┘
┌─────────────────────────────────────┐
│           基础设施层接口             │
│  (Infrastructure Layer Interfaces)  │
│  - ISessionRepository               │
│  - IWorkflowExecutor                │
│  - IToolRegistry                    │
└─────────────────────────────────────┘
```

#### 1.1.2 接口职责重新划分
**应用层接口**：
- 负责业务流程编排
- 处理用例逻辑
- 协调多个领域服务

**领域层接口**：
- 定义核心业务概念
- 封装业务规则
- 提供领域服务

**基础设施层接口**：
- 提供技术实现抽象
- 处理数据持久化
- 集成外部系统

### 1.2 解决循环依赖

#### 1.2.1 依赖倒置原则应用
```python
# 当前问题：workflow 依赖 state
class IWorkflow(ABC):
    @abstractmethod
    def execute(self, initial_state: IWorkflowState) -> IWorkflowState:
        pass

# 优化方案：引入事件驱动
class IWorkflow(ABC):
    @abstractmethod
    def execute(self, context: IExecutionContext) -> IExecutionResult:
        pass

class IExecutionContext(ABC):
    @abstractmethod
    def get_initial_state(self) -> IState:
        pass
    
    @abstractmethod
    def update_state(self, state: IState) -> None:
        pass
```

#### 1.2.2 模块解耦策略
1. **引入事件机制**：使用事件总线解耦模块
2. **依赖注入**：通过容器管理依赖关系
3. **接口隔离**：定义最小化的接口契约

## 2. 设计一致性改进

### 2.1 统一命名规范

#### 2.1.1 接口命名标准
```python
# 统一的接口命名规范
class I{ModuleName}{ComponentType}(ABC):
    """接口文档"""
    pass

# 示例
class ISessionManager(ABC):      # 会话管理器
class IWorkflowExecutor(ABC):    # 工作流执行器
class IToolRegistry(ABC):        # 工具注册表
class IStateRepository(ABC):     # 状态仓储
```

#### 2.1.2 方法命名标准
```python
# CRUD操作标准命名
async def create_{entity}(self, **kwargs) -> str:           # 创建
async def get_{entity}(self, entity_id: str) -> EntityType: # 获取
async def update_{entity}(self, entity_id: str, **kwargs) -> bool: # 更新
async def delete_{entity}(self, entity_id: str) -> bool:   # 删除
async def list_{entities}(self, **filters) -> List[EntityType]: # 列表

# 异步方法命名标准
async def {method}_async(self, *args, **kwargs) -> ReturnType:
    """异步版本的方法"""
    pass

# 流式方法命名标准
async def {method}_stream(self, *args, **kwargs) -> AsyncIterator[ItemType]:
    """流式版本的方法"""
    pass
```

### 2.2 统一参数设计

#### 2.2.1 标准参数模式
```python
# 标准的创建方法参数
async def create_entity(
    self,
    name: str,
    config: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> str:
    """创建实体"""
    pass

# 标准的查询方法参数
async def list_entities(
    self,
    filters: Optional[Dict[str, Any]] = None,
    sort_by: Optional[str] = None,
    sort_order: str = "asc",
    limit: Optional[int] = None,
    offset: int = 0
) -> List[EntityType]:
    """列出实体"""
    pass
```

#### 2.2.2 配置对象标准化
```python
# 标准配置基类
@dataclass
class BaseConfig:
    """基础配置类"""
    name: str
    description: Optional[str] = None
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

# 具体配置类继承
@dataclass
class SessionConfig(BaseConfig):
    """会话配置"""
    workflow_config_path: str
    timeout: int = 300
    max_threads: int = 10
```

### 2.3 统一返回值处理

#### 2.3.1 标准返回值类型
```python
# 操作结果类型
@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

# 分页结果类型
@dataclass
class PagedResult:
    """分页结果"""
    items: List[Any]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_prev: bool
```

#### 2.3.2 统一错误处理
```python
# 标准异常层次
class InterfaceException(Exception):
    """接口基础异常"""
    pass

class NotFoundException(InterfaceException):
    """未找到异常"""
    pass

class ValidationException(InterfaceException):
    """验证异常"""
    pass

class ConfigurationException(InterfaceException):
    """配置异常"""
    pass
```

## 3. 接口粒度优化

### 3.1 接口拆分策略

#### 3.1.1 大接口拆分示例
```python
# 当前的大接口
class IDependencyContainer(ABC):
    # 注册相关方法（5个）
    def register(...)
    def register_factory(...)
    def register_instance(...)
    # 获取相关方法（3个）
    def get(...)
    def get_all(...)
    def try_get(...)
    # 管理相关方法（4个）
    def clear(...)
    def has_service(...)
    # ... 更多方法

# 拆分后的接口
class IServiceRegistry(ABC):
    """服务注册接口"""
    @abstractmethod
    def register(self, interface: Type, implementation: Type) -> None:
        pass
    
    @abstractmethod
    def register_factory(self, interface: Type, factory: Callable) -> None:
        pass
    
    @abstractmethod
    def unregister(self, interface: Type) -> bool:
        pass

class IServiceResolver(ABC):
    """服务解析接口"""
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        pass
    
    @abstractmethod
    def try_get(self, service_type: Type[T]) -> Optional[T]:
        pass
    
    @abstractmethod
    def get_all(self, interface: Type) -> List[Any]:
        pass

class IContainerManager(ABC):
    """容器管理接口"""
    @abstractmethod
    def clear(self) -> None:
        pass
    
    @abstractmethod
    def has_service(self, service_type: Type) -> bool:
        pass
    
    @abstractmethod
    def get_service_count(self) -> int:
        pass

# 组合接口
class IDependencyContainer(IServiceRegistry, IServiceResolver, IContainerManager):
    """完整的依赖注入容器接口"""
    pass
```

#### 3.1.2 小接口合并示例
```python
# 当前的小接口
class IPromptLoader(ABC):
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        pass

class IPromptInjector(ABC):
    @abstractmethod
    def inject_prompt(self, state: IWorkflowState, prompt: str) -> IWorkflowState:
        pass

# 合并后的接口
class IPromptManager(ABC):
    """统一的提示词管理接口"""
    
    # 加载相关方法
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        pass
    
    @abstractmethod
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        pass
    
    # 注入相关方法
    @abstractmethod
    def inject_prompt(self, state: IWorkflowState, prompt: str) -> IWorkflowState:
        pass
    
    @abstractmethod
    def inject_prompts(self, state: IWorkflowState, prompts: List[str]) -> IWorkflowState:
        pass
```

### 3.2 接口组合模式

#### 3.2.1 特征接口模式
```python
# 定义特征接口
class IAsyncExecutable(ABC):
    """异步执行特征"""
    @abstractmethod
    async def execute_async(self, *args, **kwargs) -> Any:
        pass

class IStreamable(ABC):
    """流式处理特征"""
    @abstractmethod
    async def stream(self, *args, **kwargs) -> AsyncIterator[Any]:
        pass

class ICancellable(ABC):
    """可取消特征"""
    @abstractmethod
    def cancel(self) -> bool:
        pass

# 组合特征接口
class IAdvancedExecutor(IAsyncExecutable, IStreamable, ICancellable):
    """高级执行器接口"""
    pass
```

#### 3.2.2 适配器模式
```python
# 适配器接口
class IAsyncAdapter(ABC):
    """异步适配器接口"""
    @abstractmethod
    def adapt_sync_method(self, sync_method: Callable) -> Callable:
        """将同步方法适配为异步方法"""
        pass

class IStreamAdapter(ABC):
    """流式适配器接口"""
    @abstractmethod
    def adapt_to_stream(self, result: Any) -> AsyncIterator[Any]:
        """将结果适配为流"""
        pass
```

## 4. 类型安全改进

### 4.1 完善类型注解

#### 4.1.1 泛型接口设计
```python
# 泛型基础接口
class IRepository(ABC, Generic[T, K]):
    """泛型仓储接口"""
    
    @abstractmethod
    async def create(self, entity: T) -> K:
        """创建实体"""
        pass
    
    @abstractmethod
    async def get(self, id: K) -> Optional[T]:
        """获取实体"""
        pass
    
    @abstractmethod
    async def update(self, id: K, updates: Dict[str, Any]) -> bool:
        """更新实体"""
        pass
    
    @abstractmethod
    async def delete(self, id: K) -> bool:
        """删除实体"""
        pass

# 具体类型实现
class ISessionRepository(IRepository[Session, str]):
    """会话仓储接口"""
    pass

class IStateRepository(IRepository[State, str]):
    """状态仓储接口"""
    pass
```

#### 4.1.2 联合类型和可选类型
```python
# 使用联合类型
def create_tool(
    self, 
    config: Union[NativeToolConfig, RestToolConfig, MCPToolConfig]
) -> ITool:
    """创建工具"""
    pass

# 使用可选类型
def get_config(
    self, 
    key: str, 
    default: Optional[T] = None
) -> Optional[T]:
    """获取配置"""
    pass

# 使用类型字面量
def set_log_level(self, level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]) -> None:
    """设置日志级别"""
    pass
```

### 4.2 类型验证和转换

#### 4.2.1 运行时类型检查
```python
# 类型检查装饰器
def validate_types(**type_hints):
    """类型验证装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 验证参数类型
            for param_name, expected_type in type_hints.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    if not isinstance(value, expected_type):
                        raise TypeError(f"Parameter {param_name} must be {expected_type}")
            
            # 执行方法
            result = await func(*args, **kwargs)
            
            # 验证返回值类型
            if 'return' in type_hints:
                if not isinstance(result, type_hints['return']):
                    raise TypeError(f"Return value must be {type_hints['return']}")
            
            return result
        return wrapper
    return decorator

# 使用示例
class IToolManager(ABC):
    @validate_types(config=ToolConfig, return=ITool)
    @abstractmethod
    async def create_tool(self, config: ToolConfig) -> ITool:
        """创建工具"""
        pass
```

#### 4.2.2 类型转换器
```python
# 类型转换接口
class ITypeConverter(ABC):
    """类型转换器接口"""
    
    @abstractmethod
    def can_convert(self, source_type: Type, target_type: Type) -> bool:
        """检查是否可以转换"""
        pass
    
    @abstractmethod
    def convert(self, value: Any, target_type: Type) -> Any:
        """执行类型转换"""
        pass

# 具体转换器实现
class DictToModelConverter(ITypeConverter):
    """字典到模型转换器"""
    
    def can_convert(self, source_type: Type, target_type: Type) -> bool:
        return source_type == dict and hasattr(target_type, '__annotations__')
    
    def convert(self, value: Dict[str, Any], target_type: Type) -> Any:
        return target_type(**value)
```

## 5. 文档和注释改进

### 5.1 标准化文档格式

#### 5.1.1 接口文档模板
```python
class IExampleInterface(ABC):
    """
    示例接口文档
    
    这个接口提供了示例功能，用于演示文档标准化。
    
    职责：
    - 职责1的描述
    - 职责2的描述
    - 职责3的描述
    
    使用示例：
        ```python
        # 创建实例
        example = ExampleImplementation()
        
        # 调用方法
        result = await example.do_something("param")
        ```
    
    注意事项：
    - 注意事项1
    - 注意事项2
    
    相关接口：
    - IRelatedInterface1
    - IRelatedInterface2
    
    版本历史：
    - v1.0.0: 初始版本
    - v1.1.0: 添加新功能
    """
    
    @abstractmethod
    async def do_something(
        self, 
        param1: str, 
        param2: Optional[int] = None,
        **kwargs: Any
    ) -> ResultType:
        """
        执行某个操作
        
        Args:
            param1: 参数1的详细描述
            param2: 参数2的详细描述，可选参数
            **kwargs: 额外的关键字参数
        
        Returns:
            ResultType: 返回值的详细描述
        
        Raises:
            ValueError: 当参数1无效时抛出
            RuntimeError: 当执行失败时抛出
        
        Examples:
            ```python
            # 基本用法
            result = await interface.do_something("test")
            
            # 带可选参数
            result = await interface.do_something("test", param2=42)
            
            # 带额外参数
            result = await interface.do_something("test", extra="value")
            ```
        
        Note:
            这里可以添加额外的注意事项
        
        See Also:
            - related_method1: 相关方法1
            - related_method2: 相关方法2
        """
        pass
```

#### 5.1.2 自动文档生成
```python
# 文档生成装饰器
def auto_doc(examples: Optional[List[str]] = None, see_also: Optional[List[str]] = None):
    """自动文档生成装饰器"""
    def decorator(func):
        # 生成标准文档
        func.__doc__ = generate_docstring(func, examples, see_also)
        return func
    return decorator

# 使用示例
class IToolManager(ABC):
    @auto_doc(
        examples=[
            "tool = await manager.create_tool(config)",
            "tools = await manager.list_tools()"
        ],
        see_also=["IToolRegistry", "IToolFactory"]
    )
    @abstractmethod
    async def create_tool(self, config: ToolConfig) -> ITool:
        """创建工具"""
        pass
```

### 5.2 示例代码库

#### 5.2.1 使用示例模板
```python
# examples/interface_usage.py
"""
接口使用示例集合

这个文件包含了所有接口的标准使用示例，用于：
1. 开发者学习
2. 测试用例参考
3. 文档生成
"""

class InterfaceExamples:
    """接口使用示例类"""
    
    @staticmethod
    def session_service_example():
        """会话服务使用示例"""
        async def example():
            # 创建会话服务
            session_service = container.get(ISessionService)
            
            # 创建用户请求
            user_request = UserRequest(
                message="Hello, world!",
                metadata={"source": "web"}
            )
            
            # 创建会话
            session_id = await session_service.create_session(user_request)
            
            # 获取会话信息
            session_info = await session_service.get_session_info(session_id)
            
            # 执行工作流
            result = await session_service.execute_workflow_in_session(
                session_id, 
                "main_thread"
            )
            
            return result
    
    @staticmethod
    def tool_manager_example():
        """工具管理器使用示例"""
        async def example():
            # 获取工具管理器
            tool_manager = container.get(IToolManager)
            
            # 初始化
            await tool_manager.initialize()
            
            # 创建工具配置
            config = NativeToolConfig(
                name="calculator",
                description="Basic calculator",
                parameters_schema={
                    "type": "object",
                    "properties": {
                        "operation": {"type": "string"},
                        "a": {"type": "number"},
                        "b": {"type": "number"}
                    }
                }
            )
            
            # 创建工具
            tool = await tool_manager.create_tool(config)
            
            # 执行工具
            result = await tool_manager.execute_tool(
                "calculator",
                {"operation": "add", "a": 1, "b": 2}
            )
            
            return result
```

#### 5.2.2 测试用例模板
```python
# tests/interface_test_template.py
"""
接口测试模板

提供标准的接口测试模板，确保所有接口实现的一致性。
"""

class InterfaceTestTemplate(Generic[T]):
    """接口测试模板"""
    
    def __init__(self, interface_class: Type[T], implementation: T):
        self.interface_class = interface_class
        self.implementation = implementation
    
    async def test_all_methods(self):
        """测试所有方法"""
        methods = self._get_abstract_methods()
        
        for method in methods:
            await self._test_method(method)
    
    def _get_abstract_methods(self) -> List[str]:
        """获取抽象方法列表"""
        return [
            name for name in method_names(self.interface_class)
            if getattr(getattr(self.interface_class, name), '__isabstractmethod__', False)
        ]
    
    async def _test_method(self, method_name: str):
        """测试单个方法"""
        method = getattr(self.implementation, method_name)
        
        # 获取方法签名
        sig = signature(method)
        
        # 生成测试参数
        test_args = self._generate_test_args(sig)
        
        # 执行测试
        try:
            result = await method(*test_args.args, **test_args.kwargs)
            self._validate_result(method_name, result)
        except Exception as e:
            self._handle_test_error(method_name, e)
```

## 6. 实施计划

### 6.1 分阶段重构计划

#### 6.1.1 第一阶段：基础标准化（2-3周）
1. **统一命名规范**
   - 制定接口命名标准
   - 重命名不符合标准的接口
   - 更新所有相关文档

2. **统一参数设计**
   - 制定参数设计标准
   - 重构接口方法签名
   - 更新实现类

3. **统一返回值处理**
   - 定义标准返回值类型
   - 重构接口返回值
   - 更新调用代码

#### 6.1.2 第二阶段：架构重构（3-4周）
1. **接口层次重构**
   - 重新设计接口层次
   - 拆分大接口
   - 合并小接口

2. **解决循环依赖**
   - 识别循环依赖
   - 引入事件机制
   - 重构依赖关系

3. **类型安全改进**
   - 完善类型注解
   - 引入泛型设计
   - 添加类型检查

#### 6.1.3 第三阶段：文档完善（1-2周）
1. **文档标准化**
   - 制定文档标准
   - 重写接口文档
   - 添加使用示例

2. **测试用例完善**
   - 编写接口测试模板
   - 完善现有测试
   - 添加集成测试

### 6.2 风险控制

#### 6.2.1 向后兼容性
```python
# 兼容性适配器
class LegacyInterfaceAdapter:
    """旧接口适配器"""
    
    def __init__(self, new_implementation):
        self.new_impl = new_implementation
    
    def old_method(self, *args, **kwargs):
        """旧方法适配"""
        # 转换参数
        new_args = self._convert_args(args, kwargs)
        
        # 调用新方法
        result = self.new_impl.new_method(*new_args)
        
        # 转换结果
        return self._convert_result(result)

# 渐进式迁移
@deprecated("Use INewInterface instead", version="2.0.0")
class IOldInterface(ABC):
    """已弃用的旧接口"""
    pass
```

#### 6.2.2 测试策略
1. **单元测试**：确保每个接口方法正确实现
2. **集成测试**：确保接口间协作正常
3. **回归测试**：确保重构不破坏现有功能
4. **性能测试**：确保重构不影响性能

### 6.3 质量保证

#### 6.3.1 代码审查检查清单
- [ ] 接口命名符合规范
- [ ] 方法签名一致
- [ ] 类型注解完整
- [ ] 文档格式标准
- [ ] 异常处理合理
- [ ] 测试覆盖充分

#### 6.3.2 自动化检查
```python
# 接口规范检查器
class InterfaceComplianceChecker:
    """接口规范检查器"""
    
    def check_interface(self, interface_class: Type) -> List[str]:
        """检查接口规范合规性"""
        issues = []
        
        # 检查命名规范
        if not interface_class.__name__.startswith('I'):
            issues.append("Interface name should start with 'I'")
        
        # 检查方法命名
        for method_name in dir(interface_class):
            if not method_name.startswith('_'):
                if not self._check_method_naming(method_name):
                    issues.append(f"Method {method_name} naming is inconsistent")
        
        # 检查类型注解
        for method_name, method in getmembers(interface_class):
            if callable(method):
                if not self._check_type_annotations(method):
                    issues.append(f"Method {method_name} missing type annotations")
        
        return issues
```

## 7. 总结

### 7.1 预期收益
1. **开发效率提升**：统一的接口规范降低学习成本
2. **维护成本降低**：清晰的架构减少维护复杂度
3. **代码质量提升**：类型安全和文档完善提高代码质量
4. **团队协作改善**：标准化规范提升团队协作效率

### 7.2 成功指标
1. **接口一致性**：95%以上的接口符合设计规范
2. **文档完整性**：100%的接口有完整文档和示例
3. **类型安全性**：100%的接口有完整类型注解
4. **测试覆盖率**：接口测试覆盖率达到90%以上

### 7.3 持续改进
1. **定期审查**：每季度审查接口设计规范
2. **反馈收集**：收集团队反馈，持续改进
3. **工具支持**：开发自动化工具支持规范检查
4. **培训推广**：定期培训，推广最佳实践

通过以上优化建议的实施，可以显著改善 `src/interfaces` 目录的接口设计质量，提升整个项目的可维护性和开发效率。