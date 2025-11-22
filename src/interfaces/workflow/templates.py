"""工作流模板接口定义

为工作流模板系统提供统一的接口定义。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ...interfaces.prompts import IPromptInjector, PromptConfig


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


class IPromptTemplateRegistry(ABC):
    """提示词模板注册表接口
    
    管理提示词相关模板的注册和获取。
    """
    
    @abstractmethod
    def register_prompt_template(self, template: Any) -> None:
        """注册提示词模板
        
        Args:
            template: 提示词模板实例
        """
        pass
    
    @abstractmethod
    def get_prompt_template(self, template_name: str) -> Optional[Any]:
        """获取提示词模板
        
        Args:
            template_name: 模板名称
            
        Returns:
            Optional[Any]: 提示词模板实例
        """
        pass
    
    @abstractmethod
    def list_prompt_templates(self) -> List[str]:
        """列出所有提示词模板
        
        Returns:
            List[str]: 提示词模板名称列表
        """
        pass