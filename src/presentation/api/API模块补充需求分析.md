# API模块补充需求分析

## 分析目标
分析当前`src\presentation\api`模块需要补充哪些内容，让整个系统的各个功能都可以通过API调用。

## 当前API覆盖情况

### 已实现的路由模块

#### 1. 会话管理 (sessions.py)
- **端点数**: 8个
- **功能覆盖**: 会话的CRUD操作、历史记录、状态管理、统计信息
- **主要端点**: 
  - GET /sessions - 获取会话列表
  - GET /sessions/{session_id} - 获取会话详情
  - POST /sessions - 创建会话
  - PUT /sessions/{session_id} - 更新会话
  - DELETE /sessions/{session_id} - 删除会话
  - GET /sessions/{session_id}/history - 获取会话历史
  - POST /sessions/{session_id}/state - 保存会话状态
  - POST /sessions/{session_id}/restore - 恢复会话

#### 2. 工作流管理 (workflows.py)
- **端点数**: 9个（更新功能待实现）
- **功能覆盖**: 工作流的CRUD、运行、可视化、搜索
- **主要端点**:
  - GET /workflows - 获取工作流列表
  - GET /workflows/{workflow_id} - 获取工作流详情
  - POST /workflows - 创建工作流
  - POST /workflows/{workflow_id}/load - 加载工作流
  - POST /workflows/{workflow_id}/run - 运行工作流
  - POST /workflows/{workflow_id}/run/stream - 流式运行工作流
  - GET /workflows/{workflow_id}/visualize - 工作流可视化
  - POST /workflows/{workflow_id}/unload - 卸载工作流
  - PUT /workflows/{workflow_id} - 更新工作流（待实现）

#### 3. 线程管理 (threads.py)
- **端点数**: 5个
- **功能覆盖**: 线程分支、回滚、快照、历史记录
- **主要端点**:
  - POST /threads/{thread_id}/branch - 创建线程分支
  - POST /threads/{thread_id}/rollback - 回滚线程到检查点
  - POST /threads/{thread_id}/snapshot - 创建线程快照
  - GET /threads/{thread_id}/history - 获取线程历史记录
  - GET /threads - 获取线程列表

#### 4. 其他已实现的模块
- **analytics.py** - 分析功能
- **history.py** - 历史记录管理
- **websocket.py** - WebSocket实时通信

## 缺失的API路由模块

基于domain层核心接口分析，以下模块尚未提供API接口：

### 1. 状态管理API（高优先级）
**相关接口**: `IStateManager`, `IEnhancedStateManager`, `IStateCollaborationManager`

**建议端点**:
```
GET    /states                    - 获取状态列表
GET    /states/{state_id}        - 获取状态详情
POST   /states                    - 创建状态
PUT    /states/{state_id}        - 更新状态
DELETE /states/{state_id}        - 删除状态
POST   /states/{state_id}/validate - 验证状态
POST   /states/{state_id}/snapshot - 创建状态快照
GET    /states/{state_id}/snapshots - 获取状态快照列表
POST   /states/{state_id}/restore  - 恢复状态快照
GET    /states/{state_id}/history  - 获取状态历史记录
```

### 2. 工具系统API（高优先级）
**相关接口**: `ITool`, `IToolRegistry`, `IToolExecutor`, `IToolFactory`

**建议端点**:
```
GET    /tools                     - 获取工具列表
GET    /tools/{tool_name}         - 获取工具详情
POST   /tools/{tool_name}/execute - 执行工具
GET    /tools/{tool_name}/schema  - 获取工具参数模式
POST   /tools/{tool_name}/validate - 验证工具参数
GET    /tools/categories          - 获取工具分类
POST   /tools/register            - 注册新工具
DELETE /tools/{tool_name}         - 注销工具
```

### 3. 提示词管理API（中优先级）
**相关接口**: `IPromptRegistry`, `IPromptLoader`, `IPromptInjector`

**建议端点**:
```
GET    /prompts                   - 获取提示词列表
GET    /prompts/{prompt_id}       - 获取提示词详情
GET    /prompts/categories        - 获取提示词分类
POST   /prompts/{prompt_id}/load  - 加载提示词
POST   /prompts/register          - 注册提示词
PUT    /prompts/{prompt_id}      - 更新提示词
DELETE /prompts/{prompt_id}        - 删除提示词
POST   /prompts/validate         - 验证提示词注册表
```

### 4. 检查点管理API（中优先级）
**相关接口**: `ICheckpointStore`, `ICheckpointManager`, `ICheckpointPolicy`

**建议端点**:
```
GET    /checkpoints               - 获取检查点列表
GET    /checkpoints/{checkpoint_id} - 获取检查点详情
POST   /checkpoints               - 创建检查点
PUT    /checkpoints/{checkpoint_id} - 更新检查点
DELETE /checkpoints/{checkpoint_id} - 删除检查点
POST   /checkpoints/{checkpoint_id}/restore - 恢复检查点
POST   /checkpoints/{checkpoint_id}/copy    - 复制检查点
POST   /checkpoints/import      - 导入检查点
POST   /checkpoints/export      - 导出检查点
```

### 5. 配置管理API（低优先级）
**相关接口**: `IConfigSystem`, `IConfigLoader`, `IConfigValidator`

**建议端点**:
```
GET    /config                    - 获取当前配置
GET    /config/{config_type}      - 获取特定类型配置
POST   /config/reload            - 重新加载配置
PUT    /config/{config_type}      - 更新配置
POST   /config/validate          - 验证配置
GET    /config/templates         - 获取配置模板
```

### 6. 系统管理API（低优先级）
**功能**: 系统监控、健康检查、服务状态、性能指标

**建议端点**:
```
GET    /system/health            - 系统健康检查
GET    /system/metrics           - 系统性能指标
GET    /system/services          - 服务状态列表
GET    /system/logs              - 系统日志
POST   /system/logs/clear        - 清理日志
GET    /system/info              - 系统信息
```

## 实施建议

### 第一阶段（高优先级）
1. **状态管理API** - 核心功能，支持工作流和会话的状态操作
2. **工具系统API** - 支持工具的执行和管理

### 第二阶段（中优先级）
3. **提示词管理API** - 支持提示词的加载和管理
4. **检查点管理API** - 支持状态的保存和恢复

### 第三阶段（低优先级）
5. **配置管理API** - 支持配置的动态管理
6. **系统管理API** - 支持系统监控和运维

## 技术实现要点

### 服务层设计
- 每个API模块对应一个服务类（如`StateService`, `ToolService`）
- 服务类通过依赖注入获取domain层接口实例
- 统一异常处理和响应格式

### 数据模型设计
- 基于domain层的模型创建请求/响应模型
- 使用Pydantic进行数据验证
- 保持与domain层模型的兼容性

### 依赖注入
- 在`main.py`中注册新的路由模块
- 在`services`目录下实现对应的服务类
- 在`models`目录下定义请求响应模型

### 异常处理
- 统一使用`HTTPException`包装业务异常
- 区分客户端错误（4xx）和服务器错误（5xx）
- 提供详细的错误信息和调试信息

## 后续步骤

1. 按优先级逐个实现缺失的API模块
2. 为每个模块编写对应的测试用例
3. 更新API文档和OpenAPI规范
4. 实现权限控制和访问限制
5. 添加API版本控制支持