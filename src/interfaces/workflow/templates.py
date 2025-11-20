"""Workflow template interfaces.

This module contains interfaces related to workflow templates.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

from .core import IWorkflow


class IWorkflowTemplate(ABC):
    """工作流模板接口"""
    
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
    def create_workflow(self, name: str, description: str, config: Dict[str, Any]) -> IWorkflow:
        """从模板创建工作流"""
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义"""
        pass
    
    @abstractmethod
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数"""
        pass


class IWorkflowTemplateRegistry(ABC):
    """工作流模板注册表接口"""
    
    @abstractmethod
    def register_template(self, template: IWorkflowTemplate) -> None:
        """注册模板"""
        pass
    
    @abstractmethod
    def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
        """获取模板"""
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """列出所有模板"""
        pass
    
    @abstractmethod
    def unregister_template(self, name: str) -> bool:
        """注销模板"""
        pass
    
    @abstractmethod
    def validate_template_config(self, template_name: str, config: Dict[str, Any]) -> List[str]:
        """验证模板配置"""
        pass
    
    @abstractmethod
    def create_workflow_from_template(self, template_name: str, name: str, 
                                     description: str, config: Dict[str, Any]) -> IWorkflow:
        """使用模板创建工作流"""
        pass
    
    @abstractmethod
    def search_templates(self, keyword: str) -> List[str]:
        """搜索模板"""
        pass
    
    @abstractmethod
    def get_templates_by_category(self, category: str) -> List[str]:
        """根据类别获取模板"""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有模板"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息"""
        pass