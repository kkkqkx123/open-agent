"""纯同步节点基类

提供本地、快速、CPU密集操作的节点实现。
"""

from typing import Dict, Any

from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.workflow import IWorkflowState
from src.infrastructure.graph.nodes.base import BaseNode


class SyncNode(BaseNode):
    """纯同步节点基类
    
    用途：
    ─────────────────────────────────────
    本地、快速、CPU密集的操作，不涉及I/O等待。
    
    示例节点类型：
    - ConditionNode：条件判断、路由决策
    - ToolNode：工具执行协调（工具本身可异步）
    - StartNode：工作流初始化
    - EndNode：工作流清理
    - WaitNode：超时处理
    
    设计原则：
    ─────────────────────────────────────
    1. execute() 有真实的同步实现（子类必须提供）
    2. execute_async() 抛出RuntimeError（不支持异步）
    3. 同步调用：直接执行（最快）
    4. 异步调用：抛错并告知用户（提示改为SyncMode）
    
    何时使用SyncNode：
    ─────────────────────────────────────
    ✓ 节点操作本地完成
    ✓ 不涉及网络、文件、数据库I/O
    ✓ 操作通常< 100ms
    ✓ CPU密集计算
    ✓ 状态转换和路由决策
    
    何时改为AsyncNode：
    ─────────────────────────────────────
    ✗ 需要调用外部API
    ✗ 需要网络请求
    ✗ 需要数据库操作
    ✗ 需要文件I/O
    ✗ 操作可能> 1秒
    """
    
    async def execute_async(
        self, 
        state: IWorkflowState, 
        config: Dict[str, Any]
    ) -> NodeExecutionResult:
        """异步执行节点（不支持）
        
        SyncNode不支持异步执行。
        
        Args:
            state: 工作流状态
            config: 节点配置
            
        Raises:
            RuntimeError: 纯同步节点不支持异步执行
        """
        raise RuntimeError(
            f"SyncNode '{self.node_id}' does not support async execution. "
            f"This is a synchronous-only node. "
            f"Please use SyncMode or convert it to AsyncNode if async execution is needed."
        )
