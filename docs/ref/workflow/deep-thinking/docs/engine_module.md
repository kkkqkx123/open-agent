# DeepAPI Engine 模块文档

## 概述

DeepAPI Engine 模块是 DeepAPI 项目的核心推理引擎，提供两种不同层次的思考模式：
- **Deep Think Engine**: 单 Agent 深度推理引擎
- **Ultra Think Engine**: 多 Agent 并行探索引擎

## 模块结构

```
engine/
├── __init__.py          # 模块导出文件
├── deep_think.py        # 单 Agent 深度推理引擎
├── ultra_think.py       # 多 Agent 并行探索引擎
└── prompts.py           # 提示词管理模块
```

## 1. Deep Think Engine

### 1.1 核心功能

Deep Think Engine 是一个单 Agent 深度推理引擎，通过迭代验证和修正机制确保推理质量。

**主要特性：**
- 支持多模态内容输入（文本、图像等）
- 完整的对话历史支持
- 知识库上下文集成
- 可配置的验证机制
- 并行验证支持
- 进度事件回调

### 1.2 核心类：DeepThinkEngine

#### 构造函数参数

```python
class DeepThinkEngine:
    def __init__(
        self,
        client: OpenAIClient,           # OpenAI 客户端
        model: str,                     # 基础模型
        problem_statement: MessageContent,  # 问题陈述（多模态）
        conversation_history: List[Dict[str, Any]] = None,  # 对话历史
        other_prompts: List[str] = None,    # 额外提示词
        knowledge_context: str = None,      # 知识库上下文
        max_iterations: int = 30,            # 最大迭代次数
        required_successful_verifications: int = 3,  # 所需验证通过次数
        max_errors_before_give_up: int = 10, # 最大错误次数
        model_stages: Dict[str, str] = None, # 阶段模型配置
        on_progress: Optional[Callable[[ProgressEvent], None]] = None,  # 进度回调
        enable_planning: bool = False,       # 启用计划阶段
        enable_parallel_check: bool = False, # 启用并行验证
        llm_params: Optional[Dict[str, Any]] = None,  # LLM 参数
    )
```

#### 核心方法

**`run()`** - 执行深度思考流程

**执行流程：**
1. **初始化阶段**：发送初始化事件
2. **计划阶段**（可选）：生成思考计划
3. **初始探索阶段**：
   - 第一次思考
   - 自我改进
   - 验证解决方案
4. **主循环**：
   - 验证当前解决方案
   - 如果验证失败：修正解决方案
   - 如果验证通过：增加通过计数
   - 达到所需验证通过次数后生成最终摘要

### 1.3 验证机制

#### 串行验证 (`_verify_solution`)
- 单个 LLM 调用验证解决方案
- 检查是否存在关键错误或主要论证漏洞

#### 并行验证 (`_verify_solution_parallel`)
- 同时启动多个验证 LLM 调用
- 所有验证都必须通过才算成功
- 提供更严格的验证标准

## 2. Ultra Think Engine

### 2.1 核心功能

Ultra Think Engine 是多 Agent 并行探索引擎，通过多个 Agent 从不同角度分析问题，然后综合结果。

**主要特性：**
- 多 Agent 并行执行
- 自动生成分析计划
- Agent 配置自动生成
- 结果综合机制
- Agent 状态监控

### 2.2 核心类：UltraThinkEngine

#### 构造函数参数

```python
class UltraThinkEngine:
    def __init__(
        self,
        client: OpenAIClient,           # OpenAI 客户端
        model: str,                     # 基础模型
        problem_statement: MessageContent,  # 问题陈述
        conversation_history: List[Dict[str, Any]] = None,  # 对话历史
        other_prompts: List[str] = None,    # 额外提示词
        knowledge_context: str = None,      # 知识库上下文
        max_iterations: int = 30,            # 最大迭代次数
        required_successful_verifications: int = 3,  # 所需验证通过次数
        max_errors_before_give_up: int = 10, # 最大错误次数
        num_agents: Optional[int] = None,    # Agent 数量限制
        parallel_run_agent: int = 3,        # 并行运行 Agent 数量
        model_stages: Dict[str, str] = None, # 阶段模型配置
        on_progress: Optional[Callable[[ProgressEvent], None]] = None,  # 进度回调
        on_agent_update: Optional[Callable[[str, Dict[str, Any]], None]] = None,  # Agent 更新回调
        enable_parallel_check: bool = False, # 启用并行验证
        llm_params: Optional[Dict[str, Any]] = None,  # LLM 参数
    )
```

#### 核心方法

**`run()`** - 执行超思考流程

**执行流程：**
1. **计划生成阶段**：生成多角度分析计划
2. **Agent 配置生成**：基于计划生成 Agent 配置
3. **并行 Agent 执行**：
   - 使用信号量控制并发数量
   - 每个 Agent 运行独立的 Deep Think 引擎
   - 实时监控 Agent 状态
