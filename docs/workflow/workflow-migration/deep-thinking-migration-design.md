# Deep Thinking 工作流迁移设计

## 概述

Deep Thinking 是一个单Agent深度推理引擎，通过迭代验证和自改进机制确保答案质量。本设计文档描述如何将Deep Thinking工作流迁移到本项目的图工作流架构中。

## 核心组件分析

### 1. 主要类结构
- **DeepThinkEngine**: 核心引擎类，管理整个推理过程
- **DeepThinkResult**: 结果数据结构
- **DeepThinkIteration**: 单次迭代数据
- **Verification**: 验证结果

### 2. 关键流程
1. **初始化阶段**: 设置问题陈述、对话历史、知识上下文
2. **计划阶段** (可选): 生成思考计划
3. **迭代推理阶段**: 
   - 生成解决方案
   - 验证解决方案
   - 根据验证结果进行修正
4. **总结阶段**: 生成最终解决方案和总结

### 3. 核心特性
- **多模态支持**: 支持文本和图像输入
- **迭代验证**: 通过多次验证确保答案质量
- **并行验证**: 可选的并行验证机制
- **进度监控**: 实时进度事件通知

## 迁移架构设计

### 1. 工作流图结构

```yaml
# deep_thinking_workflow.yaml
name: deep_thinking_workflow
description: Deep Thinking 单Agent深度推理工作流
version: 1.0

state_schema:
  messages: List[BaseMessage]
  tool_calls: List[ToolCall]
  tool_results: List[ToolResult]
  iteration_count: int
  max_iterations: int
  current_iteration: int
  problem_statement: str
  conversation_history: List[Dict[str, Any]]
  knowledge_context: str
  current_solution: str
  verification_results: List[Dict[str, Any]]
  successful_verifications: int
  required_verifications: int
  enable_planning: bool
  enable_parallel_check: bool

nodes:
  # 初始化节点
  initialize_deep_think:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        初始化Deep Thinking工作流，准备问题陈述和上下文。
      max_tokens: 500
      temperature: 0.1

  # 计划生成节点 (可选)
  generate_thinking_plan:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        为复杂问题生成思考计划，将问题分解为可管理的部分。
      max_tokens: 1000
      temperature: 0.3

  # 核心推理节点
  deep_think_iteration:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        执行深度推理迭代，生成详细的解决方案。
        遵循深度优先、系统思考的原则。
      max_tokens: 2000
      temperature: 0.7

  # 验证节点
  verify_solution:
    type: analysis_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        作为关键评审员，验证解决方案的质量和正确性。
        识别逻辑错误、事实错误和推理缺陷。
      max_tokens: 1500
      temperature: 0.2

  # 修正节点
  correct_solution:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        根据验证反馈修正解决方案。
        保持诚实和批判性思维。
      max_tokens: 1500
      temperature: 0.5

  # 并行验证节点 (可选)
  parallel_verification:
    type: tool_node
    config:
      tool_manager: default
      max_parallel_calls: 3
      timeout: 60

  # 总结节点
  generate_final_summary:
    type: llm_node
    config:
      llm_client: openai-gpt4
      system_prompt: |
        生成最终解决方案的总结，包括关键洞察和下一步建议。
      max_tokens: 1500
      temperature: 0.3

edges:
  # 初始化流程
  - from: initialize_deep_think
    to: generate_thinking_plan
    type: conditional
    condition: needs_planning
    path_map:
      true: generate_thinking_plan
      false: deep_think_iteration

  # 推理循环
  - from: deep_think_iteration
    to: verify_solution
    type: simple

  # 验证结果处理
  - from: verify_solution
    to: correct_solution
    type: conditional
    condition: verification_failed
    path_map:
      true: correct_solution
      false: generate_final_summary

  # 修正后继续推理
  - from: correct_solution
    to: deep_think_iteration
    type: conditional
    condition: can_continue_iteration
    path_map:
      true: deep_think_iteration
      false: generate_final_summary

  # 终止条件
  - from: generate_final_summary
    to: __end__
    type: simple

entry_point: initialize_deep_think
```

### 2. 状态管理设计

```python
# 在 src/domain/workflow/states/deep_think_state.py
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class DeepThinkState(BaseModel):
    """Deep Thinking 工作流状态"""
    
    # 基础状态
    problem_statement: str
    conversation_history: List[Dict[str, Any]] = []
    knowledge_context: str = ""
    
    # 迭代状态
    current_iteration: int = 0
    max_iterations: int = 30
    current_solution: str = ""
    
    # 验证状态
    verification_results: List[Dict[str, Any]] = []
    successful_verifications: int = 0
    required_verifications: int = 3
    
    # 配置状态
    enable_planning: bool = False
    enable_parallel_check: bool = False
    model_stages: Dict[str, str] = {}
    
    # 进度状态
    status: str = "initializing"  # initializing, planning, thinking, verifying, correcting, summarizing, completed
    progress: float = 0.0
    error_message: Optional[str] = None
```

