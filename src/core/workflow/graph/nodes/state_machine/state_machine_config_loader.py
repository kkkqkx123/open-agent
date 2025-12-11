"""状态机工作流配置加载器

提供便捷的状态机工作流配置文件加载功能，支持从单一配置文件创建完整的工作流实例。
"""

from typing import Dict, Any, Optional, Type
import yaml
from pathlib import Path
from src.interfaces.dependency_injection import get_logger

from .state_machine_workflow import StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
from .state_machine_workflow_factory import StateMachineWorkflowFactory
from .workflow_config import WorkflowConfig
from src.core.config.config_manager import get_default_manager, ConfigManager

logger = get_logger(__name__)


class StateMachineWorkflowLoader:
    """状态机工作流加载器
    
    提供一站式状态机工作流配置加载和实例创建功能。
    """
    
    def __init__(self, factory: Optional[StateMachineWorkflowFactory] = None, config_manager: Optional[ConfigManager] = None):
        """初始化加载器
         
        Args:
            factory: 状态机工作流工厂，如果为None则使用全局工厂
            config_manager: 配置管理器，如果为None则使用默认管理器
        """
        self.factory = factory or StateMachineWorkflowFactory()
        self.config_manager = config_manager or get_default_manager()
    
    def load_from_file(self, config_path: str) -> StateMachineWorkflow:
        """从配置文件加载并创建工作流实例
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            StateMachineWorkflow: 工作流实例
        """
        # 加载配置文件
        config_data = self._load_yaml_file(config_path)
        
        # 解析配置
        workflow_config, state_machine_config = self._parse_config(config_data)
        
        # 创建工作流类
        workflow_class = self._create_workflow_class(config_data, state_machine_config)
        
        # 注册工作流
        workflow_name = workflow_config.name
        self.factory.register_workflow_type(workflow_name, workflow_class)
        
        # 创建工作流实例
        return self.factory.create_workflow(workflow_config, state_machine_config)
    
    def load_from_dict(self, config_data: Dict[str, Any]) -> StateMachineWorkflow:
        """从字典配置加载并创建工作流实例
        
        Args:
            config_data: 配置字典
            
        Returns:
            StateMachineWorkflow: 工作流实例
        """
        # 解析配置
        workflow_config, state_machine_config = self._parse_config(config_data)
        
        # 创建工作流类
        workflow_class = self._create_workflow_class(config_data, state_machine_config)
        
        # 注册工作流
        workflow_name = workflow_config.name
        self.factory.register_workflow_type(workflow_name, workflow_class)
        
        # 创建工作流实例
        return self.factory.create_workflow(workflow_config)
    
    def _load_yaml_file(self, config_path: str) -> Dict[str, Any]:
        """加载YAML配置文件
         
        Args:
            config_path: 配置文件路径
             
        Returns:
            Dict[str, Any]: 配置数据
        """
        # 使用统一配置管理器加载
        return self.config_manager.load_config_for_module(config_path, "workflow")
    
    def _parse_config(self, config_data: Dict[str, Any]) -> tuple:
        """解析配置数据
        
        Args:
            config_data: 配置数据
            
        Returns:
            tuple: (WorkflowConfig, StateMachineConfig)
        """
        # 解析工作流配置
        workflow_config = WorkflowConfig.from_dict(config_data)
        
        # 解析状态机配置
        state_machine_config = self._parse_state_machine_config(config_data)
        
        return workflow_config, state_machine_config
    
    def _parse_state_machine_config(self, config_data: Dict[str, Any]) -> StateMachineConfig:
        """解析状态机配置
        
        Args:
            config_data: 配置数据
            
        Returns:
            StateMachineConfig: 状态机配置
        """
        # 创建状态机配置
        state_machine_config = StateMachineConfig(
            name=config_data.get('name', 'unnamed'),
            description=config_data.get('description', ''),
            version=config_data.get('version', '1.0.0'),
            initial_state=config_data.get('initial_state', 'start')
        )
        
        # 解析状态定义
        states_data = config_data.get('states', {})
        for state_name, state_data in states_data.items():
            state_type = StateType(state_data.get('type', 'process'))
            
            state_def = StateDefinition(
                name=state_name,
                state_type=state_type,
                description=state_data.get('description', '')
            )
            
            # 解析转移
            transitions_data = state_data.get('transitions', [])
            for trans_data in transitions_data:
                transition = Transition(
                    target_state=trans_data.get('target'),
                    condition=trans_data.get('condition'),
                    description=trans_data.get('description', '')
                )
                state_def.add_transition(transition)
            
            state_machine_config.add_state(state_def)
        
        return state_machine_config
    
    def _create_workflow_class(
        self, 
        config_data: Dict[str, Any], 
        state_machine_config: StateMachineConfig
    ) -> Type[StateMachineWorkflow]:
        """创建动态工作流类
        
        Args:
            config_data: 配置数据
            state_machine_config: 状态机配置
            
        Returns:
            Type[StateMachineWorkflow]: 工作流类
        """
        workflow_name = config_data.get('name', 'UnnamedWorkflow')
        
        # 创建动态类
        class DynamicStateMachineWorkflow(StateMachineWorkflow):
            """动态生成的状态机工作流类"""
            
            def __init__(self, config: WorkflowConfig, **kwargs):
                """初始化动态工作流
                
                Args:
                    config: 工作流配置
                    **kwargs: 额外参数
                """
                # 工厂会处理state_machine_config参数，这里不需要重复传递
                super().__init__(config, **kwargs)
        
        # 为每个状态添加处理方法
        states_data = config_data.get('states', {})
        for state_name, state_data in states_data.items():
            handler_name = f"handle_{state_name}"
            
            # 创建状态处理方法
            def create_state_handler(state_name):
                def state_handler(self, state: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
                    """状态处理方法"""
                    # 默认处理逻辑：记录状态执行
                    state[f"{state_name}_executed"] = True
                    state["current_state"] = state_name
                    
                    # 如果有自定义处理逻辑，可以在这里添加
                    handler_config = config.get('handler_config', {})
                    if handler_config:
                        state.update(handler_config)
                    
                    return state
                
                return state_handler
            
            # 为动态类添加状态处理方法
            setattr(DynamicStateMachineWorkflow, handler_name, create_state_handler(state_name))
        
        # 设置类名
        DynamicStateMachineWorkflow.__name__ = f"{workflow_name}Workflow"
        DynamicStateMachineWorkflow.__qualname__ = f"{workflow_name}Workflow"
        
        return DynamicStateMachineWorkflow


# 便捷函数
def load_state_machine_workflow(config_path: str) -> StateMachineWorkflow:
    """从配置文件加载状态机工作流
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        StateMachineWorkflow: 工作流实例
    """
    loader = StateMachineWorkflowLoader()
    return loader.load_from_file(config_path)

def create_state_machine_workflow_from_dict(config_data: Dict[str, Any]) -> StateMachineWorkflow:
    """从字典配置创建状态机工作流
    
    Args:
        config_data: 配置字典
        
    Returns:
        StateMachineWorkflow: 工作流实例
    """
    loader = StateMachineWorkflowLoader()
    return loader.load_from_dict(config_data)