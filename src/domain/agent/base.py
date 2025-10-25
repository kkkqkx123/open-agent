"""Agent基类定义"""

from abc import ABC
from typing import Any, Dict, List, Optional, TYPE_CHECKING
import asyncio
import time
from .interfaces import IAgent
from .events import AgentEventManager, AgentEvent
from ..workflow.state import WorkflowState
from ..tools.interfaces import ToolCall, ToolResult


if TYPE_CHECKING:
    from .config import AgentConfig
    from src.infrastructure.llm.interfaces import ILLMClient
    from src.infrastructure.tools.executor import IToolExecutor


class BaseAgent(IAgent, ABC):
    """Agent基类，提供通用的执行框架和功能"""
    
    def __init__(
        self, 
        config: 'AgentConfig', 
        llm_client: 'ILLMClient', 
        tool_executor: 'IToolExecutor', 
        event_manager: Optional['AgentEventManager'] = None
    ):
        """初始化Agent基类
        
        Args:
            config: Agent配置
            llm_client: LLM客户端
            tool_executor: 工具执行器
            event_manager: 事件管理器（可选）
        """
        self.config = config
        self.llm_client = llm_client
        self.tool_executor = tool_executor
        self.event_manager = event_manager or AgentEventManager()
        self._execution_stats = {
            "total_executions": 0,
            "total_errors": 0,
            "total_time": 0.0,
            "average_execution_time": 0.0
        }
    
    async def execute(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """执行Agent逻辑，返回更新后的状态
        
        Args:
            state: 当前工作流状态
            config: 执行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        start_time = time.time()

        # 发布执行开始事件
        self.event_manager.publish(AgentEvent.EXECUTION_STARTED, {
            "agent_id": self.config.name,
            "state": state,
            "config": config
        })

        try:
            # 验证状态
            if not self.validate_state(state):
                raise ValueError(f"状态验证失败，Agent {self.config.name} 无法处理当前状态")
            
            # 基础执行逻辑
            result = await self._execute_logic(state, config)

            # 发布执行完成事件
            execution_time = time.time() - start_time
            self.event_manager.publish(AgentEvent.EXECUTION_COMPLETED, {
                "agent_id": self.config.name,
                "input_state": state,
                "output_state": result,
                "config": config,
                "execution_time": execution_time
            })

            # 更新执行统计
            self._update_stats(execution_time, success=True)

            return result
        except Exception as e:
            execution_time = time.time() - start_time
            # 发布错误事件
            self.event_manager.publish(AgentEvent.ERROR_OCCURRED, {
                "agent_id": self.config.name,
                "error": str(e),
                "state": state,
                "config": config,
                "execution_time": execution_time
            })

            # 更新执行统计
            self._update_stats(execution_time, success=False)

            # 重新抛出异常
            raise e
    
    async def _execute_logic(self, state: WorkflowState, config: Dict[str, Any]) -> WorkflowState:
        """执行逻辑的具体实现，子类需要重写此方法
        
        Args:
            state: 当前工作流状态
            config: 执行配置
            
        Returns:
            WorkflowState: 更新后的状态
        """
        # 基础执行逻辑，子类应该重写此方法
        return state
    
    def validate_state(self, state: WorkflowState) -> bool:
        """验证状态是否适合此Agent
        
        Args:
            state: 工作流状态
            
        Returns:
            bool: 是否适合
        """
        # 基础验证逻辑，子类可以重写
        return True
    
    def can_handle(self, state: WorkflowState) -> bool:
        """判断Agent是否能处理当前状态
        
        Args:
            state: 工作流状态
            
        Returns:
            bool: 是否能处理
        """
        # 基础判断逻辑，子类可以重写
        return self.validate_state(state)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """获取Agent能力描述
        
        Returns:
            Dict[str, Any]: 能力描述字典
        """
        return {
            "name": self.config.name,
            "type": self.config.agent_type,
            "description": self.config.description,
            "tools": self.get_available_tools(),
            "max_iterations": self.config.max_iterations,
            "supported_tasks": self._get_supported_tasks()
        }
    
    def get_available_tools(self) -> List[str]:
        """获取可用工具列表
        
        Returns:
            List[str]: 工具名称列表
        """
        # 从配置中获取工具列表
        tools = list(self.config.tools)
        
        # 如果配置了工具集，也需要包含进来
        # 注意：这里需要根据实际的工具执行器接口进行调整
        # 目前暂时只返回配置中的工具列表
        
        return tools
    
    def _get_supported_tasks(self) -> List[str]:
        """获取支持的任务类型，子类可以重写
        
        Returns:
            List[str]: 支持的任务类型列表
        """
        return []
    
    def _update_stats(self, execution_time: float, success: bool = True) -> None:
        """更新执行统计信息
        
        Args:
            execution_time: 执行时间
            success: 是否成功
        """
        self._execution_stats["total_executions"] += 1
        if not success:
            self._execution_stats["total_errors"] += 1
        self._execution_stats["total_time"] += execution_time
        self._execution_stats["average_execution_time"] = (
            self._execution_stats["total_time"] / self._execution_stats["total_executions"]
        )

    @property
    def execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息"""
        return self._execution_stats

    def get_execution_stats(self) -> Dict[str, Any]:
        """获取执行统计信息
        
        Returns:
            Dict[str, Any]: 统计信息字典
        """
        stats = self._execution_stats.copy()
        total_executions = stats["total_executions"]
        if total_executions > 0:
            stats["success_rate"] = (total_executions - stats["total_errors"]) / total_executions
        else:
            stats["success_rate"] = 0.0
        return stats

    async def execute_tool_async(self, tool_call: Dict[str, Any]) -> ToolResult:
        """异步执行工具调用
        
        Args:
            tool_call: 工具调用字典
            
        Returns:
            ToolResult: 工具执行结果
        """
        tool_call_obj = ToolCall(name=tool_call["name"], arguments=tool_call["arguments"])
        return await self.tool_executor.execute_async(tool_call_obj)

    async def execute_with_retry(
        self, 
        state: WorkflowState, 
        config: Dict[str, Any], 
        max_retries: int = 3
    ) -> WorkflowState:
        """带重试机制的执行方法
        
        Args:
            state: 工作流状态
            config: 执行配置
            max_retries: 最大重试次数
            
        Returns:
            WorkflowState: 更新后的状态
        """
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                return await self.execute(state, config)
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