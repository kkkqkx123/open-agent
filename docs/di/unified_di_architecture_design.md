# 统一DI容器架构设计方案

## 1. 设计目标

基于当前DI容器架构分析，设计统一、分层、可维护的依赖注入架构，解决现有架构中的依赖倒置、配置分散、容器不统一等问题。

## 2. 架构原则

### 2.1 分层原则
- **单一职责**: 每层只负责自己的服务注册
- **依赖方向**: 高层依赖低层，基础设施层不依赖其他层
- **接口隔离**: 各层通过接口进行交互，不直接依赖具体实现

### 2.2 统一原则
- **统一接口**: 所有层使用相同的IDependencyContainer接口
- **统一入口**: 通过统一配置入口组合各层配置
- **统一管理**: 统一的服务生命周期管理和环境配置

### 2.3 可维护原则
- **模块化**: 服务注册模块化，便于维护和扩展
- **可配置**: 支持不同环境的灵活配置
- **可测试**: 各层可独立测试，支持Mock和Stub

## 3. 分层架构设计

### 3.1 基础设施层DI配置 (infrastructure/di/)

**职责**: 注册基础设施相关服务，如数据库、缓存、日志、配置等

**文件结构**:
```
src/infrastructure/di/
├── __init__.py
├── infrastructure_config.py      # 基础设施服务配置
├── container_factory.py          # 容器工厂
├── service_registries.py         # 服务注册表
├── infrastructure_module.py        # 基础设施模块
└── config/
    ├── __init__.py
    ├── database_config.py        # 数据库服务配置
    ├── cache_config.py           # 缓存服务配置
    ├── logging_config.py         # 日志服务配置
    └── monitoring_config.py      # 监控服务配置
```

**核心实现**:
```python
# infrastructure/di/infrastructure_config.py
class InfrastructureConfig:
    """基础设施层DI配置"""
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置基础设施服务"""
        # 配置数据库服务
        DatabaseConfig.configure(container, environment)
        
        # 配置缓存服务
        CacheConfig.configure(container, environment)
        
        # 配置日志服务
        LoggingConfig.configure(container, environment)
        
        # 配置监控服务
        MonitoringConfig.configure(container, environment)
        
        # 配置基础工具服务
        InfrastructureModule.register_services(container, environment)
```

### 3.2 领域层DI配置 (domain/di/)

**职责**: 注册领域模型、领域服务和领域事件

**文件结构**:
```
src/domain/di/
├── __init__.npy
├── domain_config.py              # 领域服务配置
├── domain_module.py              # 领域模块
├── workflow_domain_config.py     # 工作流领域配置
├── session_domain_config.py      # 会话领域配置
└── repositories/
    ├── __init__.py
    ├── workflow_repo_config.py   # 工作流仓库配置
    └── session_repo_config.py    # 会话仓库配置
```

**核心实现**:
```python
# domain/di/domain_config.py
class DomainConfig:
    """领域层DI配置"""
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置领域服务"""
        # 配置工作流领域服务
        WorkflowDomainConfig.configure(container, environment)
        
        # 配置会话领域服务
        SessionDomainConfig.configure(container, environment)
        
        # 配置领域模块
        DomainModule.register_services(container, environment)
```

### 3.3 应用层DI配置 (application/di/)

**职责**: 注册应用服务、工作流协调、会话管理等

**文件结构**:
```
src/application/di/
├── __init__.py
├── application_config.py       # 应用服务配置
├── application_module.py       # 应用模块
├── workflow_config.py          # 工作流应用配置
├── session_config.py           # 会话应用配置
└── services/
    ├── __init__.py
    ├── workflow_service_config.py  # 工作流服务配置
    └── session_service_config.py   # 会话服务配置
```

**核心实现**:
```python
# application/di/application_config.py
class ApplicationConfig:
    """应用层DI配置"""
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置应用服务"""
        # 配置工作流应用服务
        WorkflowConfig.configure(container, environment)
        
        # 配置会话应用服务
        SessionConfig.configure(container, environment)
        
        # 配置应用模块
        ApplicationModule.register_services(container, environment)
```

