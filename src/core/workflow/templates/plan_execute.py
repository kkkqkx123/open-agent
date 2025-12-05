"""Plan-Execute工作流模板

实现Plan-Execute模式的工作流模板：先制定计划，然后执行计划。
"""

from typing import Dict, Any, List
from src.services.logger.injection import get_logger

from .base import BaseWorkflowTemplate
from src.interfaces.workflow.core import IWorkflow
from ..value_objects import StepType, TransitionType

logger = get_logger(__name__)


class PlanExecuteWorkflowTemplate(BaseWorkflowTemplate):
    """Plan-Execute工作流模板
    
    实现Plan-Execute模式：先制定计划，然后按计划执行
    """
    
    def __init__(self) -> None:
        """初始化Plan-Execute模板"""
        super().__init__()
        self._name = "plan_execute"
        self._description = "Plan-Execute工作流模式，先制定计划，然后按计划执行"
        self._category = "planning"
        self._version = "1.0"
        self._parameters = [
            {
                "name": "llm_client",
                "type": "string",
                "description": "LLM客户端标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "max_steps",
                "type": "integer",
                "description": "最大执行步骤数",
                "required": False,
                "default": 10,
                "min": 1,
                "max": 50
            },
            {
                "name": "planning_prompt",
                "type": "string",
                "description": "计划制定节点的系统提示词",
                "required": False,
                "default": "请分析用户需求并制定详细的执行计划"
            },
            {
                "name": "execution_prompt",
                "type": "string",
                "description": "步骤执行节点的系统提示词",
                "required": False,
                "default": "请按照计划执行当前步骤"
            },
            {
                "name": "review_prompt",
                "type": "string",
                "description": "结果审查节点的系统提示词",
                "required": False,
                "default": "请审查执行结果并决定下一步"
            },
            {
                "name": "planning_tools",
                "type": "array",
                "description": "计划制定阶段可用工具列表",
                "required": False,
                "default": [],
                "items": {
                    "type": "string"
                }
            },
            {
                "name": "execution_tools",
                "type": "array",
                "description": "执行阶段可用工具列表",
                "required": False,
                "default": [],
                "items": {
                    "type": "string"
                }
            },
            {
                "name": "step_timeout",
                "type": "integer",
                "description": "单个步骤超时时间（秒）",
                "required": False,
                "default": 60,
                "min": 10,
                "max": 300
            },
            {
                "name": "review_criteria",
                "type": "array",
                "description": "审查标准列表",
                "required": False,
                "default": ["completeness", "accuracy", "efficiency"],
                "items": {
                    "type": "string"
                }
            },
            {
                "name": "name_suffix",
                "type": "string",
                "description": "工作流名称后缀",
                "required": False,
                "default": "workflow"
            },
            {
                "name": "description",
                "type": "string",
                "description": "工作流描述",
                "required": False,
                "default": "默认Plan-Execute模式"
            }
        ]
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建Plan-Execute工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        max_steps = config.get("max_steps", 10)
        planning_prompt = config.get("planning_prompt", "请分析用户需求并制定详细的执行计划")
        execution_prompt = config.get("execution_prompt", "请按照计划执行当前步骤")
        review_prompt = config.get("review_prompt", "请审查执行结果并决定下一步")
        planning_tools = config.get("planning_tools", [])
        execution_tools = config.get("execution_tools", [])
        step_timeout = config.get("step_timeout", 60)
        review_criteria = config.get("review_criteria", ["completeness", "accuracy", "efficiency"])
        
        # 创建计划制定节点
        planning_step = self._create_step(
            step_id="planning",
            step_name="planning",
            step_type=StepType.ANALYSIS,
            description="分析需求并制定执行计划",
            config={
                "agent_config": {
                    "agent_type": "react",
                    "name": "planner",
                    "description": "计划制定节点",
                    "llm": llm_client,
                    "system_prompt": planning_prompt,
                    "max_iterations": 3,
                    "tools": planning_tools,
                    "output_format": "plan"
                }
            }
        )
        workflow.add_step(planning_step)
        
        # 创建步骤执行节点
        execute_step = self._create_step(
            step_id="execute_step",
            step_name="execute_step",
            step_type=StepType.EXECUTION,
            description="执行计划中的当前步骤",
            config={
                "agent_config": {
                    "agent_type": "react",
                    "name": "executor",
                    "description": "步骤执行节点",
                    "llm": llm_client,
                    "system_prompt": execution_prompt,
                    "max_iterations": 3,
                    "tools": execution_tools,
                    "step_timeout": step_timeout
                }
            }
        )
        workflow.add_step(execute_step)
        
        # 创建结果审查节点
        review_step = self._create_step(
            step_id="review",
            step_name="review",
            step_type=StepType.DECISION,
            description="审查执行结果并决定下一步",
            config={
                "agent_config": {
                    "agent_type": "react",
                    "name": "reviewer",
                    "description": "结果审查节点",
                    "llm": llm_client,
                    "system_prompt": review_prompt,
                    "max_iterations": 2,
                    "tools": [],
                    "review_criteria": review_criteria
                }
            }
        )
        workflow.add_step(review_step)
        
        # 创建最终总结节点
        finalize_step = self._create_step(
            step_id="finalize",
            step_name="finalize",
            step_type=StepType.ANALYSIS,
            description="生成最终总结和结果",
            config={
                "agent_config": {
                    "agent_type": "react",
                    "name": "finalizer",
                    "description": "最终总结节点",
                    "llm": llm_client,
                    "system_prompt": "请总结整个执行过程并提供最终结果",
                    "max_iterations": 1,
                    "tools": []
                }
            }
        )
        workflow.add_step(finalize_step)
        
        # 创建转换
        # 计划制定 -> 步骤执行
        planning_to_execute = self._create_transition(
            transition_id="planning_to_execute",
            from_step="planning",
            to_step="execute_step",
            transition_type=TransitionType.SIMPLE,
            description="计划制定完成后开始执行"
        )
        workflow.add_transition(planning_to_execute)
        
        # 步骤执行 -> 结果审查
        execute_to_review = self._create_transition(
            transition_id="execute_to_review",
            from_step="execute_step",
            to_step="review",
            transition_type=TransitionType.SIMPLE,
            description="步骤执行完成后进行审查"
        )
        workflow.add_transition(execute_to_review)
        
        # 结果审查 -> 步骤执行（条件：继续执行）
        review_to_execute = self._create_transition(
            transition_id="review_to_execute",
            from_step="review",
            to_step="execute_step",
            transition_type=TransitionType.CONDITIONAL,
            condition="continue_execution",
            description="如果需要继续执行则执行下一步"
        )
        workflow.add_transition(review_to_execute)
        
        # 结果审查 -> 最终总结（条件：执行完成）
        review_to_finalize = self._create_transition(
            transition_id="review_to_finalize",
            from_step="review",
            to_step="finalize",
            transition_type=TransitionType.CONDITIONAL,
            condition="execution_completed",
            description="如果执行完成则进行最终总结"
        )
        workflow.add_transition(review_to_finalize)
        
        # 设置入口点
        workflow.set_entry_point("planning")
        
        logger.info(f"构建Plan-Execute工作流结构完成: {workflow.name}")