4. **结果综合阶段**：
   - 使用 Deep Think 引擎综合所有 Agent 结果
   - 分析不同方法的优缺点
   - 生成统一解决方案
5. **最终摘要生成**：创建用户友好的最终响应

### 2.3 Agent 管理

**Agent 配置格式：**
```json
[
  {
    "agentId": "agent_01",
    "approach": "方法名称",
    "specificPrompt": "具体指令"
  }
]
```

**Agent 执行流程：**
- 每个 Agent 使用独立的 Deep Think 引擎
- Agent 特定提示词作为额外上下文
- 实时进度和状态更新

## 3. Prompts 模块

### 3.1 核心提示词

**Deep Think 核心提示词：**
- `DEEP_THINK_INITIAL_PROMPT`: 核心原则和响应结构
- `SELF_IMPROVEMENT_PROMPT`: 自我改进提示词
- `VERIFICATION_SYSTEM_PROMPT`: 验证系统提示词
- `CORRECTION_PROMPT`: 修正提示词

**Ultra Think 提示词：**
- `ULTRA_THINK_PLAN_PROMPT`: 多角度分析计划生成
- `GENERATE_AGENT_PROMPTS_PROMPT`: Agent 配置生成
- `SYNTHESIZE_RESULTS_PROMPT`: 结果综合
- `FINAL_SUMMARY_PROMPT`: 最终摘要

### 3.2 提示词构建函数

**`build_verification_prompt(problem, solution)`** - 构建验证提示词
**`build_initial_thinking_prompt(problem, other_prompts, knowledge_context)`** - 构建初始思考提示词
**`build_final_summary_prompt(problem, analysis)`** - 构建最终摘要提示词
**`build_thinking_plan_prompt(problem)`** - 构建思考计划提示词

## 4. 核心设计模式

### 4.1 多阶段模型配置

引擎支持为不同阶段配置不同的模型：
```python
model_stages = {
    "initial": "gpt-4",           # 初始思考阶段
    "improvement": "gpt-4",       # 自我改进阶段
    "verification": "gpt-4",      # 验证阶段
    "correction": "gpt-4",        # 修正阶段
    "summary": "gpt-4",           # 摘要阶段
    "planning": "gpt-4",          # 计划阶段
    "agent_config": "gpt-4",      # Agent 配置生成
    "agent_thinking": "gpt-4",    # Agent 思考阶段
    "synthesis": "gpt-4"          # 综合阶段
}
```

### 4.2 事件驱动架构

引擎通过 `ProgressEvent` 系统提供实时反馈：
- `init`: 初始化事件
- `progress`: 进度更新
- `thinking`: 思考阶段
- `verification`: 验证阶段
- `correction`: 修正阶段
- `success`: 成功完成
- `failure`: 失败事件

### 4.3 多模态支持

引擎支持 `MessageContent` 类型，可以处理：
- 纯文本
- 多模态内容（文本 + 图像）
- 结构化消息历史

## 5. 使用示例

### 5.1 Deep Think Engine 使用

```python
from engine.deep_think import DeepThinkEngine
from utils.openai_client import OpenAIClient

# 创建客户端
client = OpenAIClient(api_key="your-api-key")

# 创建引擎
engine = DeepThinkEngine(
    client=client,
    model="gpt-4",
    problem_statement="如何优化网站性能？",
    max_iterations=20,
    required_successful_verifications=3,
    enable_parallel_check=True
)

# 运行引擎
result = await engine.run()
print(result.final_solution)
```

### 5.2 Ultra Think Engine 使用

```python
from engine.ultra_think import UltraThinkEngine
from utils.openai_client import OpenAIClient

def on_progress(event):
    print(f"Progress: {event.type} - {event.data}")

def on_agent_update(agent_id, data):
    print(f"Agent {agent_id}: {data}")

# 创建引擎
engine = UltraThinkEngine(
    client=client,
    model="gpt-4",
    problem_statement="如何设计一个可扩展的微服务架构？",
    on_progress=on_progress,
    on_agent_update=on_agent_update,
    parallel_run_agent=3
)

# 运行引擎
result = await engine.run()
print(result.summary)
```

## 6. 性能优化

### 6.1 并行处理

- Ultra Think Engine 支持并行运行多个 Agent
- Deep Think Engine 支持并行验证
- 使用信号量控制并发数量

### 6.2 缓存策略

- 对话历史缓存
- 验证结果缓存
- 模型响应缓存

### 6.3 资源管理

- 可配置的最大迭代次数
- 错误计数限制
- 超时处理机制

## 7. 扩展性

### 7.1 自定义提示词

通过 `other_prompts` 参数添加自定义提示词

### 7.2 模型适配

支持多种 OpenAI 兼容模型

### 7.3 插件系统

可通过继承基类实现自定义引擎

## 总结

DeepAPI Engine 模块提供了一个强大的推理引擎框架，支持从简单问题到复杂问题的多层次分析。通过深度思考和超思考两种模式，可以满足不同复杂度的推理需求。