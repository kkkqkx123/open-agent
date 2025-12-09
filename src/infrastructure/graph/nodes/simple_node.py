"""简单节点实现，用于工作流模板

提供一个简单的节点实现，用于在工作流模板中创建节点。
"""

from typing import Dict, Any, List

from src.infrastructure.graph.nodes.base import BaseNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.base import IState


class SimpleNode(BaseNode):
    """简单节点实现"""
    
    def __init__(self, node_id: str = "", name: str = "", node_type: str = "simple",
                 description: str = "", config: Dict[str, Any] | None = None):
        """初始化节点
        
        Args:
            node_id: 节点ID
            name: 节点名称
            node_type: 节点类型
            description: 节点描述
            config: 节点配置
        """
        super().__init__(node_id, name, node_type, description, config)
    
    def execute(self, state: 'IState', config: Dict[str, Any]) -> 'NodeExecutionResult':
        """执行节点逻辑"""
        # 简单实现：返回当前状态
        from src.interfaces.workflow.graph import NodeExecutionResult
        return NodeExecutionResult(state=state)
    
    async def execute_async(self, state: 'IState', config: Dict[str, Any]) -> 'NodeExecutionResult':
        """异步执行节点逻辑"""
        # 简单实现：返回当前状态
        from src.interfaces.workflow.graph import NodeExecutionResult
        return NodeExecutionResult(state=state)
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }
    
    def validate(self) -> List[str]:
        """验证节点配置"""
        errors = []
        if not self._node_id:
            errors.append("节点ID不能为空")
        if not self.name:
            errors.append("节点名称不能为空")
        if not self._node_type:
            errors.append("节点类型不能为空")
        return errors