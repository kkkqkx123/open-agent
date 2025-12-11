"""工作流组合和拼接接口定义

定义工作流组合和拼接的核心接口，提供类型定义和抽象基类。
遵循分层架构原则，interface层只定义接口，不依赖其他层。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from .core import IWorkflow
    from .config import IGraphConfig

from ..common_domain import IValidationResult


class CompositionStrategyType(Enum):
    """组合策略类型枚举"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    LOOP = "loop"


class IWorkflowComposition(ABC):
    """工作流组合接口"""
    
    @abstractmethod
    def compose_workflows(self, workflow_configs: List['IGraphConfig']) -> 'IGraphConfig':
        """组合多个工作流配置
        
        Args:
            workflow_configs: 工作流配置列表
            
        Returns:
            IGraphConfig: 组合后的工作流配置
        """
        pass


class IWorkflowStitching(ABC):
    """工作流拼接接口"""
    
    @abstractmethod
    def stitch_workflows(self, workflows: List['IWorkflow']) -> 'IWorkflow':
        """拼接多个工作流实例
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 拼接后的工作流实例
        """
        pass


class ICompositionStrategy(ABC):
    """组合策略接口"""
    
    @abstractmethod
    def execute(self, workflows: List['IWorkflow']) -> 'IWorkflow':
        """执行组合策略
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 组合后的工作流实例
        """
        pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> CompositionStrategyType:
        """策略类型"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """策略名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> Optional[str]:
        """策略描述"""
        pass


class IDataMapper(ABC):
    """数据映射接口"""
    
    @abstractmethod
    def map_input_data(self, source_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """映射输入数据
        
        Args:
            source_data: 源数据
            mapping_config: 映射配置
            
        Returns:
            Dict[str, Any]: 映射后的数据
        """
        pass
    
    @abstractmethod
    def map_output_data(self, source_data: Dict[str, Any], mapping_config: Dict[str, Any]) -> Dict[str, Any]:
        """映射输出数据
        
        Args:
            source_data: 源数据
            mapping_config: 映射配置
            
        Returns:
            Dict[str, Any]: 映射后的数据
        """
        pass
    
    @abstractmethod
    def validate_mapping_config(self, mapping_config: Dict[str, Any]) -> ValidationResult:
        """验证映射配置
        
        Args:
            mapping_config: 映射配置
            
        Returns:
            ValidationResult: 验证结果
        """
        pass


class IWorkflowCompositionManager(ABC):
    """工作流组合管理器接口"""
    
    @abstractmethod
    def create_composition(self, composition_config: Dict[str, Any]) -> 'IWorkflow':
        """创建组合工作流
        
        Args:
            composition_config: 组合配置
            
        Returns:
            IWorkflow: 组合工作流实例
        """
        pass
    
    @abstractmethod
    def get_strategy(self, strategy_type: CompositionStrategyType) -> ICompositionStrategy:
        """获取组合策略
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            ICompositionStrategy: 组合策略实例
        """
        pass
    
    @abstractmethod
    def register_strategy(self, strategy: ICompositionStrategy) -> None:
        """注册组合策略
        
        Args:
            strategy: 组合策略实例
        """
        pass
    
    @abstractmethod
    def list_strategies(self) -> List[CompositionStrategyType]:
        """列出所有可用的策略类型
        
        Returns:
            List[CompositionStrategyType]: 策略类型列表
        """
        pass


class IWorkflowCompositionOrchestrator(ABC):
    """工作流组合编排器接口"""
    
    @abstractmethod
    def orchestrate_composition(self, composition: 'IWorkflow', initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """编排组合工作流执行
        
        Args:
            composition: 组合工作流实例
            initial_state: 初始状态
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        pass
    
    @abstractmethod
    def handle_composition_error(self, error: Exception, composition: 'IWorkflow') -> None:
        """处理组合错误
        
        Args:
            error: 错误实例
            composition: 组合工作流实例
        """
        pass
    
    @abstractmethod
    def get_composition_status(self, composition: 'IWorkflow') -> Dict[str, Any]:
        """获取组合状态
        
        Args:
            composition: 组合工作流实例
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        pass


# 导出接口
__all__ = [
    "CompositionStrategyType",
    "IWorkflowComposition",
    "IWorkflowStitching", 
    "ICompositionStrategy",
    "IDataMapper",
    "IWorkflowCompositionManager",
    "IWorkflowCompositionOrchestrator",
]