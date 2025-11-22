"""提示词集成模板基类

提供提示词注入功能的基础实现，供具体模板继承。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ....interfaces.prompts import IPromptInjector, PromptConfig


class PromptIntegratedTemplate(ABC):
    """提示词集成模板基类
    
    提供提示词注入功能的基础实现，供具体模板继承。
    """
    
    def __init__(self, prompt_injector: Optional["IPromptInjector"] = None):
        """初始化提示词集成模板
        
        Args:
            prompt_injector: 提示词注入器实例
        """
        self.prompt_injector = prompt_injector
    
    @abstractmethod
    def get_default_prompt_config(self) -> "PromptConfig":
        """获取默认提示词配置
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        pass
    
    def inject_prompts_to_state(self, state: Dict[str, Any],
                               config: Optional["PromptConfig"] = None) -> Dict[str, Any]:
        """将提示词注入到状态中
        
        Args:
            state: 工作流状态
            config: 提示词配置，如果为None则使用默认配置
            
        Returns:
            Dict[str, Any]: 注入提示词后的状态
        """
        if self.prompt_injector is None:
            return state
            
        prompt_config = config or self.get_default_prompt_config()
        
        # 类型转换：将 Dict[str, Any] 转换为 IWorkflowState
        # 这里我们假设 IWorkflowState 是 Dict[str, Any] 的子类型
        workflow_state = state
        
        result = self.prompt_injector.inject_prompts(workflow_state, prompt_config)  # type: ignore[arg-type]
        
        # 类型转换：将 IWorkflowState 转换回 Dict[str, Any]
        return result  # type: ignore[return-value]
    
    def set_prompt_injector(self, injector: "IPromptInjector") -> None:
        """设置提示词注入器
        
        Args:
            injector: 提示词注入器实例
        """
        self.prompt_injector = injector
    
    def get_prompt_injector(self) -> Optional["IPromptInjector"]:
        """获取提示词注入器
        
        Returns:
            Optional[IPromptInjector]: 提示词注入器实例
        """
        return self.prompt_injector
    
    def create_prompt_config(self, config: Dict[str, Any]) -> "PromptConfig":
        """从配置创建提示词配置
        
        Args:
            config: 工作流配置
            
        Returns:
            PromptConfig: 提示词配置
        """
        from ....interfaces.prompts import PromptConfig
        return PromptConfig(
            system_prompt=config.get("system_prompt"),
            rules=config.get("rules", []),
            user_command=config.get("user_command"),
            cache_enabled=config.get("cache_enabled", True)
        )