### 3.4 表示层DI配置 (presentation/di/)

**职责**: 注册UI组件、API控制器、视图模型等

**文件结构**:
```
src/presentation/di/
├── __init__.py
├── presentation_config.py        # 表示服务配置
├── presentation_module.py        # 表示模块
├── api_config.py                # API服务配置
├── ui_config.py                 # UI服务配置
└── controllers/
    ├── __init__.py
    ├── workflow_controller_config.py  # 工作流控制器配置
    └── session_controller_config.py   # 会话控制器配置
```

**核心实现**:
```python
# presentation/di/presentation_config.py
class PresentationConfig:
    """表示层DI配置"""
    
    @staticmethod
    def configure(container: IDependencyContainer, environment: str = "default") -> None:
        """配置表示服务"""
        # 配置API服务
        ApiConfig.configure(container, environment)
        
        # 配置UI服务
        UiConfig.configure(container, environment)
        
        # 配置表示模块
        PresentationModule.register_services(container, environment)
```

## 4. 统一容器管理

### 4.1 统一容器管理器 (di/unified_container.py)

**职责**: 统一管理所有层的DI配置，提供统一的配置入口

**核心实现**:
```python
# di/unified_container.py
class UnifiedContainerManager:
    """统一容器管理器"""
    
    def __init__(self):
        self.container = EnhancedDependencyContainer()
        self.environment = "default"
        self._configured = False
    
    def configure_all_layers(self, environment: str = "default") -> IDependencyContainer:
        """配置所有层的服务"""
        if self._configured:
            logger.warning("容器已经配置过，重新配置将清除现有配置")
            self.container.clear()
        
        self.environment = environment
        
        try:
            # 基础设施层配置（最先配置）
            logger.info("开始配置基础设施层服务...")
            InfrastructureConfig.configure(self.container, environment)
            
            # 领域层配置
            logger.info("开始配置领域层服务...")
            DomainConfig.configure(self.container, environment)
            
            # 应用层配置
            logger.info("开始配置应用层服务...")
            ApplicationConfig.configure(self.container, environment)
            
            # 表示层配置（最后配置）
            logger.info("开始配置表示层服务...")
            PresentationConfig.configure(self.container, environment)
            
            self._configured = True
            logger.info(f"所有层服务配置完成，环境: {environment}")
            
            return self.container
            
        except Exception as e:
            logger.error(f"配置过程中发生错误: {e}")
            self._configured = False
            raise
    
    def get_container(self) -> IDependencyContainer:
        """获取配置好的容器"""
        if not self._configured:
            raise RuntimeError("容器尚未配置，请先调用configure_all_layers()")
        return self.container
    
    def validate_configuration(self) -> Dict[str, Any]:
        """验证配置"""
        if not self._configured:
            return {"valid": False, "error": "容器尚未配置"}
        
        # 验证各层核心服务
        validation_results = {
            "valid": True,
            "infrastructure_services": self._validate_infrastructure_services(),
            "domain_services": self._validate_domain_services(),
            "application_services": self._validate_application_services(),
            "presentation_services": self._validate_presentation_services(),
            "errors": [],
            "warnings": []
        }
        
        # 汇总验证结果
        for category in ["infrastructure_services", "domain_services", 
                        "application_services", "presentation_services"]:
            if not validation_results[category]["valid"]:
                validation_results["valid"] = False
                validation_results["errors"].extend(validation_results[category]["errors"])
        
        return validation_results
```

### 4.2 全局容器管理

**全局访问点**:
```python
# di/__init__.py
_unified_manager: Optional[UnifiedContainerManager] = None

def get_unified_container(environment: str = "default", 
                         force_reconfigure: bool = False) -> IDependencyContainer:
    """获取统一配置的容器"""
    global _unified_manager
    
    if _unified_manager is None or force_reconfigure:
        _unified_manager = UnifiedContainerManager()
        _unified_manager.configure_all_layers(environment)
    
    return _unified_manager.get_container()

def reset_unified_container() -> None:
    """重置统一容器"""
    global _unified_manager
    _unified_manager = None
```

