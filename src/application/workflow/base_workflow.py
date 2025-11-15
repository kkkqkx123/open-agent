"""基础工作流实现

提供所有工作流的基础功能和通用接口。
"""

from typing import Dict, Any, Optional
from abc import ABC

from src.infrastructure.graph.states import WorkflowState
from src.infrastructure.graph.config import WorkflowConfig
from infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.container import IDependencyContainer


class BaseWorkflow(ABC):
    """基础工作流类"""
    
    def __init__(
        self,
        config: WorkflowConfig,
        config_loader: Optional[IConfigLoader] = None,
        container: Optional[IDependencyContainer] = None
    ):
        """初始化基础工作流
        
        Args:
            config: 工作流配置
            config_loader: 配置加载器
            container: 依赖注入容器
        """
        self.config = config
        self.config_loader = config_loader
        self.container = container
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 基础实现，子类应该重写此方法
        return state
    
    def validate_config(self) -> list:
        """验证配置
        
        Returns:
            list: 验证错误列表
        """
        # 基础实现，子类可以重写此方法
        return []
    
    def invoke(self, state: WorkflowState, **kwargs) -> WorkflowState:
        """调用工作流（LangGraph兼容接口）
        
        Args:
            state: 工作流状态
            **kwargs: 其他参数
            
        Returns:
            WorkflowState: 更新后的状态
        """
        return self.execute(state)