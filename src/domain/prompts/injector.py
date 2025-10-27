"""提示词注入器实现"""

from typing import List

from .interfaces import IPromptLoader, IPromptInjector
from .models import PromptConfig
from ...application.workflow.state import AgentState, SystemMessage, HumanMessage


class PromptInjector(IPromptInjector):
    """提示词注入器实现"""
    
    def __init__(self, loader: IPromptLoader):
        self.loader = loader
        
    def inject_prompts(self, state: AgentState, config: PromptConfig) -> AgentState:
        """将提示词注入Agent状态"""
        # 注入系统提示词
        if config.system_prompt:
            state = self.inject_system_prompt(state, config.system_prompt)
            
        # 注入规则提示词
        if config.rules:
            state = self.inject_rule_prompts(state, config.rules)
            
        # 注入用户指令
        if config.user_command:
            state = self.inject_user_command(state, config.user_command)
            
        return state
        
    def inject_system_prompt(self, state: AgentState, prompt_name: str) -> AgentState:
        """注入系统提示词"""
        try:
            prompt_content = self.loader.load_prompt("system", prompt_name)
            system_message = SystemMessage(content=prompt_content)
            state["messages"].insert(0, system_message)  # 系统消息在最前面
        except Exception as e:
            raise ValueError(f"注入系统提示词失败 {prompt_name}: {e}")

        return state
        
    def inject_rule_prompts(self, state: AgentState, rule_names: List[str]) -> AgentState:
        """注入规则提示词"""
        # 找到插入位置：系统消息之后，其他消息之前
        insert_index = 0
        for i, message in enumerate(state["messages"]):
            if isinstance(message, SystemMessage):
                insert_index = i + 1
            else:
                break
        
        for rule_name in rule_names:
            try:
                rule_content = self.loader.load_prompt("rules", rule_name)
                rule_message = SystemMessage(content=rule_content)
                state["messages"].insert(insert_index, rule_message)  # 规则消息在系统消息之后
                insert_index += 1
            except Exception as e:
                raise ValueError(f"注入规则提示词失败 {rule_name}: {e}")
            
        return state
        
    def inject_user_command(self, state: AgentState, command_name: str) -> AgentState:
        """注入用户指令"""
        try:
            command_content = self.loader.load_prompt("user_commands", command_name)
            user_message = HumanMessage(content=command_content)
            state["messages"].append(user_message)  # 用户指令在最后
        except Exception as e:
            raise ValueError(f"注入用户指令失败 {command_name}: {e}")
            
        return state