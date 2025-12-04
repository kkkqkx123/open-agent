"""
提示词注入器和加载器接口定义

提供提示词注入、加载等功能的抽象接口
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from src.infrastructure.messages.base import BaseMessage
    from ..state.workflow import IWorkflowState
    from .models import PromptConfig


class IPromptLoader(ABC):
    """提示词加载器接口"""
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """同步加载提示词
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            提示词内容
        """
        pass
    
    @abstractmethod
    async def load_prompt_async(self, category: str, name: str) -> str:
        """异步加载提示词
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            提示词内容
        """
        pass
    
    @abstractmethod
    def load_prompts(self, category: str) -> dict:
        """加载指定类别的所有提示词
        
        Args:
            category: 提示词类别
            
        Returns:
            提示词字典
        """
        pass


class IPromptInjector(ABC):
    """提示词注入器接口"""
    
    @abstractmethod
    async def inject_prompts(
        self,
        state: "IWorkflowState",
        config: "PromptConfig"
    ) -> "IWorkflowState":
        """异步注入所有配置的提示词到工作流状态
        
        Args:
            state: 工作流状态
            config: 提示词配置
            
        Returns:
            更新后的工作流状态
        """
        pass
    
    @abstractmethod
    def inject_system_prompt(
        self,
        state: "IWorkflowState",
        prompt_name: str
    ) -> "IWorkflowState":
        """注入系统提示词
        
        Args:
            state: 工作流状态
            prompt_name: 提示词名称
            
        Returns:
            更新后的工作流状态
        """
        pass
    
    @abstractmethod
    def inject_rule_prompts(
        self,
        state: "IWorkflowState",
        rule_names: List[str]
    ) -> "IWorkflowState":
        """注入规则提示词
        
        Args:
            state: 工作流状态
            rule_names: 规则提示词名称列表
            
        Returns:
            更新后的工作流状态
        """
        pass
    
    @abstractmethod
    def inject_user_command(
        self,
        state: "IWorkflowState",
        command_name: str
    ) -> "IWorkflowState":
        """注入用户命令提示词
        
        Args:
            state: 工作流状态
            command_name: 命令名称
            
        Returns:
            更新后的工作流状态
        """
        pass
