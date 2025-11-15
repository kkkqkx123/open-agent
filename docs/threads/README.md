# Thread层文档

## 概述

Thread层是项目的核心执行层，负责工作流的执行、状态管理和与LangGraph框架的交互。本目录包含了Thread层的完整文档，帮助开发者理解和使用Thread层的各项功能。

## 文档结构

### 核心文档

1. **[Thread层与工作流集成指南](thread-workflow-integration-guide.md)**
   - Thread层的架构定位和职责
   - 工作流配置与Thread层的集成方式
   - Session层如何协调和管理Thread
   - 核心功能实现详解
   - 高级功能（分支、快照、协作）
   - LangGraph适配器的作用
   - 整体协作模式
   - 实际使用指南和示例

2. **[Thread层快速参考](thread-quick-reference.md)**
   - 核心API速查表
   - 常用使用模式
   - 错误处理模式
   - 性能优化技巧
   - 监控与调试方法
   - 最佳实践
   - 常见问题解答

3. **[Thread层优化指南](thread-optimization-guide.md)**
   - 性能优化策略
   - 可靠性增强方案
   - 可扩展性改进
   - 安全性强化措施
   - 监控与观测
   - 实施建议

## 快速开始

### 基本使用

```python
from src.infrastructure.di.thread_session_di_config import create_development_stack
from src.application.sessions.manager import UserRequest
from pathlib import Path
from datetime import datetime

# 创建组件栈
components = create_development_stack(Path("./storage"))
session_manager = components["session_manager"]

# 创建用户会话
user_request = UserRequest(
    request_id="req_001",
    user_id="user_123",
    content="分析数据并生成报告",
    timestamp=datetime.now()
)

session_id = await session_manager.create_session(user_request)

# 创建并执行工作流Thread
thread_configs = [{
    "name": "data_analysis",
    "config_path": "configs/workflows/plan_execute_workflow.yaml",
    "initial_state": {"messages": [{"role": "user", "content": "分析任务"}]}
}]

thread_ids = await session_manager.coordinate_threads(session_id, thread_configs)
result = await session_manager.execute_workflow_in_session(session_id, "data_analysis")
```

### 流式执行

```python
# 流式执行工作流，实时获取中间状态
async for state in session_manager.stream_workflow_in_session(
    session_id, 
    "data_analysis",
    config={"temperature": 0.7}
):
    print(f"当前步骤: {state.get('current_step', 'unknown')}")
    print(f"进度: {state.get('iteration_count', 0)}")
```

### Thread分支

```python
# 创建Thread分支
branch_thread_id = await thread_manager.fork_thread(
    original_thread_id,
    checkpoint_id="latest",
    branch_name="experimental_branch",
    metadata={"experiment": "try_different_temperature"}
)
```

## 架构概览

```
用户层 (User Layer)
    ↓
表现层 (Presentation Layer) - API、TUI、CLI
    ↓
应用层 (Application Layer) - Session管理器、协作管理器
    ↓
领域层 (Domain Layer) - Thread管理器、Checkpoint管理器
    ↓
基础设施层 (Infrastructure Layer) - LangGraph适配器、存储
```

## 核心概念

### Thread
- **定义**：工作流的执行实例
- **生命周期**：创建 → 执行 → 完成/错误
- **状态管理**：通过Checkpoint机制实现状态持久化

### Session
- **定义**：用户交互的上下文
- **职责**：协调多个Thread，追踪用户交互
- **生命周期**：创建 → 活跃 → 结束

### Checkpoint
- **定义**：Thread状态的快照
- **作用**：状态保存、恢复、回滚
- **存储**：支持内存和SQLite存储

### Collaboration
- **定义**：多Thread协作机制
- **功能**：状态共享、同步、权限管理
- **应用场景**：复杂工作流、并行处理

## 主要特性

### 1. 工作流执行
- 同步和异步执行
- 流式执行支持
- 错误处理和恢复

### 2. 状态管理
- Checkpoint机制
- 状态历史查询
- 状态回滚功能

### 3. 高级功能
- Thread分支
- 状态快照
- 多Thread协作

### 4. 性能优化
- 图缓存
- 批量操作
- 资源池管理

### 5. 可扩展性
- 插件化架构
- 分布式支持
- 动态加载

## 最佳实践

### 1. 资源管理
- 使用完Thread后清理缓存
- 定期清理旧的Thread和checkpoint
- 监控内存使用情况

### 2. 错误处理
- 捕获并记录所有异常
- 提供有意义的错误消息
- 实现适当的错误恢复机制

### 3. 性能优化
- 使用批量操作减少API调用
- 合理设置缓存大小
- 根据使用场景选择存储后端

### 4. 安全考虑
- 验证所有输入参数
- 实现适当的权限控制
- 记录关键操作日志

## 常见问题

### Q: Thread和Session的区别是什么？
A: Thread是工作流的执行实例，负责具体的执行逻辑；Session是用户交互的上下文，负责协调多个Thread和追踪用户交互。

### Q: 如何处理长时间运行的工作流？
A: 使用流式执行模式，定期检查状态，并实现适当的超时机制。

### Q: 如何比较不同配置的执行结果？
A: 使用Thread分支功能，从同一checkpoint创建多个分支，使用不同配置执行后比较结果。

### Q: 如何优化大量Thread的性能？
A: 使用批量操作、合理设置缓存、定期清理不需要的Thread，考虑使用分布式架构。

### Q: 如何调试工作流执行问题？
A: 查看Thread历史、检查交互记录、使用日志记录、分析checkpoint状态。

## 扩展阅读

- [LangGraph官方文档](https://langchain-ai.github.io/langgraph/)
- [项目整体架构文档](../architecture/)
- [配置系统文档](../config/)
- [工作流设计指南](../workflow/)

## 贡献指南

如果您想为Thread层贡献代码或文档，请遵循以下步骤：

1. 阅读项目贡献指南
2. 熟悉Thread层的架构和API
3. 编写测试用例
4. 提交Pull Request
5. 等待代码审查

## 版本历史

- **v1.0**：基础Thread管理功能
- **v1.1**：添加分支和快照功能
- **v1.2**：实现多Thread协作
- **v1.3**：性能优化和插件化架构
- **v1.4**：分布式支持和安全性增强

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue：[项目Issues页面]
- 邮件联系：[维护者邮箱]
- 技术讨论：[项目讨论区]

---

*最后更新时间：2024年11月*