"""迭代感知图构建器

扩展增强图构建器，集成迭代管理器，提供统一的迭代控制能力。
"""

from typing import Dict, Any, Optional, Callable, Union
from datetime import datetime
import logging

from .enhanced_builder import EnhancedGraphBuilder
from .iteration_manager import IterationManager
from .config import GraphConfig
from .states import WorkflowState
from src.domain.state.interfaces import IStateCollaborationManager

logger = logging.getLogger(__name__)


class IterationAwareGraphBuilder(EnhancedGraphBuilder):
    """迭代感知图构建器

    在增强图构建器基础上，集成迭代管理器，实现全局和节点级别的迭代控制。
    """

    def __init__(
        self,
        node_registry=None,
        function_registry=None,
        enable_function_fallback=True,
    ):
        """初始化迭代感知图构建器

        Args:
            node_registry: 节点注册表
            function_registry: 函数注册表
            enable_function_fallback: 是否启用函数回退机制
        """
        super().__init__(node_registry, function_registry, enable_function_fallback)
        self.iteration_manager: Optional[IterationManager] = None

    def build_graph(self, config: GraphConfig, state_manager: Optional[IStateCollaborationManager] = None):
        """构建LangGraph图并集成迭代管理

        Args:
            config: 图配置
            state_manager: 状态管理器

        Returns:
            编译后的LangGraph图
        """
        # 创建迭代管理器
        self.iteration_manager = IterationManager(config)
        
        # 使用父类方法构建图
        graph = super().build_graph(config, state_manager)
        
        return graph

    def _get_node_function(self, node_config, state_manager: Optional[IStateCollaborationManager] = None):
        """获取节点函数（重写父类方法以集成迭代管理）

        Args:
            node_config: 节点配置
            state_manager: 状态管理器

        Returns:
            Optional[Callable]: 节点函数
        """
        # 获取原始节点函数
        original_function = super()._get_node_function(node_config, state_manager)

        if original_function is None:
            return None

        # 包装函数以集成迭代管理
        return self._wrap_with_iteration_management(original_function, node_config.name)

    def _wrap_with_iteration_management(self, function: Callable, node_name: str) -> Callable:
        """包装节点函数以集成迭代管理

        Args:
            function: 原始节点函数
            node_name: 节点名称

        Returns:
            Callable: 包装后的函数
        """
        def wrapped_function(state: Union[WorkflowState, Dict[str, Any]]) -> Any:
            """包装的节点函数，集成迭代管理"""
            
            # 记录开始时间
            start_time = datetime.now()
            
            try:
                # 检查迭代限制
                if self.iteration_manager and not self.iteration_manager.check_limits(state, node_name):
                    logger.info(f"节点 {node_name} 达到迭代限制，提前终止")
                    # 返回表明工作流已完成的状态
                    completed_state = dict(state)
                    completed_state['complete'] = True
                    return completed_state

                # 执行原始函数
                result = function(state)
                
                # 确保结果是字典格式
                if not isinstance(result, dict):
                    # 如果结果不是字典，尝试将其转换为字典
                    if hasattr(result, '__dict__'):
                        result = result.__dict__
                    else:
                        # 如果无法转换，则使用原始状态
                        result = state
                
                # 记录结束时间
                end_time = datetime.now()
                
                # 更新迭代计数
                if self.iteration_manager:
                    # 确保结果中包含原始状态信息
                    updated_result = dict(state, **result)  # 合并原始状态和结果
                    updated_result = self.iteration_manager.record_and_increment(
                        updated_result,
                        node_name,
                        start_time,
                        end_time,
                        status='SUCCESS'
                    )
                else:
                    updated_result = result
                
                return updated_result
                
            except Exception as e:
                logger.error(f"节点 {node_name} 执行失败: {e}")
                
                # 记录结束时间
                end_time = datetime.now()
                
                # 即使出错也要记录迭代
                if self.iteration_manager:
                    error_result = dict(state)
                    error_result = self.iteration_manager.record_and_increment(
                        error_result,
                        node_name,
                        start_time,
                        end_time,
                        status='FAILURE',
                        error=str(e)
                    )
                else:
                    error_result = state
                
                # 添加错误信息到状态
                errors = error_result.get('errors', [])
                errors.append(f"节点 {node_name} 执行失败: {str(e)}")
                error_result['errors'] = errors
                
                return error_result

        return wrapped_function