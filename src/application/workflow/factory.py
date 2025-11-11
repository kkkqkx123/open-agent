"""工作流工厂

提供工作流实例的创建和管理功能。
"""

from typing import Dict, Any, Optional, Type
from abc import ABC, abstractmethod
import logging

from .interfaces import IWorkflowFactory, IWorkflowManager
from ...infrastructure.graph.states import WorkflowState
from ...infrastructure.graph.config import WorkflowConfig
from ...infrastructure.config_loader import IConfigLoader
from ...infrastructure.container import IDependencyContainer

logger = logging.getLogger(__name__)


class WorkflowFactory(IWorkflowFactory):
    """工作流工厂实现"""
    
    def __init__(
        self,
        container: Optional[IDependencyContainer] = None,
        config_loader: Optional[IConfigLoader] = None
    ):
        """初始化工作流工厂
        
        Args:
            container: 依赖注入容器
            config_loader: 配置加载器
        """
        self.container = container
        self.config_loader = config_loader
        self._workflow_types: Dict[str, Type] = {}
        
        # 注册内置工作流类型
        self._register_builtin_workflows()
    
    def create_workflow(self, config: WorkflowConfig) -> Any:
        """创建工作流实例

        Args:
            config: 工作流配置

        Returns:
            工作流实例
        """
        # 从配置中推断工作流类型
        # 首先尝试从additional_config中获取类型
        workflow_type = config.additional_config.get('workflow_type')

        # 如果没有，则从名称中推断
        if not workflow_type:
            name = config.name.lower()
            if 'react' in name:
                workflow_type = 'react'
            elif 'plan_execute' in name or 'plan' in name:
                workflow_type = 'plan_execute'
            else:
                workflow_type = 'base'

        if workflow_type not in self._workflow_types:
            raise ValueError(f"未知的工作流类型: {workflow_type}")

        workflow_class = self._workflow_types[workflow_type]

        return workflow_class(config, self.config_loader, self.container)
    
    def register_workflow_type(self, workflow_type: str, workflow_class: Type) -> None:
        """注册工作流类型
        
        Args:
            workflow_type: 工作流类型名称
            workflow_class: 工作流类
        """
        self._workflow_types[workflow_type] = workflow_class
        logger.debug(f"注册工作流类型: {workflow_type}")
    
    def get_supported_types(self) -> list:
        """获取支持的工作流类型列表
        
        Returns:
            list: 工作流类型列表
        """
        return list(self._workflow_types.keys())
    
    def _register_builtin_workflows(self) -> None:
        """注册内置工作流类型"""
        try:
            # 注册基础工作流
            from .base_workflow import BaseWorkflow
            self.register_workflow_type("base", BaseWorkflow)
            
            logger.debug("内置工作流类型注册完成")
        except ImportError as e:
            logger.warning(f"部分内置工作流类型不可用: {e}")
    
    def load_workflow_config(self, config_path: str) -> WorkflowConfig:
        """加载工作流配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            WorkflowConfig: 工作流配置
        """
        if not self.config_loader:
            raise ValueError("配置加载器未初始化")
        
        # 使用配置加载器加载YAML配置文件
        import yaml
        from pathlib import Path
        
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 转换为WorkflowConfig对象
        return WorkflowConfig.from_dict(config_data)


class BaseWorkflow:
    """基础工作流类"""
    
    def __init__(self, config: Dict[str, Any], config_loader: IConfigLoader, container: IDependencyContainer):
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


class ReActWorkflow(BaseWorkflow):
    """ReAct工作流"""
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行ReAct工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # ReAct工作流的实现逻辑
        # 这里应该实现ReAct算法的具体步骤
        
        # 确保状态中有必要的字段
        if "iteration_count" not in state:
            state["iteration_count"] = 0
        if "max_iterations" not in state:
            state["max_iterations"] = self.config.get("max_iterations", 10)
        
        # 简化的ReAct实现
        state["iteration_count"] += 1
        
        return state


class PlanExecuteWorkflow(BaseWorkflow):
    """计划执行工作流"""
    
    def execute(self, state: WorkflowState) -> WorkflowState:
        """执行计划执行工作流
        
        Args:
            state: 工作流状态
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 计划执行工作流的实现逻辑
        # 这里应该实现计划执行算法的具体步骤
        
        # 确保状态中有必要的字段
        if "context" not in state:
            state["context"] = {}
        
        # 简化的计划执行实现
        context = state["context"]
        if "current_plan" not in context:
            # 生成初始计划
            context["current_plan"] = [
                "分析用户需求",
                "制定执行计划",
                "执行计划步骤",
                "总结结果"
            ]
            context["current_step_index"] = 0
        
        return state