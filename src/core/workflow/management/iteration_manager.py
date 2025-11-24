"""迭代管理器

统一管理图节点的迭代次数，提供全局和节点级别的迭代控制。
"""

from typing import TypedDict, List, Dict, Optional, Any
from datetime import datetime

from ..config.config import GraphConfig
from ...state.implementations.workflow_state import WorkflowState

# 定义迭代记录类型
class IterationRecord(TypedDict):
    node_name: str
    start_time: datetime
    end_time: datetime
    duration: float
    status: str
    error: Optional[str]

# 定义节点迭代统计类型
class NodeIterationStats(TypedDict):
    count: int
    total_duration: float
    errors: int


class IterationManager:
    """迭代管理器，统一管理所有迭代相关逻辑"""

    def __init__(self, config: GraphConfig):
        """
        初始化迭代管理器
        
        Args:
            config: 图配置，包含迭代限制信息
        """
        self.workflow_max_iterations = config.additional_config.get("max_iterations", 10)
        # 从节点配置中提取节点级别的最大迭代次数
        self.node_specific_limits = {}
        for node_name, node_config in config.nodes.items():
            node_max_iterations = node_config.config.get('max_iterations')
            if node_max_iterations is not None:
                self.node_specific_limits[node_name] = node_max_iterations
        
        # 从配置获取循环完成节点
        self.cycle_completer_node = config.additional_config.get("cycle_completer_node")

    def record_and_increment(self, state: WorkflowState, node_name: str, start_time: datetime, 
                           end_time: datetime, status: str = 'SUCCESS', error: Optional[str] = None) -> WorkflowState:
        """
        记录一次迭代并更新所有相关计数
        
        Args:
            state: 当前工作流状态
            node_name: 执行的节点名称
            start_time: 迭代开始时间
            end_time: 迭代结束时间
            status: 迭代执行状态
            error: 如果有错误则记录错误信息
            
        Returns:
            更新后的工作流状态
        """
        # 计算迭代耗时
        duration = (end_time - start_time).total_seconds()
        
        # 创建迭代记录
        record: IterationRecord = {
            'node_name': node_name,
            'start_time': start_time,
            'end_time': end_time,
            'duration': duration,
            'status': status,
            'error': error
        }
        
        # 1. 添加到历史记录
        history = state.get('iteration_history', [])
        history.append(record)
        state['iteration_history'] = history

        # 2. 更新节点统计
        node_stats = state.get('node_iterations', {}).get(node_name, {
            'count': 0, 
            'total_duration': 0.0, 
            'errors': 0
        })
        node_stats['count'] += 1
        node_stats['total_duration'] += duration
        if status == 'FAILURE':
            node_stats['errors'] += 1
        
        # 确保 node_iterations 字典存在
        state.setdefault('node_iterations', {})
        state['node_iterations'][node_name] = node_stats

        # 3. 如果当前节点是循环完成节点，则增加全局工作流迭代计数
        if node_name == self.cycle_completer_node:
            state['workflow_iteration_count'] = state.get('workflow_iteration_count', 0) + 1

        return state

    def check_limits(self, state: WorkflowState, node_name: str) -> bool:
        """
        检查所有相关的迭代限制，如果超出则返回False
        
        Args:
            state: 当前工作流状态
            node_name: 要检查的节点名称
            
        Returns:
            True如果未超出限制，False如果超出限制
        """
        # 1. 检查全局工作流限制
        workflow_iteration_count = state.get('workflow_iteration_count', 0)
        if workflow_iteration_count >= self.workflow_max_iterations:
            print(f"工作流已达到最大迭代次数: {workflow_iteration_count}/{self.workflow_max_iterations}")
            return False

        # 2. 检查特定节点的限制
        if node_name in self.node_specific_limits:
            node_count = state.get('node_iterations', {}).get(node_name, {}).get('count', 0)
            node_max_limit = self.node_specific_limits[node_name]
            if node_count >= node_max_limit:
                print(f"节点 {node_name} 已达到最大迭代次数: {node_count}/{node_max_limit}")
                return False

        return True

    def has_reached_max_iterations(self, state: WorkflowState) -> bool:
        """
        检查是否达到最大迭代次数
        
        Args:
            state: 当前工作流状态
            
        Returns:
            True如果达到最大迭代次数，False否则
        """
        workflow_iteration_count = state.get('workflow_iteration_count', 0)
        return workflow_iteration_count >= self.workflow_max_iterations

    def get_iteration_stats(self, state: WorkflowState) -> Dict[str, Any]:
        """
        获取当前迭代统计信息
        
        Args:
            state: 当前工作流状态
            
        Returns:
            包含迭代统计信息的字典
        """
        return {
            'workflow_iteration_count': state.get('workflow_iteration_count', 0),
            'workflow_max_iterations': self.workflow_max_iterations,
            'node_iterations': state.get('node_iterations', {}),
            'iteration_history': state.get('iteration_history', [])
        }