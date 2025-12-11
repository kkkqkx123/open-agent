"""组合策略引擎实现

提供多种工作流组合策略的实现，包括顺序、并行、条件和循环策略。
"""

from typing import Dict, Any, List, Optional
from abc import ABC
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.composition import (
    ICompositionStrategy,
    CompositionStrategyType,
)
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from src.core.workflow.workflow import Workflow
from src.core.workflow.graph_entities import GraphConfig

logger = get_logger(__name__)


class BaseCompositionStrategy(ICompositionStrategy, ABC):
    """组合策略基类"""
    
    def __init__(self, name: str, description: Optional[str] = None):
        """初始化策略
        
        Args:
            name: 策略名称
            description: 策略描述
        """
        self._name = name
        self._description = description
        self._logger = get_logger(f"{__name__}.{self.__class__.__name__}")
    
    @property
    def name(self) -> str:
        """策略名称"""
        return self._name
    
    @property
    def description(self) -> Optional[str]:
        """策略描述"""
        return self._description


class SequentialStrategy(BaseCompositionStrategy):
    """顺序组合策略 - 按顺序执行工作流"""
    
    def __init__(self):
        """初始化顺序策略"""
        super().__init__(
            name="Sequential Strategy",
            description="按顺序依次执行工作流，前一个工作流的输出作为后一个工作流的输入"
        )
    
    @property
    def strategy_type(self) -> CompositionStrategyType:
        """策略类型"""
        return CompositionStrategyType.SEQUENTIAL
    
    def execute(self, workflows: List[IWorkflow]) -> IWorkflow:
        """执行顺序组合策略
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 组合后的工作流实例
            
        Raises:
            ValueError: 工作流列表为空
            RuntimeError: 组合失败
        """
        try:
            self._logger.info(f"开始执行顺序组合策略，工作流数量: {len(workflows)}")
            
            if not workflows:
                raise ValueError("工作流列表不能为空")
            
            if len(workflows) == 1:
                self._logger.info("只有一个工作流，直接返回")
                return workflows[0]
            
            # 创建组合配置
            composition_config = self._create_sequential_config(workflows)
            
            # 创建组合工作流
            composed_workflow = Workflow(composition_config)
            
            # 设置组合元数据
            composed_workflow.metadata.update({
                'composition_strategy': self.strategy_type.value,
                'component_workflows': [w.workflow_id for w in workflows],
                'execution_order': 'sequential',
            })
            
            self._logger.info(f"顺序组合策略执行完成: {composed_workflow.workflow_id}")
            return composed_workflow
            
        except Exception as e:
            self._logger.error(f"顺序组合策略执行失败: {e}")
            raise RuntimeError(f"顺序组合策略执行失败: {e}") from e
    
    def _create_sequential_config(self, workflows: List[IWorkflow]) -> GraphConfig:
        """创建顺序组合配置
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            GraphConfig: 组合配置
        """
        # 这里需要实现具体的配置合并逻辑
        # 暂时使用第一个工作流的配置作为基础
        base_config = workflows[0].config
        
        # 创建新的配置，包含所有工作流的信息
        config_dict = base_config.to_dict()
        config_dict.update({
            'name': f"SequentialComposition_{workflows[0].name}",
            'id': f"sequential_comp_{workflows[0].workflow_id}",
            'description': f"顺序组合: {' -> '.join([w.name for w in workflows])}",
            'composition_workflows': [w.workflow_id for w in workflows],
        })
        
        return GraphConfig.from_dict(config_dict)


