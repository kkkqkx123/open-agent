"""工作流组合管理器实现

负责统一管理工作流组合逻辑，支持多种组合策略，处理工作流间的依赖关系。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.composition import (
    IWorkflowCompositionManager,
    ICompositionStrategy,
    CompositionStrategyType,
)
from src.interfaces.workflow.core import IWorkflow
from src.core.workflow.graph_entities import GraphConfig
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.infrastructure.validation.result import ValidationResult

if TYPE_CHECKING:
    from src.interfaces.workflow.composition import IDataMapper

logger = get_logger(__name__)


class WorkflowCompositionManager(IWorkflowCompositionManager):
    """工作流组合管理器"""
    
    def __init__(
        self,
        coordinator: IWorkflowCoordinator,
        data_mapper: Optional['IDataMapper'] = None
    ):
        """初始化组合管理器
        
        Args:
            coordinator: 工作流协调器，用于创建工作流实例
            data_mapper: 数据映射器，用于处理工作流间的数据映射
        """
        self._coordinator = coordinator
        self._data_mapper = data_mapper
        self._strategies: Dict[CompositionStrategyType, ICompositionStrategy] = {}
        self._logger = get_logger(f"{__name__}.WorkflowCompositionManager")
        
        # 注册默认策略
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """注册默认的组合策略"""
        try:
            from .strategies import (
                SequentialStrategy,
                ParallelStrategy,
                ConditionalStrategy,
                LoopStrategy,
            )
            
            self.register_strategy(SequentialStrategy())
            self.register_strategy(ParallelStrategy())
            self.register_strategy(ConditionalStrategy())
            self.register_strategy(LoopStrategy())
            
            self._logger.info("成功注册默认组合策略")
            
        except ImportError as e:
            self._logger.warning(f"注册默认策略时发生错误: {e}")
    
    def create_composition(self, composition_config: Dict[str, Any]) -> IWorkflow:
        """创建组合工作流
        
        Args:
            composition_config: 组合配置，包含：
                - strategy: 组合策略类型
                - workflows: 工作流配置列表
                - input_mappings: 输入映射配置
                - output_mappings: 输出映射配置
                - error_handling: 错误处理配置
                
        Returns:
            IWorkflow: 组合工作流实例
            
        Raises:
            ValueError: 配置无效或策略不支持
            RuntimeError: 创建工作流失败
        """
        try:
            self._logger.info(f"开始创建组合工作流: {composition_config.get('name', 'unnamed')}")
            
            # 验证配置
            validation_result = self._validate_composition_config(composition_config)
            if not validation_result.is_valid:
                raise ValueError(f"组合配置验证失败: {', '.join(validation_result.errors)}")
            
            # 获取策略类型
            strategy_type = CompositionStrategyType(composition_config.get('strategy', 'sequential'))
            
            # 获取策略实例
            strategy = self.get_strategy(strategy_type)
            if not strategy:
                raise ValueError(f"不支持的策略类型: {strategy_type}")
            
            # 创建工作流实例
            workflows = self._create_workflow_instances(composition_config['workflows'])
            
            # 应用策略组合工作流
            composed_workflow = strategy.execute(workflows)
            
            # 设置组合元数据
            composed_workflow.metadata = {
                'composition_type': 'workflow_composition',
                'strategy': strategy_type.value,
                'component_workflows': [w.workflow_id for w in workflows],
                'composition_config': composition_config,
            }
            
            self._logger.info(f"成功创建组合工作流: {composed_workflow.workflow_id}")
            return composed_workflow
            
        except Exception as e:
            self._logger.error(f"创建组合工作流失败: {e}")
            raise RuntimeError(f"创建组合工作流失败: {e}") from e
    
    def get_strategy(self, strategy_type: CompositionStrategyType) -> ICompositionStrategy:
        """获取组合策略
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            ICompositionStrategy: 策略实例，如果不存在则返回None
        """
        result = self._strategies.get(strategy_type)
        if result is None:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
        return result
    
    def register_strategy(self, strategy: ICompositionStrategy) -> None:
        """注册组合策略
        
        Args:
            strategy: 组合策略实例
        """
        self._strategies[strategy.strategy_type] = strategy
        self._logger.info(f"注册组合策略: {strategy.name} ({strategy.strategy_type.value})")
    
    def list_strategies(self) -> List[CompositionStrategyType]:
        """列出所有可用的策略类型
        
        Returns:
            List[CompositionStrategyType]: 策略类型列表
        """
        return list(self._strategies.keys())
    
    def _validate_composition_config(self, config: Dict[str, Any]) -> 'ValidationResult':
        """验证组合配置
        
        Args:
            config: 组合配置
            
        Returns:
            ValidationResult: 验证结果
        """
        
        errors = []
        
        # 检查必需字段
        if 'workflows' not in config:
            errors.append("缺少必需字段: workflows")
        elif not isinstance(config['workflows'], list):
            errors.append("workflows 必须是列表类型")
        elif len(config['workflows']) == 0:
            errors.append("workflows 列表不能为空")
        
        # 检查策略类型
        if 'strategy' in config:
            try:
                CompositionStrategyType(config['strategy'])
            except ValueError:
                errors.append(f"无效的策略类型: {config['strategy']}")
        
        # 验证每个工作流配置
        if 'workflows' in config and isinstance(config['workflows'], list):
            for i, workflow_config in enumerate(config['workflows']):
                if not isinstance(workflow_config, dict):
                    errors.append(f"工作流配置[{i}] 必须是字典类型")
                    continue
                
                if 'workflow_id' not in workflow_config:
                    errors.append(f"工作流配置[{i}] 缺少 workflow_id")
                
                # 验证输入输出映射配置
                if 'input_mapping' in workflow_config and self._data_mapper:
                    mapping_result = self._data_mapper.validate_mapping_config(
                        workflow_config['input_mapping']
                    )
                    if not mapping_result.is_valid:
                        errors.extend([f"工作流[{i}]输入映射错误: {err}" for err in mapping_result.errors])
                
                if 'output_mapping' in workflow_config and self._data_mapper:
                    mapping_result = self._data_mapper.validate_mapping_config(
                        workflow_config['output_mapping']
                    )
                    if not mapping_result.is_valid:
                        errors.extend([f"工作流[{i}]输出映射错误: {err}" for err in mapping_result.errors])
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=[])
    
    def _create_workflow_instances(self, workflow_configs: List[Dict[str, Any]]) -> List[IWorkflow]:
        """创建工作流实例列表
        
        Args:
            workflow_configs: 工作流配置列表
            
        Returns:
            List[IWorkflow]: 工作流实例列表
        """
        workflows = []
        
        for config in workflow_configs:
            try:
                # 创建工作流配置
                workflow_config = GraphConfig.from_dict(config)
                
                # 使用协调器创建工作流
                workflow = self._coordinator.create_workflow(workflow_config)
                workflows.append(workflow)
                
                self._logger.info(f"创建工作流实例: {workflow.workflow_id}")
                
            except Exception as e:
                self._logger.error(f"创建工作流实例失败: {e}")
                raise RuntimeError(f"创建工作流实例失败: {e}") from e
        
        return workflows
    
    def get_composition_stats(self) -> Dict[str, Any]:
        """获取组合管理器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'registered_strategies': len(self._strategies),
            'strategy_types': [st.value for st in self._strategies.keys()],
            'has_data_mapper': self._data_mapper is not None,
        }


# 便捷函数
def create_workflow_composition_manager(
    coordinator: IWorkflowCoordinator,
    data_mapper: Optional['IDataMapper'] = None
) -> WorkflowCompositionManager:
    """创建工作流组合管理器实例
    
    Args:
        coordinator: 工作流协调器
        data_mapper: 数据映射器（可选）
        
    Returns:
        WorkflowCompositionManager: 组合管理器实例
    """
    return WorkflowCompositionManager(
        coordinator=coordinator,
        data_mapper=data_mapper
    )


# 导出实现
__all__ = [
    "WorkflowCompositionManager",
    "create_workflow_composition_manager",
]