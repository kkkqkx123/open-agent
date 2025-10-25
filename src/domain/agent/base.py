"""Agent基类定义"""

from abc import ABC
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
import time
from .interfaces import IAgent
from .events import AgentEventManager, AgentEvent
from ..prompts.agent_state import AgentState


if TYPE_CHECKING:
    from .config import AgentConfig
    from src.infrastructure.llm.interfaces import ILLMClient
    from src.infrastructure.tools.executor import IToolExecutor


class BaseAgent(IAgent, ABC):
    def __init__(self, config: 'AgentConfig', llm_client: 'ILLMClient', tool_executor: 'IToolExecutor', event_manager: Optional['AgentEventManager'] = None):
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager or AgentEventManager()
        self._execution_stats = {
            "total_executions": 0,
            "total_time": 0.0,
            "avg_time": 0.0
        }
    
    async def execute(self, state: AgentState) -> AgentState:
        start_time = time.time()
        
        # 发布执行开始事件
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, {
            "agent_id": self.config.name,
            "state": state,
            "config": self.config
        })
        
        try:
            # 基础执行逻辑
            result = await self._execute_logic(state)
            
            # 发布执行完成事件
            execution_time = time.time() - start_time
            self.event_manager.publish(AgentEvent.EXECUTION_COMPLETED, {
                "agent_id": self.config.name,
                "input_state": state,
                "output_state": result,
                "config": self.config,
                "execution_time": execution_time
            })
            
            # 更新执行统计
            self._update_stats(execution_time)
            
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            # 发布错误事件
            self.event_manager.publish(AgentEvent.ERROR_OCCURRED, {
                "agent_id": self.config.name,
                "error": str(e),
                "state": state,
                "config": self.config,
                "execution_time": execution_time
            })
            
            # 重新抛出异常
            raise e
    
    async def _execute_logic(self, state: AgentState) -> AgentState:
        """执行逻辑的具体实现，子类需要重写此方法"""
        # 基础执行逻辑
        return state
    
    def can_handle(self, state: AgentState) -> bool:
        # 基础判断逻辑
        return True
    
    def get_capabilities(self) -> List[str]:
        # 基础能力列表
        return []
    
    def _update_stats(self, execution_time: float) -> None:
        """更新执行统计信息"""
        self._execution_stats["total_executions"] += 1
        self._execution_stats["total_time"] += execution_time
        self._execution_stats["avg_time"] = (
            self._execution_stats["total_time"] / self._execution_stats["total_executions"]
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return self._execution_stats.copy()
    
    async def execute_with_retry(self, state: AgentState, max_retries: int = 3) -> AgentState:
        """带重试机制的执行方法"""
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await self.execute(state)
            except Exception as e:
                last_exception = e
                if attempt < max_retries - 1:
                    # 指数退避策略
                    wait_time = min(2 ** attempt, 10)  # 最多等待10秒
                    await asyncio.sleep(wait_time)
                else:
                    # 最后一次尝试失败，抛出异常
                    raise last_exception or Exception("Unknown error after retries")
        
        # 这行代码理论上不会执行，但为了类型安全添加
        raise Exception("Unknown error after retries")