"""异步节点基类

提供I/O密集操作的节点实现。
"""

import asyncio
from abc import abstractmethod
from typing import Dict, Any

from src.infrastructure.graph.nodes.base import BaseNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.workflow import IWorkflowState


class AsyncNode(BaseNode):
    """异步节点基类
    
    用途：
    ─────────────────────────────────────
    I/O密集操作，需要等待外部资源响应。
    
    示例节点类型：
    - LLMNode：调用LLM API
    - APINode：调用HTTP API
    - DatabaseNode：查询数据库
    - FileIONode：读写文件
    
    设计原则：
    ─────────────────────────────────────
    1. execute_async() 有真实的异步实现（子类必须提供）
    2. execute() 创建新事件循环调用execute_async()
    3. 同步调用：创建新循环（有开销）
    4. 异步调用：直接执行（最优）
    
    何时使用AsyncNode：
    ─────────────────────────────────────
    ✓ 需要调用外部API（LLM、HTTP等）
    ✓ 需要数据库查询
    ✓ 需要文件I/O（异步）
    ✓ 操作涉及网络延迟
    ✓ 需要真正利用异步优势
    
    性能特征：
    ─────────────────────────────────────
    同步调用: T = 新循环开销(5-10ms) + I/O等待
    异步调用: T = I/O等待（无额外开销）
    
    推荐：在异步上下文中使用AsyncMode调用execute_async()
    """
    
    def __init__(self, node_id: str = "", name: str = "", node_type: str = "async",
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
    
    def execute(
        self, 
        state: 'IWorkflowState', 
        config: Dict[str, Any]
    ) -> 'NodeExecutionResult':
        """同步执行节点（创建新事件循环）
        
        警告：
        1. 如果已在事件循环中调用，会抛RuntimeError
        2. 会创建新的事件循环，有5-10ms的开销
        3. 优先使用execute_async()在异步上下文中调用
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
            
        Raises:
            RuntimeError: 如果在运行的事件循环中调用
        """
        try:
            # 检查是否已在事件循环中
            asyncio.get_running_loop()
            raise RuntimeError(
                f"AsyncNode '{self.node_id}' cannot be called synchronously "
                f"from within a running event loop. "
                f"Use execute_async() instead."
            )
        except RuntimeError as e:
            # 检查是否是"没有运行的循环"异常
            if "no running event loop" not in str(e).lower():
                # 是其他RuntimeError（如上面抛出的），重新抛出
                raise
            
            # 没有运行的循环，创建新循环
            # 注意：这里避免依赖服务层的logger，使用简单的print
            print(
                f"Warning: AsyncNode '{self.node_id}' executing synchronously. "
                f"This creates a new event loop (~5-10ms overhead). "
                f"Consider using execute_async() in async context."
            )
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self.execute_async(state, config))
            finally:
                loop.close()
    
    @abstractmethod
    async def execute_async(self, state: 'IWorkflowState', config: Dict[str, Any]) -> 'NodeExecutionResult':
        """异步执行节点（子类必须实现）
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        pass
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "timeout": {
                    "type": "number",
                    "description": "异步操作超时时间（秒）"
                }
            },
            "required": []
        }