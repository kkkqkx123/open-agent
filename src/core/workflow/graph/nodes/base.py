"""节点基类

提供节点的基础实现。
"""

import asyncio
from typing import Dict, Any, List, Optional
from ..interfaces import INode, NodeExecutionResult


class BaseNode(INode):
    """节点基类"""

    def __init__(self, node_id: str):
        """初始化节点

        Args:
            node_id: 节点ID
        """
        self._node_id = node_id

    @property
    def node_id(self) -> str:
        """节点ID"""
        return self._node_id

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return self.__class__.__name__.replace("Node", "").lower()

    async def execute_async(self, state: 'IState', config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行节点逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        # 默认实现：使用同步执行
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.execute, state, config)