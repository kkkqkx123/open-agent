# 依赖注入重构分阶段实施方案

## 重构概述

基于新的简洁架构设计，制定一个分阶段的重构方案。由于业务尚未部署，我们可以采用激进的重构策略，快速完成架构升级。

## 阶段划分

### 阶段1：基础设施层重构（3天）
**目标**：创建新的基础设施层容器实现

#### 任务1.1：创建新的容器接口
```python
# src/interfaces/container/core.py
# 定义简洁的容器接口
```

#### 任务1.2：实现基础设施层容器
```python
# src/infrastructure/container/dependency_container.py
# 实现简洁的容器逻辑
```

#### 任务1.3：创建容器引导器
```python
# src/infrastructure/container/bootstrap.py
# 静态方法引导容器初始化
```

#### 交付物
- ✅ 新的容器接口定义
- ✅ 基础设施层容器实现
- ✅ 容器引导器
- ✅ 基础单元测试

### 阶段2：服务绑定迁移（4天）
**目标**：迁移所有服务绑定到新架构

#### 任务2.1：重构日志服务绑定
```python
# src/services/container/bindings/logger_bindings.py
# 使用新的容器API
```

#### 任务2.2：重构配置服务绑定
```python
# src/services/container/bindings/config_bindings.py
# 简化配置服务注册
```

#### 任务2.3：重构工作流服务绑定
```python
# src/services/container/bindings/workflow_bindings.py
# 迁移工作流相关服务
```

#### 任务2.4：重构其他服务绑定
- 存储服务绑定
- LLM服务绑定
- 工具服务绑定

#### 交付物
- ✅ 所有服务绑定迁移完成
- ✅ 集成测试通过
- ✅ 性能基准测试

### 阶段3：清理旧代码（1天）
**目标**：彻底移除旧的依赖注入实现

#### 任务3.1：删除临时解决方案
```bash
# 删除临时依赖注入实现
rm -rf src/interfaces/dependency_injection/
```

#### 任务3.2：清理相关配置文件
```bash
# 清理不再需要的配置文件
rm src/services/container/core/container.py
```

#### 任务3.3：更新导入引用
```python
# 更新所有使用旧容器的代码
from src.infrastructure.container.bootstrap import ContainerBootstrap
```

#### 交付物
- ✅ 旧代码完全移除
- ✅ 所有导入引用更新
- ✅ 代码库清理完成

### 阶段4：测试和优化（2天）
**目标**：确保新架构稳定可靠

#### 任务4.1：全面测试
- 单元测试覆盖率 > 90%
- 集成测试覆盖所有服务
- 性能回归测试

#### 任务4.2：性能优化
- 容器初始化时间优化
- 服务解析性能优化
- 内存使用优化

#### 任务4.3：文档更新
- 更新架构文档
- 创建使用指南
- 更新API文档

#### 交付物
- ✅ 测试覆盖率达标
- ✅ 性能指标达标
- ✅ 文档完整

## 详细实施步骤

### 第1天：创建新架构基础

#### 上午：创建接口层
```python
# src/interfaces/container/core.py
from abc import ABC, abstractmethod
from typing import Type, TypeVar, Callable
from enum import Enum

T = TypeVar('T')

class ServiceLifetime(Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"

class IDependencyContainer(ABC):
    @abstractmethod
    def register(self, interface: Type, implementation: Type, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        pass
    
    @abstractmethod
    def get(self, service_type: Type[T]) -> T:
        pass
```

#### 下午：实现基础设施层容器
```python
# src/infrastructure/container/dependency_container.py
import threading
from typing import Dict, Any

from src.interfaces.container.core import IDependencyContainer, ServiceLifetime

class DependencyContainer(IDependencyContainer):
    def __init__(self):
        self._registrations: Dict[Type, Dict] = {}
        self._instances: Dict[Type, Any] = {}
        self._lock = threading.RLock()
    
    def register(self, interface: Type, implementation: Type, lifetime: ServiceLifetime = ServiceLifetime.SINGLETON) -> None:
        with self._lock:
            self._registrations[interface] = {
                'implementation': implementation,
                'lifetime': lifetime
            }
    
    def get(self, service_type: Type[T]) -> T:
        with self._lock:
            if service_type not in self._registrations:
                raise ValueError(f"服务未注册: {service_type.__name__}")
            
            registration = self._registrations[service_type]
            
            # 单例模式检查缓存
            if registration['lifetime'] == ServiceLifetime.SINGLETON:
                if service_type in self._instances:
                    return self._instances[service_type]
            
            # 创建实例
            instance = registration['implementation']()
            
            # 缓存单例实例
            if registration['lifetime'] == ServiceLifetime.SINGLETON:
                self._instances[service_type] = instance
            
            return instance
```

