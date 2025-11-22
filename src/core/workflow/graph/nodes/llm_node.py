"""LLM节点实现

提供LLM调用功能，集成提示词系统。
"""

from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import logging

from .registry import BaseNode, NodeExecutionResult, node
from ...states import WorkflowState
from src.interfaces.llm import ILLMClient
from src.services.llm.scheduling.task_group_manager import TaskGroupManager
from ...services.prompt_service import get_workflow_prompt_service

logger = logging.getLogger(__name__)


@node("llm_node")
class LLMNode(BaseNode):
    """LLM调用节点，集成提示词系统"""
    
    def __init__(self,
                 llm_client: Optional[ILLMClient] = None,
                 task_group_manager: Optional[TaskGroupManager] = None,
                 wrapper_factory: Optional[Any] = None) -> None:
        """初始化LLM节点

        Args:
            llm_client: LLM客户端实例（可选，可在运行时设置）
            task_group_manager: 任务组管理器（可选）
            wrapper_factory: 包装器工厂（可选）
        """
        self._llm_client = llm_client
        self._task_group_manager = task_group_manager
        self._wrapper_factory = wrapper_factory
        self._prompt_service = get_workflow_prompt_service()

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "llm_node"

    def execute(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """执行LLM调用逻辑"""
        try:
            # 使用运行时配置，避免循环依赖
            import asyncio
            
            # 在同步方法中运行异步逻辑
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._execute_async(state, config))
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"LLM节点执行失败: {e}")
            return NodeExecutionResult(
                state,
                None,
                {"error": str(e), "error_type": type(e).__name__}
            )
    
    async def _execute_async(self, state: WorkflowState, config: Dict[str, Any]) -> NodeExecutionResult:
        """异步执行逻辑"""
        try:
            # 预处理配置
            processed_config = await self._preprocess_config(state, config)
            
            # 选择LLM客户端
            llm_client = self._select_llm_client(processed_config)
            
            # 准备消息（使用提示词服务）
            messages = await self._prepare_messages_with_prompts(state, processed_config)
            
            # 设置生成参数
            parameters = self._prepare_parameters(processed_config)
            
            # 调用LLM
            response = llm_client.generate(messages=messages, parameters=parameters)
            
            # 更新状态 - 添加LLM响应到消息列表
            ai_message = AIMessage(content=response.content)
            
            # 安全地更新消息列表
            if state.get("messages") is None:
                state.set_value("messages", [])
            state.get("messages", []).append(ai_message)
            
            # 确定下一步
            next_node = self._determine_next_node(response, processed_config)
            
            # 构建结果元数据
            result_metadata: Dict[str, Any] = {
                "llm_response": response.content,
                "token_usage": getattr(response, "token_usage", None),
                "model_info": llm_client.get_model_info(),
                "prompt_info": self._get_prompt_info(processed_config)
            }
            return NodeExecutionResult(state, next_node, result_metadata)
            
        except Exception as e:
            logger.error(f"LLM节点异步执行失败: {e}")
            raise
    
    async def _preprocess_config(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """预处理配置"""
        try:
            # 使用提示词服务处理配置
            processed_config = await self._prompt_service.process_node_input(
                "llm_node", config, state, config
            )
            return processed_config
        except Exception as e:
            logger.warning(f"配置预处理失败，使用原始配置: {e}")
            return config

    def _get_default_system_prompt(self) -> str:
        """获取默认系统提示词"""
        return """你是一个智能助手，请根据上下文信息提供准确、有用的回答。

请遵循以下原则：
1. 基于提供的工具执行结果和上下文信息回答问题
2. 如果信息不足，请明确说明需要什么额外信息
3. 保持回答简洁明了，重点突出
4. 如果有多个步骤的结果，请按逻辑顺序组织回答
5. 始终保持友好和专业的语调"""

    async def _prepare_messages_with_prompts(self, state: WorkflowState, config: Dict[str, Any]) -> List[Union[SystemMessage, Any]]:
        """准备消息列表（使用提示词服务）"""
        messages = []
        
        # 准备基础消息
        base_messages = []
        
        # 添加系统提示词
        system_prompt = self._get_system_prompt_from_config(config)
        if system_prompt:
            base_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        if state.get("messages"):
            base_messages.extend(state.get("messages", []))
        
        # 使用提示词服务构建完整消息列表
        prompt_ids = []
        system_prompt_id = config.get("system_prompt_id")
        user_prompt_id = config.get("user_prompt_id")
        
        if system_prompt_id:
            prompt_ids.append(system_prompt_id)
        if user_prompt_id:
            prompt_ids.append(user_prompt_id)
        
        # 准备上下文
        context = self._prepare_prompt_context(state, config)
        
        # 添加用户输入
        user_input = config.get("user_input")
        
        # 使用提示词服务构建消息
        messages = await self._prompt_service.build_messages(
            base_messages,
            prompt_ids if prompt_ids else None,
            user_input,
            context
        )
        
        return messages

    # 注意：这个方法已被 _prepare_messages_with_prompts 替代
    # 保留是为了向后兼容，但不再使用

    def _prepare_prompt_context(self, state: WorkflowState, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备提示词上下文"""
        context = {}
        
        # 添加状态数据
        if state:
            context.update(state.get("data", {}))
        
        # 添加配置变量
        prompt_variables = config.get("prompt_variables", {})
        context.update(prompt_variables)
        
        # 添加系统变量
        context.update({
            "node_id": "llm_node",
            "timestamp": str(state.get("timestamp", "")),
            "max_tokens": config.get("max_tokens", 1000),
            "temperature": config.get("temperature", 0.7)
        })
        
        return context

    def _get_system_prompt_from_config(self, config: Dict[str, Any]) -> str:
        """从配置获取系统提示词"""
        # 优先使用配置中的系统提示词
        if "system_prompt" in config:
            return config["system_prompt"]
        
        # 回退到默认提示词
        return self._get_default_system_prompt()

    def _get_prompt_info(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """获取提示词信息"""
        prompt_info = {
            "using_prompt_system": self._prompt_service.get_service_info()["configured"],
            "system_prompt_id": config.get("system_prompt_id"),
            "user_prompt_id": config.get("user_prompt_id"),
            "prompt_variables": config.get("prompt_variables", {})
        }
        
        return prompt_info

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
        if self._llm_client is None:
            raise ValueError("LLM客户端未设置")
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
                    "description": "系统提示词（传统方式）"
                },
                "system_prompt_id": {
                    "type": "string",
                    "description": "系统提示词ID（提示词系统）"
                },
                "user_prompt_id": {
                    "type": "string",
                    "description": "用户提示词ID（提示词系统）"
                },
                "prompt_variables": {
                    "type": "object",
                    "description": "提示词变量"
                },
                "user_input": {
                    "type": "string",
                    "description": "用户输入"
                },
                "next_node": {
                    "type": "string",
                    "description": "下一个节点ID"
                }
            },
            "required": []
        }

    def configure_prompt_system(self, prompt_registry, prompt_injector) -> None:
        """配置提示词系统"""
        self._prompt_service.configure(prompt_registry, prompt_injector)
        logger.info("LLM节点已配置提示词系统")
    
    def set_llm_client(self, llm_client: ILLMClient) -> None:
        """设置LLM客户端"""
        self._llm_client = llm_client
    
    async def validate_prompt_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证提示词配置"""
        return await self._prompt_service.validate_prompt_configuration(config)
    
    async def process_content(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理内容（通用方法）"""
        context = context or {}
        return await self._prompt_service.process_prompt_content(content, context)