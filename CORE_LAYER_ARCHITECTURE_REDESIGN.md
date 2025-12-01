# Core 层架构重新设计方案

## 🎯 问题分析

当前 `src/core/workflow/error_handler.py` 存在架构违规问题：

1. **Core层直接调用Service层**：违反了分层架构原则
2. **Core层使用依赖注入容器**：Core层应该是纯净的业务逻辑，不依赖基础设施
3. **职责混乱**：错误处理逻辑与日志记录耦合

## 🏗️ 架构重新设计

### 设计原则

1. **Core层纯净性**：Core层只包含纯业务逻辑，不依赖任何外部基础设施
2. **依赖方向正确**：Service层 → Core层 → Interface层
3. **职责单一**：每层只负责自己的职责
4. **接口驱动**：通过接口实现解耦

### 新的架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    Adapters Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │   API Adapter   │  │   TUI Adapter   │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Services Layer                            │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Workflow Service│  │ Logger Service  │                  │
│  │ - Error Handler │  │ - Logging Logic │                  │
│  │ - Recovery Mgr  │  │ - DI Container  │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Core Layer                              │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ Workflow Core   │  │ Error Core      │                  │
│  │ - Business Logic│  │ - Error Types   │                  │
│  │ - State Mgmt    │  │ - Strategies    │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                  Interfaces Layer                           │
│  ┌─────────────────┐  ┌─────────────────┐                  │
│  │ IWorkflow       │  │ ILogger         │                  │
│  │ IErrorHandler   │  │ IErrorStrategy  │                  │
│  └─────────────────┘  └─────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## 📋 具体实施方案

### 第一步：Core层重构

**目标**：创建纯业务逻辑的Core层

#### 1.1 创建纯Core层错误处理逻辑

```python
# src/core/workflow/error_core.py
class WorkflowErrorCore:
    """纯Core层工作流错误处理逻辑"""
    
    def classify_error(self, error: Exception) -> WorkflowErrorType:
        """错误分类逻辑（纯业务逻辑）"""
        pass
    
    def create_recovery_strategy(self, error_type: WorkflowErrorType) -> Dict[str, Any]:
        """创建恢复策略（纯业务逻辑）"""
        pass
    
    def validate_workflow_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流配置（纯业务逻辑）"""
        pass
```

#### 1.2 移除Core层中的依赖注入

```python
# 移除以下内容：
# - from src.services.container import get_global_container
# - from src.interfaces.common_infra import ILogger
# - 所有依赖注入相关代码
```

### 第二步：Service层重构

**目标**：将需要依赖注入的功能移到Service层

#### 2.1 创建Service层错误处理器

```python
# src/services/workflow/error_service.py
class WorkflowErrorService:
    """Service层工作流错误处理服务"""
    
    def __init__(self, logger: ILogger, error_core: WorkflowErrorCore):
        self._logger = logger
        self._error_core = error_core
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None:
        """处理错误（包含日志记录）"""
        # 使用Core层进行错误分类
        error_type = self._error_core.classify_error(error)
        
        # 使用Service层进行日志记录
        self._logger.error(f"处理错误: {error_type.value}")
        
        # 使用Core层创建恢复策略
        strategy = self._error_core.create_recovery_strategy(error_type)
```

#### 2.2 创建Service层恢复管理器

```python
# src/services/workflow/recovery_service.py
class WorkflowRecoveryService:
    """Service层工作流恢复管理器"""
    
    def __init__(self, logger: ILogger, error_service: WorkflowErrorService):
        self._logger = logger
        self._error_service = error_service
    
    def attempt_recovery(self, error: Exception, context: Dict[str, Any]) -> Optional[Any]:
        """尝试恢复（包含日志记录）"""
        pass
```

### 第三步：依赖注入配置

**目标**：正确配置Service层的依赖注入

#### 3.1 更新依赖注入绑定

```python
# src/services/container/workflow_bindings.py
def register_workflow_services(container, config: Dict[str, Any]) -> None:
    """注册工作流相关服务"""
    
    # 注册Core层组件（无依赖）
    container.register_factory(
        IWorkflowErrorCore,
        lambda: WorkflowErrorCore(),
        lifetime=ServiceLifetime.SINGLETON
    )
    
    # 注册Service层组件（有依赖）
    def error_service_factory() -> IWorkflowErrorHandler:
        logger = container.get(ILogger)
        error_core = container.get(IWorkflowErrorCore)
        return WorkflowErrorService(logger, error_core)
    
    container.register_factory(
        IWorkflowErrorHandler,
        error_service_factory,
        lifetime=ServiceLifetime.SINGLETON
    )
```

### 第四步：接口层完善

**目标**：确保接口层定义完整

#### 4.1 添加缺失的接口

```python
# src/interfaces/workflow.py
class IWorkflowErrorCore(Protocol):
    """工作流错误处理核心接口"""
    
    def classify_error(self, error: Exception) -> WorkflowErrorType: ...
    def create_recovery_strategy(self, error_type: WorkflowErrorType) -> Dict[str, Any]: ...

class IWorkflowErrorHandler(Protocol):
    """工作流错误处理服务接口"""
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> None: ...
```

## 🔄 迁移策略

### 阶段1：创建新的Core层组件
1. 创建 `src/core/workflow/error_core.py`
2. 移植纯业务逻辑
3. 移除所有依赖注入代码

### 阶段2：创建新的Service层组件
1. 创建 `src/services/workflow/error_service.py`
2. 创建 `src/services/workflow/recovery_service.py`
3. 实现依赖注入

### 阶段3：更新依赖注入配置
1. 创建 `src/services/container/workflow_bindings.py`
2. 注册新的服务
3. 更新现有绑定

### 阶段4：清理旧代码
1. 删除 `src/core/workflow/error_handler.py` 中的违规代码
2. 更新导入引用
3. 运行测试验证

## ✅ 验证标准

1. **架构合规性**：Core层不依赖任何Service层或基础设施
2. **功能完整性**：所有原有功能正常工作
3. **依赖注入正确**：Service层正确使用依赖注入
4. **接口一致性**：所有接口定义完整且一致
5. **测试通过**：所有相关测试用例通过

## 🎯 预期收益

1. **架构清晰**：分层明确，职责单一
2. **易于测试**：Core层可以独立测试
3. **易于维护**：依赖关系清晰，修改影响范围可控
4. **符合规范**：遵循项目架构规范和最佳实践

这个重新设计方案确保了架构的合规性，同时保持了功能的完整性。