class ParallelStrategy(BaseCompositionStrategy):
    """并行组合策略 - 并行执行工作流"""
    
    def __init__(self):
        """初始化并行策略"""
        super().__init__(
            name="Parallel Strategy",
            description="并行执行所有工作流，收集所有结果"
        )
    
    @property
    def strategy_type(self) -> CompositionStrategyType:
        """策略类型"""
        return CompositionStrategyType.PARALLEL
    
    def execute(self, workflows: List[IWorkflow]) -> IWorkflow:
        """执行并行组合策略
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 组合后的工作流实例
        """
        try:
            self._logger.info(f"开始执行并行组合策略，工作流数量: {len(workflows)}")
            
            if not workflows:
                raise ValueError("工作流列表不能为空")
            
            if len(workflows) == 1:
                self._logger.info("只有一个工作流，直接返回")
                return workflows[0]
            
            # 创建组合配置
            composition_config = self._create_parallel_config(workflows)
            
            # 创建组合工作流
            composed_workflow = Workflow(composition_config)
            
            # 设置组合元数据
            composed_workflow.metadata.update({
                'composition_strategy': self.strategy_type.value,
                'component_workflows': [w.workflow_id for w in workflows],
                'execution_order': 'parallel',
            })
            
            self._logger.info(f"并行组合策略执行完成: {composed_workflow.workflow_id}")
            return composed_workflow
            
        except Exception as e:
            self._logger.error(f"并行组合策略执行失败: {e}")
            raise RuntimeError(f"并行组合策略执行失败: {e}") from e
    
    def _create_parallel_config(self, workflows: List[IWorkflow]) -> GraphConfig:
        """创建并行组合配置
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            GraphConfig: 组合配置
        """
        # 使用第一个工作流的配置作为基础
        base_config = workflows[0].config
        
        config_dict = base_config.to_dict()
        config_dict.update({
            'name': f"ParallelComposition_{workflows[0].name}",
            'id': f"parallel_comp_{workflows[0].workflow_id}",
            'description': f"并行组合: {', '.join([w.name for w in workflows])}",
            'composition_workflows': [w.workflow_id for w in workflows],
        })
        
        return GraphConfig.from_dict(config_dict)


class ConditionalStrategy(BaseCompositionStrategy):
    """条件组合策略 - 根据条件选择执行工作流"""
    
    def __init__(self):
        """初始化条件策略"""
        super().__init__(
            name="Conditional Strategy",
            description="根据条件选择执行特定的工作流"
        )
    
    @property
    def strategy_type(self) -> CompositionStrategyType:
        """策略类型"""
        return CompositionStrategyType.CONDITIONAL
    
    def execute(self, workflows: List[IWorkflow]) -> IWorkflow:
        """执行条件组合策略
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 组合后的工作流实例
        """
        try:
            self._logger.info(f"开始执行条件组合策略，工作流数量: {len(workflows)}")
            
            if not workflows:
                raise ValueError("工作流列表不能为空")
            
            # 创建组合配置
            composition_config = self._create_conditional_config(workflows)
            
            # 创建组合工作流
            composed_workflow = Workflow(composition_config)
            
            # 设置组合元数据
            composed_workflow.metadata.update({
                'composition_strategy': self.strategy_type.value,
                'component_workflows': [w.workflow_id for w in workflows],
                'execution_order': 'conditional',
            })
            
            self._logger.info(f"条件组合策略执行完成: {composed_workflow.workflow_id}")
            return composed_workflow
            
        except Exception as e:
            self._logger.error(f"条件组合策略执行失败: {e}")
            raise RuntimeError(f"条件组合策略执行失败: {e}") from e
    
    def _create_conditional_config(self, workflows: List[IWorkflow]) -> GraphConfig:
        """创建条件组合配置
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            GraphConfig: 组合配置
        """
        base_config = workflows[0].config
        
        config_dict = base_config.to_dict()
        config_dict.update({
            'name': f"ConditionalComposition_{workflows[0].name}",
            'id': f"conditional_comp_{workflows[0].workflow_id}",
            'description': f"条件组合: {', '.join([w.name for w in workflows])}",
            'composition_workflows': [w.workflow_id for w in workflows],
        })
        
        return GraphConfig.from_dict(config_dict)