## 5. 模块化服务注册标准

### 5.1 标准化模块接口

```python
# di/interfaces.py
from abc import ABC, abstractmethod
from typing import Dict, Any, Type

class IServiceModule(ABC):
    """服务模块接口"""
    
    @abstractmethod
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务"""
        pass
    
    @abstractmethod
    def register_environment_services(self, 
                                    container: IDependencyContainer, 
                                    environment: str) -> None:
        """注册环境特定服务"""
        pass
    
    @abstractmethod
    def get_module_name(self) -> str:
        """获取模块名称"""
        pass
    
    @abstractmethod
    def get_registered_services(self) -> Dict[str, Type]:
        """获取注册的服务类型"""
        pass
```

### 5.2 基础模块实现

```python
# infrastructure/di/infrastructure_module.py
class InfrastructureModule(IServiceModule):
    """基础设施模块"""
    
    def __init__(self):
        self.registered_services = {}
    
    def register_services(self, container: IDependencyContainer) -> None:
        """注册基础服务"""
        # 注册配置相关服务
        self._register_config_services(container)
        
        # 注册数据库相关服务
        self._register_database_services(container)
        
        # 注册缓存相关服务
        self._register_cache_services(container)
        
        # 注册日志相关服务
        self._register_logging_services(container)
    
    def register_environment_services(self, 
                                    container: IDependencyContainer, 
                                    environment: str) -> None:
        """注册环境特定服务"""
        if environment == "development":
            self._register_development_services(container)
        elif environment == "test":
            self._register_test_services(container)
        elif environment == "production":
            self._register_production_services(container)
    
    def get_module_name(self) -> str:
        return "infrastructure"
    
    def get_registered_services(self) -> Dict[str, Type]:
        return self.registered_services.copy()
    
    def _register_config_services(self, container: IDependencyContainer) -> None:
        """注册配置服务"""
        # 具体实现...
        pass
    
    def _register_database_services(self, container: IDependencyContainer) -> None:
        """注册数据库服务"""
        # 具体实现...
        pass
    
    def _register_cache_services(self, container: IDependencyContainer) -> None:
        """注册缓存服务"""
        # 具体实现...
        pass
    
    def _register_logging_services(self, container: IDependencyContainer) -> None:
        """注册日志服务"""
        # 具体实现...
        pass
    
    def _register_development_services(self, container: IDependencyContainer) -> None:
        """注册开发环境服务"""
        # 具体实现...
        pass
    
    def _register_test_services(self, container: IDependencyContainer) -> None:
        """注册测试环境服务"""
        # 具体实现...
        pass
    
    def _register_production_services(self, container: IDependencyContainer) -> None:
        """注册生产环境服务"""
        # 具体实现...
        pass
```

## 6. 环境配置管理

### 6.1 环境配置管理器

