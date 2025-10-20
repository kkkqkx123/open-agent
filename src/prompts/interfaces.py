"""提示词管理模块核心接口定义"""

from abc import ABC, abstractmethod
from typing import List
from pathlib import Path

from prompts.agent_state import AgentState

from .models import PromptMeta, PromptConfig


class IPromptRegistry(ABC):
    """提示词注册表接口"""
    
    @abstractmethod
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元信息"""
        pass
        
    @abstractmethod
    def list_prompts(self, category: str) -> List[PromptMeta]:
        """列出指定类别的所有提示词"""
        pass
        
    @abstractmethod
    def register_prompt(self, category: str, meta: PromptMeta) -> None:
        """注册提示词"""
        pass
        
    @abstractmethod
    def validate_registry(self) -> bool:
        """验证注册表完整性"""
        pass


class IPromptLoader(ABC):
    """提示词加载器接口"""
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容"""
        pass
        
    @abstractmethod
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词"""
        pass
        
    @abstractmethod
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词"""
        pass
        
    @abstractmethod
    def clear_cache(self) -> None:
        """清空缓存"""
        pass


class IPromptInjector(ABC):
    """提示词注入器接口"""
    
    @abstractmethod
    def inject_prompts(self, state: "AgentState", config: PromptConfig) -> "AgentState":
        """将提示词注入Agent状态"""
        pass
        
    @abstractmethod
    def inject_system_prompt(self, state: "AgentState", prompt_name: str) -> "AgentState":
        """注入系统提示词"""
        pass
        
    @abstractmethod
    def inject_rule_prompts(self, state: "AgentState", rule_names: List[str]) -> "AgentState":
        """注入规则提示词"""
        pass
        
    @abstractmethod
    def inject_user_command(self, state: "AgentState", command_name: str) -> "AgentState":
        """注入用户指令"""
        pass