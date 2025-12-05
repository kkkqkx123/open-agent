# common_infra.py 接口依赖关系和使用模式分析

## 📊 依赖关系统计

### 接口使用频率分析

基于代码搜索结果，各接口的使用情况如下：

#### 1. ServiceLifetime 枚举
- **使用次数**: 15+ 次
- **主要使用者**: 
  - `src/services/container/bindings/*.py` (所有绑定文件)
  - `src/services/container/core/container.py`
  - `src/services/container/core/base_service_bindings.py`
- **使用层级**: 主要在服务层
- **依赖模式**: 作为参数传递给容器注册方法

#### 2. IConfigLoader 接口
- **使用次数**: 10+ 次
- **主要使用者**: 
  - `src/core/config/config_loader.py` (实现)
  - `src/core/workflow/config/node_config_loader.py`
  - `src/services/tools/validation/manager.py`
  - `src/adapters/tui/app.py`
  - `src/adapters/tui/config.py`
  - `src/adapters/cli/run_command.py`
  - `src/adapters/cli/commands.py`
- **使用层级**: 核心层、服务层、适配器层
- **依赖模式**: 依赖注入、直接实例化

#### 3. IStorage 接口
- **使用次数**: 8+ 次
- **主要使用者**: 
  - `src/core/common/storage.py` (实现)
  - `src/adapters/storage/adapters/base.py` (实现)
  - `src/services/storage/migration.py`
- **使用层级**: 核心层、适配器层、服务层
- **依赖模式**: 继承实现、依赖注入

#### 4. IDependencyContainer 接口
- **使用次数**: 20+ 次
- **主要使用者**: 
  - `src/services/container/core/container.py` (实现)
  - `src/services/workflow/workflow_service_factory.py`
  - `src/services/container/bindings/*.py`
  - `src/services/container/core/test_container.py`
- **使用层级**: 主要在服务层
- **依赖模式**: 依赖注入、类型注解

#### 5. IConfigInheritanceHandler 接口
- **使用次数**: 3+ 次
- **主要使用者**: 
  - `src/core/common/utils/inheritance_handler.py` (实现)
- **使用层级**: 核心层内部
- **依赖模式**: 内部使用

## 🔄 依赖关系图

### 当前依赖流向
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   适配器层       │    │    服务层       │    │    核心层       │
│                │    │                │    │                │
│ - TUI适配器     │───▶│ - 容器绑定      │───▶│ - 配置加载器    │
│ - CLI适配器     │    │ - 服务工厂      │    │ - 存储基类      │
│ - API适配器     │    │ - 验证管理器    │    │ - 工具执行器    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   接口层        │
                    │                │
                    │ - common_infra  │
                    └─────────────────┘
```

### 目标依赖流向
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   适配器层       │    │    服务层       │    │    核心层       │
│                │    │                │    │                │
│ - TUI适配器     │───▶│ - 容器绑定      │───▶│ - 业务逻辑      │
│ - CLI适配器     │    │ - 服务工厂      │    │ - 领域模型      │
│ - API适配器     │    │ - 验证管理器    │    │ - 核心规则      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │ 基础设施层      │
                    │                │
                    │ - 接口定义      │
                    │ - 技术实现      │
                    └─────────────────┘
```

## 🎯 使用模式分析

### 1. ServiceLifetime 使用模式
```python
# 典型使用场景
from src.interfaces.common_infra import ServiceLifetime

container.register(
    interface=IService,
    implementation=ServiceImplementation,
    lifetime=ServiceLifetime.SINGLETON  # 枚举值使用
)
```

**特点**:
- 纯枚举值，无状态
- 编译时确定
- 被容器系统广泛使用

### 2. IConfigLoader 使用模式
```python
# 依赖注入模式
class SomeService:
    def __init__(self, config_loader: IConfigLoader):
        self.config_loader = config_loader

# 直接使用模式
config_loader = container.get(IConfigLoader)
config = config_loader.load_config("app.yaml")
```

**特点**:
- 接口抽象，多种实现
- 被多个层级依赖
- 配置系统的核心抽象

