"""LLM节点实现

提供LLM调用功能，集成提示词系统。
"""

from typing import Dict, Any, List, Optional, Union
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage
import logging

from .registry import node
from .async_node import AsyncNode
from src.interfaces.workflow.graph import NodeExecutionResult
from src.interfaces.state.interfaces import IState
from src.interfaces.llm import ILLMClient
from src.services.llm.scheduling.task_group_manager import TaskGroupManager

logger = logging.getLogger(__name__)


@node("llm_node")
class LLMNode(AsyncNode):
    """LLM调用节点，集成提示词系统
    
    这是一个异步节点，用于调用大语言模型API。
    
    特点：
    - execute_async() 有真实的异步实现，直接调用LLM
    - execute() 会创建新事件循环（仅作为兼容性提供）
    - 推荐在AsyncMode中使用execute_async()调用
    """
    
    def __init__(self,
                 llm_client: Optional[ILLMClient] = None,
                 task_group_manager: Optional[TaskGroupManager] = None,
                 wrapper_factory: Optional[Any] = None,
                 prompt_service: Optional[Any] = None) -> None:
        """初始化LLM节点

        Args:
            llm_client: LLM客户端实例（可选，可在运行时设置）
            task_group_manager: 任务组管理器（可选）
            wrapper_factory: 包装器工厂（可选）
            prompt_service: 提示词服务（可选，通过依赖注入提供）
        """
        self._llm_client = llm_client
        self._task_group_manager = task_group_manager
        self._wrapper_factory = wrapper_factory
        self._prompt_service = prompt_service

    @property
    def node_type(self) -> str:
        """节点类型标识"""
        return "llm_node"

    async def execute_async(self, state: IState, config: Dict[str, Any]) -> NodeExecutionResult:
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
            response = await llm_client.generate(messages=messages, parameters=parameters)
            
            # 更新状态 - 添加LLM响应到消息列表
            ai_message = AIMessage(content=response.content)
            
            # 安全地更新消息列表
            if state.get_data("messages") is None:
                state.set_data("messages", [])
            state.get_data("messages", []).append(ai_message)
            
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
    
    async def _preprocess_config(self, state: IState, config: Dict[str, Any]) -> Dict[str, Any]:
        """预处理配置"""
        try:
            # 使用提示词服务处理配置（如果已注入）
            if self._prompt_service and hasattr(self._prompt_service, 'process_node_input'):
                processed_config = await self._prompt_service.process_node_input(
                    "llm_node", config, state, config
                )
                return processed_config
            return config
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

    async def _prepare_messages_with_prompts(self, state: IState, config: Dict[str, Any]) -> List[Union[SystemMessage, Any]]:
        """准备消息列表（使用提示词服务，支持缓存和多种配置方式）"""
        # 生成缓存键
        cache_key = self._generate_prompt_cache_key(config)
        
        # 尝试从缓存获取消息
        cached_messages = await self._get_cached_messages(state, cache_key)
        if cached_messages:
            logger.debug(f"LLM节点消息缓存命中: {cache_key}")
            return cached_messages
        
        # 解析和处理提示词
        messages = await self._resolve_and_process_prompts(state, config)
        
        # 缓存处理结果
        await self._cache_processed_messages(state, cache_key, messages)
        
        return messages
    
    def _generate_prompt_cache_key(self, config: Dict[str, Any]) -> str:
        """生成提示词缓存键"""
        from ....common.utils.cache_key_generator import CacheKeyGenerator
        
        # 提取影响提示词的关键配置
        key_config = {
            "system_prompt": config.get("system_prompt"),
            "system_prompt_ref": config.get("system_prompt_ref"),
            "system_prompt_template": config.get("system_prompt_template"),
            "system_prompt_parts": config.get("system_prompt_parts"),
            "user_prompt_id": config.get("user_prompt_id"),
            "user_input": config.get("user_input"),
            "prompt_variables": config.get("prompt_variables", {}),
            "prompt_ids": config.get("prompt_ids", [])
        }
        
        return CacheKeyGenerator.generate_params_key(key_config)
    
    async def _get_cached_messages(self, state: IState, cache_key: str) -> Optional[List[Union[SystemMessage, Any]]]:
        """获取缓存的消息"""
        try:
            # 检查是否启用缓存
            cache_scope = state.get_data("prompt_cache_scope", "state")
            if cache_scope == "none":
                return None
            
            # 从提示词服务获取缓存（如果已注入）
            if self._prompt_service and hasattr(self._prompt_service, 'resolve_prompt_references'):
                cached_content = await self._prompt_service.resolve_prompt_references(
                    [cache_key],
                    self._prepare_prompt_context(state, {}),
                    cache_scope=cache_scope
                )
                
                if cached_content:
                    # 将缓存的内容转换为消息列表
                    messages = []
                    for content in cached_content:
                        if hasattr(content, 'content'):
                            messages.append(SystemMessage(content=content.content))
                    return messages
            
        except Exception as e:
            logger.warning(f"获取缓存消息失败: {e}")
        
        return None
    
    async def _cache_processed_messages(self, state: IState, cache_key: str, messages: List[Union[SystemMessage, Any]]) -> None:
        """缓存处理后的消息"""
        try:
            # 检查是否启用缓存
            cache_scope = state.get_data("prompt_cache_scope", "state")
            cache_ttl = state.get_data("prompt_cache_ttl", 3600)
            
            if cache_scope == "none":
                return
            
            # 如果未注入提示词服务，跳过缓存
            if not self._prompt_service or not hasattr(self._prompt_service, 'process_prompt_content'):
                return
            
            # 将消息列表转换为可缓存的内容
            content_parts = []
            for msg in messages:
                if hasattr(msg, 'content') and isinstance(msg.content, str):
                    content_parts.append(msg.content)
            content = "\n".join(content_parts)
            
            # 缓存内容
            await self._prompt_service.process_prompt_content(
                content,
                {"cache_key": cache_key},
                cache_scope=cache_scope,
                cache_ttl=cache_ttl
            )
            
        except Exception as e:
            logger.warning(f"缓存处理消息失败: {e}")
    
    async def _resolve_and_process_prompts(self, state: IState, config: Dict[str, Any]) -> List[Union[SystemMessage, Any]]:
        """解析和处理提示词"""
        messages = []
        
        # 准备基础消息
        base_messages = []
        
        # 处理系统提示词（支持多种配置方式）
        system_prompt = await self._resolve_system_prompt(config, state)
        if system_prompt:
            base_messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史消息
        if state.get_data("messages"):
            base_messages.extend(state.get_data("messages", []))
        
        # 处理提示词引用
        prompt_ids = self._extract_prompt_ids(config)
        
        # 准备上下文
        context = self._prepare_prompt_context(state, config)
        
        # 添加用户输入
        user_input = config.get("user_input")
        
        # 使用提示词服务构建消息（如果已注入）
        if self._prompt_service and hasattr(self._prompt_service, 'build_messages'):
            messages = await self._prompt_service.build_messages(
                base_messages,
                prompt_ids if prompt_ids else None,
                user_input,
                context
            )
        else:
            messages = base_messages
            if user_input:
                messages.append(HumanMessage(content=user_input))
        
        return messages
    
    async def _resolve_system_prompt(self, config: Dict[str, Any], state: IState) -> Optional[str]:
        """解析系统提示词（支持多种配置方式）"""
        # 1. 直接定义（向后兼容）
        if "system_prompt" in config:
            return config["system_prompt"]
        
        # 2. 引用文件化提示词
        if "system_prompt_ref" in config:
            prompt_ref = config["system_prompt_ref"]
            try:
                # 检查提示词服务是否可用
                if self._prompt_service and hasattr(self._prompt_service, 'resolve_prompt_references'):
                    context = self._prepare_prompt_context(state, config)
                    
                    # 尝试从缓存获取
                    cached_prompt = await self._prompt_service.resolve_prompt_references(
                        [prompt_ref],
                        context,
                        cache_scope=config.get("prompt_cache_scope", "state")
                    )
                    
                    if cached_prompt:
                        return cached_prompt[0].content if hasattr(cached_prompt[0], 'content') else str(cached_prompt[0])
                
            except Exception as e:
                logger.warning(f"解析系统提示词引用失败: {prompt_ref}, 错误: {e}")
        
        # 3. 模板化提示词
        if "system_prompt_template" in config:
            try:
                # 检查提示词服务是否可用
                if self._prompt_service and hasattr(self._prompt_service, 'process_prompt_content'):
                    template = config["system_prompt_template"]
                    context = self._prepare_prompt_context(state, config)
                    
                    # 处理模板变量
                    processed_template = await self._prompt_service.process_prompt_content(
                        template,
                        context,
                        cache_scope=config.get("prompt_cache_scope", "state")
                    )
                    
                    return processed_template
                
            except Exception as e:
                logger.warning(f"处理系统提示词模板失败: {e}")
        
        # 4. 组合式提示词
        if "system_prompt_parts" in config:
            try:
                # 检查提示词服务是否可用
                if self._prompt_service and hasattr(self._prompt_service, 'resolve_prompt_references'):
                    parts = config["system_prompt_parts"]
                    context = self._prepare_prompt_context(state, config)
                    
                    combined_prompt = ""
                    for part in parts:
                        # 解析每个部分
                        part_content = await self._prompt_service.resolve_prompt_references(
                            [part],
                            context,
                            cache_scope=config.get("prompt_cache_scope", "state")
                        )
                        
                        if part_content:
                            combined_prompt += part_content[0].content if hasattr(part_content[0], 'content') else str(part_content[0])
                            combined_prompt += "\n\n"
                    
                    return combined_prompt.strip()
                
            except Exception as e:
                logger.warning(f"处理组合式系统提示词失败: {e}")
        
        # 回退到默认提示词
        return self._get_default_system_prompt()
    
    def _extract_prompt_ids(self, config: Dict[str, Any]) -> List[str]:
        """提取提示词ID"""
        prompt_ids = []
        
        # 传统方式
        system_prompt_id = config.get("system_prompt_id")
        user_prompt_id = config.get("user_prompt_id")
        
        if system_prompt_id:
            prompt_ids.append(system_prompt_id)
        if user_prompt_id:
            prompt_ids.append(user_prompt_id)
        
        # 新的提示词列表方式
        prompt_ids_list = config.get("prompt_ids", [])
        if prompt_ids_list:
            prompt_ids.extend(prompt_ids_list)
        
        return list(set(prompt_ids))  # 去重

    # 注意：这个方法已被 _prepare_messages_with_prompts 替代
    # 保留是为了向后兼容，但不再使用

    def _prepare_prompt_context(self, state: IState, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备提示词上下文"""
        context = {}
        
        # 添加状态数据
        if state:
            context.update(state.get_data("data", {}))
        
        # 添加配置变量
        prompt_variables = config.get("prompt_variables", {})
        context.update(prompt_variables)
        
        # 添加系统变量
        context.update({
            "node_id": "llm_node",
            "timestamp": str(state.get_data("timestamp", "")),
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
            "using_prompt_system": (
                self._prompt_service.get_service_info()["configured"]
                if self._prompt_service and hasattr(self._prompt_service, 'get_service_info')
                else False
            ),
            "system_prompt_id": config.get("system_prompt_id"),
            "user_prompt_id": config.get("user_prompt_id"),
            "prompt_variables": config.get("prompt_variables", {})
        }
        
        return prompt_info

    def _prepare_parameters(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """准备生成参数"""
        # 使用配置合并获取默认值
        merged_config = self.merge_configs(config)
        
        return {
            "temperature": merged_config.get("temperature", 0.7),
            "max_tokens": merged_config.get("max_tokens", 1000),
            "top_p": merged_config.get("top_p", 0.9),
            "frequency_penalty": merged_config.get("frequency_penalty", 0.0),
            "presence_penalty": merged_config.get("presence_penalty", 0.0)
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
        try:
            from ...config.schema_generator import generate_node_schema
            return generate_node_schema("llm_node")
        except Exception as e:
            logger.warning(f"无法从配置文件生成Schema，使用默认Schema: {e}")
            return self._get_fallback_schema()
    
    def _get_fallback_schema(self) -> Dict[str, Any]:
        """获取备用Schema（当配置文件不可用时）"""
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

    def configure_prompt_system(self, prompt_registry, prompt_injector) -> None:
        """配置提示词系统"""
        if self._prompt_service and hasattr(self._prompt_service, 'configure'):
            self._prompt_service.configure(prompt_registry, prompt_injector)
            logger.info("LLM节点已配置提示词系统")
        else:
            logger.warning("提示词服务未注入，配置失败")
    
    def set_llm_client(self, llm_client: ILLMClient) -> None:
        """设置LLM客户端"""
        self._llm_client = llm_client
    
    async def validate_prompt_configuration(self, config: Dict[str, Any]) -> List[str]:
        """验证提示词配置"""
        if self._prompt_service and hasattr(self._prompt_service, 'validate_prompt_configuration'):
            return await self._prompt_service.validate_prompt_configuration(config)
        return []
    
    async def process_content(self, content: str, context: Optional[Dict[str, Any]] = None) -> str:
        """处理内容（通用方法）"""
        context = context or {}
        if self._prompt_service and hasattr(self._prompt_service, 'process_prompt_content'):
            return await self._prompt_service.process_prompt_content(content, context)
        return content
    
    async def invalidate_prompt_cache(self, prompt_ref: Optional[str] = None, cache_scope: str = "all") -> None:
        """失效提示词缓存
        
        Args:
            prompt_ref: 提示词引用，如果为None则清理所有缓存
            cache_scope: 缓存范围
        """
        try:
            if self._prompt_service and hasattr(self._prompt_service, 'invalidate_prompt_cache'):
                await self._prompt_service.invalidate_prompt_cache(prompt_ref, cache_scope)
                logger.info(f"LLM节点提示词缓存已清理: {prompt_ref}, 范围: {cache_scope}")
        except Exception as e:
            logger.warning(f"清理LLM节点提示词缓存失败: {e}")
    
    async def preload_prompts(self, prompt_refs: List[str], cache_scope: str = "session") -> None:
        """预加载提示词到缓存
        
        Args:
            prompt_refs: 提示词引用列表
            cache_scope: 缓存范围
        """
        try:
            if self._prompt_service and hasattr(self._prompt_service, 'preload_prompts'):
                await self._prompt_service.preload_prompts(prompt_refs, cache_scope)
                logger.info(f"LLM节点预加载提示词完成: {len(prompt_refs)} 个")
        except Exception as e:
            logger.warning(f"LLM节点预加载提示词失败: {e}")
    
    def get_prompt_cache_statistics(self) -> Dict[str, Any]:
        """获取提示词缓存统计信息"""
        try:
            if self._prompt_service and hasattr(self._prompt_service, 'get_service_info'):
                service_info = self._prompt_service.get_service_info()
                return service_info.get("cache_statistics", {})
        except Exception as e:
            logger.warning(f"获取提示词缓存统计信息失败: {e}")
        return {}