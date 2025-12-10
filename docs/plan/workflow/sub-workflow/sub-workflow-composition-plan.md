# 子工作流组合和拼接分层实现方案

## 概述

基于当前项目的分层架构（Interfaces + Core + Services + Infrastructure），制定子工作流组合和拼接功能的实现方案。

## 当前架构分析

### Core层已实现的功能
- **工作流协调器** ([`src/core/workflow/coordinator/workflow_coordinator.py`](src/core/workflow/coordinator/workflow_coordinator.py))
  - 工作流创建、执行、验证
  - 配置加载和验证
  - 工作流统计信息
- **工作流构建器** ([`src/core/workflow/core/builder.py`](src/core/workflow/core/builder.py))
  - 图构建逻辑
  - 节点和边构建
- **配置管理** ([`src/core/workflow/config/config.py`](src/core/workflow/config/config.py))
  - 图配置定义
  - 配置验证
- **子工作流节点** ([`src/core/workflow/graph/nodes/state_machine/subworkflow_node.py`](src/core/workflow/graph/nodes/state_machine/subworkflow_node.py))
  - 状态机模式的子工作流执行

### Services层已实现的功能
- **工作流编排器** ([`src/services/workflow/workflow_orchestrator.py`](src/services/workflow/workflow_orchestrator.py))
  - 业务逻辑协调
  - 业务上下文处理
  - 业务规则验证

## 分层实现方案（调整后）

### 1. Interfaces 层 - 接口定义

**文件位置**: `src/interfaces/workflow/composition.py`

**功能职责**:
- 定义工作流组合和拼接的核心接口
- 提供类型定义和抽象基类
- 定义组合策略接口

**具体接口定义**:
```python
class IWorkflowComposition(ABC):
    """工作流组合接口"""
    
    @abstractmethod
    def compose_workflows(self, workflow_configs: List[GraphConfig]) -> GraphConfig:
        """组合多个工作流配置"""
        pass

class IWorkflowStitching(ABC):
    """工作流拼接接口"""
    
    @abstractmethod
    def stitch_workflows(self, workflows: List[IWorkflow]) -> IWorkflow:
        """拼接多个工作流实例"""
        pass

class ICompositionStrategy(ABC):
    """组合策略接口"""
    
    @abstractmethod
    def execute(self, workflows: List[IWorkflow]) -> IWorkflow:
        """执行组合策略"""
        pass

class IDataMapper(ABC):
    """数据映射接口"""
    
    @abstractmethod
    def map_input_data(self, source_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """映射输入数据"""
        pass
```

### 2. Core 层 - 核心实现（扩展现有功能）

**文件位置**: `src/core/workflow/composition/`

**功能职责**（基于现有core层功能扩展）:
- 实现工作流组合和拼接的核心逻辑
- 提供组合策略引擎
- 管理工作流间的数据映射
- 处理配置加载和验证（复用现有配置系统）
- 管理工作流编排逻辑（复用现有协调器）

**具体实现模块**（在Core层实现）:

#### 2.1 组合管理器 (`WorkflowCompositionManager`)
- 统一管理工作流组合逻辑
- 支持多种组合策略
- 处理工作流间的依赖关系
- **依赖**: 复用现有的工作流协调器

#### 2.2 策略引擎 (`CompositionStrategyEngine`)
- `SequentialStrategy` - 顺序组合策略
- `ParallelStrategy` - 并行组合策略  
- `ConditionalStrategy` - 条件组合策略
- `LoopStrategy` - 循环组合策略

#### 2.3 数据映射器 (`DataMapper`)
- 工作流间数据传递
- 输入输出映射配置
- 数据转换和验证

#### 2.4 组合编排器 (`WorkflowCompositionOrchestrator`)
- 协调组合工作流的执行
- 处理错误和重试
- 管理组合工作流的生命周期
- **替代Services层的编排器功能**

### 3. Services 层 - 业务逻辑服务（简化）

**文件位置**: `src/services/workflow/composition/`

**功能职责**（仅保留业务逻辑）:
- 提供工作流组合的业务逻辑服务
- 处理组合配置的业务验证
- 管理组合工作流的业务状态

**具体服务模块**（简化实现）:

#### 3.1 组合验证服务 (`CompositionValidationService`)
- 业务规则验证
- 权限检查
- 资源限制验证

#### 3.2 组合监控服务 (`CompositionMonitoringService`)
- 性能监控
- 错误追踪
- 业务指标收集

### 4. Infrastructure 层 - 基础设施

**文件位置**: `src/infrastructure/workflow/composition/`

**功能职责**:
- 提供组合功能的持久化存储
- 实现配置加载器
- 提供监控和日志基础设施

**具体基础设施模块**:

#### 4.1 组合存储适配器 (`CompositionStorageAdapter`)
- 组合配置持久化
- 组合结果存储
- 历史记录管理

#### 4.2 配置加载器 (`CompositionConfigLoader`)
- 从文件系统加载配置
- 支持环境变量注入
- 配置热重载

## 配置系统扩展

### 配置格式设计

**文件位置**: `configs/workflow_compositions/`

```yaml
# 工作流组合配置示例
composition:
  name: "complex_analysis"
  strategy: "sequential"
  workflows:
    - workflow_id: "data_preprocessing"
      input_mapping:
        raw_data: "input.data"
      output_mapping:
        processed_data: "preprocessed.data"
    - workflow_id: "analysis"
      input_mapping:
        data: "preprocessed.data"
      output_mapping:
        result: "analysis.result"
  error_handling:
    on_failure: "rollback"
    retry_count: 3
```

## 依赖关系约束

### 严格的分层依赖

1. **Infrastructure 层**
   - 只能依赖 Interfaces 层
   - 实现组合功能的底层基础设施

2. **Core 层**
   - 可以依赖 Interfaces 层
   - 实现组合功能的核心逻辑
   - **包含配置加载和编排逻辑**（复用现有功能）

3. **Services 层**
   - 可以依赖 Interfaces 层和 Core 层
   - **仅提供业务逻辑服务**（简化实现）

## 实现优先级

### 第一阶段（高优先级）
1. Interfaces 层接口定义
2. Core 层基础实现（组合管理器、策略引擎）
3. 配置系统扩展

### 第二阶段（中优先级）
1. Core 层完整实现（数据映射器、编排器）
2. Infrastructure 层基础设施

### 第三阶段（低优先级）
1. Services 层业务逻辑服务
2. 高级组合策略

## 与现有架构的集成

### 与工作流协调器的集成
- 组合管理器通过工作流协调器创建子工作流
- 复用现有的工作流构建和执行机制

### 与配置系统的集成
- 扩展现有的配置加载器支持组合配置
- 复用环境变量注入机制

### 与状态管理系统的集成
- 使用现有的状态管理机制
- 扩展状态字段支持组合上下文

## 架构调整说明

### Services层简化
- **移除**: `CompositionLifecycleService`（功能并入Core层编排器）
- **保留**: 仅业务验证和监控功能

### Core层增强
- **新增**: 组合编排器，替代Services层的编排功能
- **复用**: 现有配置加载、验证、协调功能

### 优势
- 保持Core层的完整性和一致性
- 减少Services层的复杂性
- 提高代码复用性

## 预期效果

通过分层实现，确保：
- **职责清晰**: 每层有明确的职责边界
- **可扩展性**: 易于添加新的组合策略
- **可维护性**: 遵循依赖注入原则
- **可测试性**: 每层可独立测试
- **与现有系统无缝集成**: 充分利用现有架构

这个方案充分利用了现有的分层架构，确保新功能与现有系统无缝集成。