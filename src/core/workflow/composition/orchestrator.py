"""工作流组合编排器实现

负责协调组合工作流的执行，处理错误和重试，管理组合工作流的生命周期。
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from enum import Enum
from src.interfaces.dependency_injection import get_logger

from src.interfaces.workflow.composition import IWorkflowCompositionOrchestrator
from src.interfaces.workflow.core import IWorkflow
from src.interfaces.state.workflow import IWorkflowState
from src.interfaces.workflow.coordinator import IWorkflowCoordinator
from src.interfaces.workflow.composition import IWorkflowCompositionManager

if TYPE_CHECKING:
    from src.interfaces.workflow.composition import IDataMapper

logger = get_logger(__name__)


class CompositionStatus(Enum):
    """组合状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class WorkflowCompositionOrchestrator(IWorkflowCompositionOrchestrator):
    """工作流组合编排器"""
    
    def __init__(
        self,
        coordinator: IWorkflowCoordinator,
        composition_manager: IWorkflowCompositionManager,
        data_mapper: Optional['IDataMapper'] = None,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """初始化组合编排器
        
        Args:
            coordinator: 工作流协调器
            composition_manager: 组合管理器
            data_mapper: 数据映射器
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
        """
        self._coordinator = coordinator
        self._composition_manager = composition_manager
        self._data_mapper = data_mapper
        self._max_retries = max_retries
        self._retry_delay = retry_delay
        self._logger = get_logger(f"{__name__}.WorkflowCompositionOrchestrator")
        
        # 组合状态跟踪
        self._composition_states: Dict[str, Dict[str, Any]] = {}
    
    def orchestrate_composition(
        self,
        composition: IWorkflow,
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """编排组合工作流执行
        
        Args:
            composition: 组合工作流实例
            initial_state: 初始状态
            
        Returns:
            Dict[str, Any]: 执行结果
            
        Raises:
            ValueError: 参数无效
            RuntimeError: 执行失败
        """
        try:
            self._logger.info(f"开始编排组合工作流: {composition.workflow_id}")
            
            # 验证参数
            if not composition:
                raise ValueError("组合工作流不能为空")
            
            if not initial_state:
                initial_state = {}
            
            # 获取组合配置
            composition_config = composition.metadata.get('composition_config', {})
            
            # 初始化组合状态
            self._init_composition_state(composition, initial_state)
            
            # 获取组件工作流列表
            component_workflows = self._get_component_workflows(composition)
            
            # 获取组合策略
            strategy_type = composition.metadata.get('composition_strategy', 'sequential')
            from src.interfaces.workflow.composition import CompositionStrategyType
            strategy = self._composition_manager.get_strategy(CompositionStrategyType(strategy_type))
            
            if not strategy:
                raise ValueError(f"不支持的组合策略: {strategy_type}")
            
            # 执行组合策略
            result = self._execute_composition_strategy(
                composition,
                component_workflows,
                strategy,
                initial_state,
                composition_config
            )
            
            # 更新组合状态
            self._update_composition_state(composition, CompositionStatus.COMPLETED, result)
            
            self._logger.info(f"组合工作流编排完成: {composition.workflow_id}")
            return result
            
        except Exception as e:
            self._logger.error(f"组合工作流编排失败: {e}")
            self._update_composition_state(composition, CompositionStatus.FAILED, {'error': str(e)})
            raise RuntimeError(f"组合工作流编排失败: {e}") from e
    
    def handle_composition_error(self, error: Exception, composition: IWorkflow) -> None:
        """处理组合错误
        
        Args:
            error: 错误实例
            composition: 组合工作流实例
        """
        try:
            self._logger.error(f"处理组合工作流错误: {composition.workflow_id}, 错误: {error}")
            
            # 获取当前状态
            state = self._composition_states.get(composition.workflow_id, {})
            retry_count = state.get('retry_count', 0)
            
            # 检查是否还可以重试
            if retry_count < self._max_retries:
                self._logger.info(f"准备重试组合工作流，当前重试次数: {retry_count}")
                self._update_composition_state(composition, CompositionStatus.RETRYING, {
                    'error': str(error),
                    'retry_count': retry_count + 1
                })
                
                # 这里可以实现重试逻辑
                # 例如：重新执行组合或通知上层进行重试
                
            else:
                self._logger.warning(f"组合工作流重试次数已达上限: {self._max_retries}")
                self._update_composition_state(composition, CompositionStatus.FAILED, {
                    'error': str(error),
                    'final_error': True
                })
            
        except Exception as e:
            self._logger.error(f"处理组合错误时发生错误: {e}")
    
    def get_composition_status(self, composition: IWorkflow) -> Dict[str, Any]:
        """获取组合状态
        
        Args:
            composition: 组合工作流实例
            
        Returns:
            Dict[str, Any]: 状态信息
        """
        return self._composition_states.get(composition.workflow_id, {
            'status': CompositionStatus.PENDING.value,
            'created_at': None,
            'updated_at': None,
            'retry_count': 0,
            'error': None,
            'result': None
        })
    
    def _init_composition_state(self, composition: IWorkflow, initial_state: Dict[str, Any]) -> None:
        """初始化组合状态
        
        Args:
            composition: 组合工作流实例
            initial_state: 初始状态
        """
        import time
        
        self._composition_states[composition.workflow_id] = {
            'status': CompositionStatus.RUNNING.value,
            'created_at': time.time(),
            'updated_at': time.time(),
            'retry_count': 0,
            'error': None,
            'result': None,
            'initial_state': initial_state,
            'component_states': {}
        }
        
        self._logger.debug(f"初始化组合状态: {composition.workflow_id}")
    
    def _update_composition_state(
        self,
        composition: IWorkflow,
        status: CompositionStatus,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """更新组合状态
        
        Args:
            composition: 组合工作流实例
            status: 状态
            data: 附加数据
        """
        import time
        
        state = self._composition_states.get(composition.workflow_id, {})
        state['status'] = status.value
        state['updated_at'] = time.time()
        
        if data:
            state.update(data)
        
        self._composition_states[composition.workflow_id] = state
        
        self._logger.debug(f"更新组合状态: {composition.workflow_id} -> {status.value}")
    
    def _get_component_workflows(self, composition: IWorkflow) -> List[IWorkflow]:
        """获取组件工作流列表
        
        Args:
            composition: 组合工作流实例
            
        Returns:
            List[IWorkflow]: 组件工作流列表
        """
        # 从元数据中获取组件工作流ID列表
        component_ids = composition.metadata.get('component_workflows', [])
        
        # 这里需要实现从工作流注册表或存储中获取工作流实例的逻辑
        # 暂时返回空列表，需要在实际使用时实现
        self._logger.warning(f"获取组件工作流功能需要实现，当前组件ID: {component_ids}")
        return []
    
    def _execute_composition_strategy(
        self,
        composition: IWorkflow,
        component_workflows: List[IWorkflow],
        strategy,
        initial_state: Dict[str, Any],
        composition_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行组合策略
        
        Args:
            composition: 组合工作流实例
            component_workflows: 组件工作流列表
            strategy: 组合策略
            initial_state: 初始状态
            composition_config: 组合配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._logger.info(f"执行组合策略: {strategy.name}")
        
        # 根据策略类型执行不同的逻辑
        strategy_type = strategy.strategy_type
        
        if strategy_type.value == 'sequential':
            return self._execute_sequential_strategy(
                component_workflows, initial_state, composition_config
            )
        elif strategy_type.value == 'parallel':
            return self._execute_parallel_strategy(
                component_workflows, initial_state, composition_config
            )
        elif strategy_type.value == 'conditional':
            return self._execute_conditional_strategy(
                component_workflows, initial_state, composition_config
            )
        elif strategy_type.value == 'loop':
            return self._execute_loop_strategy(
                component_workflows, initial_state, composition_config
            )
        else:
            raise ValueError(f"不支持的策略类型: {strategy_type}")
    
    def _execute_sequential_strategy(
        self,
        workflows: List[IWorkflow],
        initial_state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行顺序策略
        
        Args:
            workflows: 工作流列表
            initial_state: 初始状态
            config: 配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._logger.info(f"执行顺序策略，工作流数量: {len(workflows)}")
        
        current_state = initial_state.copy()
        results = {}
        
        for i, workflow in enumerate(workflows):
            try:
                self._logger.debug(f"执行顺序工作流 {i+1}/{len(workflows)}: {workflow.workflow_id}")
                
                # 应用输入映射
                if self._data_mapper and config.get('workflows', [])[i].get('input_mapping'):
                    input_mapping = config['workflows'][i]['input_mapping']
                    current_state = self._data_mapper.map_input_data(current_state, input_mapping)
                
                # 创建工作流状态
                workflow_state = self._create_workflow_state(current_state)
                
                # 执行工作流
                result_state = self._coordinator.execute_workflow(workflow, workflow_state)
                
                # 获取结果
                result_data = self._extract_state_data(result_state)
                results[workflow.workflow_id] = result_data
                
                # 应用输出映射
                if self._data_mapper and config.get('workflows', [])[i].get('output_mapping'):
                    output_mapping = config['workflows'][i]['output_mapping']
                    current_state = self._data_mapper.map_output_data(result_data, output_mapping)
                else:
                    current_state.update(result_data)
                
                self._logger.debug(f"顺序工作流 {i+1} 执行完成: {workflow.workflow_id}")
                
            except Exception as e:
                self._logger.error(f"顺序工作流 {i+1} 执行失败: {workflow.workflow_id}, 错误: {e}")
                raise RuntimeError(f"顺序工作流执行失败: {workflow.workflow_id}, 错误: {e}") from e
        
        return {
            'strategy': 'sequential',
            'results': results,
            'final_state': current_state,
            'workflow_count': len(workflows)
        }
    
    def _execute_parallel_strategy(
        self,
        workflows: List[IWorkflow],
        initial_state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行并行策略
        
        Args:
            workflows: 工作流列表
            initial_state: 初始状态
            config: 配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._logger.info(f"执行并行策略，工作流数量: {len(workflows)}")
        
        # 这里需要实现真正的并行执行逻辑
        # 暂时使用顺序执行作为占位符
        results = {}
        final_state = initial_state.copy()
        
        for i, workflow in enumerate(workflows):
            try:
                self._logger.debug(f"执行并行工作流 {i+1}/{len(workflows)}: {workflow.workflow_id}")
                
                # 应用输入映射
                workflow_state = initial_state.copy()
                if self._data_mapper and config.get('workflows', [])[i].get('input_mapping'):
                    input_mapping = config['workflows'][i]['input_mapping']
                    workflow_state = self._data_mapper.map_input_data(workflow_state, input_mapping)
                
                # 创建工作流状态
                wf_state = self._create_workflow_state(workflow_state)
                
                # 执行工作流
                result_state = self._coordinator.execute_workflow(workflow, wf_state)
                
                # 获取结果
                result_data = self._extract_state_data(result_state)
                results[workflow.workflow_id] = result_data
                
                # 合并结果到最终状态
                final_state.update(result_data)
                
                self._logger.debug(f"并行工作流 {i+1} 执行完成: {workflow.workflow_id}")
                
            except Exception as e:
                self._logger.error(f"并行工作流 {i+1} 执行失败: {workflow.workflow_id}, 错误: {e}")
                # 并行策略中，单个工作流失败不应该阻止其他工作流执行
                results[workflow.workflow_id] = {'error': str(e)}
        
        return {
            'strategy': 'parallel',
            'results': results,
            'final_state': final_state,
            'workflow_count': len(workflows)
        }
    
    def _execute_conditional_strategy(
        self,
        workflows: List[IWorkflow],
        initial_state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行条件策略
        
        Args:
            workflows: 工作流列表
            initial_state: 初始状态
            config: 配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._logger.info(f"执行条件策略，工作流数量: {len(workflows)}")
        
        # 这里需要实现条件选择逻辑
        # 暂时执行第一个工作流作为示例
        if workflows:
            workflow = workflows[0]
            self._logger.debug(f"执行条件工作流: {workflow.workflow_id}")
            
            # 创建工作流状态
            workflow_state = self._create_workflow_state(initial_state)
            
            # 执行工作流
            result_state = self._coordinator.execute_workflow(workflow, workflow_state)
            
            # 获取结果
            result_data = self._extract_state_data(result_state)
            
            return {
                'strategy': 'conditional',
                'selected_workflow': workflow.workflow_id,
                'results': {workflow.workflow_id: result_data},
                'final_state': result_data,
                'workflow_count': 1
            }
        
        return {
            'strategy': 'conditional',
            'selected_workflow': None,
            'results': {},
            'final_state': initial_state,
            'workflow_count': 0
        }
    
    def _execute_loop_strategy(
        self,
        workflows: List[IWorkflow],
        initial_state: Dict[str, Any],
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """执行循环策略
        
        Args:
            workflows: 工作流列表
            initial_state: 初始状态
            config: 配置
            
        Returns:
            Dict[str, Any]: 执行结果
        """
        self._logger.info(f"执行循环策略，工作流数量: {len(workflows)}")
        
        # 这里需要实现循环逻辑
        # 暂时执行一次作为示例
        results = {}
        current_state = initial_state.copy()
        
        if workflows:
            workflow = workflows[0]  # 通常循环策略只针对一个工作流
            self._logger.debug(f"执行循环工作流: {workflow.workflow_id}")
            
            # 创建工作流状态
            workflow_state = self._create_workflow_state(current_state)
            
            # 执行工作流
            result_state = self._coordinator.execute_workflow(workflow, workflow_state)
            
            # 获取结果
            result_data = self._extract_state_data(result_state)
            results[workflow.workflow_id] = result_data
            current_state = result_data
        
        return {
            'strategy': 'loop',
            'loop_count': 1,  # 实际实现中应该根据条件计算
            'results': results,
            'final_state': current_state,
            'workflow_count': len(results)
        }
    
    def _create_workflow_state(self, data: Dict[str, Any]) -> IWorkflowState:
        """创建工作流状态
        
        Args:
            data: 状态数据
            
        Returns:
            IWorkflowState: 工作流状态
        """
        # 这里需要实现具体的工作流状态创建逻辑
        # 暂时返回一个简单的字典包装
        from src.core.state.implementations.workflow_state import WorkflowState
        return WorkflowState(**data)
    
    def _extract_state_data(self, state: IWorkflowState) -> Dict[str, Any]:
        """从工作流状态提取数据
        
        Args:
            state: 工作流状态
            
        Returns:
            Dict[str, Any]: 状态数据
        """
        # 这里需要实现具体的状态数据提取逻辑
        # 暂时假设状态可以直接转换为字典
        if hasattr(state, 'to_dict'):
            return state.to_dict()
        elif isinstance(state, dict):
            return state
        else:
            return {}
    
    def get_orchestrator_stats(self) -> Dict[str, Any]:
        """获取编排器统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return {
            'active_compositions': len(self._composition_states),
            'max_retries': self._max_retries,
            'retry_delay': self._retry_delay,
            'has_data_mapper': self._data_mapper is not None,
            'composition_states': {
                comp_id: {
                    'status': state.get('status'),
                    'retry_count': state.get('retry_count', 0),
                    'created_at': state.get('created_at'),
                    'updated_at': state.get('updated_at')
                }
                for comp_id, state in self._composition_states.items()
            }
        }


# 便捷函数
def create_workflow_composition_orchestrator(
    coordinator: IWorkflowCoordinator,
    composition_manager: IWorkflowCompositionManager,
    data_mapper: Optional['IDataMapper'] = None,
    max_retries: int = 3,
    retry_delay: float = 1.0
) -> WorkflowCompositionOrchestrator:
    """创建工作流组合编排器实例
    
    Args:
        coordinator: 工作流协调器
        composition_manager: 组合管理器
        data_mapper: 数据映射器（可选）
        max_retries: 最大重试次数
        retry_delay: 重试延迟
        
    Returns:
        WorkflowCompositionOrchestrator: 组合编排器实例
    """
    return WorkflowCompositionOrchestrator(
        coordinator=coordinator,
        composition_manager=composition_manager,
        data_mapper=data_mapper,
        max_retries=max_retries,
        retry_delay=retry_delay
    )


# 导出实现
__all__ = [
    "CompositionStatus",
    "WorkflowCompositionOrchestrator",
    "create_workflow_composition_orchestrator",
]