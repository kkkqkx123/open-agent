"""提示词注入器实现

负责将提示词注入到工作流状态中。
"""

from typing import TYPE_CHECKING, Any, Dict, List, cast

from ...interfaces.prompts import IPromptLoader, IPromptInjector, PromptConfig
from ...core.common.exceptions import PromptInjectionError

if TYPE_CHECKING:
    from ...interfaces.state import IWorkflowState


class PromptInjector(IPromptInjector):
    """提示词注入器实现
    
    负责将提示词内容注入到工作流状态中的消息列表。
    """
    
    def __init__(self, loader: IPromptLoader) -> None:
        """初始化提示词注入器
        
        Args:
            loader: 提示词加载器实例
        """
        self.loader = loader
        
    def inject_prompts(
        self,
        state: "IWorkflowState",
        config: PromptConfig
    ) -> "IWorkflowState":
        """将提示词注入工作流状态
        
        按顺序注入系统提示、规则和用户指令。
        
        Args:
            state: 工作流状态
            config: 提示词配置
            
        Returns:
            IWorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        try:
            # 将状态对象强制转换为字典进行处理
            state_dict = cast(Dict[str, Any], state)
            
            # 注入系统提示词
            if config.system_prompt:
                self.inject_system_prompt(state, config.system_prompt)
                
            # 注入规则提示词
            if config.rules:
                self.inject_rule_prompts(state, config.rules)
                
            # 注入用户指令
            if config.user_command:
                self.inject_user_command(state, config.user_command)
                
            return state
        except PromptInjectionError:
            raise
        except Exception as e:
            raise PromptInjectionError(f"注入提示词失败: {e}") from e
        
    def inject_system_prompt(
        self,
        state: "IWorkflowState",
        prompt_name: str
    ) -> "IWorkflowState":
        """注入系统提示词
        
        在消息列表最前面插入系统提示词。
        
        Args:
            state: 工作流状态
            prompt_name: 系统提示词名称
            
        Returns:
            IWorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        try:
            from langchain_core.messages import SystemMessage
            
            prompt_content = self.loader.load_prompt("system", prompt_name)
            system_message = SystemMessage(content=prompt_content)
            
            # 强制转换为字典以进行操作
            state_dict = cast(Dict[str, Any], state)
            
            # 安全访问messages列表
            if "messages" not in state_dict:
                state_dict["messages"] = []
            state_dict["messages"].insert(0, system_message)  # 系统消息在最前面
        except Exception as e:
            raise PromptInjectionError(
                f"注入系统提示词失败 {prompt_name}: {e}"
            ) from e

        return state
        
    def inject_rule_prompts(
        self,
        state: "IWorkflowState",
        rule_names: List[str]
    ) -> "IWorkflowState":
        """注入规则提示词
        
        在系统消息之后插入规则提示词。
        
        Args:
            state: 工作流状态
            rule_names: 规则提示词名称列表
            
        Returns:
            IWorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        try:
            from langchain_core.messages import SystemMessage
            
            # 强制转换为字典以进行操作
            state_dict = cast(Dict[str, Any], state)
            
            # 找到插入位置：系统消息之后，其他消息之前
            insert_index = 0
            for i, message in enumerate(state_dict.get("messages", [])):
                if isinstance(message, SystemMessage):
                    insert_index = i + 1
                else:
                    break
            
            for rule_name in rule_names:
                rule_content = self.loader.load_prompt("rules", rule_name)
                rule_message = SystemMessage(content=rule_content)
                state_dict["messages"].insert(insert_index, rule_message)  # 规则消息在系统消息之后
                insert_index += 1
                
            return state
        except Exception as e:
            raise PromptInjectionError(
                f"注入规则提示词失败: {e}"
            ) from e
        
    def inject_user_command(
        self,
        state: "IWorkflowState",
        command_name: str
    ) -> "IWorkflowState":
        """注入用户指令
        
        在消息列表最后添加用户指令。
        
        Args:
            state: 工作流状态
            command_name: 用户指令名称
            
        Returns:
            IWorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        try:
            from langchain_core.messages import HumanMessage
            
            prompt_content = self.loader.load_prompt("user_commands", command_name)
            user_message = HumanMessage(content=prompt_content)
            
            # 强制转换为字典以进行操作
            state_dict = cast(Dict[str, Any], state)
            
            # 安全访问messages列表
            if "messages" not in state_dict:
                state_dict["messages"] = []
            state_dict["messages"].append(user_message)  # 用户指令在最后
        except Exception as e:
            raise PromptInjectionError(
                f"注入用户指令失败 {command_name}: {e}"
            ) from e
            
        return state
