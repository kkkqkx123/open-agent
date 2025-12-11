"""LLM请求执行器

专注于LLM请求的执行和降级处理。
"""

from typing import Any, Dict, List, Optional, Sequence, AsyncGenerator
from src.interfaces.dependency_injection import get_logger
from src.infrastructure.messages.base import BaseMessage

from src.interfaces.llm import ILLMClient, IFallbackManager, ITaskGroupManager, LLMResponse
from src.interfaces.llm.exceptions import LLMError

logger = get_logger(__name__)


class LLMRequestExecutor:
    """LLM请求执行器
    
    专注于：
    1. 执行LLM请求
    2. 处理降级逻辑
    3. 流式请求处理
    4. 任务类型到客户端的映射
    """
    
    def __init__(
        self,
        fallback_manager: IFallbackManager,
        task_group_manager: ITaskGroupManager
    ) -> None:
        """初始化请求执行器
        
        Args:
            fallback_manager: 降级管理器
            task_group_manager: 任务组管理器
        """
        self._fallback_manager = fallback_manager
        self._task_group_manager = task_group_manager
    
    async def execute_with_fallback(
        self,
        client: ILLMClient,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """使用降级机制执行LLM请求
        
        Args:
            client: LLM客户端实例
            messages: 消息列表
            task_type: 任务类型
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM响应
            
        Raises:
            LLMError: 执行失败
        """
        try:
            # 直接使用客户端执行请求
            return await client.generate_async(messages, parameters, **kwargs)
            
        except Exception as e:
            logger.error(f"执行LLM请求失败: {e}")
            
            # 如果有任务类型，尝试使用降级管理器
            if task_type:
                try:
                    # 构建降级目标
                    fallback_targets = self._build_fallback_targets(task_type)
                    if fallback_targets:
                        # 使用降级管理器执行
                        return await self._execute_with_fallback_targets(
                            messages, task_type, fallback_targets, parameters, **kwargs
                        )
                except Exception as fallback_error:
                    logger.error(f"降级执行也失败: {fallback_error}")
            
            raise LLMError(f"执行LLM请求失败: {e}") from e
    
    async def stream_with_fallback(
        self,
        client: ILLMClient,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """使用降级机制执行流式LLM请求
        
        Args:
            client: LLM客户端实例
            messages: 消息列表
            task_type: 任务类型
            parameters: 参数
            **kwargs: 其他参数
            
        Yields:
            str: LLM响应片段
            
        Raises:
            LLMError: 执行失败
        """
        try:
            # 直接使用客户端执行流式请求
            async for chunk in client.stream_generate_async(messages, parameters, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"执行流式LLM请求失败: {e}")
            
            # 流式请求的降级处理比较复杂，这里简化处理
            # 在实际应用中，可能需要更复杂的降级策略
            raise LLMError(f"执行流式LLM请求失败: {e}") from e
    
    def get_client_for_task(
        self,
        task_type: str,
        available_clients: Dict[str, ILLMClient],
        preferred_client: Optional[str] = None
    ) -> ILLMClient:
        """根据任务类型获取最适合的LLM客户端
        
        Args:
            task_type: 任务类型
            available_clients: 可用的客户端映射
            preferred_client: 首选客户端名称
            
        Returns:
            ILLMClient: 适合的LLM客户端实例
            
        Raises:
            LLMError: 没有可用的客户端
        """
        try:
            # 首选客户端逻辑
            if preferred_client and preferred_client in available_clients:
                return available_clients[preferred_client]
            
            # 使用任务组管理器获取适合的模型
            if task_type:
                try:
                    models = self._task_group_manager.get_models_for_group(task_type)
                    if models:
                        # 从任务组中获取第一个可用的客户端
                        for model_name in models:
                            if model_name in available_clients:
                                return available_clients[model_name]
                except Exception as e:
                    logger.warning(f"从任务组获取模型失败: {e}")
            
            # 返回第一个可用的客户端
            if available_clients:
                return next(iter(available_clients.values()))
            
            raise LLMError("没有可用的LLM客户端")
            
        except Exception as e:
            logger.error(f"获取任务 {task_type} 的LLM客户端失败: {e}")
            raise LLMError(f"获取任务 {task_type} 的LLM客户端失败: {e}") from e
    
    def _build_fallback_targets(self, task_type: str) -> List[str]:
        """构建降级目标列表
        
        Args:
            task_type: 任务类型
            
        Returns:
            List[str]: 降级目标列表
        """
        targets = []
        
        # 添加任务组相关的降级目标
        if task_type:
            try:
                task_groups = self._task_group_manager.get_fallback_groups(task_type)
                targets.extend(task_groups)
            except Exception as e:
                logger.warning(f"获取任务组降级目标失败: {e}")
        
        return targets
    
    async def _execute_with_fallback_targets(
        self,
        messages: Sequence[BaseMessage],
        task_type: str,
        fallback_targets: List[str],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """使用降级目标执行请求
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            fallback_targets: 降级目标列表
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM响应
            
        Raises:
            LLMError: 所有降级目标都失败
        """
        # 将消息转换为提示字符串（简化处理）
        prompt_parts = []
        for msg in messages:
            if hasattr(msg, 'content'):
                content = msg.content
                if isinstance(content, str):
                    prompt_parts.append(content)
                elif isinstance(content, list):
                    # 处理内容列表，只提取字符串部分
                    for item in content:
                        if isinstance(item, str):
                            prompt_parts.append(item)
                else:
                    prompt_parts.append(str(content))
        prompt = " ".join(prompt_parts)
        
        # 使用降级管理器执行
        try:
            return await self._fallback_manager.execute_with_fallback(
                primary_target=fallback_targets[0] if fallback_targets else task_type,
                fallback_groups=fallback_targets[1:] if len(fallback_targets) > 1 else [],
                prompt=prompt,
                parameters=parameters,
                **kwargs
            )
        except Exception as e:
            raise LLMError(f"降级执行失败: {e}") from e