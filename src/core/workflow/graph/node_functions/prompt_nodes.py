"""提示词相关节点函数

提供提示词注入和处理相关的节点函数实现。
"""

from typing import Any, Dict, Optional, TYPE_CHECKING
import logging

from ....interfaces.prompts import IPromptInjector, PromptConfig

if TYPE_CHECKING:
    from ....interfaces.state import IWorkflowState

logger = logging.getLogger(__name__)


def create_prompt_injection_node(prompt_injector: IPromptInjector, 
                                prompt_config: Optional[PromptConfig] = None):
    """创建提示词注入节点函数
    
    Args:
        prompt_injector: 提示词注入器实例
        prompt_config: 提示词配置，如果为None则使用默认配置
        
    Returns:
        Callable: 提示词注入节点函数
    """
    def prompt_injection_node(state: "IWorkflowState") -> "IWorkflowState":
        """提示词注入节点
        
        将配置的提示词注入到工作流状态中。
        
        Args:
            state: 工作流状态
            
        Returns:
            IWorkflowState: 注入提示词后的状态
        """
        try:
            if prompt_config:
                result = prompt_injector.inject_prompts(state, prompt_config)
            else:
                # 使用默认配置
                default_config = PromptConfig(
                    system_prompt="assistant",
                    rules=["safety", "format"],
                    user_command="data_analysis",
                    cache_enabled=True
                )
                result = prompt_injector.inject_prompts(state, default_config)
            
            logger.debug("提示词注入完成")
            return result
        except Exception as e:
            logger.error(f"提示词注入失败: {e}")
            # 返回原始状态，避免工作流中断
            return state
    
    return prompt_injection_node


def create_llm_call_node(llm_client: Optional[Any] = None, 
                        timeout: int = 30,
                        retry_on_failure: bool = True,
                        max_retries: int = 3):
    """创建LLM调用节点函数
    
    Args:
        llm_client: LLM客户端实例
        timeout: 超时时间（秒）
        retry_on_failure: 是否在失败时重试
        max_retries: 最大重试次数
        
    Returns:
        Callable: LLM调用节点函数
    """
    def llm_call_node(state: "IWorkflowState") -> "IWorkflowState":
        """LLM调用节点
        
        调用LLM生成响应。
        
        Args:
            state: 工作流状态
            
        Returns:
            IWorkflowState: 包含LLM响应的状态
        """
        try:
            if llm_client is None:
                # 模拟LLM响应
                try:
                    from langchain_core.messages import HumanMessage
                    response = HumanMessage(content="这是一个模拟的LLM响应")
                except ImportError:
                    # 如果无法导入HumanMessage，使用BaseMessage
                    from langchain_core.messages import BaseMessage
                    response = BaseMessage(content="这是一个模拟的LLM响应", type="human")
                
                # 安全访问messages列表
                if "messages" not in state:
                    state["messages"] = []
                state["messages"].append(response)
            else:
                # 使用真实的LLM客户端
                messages = state.get("messages", [])
                response = llm_client.generate(messages)
                
                # 安全访问messages列表
                if "messages" not in state:
                    state["messages"] = []
                state["messages"].append(response)
            
            logger.debug("LLM调用完成")
            return state
        except Exception as e:
            logger.error(f"LLM调用失败: {e}")
            # 添加错误信息到状态
            if "errors" not in state:
                state["errors"] = []
            state["errors"].append(f"LLM调用失败: {str(e)}")
            return state
    
    return llm_call_node


def create_prompt_validation_node():
    """创建提示词验证节点函数
    
    Returns:
        Callable: 提示词验证节点函数
    """
    def prompt_validation_node(state: "IWorkflowState") -> "IWorkflowState":
        """提示词验证节点
        
        验证状态中的提示词是否有效。
        
        Args:
            state: 工作流状态
            
        Returns:
            IWorkflowState: 验证后的状态
        """
        try:
            messages = state.get("messages", [])
            if not messages:
                logger.warning("状态中没有消息，提示词验证失败")
                if "validation_errors" not in state:
                    state["validation_errors"] = []
                state["validation_errors"].append("状态中没有消息")
                return state
            
            # 检查是否有系统消息
            has_system_message = False
            for message in messages:
                if hasattr(message, 'type') and message.type == 'system':
                    has_system_message = True
                    break
            
            if not has_system_message:
                logger.warning("状态中没有系统消息")
                if "validation_warnings" not in state:
                    state["validation_warnings"] = []
                state["validation_warnings"].append("状态中没有系统消息")
            
            logger.debug("提示词验证完成")
            return state
        except Exception as e:
            logger.error(f"提示词验证失败: {e}")
            if "validation_errors" not in state:
                state["validation_errors"] = []
            state["validation_errors"].append(f"提示词验证失败: {str(e)}")
            return state
    
    return prompt_validation_node


def create_prompt_caching_node(cache_enabled: bool = True):
    """创建提示词缓存节点函数
    
    Args:
        cache_enabled: 是否启用缓存
        
    Returns:
        Callable: 提示词缓存节点函数
    """
    def prompt_caching_node(state: "IWorkflowState") -> "IWorkflowState":
        """提示词缓存节点
        
        处理提示词缓存逻辑。
        
        Args:
            state: 工作流状态
            
        Returns:
            IWorkflowState: 处理缓存后的状态
        """
        try:
            if not cache_enabled:
                logger.debug("提示词缓存已禁用")
                return state
            
            # 检查是否有缓存键
            cache_key = state.get("prompt_cache_key")
            if cache_key:
                # 这里可以实现具体的缓存逻辑
                # 目前只是标记已处理缓存
                state["prompt_cache_processed"] = True
                logger.debug(f"提示词缓存处理完成，缓存键: {cache_key}")
            else:
                logger.debug("没有提示词缓存键")
            
            return state
        except Exception as e:
            logger.error(f"提示词缓存处理失败: {e}")
            return state
    
    return prompt_caching_node


# 预定义的节点函数配置
PROMPT_NODE_CONFIGS = {
    "prompt_injection": {
        "description": "提示词注入节点",
        "timeout": 10,
        "retry_on_failure": False,
        "max_retries": 1
    },
    "llm_call": {
        "description": "LLM调用节点",
        "timeout": 30,
        "retry_on_failure": True,
        "max_retries": 3
    },
    "prompt_validation": {
        "description": "提示词验证节点",
        "timeout": 5,
        "retry_on_failure": False,
        "max_retries": 1
    },
    "prompt_caching": {
        "description": "提示词缓存节点",
        "timeout": 5,
        "retry_on_failure": False,
        "max_retries": 1
    }
}


def get_prompt_node_config(node_type: str) -> Dict[str, Any]:
    """获取提示词节点配置
    
    Args:
        node_type: 节点类型
        
    Returns:
        Dict[str, Any]: 节点配置
    """
    return PROMPT_NODE_CONFIGS.get(node_type, {})