### 3. 节点实现设计

#### 3.1 深度推理节点
```python
# 在 src/infrastructure/graph/nodes/deep_think_node.py
from typing import Dict, Any
from src.infrastructure.graph.nodes.analysis_node import AnalysisNode

class DeepThinkNode(AnalysisNode):
    """深度推理节点"""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行深度推理"""
        
        # 获取当前状态
        problem_statement = state.get("problem_statement", "")
        iteration = state.get("current_iteration", 0)
        
        # 构建深度推理提示词
        prompt = self._build_deep_think_prompt(problem_statement, iteration)
        
        # 调用LLM生成解决方案
        solution = await self.llm_client.generate_text(
            model=self.config.get("model", "gpt-4"),
            prompt=prompt,
            max_tokens=self.config.get("max_tokens", 2000),
            temperature=self.config.get("temperature", 0.7)
        )
        
        # 更新状态
        state["current_solution"] = solution
        state["current_iteration"] = iteration + 1
        
        # 发送进度事件
        await self._emit_progress_event(state, "thinking", {
            "iteration": iteration + 1,
            "solution_preview": solution[:200] + "..." if len(solution) > 200 else solution
        })
        
        return state
    
    def _build_deep_think_prompt(self, problem: str, iteration: int) -> str:
        """构建深度推理提示词"""
        return f"""
### Deep Thinking 迭代 {iteration + 1} ###

**问题陈述:**
{problem}

**深度推理要求:**
- 进行系统性的深度分析
- 考虑多种角度和替代方案
- 验证每个推理步骤的逻辑
- 识别潜在的假设和限制
- 提供详细的技术细节和解释

请生成详细的解决方案。
"""
```

#### 3.2 验证节点
```python
# 在 src/infrastructure/graph/nodes/verification_node.py
from typing import Dict, Any
from src.infrastructure.graph.nodes.analysis_node import AnalysisNode

class VerificationNode(AnalysisNode):
    """验证节点"""
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """执行验证"""
        
        solution = state.get("current_solution", "")
        problem = state.get("problem_statement", "")
        
        # 构建验证提示词
        prompt = self._build_verification_prompt(problem, solution)
        
        # 调用LLM进行验证
        verification_result = await self.llm_client.generate_text(
            model=self.config.get("verification_model", "gpt-4"),
            prompt=prompt,
            max_tokens=self.config.get("max_tokens", 1500),
            temperature=self.config.get("temperature", 0.2)
        )
        
        # 解析验证结果
        verification_data = self._parse_verification_result(verification_result)
        
        # 更新状态
        state["verification_results"].append(verification_data)
        
        if verification_data.get("passed", False):
            state["successful_verifications"] += 1
        
        # 发送进度事件
        await self._emit_progress_event(state, "verifying", {
            "verification_result": verification_data,
            "successful_count": state["successful_verifications"]
        })
        
        return state
    
    def _build_verification_prompt(self, problem: str, solution: str) -> str:
        """构建验证提示词"""
        return f"""
### 关键评审员验证 ###

**问题:**
{problem}

**待验证的解决方案:**
{solution}

**验证要求:**
- 识别逻辑错误、事实错误和推理缺陷
- 区分关键缺陷和次要问题
- 提供具体的改进建议
- 最终给出通过/不通过的判断
"""
```

## 配置参数映射

| Deep Thinking 参数 | 本项目工作流参数 | 说明 |
|------------------|-----------------|------|
| `max_iterations` | `max_iterations` | 最大迭代次数 |
| `required_successful_verifications` | `required_verifications` | 所需成功验证次数 |
| `enable_planning` | `enable_planning` | 是否启用计划阶段 |
| `enable_parallel_check` | `enable_parallel_check` | 是否启用并行验证 |
| `model_stages` | `model_stages` | 不同阶段使用的模型 |
| `llm_params` | 节点配置参数 | LLM调用参数 |

## 迁移注意事项

### 1. 多模态支持
- 本项目需要扩展对多模态输入的支持
- 需要修改状态模型以支持图像和文本混合内容

### 2. 进度事件系统
- 需要实现与Deep Thinking兼容的进度事件机制
- 支持实时进度更新和状态监控

### 3. 验证机制
- 保持原有的严格验证标准
- 支持并行验证和串行验证两种模式

### 4. 错误处理
- 实现完善的错误恢复机制
- 支持在验证失败时的自动修正

## 测试策略

1. **单元测试**: 测试每个节点的功能
2. **集成测试**: 测试完整的工作流执行
3. **性能测试**: 验证大规模迭代的性能
4. **质量测试**: 验证输出质量与原Deep Thinking一致

## 后续优化

1. **缓存机制**: 实现中间结果的缓存
2. **并行优化**: 优化并行验证的性能
3. **自适应迭代**: 根据问题复杂度动态调整迭代次数