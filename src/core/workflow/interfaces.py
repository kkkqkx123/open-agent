"""工作流核心接口

定义工作流系统的核心接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncIterator
from dataclasses import dataclass

from .graph.interfaces import IGraph, INode, IEdge
from src.state.interfaces import IState, IWorkflowState

# 需要延迟导入避免循环依赖
try:
    from .config import GraphConfig
except ImportError:
    GraphConfig = Any  # type: ignore


@dataclass
class ExecutionContext:
    """执行上下文"""
    workflow_id: str
    execution_id: str
    metadata: Dict[str, Any]
    config: Dict[str, Any]


class IWorkflow(ABC):
    """工作流接口"""

    @property
    @abstractmethod
    def workflow_id(self) -> str:
        """工作流ID"""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """工作流名称"""
        pass

    @property
    @abstractmethod
    def _nodes(self) -> Dict[str, INode]:
        """工作流节点字典"""
        pass

    @property
    @abstractmethod
    def _edges(self) -> Dict[str, IEdge]:
        """工作流边字典"""
        pass

    @property
    @abstractmethod
    def _entry_point(self) -> Optional[str]:
        """工作流入口点"""
        pass

    @abstractmethod
    def add_node(self, node: INode) -> None:
        """添加节点"""
        pass

    @abstractmethod
    def add_edge(self, edge: IEdge) -> None:
        """添加边"""
        pass

    @abstractmethod
    def get_node(self, node_id: str) -> Optional[INode]:
        """获取节点
        
        Args:
            node_id: 节点ID
            
        Returns:
            Optional[INode]: 节点实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def get_edge(self, edge_id: str) -> Optional[IEdge]:
        """获取边
        
        Args:
            edge_id: 边ID
            
        Returns:
            Optional[IEdge]: 边实例，如果不存在则返回None
        """
        pass

    @abstractmethod
    def validate(self) -> List[str]:
        """验证工作流"""
        pass

    @abstractmethod
    def execute(self, initial_state: IWorkflowState, context: ExecutionContext) -> IWorkflowState:
        """执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, initial_state: IWorkflowState, context: ExecutionContext) -> IWorkflowState:
        """异步执行工作流"""
        pass


class IWorkflowExecutor(ABC):
    """工作流执行器接口"""

    @abstractmethod
    def execute(self, workflow: IWorkflow, initial_state: IState, 
                context: ExecutionContext) -> IState:
        """执行工作流"""
        pass

    @abstractmethod
    async def execute_async(self, workflow: IWorkflow, initial_state: IState,
                           context: ExecutionContext) -> IState:
        """异步执行工作流"""
        pass

    @abstractmethod
    def execute_stream(self, workflow: IWorkflow, initial_state: IState,
                       context: ExecutionContext) -> List[Dict[str, Any]]:
        """流式执行工作流"""
        pass

    @abstractmethod
    async def execute_stream_async(self, workflow: IWorkflow, initial_state: IState,
                                  context: ExecutionContext) -> AsyncIterator[Dict[str, Any]]:
        """异步流式执行工作流"""
        pass


class IWorkflowBuilder(ABC):
    """工作流构建器接口"""

    @abstractmethod
    def create_workflow(self, config: Dict[str, Any]) -> IWorkflow:
        """创建工作流"""
        pass

    @abstractmethod
    def validate_config(self, config: Dict[str, Any]) -> List[str]:
        """验证配置"""
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
        """从模板创建工作流
        
        Args:
            name: 工作流名称
            description: 工作流描述
            config: 配置参数
            
        Returns:
            IWorkflow: 工作流实例
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
            Optional[IWorkflowTemplate]: 模板实例，如果不存在则返回None
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
    
    @abstractmethod
    def validate_template_config(self, template_name: str, config: Dict[str, Any]) -> List[str]:
        """验证模板配置
        
        Args:
            template_name: 模板名称
            config: 配置参数
            
        Returns:
            List[str]: 验证错误列表
        """
        pass
    
    @abstractmethod
    def create_workflow_from_template(self, template_name: str, name: str, 
                                     description: str, config: Dict[str, Any]) -> IWorkflow:
        """使用模板创建工作流
        
        Args:
            template_name: 模板名称
            name: 工作流名称
            description: 工作流描述
            config: 配置参数
            
        Returns:
            IWorkflow: 工作流实例
        """
        pass
    
    @abstractmethod
    def search_templates(self, keyword: str) -> List[str]:
        """搜索模板
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            List[str]: 匹配的模板名称列表
        """
        pass
    
    @abstractmethod
    def get_templates_by_category(self, category: str) -> List[str]:
        """根据类别获取模板
        
        Args:
            category: 模板类别
            
        Returns:
            List[str]: 模板名称列表
        """
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """清除所有模板"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """获取注册表统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        pass


    class IWorkflowVisualizer(ABC):
        """工作流可视化器接口
        
        提供工作流的可视化能力，包括图形化展示和多格式导出。
        """
    
    @abstractmethod
    def generate_visualization(self, config: Any, layout: str = "hierarchical") -> Dict[str, Any]:
        """生成可视化数据
        
        Args:
            config: 工作流配置
            layout: 布局算法（hierarchical, force_directed, circular）
            
        Returns:
            Dict[str, Any]: 可视化数据
        """
        pass
    
    @abstractmethod
    def export_diagram(self, config: Any, format: str = "json") -> bytes:
        """导出图表
        
        Args:
            config: 工作流配置
            format: 导出格式（json, svg, png, mermaid）
            
        Returns:
            bytes: 图表数据
        """
        pass