"""工作流辅助函数

提供创建提示词工作流的便捷函数。
"""

from typing import Any, Dict, Optional
from ...interfaces.prompts import IPromptInjector
from ...core.workflow.templates.prompt_agent import PromptAgentTemplate, SimplePromptAgentTemplate


def create_prompt_agent_workflow(prompt_injector: IPromptInjector,
                                llm_client: Optional[Any] = None,
                                system_prompt: Optional[str] = None,
                                rules: Optional[list] = None,
                                user_command: Optional[str] = None,
                                cache_enabled: bool = True) -> Any:
    """创建提示词代理工作流
    
    Args:
        prompt_injector: 提示词注入器实例
        llm_client: LLM客户端实例
        system_prompt: 系统提示词名称
        rules: 规则提示词列表
        user_command: 用户指令名称
        cache_enabled: 是否启用缓存
        
    Returns:
        Any: 工作流实例
    """
    template = PromptAgentTemplate(prompt_injector=prompt_injector)
    
    config = {
        "llm_client": llm_client or "default"
    }
    
    if system_prompt is not None:
        config["system_prompt"] = system_prompt
    if rules is not None:
        config["rules"] = rules
    if user_command is not None:
        config["user_command"] = user_command
    if cache_enabled is not None:
        config["cache_enabled"] = cache_enabled
    
    workflow = template.create_workflow(
        name="prompt_agent_workflow",
        description="基于提示词的代理工作流",
        config=config
    )
    
    return workflow


def create_simple_prompt_agent_workflow(prompt_injector: IPromptInjector,
                                       llm_client: Optional[Any] = None,
                                       system_prompt: Optional[str] = None) -> Any:
    """创建简单提示词代理工作流
    
    Args:
        prompt_injector: 提示词注入器实例
        llm_client: LLM客户端实例
        system_prompt: 系统提示词名称
        
    Returns:
        Any: 工作流实例
    """
    template = SimplePromptAgentTemplate(prompt_injector=prompt_injector)
    
    config = {
        "llm_client": llm_client or "default"
    }
    
    if system_prompt is not None:
        config["system_prompt"] = system_prompt
    
    workflow = template.create_workflow(
        name="simple_prompt_agent_workflow",
        description="简化的提示词代理工作流",
        config=config
    )
    
    return workflow