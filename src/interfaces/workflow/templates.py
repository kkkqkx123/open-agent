"""工作流模板接口定义

为工作流模板系统提供统一的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, TYPE_CHECKING
# 修复相对导入路径：从 workflow/templates.py 到 prompts/ 只需要向上两级
from ..prompts import IPromptInjector, PromptConfig

if TYPE_CHECKING:
    from ...interfaces.workflow.core import IWorkflow


class IWorkflowTemplate(ABC):
    """工作流模板接口
    
    定义工作流模板的基础接口。
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """模板名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """模板描述"""
        pass
    
    @property
    @abstractmethod
    def category(self) -> str:
        """模板类别"""
        pass
    
    @property
    @abstractmethod
    def version(self) -> str:
        """模板版本"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数列表
        
        Returns:
            List[Dict[str, Any]]: 参数列表
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def create_workflow(self, name: str, description: str, config: Dict[str, Any]) -> "IWorkflow":
        """使用模板创建工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
            config: 配置参数
            
        Returns:
            IWorkflow: 创建的工作流实例
        """
        pass


class IPromptIntegratedTemplate(ABC):
    """提示词集成模板接口
    
    为需要提示词注入功能的模板提供统一接口。
    """
    
    @abstractmethod
    def set_prompt_injector(self, injector: IPromptInjector) -> None:
        """设置提示词注入器
        
        Args:
            injector: 提示词注入器实例
        """
        pass
    
    @abstractmethod
    def get_prompt_injector(self) -> Optional[IPromptInjector]:
        """获取提示词注入器
        
        Returns:
            Optional[IPromptInjector]: 提示词注入器实例
        """
        pass
    
    @abstractmethod
    def create_prompt_config(self, config: Dict[str, Any]) -> PromptConfig:
        """从配置创建提示词配置
        
        Args:
            config: 工作流配置
            
        Returns:
            PromptConfig: 提示词配置
        """
        pass
    
    @abstractmethod
    def get_default_prompt_config(self) -> PromptConfig:
        """获取默认提示词配置
        
        Returns:
            PromptConfig: 默认提示词配置
        """
        pass


class IWorkflowTemplateFactory(ABC):
    """工作流模板工厂接口
    
    提供创建工作流模板的统一接口。
    """
    
    @abstractmethod
    def create_template(self, template_name: str, **kwargs: Any) -> Any:
        """创建工作流模板
        
        Args:
            template_name: 模板名称
            **kwargs: 模板参数
            
        Returns:
            Any: 工作流模板实例
        """
        pass
    
    @abstractmethod
    def list_available_templates(self) -> List[str]:
        """列出可用的模板
        
        Returns:
            List[str]: 可用模板名称列表
        """
        pass
    
    @abstractmethod
    def get_template_info(self, template_name: str) -> Dict[str, Any]:
        """获取模板信息
        
        Args:
            template_name: 模板名称
            
        Returns:
            Dict[str, Any]: 模板信息
        """
        pass


class IWorkflowTemplateRegistry(ABC):
    """工作流模板注册表接口
    
    管理工作流模板的注册、获取和查询。
    """
    
    @abstractmethod
    def register_template(self, template: IWorkflowTemplate) -> None:
        """注册工作流模板
        
        Args:
            template: 工作流模板实例
        """
        pass
    
    @abstractmethod
    def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
        """获取工作流模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[IWorkflowTemplate]: 工作流模板实例
        """
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """列出所有工作流模板
        
        Returns:
            List[str]: 工作流模板名称列表
        """
        pass
    
    @abstractmethod
    def unregister_template(self, name: str) -> bool:
        """注销工作流模板
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 是否成功注销
        """
        pass
