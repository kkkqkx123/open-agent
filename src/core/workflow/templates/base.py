"""工作流模板基类

提供工作流模板的基础实现。
"""

from abc import ABC
from typing import Dict, Any, List, Optional, cast
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.templates import IWorkflowTemplate
from src.interfaces.workflow.core import IWorkflow
from ..entities import Workflow
from ..value_objects import WorkflowStep, WorkflowTransition, WorkflowRule, StepType, TransitionType

logger = get_logger(__name__)


class BaseWorkflowTemplate(IWorkflowTemplate, ABC):
    """工作流模板基类"""
    
    def __init__(self) -> None:
        """初始化模板"""
        self._name = ""
        self._description = ""
        self._category = ""
        self._version = "1.0"
        self._parameters: List[Dict[str, Any]] = []
    
    @property
    def name(self) -> str:
        """模板名称"""
        return self._name
    
    @property
    def description(self) -> str:
        """模板描述"""
        return self._description
    
    @property
    def category(self) -> str:
        """模板类别"""
        return self._category
    
    @property
    def version(self) -> str:
        """模板版本"""
        return self._version
    
    def create_workflow(self, name: str, description: str, config: Dict[str, Any]) -> IWorkflow:
        """从模板创建工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
            config: 配置参数
            
        Returns:
            IWorkflow: 工作流实例
        """
        # 验证参数
        errors = self.validate_parameters(config)
        if errors:
            raise ValueError(f"参数验证失败: {'; '.join(errors)}")
        
        # 创建工作流
        workflow_instance = Workflow(
            workflow_id=f"{self.name}_{name}",
            name=name,
            description=description
        )
        
        # 设置元数据
        workflow_instance.metadata = {
            "template": self.name,
            "template_version": self.version,
            "config": config
        }
        
        # 转换为接口类型
        workflow: IWorkflow = cast(IWorkflow, workflow_instance)
        
        # 构建工作流结构
        self._build_workflow_structure(workflow, config)
        
        logger.info(f"从模板 '{self.name}' 创建工作流: {name}")
        return workflow
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 基础实现，子类应该重写此方法
        pass
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义
        
        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        return self._parameters
    
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 参数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证必需参数
        for param in self._parameters:
            if param.get("required", False):
                param_name = param["name"]
                if param_name not in config:
                    errors.append(f"必需参数 '{param_name}' 缺失")
        
        # 验证参数类型
        for param_name, value in config.items():
            param_def = self._get_parameter_definition(param_name)
            if param_def:
                errors.extend(self._validate_parameter_type(param_name, value, param_def))
        
        return errors
    
    def _get_parameter_definition(self, param_name: str) -> Optional[Dict[str, Any]]:
        """获取参数定义
        
        Args:
            param_name: 参数名称
            
        Returns:
            Optional[Dict[str, Any]]: 参数定义
        """
        for param in self._parameters:
            if param["name"] == param_name:
                return param
        return None
    
    def _validate_parameter_type(self, param_name: str, value: Any, param_def: Dict[str, Any]) -> List[str]:
        """验证参数类型
        
        Args:
            param_name: 参数名称
            value: 参数值
            param_def: 参数定义
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        param_type = param_def.get("type", "string")
        
        # 类型验证
        if param_type == "string" and not isinstance(value, str):
            errors.append(f"参数 '{param_name}' 必须是字符串类型")
        elif param_type == "integer" and not isinstance(value, int):
            errors.append(f"参数 '{param_name}' 必须是整数类型")
        elif param_type == "number" and not isinstance(value, (int, float)):
            errors.append(f"参数 '{param_name}' 必须是数字类型")
        elif param_type == "boolean" and not isinstance(value, bool):
            errors.append(f"参数 '{param_name}' 必须是布尔类型")
        elif param_type == "array" and not isinstance(value, list):
            errors.append(f"参数 '{param_name}' 必须是数组类型")
        elif param_type == "object" and not isinstance(value, dict):
            errors.append(f"参数 '{param_name}' 必须是对象类型")
        
        # 范围验证
        if param_type in ["integer", "number"]:
            if "min" in param_def and value < param_def["min"]:
                errors.append(f"参数 '{param_name}' 必须大于等于 {param_def['min']}")
            if "max" in param_def and value > param_def["max"]:
                errors.append(f"参数 '{param_name}' 必须小于等于 {param_def['max']}")
        
        # 数组元素验证
        if param_type == "array" and "items" in param_def:
            item_type = param_def["items"].get("type", "string")
            if isinstance(value, list):
                for item in value:
                    if item_type == "string" and not isinstance(item, str):
                        errors.append(f"参数 '{param_name}' 数组中的所有元素必须是字符串类型")
                        break
                    elif item_type == "integer" and not isinstance(item, int):
                        errors.append(f"参数 '{param_name}' 数组中的所有元素必须是整数类型")
                        break
        
        return errors
    
    def _create_step(self, step_id: str, step_name: str, step_type: StepType, 
                    description: str, config: Dict[str, Any]) -> WorkflowStep:
        """创建工作流步骤
        
        Args:
            step_id: 步骤ID
            step_name: 步骤名称
            step_type: 步骤类型
            description: 步骤描述
            config: 步骤配置
            
        Returns:
            WorkflowStep: 工作流步骤
        """
        return WorkflowStep(
            id=step_id,
            name=step_name,
            type=step_type,
            description=description,
            config=config
        )
    
    def _create_transition(self, transition_id: str, from_step: str, to_step: str,
                          transition_type: TransitionType = TransitionType.SIMPLE,
                          condition: Optional[str] = None, 
                          description: str = "") -> WorkflowTransition:
        """创建工作流转换
        
        Args:
            transition_id: 转换ID
            from_step: 起始步骤
            to_step: 目标步骤
            transition_type: 转换类型
            condition: 条件表达式
            description: 转换描述
            
        Returns:
            WorkflowTransition: 工作流转换
        """
        return WorkflowTransition(
            id=transition_id,
            from_step=from_step,
            to_step=to_step,
            type=transition_type,
            condition=condition,
            description=description
        )
    
    def _create_rule(self, rule_id: str, rule_name: str, rule_type: str,
                    target_field: str, description: str = "") -> WorkflowRule:
        """创建工作流规则
        
        Args:
            rule_id: 规则ID
            rule_name: 规则名称
            rule_type: 规则类型
            target_field: 目标字段
            description: 规则描述
            
        Returns:
            WorkflowRule: 工作流规则
        """
        from ..value_objects import RuleType
        return WorkflowRule(
            id=rule_id,
            name=rule_name,
            type=RuleType(rule_type),
            target_field=target_field,
            description=description
        )