### 第2天：创建引导器和测试

#### 上午：创建容器引导器
```python
# src/infrastructure/container/bootstrap.py
from typing import Dict, Any
from .dependency_container import DependencyContainer
from src.interfaces.container.core import IDependencyContainer

class ContainerBootstrap:
    @staticmethod
    def create_container(config: Dict[str, Any]) -> IDependencyContainer:
        """创建并初始化容器"""
        container = DependencyContainer()
        
        # 注册基础设施服务
        ContainerBootstrap._register_infrastructure_services(container, config)
        
        return container
    
    @staticmethod
    def _register_infrastructure_services(container: IDependencyContainer, config: Dict[str, Any]):
        """注册基础设施服务"""
        # 注册日志服务
        from src.services.container.bindings.logger_bindings import LoggerServiceBindings
        logger_bindings = LoggerServiceBindings()
        logger_bindings.register_services(container, config)
```

#### 下午：编写基础测试
```python
# tests/test_new_container.py
import pytest
from src.infrastructure.container.bootstrap import ContainerBootstrap
from src.interfaces.logger import ILogger

def test_container_creation():
    """测试容器创建"""
    config = {"log_level": "INFO"}
    container = ContainerBootstrap.create_container(config)
    
    assert container is not None

def test_service_resolution():
    """测试服务解析"""
    config = {"log_level": "INFO"}
    container = ContainerBootstrap.create_container(config)
    
    logger = container.get(ILogger)
    assert logger is not None
```

### 第3-6天：服务绑定迁移

#### 逐个迁移服务绑定
```python
# src/services/container/bindings/logger_bindings.py
from src.interfaces.logger import ILogger, ILoggerFactory
from src.interfaces.container.core import ServiceLifetime

class LoggerServiceBindings:
    def register_services(self, container, config: Dict[str, Any]):
        """注册日志服务"""
        # 注册日志工厂
        container.register(
            ILoggerFactory,
            lambda: __import__('src.infrastructure.logger.factory.logger_factory').LoggerFactory(),
            ServiceLifetime.SINGLETON
        )
        
        # 注册日志服务
        container.register(
            ILogger,
            lambda: container.get(ILoggerFactory).create_logger("application"),
            ServiceLifetime.SINGLETON
        )
```

### 第7天：清理旧代码

#### 删除临时解决方案
```bash
# 删除临时依赖注入目录
rm -rf src/interfaces/dependency_injection/

# 删除旧的容器实现
rm src/services/container/core/container.py
rm src/infrastructure/container/dependency_container.py
```

#### 更新所有导入
```python
# 在所有文件中更新导入
# 旧：from src.services.container.core.container import DependencyContainer
# 新：from src.infrastructure.container.bootstrap import ContainerBootstrap
```

### 第8-9天：测试和优化

#### 全面测试
```python
# 运行所有测试
pytest tests/ -v

# 性能测试
python benchmarks/container_performance.py
```

#### 性能优化
- 优化容器初始化逻辑
- 缓存优化
- 内存使用优化

## 风险评估和缓解

### 风险1：服务绑定迁移失败
- **风险**：某些服务绑定无法正常迁移
- **缓解**：逐个服务测试，确保每个服务迁移后功能正常
- **回滚**：保留旧代码备份，随时可以回滚

### 风险2：性能下降
- **风险**：新架构可能影响性能
- **缓解**：进行性能基准测试，优化关键路径
- **监控**：实时监控性能指标

### 风险3：集成问题
- **风险**：与其他模块集成出现问题
- **缓解**：全面的集成测试
- **沟通**：与其他模块负责人协调

## 成功指标

### 功能指标
- ✅ 所有现有功能正常工作
- ✅ 新架构稳定运行
- ✅ 无回归问题

### 技术指标
- ✅ 测试覆盖率 > 90%
- ✅ 性能指标达标
- ✅ 代码质量达标

### 时间指标
- ✅ 按计划完成各阶段
- ✅ 总实施时间 < 10天

## 总结

这个分阶段的重构方案具有以下特点：

1. **激进但可控**：采用激进的重构策略，但通过分阶段控制风险
2. **时间紧凑**：总实施时间控制在10天内
3. **质量保证**：每个阶段都有明确的交付物和测试
4. **风险可控**：有明确的风险缓解措施

通过这个方案，我们可以快速、安全地完成依赖注入架构的重构，从根本上解决循环依赖问题。