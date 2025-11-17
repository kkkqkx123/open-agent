# LLM依赖关系重构计划

## 概述

本文档详细描述了如何解决`src/core/llm/wrappers/task_group_wrapper.py`和`src/core/llm/wrappers/fallback_manager.py`的依赖关系问题。

## 问题分析

### 当前问题

1. **TaskGroupWrapper依赖问题**：
   - 位置：`src/core/llm/wrappers/task_group_wrapper.py`
   - 问题：直接依赖`src.services.llm.task_group_manager`
   - 违反：Core层不应依赖Services层的架构原则

2. **FallbackManager依赖问题**：
   - 位置：`src/core/llm/wrappers/fallback_manager.py`
   - 问题：大量依赖Services层组件
   - 违反：Core层不应依赖Services层的架构原则

### 架构原则

- **Core层**：包含核心接口、实体和基础逻辑，不依赖外部层
- **Services层**：依赖Core层，提供具体的业务服务实现
- **Adapters层**：依赖Core层和Services层，提供外部接口适配

## 解决方案

### 1. 创建接口抽象层

#### 1.1 在`src/core/llm/interfaces.py`中添加新接口

```python
class ITaskGroupManager(ABC):
    """任务组管理器接口"""
    
    @abstractmethod
    def get_models_for_group(self, group_reference: str) -> List[str]:
        """获取组引用对应的模型列表"""
        pass
    
    @abstractmethod
    def parse_group_reference(self, reference: str) -> Tuple[str, Optional[str]]:
        """解析组引用字符串"""
        pass
    
    @abstractmethod
    def get_fallback_groups(self, group_reference: str) -> List[str]:
        """获取降级组列表"""
        pass
    
    @abstractmethod
    def get_echelon_config(self, group_name: str, echelon_name: str) -> Optional[Dict[str, Any]]:
        """获取层级配置"""
        pass
    
    @abstractmethod
    def get_group_models_by_priority(self, group_name: str) -> List[Tuple[str, int, List[str]]]:
        """按优先级获取组的模型"""
        pass
    
    @abstractmethod
    def list_task_groups(self) -> List[str]:
        """列出所有任务组名称"""
        pass


class IFallbackManager(ABC):
    """降级管理器接口"""
    
    @abstractmethod
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """执行带降级的请求"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        pass
    
    @abstractmethod
    def reset_stats(self) -> None:
        """重置统计信息"""
        pass


class IPollingPoolManager(ABC):
    """轮询池管理器接口"""
    
    @abstractmethod
    def get_pool(self, name: str) -> Optional[Any]:
        """获取轮询池"""
        pass
    
    @abstractmethod
    def list_all_status(self) -> Dict[str, Any]:
        """获取所有轮询池状态"""
        pass
    
    @abstractmethod
    async def shutdown_all(self) -> None:
        """关闭所有轮询池"""
        pass


class IClientFactory(ABC):
    """客户端工厂接口"""
    
    @abstractmethod
    def create_client(self, model_name: str) -> ILLMClient:
        """创建客户端实例"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表"""
        pass
```

### 2. 重构TaskGroupWrapper

#### 2.1 修改导入语句

```python
# 原来的导入
from src.services.llm.task_group_manager import TaskGroupManager

# 新的导入
from ..interfaces import ITaskGroupManager, IFallbackManager
```

#### 2.2 修改构造函数

```python
def __init__(self, 
             name: str,
             task_group_manager: ITaskGroupManager,  # 使用接口
             fallback_manager: Optional[IFallbackManager] = None,  # 使用接口
             config: Optional[Dict[str, Any]] = None):
```

#### 2.3 修改方法实现

所有使用`task_group_manager`的地方保持不变，因为接口方法与原实现类方法一致。

### 3. 重构FallbackManager

#### 3.1 修改导入语句

```python
# 原来的导入
from ....services.llm.task_group_manager import TaskGroupManager
from ....services.llm.polling_pool import PollingPoolManager
from ....services.llm.fallback_system.fallback_manager import FallbackManager, DefaultFallbackLogger
from ....services.llm.fallback_system.fallback_config import FallbackConfig
from ....services.llm.fallback_system.interfaces import IClientFactory

# 新的导入
from ..interfaces import ITaskGroupManager, IPollingPoolManager, IClientFactory
```

#### 3.2 修改构造函数

```python
def __init__(self, 
             task_group_manager: ITaskGroupManager,  # 使用接口
             polling_pool_manager: IPollingPoolManager,  # 使用接口
             client_factory: IClientFactory,  # 使用接口
             logger: Optional[Any] = None):
```

#### 3.3 修改方法实现

所有使用这些管理器的地方保持不变，因为接口方法与原实现类方法一致。

### 4. 更新Services层实现类

#### 4.1 TaskGroupManager实现接口

```python
# 在src/services/llm/task_group_manager.py中
class TaskGroupManager(ITaskGroupManager):
    # 现有实现已经满足接口要求，无需修改
```