class CollaborativePlanExecuteTemplate(PlanExecuteWorkflowTemplate):
    """协作式Plan-Execute模板
    
    支持多个Agent协作的Plan-Execute模式
    """
    
    def __init__(self) -> None:
        """初始化协作式Plan-Execute模板"""
        super().__init__()
        self._name = "collaborative_plan_execute"
        self._description = "协作式Plan-Execute工作流模式，支持多个Agent协作执行"
        self._category = "planning"
        self._version = "2.0"
        
        # 添加协作参数
        collaboration_params = [
            {
                "name": "collaborators",
                "type": "array",
                "description": "协作者配置列表",
                "required": True,
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "agent_type": {"type": "string"},
                        "description": {"type": "string"},
                        "llm": {"type": "string"},
                        "system_prompt": {"type": "string"},
                        "max_iterations": {"type": "integer"},
                        "tools": {"type": "array"},
                        "role": {"type": "string"}
                    }
                }
            }
        ]
        
        self._parameters.extend(collaboration_params)
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建协作式Plan-Execute工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取协作配置
        collaborators = config.get("collaborators", [])
        if not collaborators:
            raise ValueError("协作式模板必须配置collaborators参数")
        
        # 调用基类方法创建基础结构
        super()._build_workflow_structure(workflow, config)
        
        # 添加协作节点
        for i, collaborator in enumerate(collaborators):
            node_name = f"collaborator_{i}"
            collaborator_step = self._create_step(
                step_id=node_name,
                step_name=node_name,
                step_type=StepType.EXECUTION,
                description=f"协作节点 {i}: {collaborator.get('description', '')}",
                config={
                    "agent_config": {
                        "agent_type": collaborator.get("agent_type", "react"),
                        "name": collaborator.get("name", f"collaborator_{i}"),
                        "description": collaborator.get("description", f"协作节点 {i}"),
                        "llm": collaborator.get("llm", config.get("llm_client", "default")),
                        "system_prompt": collaborator.get("system_prompt", "你是协作执行者"),
                        "max_iterations": collaborator.get("max_iterations", 3),
                        "tools": collaborator.get("tools", []),
                        "role": collaborator.get("role", "executor")
                    }
                }
            )
            workflow.add_step(collaborator_step)
            
            # 添加协作转换
            if i == 0:
                # 第一个协作者连接到执行步骤
                execute_to_collaborator = self._create_transition(
                    transition_id=f"execute_to_collaborator_{i}",
                    from_step="execute_step",
                    to_step=node_name,
                    transition_type=TransitionType.CONDITIONAL,
                    condition=f"needs_collaborator_{i}",
                    description=f"如果需要协作者{i}则调用"
                )
                workflow.add_transition(execute_to_collaborator)
            else:
                # 其他协作者连接到前一个协作者
                prev_node = f"collaborator_{i-1}"
                collaborator_to_collaborator = self._create_transition(
                    transition_id=f"collaborator_{i-1}_to_collaborator_{i}",
                    from_step=prev_node,
                    to_step=node_name,
                    transition_type=TransitionType.CONDITIONAL,
                    condition=f"needs_collaborator_{i}",
                    description=f"如果需要协作者{i}则调用"
                )
                workflow.add_transition(collaborator_to_collaborator)
            
            # 最后一个协作者连接到审查节点
            if i == len(collaborators) - 1:
                collaborator_to_review = self._create_transition(
                    transition_id=f"collaborator_{i}_to_review",
                    from_step=node_name,
                    to_step="review",
                    transition_type=TransitionType.SIMPLE,
                    description="协作完成后进行审查"
                )
                workflow.add_transition(collaborator_to_review)
        
        logger.info(f"构建协作式Plan-Execute工作流结构完成: {workflow.name}")