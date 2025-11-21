"""LLM节点实现

提供LLM调用功能，避免循环依赖。
"""

from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import AIMessage, SystemMessage
import logging

from .registry import BaseNode, NodeExecutionResult, node
from ...states import WorkflowState
from src.interfaces.llm import ILLMClient
from src.services.llm.scheduling.task_group_manager import TaskGroupManager

logger = logging.getLogger(__name__)


@node("llm_node")
class LLMNode(BaseNode):
    """LLM调用节点"""
    
    def __init__(self, 
                 llm_client: ILLMClient, 
                 task_group_manager: Optional[TaskGroupManager] = None,
                 wrapper_factory: Optional[Any] = None) -> None:
        """初始化LLM节点

        Args:
            llm_client: LLM客户端实例（必需）
            task_group_manager: 任务组管理器（可选）
            wrapper_factory: 包装器工厂（可选）
        """
        self._llm_client = llm_client
        self._task_group_manager = task_group_manager
        self._wrapper_factory = wrapper_factory

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "llm_node"

    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行LLM调用逻辑

        Args:
            state: 当前工作流状态
            config: 节点配置

        Returns:
            NodeExecutionResult: 执行结果
        """
        try:
            # 使用运行时配置，避免循环依赖
            merged_config = config
            
            # 选择LLM客户端
            llm_client = self._select_llm_client(merged_config)
            
            # 构建系统提示词
            system_prompt = self._get_default_system_prompt()
            
            # 准备消息
            messages = self._prepare_messages(state, system_prompt)
            
            # 设置生成参数
            parameters = self._prepare_parameters(merged_config)
            
            # 调用LLM
            response = llm_client.generate(messages=messages, parameters=parameters)
            
            # 更新状态 - 添加LLM响应到消息列表
            ai_message = AIMessage(content=response.content)
            
            # 安全地更新消息列表
            if state.get("messages") is None:
                state.set_value("messages", [])
            state.get("messages", []).append(ai_message)
            
            # 确定下一步
            next_node = self._determine_next_node(response, config)
            
            result_metadata: Dict[str, Any] = {
                "llm_response": response.content,
                "token_usage": getattr(response, "token_usage", None),
                "model_info": llm_client.get_model_info(),
                "system_prompt": system_prompt
            }
            return NodeExecutionResult(state, next_node, result_metadata)
            
        except Exception as e:
            logger.error(f"LLM节点执行失败: {e}")
            return NodeExecutionResult(
                state, 
                None, 
                {"error": str(e), "error_type": type(e).__name__}
            )

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个智能助手，请根据上下文信息提供准确、有用的回答。

请遵循以下原则：
1. 基于提供的工具执行结果和上下文信息回答问题
2. 如果信息不足，请明确说明需要什么额外信息
3. 保持回答简洁明了，重点突出
4. 如果有多个步骤的结果，请按逻辑顺序组织回答
5. 始终保持友好和专业的语调"""

    def _prepare_messages(self, state: WorkflowState, system_prompt: str) -> List[Union[SystemMessage, Any]]:
        """准备消息列表"""
        messages = [SystemMessage(content=system_prompt)]
        
        # 添加历史消息
        if state.get("messages"):
            messages.extend(state.get("messages", []))
        
        return messages

    def _prepare_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成参数"""
        return {
            "temperature": config.get("temperature", 0.7),
            "max_tokens": config.get("max_tokens", 1000),
            "top_p": config.get("top_p", 0.9),
            "frequency_penalty": config.get("frequency_penalty", 0.0),
            "presence_penalty": config.get("presence_penalty", 0.0)
        }

    def _determine_next_node(self, response: Any, config: Dict[str, Any]) -> Optional[str]:
        """确定下一个节点"""
        # 简单实现：根据配置或响应内容决定下一步
        if "next_node" in config:
            return config["next_node"]
        
        # 可以根据响应内容智能判断下一步
        if hasattr(response, 'content') and response.content:
            content = response.content.lower()
            if "完成" in content or "结束" in content:
                return "__end__"
        
        return None

    def _select_llm_client(self, config: Dict[str, Any]) -> ILLMClient:
        """选择LLM客户端"""
        # 简单实现：使用默认客户端
        return self._llm_client

    def get_config_schema(self) -> Dict[str, Any]:
        """获取节点配置Schema"""
        return {
            "type": "object",
            "properties": {
                "temperature": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 2.0,
                    "default": 0.7,
                    "description": "生成温度"
                },
                "max_tokens": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 4096,
                    "default": 1000,
                    "description": "最大生成令牌数"
                },
                "system_prompt": {
                    "type": "string",
                    "description": "系统提示词"
                },
                "next_node": {
                    "type": "string",
                    "description": "下一个节点ID"
                }
            },
            "required": []
        }