"""状态模板管理

管理状态模板和自动状态初始化。
"""

from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from src.interfaces.dependency_injection import get_logger
from copy import deepcopy

from .workflow_config import WorkflowConfig
from typing import Any

logger = get_logger(__name__)


@dataclass
class StateTemplate:
    """状态模板"""
    name: str
    description: str
    fields: Dict[str, Any] = field(default_factory=dict)
    inherits_from: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def merge_with_parent(self, parent_template: 'StateTemplate') -> 'StateTemplate':
        """与父模板合并
        
        Args:
            parent_template: 父模板
            
        Returns:
            StateTemplate: 合并后的模板
        """
        merged_fields = deepcopy(parent_template.fields)
        merged_fields.update(self.fields)
        
        return StateTemplate(
            name=self.name,
            description=self.description,
            fields=merged_fields,
            inherits_from=self.inherits_from,
            metadata={**parent_template.metadata, **self.metadata}
        )


class StateTemplateManager:
    """状态模板管理器
    
    管理状态模板和自动状态初始化。
    """
    
    def __init__(self):
        """初始化状态模板管理器"""
        self._templates: Dict[str, StateTemplate] = {}
        self._register_rest_templates()
    
    def register_template(self, template: StateTemplate) -> None:
        """注册状态模板
        
        Args:
            template: 状态模板
        """
        if not template.name or not template.name.strip():
            raise ValueError("模板名称不能为空")
        
        self._templates[template.name] = template
        logger.debug(f"注册状态模板: {template.name}")
    
    def get_template(self, name: str) -> Optional[StateTemplate]:
        """获取状态模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[StateTemplate]: 状态模板，如果不存在返回None
        """
        return self._templates.get(name)
    
    def create_state_from_template(
        self, 
        template_name: str, 
        overrides: Optional[Dict[str, Any]] = None,
        workflow_config: Optional[WorkflowConfig] = None
    ) -> Dict[str, Any]:
        """从模板创建状态
        
        Args:
            template_name: 模板名称
            overrides: 覆盖字段
            workflow_config: 工作流配置
            
        Returns:
            Dict[str, Any]: 创建的状态
        """
        template = self.get_template(template_name)
        if not template:
            raise ValueError(f"状态模板 '{template_name}' 不存在")
        
        # 解析继承关系
        resolved_template = self._resolve_template_inheritance(template)
        
        # 创建状态
        state = deepcopy(resolved_template.fields)
        
        # 应用覆盖
        if overrides:
            state.update(overrides)
        
        # 应用工作流配置中的状态覆盖
        if workflow_config and hasattr(workflow_config, 'state_overrides'):
            state.update(getattr(workflow_config, 'state_overrides', {}))
        
        # 处理状态字段的默认值和类型转换
        state = self._process_state_fields(state, workflow_config)
        
        logger.debug(f"从模板 '{template_name}' 创建状态完成")
        return state
    
    def create_state_from_config(
        self, 
        config: WorkflowConfig, 
        initial_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """从配置创建状态
        
        Args:
            config: 工作流配置
            initial_data: 初始数据
            
        Returns:
            Dict[str, Any]: 创建的状态
        """
        # 检查是否指定了状态模板
        template_name = getattr(config, 'state_template', None)
        
        if template_name:
            # 使用模板创建状态
            state = self.create_state_from_template(template_name, initial_data, config)
        else:
            # 从状态模式创建状态
            state_schema = getattr(config, 'state_schema', None)
            if state_schema:
                state = self._create_state_from_schema(state_schema, initial_data)
            else:
                state = initial_data or {}
        
        # 应用配置中的状态覆盖
        state_overrides = getattr(config, 'state_overrides', {}) or getattr(config, 'additional_config', {})
        if state_overrides:
            state.update(state_overrides)
        
        return state
    
    def list_templates(self) -> List[str]:
        """列出所有模板
        
        Returns:
            List[str]: 模板名称列表
        """
        return list(self._templates.keys())
    
    def get_template_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板信息
        """
        template = self.get_template(name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "inherits_from": template.inherits_from,
            "field_count": len(template.fields),
            "fields": list(template.fields.keys()),
            "metadata": template.metadata
        }
    
    def _register_rest_templates(self) -> None:
        """注册内置模板"""
        
        # 基础状态模板
        base_template = StateTemplate(
            name="base_state",
            description="基础状态模板",
            fields={
                "messages": [],
                "tool_calls": [],
                "tool_results": [],
                "iteration_count": 0,
                "max_iterations": 10,
                "errors": [],
                "metadata": {}
            }
        )
        self.register_template(base_template)
        
        # 工作流状态模板
        workflow_template = StateTemplate(
            name="workflow_state",
            description="工作流状态模板",
            fields={
                "workflow_messages": [],
                "workflow_tool_calls": [],
                "workflow_tool_results": [],
                "workflow_iteration_count": 0,
                "workflow_max_iterations": 10,
                "task_history": [],
                "workflow_errors": [],
                "context": {},
                "current_task": ""
            }
        )
        self.register_template(workflow_template)
        
        # Plan-Execute 状态模板
        plan_execute_template = StateTemplate(
            name="plan_execute_state",
            description="Plan-Execute 状态模板",
            fields={
                "workflow_messages": [],
                "workflow_tool_calls": [],
                "workflow_tool_results": [],
                "workflow_iteration_count": 0,
                "workflow_max_iterations": 10,
                "task_history": [],
                "workflow_errors": [],
                "context": {
                    "current_plan": [],
                    "current_step_index": 0,
                    "plan_completed": False,
                    "needs_review": False
                },
                "current_task": ""
            }
        )
        self.register_template(plan_execute_template)
        
        # ReAct 状态模板
        react_template = StateTemplate(
            name="react_state",
            description="ReAct 状态模板",
            fields={
                "messages": [],
                "tool_calls": [],
                "tool_results": [],
                "iteration_count": 0,
                "max_iterations": 10,
                "thought": "",
                "action": "",
                "observation": "",
                "steps": []
            }
        )
        self.register_template(react_template)
        
        logger.debug("内置状态模板注册完成")
    
    def _resolve_template_inheritance(self, template: StateTemplate) -> StateTemplate:
        """解析模板继承关系
        
        Args:
            template: 模板
            
        Returns:
            StateTemplate: 解析后的模板
        """
        if not template.inherits_from:
            return template
        
        parent_template = self.get_template(template.inherits_from)
        if not parent_template:
            logger.warning(f"父模板 '{template.inherits_from}' 不存在，跳过继承")
            return template
        
        # 递归解析父模板
        resolved_parent = self._resolve_template_inheritance(parent_template)
        
        # 合并模板
        return template.merge_with_parent(resolved_parent)
    
    def _create_state_from_schema(self, state_schema, initial_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """从状态模式创建状态
        
        Args:
            state_schema: 状态模式
            initial_data: 初始数据
            
        Returns:
            Dict[str, Any]: 创建的状态
        """
        state = {}
        
        # 根据状态模式创建字段
        if hasattr(state_schema, 'fields'):
            for field_name, field_config in state_schema.fields.items():
                if hasattr(field_config, 'default'):
                    state[field_name] = field_config.default
                else:
                    # 根据类型设置默认值
                    state[field_name] = self._get_default_value_for_type(field_config.type)
        
        # 应用初始数据
        if initial_data:
            state.update(initial_data)
        
        return state
    
    def _get_default_value_for_type(self, type_str: str) -> Any:
        """根据类型获取默认值
        
        Args:
            type_str: 类型字符串
            
        Returns:
            Any: 默认值
        """
        type_defaults = {
            "str": "",
            "int": 0,
            "float": 0.0,
            "bool": False,
            "list": [],
            "dict": {},
            "List[str]": [],
            "List[int]": [],
            "List[dict]": [],
            "Dict[str, Any]": {}
        }
        
        return type_defaults.get(type_str, None)
    
    def _process_state_fields(self, state: Dict[str, Any], workflow_config: Optional[WorkflowConfig] = None) -> Dict[str, Any]:
        """处理状态字段
        
        Args:
            state: 状态字典
            workflow_config: 工作流配置
            
        Returns:
            Dict[str, Any]: 处理后的状态
        """
        if not workflow_config:
            return state
        
        state_schema = getattr(workflow_config, 'state_schema', None)
        if not state_schema:
            return state
        
        # 处理每个字段
        for field_name, field_config in state_schema.fields.items():
            if field_name in state:
                # 类型转换
                state[field_name] = self._convert_field_type(state[field_name], field_config)
            else:
                # 设置默认值
                if hasattr(field_config, 'default') and field_config.default is not None:
                    state[field_name] = field_config.default
                else:
                    state[field_name] = self._get_default_value_for_type(field_config.type)
        
        return state
    
    def _convert_field_type(self, value: Any, field_config: Any) -> Any:
        """转换字段类型
        
        Args:
            value: 字段值
            field_config: 字段配置
            
        Returns:
            Any: 转换后的值
        """
        if value is None:
            return value
        
        target_type = field_config.type
        
        try:
            if target_type == "str":
                return str(value)
            elif target_type == "int":
                return int(value)
            elif target_type == "float":
                return float(value)
            elif target_type == "bool":
                return bool(value)
            elif target_type in ["list", "List[str]", "List[int]", "List[dict]"]:
                if not isinstance(value, list):
                    return [value]
                return value
            elif target_type in ["dict", "Dict[str, Any]"]:
                if not isinstance(value, dict):
                    return {"value": value}
                return value
            else:
                return value
        except (ValueError, TypeError) as e:
            logger.warning(f"字段类型转换失败: {value} -> {target_type}, 错误: {e}")
            return value
    
    def validate_template(self, template: StateTemplate) -> List[str]:
        """验证模板
        
        Args:
            template: 模板
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        if not template.name or not template.name.strip():
            errors.append("模板名称不能为空")
        
        if not template.description or not template.description.strip():
            errors.append("模板描述不能为空")
        
        if template.inherits_from and template.inherits_from not in self._templates:
            errors.append(f"父模板 '{template.inherits_from}' 不存在")
        
        return errors
    
    def export_template(self, name: str) -> Optional[Dict[str, Any]]:
        """导出模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[Dict[str, Any]]: 模板数据
        """
        template = self.get_template(name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "description": template.description,
            "fields": template.fields,
            "inherits_from": template.inherits_from,
            "metadata": template.metadata
        }
    
    def import_template(self, template_data: Dict[str, Any]) -> bool:
        """导入模板
        
        Args:
            template_data: 模板数据
            
        Returns:
            bool: 是否导入成功
        """
        try:
            template = StateTemplate(
                name=template_data["name"],
                description=template_data["description"],
                fields=template_data.get("fields", {}),
                inherits_from=template_data.get("inherits_from"),
                metadata=template_data.get("metadata", {})
            )
            
            # 验证模板
            errors = self.validate_template(template)
            if errors:
                logger.error(f"模板验证失败: {errors}")
                return False
            
            self.register_template(template)
            return True
            
        except Exception as e:
            logger.error(f"导入模板失败: {e}")
            return False


# 全局状态模板管理器实例
_global_template_manager: Optional[StateTemplateManager] = None


def get_global_template_manager() -> StateTemplateManager:
    """获取全局状态模板管理器
    
    Returns:
        StateTemplateManager: 全局状态模板管理器
    """
    global _global_template_manager
    if _global_template_manager is None:
        _global_template_manager = StateTemplateManager()
    return _global_template_manager


def create_state_from_template(template_name: str, overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """从模板创建状态（便捷函数）
    
    Args:
        template_name: 模板名称
        overrides: 覆盖字段
        
    Returns:
        Dict[str, Any]: 创建的状态
    """
    manager = get_global_template_manager()
    return manager.create_state_from_template(template_name, overrides)