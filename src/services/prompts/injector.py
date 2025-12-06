"""
提示词注入器实现

提供异步的提示词注入功能，支持缓存和错误处理
"""

from typing import List, TYPE_CHECKING, Dict, Any, Optional
from ...interfaces.prompts import IPromptInjector, IPromptLoader, IPromptCache, PromptConfig
from ...interfaces.state.workflow import IWorkflowState
from ...core.state.builders.workflow_state_builder import WorkflowStateBuilder as StateBuilder
from src.interfaces.prompts.exceptions import PromptInjectionError

if TYPE_CHECKING:
    from src.infrastructure.messages.base import BaseMessage


class PromptInjector(IPromptInjector):
    """提示词注入器实现"""
    
    def __init__(
        self,
        loader: IPromptLoader,
        cache: Optional[IPromptCache] = None
    ):
        self.loader = loader
        self.cache = cache
    
    async def inject_prompts(
        self,
        state: IWorkflowState,
        config: PromptConfig
    ) -> IWorkflowState:
        """异步注入提示词到工作流状态"""
        try:
            builder = StateBuilder()
            
            # 注入系统提示词
            if config.system_prompt:
                await self._inject_system_prompt_async(builder, config.system_prompt)
            
            # 注入规则提示词
            if config.rules:
                await self._inject_rule_prompts_async(builder, config.rules)
            
            # 注入用户指令
            if config.user_command:
                await self._inject_user_command_async(builder, config.user_command)
            
            # 注入上下文
            if config.context:
                await self._inject_context_prompts_async(builder, config.context)
            
            # 注入示例
            if config.examples:
                await self._inject_examples_async(builder, config.examples)
            
            # 注入约束
            if config.constraints:
                await self._inject_constraints_async(builder, config.constraints)
            
            # 注入格式
            if config.format:
                await self._inject_format_async(builder, config.format)
            
            return builder.build()
        except Exception as e:
            raise PromptInjectionError(f"注入提示词失败: {e}") from e
    
    def inject_system_prompt(
        self,
        state: IWorkflowState,
        prompt_name: str
    ) -> IWorkflowState:
        """注入系统提示词"""
        builder = StateBuilder()
        content = self.loader.load_prompt("system", prompt_name)
        builder.add_message({"role": "system", "content": content})
        return builder.build()
    
    def inject_rule_prompts(
        self,
        state: IWorkflowState,
        rule_names: List[str]
    ) -> IWorkflowState:
        """注入规则提示词"""
        builder = StateBuilder()
        for rule_name in rule_names:
            content = self.loader.load_prompt("rules", rule_name)
            builder.add_message({"role": "system", "content": content})
        return builder.build()
    
    def inject_user_command(
        self,
        state: IWorkflowState,
        command_name: str
    ) -> IWorkflowState:
        """注入用户指令"""
        builder = StateBuilder()
        content = self.loader.load_prompt("user_commands", command_name)
        builder.add_message({"role": "human", "content": content})
        return builder.build()
    
    async def _inject_system_prompt_async(
        self,
        builder: StateBuilder,
        prompt_name: str
    ) -> None:
        """异步注入系统提示词"""
        content = await self._load_prompt_cached("system", prompt_name)
        builder.add_message({"role": "system", "content": content})
    
    async def _inject_rule_prompts_async(
        self,
        builder: StateBuilder,
        rule_names: List[str]
    ) -> None:
        """异步注入规则提示词"""
        for rule_name in rule_names:
            content = await self._load_prompt_cached("rules", rule_name)
            builder.add_message({"role": "system", "content": content})
    
    async def _inject_user_command_async(
        self,
        builder: StateBuilder,
        command_name: str
    ) -> None:
        """异步注入用户指令"""
        content = await self._load_prompt_cached("user_commands", command_name)
        builder.add_message({"role": "human", "content": content})
    
    async def _inject_context_prompts_async(
        self,
        builder: StateBuilder,
        context_names: List[str]
    ) -> None:
        """异步注入上下文提示词"""
        for context_name in context_names:
            content = await self._load_prompt_cached("context", context_name)
            builder.add_message({"role": "system", "content": content})
    
    async def _inject_examples_async(
        self,
        builder: StateBuilder,
        example_names: List[str]
    ) -> None:
        """异步注入示例"""
        for example_name in example_names:
            content = await self._load_prompt_cached("examples", example_name)
            builder.add_message({"role": "system", "content": content})
    
    async def _inject_constraints_async(
        self,
        builder: StateBuilder,
        constraint_names: List[str]
    ) -> None:
        """异步注入约束"""
        for constraint_name in constraint_names:
            content = await self._load_prompt_cached("constraints", constraint_name)
            builder.add_message({"role": "system", "content": content})
    
    async def _inject_format_async(
        self,
        builder: StateBuilder,
        format_name: str
    ) -> None:
        """异步注入格式"""
        content = await self._load_prompt_cached("format", format_name)
        builder.add_message({"role": "system", "content": content})
    
    async def _load_prompt_cached(self, category: str, name: str) -> str:
        """带缓存的提示词加载"""
        cache_key = f"{category}:{name}"
        
        if self.cache:
            cached_content = await self.cache.get(cache_key)
            if cached_content:
                return cached_content
        
        content = await self.loader.load_prompt_async(category, name)
        
        if self.cache:
            await self.cache.set(cache_key, content)
        
        return content



def create_prompt_injector(
    loader: IPromptLoader,
    cache: Optional[IPromptCache] = None
) -> PromptInjector:
    """创建提示词注入器"""
    return PromptInjector(loader, cache)