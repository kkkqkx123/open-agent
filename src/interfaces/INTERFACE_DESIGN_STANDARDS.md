# 接口设计规范文档

本文档定义了 `src/interfaces` 目录中接口设计的标准和最佳实践，确保接口的一致性、可维护性和可扩展性。

## 1. 架构原则

### 1.1 三层架构
按照三层架构原则，接口分为三个层次：

#### 领域层接口 (Domain Layer)
- **职责**：定义核心业务概念和业务规则
- **特点**：业务纯净，不依赖技术细节
- **命名**：通常以 `I` + 业务概念命名
- **示例**：`ISession`, `IWorkflow`, `ITool`

#### 应用层接口 (Application Layer)
- **职责**：协调领域服务，处理业务用例
- **特点**：组合多个领域服务，提供高级API
- **命名**：通常以 `I` + 业务概念 + `Service`/`Manager` 命名
- **示例**：`ISessionService`, `IWorkflowManager`, `IToolManager`

#### 基础设施层接口 (Infrastructure Layer)
- **职责**：提供技术实现抽象，支持领域需求
- **特点**：技术导向，可被领域层使用
- **命名**：通常以 `I` + 技术概念命名
- **示例**：`IStorage`, `ILogger`, `IConfigLoader`

### 1.2 依赖方向
```
应用层 → 领域层 → 基础设施层
```
- 禁止反向依赖
- 同层内可以相互依赖
- 跨层依赖必须遵循依赖倒置原则

## 2. 接口设计原则

### 2.1 单一职责原则 (SRP)
每个接口应该只有一个变化的理由。

**好的示例**：
```python
class IServiceRegistry(ABC):
    """服务注册接口 - 只负责注册"""
    @abstractmethod
    def register(self, interface: Type, implementation: Type) -> None:
        pass

class IServiceResolver(ABC):
    """服务解析接口 - 只负责解析"""
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        pass
```

**不好的示例**：
```python
class IServiceContainer(ABC):
    """服务容器接口 - 职责过多"""
    @abstractmethod
    def register(self, interface: Type, implementation: Type) -> None:
        pass
    
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        pass
    
    @abstractmethod
    def track_performance(self, metric: str) -> None:
        pass
```

### 2.2 接口隔离原则 (ISP)
客户端不应该依赖它不需要的接口。

**好的示例**：
```python
class IAsyncExecutable(ABC):
    """异步执行特征接口"""
    @abstractmethod
    async def execute_async(self, *args, **kwargs) -> Any:
        pass

class ICancellable(ABC):
    """可取消特征接口"""
    @abstractmethod
    def cancel(self) -> bool:
        pass

class IAdvancedExecutor(IAsyncExecutable, ICancellable):
    """组合接口 - 按需组合"""
    pass
```

### 2.3 依赖倒置原则 (DIP)
高层模块不应该依赖低层模块，两者都应该依赖抽象。

**好的示例**：
```python
# 领域层接口
class IRepository(ABC):
    @abstractmethod
    async def save(self, entity: T) -> str:
        pass

# 应用层服务
class UserService:
    def __init__(self, repository: IRepository[User]):
        self.repository = repository
```

## 3. 命名规范

### 3.1 接口命名
- **前缀**：所有接口以 `I` 开头
- **格式**：`I` + 模块名 + 组件类型
- **示例**：
  - `ISessionService` - 会话服务接口
  - `IWorkflowExecutor` - 工作流执行器接口
  - `IToolRegistry` - 工具注册表接口

### 3.2 方法命名
#### CRUD操作
```python
async def create_entity(self, **kwargs) -> str:           # 创建
async def get_entity(self, entity_id: str) -> EntityType:  # 获取
async def update_entity(self, entity_id: str, **kwargs) -> bool: # 更新
async def delete_entity(self, entity_id: str) -> bool:   # 删除
async def list_entities(self, **filters) -> List[EntityType]: # 列表
```

#### 异步方法
```python
async def method_async(self, *args, **kwargs) -> ReturnType:
    """异步版本方法"""
    pass

async def method_stream(self, *args, **kwargs) -> AsyncIterator[ItemType]:
    """流式版本方法"""
    pass
```

#### 查询方法
```python
async def query(self, query: str, params: Dict[str, Any]) -> List[T]:
    """执行查询"""
    pass

async def search(self, term: str, **filters) -> List[T]:
    """搜索"""
    pass

async def count(self, **filters) -> int:
    """统计数量"""
    pass
```

### 3.3 参数命名
- **配置参数**：使用描述性名称
- **可选参数**：提供合理的默认值
- **关键字参数**：使用 `**kwargs` 扩展性

**好的示例**：
```python
async def create_session(
    self,
    workflow_config_path: str,
    metadata: Optional[Dict[str, Any]] = None,
    timeout: int = 300,
    **kwargs: Any
) -> str:
    """创建会话"""
    pass
```

## 4. 类型注解规范

### 4.1 完整类型注解
所有公共方法必须有完整的类型注解。

**好的示例**：
```python
from typing import Dict, Any, Optional, List, TypeVar, Generic

T = TypeVar('T')

class IRepository(Generic[T], ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> str:
        """创建实体"""
        pass
    
    @abstractmethod
    async def get(self, entity_id: str) -> Optional[T]:
        """获取实体"""
        pass
```