#### 4.2 PollingPoolManager实现接口

```python
# 在src/services/llm/polling_pool.py中
class PollingPoolManager(IPollingPoolManager):
    # 需要添加list_all_status方法（已有get_all_status，可以重命名或添加别名）
    def list_all_status(self) -> Dict[str, Any]:
        return self.get_all_status()
```

#### 4.3 创建ClientFactory实现

```python
# 在src/services/llm/client_factory.py中（新文件）
class ClientFactory(IClientFactory):
    def __init__(self, llm_factory):
        self.llm_factory = llm_factory
    
    def create_client(self, model_name: str) -> ILLMClient:
        # 使用LLMFactory创建客户端
        config = {"model_name": model_name}
        return self.llm_factory.create_client(config)
    
    def get_available_models(self) -> List[str]:
        # 从LLMFactory获取可用模型
        return self.llm_factory.list_supported_types()
```

#### 4.4 创建FallbackManager实现

```python
# 在src/services/llm/enhanced_fallback_manager.py中（新文件）
class EnhancedFallbackManager(IFallbackManager):
    def __init__(self, task_group_manager, polling_pool_manager, client_factory):
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.client_factory = client_factory
        # 将原有的EnhancedFallbackManager逻辑移到这里
    
    async def execute_with_fallback(self, primary_target, fallback_groups, prompt, parameters=None, **kwargs):
        # 实现降级逻辑
        pass
    
    def get_stats(self):
        # 返回统计信息
        pass
    
    def reset_stats(self):
        # 重置统计信息
        pass
```

### 5. 更新依赖注入配置

#### 5.1 创建LLM模块DI配置

```python
# 在src/services/llm/di_config.py中
def register_llm_services(container):
    """注册LLM相关服务"""
    
    # 注册配置加载器
    from infrastructure.config.loader.file_config_loader import FileConfigLoader
    container.register_singleton(FileConfigLoader)
    
    # 注册任务组管理器
    from .task_group_manager import TaskGroupManager
    container.register_singleton(ITaskGroupManager, TaskGroupManager)
    
    # 注册轮询池管理器
    from .polling_pool import PollingPoolManager
    container.register_singleton(IPollingPoolManager, PollingPoolManager)
    
    # 注册LLM工厂
    from ..core.llm.factory import LLMFactory
    container.register_singleton(LLMFactory)
    
    # 注册客户端工厂
    from .client_factory import ClientFactory
    container.register_singleton(IClientFactory, ClientFactory)
    
    # 注册降级管理器
    from .enhanced_fallback_manager import EnhancedFallbackManager
    container.register_singleton(IFallbackManager, EnhancedFallbackManager)
```

### 6. 更新包装器工厂

#### 6.1 修改wrapper_factory.py

```python
# 在src/core/llm/wrappers/wrapper_factory.py中
def create_task_group_wrapper(name: str, config: Dict[str, Any], container) -> TaskGroupWrapper:
    """创建任务组包装器"""
    task_group_manager = container.get(ITaskGroupManager)
    fallback_manager = container.get(IFallbackManager) if config.get("enable_fallback", True) else None
    
    return TaskGroupWrapper(
        name=name,
        task_group_manager=task_group_manager,
        fallback_manager=fallback_manager,
        config=config
    )

def create_enhanced_fallback_manager(container) -> EnhancedFallbackManager:
    """创建增强降级管理器"""
    task_group_manager = container.get(ITaskGroupManager)
    polling_pool_manager = container.get(IPollingPoolManager)
    client_factory = container.get(IClientFactory)
    
    return EnhancedFallbackManager(
        task_group_manager=task_group_manager,
        polling_pool_manager=polling_pool_manager,
        client_factory=client_factory
    )
```

## 实施步骤

1. **第一步**：在`src/core/llm/interfaces.py`中添加新接口定义
2. **第二步**：重构`TaskGroupWrapper`使用接口依赖
3. **第三步**：重构`EnhancedFallbackManager`使用接口依赖
4. **第四步**：更新Services层实现类以实现相应接口
5. **第五步**：创建新的实现类（ClientFactory、EnhancedFallbackManager）
6. **第六步**：更新依赖注入配置
7. **第七步**：更新包装器工厂
8. **第八步**：测试验证

## 预期效果

1. **架构清晰**：Core层不再依赖Services层，符合依赖倒置原则
2. **易于测试**：可以轻松创建接口的Mock实现进行单元测试
3. **松耦合**：各组件通过接口交互，降低耦合度
4. **可扩展性**：可以轻松替换实现类而不影响使用方

## 风险评估

1. **低风险**：主要是重构现有代码，不改变核心业务逻辑
2. **测试覆盖**：需要确保所有现有测试仍然通过
3. **依赖注入**：需要确保DI容器正确配置所有依赖关系

## 总结

通过引入接口抽象层和依赖注入，我们可以解决Core层依赖Services层的架构问题，使代码更加清晰、可测试和可维护。