"""工作流相关接口定义"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from ...infrastructure.graph.config import WorkflowConfig


class IWorkflowConfigManager(ABC):
    """工作流配置管理器接口"""
    
    @abstractmethod
    def load_config(self, config_path: str) -> str:
        """加载工作流配置"""
        pass
    
    @abstractmethod
    def get_config(self, config_id: str) -> Optional[WorkflowConfig]:
        """获取工作流配置"""
        pass
    
    @abstractmethod
    def validate_config(self, config: WorkflowConfig) -> bool:
        """验证工作流配置"""
        pass
    
    @abstractmethod
    def get_config_metadata(self, config_id: str) -> Optional[Dict[str, Any]]:
        """获取配置元数据"""
        pass
    
    @abstractmethod
    def list_configs(self) -> List[str]:
        """列出所有已加载的配置"""
        pass
    
    @abstractmethod
    def reload_config(self, config_id: str) -> bool:
        """重新加载配置"""
        pass


class IWorkflowVisualizer(ABC):
    """工作流可视化器接口"""
    
    @abstractmethod
    def generate_visualization(self, config: WorkflowConfig) -> Dict[str, Any]:
        """生成可视化数据"""
        pass
    
    @abstractmethod
    def export_diagram(self, config: WorkflowConfig, format: str) -> bytes:
        """导出图表"""
        pass


class IWorkflowRegistry(ABC):
    """工作流注册表接口"""
    
    @abstractmethod
    def register_workflow(self, workflow_def: Dict[str, Any]) -> str:
        """注册工作流定义"""
        pass
    
    @abstractmethod
    def get_workflow_definition(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """获取工作流定义"""
        pass
    
    @abstractmethod
    def list_available_workflows(self) -> List[Dict[str, Any]]:
        """列出可用工作流"""
        pass