### 4.2 泛型使用
- 使用 `TypeVar` 定义泛型类型变量
- 在接口类上声明泛型约束
- 在方法中使用泛型类型

**好的示例**：
```python
from typing import TypeVar, Generic

T = TypeVar('T')
K = TypeVar('K')

class ICrudService(Generic[T, K], ABC):
    @abstractmethod
    async def create(self, data: Dict[str, Any]) -> K:
        pass
    
    @abstractmethod
    async def get_by_id(self, entity_id: K) -> Optional[T]:
        pass
```

### 4.3 联合类型和可选类型
```python
from typing import Union, Optional, Literal

def process_config(
    config: Union[DictConfig, YamlConfig, JsonConfig]
) -> ProcessedConfig:
    """处理配置"""
    pass

def get_optional_value(
    key: str, 
    default: Optional[str] = None
) -> Optional[str]:
    """获取可选值"""
    pass

def set_log_level(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"]
) -> None:
    """设置日志级别"""
    pass
```

## 5. 文档规范

### 5.1 接口文档模板
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

### 5.2 文档要求
- **接口级别**：必须有职责描述、使用示例、注意事项
- **方法级别**：必须有参数说明、返回值说明、异常说明
- **示例代码**：提供基本用法和高级用法示例
- **交叉引用**：使用 `See Also` 引用相关接口和方法

## 6. 错误处理规范

### 6.1 异常定义
```python
class InterfaceException(Exception):
    """接口基础异常"""
    pass

class NotFoundException(InterfaceException):
    """未找到异常"""
    def __init__(self, resource_type: str, resource_id: str):
        self.resource_type = resource_type
        self.resource_id = resource_id
        super().__init__(f"{resource_type} with id {resource_id} not found")

class ValidationException(InterfaceException):
    """验证异常"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {', '.join(errors)}")
```

### 6.2 异常处理
```python
@abstractmethod
async def get_entity(self, entity_id: str) -> EntityType:
    """
    获取实体
    
    Args:
        entity_id: 实体ID
        
    Returns:
        EntityType: 实体对象
        
    Raises:
        NotFoundException: 当实体不存在时抛出
        ValidationException: 当ID格式无效时抛出
    """
    pass
```

## 7. 返回值规范

### 7.1 操作结果
```python
@dataclass
class OperationResult:
    """操作结果"""
    success: bool
    data: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
```

### 7.2 分页结果
```python
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

### 7.3 返回值约定
- **创建操作**：返回创建的ID或实体
- **查询操作**：返回实体或实体列表
- **更新操作**：返回布尔值表示是否成功
- **删除操作**：返回布尔值表示是否成功
- **复杂操作**：返回 `OperationResult`

## 8. 测试规范

### 8.1 接口测试模板
```python
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
```

### 8.2 测试要求
- **单元测试**：每个接口方法必须有对应的单元测试
- **集成测试**：测试接口间的协作
- **边界测试**：测试异常情况和边界条件
- **性能测试**：关键接口需要性能测试

## 9. 版本控制规范

### 9.1 版本号格式
使用语义化版本号：`MAJOR.MINOR.PATCH`

### 9.2 版本兼容性
- **MAJOR**：不兼容的API修改
- **MINOR**：向后兼容的功能性新增
- **PATCH**：向后兼容的问题修正

### 9.3 废弃处理
```python
@deprecated("Use INewInterface instead", version="2.0.0")
class IOldInterface(ABC):
    """已弃用的旧接口"""
    pass
```

## 10. 最佳实践

### 10.1 接口设计
1. **保持接口小而专注**：每个接口不超过10个方法
2. **使用组合而非继承**：通过组合小接口构建大接口
3. **避免接口污染**：不要在接口中添加不相关的方法
4. **考虑扩展性**：设计接口时考虑未来的扩展需求

### 10.2 实现指导
1. **优先组合**：使用组合而非继承实现复杂功能
2. **依赖注入**：通过构造函数注入依赖
3. **错误处理**：实现类应该处理所有可能的异常
4. **日志记录**：在关键操作点添加日志

### 10.3 代码质量
1. **类型安全**：使用完整的类型注解
2. **文档完整**：提供详细的文档和示例
3. **测试覆盖**：确保足够的测试覆盖率
4. **性能考虑**：考虑接口的性能影响

## 11. 检查清单

### 11.1 设计阶段
- [ ] 接口职责单一明确
- [ ] 遵循三层架构原则
- [ ] 依赖关系正确
- [ ] 命名符合规范

### 11.2 实现阶段
- [ ] 类型注解完整
- [ ] 文档格式标准
- [ ] 异常处理合理
- [ ] 返回值一致

### 11.3 测试阶段
- [ ] 单元测试完整
- [ ] 集成测试通过
- [ ] 边界条件测试
- [ ] 性能测试满足要求

### 11.4 维护阶段
- [ ] 文档及时更新
- [ ] 版本兼容性考虑
- [ ] 废弃接口处理
- [ ] 重构影响评估

通过遵循这些规范，我们可以确保接口设计的一致性、可维护性和可扩展性，提高整个项目的代码质量。