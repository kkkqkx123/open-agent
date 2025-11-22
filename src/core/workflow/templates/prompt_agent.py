"""提示词代理工作流模板

基于提示词注入的简单代理工作流模板。
"""

from typing import Dict, Any, Optional, List, TYPE_CHECKING
import logging

from .base import BaseWorkflowTemplate
from .prompt_integration import PromptIntegratedTemplate
from ..workflow import Workflow
from ..value_objects import WorkflowStep, WorkflowTransition, StepType, TransitionType

if TYPE_CHECKING:
    from ....interfaces.prompts import IPromptInjector, PromptConfig

logger = logging.getLogger(__name__)


class PromptAgentTemplate(BaseWorkflowTemplate, PromptIntegratedTemplate):
    """提示词代理工作流模板
    
    基于提示词注入的简单代理工作流模板。
    """
    
    def __init__(self, prompt_injector: Optional["IPromptInjector"] = None):
        """初始化提示词代理模板
        
        Args:
            prompt_injector: 提示词注入器实例
        """
        BaseWorkflowTemplate.__init__(self)
        PromptIntegratedTemplate.__init__(self, prompt_injector)
        self._name = "prompt_agent"
        self._description = "基于提示词注入的代理工作流模板"
        self._category = "agent"
        self._version = "1.0"
        
        # 更新参数定义
        self._parameters = [
            {
                "name": "llm_client",
                "type": "string",
                "description": "LLM客户端标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "system_prompt",
                "type": "string",
                "description": "系统提示词名称",
                "required": False,
                "default": "assistant"
            },
            {
                "name": "rules",
                "type": "array",
                "description": "规则提示词列表",
                "required": False,
                "default": ["safety", "format"]
            },
            {
                "name": "user_command",
                "type": "string",
                "description": "用户指令名称",
                "required": False,
                "default": "data_analysis"
            },
            {
                "name": "cache_enabled",
                "type": "boolean",
                "description": "是否启用提示词缓存",
                "required": False,
                "default": True
            }
        ]
    
    def get_default_prompt_config(self) -> "PromptConfig":
        """获取默认提示词配置
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        from ....interfaces.prompts import PromptConfig
        return PromptConfig(
            system_prompt="assistant",
            rules=["safety", "format"],
            user_command="data_analysis",
            cache_enabled=True
        )
    
    def _build_workflow_structure(self, workflow: Workflow, config: Dict[str, Any]) -> None:
        """构建提示词代理工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        system_prompt = config.get("system_prompt", "assistant")
        rules = config.get("rules", ["safety", "format"])
        user_command = config.get("user_command", "data_analysis")
        cache_enabled = config.get("cache_enabled", True)
        
        # 创建提示词注入节点
        inject_prompts_step = self._create_step(
            step_id="inject_prompts",
            step_name="inject_prompts",
            step_type=StepType.ANALYSIS,
            description="注入提示词到工作流状态",
            config={
                "prompt_config": {
                    "system_prompt": system_prompt,
                    "rules": rules,
                    "user_command": user_command,
                    "cache_enabled": cache_enabled
                },
                "prompt_injector": self.prompt_injector
            }
        )
        workflow.add_step(inject_prompts_step)
        
        # 创建LLM调用节点
        llm_step = self._create_step(
            step_id="call_llm",
            step_name="call_llm",
            step_type=StepType.EXECUTION,
            description="调用LLM生成响应",
            config={
                "llm_client": llm_client,
                "timeout": 30,
                "retry_on_failure": True,
                "max_retries": 3
            }
        )
        workflow.add_step(llm_step)
        
        # 创建转换：提示词注入 -> LLM调用
        inject_to_llm = self._create_transition(
            transition_id="inject_to_llm",
            from_step="inject_prompts",
            to_step="call_llm",
            transition_type=TransitionType.SIMPLE,
            description="注入提示词后调用LLM"
        )
        workflow.add_transition(inject_to_llm)
        
        # 设置入口点
        workflow.set_entry_point("inject_prompts")
        
        logger.info(f"构建提示词代理工作流结构完成: {workflow.name}")


class SimplePromptAgentTemplate(PromptAgentTemplate):
    """简单提示词代理模板
    
    提供更简化的配置和功能。
    """
    
    def __init__(self, prompt_injector: Optional["IPromptInjector"] = None):
        """初始化简单提示词代理模板"""
        super().__init__(prompt_injector)
        self._name = "simple_prompt_agent"
        self._description = "简化的提示词代理工作流模板"
        self._category = "agent"
        self._version = "1.0"
        
        # 简化参数定义
        self._parameters = [
            {
                "name": "llm_client",
                "type": "string",
                "description": "LLM客户端标识",
                "required": False,
                "default": "default"
            },
            {
                "name": "system_prompt",
                "type": "string",
                "description": "系统提示词名称",
                "required": False,
                "default": "assistant"
            }
        ]
    
    def get_default_prompt_config(self) -> "PromptConfig":
        """获取默认提示词配置（简化版）
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        from ....interfaces.prompts import PromptConfig
        return PromptConfig(
            system_prompt="assistant",
            rules=["safety"],
            user_command="general",
            cache_enabled=True
        )
    
    def _build_workflow_structure(self, workflow: Workflow, config: Dict[str, Any]) -> None:
        """构建简单提示词代理工作流结构
        
        Args:
            workflow: 工作流实例
            config: 配置参数
        """
        # 获取配置参数
        llm_client = config.get("llm_client", "default")
        system_prompt = config.get("system_prompt", "assistant")
        
        # 创建提示词注入节点
        inject_prompts_step = self._create_step(
            step_id="inject_prompts",
            step_name="inject_prompts",
            step_type=StepType.ANALYSIS,
            description="注入提示词到工作流状态",
            config={
                "prompt_config": {
                    "system_prompt": system_prompt,
                    "rules": ["safety"],
                    "user_command": "general",
                    "cache_enabled": True
                },
                "prompt_injector": self.prompt_injector
            }
        )
        workflow.add_step(inject_prompts_step)
        
        # 创建LLM调用节点
        llm_step = self._create_step(
            step_id="call_llm",
            step_name="call_llm",
            step_type=StepType.EXECUTION,
            description="调用LLM生成响应",
            config={
                "llm_client": llm_client,
                "timeout": 30,
                "retry_on_failure": False,
                "max_retries": 1
            }
        )
        workflow.add_step(llm_step)
        
        # 创建转换：提示词注入 -> LLM调用
        inject_to_llm = self._create_transition(
            transition_id="inject_to_llm",
            from_step="inject_prompts",
            to_step="call_llm",
            transition_type=TransitionType.SIMPLE,
            description="注入提示词后调用LLM"
        )
        workflow.add_transition(inject_to_llm)
        
        # 设置入口点
        workflow.set_entry_point("inject_prompts")
        
        logger.info(f"构建简单提示词代理工作流结构完成: {workflow.name}")