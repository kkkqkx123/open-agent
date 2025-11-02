"""Plan-Execute Agent节点

基于Plan-Execute Agent实现的图节点，提供计划和执行能力。
"""

from typing import Dict, Any, Optional, List
from ..registry import BaseNode, NodeExecutionResult, node
from src.domain.agent.state import AgentState
from src.domain.agent.builtin.plan_execute_agent import PlanExecuteAgent
from src.domain.agent.config import AgentConfig
from src.infrastructure.llm.interfaces import ILLMClient
from src.domain.tools.interfaces import IToolExecutor
from src.domain.agent.events import AgentEventManager
import asyncio


@node("plan_execute_agent_node")
class PlanExecuteAgentNode(BaseNode):
    """Plan-Execute Agent节点
    
    封装Plan-Execute Agent作为图节点，提供计划和执行能力。
    """
    
    def __init__(
        self,
        llm_client: Optional[ILLMClient] = None,
        tool_executor: Optional[IToolExecutor] = None,
        event_manager: Optional[AgentEventManager] = None
    ) -> None:
        """初始化Plan-Execute Agent节点

        Args:
            llm_client: LLM客户端实例
            tool_executor: 工具执行器实例
            event_manager: 事件管理器实例
        """
        if tool_executor is None:
            raise ValueError("tool_executor不能为None")
        self._llm_client = llm_client
        self._tool_executor = tool_executor
        self._event_manager = event_manager or AgentEventManager()
        self._agent: Optional[PlanExecuteAgent] = None
    
    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "plan_execute_agent_node"
    
    def execute(self, state: AgentState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行Plan-Execute Agent逻辑
        
        Args:
            state: 当前Agent状态
            config: 节点配置
            
        Returns:
            NodeExecutionResult: 执行结果
        """
        # 创建或获取Plan-Execute Agent实例
        agent = self._get_or_create_agent(config)
        
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
                    "agent_type": "plan_execute",
                    "iterations": result_state.iteration_count,
                    "task_history": result_state.task_history,
                    "errors": result_state.errors,
                    "current_plan": result_state.context.get("current_plan"),
                    "current_step_index": result_state.context.get("current_step_index"),
                    "plan_completed": result_state.context.get("plan_completed", False)
                }
            )
        except Exception as e:
            # 处理执行错误
            error_msg = f"Plan-Execute Agent执行失败: {str(e)}"
            state.add_error({"error": error_msg, "type": "plan_execute_agent_execution_error"})
            
            return NodeExecutionResult(
                state=state,
                next_node="error_handler",
                metadata={
                    "agent_type": "plan_execute",
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
                    "default": "plan_execute_agent"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "系统提示词",
                    "default": "你是一个使用Plan-Execute算法的智能助手，先制定计划然后逐步执行。"
                },
                "max_iterations": {
                    "type": "integer",
                    "description": "最大迭代次数",
                    "default": 10
                },
                "max_steps": {
                    "type": "integer",
                    "description": "最大计划步骤数",
                    "default": 7
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
                },
                "continue_on_plan_generated": {
                    "type": "boolean",
                    "description": "计划生成后是否继续执行步骤",
                    "default": True
                }
            },
            "required": ["name"]
        }
    
    def _get_or_create_agent(self, config: Dict[str, Any]) -> PlanExecuteAgent:
        """获取或创建Plan-Execute Agent实例
        
        Args:
            config: 节点配置
            
        Returns:
            PlanExecuteAgent: Agent实例
        """
        if self._agent is None:
            # 创建Agent配置
            agent_config = AgentConfig(
                name=config.get("name", "plan_execute_agent"),
                agent_type="plan_execute",
                system_prompt=config.get("system_prompt", "你是一个使用Plan-Execute算法的智能助手，先制定计划然后逐步执行。"),
                max_iterations=config.get("max_iterations", 10),
                tools=config.get("tools", []),
                tool_sets=config.get("tool_sets", []),
                llm=config.get("llm_client", "default")
            )
            
            # 获取LLM客户端
            llm_client = self._get_llm_client(config)
            
            # 创建Agent实例
            self._agent = PlanExecuteAgent(
                config=agent_config,
                llm_client=llm_client,
                tool_executor=self._tool_executor,
                event_manager=self._event_manager
            )
        
        return self._agent
    
    def _get_llm_client(self, config: Dict[str, Any]) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            config: 节点配置
            
        Returns:
            ILLMClient: LLM客户端实例
        """
        if self._llm_client:
            return self._llm_client
        
        # 从依赖容器获取
        try:
            from src.infrastructure.container import get_global_container
            container = get_global_container()
            llm_client = container.get(ILLMClient)
            return llm_client
        except Exception:
            # 如果无法获取客户端，创建模拟客户端
            return self._create_mock_client()
    
    def _create_mock_client(self) -> ILLMClient:
        """创建模拟LLM客户端"""
        from src.infrastructure.llm.clients.mock import MockLLMClient
        from src.infrastructure.llm.config import MockConfig
        
        class MockPlanExecuteClient(MockLLMClient):
            def __init__(self) -> None:
                super().__init__(MockConfig(model_type="mock", model_name="mock-plan-execute"))
            
            async def generate_async(self, messages: Any, parameters: Any = None, **kwargs: Any) -> Any:
                # 模拟异步响应
                from src.infrastructure.llm.models import LLMResponse, TokenUsage
                content = "这是Plan-Execute Agent的模拟计划结果"
                
                # 创建模拟响应对象
                class MockResponse:
                    def __init__(self, content: str) -> None:
                        self.content = content
                
                return MockResponse(content)
        
        return MockPlanExecuteClient()
    
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
        
        # 检查计划是否完成
        if state.context.get("plan_completed", False):
            return config.get("next_node_on_complete", None)
        
        # 检查是否刚生成计划
        if state.task_history:
            last_task = state.task_history[-1]
            if last_task.get("final_state") == "plan_generated":
                # 如果配置为计划生成后继续执行，则返回None继续当前节点
                if config.get("continue_on_plan_generated", True):
                    return None
                # 否则可以转到其他节点（如计划审查节点）
                else:
                    return "plan_review_node"
        
        # 默认继续执行
        return None
    
    def get_plan_status(self, state: AgentState) -> Dict[str, Any]:
        """获取计划状态信息
        
        Args:
            state: Agent状态
            
        Returns:
            Dict[str, Any]: 计划状态信息
        """
        return {
            "has_plan": "current_plan" in state.context,
            "current_plan": state.context.get("current_plan", []),
            "current_step_index": state.context.get("current_step_index", 0),
            "plan_completed": state.context.get("plan_completed", False),
            "total_steps": len(state.context.get("current_plan", []))
        }