### 3. IStorage 使用模式
```python
# 继承实现模式
class BaseStorage(IStorage):
    async def save(self, data: Dict[str, Any]) -> bool:
        # 实现逻辑
        pass

# 依赖注入模式
class DataService:
    def __init__(self, storage: IStorage):
        self.storage = storage
```

**特点**:
- 抽象存储接口
- 多种实现方式
- 数据持久化的核心抽象

### 4. IDependencyContainer 使用模式
```python
# 类型注解模式
def create_service_factory(container: IDependencyContainer) -> ServiceFactory:
    return ServiceFactory(container)

# 直接使用模式
container = get_global_container()
service = container.get(IService)
```

**特点**:
- 依赖注入的核心接口
- 被整个系统使用
- 架构的基础设施

### 5. IConfigInheritanceHandler 使用模式
```python
# 内部使用模式
class ConfigLoader(IConfigLoader):
    def __init__(self, inheritance_handler: IConfigInheritanceHandler):
        self.inheritance_handler = inheritance_handler
```

**特点**:
- 配置系统内部使用
- 专门的技术功能
- 使用范围相对有限

## 📈 影响范围分析

### 高影响接口 (需要谨慎处理)
1. **IDependencyContainer**: 被整个系统使用，影响面最大
2. **IConfigLoader**: 被多个层级使用，影响面较大
3. **IStorage**: 被核心层和适配器层使用，影响面中等

### 中影响接口
1. **ServiceLifetime**: 主要在服务层使用，影响面可控
2. **IConfigInheritanceHandler**: 主要在配置系统内部使用，影响面较小

## 🚨 潜在风险点

### 1. 循环依赖风险
- 当前基础设施层已有部分实现
- 迁移接口时需要避免循环依赖
- 需要仔细设计导入路径

### 2. 向后兼容风险
- 大量现有代码使用这些接口
- 需要保持API兼容性
- 可能需要过渡期兼容层

### 3. 测试覆盖风险
- 迁移后需要确保所有测试通过
- 可能需要更新测试用例
- 需要验证功能完整性

## 📋 迁移复杂度评估

### 复杂度矩阵

| 接口 | 使用频率 | 实现复杂度 | 迁移风险 | 整体复杂度 |
|------|----------|------------|----------|------------|
| ServiceLifetime | 高 | 低 | 低 | 🟢 低 |
| IConfigInheritanceHandler | 低 | 中 | 低 | 🟡 中低 |
| IStorage | 中 | 中 | 中 | 🟡 中 |
| IConfigLoader | 高 | 高 | 高 | 🔴 高 |
| IDependencyContainer | 高 | 高 | 高 | 🔴 高 |

### 迁移难度排序
1. **简单**: ServiceLifetime
2. **中等**: IConfigInheritanceHandler, IStorage
3. **困难**: IConfigLoader, IDependencyContainer

## 🎯 迁移策略建议

### 分阶段迁移策略

#### 第一阶段: 低风险接口
- **目标**: ServiceLifetime, IConfigInheritanceHandler
- **理由**: 使用范围相对有限，迁移风险较低
- **预期时间**: 1-2天

#### 第二阶段: 中等风险接口
- **目标**: IStorage
- **理由**: 使用范围中等，需要仔细处理实现迁移
- **预期时间**: 3-5天

#### 第三阶段: 高风险接口
- **目标**: IConfigLoader, IDependencyContainer
- **理由**: 使用广泛，影响面大，需要充分测试
- **预期时间**: 1-2周

### 迁移原则
1. **渐进式迁移**: 分阶段进行，降低风险
2. **向后兼容**: 保持API兼容性
3. **充分测试**: 每个阶段都要进行全面测试
4. **文档更新**: 及时更新相关文档

## 📊 总结

通过依赖关系和使用模式分析，我们发现：

1. **所有接口都应该迁移**: 都符合基础设施层特征
2. **迁移复杂度不同**: 需要根据复杂度制定不同的迁移策略
3. **影响范围广泛**: 需要谨慎处理，确保系统稳定性
4. **分阶段实施**: 建议按照复杂度分阶段进行迁移

这些分析为后续的迁移策略制定提供了重要依据。