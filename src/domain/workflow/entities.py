"""业务工作流领域实体

定义真正的业务工作流实体，与LangGraph技术实现分离。
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from enum import Enum
from datetime import datetime
import uuid

from .value_objects import WorkflowStep, WorkflowTransition, WorkflowRule, StepType
from .exceptions import WorkflowValidationError

if TYPE_CHECKING:
    from src.core.workflow.config.config import GraphConfig


class WorkflowStatus(Enum):
    """工作流状态"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class BusinessWorkflow:
    """业务工作流领域实体
    
    这是真正的业务工作流定义，不依赖具体的技术实现。
    """
    
    # 基本属性
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0"
    status: WorkflowStatus = WorkflowStatus.DRAFT
    
    # 业务逻辑
    steps: List[WorkflowStep] = field(default_factory=list)
    transitions: List[WorkflowTransition] = field(default_factory=list)
    rules: List[WorkflowRule] = field(default_factory=list)
    
    # 元数据
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    created_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    # 配置
    config: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """初始化后处理"""
        if not self.name:
            raise WorkflowValidationError("工作流名称不能为空")
        
        # 确保步骤ID唯一
        step_ids = [step.id for step in self.steps]
        if len(step_ids) != len(set(step_ids)):
            raise WorkflowValidationError("步骤ID必须唯一")
    
    def add_step(self, step: WorkflowStep) -> None:
        """添加步骤"""
        # 检查步骤ID是否已存在
        if any(s.id == step.id for s in self.steps):
            raise WorkflowValidationError(f"步骤ID '{step.id}' 已存在")
        
        self.steps.append(step)
        self.updated_at = datetime.now()
    
    def remove_step(self, step_id: str) -> None:
        """移除步骤"""
        self.steps = [s for s in self.steps if s.id != step_id]
        # 同时移除相关的转换
        self.transitions = [
            t for t in self.transitions 
            if t.from_step != step_id and t.to_step != step_id
        ]
        self.updated_at = datetime.now()
    
    def add_transition(self, transition: WorkflowTransition) -> None:
        """添加转换"""
        # 验证步骤存在
        step_ids = [s.id for s in self.steps]
        if transition.from_step not in step_ids:
            raise WorkflowValidationError(f"起始步骤 '{transition.from_step}' 不存在")
        if transition.to_step not in step_ids:
            raise WorkflowValidationError(f"目标步骤 '{transition.to_step}' 不存在")
        
        self.transitions.append(transition)
        self.updated_at = datetime.now()
    
    def add_rule(self, rule: WorkflowRule) -> None:
        """添加规则"""
        self.rules.append(rule)
        self.updated_at = datetime.now()
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """根据ID获取步骤"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_entry_steps(self) -> List[WorkflowStep]:
        """获取入口步骤（没有前置转换的步骤）"""
        from_step_ids = {t.from_step for t in self.transitions}
        return [s for s in self.steps if s.id not in from_step_ids]
    
    def get_exit_steps(self) -> List[WorkflowStep]:
        """获取出口步骤（没有后置转换的步骤）"""
        to_step_ids = {t.to_step for t in self.transitions}
        return [s for s in self.steps if s.id not in to_step_ids]
    
    def validate(self) -> List[str]:
        """验证工作流定义"""
        errors = []
        
        # 基本验证
        if not self.name:
            errors.append("工作流名称不能为空")
        if not self.description:
            errors.append("工作流描述不能为空")
        
        # 步骤验证
        if not self.steps:
            errors.append("工作流必须包含至少一个步骤")
        
        # 入口步骤验证
        entry_steps = self.get_entry_steps()
        if len(entry_steps) == 0:
            errors.append("工作流必须至少有一个入口步骤")
        elif len(entry_steps) > 1:
            errors.append("工作流只能有一个入口步骤")
        
        # 转换验证
        step_ids = {s.id for s in self.steps}
        for transition in self.transitions:
            if transition.from_step not in step_ids:
                errors.append(f"转换的起始步骤 '{transition.from_step}' 不存在")
            if transition.to_step not in step_ids:
                errors.append(f"转换的目标步骤 '{transition.to_step}' 不存在")
            
            # 条件转换验证
            if transition.condition and not transition.condition.strip():
                errors.append(f"转换 '{transition.from_step}' -> '{transition.to_step}' 的条件不能为空")
        
        # 规则验证
        for rule in self.rules:
            rule_errors = rule.validate()
            errors.extend([f"规则 '{rule.name}': {error}" for error in rule_errors])
        
        return errors
    
    def to_graph_config(self) -> "GraphConfig":
        """转换为LangGraph配置
        
        这是业务工作流到技术实现的转换层。
        """
        from src.core.workflow.config.config import (
            GraphConfig, GraphStateConfig, StateFieldConfig,
            NodeConfig, EdgeConfig, EdgeType
        )
        
        # 创建状态配置
        state_fields = {
            "messages": StateFieldConfig(
                name="messages",
                type="List[BaseMessage]",
                reducer="operator.add",
                description="消息历史"
            ),
            "current_step": StateFieldConfig(
                name="current_step",
                type="str",
                description="当前步骤"
            ),
            "workflow_id": StateFieldConfig(
                name="workflow_id",
                type="str",
                default=self.id,
                description="工作流ID"
            ),
            "iteration_count": StateFieldConfig(
                name="iteration_count",
                type="int",
                reducer="operator.add",
                default=0,
                description="迭代计数"
            ),
            "complete": StateFieldConfig(
                name="complete",
                type="bool",
                default=False,
                description="完成标志"
            )
        }
        
        state_schema = GraphStateConfig(
            name=f"{self.name}State",
            fields=state_fields
        )
        
        # 创建节点配置
        nodes = {}
        for step in self.steps:
            nodes[step.id] = NodeConfig(
                name=step.id,
                function_name=self._map_step_type_to_function(step.type),
                config=step.config,
                description=step.description
            )
        
        # 创建边配置
        edges = []
        for transition in self.transitions:
            edge_type = EdgeType.CONDITIONAL if transition.condition else EdgeType.SIMPLE
            edges.append(EdgeConfig(
                from_node=transition.from_step,
                to_node=transition.to_step,
                type=edge_type,
                condition=transition.condition,
                description=transition.description
            ))
        
        # 确定入口点
        entry_steps = self.get_entry_steps()
        entry_point = entry_steps[0].id if entry_steps else None
        
        return GraphConfig(
            name=self.name,
            description=self.description,
            version=self.version,
            state_schema=state_schema,
            nodes=nodes,
            edges=edges,
            entry_point=entry_point,
            additional_config=self.config
        )
    
    def _map_step_type_to_function(self, step_type: StepType) -> str:
        """将步骤类型映射到函数名"""
        mapping = {
            StepType.ANALYSIS: "analysis_node",
            StepType.EXECUTION: "tool_node",
            StepType.DECISION: "condition_node",
            StepType.WAITING: "wait_node",
            StepType.NOTIFICATION: "notification_node",
            StepType.START: "start_node",
            StepType.END: "end_node"
        }
        return mapping.get(step_type, "default_node")
    
    def update_status(self, status: WorkflowStatus) -> None:
        """更新状态"""
        self.status = status
        self.updated_at = datetime.now()
    
    def clone(self, new_name: Optional[str] = None) -> "BusinessWorkflow":
        """克隆工作流"""
        import copy
        
        cloned = copy.deepcopy(self)
        cloned.id = str(uuid.uuid4())
        cloned.name = new_name or f"{self.name}_副本"
        cloned.status = WorkflowStatus.DRAFT
        cloned.created_at = datetime.now()
        cloned.updated_at = datetime.now()
        
        return cloned


@dataclass
class WorkflowExecution:
    """工作流执行实例"""
    
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.DRAFT
    
    # 执行状态
    current_step: Optional[str] = None
    execution_context: Dict[str, Any] = field(default_factory=dict)
    
    # 时间信息
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_updated: datetime = field(default_factory=datetime.now)
    
    # 执行历史
    step_history: List[Dict[str, Any]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    
    def start_execution(self, entry_step: str) -> None:
        """开始执行"""
        self.status = WorkflowStatus.ACTIVE
        self.current_step = entry_step
        self.started_at = datetime.now()
        self.last_updated = datetime.now()
        
        self.step_history.append({
            "step": entry_step,
            "action": "start",
            "timestamp": datetime.now().isoformat()
        })
    
    def complete_step(self, step: str, result: Dict[str, Any]) -> None:
        """完成步骤"""
        self.step_history.append({
            "step": step,
            "action": "complete",
            "result": result,
            "timestamp": datetime.now().isoformat()
        })
        self.last_updated = datetime.now()
    
    def add_error(self, error: str) -> None:
        """添加错误"""
        self.errors.append(error)
        self.status = WorkflowStatus.ERROR
        self.last_updated = datetime.now()
    
    def complete_execution(self) -> None:
        """完成执行"""
        self.status = WorkflowStatus.COMPLETED
        self.completed_at = datetime.now()
        self.last_updated = datetime.now()
        self.current_step = None