class LoopStrategy(BaseCompositionStrategy):
    """循环组合策略 - 循环执行工作流"""
    
    def __init__(self):
        """初始化循环策略"""
        super().__init__(
            name="Loop Strategy",
            description="循环执行工作流，直到满足特定条件"
        )
    
    @property
    def strategy_type(self) -> CompositionStrategyType:
        """策略类型"""
        return CompositionStrategyType.LOOP
    
    def execute(self, workflows: List[IWorkflow]) -> IWorkflow:
        """执行循环组合策略
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            IWorkflow: 组合后的工作流实例
        """
        try:
            self._logger.info(f"开始执行循环组合策略，工作流数量: {len(workflows)}")
            
            if not workflows:
                raise ValueError("工作流列表不能为空")
            
            # 创建组合配置
            composition_config = self._create_loop_config(workflows)
            
            # 创建组合工作流
            composed_workflow = Workflow(composition_config)
            
            # 设置组合元数据
            composed_workflow.metadata.update({
                'composition_strategy': self.strategy_type.value,
                'component_workflows': [w.workflow_id for w in workflows],
                'execution_order': 'loop',
            })
            
            self._logger.info(f"循环组合策略执行完成: {composed_workflow.workflow_id}")
            return composed_workflow
            
        except Exception as e:
            self._logger.error(f"循环组合策略执行失败: {e}")
            raise RuntimeError(f"循环组合策略执行失败: {e}") from e
    
    def _create_loop_config(self, workflows: List[IWorkflow]) -> GraphConfig:
        """创建循环组合配置
        
        Args:
            workflows: 工作流实例列表
            
        Returns:
            GraphConfig: 组合配置
        """
        base_config = workflows[0].config
        
        config_dict = base_config.to_dict()
        config_dict.update({
            'name': f"LoopComposition_{workflows[0].name}",
            'id': f"loop_comp_{workflows[0].workflow_id}",
            'description': f"循环组合: {', '.join([w.name for w in workflows])}",
            'composition_workflows': [w.workflow_id for w in workflows],
        })
        
        return GraphConfig.from_dict(config_dict)


class CompositionStrategyEngine:
    """组合策略引擎 - 管理和执行组合策略"""
    
    def __init__(self):
        """初始化策略引擎"""
        self._strategies: Dict[CompositionStrategyType, ICompositionStrategy] = {}
        self._logger = get_logger(f"{__name__}.CompositionStrategyEngine")
        
        # 注册默认策略
        self._register_default_strategies()
    
    def _register_default_strategies(self) -> None:
        """注册默认策略"""
        self.register_strategy(SequentialStrategy())
        self.register_strategy(ParallelStrategy())
        self.register_strategy(ConditionalStrategy())
        self.register_strategy(LoopStrategy())
        
        self._logger.info("成功注册默认组合策略")
    
    def register_strategy(self, strategy: ICompositionStrategy) -> None:
        """注册策略
        
        Args:
            strategy: 策略实例
        """
        self._strategies[strategy.strategy_type] = strategy
        self._logger.info(f"注册策略: {strategy.name}")
    
    def get_strategy(self, strategy_type: CompositionStrategyType) -> Optional[ICompositionStrategy]:
        """获取策略
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            ICompositionStrategy: 策略实例，如果不存在则返回None
        """
        return self._strategies.get(strategy_type)
    
    def list_strategies(self) -> List[CompositionStrategyType]:
        """列出所有策略类型
        
        Returns:
            List[CompositionStrategyType]: 策略类型列表
        """
        return list(self._strategies.keys())
    
    def execute_strategy(
        self,
        strategy_type: CompositionStrategyType,
        workflows: List[IWorkflow]
    ) -> IWorkflow:
        """执行策略
        
        Args:
            strategy_type: 策略类型
            workflows: 工作流列表
            
        Returns:
            IWorkflow: 组合后的工作流
            
        Raises:
            ValueError: 策略类型不支持
            RuntimeError: 执行失败
        """
        strategy = self.get_strategy(strategy_type)
        if not strategy:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
        
        return strategy.execute(workflows)
    
    def get_strategy_stats(self) -> Dict[str, Any]:
        """获取策略引擎统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'registered_strategies': len(self._strategies),
            'strategy_types': [st.value for st in self._strategies.keys()],
        }


# 便捷函数
def create_composition_strategy_engine() -> CompositionStrategyEngine:
    """创建组合策略引擎实例
    
    Returns:
        CompositionStrategyEngine: 策略引擎实例
    """
    return CompositionStrategyEngine()


# 导出实现
__all__ = [
    "BaseCompositionStrategy",
    "SequentialStrategy",
    "ParallelStrategy",
    "ConditionalStrategy",
    "LoopStrategy",
    "CompositionStrategyEngine",
    "create_composition_strategy_engine",
]