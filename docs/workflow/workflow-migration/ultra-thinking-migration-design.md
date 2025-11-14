# Ultra Thinking 工作流迁移设计

## 概述

Ultra Thinking 是一个多Agent并行探索引擎，通过多个Agent从不同视角分析问题并生成解决方案。本设计文档描述如何将Ultra Thinking工作流迁移到本项目的工作流架构中。

## 核心组件分析

### Ultra Thinking 原始架构
- **UltraThinkEngine**: 多Agent并行探索引擎
- **Agent配置生成**: 基于问题类型创建不同视角的Agent
- **并行执行**: 多个Agent同时分析问题
- **结果整合**: 综合各Agent的解决方案生成最终结果

### 与本项目工作流架构的映射
- **多Agent协作**: 对应本项目的工作流多节点并行执行
- **Agent配置**: 对应工作流中的节点配置和参数
- **结果整合**: 对应工作流中的聚合节点

## 迁移架构设计

### YAML 工作流定义结构

```yaml
# ultra_thinking_workflow.yaml
name: "ultra_thinking_workflow"
description: "多Agent并行探索工作流"
version: "1.0"

states:
  initial:
    type: "start"
    transitions:
      - target: "agent_configuration"
        condition: "always"

  agent_configuration:
    type: "llm_node"
    config:
      model: "gpt-4"
      temperature: 0.7
      prompt: """
      基于以下问题，分析需要哪些视角的Agent来并行探索：
      问题：{{input.problem}}
      
      请生成3-5个不同视角的Agent配置，每个Agent应该：
      1. 有明确的专业领域
      2. 有特定的分析角度
      3. 有对应的提示词模板
      """
    transitions:
      - target: "parallel_agents"
        condition: "always"

  parallel_agents:
    type: "parallel_node"
    config:
      nodes:
        - name: "technical_agent"
          type: "llm_node"
          config:
            model: "gpt-4"
            temperature: 0.8
            prompt: """
            作为技术专家，从技术实现角度分析问题：{{input.problem}}
            
            请提供：
            1. 技术可行性分析
            2. 实现方案建议
            3. 潜在技术风险
            """
        
        - name: "business_agent"
          type: "llm_node"
          config:
            model: "gpt-4"
            temperature: 0.8
            prompt: """
            作为业务专家，从商业价值角度分析问题：{{input.problem}}
            
            请提供：
            1. 商业价值评估
            2. 市场可行性分析
            3. 投资回报分析
            """
        
        - name: "user_experience_agent"
          type: "llm_node"
          config:
            model: "gpt-4"
            temperature: 0.8
            prompt: """
            作为用户体验专家，从用户角度分析问题：{{input.problem}}
            
            请提供：
            1. 用户体验影响分析
            2. 用户接受度评估
            3. 可用性改进建议
            """
    transitions:
      - target: "solution_integration"
        condition: "all_completed"

  solution_integration:
    type: "llm_node"
    config:
      model: "gpt-4"
      temperature: 0.5
      prompt: """
      基于以下多个Agent的分析结果，整合生成最终解决方案：
      
      技术专家分析：{{states.parallel_agents.technical_agent.output}}
      业务专家分析：{{states.parallel_agents.business_agent.output}}
      用户体验专家分析：{{states.parallel_agents.user_experience_agent.output}}
      
      原始问题：{{input.problem}}
      
      请生成综合解决方案，包括：
      1. 整体评估
      2. 推荐方案
      3. 实施建议
      4. 风险评估
      """
    transitions:
      - target: "validation"
        condition: "always"

  validation:
    type: "analysis_node"
    config:
      validation_rules:
        - type: "completeness"
          threshold: 0.8
        - type: "coherence"
          threshold: 0.7
      fallback_state: "solution_integration"
    transitions:
      - target: "final"
        condition: "validation_passed"

  final:
    type: "end"
    output_mapping:
      integrated_solution: "{{states.solution_integration.output}}"
      agent_analyses: "{{states.parallel_agents.output}}"
```

## 状态管理设计

### UltraThinkingState 类

```python
# src/workflow/states/ultra_thinking_state.py
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
from ..interfaces import WorkflowState

class AgentAnalysis(BaseModel):
    """单个Agent的分析结果"""
    agent_name: str
    perspective: str
    analysis: str
    confidence: float
    reasoning: str

class UltraThinkingState(WorkflowState):
    """Ultra Thinking工作流状态"""
    
    # 输入参数
    problem: str
    max_agents: int = Field(default=5, ge=1, le=10)
    
    # 中间状态
    agent_configurations: Optional[List[Dict[str, Any]]] = None
    agent_analyses: Optional[Dict[str, AgentAnalysis]] = None
    integrated_solution: Optional[str] = None
    
    # 验证结果
    validation_results: Optional[Dict[str, bool]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "problem": self.problem,
            "max_agents": self.max_agents,
            "agent_configurations": self.agent_configurations,
            "agent_analyses": {
                name: analysis.dict() 
                for name, analysis in (self.agent_analyses or {}).items()
            },
            "integrated_solution": self.integrated_solution,
            "validation_results": self.validation_results
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UltraThinkingState':
        """从字典创建实例"""
        return cls(**data)
```

