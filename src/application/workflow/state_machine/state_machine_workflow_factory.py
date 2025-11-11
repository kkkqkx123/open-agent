"""状态机工作流工厂

负责创建和管理基于状态机的工作流实例。
"""

from typing import Dict, Any, Optional, Type
import logging

from ..interfaces import IWorkflowFactory
from .state_machine_workflow import StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
from ....infrastructure.graph.config import WorkflowConfig
from ....infrastructure.config_loader import IConfigLoader
from ....infrastructure.container import IDependencyContainer

logger = logging.getLogger(__name__)


class StateMachineWorkflowFactory(IWorkflowFactory):
    """状态机工作流工厂"""
    
    def __init__(
        self,
        config_loader: Optional[IConfigLoader] = None,
        container: Optional[IDependencyContainer] = None
    ):
        """初始化工厂
        
        Args:
            config_loader: 配置加载器
            container: 依赖注入容器
        """
        self.config_loader = config_loader
        self.container = container
        self._workflow_classes: Dict[str, Type[StateMachineWorkflow]] = {}
    
    def create_workflow(
        self, 
        config: WorkflowConfig,
        state_machine_config: Optional[StateMachineConfig] = None
    ) -> Any:
        """创建工作流实例
        
        Args:
            config: 工作流配置
            state_machine_config: 可选的状态机配置，如果为None则自动创建
            
        Returns:
            工作流实例
        """
        # 从配置中获取工作流名称
        workflow_name = config.name
        
        # 获取工作流类
        workflow_class = self._workflow_classes.get(workflow_name)
        if workflow_class is None:
            raise ValueError(f"未注册的工作流: {workflow_name}")
        
        # 创建状态机配置（如果未提供）
        if state_machine_config is None:
            state_machine_config = self._create_state_machine_config(workflow_name, config)
        
        # 创建工作流实例
        return workflow_class(
            config=config,
            state_machine_config=state_machine_config,
            config_loader=self.config_loader,
            container=self.container
        )
    
    def register_workflow_type(self, workflow_type: str, workflow_class: Type) -> None:
        """注册工作流类型
        
        Args:
            workflow_type: 工作流类型名称
            workflow_class: 工作流类
        """
        self._workflow_classes[workflow_type] = workflow_class
        logger.info(f"已注册状态机工作流类型: {workflow_type}")
    
    def get_supported_types(self) -> list:
        """获取支持的工作流类型列表
        
        Returns:
            list: 工作流类型列表
        """
        return list(self._workflow_classes.keys())
    
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
    
    def register_workflow(
        self,
        workflow_name: str,
        workflow_class: Type[StateMachineWorkflow]
    ) -> None:
        """注册工作流类
        
        Args:
            workflow_name: 工作流名称
            workflow_class: 工作流类
        """
        self._workflow_classes[workflow_name] = workflow_class
        logger.info(f"已注册状态机工作流: {workflow_name}")
    
    def unregister_workflow(self, workflow_name: str) -> None:
        """注销工作流类
        
        Args:
            workflow_name: 工作流名称
        """
        if workflow_name in self._workflow_classes:
            del self._workflow_classes[workflow_name]
            logger.info(f"已注销状态机工作流: {workflow_name}")
    
    def get_registered_workflows(self) -> Dict[str, Type[StateMachineWorkflow]]:
        """获取已注册的工作流
        
        Returns:
            Dict[str, Type[StateMachineWorkflow]]: 已注册的工作流字典
        """
        return self._workflow_classes.copy()
    
    def _create_state_machine_config(
        self,
        workflow_name: str,
        config: Optional[WorkflowConfig]
    ) -> StateMachineConfig:
        """创建状态机配置
        
        Args:
            workflow_name: 工作流名称
            config: 工作流配置
            
        Returns:
            StateMachineConfig: 状态机配置
        """
        # 这里可以根据工作流名称和配置创建特定的状态机配置
        # 实际项目中应该从配置文件或数据库加载
        
        if workflow_name == "deep_thinking":
            return self._create_deep_thinking_config()
        elif workflow_name == "ultra_thinking":
            return self._create_ultra_thinking_config()
        else:
            # 默认配置
            return StateMachineConfig(
                name=workflow_name,
                description=f"{workflow_name} 状态机工作流",
                version="1.0.0",
                initial_state="start"
            )
    
    def _create_deep_thinking_config(self) -> StateMachineConfig:
        """创建深度思考工作流的状态机配置"""
        config = StateMachineConfig(
            name="deep_thinking",
            description="深度思考工作流状态机",
            version="1.0.0",
            initial_state="initial"
        )
        
        # 定义状态
        states = [
            StateDefinition("initial", StateType.START, description="初始状态"),
            StateDefinition("problem_analysis", StateType.PROCESS, description="问题分析"),
            StateDefinition("plan_generation", StateType.PROCESS, description="计划生成"),
            StateDefinition("deep_thinking", StateType.PROCESS, description="深度思考"),
            StateDefinition("solution_validation", StateType.PROCESS, description="方案验证"),
            StateDefinition("final", StateType.END, description="最终状态")
        ]
        
        # 添加状态
        for state in states:
            config.add_state(state)
        
        # 定义转移
        initial_state = config.get_state("initial")
        if initial_state:
            initial_state.add_transition(Transition("problem_analysis"))
        
        problem_state = config.get_state("problem_analysis")
        if problem_state:
            problem_state.add_transition(Transition("plan_generation"))
        
        plan_state = config.get_state("plan_generation")
        if plan_state:
            plan_state.add_transition(Transition("deep_thinking"))
        
        thinking_state = config.get_state("deep_thinking")
        if thinking_state:
            thinking_state.add_transition(Transition("solution_validation"))
        
        validation_state = config.get_state("solution_validation")
        if validation_state:
            validation_state.add_transition(Transition("final"))
        
        return config
    
    def _create_ultra_thinking_config(self) -> StateMachineConfig:
        """创建超思考工作流的状态机配置"""
        config = StateMachineConfig(
            name="ultra_thinking",
            description="超思考工作流状态机",
            version="1.0.0",
            initial_state="initial"
        )
        
        # 定义状态
        states = [
            StateDefinition("initial", StateType.START, description="初始状态"),
            StateDefinition("problem_analysis", StateType.PROCESS, description="问题分析"),
            StateDefinition("plan_generation", StateType.PROCESS, description="计划生成"),
            StateDefinition("ultra_thinking", StateType.PROCESS, description="超思考"),
            StateDefinition("solution_validation", StateType.PROCESS, description="方案验证"),
            StateDefinition("final", StateType.END, description="最终状态")
        ]
        
        # 添加状态
        for state in states:
            config.add_state(state)
        
        # 定义转移
        initial_state = config.get_state("initial")
        if initial_state:
            initial_state.add_transition(Transition("problem_analysis"))
        
        problem_state = config.get_state("problem_analysis")
        if problem_state:
            problem_state.add_transition(Transition("plan_generation"))
        
        plan_state = config.get_state("plan_generation")
        if plan_state:
            plan_state.add_transition(Transition("ultra_thinking"))
        
        ultra_state = config.get_state("ultra_thinking")
        if ultra_state:
            ultra_state.add_transition(Transition("solution_validation"))
        
        validation_state = config.get_state("solution_validation")
        if validation_state:
            validation_state.add_transition(Transition("final"))
        
        return config