```python
# di/environment_config.py
class EnvironmentConfigManager:
    """环境配置管理器"""
    
    def __init__(self):
        self.environments = {
            "development": DevelopmentConfig(),
            "test": TestConfig(),
            "production": ProductionConfig()
        }
        self.current_environment = "default"
    
    def set_environment(self, environment: str) -> None:
        """设置当前环境"""
        if environment not in self.environments:
            raise ValueError(f"不支持的环境: {environment}")
        
        self.current_environment = environment
        logger.info(f"环境设置为: {environment}")
    
    def get_current_config(self) -> EnvironmentConfig:
        """获取当前环境配置"""
        if self.current_environment == "default":
            return DefaultConfig()
        
        return self.environments[self.current_environment]
    
    def should_register_service(self, service_type: Type, environment: str) -> bool:
        """判断是否应该注册服务"""
        config = self.environments.get(environment, DefaultConfig())
        return config.should_register_service(service_type)
    
    def get_service_config(self, service_type: Type, environment: str) -> Dict[str, Any]:
        """获取服务配置"""
        config = self.environments.get(environment, DefaultConfig())
        return config.get_service_config(service_type)

class EnvironmentConfig(ABC):
    """环境配置基类"""
    
    @abstractmethod
    def should_register_service(self, service_type: Type) -> bool:
        """判断是否应该注册服务"""
        pass
    
    @abstractmethod
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        """获取服务配置"""
        pass

class DevelopmentConfig(EnvironmentConfig):
    """开发环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        # 开发环境注册所有服务
        return True
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        # 返回开发环境特定配置
        return {
            "enable_debug": True,
            "enable_profiling": True,
            "log_level": "DEBUG"
        }

class ProductionConfig(EnvironmentConfig):
    """生产环境配置"""
    
    def should_register_service(self, service_type: Type) -> bool:
        # 生产环境只注册必要服务
        # 过滤掉调试和开发相关服务
        return not self._is_debug_service(service_type)
    
    def get_service_config(self, service_type: Type) -> Dict[str, Any]:
        # 返回生产环境特定配置
        return {
            "enable_debug": False,
            "enable_profiling": False,
            "log_level": "INFO",
            "enable_caching": True,
            "enable_optimization": True
        }
    
    def _is_debug_service(self, service_type: Type) -> bool:
        """判断是否为调试服务"""
        # 具体实现...
        pass
```

## 7. 迁移实施步骤

### 7.1 第一阶段：基础设施准备

1. **创建分层目录结构**
```bash
mkdir -p src/infrastructure/di/config
mkdir -p src/domain/di/repositories
mkdir -p src/application/di/services
mkdir -p src/presentation/di/controllers
mkdir -p src/di
```

2. **创建基础接口和类**
```bash
touch src/di/__init__.py
touch src/di/interfaces.py
touch src/di/unified_container.py
touch src/di/environment_config.py
```

3. **实现统一容器管理器**
- 实现UnifiedContainerManager
- 实现全局访问函数
- 添加基础验证逻辑

### 7.2 第二阶段：分层配置实现

1. **基础设施层配置**
```bash
touch src/infrastructure/di/__init__.py
touch src/infrastructure/di/infrastructure_config.py
touch src/infrastructure/di/infrastructure_module.py
touch src/infrastructure/di/config/database_config.py
touch src/infrastructure/di/config/cache_config.py
```

2. **领域层配置**
```bash
touch src/domain/di/__init__.py
touch src/domain/di/domain_config.py
touch src/domain/di/domain_module.py
touch src/domain/di/workflow_domain_config.py
```

3. **应用层配置**
```bash
touch src/application/di/__init__.py
touch src/application/di/application_config.py
touch src/application/di/application_module.py
touch src/application/di/workflow_config.py
```

4. **表示层配置**
```bash
touch src/presentation/di/__init__.py
touch src/presentation/di/presentation_config.py
touch src/presentation/di/presentation_module.py
touch src/presentation/di/api_config.py
```

### 7.3 第三阶段：服务迁移

1. **迁移基础设施服务**
- 将di_config.py中的基础设施服务迁移到infrastructure_config.py
- 保持现有接口不变，确保向后兼容
- 添加适当的日志和验证

2. **迁移领域服务**
- 识别并迁移领域层服务
- 确保领域层不依赖应用层和表示层
- 添加领域事件和仓储配置

3. **迁移应用服务**
- 迁移工作流、会话等应用服务
- 确保应用层依赖领域层和基础设施层
- 添加应用层特定的配置

4. **迁移表示服务**
- 迁移API和UI相关服务
- 确保表示层依赖应用层
- 添加控制器和视图模型配置

### 7.4 第四阶段：集成测试

1. **单元测试**
```bash
mkdir -p tests/unit/di/
touch tests/unit/di/test_unified_container.py
touch tests/unit/di/test_infrastructure_config.py
touch tests/unit/di/test_domain_config.py
```

