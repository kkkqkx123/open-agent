"""提示词管理接口定义

集中化接口定义，提供提示词系统的抽象契约。
"""

from abc import ABC, abstractmethod
from typing import List, Optional, TYPE_CHECKING
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

if TYPE_CHECKING:
    from .state.workflow import IWorkflowState


# 数据模型定义（在接口层定义，被核心层和服务层共享）

@dataclass
class PromptMeta:
    """提示词元信息
    
    存储提示词的基本信息和元数据。
    """
    name: str                    # 提示词名称
    category: str               # 类别：system/rules/user_commands
    path: Path                  # 文件或目录路径
    description: str            # 描述
    is_composite: bool = False  # 是否为复合提示词
    created_at: datetime = field(default_factory=datetime.now)  # 创建时间
    updated_at: datetime = field(default_factory=datetime.now)  # 更新时间
    
    def validate_path(self) -> bool:
        """验证路径是否存在
        
        Returns:
            bool: 路径是否存在
        """
        return self.path.exists()


@dataclass
class PromptConfig:
    """提示词配置
    
    定义如何注入提示词到工作流状态。
    """
    system_prompt: Optional[str] = None      # 系统提示词名称
    rules: List[str] = field(default_factory=list)  # 规则提示词列表
    user_command: Optional[str] = None       # 用户指令名称
    cache_enabled: bool = True               # 是否启用缓存


class IPromptRegistry(ABC):
    """提示词注册表接口
    
    管理提示词的元信息和注册。
    """
    
    @abstractmethod
    def get_prompt_meta(self, category: str, name: str) -> PromptMeta:
        """获取提示词元信息
        
        Args:
            category: 提示词类别（system/rules/user_commands）
            name: 提示词名称
            
        Returns:
            PromptMeta: 提示词元信息
            
        Raises:
            PromptNotFoundError: 提示词不存在
        """
        pass
        
    @abstractmethod
    def list_prompts(self, category: str) -> List[PromptMeta]:
        """列出指定类别的所有提示词
        
        Args:
            category: 提示词类别
            
        Returns:
            List[PromptMeta]: 提示词元信息列表
        """
        pass
        
    @abstractmethod
    def register_prompt(self, category: str, meta: PromptMeta) -> None:
        """注册提示词
        
        Args:
            category: 提示词类别
            meta: 提示词元信息
            
        Raises:
            PromptRegistryError: 注册失败
        """
        pass
        
    @abstractmethod
    def validate_registry(self) -> bool:
        """验证注册表完整性
        
        检查所有注册的提示词文件是否存在。
        
        Returns:
            bool: 验证是否通过
            
        Raises:
            PromptRegistryError: 验证失败
        """
        pass


class IPromptLoader(ABC):
    """提示词加载器接口
    
    负责从文件系统加载提示词内容。
    """
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """加载提示词内容
        
        根据类别和名称从注册表获取元信息，
        然后加载相应的提示词文件。
        
        Args:
            category: 提示词类别
            name: 提示词名称
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 加载失败
            PromptNotFoundError: 提示词不存在
        """
        pass
        
    @abstractmethod
    def load_simple_prompt(self, file_path: Path) -> str:
        """加载简单提示词
        
        从单个文件加载提示词内容。
        
        Args:
            file_path: 提示词文件路径
            
        Returns:
            str: 提示词内容
            
        Raises:
            PromptLoadError: 加载失败
        """
        pass
        
    @abstractmethod
    def load_composite_prompt(self, dir_path: Path) -> str:
        """加载复合提示词
        
        从目录加载复合提示词（包含多个文件）。
        加载顺序：index.md + 按文件名排序的其他文件。
        
        Args:
            dir_path: 提示词目录路径
            
        Returns:
            str: 合并后的提示词内容
            
        Raises:
            PromptLoadError: 加载失败
        """
        pass
        
    @abstractmethod
    def clear_cache(self) -> None:
        """清空缓存
        
        清空所有已加载的提示词缓存。
        """
        pass


class IPromptInjector(ABC):
    """提示词注入器接口
    
    负责将提示词注入到工作流状态中。
    """
    
    @abstractmethod
    def inject_prompts(
        self,
        state: "IWorkflowState",
        config: PromptConfig
    ) -> "IWorkflowState":
        """将提示词注入工作流状态
        
        根据配置注入系统提示、规则和用户指令。
        
        Args:
            state: 工作流状态
            config: 提示词配置
            
        Returns:
            WorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        pass

    @abstractmethod
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
            WorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        pass

    @abstractmethod
    def inject_rule_prompts(
        self,
        state: "IWorkflowState",
        rule_names: List[str]
    ) -> "IWorkflowState":
        """注入规则提示词
        
        在系统提示词之后插入规则提示词。
        
        Args:
            state: 工作流状态
            rule_names: 规则提示词名称列表
            
        Returns:
            WorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        pass

    @abstractmethod
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
            WorkflowState: 更新后的工作流状态
            
        Raises:
            PromptInjectionError: 注入失败
        """
        pass
