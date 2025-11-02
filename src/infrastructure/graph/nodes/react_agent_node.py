"""ReAct Agent节点

基于ReAct Agent实现的图节点，提供推理和行动能力。
"""

from typing import Dict, Any, Optional
from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState
from src.domain.agent.builtin.react_agent import ReActAgent
from src.domain.agent.config import AgentConfig
from src.infrastructure.llm.interfaces import ILLMClient
from src.domain.tools.interfaces import IToolExecutor
from src.domain.agent.events import AgentEventManager
from ..node_config_loader import get_node_config_loader
import asyncio


@node("react_agent_node")
class ReActAgentNode(BaseNode):
    """ReAct Agent节点
    
    封装ReAct Agent作为图节点，提供推理和行动能力。
    """
    
    def __init__(
        self,
        llm_client: ILLMClient,
        tool_executor: IToolExecutor,
        event_manager: Optional[AgentEventManager] = None
    ) -> None:
        """初始化ReAct Agent节点

        Args:
        llm_client: LLM客户端实例（必需）
        tool_executor: 工具执行器实例（必需）
        event_manager: 事件管理器实例（可选）
        """
        self._llm_client = llm_client
        self._tool_executor = tool_executor
        self._event_manager = event_manager or AgentEventManager()
        self._agent: Optional[ReActAgent] = None
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "react_agent_node"
    
    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行ReAct Agent逻辑
        
        Args:
            state: 当前Agent状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 合并默认配置和运行时配置
        config_loader = get_node_config_loader()
        merged_config = config_loader.merge_configs(self.node_type, config)
        
        # 创建或获取ReAct Agent实例
        agent = self._get_or_create_agent(merged_config)
        
        # 执行Agent逻辑
        try:
            # 使用事件循环处理异步执行
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                try:
                    result_state = loop.run_until_complete(agent.execute(state, config))
                finally:
                    loop.close()
            else:
                result_state = loop.run_until_complete(agent.execute(state, config))
            
            # 确定下一个节点
            next_node = self._determine_next_node(result_state, config)
            
            return NodeExecutionResult(
                state=result_state,
                next_node=next_node,
                metadata={
                    "agent_type": "react",
                    "iterations": result_state.iteration_count,
                    "task_history": result_state.task_history,
                    "errors": result_state.errors
                }
            )
        except Exception as e:
            # 处理执行错误
            error_msg = f"ReAct Agent执行失败: {str(e)}"
            state.add_error({"error": error_msg, "type": "react_agent_execution_error"})
            
            return NodeExecutionResult(
                state=state,
                next_node="error_handler",
                metadata={
                    "agent_type": "react",
                    "error": error_msg
                }
            )
    
    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Agent名称",
                    "default": "react_agent"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "系统提示词",
                    "default": "你是一个使用ReAct算法的智能助手，通过推理和行动来解决问题。"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大迭代次数",
                    "default": 10
                },
                "tools": {
                    "type": "array",
                    "description": "可用工具列表",
                    "items": {"type": "string"},
                    "default": []
                },
                "tool_sets": {
                    "type": "array",
                    "description": "可用工具集列表",
                    "items": {"type": "string"},
                    "default": []
                },
                "llm_client": {
                    "type": "string",
                    "description": "LLM客户端配置名称"
                },
                "next_node_on_complete": {
                    "type": "string",
                    "description": "任务完成后的下一个节点"
                },
                "next_node_on_error": {
                    "type": "string",
                    "description": "发生错误后的下一个节点",
                    "default": "error_handler"
                }
            },
            "required": ["name"]
        }
    
    def _get_or_create_agent(self, config: Dict[str, Any]) -> ReActAgent:
        """获取或创建ReAct Agent实例
        
        Args:
            config: 节点配置
            
        Returns:
            ReActAgent: Agent实例
        """
        if self._agent is None:
            # 工具执行器已在构造函数中验证为必需参数
            
            # 创建Agent配置
            agent_config = AgentConfig(
                name=config.get("name", "react_agent"),
                agent_type="react",
                system_prompt=config.get("system_prompt", "你是一个使用ReAct算法的智能助手，通过推理和行动来解决问题。"),
                max_iterations=config.get("max_iterations", 10),
                tools=config.get("tools", []),
                tool_sets=config.get("tool_sets", []),
                llm=config.get("llm_client", "default")
            )
            
            # 使用注入的LLM客户端
            llm_client = self._llm_client
            
            # 创建Agent实例
            self._agent = ReActAgent(
                config=agent_config,
                llm_client=llm_client,
                tool_executor=self._tool_executor,
                event_manager=self._event_manager
            )
        
        return self._agent
    
    
    def _determine_next_node(self, state: AgentState, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点
        
        Args:
            state: 执行后的状态
            config: 节点配置
            
        Returns:
            Optional[str]: 下一个节点名称
        """
        # 检查是否有错误
        if state.errors:
            return config.get("next_node_on_error", "error_handler")
        
        # 检查是否完成
        if state.iteration_count >= state.max_iterations:
            return config.get("next_node_on_complete", None)
        
        # 检查任务历史中是否有最终答案
        if state.task_history:
            last_task = state.task_history[-1]
            if last_task.get("final_state") == "completed":
                return config.get("next_node_on_complete", None)
        
        # 默认继续执行
        return None