class StateMachineConfigLoader:
    """状态机配置加载器
    
    负责从YAML配置文件加载状态机配置。
    """
    
    @staticmethod
    def load_from_yaml(file_path: str) -> StateMachineConfig:
        """从YAML文件加载状态机配置
        
        Args:
            file_path: YAML文件路径
            
        Returns:
            StateMachineConfig: 状态机配置
        """
        import yaml
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return StateMachineConfigLoader._parse_config(data)
    
    @staticmethod
    def _parse_config(data: Dict[str, Any]) -> StateMachineConfig:
        """解析配置数据
        
        Args:
            data: 配置数据
            
        Returns:
            StateMachineConfig: 状态机配置
        """
        config = StateMachineConfig(
            name=data.get('name', 'unnamed'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            initial_state=data.get('initial_state', 'initial')
        )
        
        # 解析状态
        states_data = data.get('states', {})
        for state_name, state_data in states_data.items():
            state_type = StateType(state_data.get('type', 'process'))
            state_def = StateDefinition(
                name=state_name,
                state_type=state_type,
                handler=state_data.get('handler'),
                description=state_data.get('description', ''),
                config=state_data.get('config', {})
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
            
            config.add_state(state_def)
        
        return config


# 全局工厂实例
_state_machine_factory: Optional[StateMachineWorkflowFactory] = None


def get_state_machine_factory() -> StateMachineWorkflowFactory:
    """获取全局状态机工作流工厂实例
    
    Returns:
        StateMachineWorkflowFactory: 工厂实例
    """
    global _state_machine_factory
    if _state_machine_factory is None:
        _state_machine_factory = StateMachineWorkflowFactory()
    return _state_machine_factory


def register_state_machine_workflow(
    workflow_name: str,
    workflow_class: Type[StateMachineWorkflow]
) -> None:
    """注册状态机工作流
    
    Args:
        workflow_name: 工作流名称
        workflow_class: 工作流类
    """
    factory = get_state_machine_factory()
    factory.register_workflow(workflow_name, workflow_class)


def create_state_machine_workflow(
    config: WorkflowConfig,
    state_machine_config: Optional[StateMachineConfig] = None,
    **kwargs
) -> StateMachineWorkflow:
    """创建状态机工作流实例
    
    Args:
        config: 工作流配置
        state_machine_config: 状态机配置
        **kwargs: 额外参数
        
    Returns:
        StateMachineWorkflow: 工作流实例
    """
    factory = get_state_machine_factory()
    return factory.create_workflow(config, state_machine_config)