2. **集成测试**
```bash
mkdir -p tests/integration/di/
touch tests/integration/di/test_layer_integration.py
touch tests/integration/di/test_environment_config.py
```

3. **验证测试**
- 验证各层服务正确注册
- 验证依赖关系正确
- 验证环境配置有效

### 7.5 第五阶段：优化和清理

1. **性能优化**
- 优化服务注册顺序
- 添加服务缓存机制
- 优化依赖解析算法

2. **代码清理**
- 移除旧的DI配置
- 清理重复代码
- 统一代码风格

3. **文档完善**
- 完善API文档
- 添加使用示例
- 更新架构文档

## 8. 验证和监控

### 8.1 配置验证

```python
# di/validation.py
class ConfigurationValidator:
    """配置验证器"""
    
    def validate_layer_configuration(self, 
                                   container: IDependencyContainer,
                                   layer_name: str) -> Dict[str, Any]:
        """验证层配置"""
        result = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "services_validated": 0
        }
        
        # 获取该层应该注册的服务
        expected_services = self._get_expected_services(layer_name)
        
        for service_type in expected_services:
            if not container.has_service(service_type):
                result["errors"].append(f"缺少服务: {service_type.__name__}")
                result["valid"] = False
            else:
                result["services_validated"] += 1
                
                # 验证服务可以正确实例化
                try:
                    service_instance = container.get(service_type)
                    if service_instance is None:
                        result["errors"].append(f"服务实例为None: {service_type.__name__}")
                        result["valid"] = False
                except Exception as e:
                    result["errors"].append(f"服务实例化失败 {service_type.__name__}: {str(e)}")
                    result["valid"] = False
        
        return result
    
    def validate_dependency_graph(self, container: IDependencyContainer) -> Dict[str, Any]:
        """验证依赖图"""
        # 使用DependencyAnalyzer验证依赖关系
        pass
```

### 8.2 运行时监控

```python
# di/monitoring.py
class ContainerMonitor:
    """容器监控器"""
    
    def __init__(self, container: IDependencyContainer):
        self.container = container
        self.metrics = {
            "service_creation_count": 0,
            "service_creation_time": {},
            "dependency_resolution_count": 0,
            "circular_dependency_detected": 0
        }
    
    def monitor_service_creation(self, service_type: Type, creation_time: float):
        """监控服务创建"""
        self.metrics["service_creation_count"] += 1
        
        service_name = service_type.__name__
        if service_name not in self.metrics["service_creation_time"]:
            self.metrics["service_creation_time"][service_name] = []
        
        self.metrics["service_creation_time"][service_name].append(creation_time)
    
    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        return self.metrics.copy()
```

## 9. 总结

统一DI容器架构设计方案通过以下方式解决了现有架构问题：

### 9.1 解决的问题

1. **依赖倒置**: 通过分层配置，确保各层只注册自己的服务
2. **配置分散**: 通过统一容器管理器，集中管理所有配置
3. **容器不统一**: 通过统一接口和全局管理，确保容器一致性
4. **环境管理**: 通过标准化环境配置，简化环境管理

### 9.2 架构优势

1. **分层清晰**: 各层职责明确，符合分层架构原则
2. **易于维护**: 模块化设计，便于维护和扩展
3. **可测试性强**: 支持分层测试和Mock注入
4. **灵活性高**: 支持多种环境和配置组合
5. **性能优化**: 支持服务缓存和依赖优化

### 9.3 实施价值

1. **提升开发效率**: 简化DI配置，减少重复代码
2. **降低维护成本**: 统一架构，减少架构债务
3. **提高代码质量**: 标准化设计，减少错误
4. **增强可扩展性**: 模块化设计，易于扩展
5. **改善团队协作**: 统一标准，便于团队协作

通过实施这个统一DI容器架构设计方案，可以显著提升项目的架构质量、可维护性和开发效率，为项目的长期发展奠定坚实基础。