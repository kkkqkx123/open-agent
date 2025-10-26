"""Workflow相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from src.infrastructure.graph.config import WorkflowConfig


class IWorkflowBuilder(ABC):
    """工作流构建器接口"""
    
    @abstractmethod
    def build_from_config(self, config: WorkflowConfig) -> Any:
        """从配置构建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            编译后的工作流
        """
        pass
    
    @abstractmethod
    def build_from_template(self, template_name: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """从模板构建工作流
        
        Args:
            template_name: 模板名称
            config: 覆盖配置（可选）
            
        Returns:
            编译后的工作流
        """
        pass


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
    
    @abstractmethod
    def create_template(self, config: Dict[str, Any]) -> WorkflowConfig:
        """创建模板实例
        
        Args:
            config: 配置参数
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> List[Dict[str, Any]]:
        """获取模板参数定义
        
        Returns:
            List[Dict[str, Any]]: 参数定义列表
        """
        pass
    
    @abstractmethod
    def validate_parameters(self, config: Dict[str, Any]) -> List[str]:
        """验证参数
        
        Args:
            config: 参数配置
            
        Returns:
            List[str]: 验证错误列表
        """
        pass


class IWorkflowTemplateRegistry(ABC):
    """工作流模板注册表接口"""
    
    @abstractmethod
    def register_template(self, template: IWorkflowTemplate) -> None:
        """注册模板
        
        Args:
            template: 模板实例
        """
        pass
    
    @abstractmethod
    def get_template(self, name: str) -> Optional[IWorkflowTemplate]:
        """获取模板
        
        Args:
            name: 模板名称
            
        Returns:
            Optional[IWorkflowTemplate]: 模板实例
        """
        pass
    
    @abstractmethod
    def list_templates(self) -> List[str]:
        """列出所有模板
        
        Returns:
            List[str]: 模板名称列表
        """
        pass
    
    @abstractmethod
    def unregister_template(self, name: str) -> bool:
        """注销模板
        
        Args:
            name: 模板名称
            
        Returns:
            bool: 是否成功注销
        """
        pass


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""
    
    @abstractmethod
    async def execute(self, workflow: Any, initial_state: Any, config: Dict[str, Any]) -> Any:
        """执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 执行配置
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def stream_execute(self, workflow: Any, initial_state: Any, config: Dict[str, Any]):
        """流式执行工作流
        
        Args:
            workflow: 工作流实例
            initial_state: 初始状态
            config: 执行配置
            
        Yields:
            执行结果
        """
        pass


class IWorkflowValidator(ABC):
    """工作流验证器接口"""
    
    @abstractmethod
    def validate_config(self, config: WorkflowConfig) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def validate_workflow(self, workflow: Any) -> List[str]:
        """验证工作流实例
        
        Args:
            workflow: 工作流实例
            
        Returns:
            List[str]: 验证错误列表
        """
        pass