## 节点实现设计

### 并行节点 (ParallelNode)

```python
# src/workflow/nodes/parallel_node.py
import asyncio
from typing import Dict, List, Any, Optional
from ..interfaces import WorkflowNode, NodeResult
from ..config_models import NodeConfig

class ParallelNode(WorkflowNode):
    """并行执行多个子节点"""
    
    def __init__(self, config: NodeConfig):
        super().__init__(config)
        self.sub_nodes = config.get("nodes", [])
    
    async def execute(self, state: Dict[str, Any]) -> NodeResult:
        """并行执行所有子节点"""
        
        # 创建执行任务
        tasks = []
        for node_config in self.sub_nodes:
            node = self.create_node(node_config)
            task = asyncio.create_task(node.execute(state))
            tasks.append((node_config["name"], task))
        
        # 等待所有任务完成
        results = {}
        completed_tasks = await asyncio.gather(
            *[task for _, task in tasks], 
            return_exceptions=True
        )
        
        # 处理结果
        for (name, _), result in zip(tasks, completed_tasks):
            if isinstance(result, Exception):
                results[name] = NodeResult(
                    success=False,
                    output=None,
                    error=str(result)
                )
            else:
                results[name] = result
        
        # 检查是否所有节点都成功执行
        all_success = all(result.success for result in results.values())
        
        return NodeResult(
            success=all_success,
            output=results,
            error=None if all_success else "部分节点执行失败"
        )
    
    def create_node(self, config: Dict[str, Any]) -> WorkflowNode:
        """根据配置创建节点实例"""
        from ..node_factory import NodeFactory
        return NodeFactory.create_node(config)
```

### Agent配置节点 (AgentConfigurationNode)

```python
# src/workflow/nodes/agent_configuration_node.py
from typing import Dict, Any
from ..interfaces import WorkflowNode, NodeResult
from ..config_models import NodeConfig

class AgentConfigurationNode(WorkflowNode):
    """生成多Agent配置的节点"""
    
    async def execute(self, state: Dict[str, Any]) -> NodeResult:
        """基于问题生成Agent配置"""
        
        problem = state.get("problem", "")
        max_agents = state.get("max_agents", 5)
        
        # 调用LLM生成Agent配置
        prompt = f"""
        问题：{problem}
        
        请生成{max_agents}个不同视角的Agent配置，每个配置包含：
        1. Agent名称
        2. 专业领域
        3. 分析角度
        4. 提示词模板
        5. 预期输出格式
        """
        
        # 这里调用实际的LLM服务
        llm_response = await self.call_llm(prompt)
        
        # 解析LLM响应，提取Agent配置
        agent_configs = self.parse_agent_configs(llm_response)
        
        # 更新状态
        state["agent_configurations"] = agent_configs
        
        return NodeResult(
            success=True,
            output=agent_configs,
            error=None
        )
    
    def parse_agent_configs(self, llm_response: str) -> List[Dict[str, Any]]:
        """解析LLM响应，提取Agent配置"""
        # 实现解析逻辑
        # 这里简化处理，实际应该根据LLM响应格式进行解析
        return [
            {
                "name": "technical_agent",
                "perspective": "技术实现",
                "prompt_template": "作为技术专家分析问题..."
            },
            {
                "name": "business_agent", 
                "perspective": "商业价值",
                "prompt_template": "作为业务专家分析问题..."
            }
        ]
```

## 配置参数映射

### Ultra Thinking 到本项目工作流的参数映射

| Ultra Thinking 参数 | 本项目工作流参数 | 说明 |
|-------------------|----------------|------|
| `max_agents` | `parallel_node.nodes` 数量 | 最大并行Agent数量 |
| `agent_perspectives` | 各子节点的提示词模板 | Agent分析视角配置 |
| `integration_strategy` | `solution_integration` 节点配置 | 结果整合策略 |
| `validation_threshold` | `validation` 节点阈值 | 验证标准 |

## 迁移注意事项

### 1. 并行执行优化
- 需要确保并行节点能够高效执行多个LLM调用
- 考虑设置最大并发数避免资源耗尽

### 2. Agent配置动态性
- 支持根据问题类型动态生成Agent配置
- 提供默认配置模板供用户自定义

### 3. 结果整合策略
- 支持多种整合策略（加权平均、优先级排序等）
- 提供可配置的整合参数

### 4. 错误处理
- 单个Agent失败不应导致整个工作流失败
- 提供降级策略和重试机制

## 测试策略

### 单元测试
- 并行节点执行测试
- Agent配置生成测试
- 结果整合逻辑测试

### 集成测试
- 完整工作流执行测试
- 多Agent协作场景测试
- 错误恢复机制测试

### 性能测试
- 并发执行性能测试
- 资源使用监控
- 响应时间优化

## 后续优化方向

### 1. 智能Agent选择
- 基于问题复杂度自动选择Agent数量
- 动态调整Agent配置

### 2. 协作机制增强
- 支持Agent间的信息交换
- 实现迭代式改进流程

### 3. 可视化监控
- 实时显示各Agent执行状态
- 提供执行过程的可视化追踪