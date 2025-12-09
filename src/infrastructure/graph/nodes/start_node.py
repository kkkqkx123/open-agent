"""开始节点基础实现

提供工作流开始节点的基础实现。
"""

from typing import Dict, Any

from src.infrastructure.graph.nodes.simple_node import SimpleNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.base import IState


class StartNode(SimpleNode):
    """开始节点基础实现
    
    提供工作流的入口点，执行基本的初始化操作。
    """
    
    def __init__(self, node_id: str = "start", name: str = "Start", 
                 description: str = "工作流开始节点", config: Dict[str, Any] | None = None):
        """初始化开始节点
        
        Args:
            node_id: 节点ID
            name: 节点名称
            description: 节点描述
            config: 节点配置
        """
        super().__init__(node_id, name, "start", description, config)
    
    def execute(self, state: 'IState', config: Dict[str, Any]) -> NodeExecutionResult:
        """执行开始节点逻辑
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 基础实现：添加开始时间戳
        import time
        
        # 如果状态是字典，添加元数据
        if isinstance(state, dict):
            state['start_time'] = time.time()
            state['node_history'] = state.get('node_history', [])
            state['node_history'].append({
                'node_id': self.node_id,
                'node_type': self.node_type,
                'timestamp': time.time(),
                'status': 'completed'
            })
        else:
            # 如果是状态对象，使用元数据方法
            if hasattr(state, 'set_metadata'):
                state.set_metadata('start_time', time.time())
                history = state.get_metadata('node_history', [])
                history.append({
                    'node_id': self.node_id,
                    'node_type': self.node_type,
                    'timestamp': time.time(),
                    'status': 'completed'
                })
                state.set_metadata('node_history', history)
        
        return NodeExecutionResult(
            state=state,
            next_node=config.get('next_node'),
            metadata={'start_time': time.time()}
        )
    
    async def execute_async(self, state: 'IState', config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行开始节点逻辑
        
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
                "next_node": {
                    "type": "string",
                    "description": "下一个节点名称"
                },
                "initial_data": {
                    "type": "object",
                    "description": "初始数据"
                }
            },
            "required": []
        }