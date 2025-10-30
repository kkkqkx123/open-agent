# 等待节点使用指南

## 概述

等待节点（WaitNode）是专门为工作流中需要暂停执行等待外部干预的场景设计的节点。它替代了原来使用LLM节点模拟等待的不合理设计，提供了真正的暂停功能和灵活的超时处理策略。

## 核心特性

### 1. 真正的等待机制
- 工作流执行会真正暂停，不会消耗LLM资源
- 支持外部输入触发恢复执行
- 维护等待状态和上下文信息

### 2. 灵活的超时处理策略
- **继续等待（continue_waiting）**：超时后给出提示，继续等待
- **缓存并退出（cache_and_exit）**：保存状态，退出任务，可稍后恢复
- **LLM继续（llm_continue）**：超时后自动让LLM继续之前的任务

### 3. 丰富的配置选项
- 可配置超时时间和策略
- 支持自定义等待消息
- 灵活的路由规则配置
- 自动恢复键名配置

## 配置示例

### 基本配置

```yaml
human_review_wait:
  type: wait_node
  config:
    timeout_enabled: true
    timeout_seconds: 300  # 5分钟超时
    timeout_strategy: "continue_waiting"
    wait_message: "等待人工审核中..."
    auto_resume_key: "human_review_result"
```

### 完整配置示例

```yaml
human_review_wait:
  type: wait_node
  config:
    # 超时配置
    timeout_enabled: true
    timeout_seconds: 300
    timeout_strategy: "continue_waiting"
    
    # 消息配置
    wait_message: "等待人工审核中...审核员将审查当前处理结果并提供反馈。"
    
    # 恢复配置
    auto_resume_key: "human_review_result"
    routing_rules:
      "approved": "final_answer"
      "rejected": "analyze"
      "modify": "modify_result"
    default_next_node: "final_answer"
    
    # LLM继续策略配置
    continue_node: "analyze"
```

## 超时处理策略详解

### 1. 继续等待策略（continue_waiting）

**适用场景**：需要持续等待，不希望因超时而丢失等待状态

**行为**：
- 超时后添加提示消息
- 重置等待计时器
- 继续保持等待状态

**配置**：
```yaml
timeout_strategy: "continue_waiting"
```

### 2. 缓存并退出策略（cache_and_exit）

**适用场景**：长时间等待，需要释放资源但保留进度

**行为**：
- 缓存当前状态到存储
- 添加退出消息
- 退出工作流执行
- 可通过外部接口恢复

**配置**：
```yaml
timeout_strategy: "cache_and_exit"
```

**恢复缓存状态**：
```python
# 获取缓存的状态
cached_state = wait_node.get_cached_state(wait_id)

# 恢复执行
state = AgentState.from_dict(cached_state)
```

### 3. LLM继续策略（llm_continue）

**适用场景**：超时后希望系统自动继续处理

**行为**：
- 清除等待状态
- 设置自动继续标志
- 跳转到指定节点继续执行

**配置**：
```yaml
timeout_strategy: "llm_continue"
continue_node: "analyze"  # 超时后跳转的节点
```

## 外部输入恢复

### 设置外部输入

```python
# 在Agent状态中设置外部输入
state.human_review_result = "approved"
state.human_review_comments = "审核通过，可以继续"
```

### 支持的输入类型

等待节点会检查 `auto_resume_key` 指定的状态属性，当该属性有值时自动恢复执行。

### 路由规则

```yaml
routing_rules:
  "approved": "final_answer"    # 批准 -> 最终答案
  "rejected": "analyze"         # 拒绝 -> 重新分析
  "modify": "modify_result"     # 修改 -> 修改结果
```

## 状态管理

### 等待状态属性

```python
class WaitState:
    start_time: float           # 等待开始时间
    is_waiting: bool           # 是否正在等待
    timeout_occurred: bool     # 是否已超时
    wait_message: str          # 等待消息
    cached_state: dict         # 缓存的状态数据
```

### Agent状态属性

```python
# 等待节点会设置以下属性
state.is_waiting = True               # 等待标志
state.wait_start_time = timestamp     # 等待开始时间
state.auto_continue = True            # 自动继续标志（LLM继续策略）
state.continue_reason = "timeout"     # 继续原因
```

## 使用示例

### 人工审核工作流

```yaml
name: human_review_workflow
description: 使用等待节点的人工审核工作流

nodes:
  analyze:
    type: analysis_node
    config:
      # ... 分析节点配置

  human_review_wait:
    type: wait_node
    config:
      timeout_enabled: true
      timeout_seconds: 600  # 10分钟
      timeout_strategy: "cache_and_exit"
      wait_message: "等待人工审核..."
      auto_resume_key: "review_result"
      routing_rules:
        "approved": "final_answer"
        "rejected": "revise"

  final_answer:
    type: llm_node
    config:
      # ... 最终答案节点配置

edges:
  - from: analyze
    to: human_review_wait
  - from: human_review_wait
    to: final_answer
```

### 代码中使用

```python
from src.infrastructure.graph.nodes.wait_node import WaitNode

# 创建等待节点
wait_node = WaitNode()

# 执行等待
result = wait_node.execute(state, config)

# 检查是否需要等待
if result.metadata["is_waiting"]:
    wait_id = result.metadata["wait_id"]
    print(f"工作流已暂停，等待ID: {wait_id}")
    
    # 外部设置恢复条件
    state.review_result = "approved"
    
    # 恢复执行
    result = wait_node.execute(state, config)
```

## 最佳实践

### 1. 合理设置超时时间
- 短期等待：30-300秒
- 中期等待：300-1800秒（30分钟）
- 长期等待：建议使用缓存并退出策略

### 2. 选择合适的超时策略
- **人工审核**：继续等待或缓存并退出
- **系统干预**：LLM继续策略
- **长时间任务**：缓存并退出策略

### 3. 状态管理
- 定期清理过期的等待状态
- 合理使用缓存功能
- 监控等待节点的资源使用

### 4. 错误处理
- 验证配置参数
- 处理超时异常
- 记录等待和恢复事件

## 与原LLM节点的对比

| 特性 | LLM节点模拟等待 | 专门的等待节点 |
|------|----------------|----------------|
| 资源消耗 | 消耗LLM调用 | 无额外资源消耗 |
| 等待真实性 | 模拟等待 | 真正暂停执行 |
| 超时处理 | 依赖提示词 | 专门的超时机制 |
| 状态管理 | 简单标记 | 完整状态管理 |
| 恢复机制 | 依赖LLM理解 | 外部输入触发 |
| 缓存功能 | 无 | 支持状态缓存 |
| 配置灵活性 | 有限 | 丰富的配置选项 |

## 总结

等待节点提供了工作流中暂停执行的标准化解决方案，解决了原来使用LLM节点模拟等待的设计缺陷。通过灵活的超时处理策略和丰富的配置选项，可以满足各种等待场景的需求，提供更好的用户体验和系统性能。