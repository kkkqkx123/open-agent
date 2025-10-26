# Workflow与Graph职责划分及改进方案

## 1. 正确的架构层级

### 1.1 五层架构设计
```
Session层 (Presentation)     → 会话管理、状态持久化
    ↓
Workflow层 (Application)    → 工作流管理、业务逻辑编排
    ↓
Agent层 (Domain)           → Agent核心逻辑、策略
    ↓
Tool层 (Infrastructure)     → 工具适配、外部系统集成
    ↓
LLM层 (Infrastructure)     → 模型配置、实例管理
```

## 2. Workflow与Graph的正确关系

### 2.1 Workflow作为高级抽象
- **一个Workflow可以包含多个LangGraph图**
- **Workflow负责业务逻辑编排，Graph负责具体执行**

## 3. 具体职责划分

### 3.1 Workflow层职责
- **工作流生命周期管理**：加载、创建、执行、监控
- **多Agent协作协调**：定义Agent间的交互流程
- **状态管理**：维护工作流执行状态

### 3.2 Graph层职责  
- **LangGraph图构建**：StateGraph创建和编译
- **节点执行管理**：协调图中各节点的执行顺序

### 3.3 正确的依赖流向
```
WorkflowManager (应用层)
    ↓ (通过适配器模式)
GraphBuilder (基础设施层)
    ↓ (构建)
StateGraph (LangGraph核心)
```

## 4. 当前架构的核心问题

### 4.1 概念混淆
- 将Workflow与Graph视为同级实体
- 未能理解Workflow可以包含多个Graph

## 5. 改进方案详细设计

### 5.1 架构重构

#### 5.1.1 明确Workflow作为容器
- Workflow管理业务逻辑和多个Agent的协作

### 5.2 技术实现优化

#### 5.2.1 支持多图工作流
```yaml
workflow:
  name: "编程助手工作流"
  graphs:
    - planning_graph: "任务规划图"
    - code_generation_graph: "代码生成图"
    - review_graph: "代码审查图"
```

### 5.3 配置系统设计

#### 5.3.1 工作流配置结构
```yaml
workflow:
  architecture: "supervisor"
  nodes:
    - supervisor: {type: "agent", agent: "main_supervisor"}
```

## 6. 实施建议

### 6.1 短期改进
- 重新定义Workflow与Graph的关系
- 实现真正的多图支持

### 6.2 长期规划
- 建立可扩展的工作流引擎
- 支持复杂的工作流模式

## 7. 总结

正确的架构理解应该是：
- **Workflow是业务逻辑的容器**
- **Graph是执行流程的实现**
- **一个Workflow可以协调多个Graph的执行**