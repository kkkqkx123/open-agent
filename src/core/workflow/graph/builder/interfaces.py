"""图构建器接口定义

定义核心图构建器的统一接口，确保架构层次清晰和依赖倒置。
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, TYPE_CHECKING
from src.core.workflow.config.config import GraphConfig

if TYPE_CHECKING:
    from src.core.workflow.graph.builder.validator import ValidationResult


class IGraphBuilder(ABC):
    """图构建器接口
    
    定义图构建的核心接口，由核心层实现，服务层依赖。
    """
    
    @abstractmethod
    def build_graph(self, config: GraphConfig) -> Any:
        """构建图
        
        Args:
            config: 图配置
            
        Returns:
            构建好的图实例
        """
        pass
    
    @abstractmethod
    def validate_config(self, config: GraphConfig) -> "ValidationResult":
        """验证配置
        
        Args:
            config: 图配置
            
        Returns:
            验证结果
        """
        pass
    
    @abstractmethod
    def get_supported_node_types(self) -> List[str]:
        """获取支持的节点类型
        
        Returns:
            支持的节点类型列表
        """
        pass
    
    @abstractmethod
    def get_supported_edge_types(self) -> List[str]:
        """获取支持的边类型
        
        Returns:
            支持的边类型列表
        """
        pass


class INodeExecutor(ABC):
    """节点执行器接口
    
    定义节点执行的统一接口，支持不同类型的节点执行策略。
    """
    
    @abstractmethod
    def execute_node(
        self, 
        node_config: Any, 
        state: Any, 
        config: Optional[Dict[str, Any]] = None
    ) -> Any:
        """执行节点
        
        Args:
            node_config: 节点配置
            state: 当前状态
            config: 执行配置
            
        Returns:
            执行结果
        """
        pass
    
    @abstractmethod
    def can_execute(self, node_type: str) -> bool:
        """检查是否可以执行指定类型的节点
        
        Args:
            node_type: 节点类型
            
        Returns:
            是否可以执行
        """
        pass
    
    @abstractmethod
    def get_execution_metadata(self) -> Dict[str, Any]:
        """获取执行器元数据
        
        Returns:
            执行器元数据
        """
        pass


class IGraphCompiler(ABC):
    """图编译器接口
    
    定义图编译的统一接口，支持不同的图编译策略。
    """
    
    @abstractmethod
    def compile(
        self, 
        graph: Any, 
        checkpointer: Optional[Any] = None,
        interrupt_before: Optional[List[str]] = None,
        interrupt_after: Optional[List[str]] = None
    ) -> Any:
        """编译图
        
        Args:
            graph: 图实例
            checkpointer: 检查点保存器
            interrupt_before: 在指定节点前中断
            interrupt_after: 在指定节点后中断
            
        Returns:
            编译后的图
        """
        pass
    
    @abstractmethod
    def get_compilation_options(self) -> Dict[str, Any]:
        """获取编译选项
        
        Returns:
            编译选项
        """
        pass


class IWorkflowBuilder(ABC):
    """工作流构建器接口
    
    定义工作流构建的统一接口，整合图构建和工作流创建。
    """
    
    @abstractmethod
    def build_workflow(self, config: Dict[str, Any]) -> Any:
        """构建工作流
        
        Args:
            config: 工作流配置
            
        Returns:
            构建的工作流
        """
        pass
    
    @abstractmethod
    def validate_workflow_config(self, config: Dict[str, Any]) -> List[str]:
        """验证工作流配置
        
        Args:
            config: 工作流配置
            
        Returns:
            验证错误列表
        """
        pass
    
    @abstractmethod
    def get_workflow_schema(self) -> Dict[str, Any]:
        """获取工作流配置模式
        
        Returns:
            配置模式
        """
        pass