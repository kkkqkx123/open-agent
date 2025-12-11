"""工作流生命周期管理器

专门负责工作流的迭代管理和生命周期控制。
"""

from typing import Dict, Any, Optional
from datetime import datetime

from src.core.workflow.graph_entities import Graph
from src.interfaces.state import IWorkflowState

# 定义迭代记录类型
class IterationRecord:
    """迭代记录"""
    
    def __init__(
        self,
        node_name: str,
        start_time: datetime,
        end_time: datetime,
        duration: float,
        status: str,
        error: Optional[str] = None
    ):
        self.node_name = node_name
        self.start_time = start_time
        self.end_time = end_time
        self.duration = duration
        self.status = status
        self.error = error


# 定义节点迭代统计类型
class NodeIterationStats:
    """节点迭代统计"""
    
    def __init__(self):
        self.count = 0
        self.total_duration = 0.0
        self.errors = 0


class WorkflowLifecycleManager:
    """工作流生命周期管理器
    
    专门负责迭代管理和生命周期控制，
    不包含验证、执行等其他业务逻辑。
    """
    
    def __init__(self, graph: Graph):
        """初始化生命周期管理器
        
        Args:
            graph: 图实体，包含迭代限制信息
        """
        # 从图的额外配置中获取最大迭代次数
        # 注意：这里需要适配新的Graph实体结构
        self.workflow_max_iterations = 10  # 默认值，实际应该从graph的配置中获取
        
        # 从节点中提取节点级别的最大迭代次数
        self.node_specific_limits = {}
        for node_name, node in graph.nodes.items():
            # 从节点的参数中获取最大迭代次数
            node_max_iterations = node.parameters.get('max_iterations')
            if node_max_iterations is not None:
                self.node_specific_limits[node_name] = node_max_iterations
        
        # 循环完成节点（暂时设为None，实际应该从graph配置中获取）
        self.cycle_completer_node = None
    
    def record_and_increment(
        self,
        state: IWorkflowState,
        node_name: str,
        start_time: datetime,
        end_time: datetime,
        status: str = 'SUCCESS',
        error: Optional[str] = None
    ) -> IWorkflowState:
        """记录一次迭代并更新所有相关计数
        
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
        record = IterationRecord(
            node_name=node_name,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            status=status,
            error=error
        )
        
        # 1. 添加到历史记录
        history = state.get_data('iteration_history', [])
        history.append({
            'node_name': record.node_name,
            'start_time': record.start_time.isoformat(),
            'end_time': record.end_time.isoformat(),
            'duration': record.duration,
            'status': record.status,
            'error': record.error
        })
        state.set_data('iteration_history', history)

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
        node_iterations = state.get_data('node_iterations', {})
        node_iterations[node_name] = node_stats
        state.set_data('node_iterations', node_iterations)

        # 3. 如果当前节点是循环完成节点，则增加全局工作流迭代计数
        if node_name == self.cycle_completer_node:
            current_count = state.get_data('workflow_iteration_count', 0)
            state.set_data('workflow_iteration_count', current_count + 1)

        return state
    
    def check_limits(self, state: IWorkflowState, node_name: str) -> bool:
        """检查所有相关的迭代限制，如果超出则返回False
        
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
    
    def has_reached_max_iterations(self, state: IWorkflowState) -> bool:
        """检查是否达到最大迭代次数
        
        Args:
            state: 当前工作流状态
            
        Returns:
            True如果达到最大迭代次数，False否则
        """
        workflow_iteration_count = state.get('workflow_iteration_count', 0)
        return workflow_iteration_count >= self.workflow_max_iterations
    
    def get_iteration_stats(self, state: IWorkflowState) -> Dict[str, Any]:
        """获取当前迭代统计信息
        
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
    
    def reset_iteration_count(self, state: IWorkflowState) -> IWorkflowState:
        """重置迭代计数
        
        Args:
            state: 当前工作流状态
            
        Returns:
            更新后的工作流状态
        """
        state.set_data('workflow_iteration_count', 0)
        state.set_data('node_iterations', {})
        state.set_data('iteration_history', [])
        return state
    
    def get_node_iteration_count(self, state: IWorkflowState, node_name: str) -> int:
        """获取特定节点的迭代次数
        
        Args:
            state: 当前工作流状态
            node_name: 节点名称
            
        Returns:
            节点迭代次数
        """
        return state.get('node_iterations', {}).get(node_name, {}).get('count', 0)
    
    def get_workflow_iteration_count(self, state: IWorkflowState) -> int:
        """获取工作流迭代次数
        
        Args:
            state: 当前工作流状态
            
        Returns:
            工作流迭代次数
        """
        return state.get('workflow_iteration_count', 0)