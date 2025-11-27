"""ReAct工作流模板

实现ReAct（Reasoning + Acting）模式的工作流模板。
"""

from typing import Dict, Any, List
import logging

from .base import BaseWorkflowTemplate
from src.interfaces.workflow.core import IWorkflow
from ..value_objects import StepType, TransitionType

logger = logging.getLogger(__name__)


class ReActWorkflowTemplate(BaseWorkflowTemplate):
    """ReAct工作流模板
    
    实现ReAct模式：推理-行动-观察循环
    """
    
    def __init__(self) -> None:
        """初始化ReAct模板"""
        super().__init__()
        self._name = "react"
        self._description = "ReAct工作流模式，支持推理-行动-观察循环"
        self._category = "agent"
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
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建ReAct工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        max_iterations = config.get("max_iterations", 10)
        system_prompt = config.get("system_prompt", "你是一个智能助手，请分析用户输入并决定是否需要调用工具")
        final_prompt = config.get("final_prompt", "请根据上下文信息提供准确、有用的回答")
        tool_threshold = config.get("tool_threshold", 0.5)
        tools = config.get("tools", [])
        
        # 创建分析节点
        analyze_step = self._create_step(
            step_id="analyze",
            step_name="analyze",
            step_type=StepType.ANALYSIS,
            description="分析用户输入并决定下一步行动",
            config={
                "agent_config": {
                    "agent_type": "react",
                    "name": "react_analyzer",
                    "description": "ReAct分析节点",
                    "llm": llm_client,
                    "system_prompt": system_prompt,
                    "max_iterations": max_iterations,
                    "tools": tools,
                    "tool_threshold": tool_threshold
                }
            }
        )
        workflow.add_step(analyze_step)
        
        # 创建工具执行节点
        tool_step = self._create_step(
            step_id="execute_tool",
            step_name="execute_tool",
            step_type=StepType.EXECUTION,
            description="执行工具调用",
            config={
                "tool_manager": "default",
                "timeout": 30,
                "max_parallel_calls": 1,
                "retry_on_failure": False,
                "continue_on_error": True
            }
        )
        workflow.add_step(tool_step)
        
        # 创建最终回答节点
        finalize_step = self._create_step(
            step_id="finalize",
            step_name="finalize",
            step_type=StepType.ANALYSIS,
            description="生成最终回答",
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
            }
        )
        workflow.add_step(finalize_step)
        
        # 创建转换
        # 分析 -> 工具执行（条件：有工具调用）
        analyze_to_tool = self._create_transition(
            transition_id="analyze_to_tool",
            from_step="analyze",
            to_step="execute_tool",
            transition_type=TransitionType.CONDITIONAL,
            condition="has_tool_call",
            description="如果有工具调用则执行工具"
        )
        workflow.add_transition(analyze_to_tool)
        
        # 分析 -> 最终回答（条件：无工具调用）
        analyze_to_finalize = self._create_transition(
            transition_id="analyze_to_finalize",
            from_step="analyze",
            to_step="finalize",
            transition_type=TransitionType.CONDITIONAL,
            condition="no_tool_call",
            description="如果没有工具调用则直接生成回答"
        )
        workflow.add_transition(analyze_to_finalize)
        
        # 工具执行 -> 分析（简单转换）
        tool_to_analyze = self._create_transition(
            transition_id="tool_to_analyze",
            from_step="execute_tool",
            to_step="analyze",
            transition_type=TransitionType.SIMPLE,
            description="工具执行完成后继续分析"
        )
        workflow.add_transition(tool_to_analyze)
        
        # 设置入口点
        workflow.set_entry_point("analyze")
        
        logger.info(f"构建ReAct工作流结构完成: {workflow.name}")


class EnhancedReActTemplate(ReActWorkflowTemplate):
    """增强的ReAct模板
    
    提供更多配置选项和优化
    """
    
    def __init__(self) -> None:
        """初始化增强ReAct模板"""
        super().__init__()
        self._name = "enhanced_react"
        self._description = "增强的ReAct工作流模式，支持更多配置选项和优化"
        self._category = "agent"
        self._version = "2.0"
        
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
        
        self._parameters.extend(enhanced_params)
    
    def _build_workflow_structure(self, workflow: IWorkflow, config: Dict[str, Any]) -> None:
        """构建增强的ReAct工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 调用基类方法创建基础结构
        super()._build_workflow_structure(workflow, config)
        
        # 获取增强配置
        enable_memory = config.get("enable_memory", True)
        enable_error_recovery = config.get("enable_error_recovery", True)
        enable_parallel_tools = config.get("enable_parallel_tools", False)
        
        # 增强分析节点配置
        if enable_memory:
            analyze_step = workflow.get_step("analyze")
            if analyze_step:
                analyze_step.config["agent_config"]["memory_config"] = {
                    "enabled": True,
                    "max_tokens": 2000,
                    "max_messages": 50
                }
        
        # 添加错误恢复节点
        if enable_error_recovery:
            error_recovery_step = self._create_step(
                step_id="error_recovery",
                step_name="error_recovery",
                step_type=StepType.ANALYSIS,
                description="处理错误并尝试恢复",
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
                }
            )
            workflow.add_step(error_recovery_step)
            
            # 添加错误处理转换
            analyze_to_error = self._create_transition(
                transition_id="analyze_to_error",
                from_step="analyze",
                to_step="error_recovery",
                transition_type=TransitionType.CONDITIONAL,
                condition="has_errors",
                description="如果有错误则进行错误恢复"
            )
            workflow.add_transition(analyze_to_error)
            
            error_to_analyze = self._create_transition(
                transition_id="error_to_analyze",
                from_step="error_recovery",
                to_step="analyze",
                transition_type=TransitionType.SIMPLE,
                description="错误恢复后重新分析"
            )
            workflow.add_transition(error_to_analyze)
        
        # 修改工具执行节点配置
        if enable_parallel_tools:
            tool_step = workflow.get_step("execute_tool")
            if tool_step:
                tool_step.config["max_parallel_calls"] = config.get("max_parallel_calls", 3)
        
        logger.info(f"构建增强ReAct工作流结构完成: {workflow.name}")