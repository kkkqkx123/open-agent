"""Agent执行节点

调用独立的Agent而不是直接实现逻辑
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass

from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState
from src.domain.agent import IAgentManager, IAgentEventManager, AgentEvent
from src.infrastructure.container import IDependencyContainer
from ..node_config_loader import get_node_config_loader


@node("agent_execution_node")
class AgentExecutionNode(BaseNode):
    """Agent执行节点"""
    
    def __init__(self, agent_manager: Optional[IAgentManager] = None, event_manager: Optional[IAgentEventManager] = None) -> None:
        """初始化Agent执行节点
        
        Args:
            agent_manager: Agent管理器实例
            event_manager: 事件管理器实例
        """
        self._agent_manager = agent_manager
        self._event_manager = event_manager
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "agent_execution_node"
    
    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行Agent逻辑
        
        Args:
            state: 当前Agent状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 合并默认配置和运行时配置
        config_loader = get_node_config_loader()
        merged_config = config_loader.merge_configs(self.node_type, config)
        
        # 获取Agent管理器
        agent_manager = self._get_agent_manager(merged_config)
        
        # 获取事件管理器
        event_manager = self._get_event_manager()
        
        # 发布节点执行开始事件
        if event_manager:
            event_manager.publish(AgentEvent.EXECUTION_STARTED, {
                "node_type": "agent_execution_node",
                "agent_id": state.context.get("current_agent_id", merged_config.get("default_agent_id", "default_agent")),
                "state": state,
                "config": merged_config
            })
        
        # 根据当前状态选择合适的Agent
        agent_id = state.context.get("current_agent_id", merged_config.get("default_agent_id", "default_agent"))
        
        # 执行Agent
        try:
            # 使用AgentManager执行Agent（同步版本）
            # 由于AgentManager的execute_agent是异步的，我们需要使用事件循环来运行它
            import asyncio
            
            # 使用更现代的事件循环处理方式
            try:
                # 尝试获取当前运行的事件循环
                loop = asyncio.get_running_loop()
            except RuntimeError:
                # 如果没有运行的事件循环，创建一个新的并运行
                loop = asyncio.new_event_loop()
                try:
                    updated_state = loop.run_until_complete(agent_manager.execute_agent(agent_id, state))
                finally:
                    loop.close()
            else:
                # 如果有运行的事件循环，直接运行
                updated_state = loop.run_until_complete(agent_manager.execute_agent(agent_id, state))
            
            # 确定下一个节点
            next_node = self._determine_next_node(updated_state, config)
            
            # 发布节点执行完成事件
            if event_manager:
                event_manager.publish(AgentEvent.EXECUTION_COMPLETED, {
                    "node_type": "agent_execution_node",
                    "agent_id": agent_id,
                    "input_state": state,
                    "output_state": updated_state,
                    "next_node": next_node
                })
            
            return NodeExecutionResult(
                state=updated_state,
                next_node=next_node,
                metadata={
                    "agent_execution": "success",
                    "agent_id": agent_id,
                    "task_history": updated_state.task_history
                }
            )
        except Exception as e:
            # 如果Agent执行失败，记录错误并返回错误状态
            error_msg = f"Agent execution failed: {str(e)}"
            state.add_error({"error": error_msg, "type": "agent_execution_error"})
            
            # 发布错误事件
            if event_manager:
                event_manager.publish(AgentEvent.ERROR_OCCURRED, {
                    "node_type": "agent_execution_node",
                    "agent_id": agent_id,
                    "error": error_msg,
                    "state": state
                })
            
            return NodeExecutionResult(
                state=state,
                next_node="error_handler",  # 指向错误处理节点
                metadata={
                    "agent_execution": "failed",
                    "agent_id": agent_id,
                    "error": error_msg
                }
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "default_agent_id": {
                    "type": "string",
                    "description": "默认Agent ID"
                },
                "agent_selection_strategy": {
                    "type": "string",
                    "description": "Agent选择策略",
                    "enum": ["context_based", "config_based", "rule_based"],
                    "default": "config_based"
                },
                "fallback_agent_id": {
                    "type": "string",
                    "description": "备用Agent ID"
                }
            },
            "required": ["default_agent_id"]
        }
    
    def _get_agent_manager(self, config: Dict[str, Any]) -> IAgentManager:
        """获取Agent管理器
        
        Args:
            config: 节点配置
            
        Returns:
            IAgentManager: Agent管理器实例
        """
        if self._agent_manager:
            return self._agent_manager
        # 从依赖容器获取Agent管理器
        try:
            from src.infrastructure.container import get_global_container
            container = get_global_container()
            # 使用正确的容器方法
            agent_manager: IAgentManager = container.get(IAgentManager)  # type: ignore
            return agent_manager
        except Exception as e:
            # 如果无法从容器获取，抛出异常
            raise ValueError(f"Could not get AgentManager from container: {e}")
    
    def _get_event_manager(self) -> Optional[IAgentEventManager]:
        """获取事件管理器
        
        Returns:
            Optional[IAgentEventManager]: 事件管理器实例
        """
        if self._event_manager:
            return self._event_manager
        
        # 尝试从依赖容器获取事件管理器
        try:
            from src.infrastructure.container import get_global_container
            container = get_global_container()
            # 尝试获取事件管理器服务
            event_manager: IAgentEventManager = container.get(IAgentEventManager)  # type: ignore
            return event_manager
        except Exception:
            # 如果无法获取，返回None
            return None
    
    def _determine_next_node(self, state: AgentState, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点
        
        Args:
            state: 更新后的状态
            config: 节点配置
            
        Returns:
            Optional[str]: 下一个节点名称
        """
        # 检查任务是否完成
        if self._is_task_completed(state):
            next_node = config.get("on_task_completed", None)
            return str(next_node) if next_node is not None else None
        
        # 检查是否需要切换到其他Agent
        if self._needs_agent_switch(state, config):
            return "agent_selection_node"  # 返回到Agent选择节点
        
        # 默认返回None，表示继续当前工作流
        default_next = config.get("default_next_node", None)
        return str(default_next) if default_next is not None else None
    
    def _is_task_completed(self, state: AgentState) -> bool:
        """检查任务是否完成
        
        Args:
            state: 当前状态
            
        Returns:
            bool: 任务是否完成
        """
        # 检查迭代次数是否达到最大值
        if state.iteration_count >= state.max_iterations:
            return True
        
        # 从配置获取任务完成指示词
        config_loader = get_node_config_loader()
        completion_indicators = config_loader.get_config_value(
            self.node_type,
            "task_completion_indicators",
            ["task_completed", "任务完成", "已完成"]
        )
        
        # 检查状态中是否有完成标记
        for message in state.messages:
            if hasattr(message, 'content'):
                content_lower = message.content.lower()
                if any(indicator.lower() in content_lower for indicator in completion_indicators):
                    return True
        
        return False
    
    def _needs_agent_switch(self, state: AgentState, config: Dict[str, Any]) -> bool:
        """检查是否需要切换Agent
        
        Args:
            state: 当前状态
            config: 节点配置
            
        Returns:
            bool: 是否需要切换Agent
        """
        # 合并默认配置和运行时配置
        config_loader = get_node_config_loader()
        merged_config = config_loader.merge_configs(self.node_type, config)
        
        # 根据配置的策略决定是否需要切换Agent
        strategy = merged_config.get("agent_selection_strategy", "config_based")
        
        if strategy == "context_based":
            # 基于上下文决定是否切换
            current_context = state.context
            # 这里可以实现复杂的上下文分析逻辑
            return False
        elif strategy == "rule_based":
            # 基于规则决定是否切换
            # 这里可以实现基于规则的切换逻辑
            return False
        else:
            # config_based - 默认不切换
            return False


async def agent_execution_node(state: AgentState) -> AgentState:
    """Agent执行节点函数版本，用于测试和简单调用"""
    node = AgentExecutionNode()
    result = node.execute(state, {})
    return result.state