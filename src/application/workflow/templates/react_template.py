"""ReAct工作流模板

实现ReAct（Reasoning + Acting）模式的工作流模板。
"""

from typing import Dict, Any, List
from src.domain.workflow.config import WorkflowConfig, NodeConfig, EdgeConfig, EdgeType
from ..interfaces import IWorkflowTemplate


class ReActWorkflowTemplate(IWorkflowTemplate):
    """ReAct工作流模板
    
    实现ReAct模式：推理-行动-观察循环
    """
    
    @property
    def name(self) -> str:
        """模板名称"""
        return "react"
    
    @property
    def description(self) -> str:
        """模板描述"""
        return "ReAct工作流模式，支持推理-行动-观察循环"
    
    def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
        """创建ReAct模板实例
        
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
        max_iterations = config.get("max_iterations", 10)
        system_prompt = config.get("system_prompt", "你是一个智能助手，请分析用户输入并决定是否需要调用工具")
        final_prompt = config.get("final_prompt", "请根据上下文信息提供准确、有用的回答")
        tool_threshold = config.get("tool_threshold", 0.5)
        
        # 创建节点配置
        nodes = {
            "analyze": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "react_analyzer",
                        "description": "ReAct分析节点",
                        "llm": llm_client,
                        "system_prompt": system_prompt,
                        "max_iterations": max_iterations,
                        "tools": config.get("tools", []),
                        "tool_threshold": tool_threshold
                    }
                },
                description="分析用户输入并决定下一步行动"
            ),
            "execute_tool": NodeConfig(
                type="tool_node",
                config={
                    "tool_manager": "default",
                    "timeout": 30,
                    "max_parallel_calls": 1,
                    "retry_on_failure": False,
                    "continue_on_error": True
                },
                description="执行工具调用"
            ),
            "finalize": NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "react_finalizer",
                        "description": "ReAct最终回答节点",
                        "llm": llm_client,
                        "system_prompt": final_prompt,
                        "max_iterations": 1,
                        "tools": []
                    }
                },
                description="生成最终回答"
            )
        }
        
        # 创建边配置
        edges = [
            EdgeConfig(
                from_node="analyze",
                to_node="execute_tool",
                type=EdgeType.CONDITIONAL,
                condition="has_tool_call",
                description="如果有工具调用则执行工具"
            ),
            EdgeConfig(
                from_node="analyze",
                to_node="finalize",
                type=EdgeType.CONDITIONAL,
                condition="no_tool_call",
                description="如果没有工具调用则直接生成回答"
            ),
            EdgeConfig(
                from_node="execute_tool",
                to_node="analyze",
                type=EdgeType.SIMPLE,
                description="工具执行完成后继续分析"
            ),
            EdgeConfig(
                from_node="finalize",
                to_node="END",
                type=EdgeType.SIMPLE,
                description="生成最终回答后结束"
            )
        ]
        
        # 创建工作流配置
        workflow_config = WorkflowConfig(
            name=f"react_{config.get('name_suffix', 'workflow')}",
            description=f"ReAct工作流 - {config.get('description', '默认ReAct模式')}",
            version="1.0",
            nodes=nodes,
            edges=edges,
            entry_point="analyze",
            additional_config={
                "template": "react",
                "max_iterations": max_iterations,
                "llm_client": llm_client,
                "tools": config.get("tools", []),
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
                "name": "max_iterations",
                "type": "integer",
                "description": "最大迭代次数",
                "required": False,
                "default": 10,
                "min": 1,
                "max": 50
            },
            {
                "name": "system_prompt",
                "type": "string",
                "description": "分析节点的系统提示词",
                "required": False,
                "default": "你是一个智能助手，请分析用户输入并决定是否需要调用工具"
            },
            {
                "name": "final_prompt",
                "type": "string",
                "description": "最终回答节点的系统提示词",
                "required": False,
                "default": "请根据上下文信息提供准确、有用的回答"
            },
            {
                "name": "tools",
                "type": "array",
                "description": "可用工具列表",
                "required": False,
                "default": [],
                "items": {
                    "type": "string"
                }
            },
            {
                "name": "tool_threshold",
                "type": "number",
                "description": "工具调用阈值",
                "required": False,
                "default": 0.5,
                "min": 0.0,
                "max": 1.0
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
                "default": "默认ReAct模式"
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
        
        # 验证max_iterations
        if "max_iterations" in config:
            max_iterations = config["max_iterations"]
            if not isinstance(max_iterations, int) or max_iterations < 1:
                errors.append("max_iterations必须是大于0的整数")
        
        # 验证tool_threshold
        if "tool_threshold" in config:
            tool_threshold = config["tool_threshold"]
            if not isinstance(tool_threshold, (int, float)) or not (0.0 <= tool_threshold <= 1.0):
                errors.append("tool_threshold必须是0.0到1.0之间的数字")
        
        # 验证tools
        if "tools" in config:
            tools = config["tools"]
            if not isinstance(tools, list):
                errors.append("tools必须是数组类型")
            elif not all(isinstance(tool, str) for tool in tools):
                errors.append("tools数组中的所有元素必须是字符串类型")
        
        # 验证字符串参数
        string_params = ["llm_client", "system_prompt", "final_prompt", "name_suffix", "description"]
        for param in string_params:
            if param in config and not isinstance(config[param], str):
                errors.append(f"{param}必须是字符串类型")
        
        return errors


class EnhancedReActTemplate(ReActWorkflowTemplate):
    """增强的ReAct模板
    
    提供更多配置选项和优化
    """
    
    @property
    def name(self) -> str:
        """模板名称"""
        return "enhanced_react"
    
    @property
    def description(self) -> str:
        """模板描述"""
        return "增强的ReAct工作流模式，支持更多配置选项和优化"
    
    def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
        """创建增强的ReAct模板实例
        
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
        enable_memory = config.get("enable_memory", True)
        enable_error_recovery = config.get("enable_error_recovery", True)
        enable_parallel_tools = config.get("enable_parallel_tools", False)
        
        # 调用基类方法创建基础配置
        base_config = super().create_template(config)
        
        # 增强节点配置
        if enable_memory:
            # 为分析节点添加记忆配置
            analyze_config = base_config.nodes["analyze"].config
            analyze_config["agent_config"]["memory_config"] = {
                "enabled": True,
                "max_tokens": 2000,
                "max_messages": 50
            }
        
        if enable_error_recovery:
            # 添加错误恢复节点
            base_config.nodes["error_recovery"] = NodeConfig(
                type="agent_node",
                config={
                    "agent_config": {
                        "agent_type": "react",
                        "name": "error_recovery",
                        "description": "错误恢复节点",
                        "llm": config.get("llm_client", "default"),
                        "system_prompt": "分析错误并尝试恢复执行",
                        "max_iterations": 1,
                        "tools": []
                    }
                },
                description="处理错误并尝试恢复"
            )
            
            # 添加错误处理边
            base_config.edges.append(EdgeConfig(
                from_node="analyze",
                to_node="error_recovery",
                type=EdgeType.CONDITIONAL,
                condition="has_errors",
                description="如果有错误则进行错误恢复"
            ))
            
            base_config.edges.append(EdgeConfig(
                from_node="error_recovery",
                to_node="analyze",
                type=EdgeType.SIMPLE,
                description="错误恢复后重新分析"
            ))
        
        if enable_parallel_tools:
            # 修改工具执行节点配置
            tool_config = base_config.nodes["execute_tool"].config
            tool_config["max_parallel_calls"] = config.get("max_parallel_calls", 3)
        
        # 更新工作流配置
        base_config.name = f"enhanced_react_{config.get('name_suffix', 'workflow')}"
        base_config.description = f"增强的ReAct工作流 - {config.get('description', '增强ReAct模式')}"
        base_config.additional_config.update({
            "template": "enhanced_react",
            "enable_memory": enable_memory,
            "enable_error_recovery": enable_error_recovery,
            "enable_parallel_tools": enable_parallel_tools
        })
        
        return base_config
    
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义
        
        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        base_params = super().get_parameters()
        
        # 添加增强参数
        enhanced_params = [
            {
                "name": "enable_memory",
                "type": "boolean",
                "description": "是否启用记忆功能",
                "required": False,
                "default": True
            },
            {
                "name": "enable_error_recovery",
                "type": "boolean",
                "description": "是否启用错误恢复",
                "required": False,
                "default": True
            },
            {
                "name": "enable_parallel_tools",
                "type": "boolean",
                "description": "是否启用并行工具执行",
                "required": False,
                "default": False
            },
            {
                "name": "max_parallel_calls",
                "type": "integer",
                "description": "最大并行工具调用数",
                "required": False,
                "default": 3,
                "min": 1,
                "max": 10
            }
        ]
        
        return base_params + enhanced_params
    
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 参数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        errors = super().validate_parameters(config)
        
        # 验证布尔参数
        bool_params = ["enable_memory", "enable_error_recovery", "enable_parallel_tools"]
        for param in bool_params:
            if param in config and not isinstance(config[param], bool):
                errors.append(f"{param}必须是布尔类型")
        
        # 验证max_parallel_calls
        if "max_parallel_calls" in config:
            max_parallel = config["max_parallel_calls"]
            if not isinstance(max_parallel, int) or not (1 <= max_parallel <= 10):
                errors.append("max_parallel_calls必须是1到10之间的整数")
        
        return errors