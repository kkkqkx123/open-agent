"""LangGraph工作流集成"""

from typing import Any, Dict, Optional

try:
    from langgraph.graph import StateGraph
    from langchain_core.messages import BaseMessage
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None  # 提供一个默认值以避免未绑定变量错误

from .interfaces import IPromptInjector
from .models import PromptConfig
from .agent_state import AgentState


def get_agent_config() -> PromptConfig:
    """获取Agent配置（示例）"""
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
    """创建Agent工作流"""
    if not LANGGRAPH_AVAILABLE:
        raise ImportError("LangGraph未安装，无法创建工作流")
    
    def inject_prompts_node(state: AgentState) -> AgentState:
        """提示词注入节点"""
        config = get_agent_config()  # 从配置获取
        return prompt_injector.inject_prompts(state, config)
        
    def call_llm_node(state: AgentState) -> AgentState:
        """LLM调用节点"""
        if llm_client is None:
            # 模拟LLM响应
            from .agent_state import HumanMessage
            response = HumanMessage(content="这是一个模拟的LLM响应")
            state.add_message(response)
        else:
            # 使用注入后的提示词调用LLM
            response = llm_client.generate(state.messages)
            state.add_message(response)
        return state
        
    # 构建工作流
    if StateGraph is not None:  # 确保 StateGraph 可用
        workflow = StateGraph(AgentState)
        
        workflow.add_node("inject_prompts", inject_prompts_node)
        workflow.add_node("call_llm", call_llm_node)
        
        workflow.set_entry_point("inject_prompts")
        workflow.add_edge("inject_prompts", "call_llm")
        
        return workflow.compile()
    else:
        raise ImportError("LangGraph的StateGraph不可用")


def create_simple_workflow(prompt_injector: IPromptInjector) -> Dict[str, Any]:
    """创建简单工作流（不依赖LangGraph）"""
    def run_workflow(initial_state: Optional[AgentState] = None) -> AgentState:
        """运行简单工作流"""
        if initial_state is None:
            initial_state = AgentState()
            
        # 注入提示词
        config = get_agent_config()
        state = prompt_injector.inject_prompts(initial_state, config)
        
        # 这里可以添加更多的处理步骤
        return state
    
    return {
        "run": run_workflow,
        "description": "简单提示词注入工作流"
    }