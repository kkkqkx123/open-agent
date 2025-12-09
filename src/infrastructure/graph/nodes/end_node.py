"""结束节点基础实现

提供工作流结束节点的基础实现。
"""

from typing import Dict, Any

from src.infrastructure.graph.nodes.simple_node import SimpleNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.base import IState


class EndNode(SimpleNode):
    """结束节点基础实现
    
    提供工作流的结束点，执行基本的清理操作。
    """
    
    def __init__(self, node_id: str = "end", name: str = "End", 
                 description: str = "工作流结束节点", config: Dict[str, Any] | None = None):
        """初始化结束节点
        
        Args:
            node_id: 节点ID
            name: 节点名称
            description: 节点描述
            config: 节点配置
        """
        super().__init__(node_id, name, "end", description, config)
    
    def execute(self, state: 'IState', config: Dict[str, Any]) -> 'NodeExecutionResult':
        """执行结束节点逻辑
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 基础实现：添加结束时间戳和完成标记
        from src.interfaces.workflow.graph import NodeExecutionResult
        import time
        
        end_time = time.time()
        
        # 如果状态是字典，添加元数据
        if isinstance(state, dict):
            state['end_time'] = end_time
            state['workflow_completed'] = True
            
            # 计算总执行时间
            if 'start_time' in state:
                state['total_execution_time'] = end_time - state['start_time']
            
            # 更新节点历史
            state['node_history'] = state.get('node_history', [])
            state['node_history'].append({
                'node_id': self.node_id,
                'node_type': self.node_type,
                'timestamp': end_time,
                'status': 'completed'
            })
        else:
            # 如果是状态对象，使用元数据方法
            if hasattr(state, 'set_metadata'):
                state.set_metadata('end_time', end_time)
                state.set_metadata('workflow_completed', True)
                
                # 计算总执行时间
                start_time = state.get_metadata('start_time')
                if start_time:
                    state.set_metadata('total_execution_time', end_time - start_time)
                
                # 更新节点历史
                history = state.get_metadata('node_history', [])
                history.append({
                    'node_id': self.node_id,
                    'node_type': self.node_type,
                    'timestamp': end_time,
                    'status': 'completed'
                })
                state.set_metadata('node_history', history)
        
        return NodeExecutionResult(
            state=state,
            next_node=None,  # 结束节点没有下一个节点
            metadata={
                'end_time': end_time,
                'workflow_completed': True
            }
        )
    
    async def execute_async(self, state: 'IState', config: Dict[str, Any]) -> 'NodeExecutionResult':
        """异步执行结束节点逻辑
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 简单实现：直接调用同步版本
        return self.execute(state, config)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "save_results": {
                    "type": "boolean",
                    "description": "是否保存结果",
                    "default": True
                },
                "generate_summary": {
                    "type": "boolean",
                    "description": "是否生成摘要",
                    "default": True
                }
            },
            "required": []
        }