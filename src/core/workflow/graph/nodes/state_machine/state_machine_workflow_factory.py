"""状态机工作流工厂

负责创建和管理基于状态机的工作流实例。
"""

from typing import Dict, Any, Optional, Type, Union
from src.interfaces.dependency_injection import get_logger

from .state_machine_workflow import StateMachineWorkflow, StateMachineConfig, StateDefinition, Transition, StateType
from .workflow_config import WorkflowConfig

logger = get_logger(__name__)


class StateMachineWorkflowFactory:
    """状态机工作流工厂"""
    
    def __init__(
        self,
        config_loader: Optional[Any] = None,
        container: Optional[Any] = None,
        registry_manager: Optional[Any] = None
    ):
        """初始化工厂
        
        Args:
            config_loader: 配置加载器
            container: 依赖注入容器
            registry_manager: 模块注册管理器
        """
        self.config_loader = config_loader
        self.container = container
        self.registry_manager = registry_manager
        
        # 工作流类注册表
        self._workflow_classes: Dict[str, Type[StateMachineWorkflow]] = {}
        
        # 初始化注册管理器
        if self.registry_manager:
            self._initialize_from_registry()
    
    def create_workflow(
        self, 
        config: Union[WorkflowConfig, Any],
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
        
        # 使用统一配置管理器加载
        from src.core.config.config_manager import get_default_manager
        config_manager = get_default_manager()
        config_data = config_manager.load_config_for_module(str(config_file), "workflow")
        
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
    
    def _initialize_from_registry(self) -> None:
        """从注册管理器初始化状态机工作流配置
        
        从模块注册管理器中加载状态机工作流配置信息。
        """
        if not self.registry_manager:
            logger.warning("注册管理器未初始化")
            return
        
        try:
            # 获取状态机配置
            state_machine_configs = self.registry_manager.get_state_machine_configs()
            
            # 注册状态机工作流类（使用通用的StateMachineWorkflow类）
            for config_name, config_data in state_machine_configs.items():
                try:
                    # 注册状态机工作流类
                    self.register_workflow(config_name, StateMachineWorkflow)
                    
                    logger.info(f"从注册表加载状态机工作流: {config_name}")
                    
                except Exception as e:
                    logger.error(f"加载状态机工作流失败: {config_name}, 错误: {e}")
            
            logger.info(f"从注册表初始化完成，加载了 {len(self._workflow_classes)} 个状态机工作流")
            
        except Exception as e:
            logger.error(f"从注册表初始化失败: {e}")
    
    def create_state_machine_from_registry(self, workflow_name: str) -> StateMachineWorkflow:
        """从注册表创建状态机工作流实例
        
        Args:
            workflow_name: 工作流名称
            
        Returns:
            StateMachineWorkflow: 工作流实例
            
        Raises:
            ValueError: 工作流不存在或创建失败
        """
        if not self.registry_manager:
            raise ValueError("注册管理器未初始化")
        
        # 获取状态机配置
        state_machine_configs = self.registry_manager.get_state_machine_configs()
        if workflow_name not in state_machine_configs:
            raise ValueError(f"状态机工作流配置不存在: {workflow_name}")
        
        # 创建状态机配置
        config_data = state_machine_configs[workflow_name]
        state_machine_config = StateMachineConfigLoader._parse_config(config_data)
        
        # 创建工作流配置
        workflow_config = WorkflowConfig(
            name=workflow_name,
            description=state_machine_config.description,
            additional_config={}
        )
        
        # 创建工作流实例
        return self.create_workflow(workflow_config, state_machine_config)
    
    def reload_from_registry(self) -> None:
        """从注册表重新加载状态机工作流配置
        
        清除当前注册的工作流类并重新从注册表加载。
        """
        if not self.registry_manager:
            logger.warning("注册管理器未初始化")
            return
        
        logger.info("重新从注册表加载状态机工作流配置")
        
        # 清除当前注册的工作流类
        self._workflow_classes.clear()
        
        # 重新初始化
        self._initialize_from_registry()
    
    def get_registry_info(self) -> Optional[Dict[str, Any]]:
        """获取注册表信息
        
        Returns:
            Optional[Dict[str, Any]]: 注册表信息，如果注册管理器未初始化则返回None
        """
        if not self.registry_manager:
            return None
        
        return self.registry_manager.get_registry_info()
    
    def _create_state_machine_config(
        self,
        workflow_name: str,
        config: Optional[Union[WorkflowConfig, Any]]
    ) -> StateMachineConfig:
        """创建状态机配置
        
        Args:
            workflow_name: 工作流名称
            config: 工作流配置
            
        Returns:
            StateMachineConfig: 状态机配置
        """
        # 尝试从注册管理器获取状态机配置
        if self.registry_manager:
            state_machine_configs = self.registry_manager.get_state_machine_configs()
            if workflow_name in state_machine_configs:
                try:
                    config_data = state_machine_configs[workflow_name]
                    return StateMachineConfigLoader._parse_config(config_data)
                except Exception as e:
                    logger.warning(f"从注册管理器加载状态机配置失败: {e}，使用默认配置")
        
        # 降级到硬编码的配置文件映射（向后兼容）
        config_file_map = {
            "deep_thinking": "configs/workflows/deep_thinking_workflow.yaml",
            "ultra_thinking": "configs/workflows/ultra_thinking_workflow.yaml"
        }
        
        config_file_path = config_file_map.get(workflow_name)
        if config_file_path:
            try:
                return StateMachineConfigLoader.load_from_yaml(config_file_path)
            except Exception as e:
                logger.warning(f"从配置文件加载状态机配置失败: {e}，使用默认配置")
        
        # 默认配置
        return StateMachineConfig(
            name=workflow_name,
            description=f"{workflow_name} 状态机工作流",
            version="1.0.0",
            initial_state="start"
        )
    


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
        
        # 使用统一配置管理器加载
        from src.core.config.config_manager import get_default_manager
        config_manager = get_default_manager()
        data = config_manager.load_config_for_module(file_path, "workflow")
        
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
        
        # 状态类型映射：将配置文件中的状态类型映射到StateType枚举
        state_type_mapping = {
            'start': StateType.START,
            'end': StateType.END,
            'process': StateType.PROCESS,
            'decision': StateType.DECISION,
            'parallel': StateType.PARALLEL,
            'conditional': StateType.CONDITIONAL,
            # 映射配置文件中使用的节点类型到PROCESS类型
            'llm_node': StateType.PROCESS,
            'analysis_node': StateType.PROCESS,
            'deep_thinking_node': StateType.PROCESS,
            'agent_configuration_node': StateType.PROCESS,
            'parallel_node': StateType.PARALLEL,
            'solution_integration_node': StateType.PROCESS,
            'collaborative_validation_node': StateType.PROCESS
        }
        
        # 解析状态
        states_data = data.get('states', {})
        for state_name, state_data in states_data.items():
            # 获取状态类型，如果不在映射中则默认为PROCESS
            state_type_str = state_data.get('type', 'process')
            state_type = state_type_mapping.get(state_type_str, StateType.PROCESS)
            
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