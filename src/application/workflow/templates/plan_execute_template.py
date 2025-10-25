"""Plan-Execute工作流模板

实现Plan-Execute模式的工作流模板：先制定计划，然后执行计划。
"""

from typing import Dict, Any, List
from src.domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from ..interfaces import IWorkflowTemplate


class PlanExecuteWorkflowTemplate(IWorkflowTemplate):
    """Plan-Execute工作流模板
    
    实现Plan-Execute模式：先制定计划，然后按计划执行
    """
    
    @property
    def name(self) -> str:
        """模板名称"""
        return "plan_execute"
    
    @property
    def description(self) -> str:
        """模板描述"""
        return "Plan-Execute工作流模式，先制定计划，然后按计划执行"
    
    def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
        """创建Plan-Execute模板实例
        
        Args:
            config: 配置参数
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        # 验证参数
        errors = self.validate_parameters(config)
        if errors:
            raise ValueError(f"参数验证失败: {'; '.join(errors)}")
        
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        max_steps = config.get("max_steps", 10)
        planning_prompt = config.get("planning_prompt", "请分析用户需求并制定详细的执行计划")
        execution_prompt = config.get("execution_prompt", "请按照计划执行当前步骤")
        review_prompt = config.get("review_prompt", "请审查执行结果并决定下一步")
        
        # 创建节点配置
        nodes = {
            "planning": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "planner",
                        "description": "计划制定节点",
                        "llm": llm_client,
                        "system_prompt": planning_prompt,
                        "max_iterations": 3,
                        "tools": config.get("planning_tools", []),
                        "output_format": "plan"
                    }
                },
                description="分析需求并制定执行计划"
            ),
            "execute_step": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "executor",
                        "description": "步骤执行节点",
                        "llm": llm_client,
                        "system_prompt": execution_prompt,
                        "max_iterations": 3,
                        "tools": config.get("execution_tools", []),
                        "step_timeout": config.get("step_timeout", 60)
                    }
                },
                description="执行计划中的当前步骤"
            ),
            "review": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "reviewer",
                        "description": "结果审查节点",
                        "llm": llm_client,
                        "system_prompt": review_prompt,
                        "max_iterations": 2,
                        "tools": [],
                        "review_criteria": config.get("review_criteria", ["completeness", "accuracy", "efficiency"])
                    }
                },
                description="审查执行结果并决定下一步"
            ),
            "finalize": NodeConfig(
                type="agent_node",
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
                },
                description="生成最终总结和结果"
            )
        }
        
        # 创建边配置
        edges = [
            EdgeConfig(
                from_node="planning",
                to_node="execute_step",
                type=EdgeType.SIMPLE,
                description="计划制定完成后开始执行"
            ),
            EdgeConfig(
                from_node="execute_step",
                to_node="review",
                type=EdgeType.SIMPLE,
                description="步骤执行完成后进行审查"
            ),
            EdgeConfig(
                from_node="review",
                to_node="execute_step",
                type=EdgeType.CONDITIONAL,
                condition="continue_execution",
                description="如果需要继续执行则执行下一步"
            ),
            EdgeConfig(
                from_node="review",
                to_node="finalize",
                type=EdgeType.CONDITIONAL,
                condition="execution_completed",
                description="如果执行完成则进行最终总结"
            ),
            EdgeConfig(
                from_node="finalize",
                to_node="END",
                type=EdgeType.SIMPLE,
                description="最终总结后结束"
            )
        ]
        
        # 创建工作流配置
        workflow_config = WorkflowConfig(
            name=f"plan_execute_{config.get('name_suffix', 'workflow')}",
            description=f"Plan-Execute工作流 - {config.get('description', '默认Plan-Execute模式')}",
            version="1.0",
            nodes=nodes,
            edges=edges,
            entry_point="planning",
            additional_config={
                "template": "plan_execute",
                "max_steps": max_steps,
                "llm_client": llm_client,
                "planning_tools": config.get("planning_tools", []),
                "execution_tools": config.get("execution_tools", []),
                "step_timeout": config.get("step_timeout", 60),
                "review_criteria": config.get("review_criteria", ["completeness", "accuracy", "efficiency"]),
                "created_at": "auto_generated"
            }
        )
        
        return workflow_config
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义
        
        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        return [
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
    
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 参数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = []
        
        # 验证max_steps
        if "max_steps" in config:
            max_steps = config["max_steps"]
            if not isinstance(max_steps, int) or max_steps < 1:
                errors.append("max_steps必须是大于0的整数")
        
        # 验证step_timeout
        if "step_timeout" in config:
            step_timeout = config["step_timeout"]
            if not isinstance(step_timeout, int) or not (10 <= step_timeout <= 300):
                errors.append("step_timeout必须是10到300之间的整数")
        
        # 验证工具列表
        tool_params = ["planning_tools", "execution_tools", "review_criteria"]
        for param in tool_params:
            if param in config:
                tools = config[param]
                if not isinstance(tools, list):
                    errors.append(f"{param}必须是数组类型")
                elif not all(isinstance(tool, str) for tool in tools):
                    errors.append(f"{param}数组中的所有元素必须是字符串类型")
        
        # 验证字符串参数
        string_params = ["llm_client", "planning_prompt", "execution_prompt", "review_prompt", "name_suffix", "description"]
        for param in string_params:
            if param in config and not isinstance(config[param], str):
                errors.append(f"{param}必须是字符串类型")
        
        return errors


class CollaborativePlanExecuteTemplate(PlanExecuteWorkflowTemplate):
    """协作式Plan-Execute模板
    
    支持多个Agent协作的Plan-Execute模式
    """
    
    @property
    def name(self) -> str:
        """模板名称"""
        return "collaborative_plan_execute"
    
    @property
    def description(self) -> str:
        """模板描述"""
        return "协作式Plan-Execute工作流模式，支持多个Agent协作执行"
    
    def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
        """创建协作式Plan-Execute模板实例
        
        Args:
            config: 配置参数
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        # 验证参数
        errors = self.validate_parameters(config)
        if errors:
            raise ValueError(f"参数验证失败: {'; '.join(errors)}")
        
        # 获取协作配置
        collaborators = config.get("collaborators", [])
        if not collaborators:
            raise ValueError("协作式模板必须配置collaborators参数")
        
        # 获取基础配置
        base_config = super().create_template(config)
        
        # 添加协作节点
        for i, collaborator in enumerate(collaborators):
            node_name = f"collaborator_{i}"
            base_config.nodes[node_name] = NodeConfig(
                type="agent_node",
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
                },
                description=f"协作节点 {i}: {collaborator.get('description', '')}"
            )
            
            # 添加协作边
            if i == 0:
                # 第一个协作者连接到执行步骤
                base_config.edges.append(EdgeConfig(
                    from_node="execute_step",
                    to_node=node_name,
                    type=EdgeType.CONDITIONAL,
                    condition=f"needs_collaborator_{i}",
                    description=f"如果需要协作者{i}则调用"
                ))
            else:
                # 其他协作者连接到前一个协作者
                prev_node = f"collaborator_{i-1}"
                base_config.edges.append(EdgeConfig(
                    from_node=prev_node,
                    to_node=node_name,
                    type=EdgeType.CONDITIONAL,
                    condition=f"needs_collaborator_{i}",
                    description=f"如果需要协作者{i}则调用"
                ))
            
            # 最后一个协作者连接到审查节点
            if i == len(collaborators) - 1:
                base_config.edges.append(EdgeConfig(
                    from_node=node_name,
                    to_node="review",
                    type=EdgeType.SIMPLE,
                    description="协作完成后进行审查"
                ))
        
        # 更新工作流配置
        base_config.name = f"collaborative_plan_execute_{config.get('name_suffix', 'workflow')}"
        base_config.description = f"协作式Plan-Execute工作流 - {config.get('description', '协作Plan-Execute模式')}"
        base_config.additional_config.update({
            "template": "collaborative_plan_execute",
            "collaborators": collaborators,
            "collaboration_enabled": True
        })
        
        return base_config
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义
        
        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        base_params = super().get_parameters()
        
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
        
        return base_params + collaboration_params
    
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 参数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = super().validate_parameters(config)
        
        # 验证collaborators参数
        if "collaborators" in config:
            collaborators = config["collaborators"]
            if not isinstance(collaborators, list):
                errors.append("collaborators必须是数组类型")
            elif len(collaborators) == 0:
                errors.append("collaborators不能为空数组")
            else:
                for i, collaborator in enumerate(collaborators):
                    if not isinstance(collaborator, dict):
                        errors.append(f"collaborators[{i}]必须是对象类型")
                    else:
                        # 验证必需字段
                        if "name" not in collaborator:
                            errors.append(f"collaborators[{i}]缺少name字段")
                        elif not isinstance(collaborator["name"], str):
                            errors.append(f"collaborators[{i}].name必须是字符串类型")
        
        return errors