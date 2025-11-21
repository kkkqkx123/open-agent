"""LangGraph工作流集成

提供与LangGraph框架的集成支持。
"""

from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph
from langchain_core.messages import BaseMessage

from ...interfaces.prompts import IPromptInjector, PromptConfig

try:
    from ...core.workflow.states import WorkflowState
except ImportError:
    WorkflowState = Dict[str, Any]  # 回退方案


def get_agent_config() -> PromptConfig:
    """获取Agent配置（示例）
    
    Returns:
        PromptConfig: 示例提示词配置
    """
    return PromptConfig(
        system_prompt="assistant",
        rules=["safety", "format"],
        user_command="data_analysis",
        cache_enabled=True
    )


def create_agent_workflow(
    prompt_injector: IPromptInjector,
    llm_client: Any = None
) -> Any:
    """创建Agent工作流
    
    使用提示词注入器创建一个简单的Agent工作流。
    
    Args:
        prompt_injector: 提示词注入器实例
        llm_client: LLM客户端（可选）
        
    Returns:
        Any: 编译后的工作流图
        
    Raises:
        ImportError: LangGraph不可用
    """
    
    def inject_prompts_node(state: Any) -> Any:
        """提示词注入节点"""
        config = get_agent_config()  # 从配置获取
        result = prompt_injector.inject_prompts(state, config)
        return result  # type: ignore
        
    def call_llm_node(state: Any) -> Any:
        """LLM调用节点"""
        if llm_client is None:
            # 模拟LLM响应
            try:
                from langchain_core.messages import HumanMessage
                response = HumanMessage(content="这是一个模拟的LLM响应")
            except ImportError:
                # 如果无法导入HumanMessage，使用BaseMessage
                response = BaseMessage(content="这是一个模拟的LLM响应", type="human")
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(response)
        else:
            # 使用注入后的提示词调用LLM
            response = llm_client.generate(state.get("messages", []))
            if "messages" not in state:
                state["messages"] = []
            state["messages"].append(response)
        return state  # type: ignore
        
    # 构建工作流
    if StateGraph is not None:  # 确保 StateGraph 可用
        from typing import TypedDict
        
        class AgentState(TypedDict):
            """Agent工作流状态"""
            messages: List[BaseMessage]
        
        workflow = StateGraph(AgentState)  # 使用TypedDict作为状态类型
        
        workflow.add_node("inject_prompts", inject_prompts_node)
        workflow.add_node("call_llm", call_llm_node)
        
        workflow.set_entry_point("inject_prompts")
        workflow.add_edge("inject_prompts", "call_llm")
        
        return workflow.compile()
    else:
        raise ImportError("LangGraph的StateGraph不可用")


def create_simple_workflow(prompt_injector: IPromptInjector) -> Dict[str, Any]:
    """创建简单工作流（不依赖LangGraph）
    
    创建一个不依赖LangGraph的简单工作流。
    
    Args:
        prompt_injector: 提示词注入器实例
        
    Returns:
        Dict[str, Any]: 包含run方法和描述的工作流字典
    """
    def run_workflow(initial_state: Optional[Any] = None) -> Any:
        """运行简单工作流"""
        if initial_state is None:
            initial_state = {}
            
        # 注入提示词
        config = get_agent_config()
        state = prompt_injector.inject_prompts(initial_state, config)
        
        # 这里可以添加更多的处理步骤
        return state  # type: ignore
    
    return {
        "run": run_workflow,
        "description": "简单提示词注入工作流"
    }
