"""降级客户端包装器"""

from typing import Dict, Any, Optional, List, AsyncGenerator
import logging

from .interfaces import ILLMClient
from .models import LLMResponse
from .fallback import FallbackManager, FallbackModel, FallbackStrategy
from .factory import get_global_factory
from .exceptions import LLMFallbackError

logger = logging.getLogger(__name__)


class FallbackClientWrapper(ILLMClient):
    """降级客户端包装器"""
    
    def __init__(self, primary_client: ILLMClient, fallback_models: List[str]) -> None:
        """
        初始化降级客户端包装器
        
        Args:
            primary_client: 主客户端
            fallback_models: 降级模型列表
        """
        self.primary_client = primary_client
        self.fallback_models = fallback_models
        
        # 创建降级模型配置
        fallback_model_configs = []
        for model_name in fallback_models:
            fallback_model_configs.append(
                FallbackModel(
                    name=model_name,
                    priority=len(fallback_model_configs),  # 按列表顺序设置优先级
                    enabled=True
                )
            )
        
        # 创建降级管理器
        self.fallback_manager = FallbackManager(
            fallback_models=fallback_model_configs,
            strategy=FallbackStrategy.SEQUENTIAL,
            max_attempts=len(fallback_models) + 1  # 主模型 + 所有降级模型
        )
    
    def generate(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        生成文本响应（带降级支持）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        try:
            # 首先尝试主客户端
            return self.primary_client.generate(messages, parameters, **kwargs)
        except Exception as primary_error:
            logger.warning(f"主客户端调用失败: {primary_error}")
            
            # 尝试降级
            try:
                return self._try_fallback(messages, parameters, primary_error, **kwargs)
            except Exception as fallback_error:
                logger.error(f"所有降级尝试都失败: {fallback_error}")
                raise LLMFallbackError("所有模型调用都失败", fallback_error)
    
    async def generate_async(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """
        异步生成文本响应（带降级支持）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 生成的响应
        """
        try:
            # 首先尝试主客户端
            return await self.primary_client.generate_async(messages, parameters, **kwargs)
        except Exception as primary_error:
            logger.warning(f"主客户端异步调用失败: {primary_error}")
            
            # 尝试降级
            try:
                return await self._try_fallback_async(messages, parameters, primary_error, **kwargs)
            except Exception as fallback_error:
                logger.error(f"所有异步降级尝试都失败: {fallback_error}")
                raise LLMFallbackError("所有模型异步调用都失败", fallback_error)
    
    def stream_generate(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        流式生成文本响应（带降级支持）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        try:
            # 首先尝试主客户端
            for chunk in self.primary_client.stream_generate(messages, parameters, **kwargs):
                yield chunk
        except Exception as primary_error:
            logger.warning(f"主客户端流式调用失败: {primary_error}")
            
            # 流式降级比较复杂，这里简化为非流式降级
            try:
                response = self._try_fallback(messages, parameters, primary_error, **kwargs)
                # 将完整响应作为单个块返回
                yield response.content
            except Exception as fallback_error:
                logger.error(f"流式降级失败: {fallback_error}")
                raise LLMFallbackError("流式降级失败", fallback_error)
    
    async def stream_generate_async(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        异步流式生成文本响应（带降级支持）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            **kwargs: 其他参数
            
        Yields:
            str: 生成的文本片段
        """
        try:
            # 首先尝试主客户端
            async for chunk in self.primary_client.stream_generate_async(messages, parameters, **kwargs):
                yield chunk
        except Exception as primary_error:
            logger.warning(f"主客户端异步流式调用失败: {primary_error}")
            
            # 异步流式降级比较复杂，这里简化为非流式降级
            try:
                response = await self._try_fallback_async(messages, parameters, primary_error, **kwargs)
                # 将完整响应作为单个块返回
                yield response.content
            except Exception as fallback_error:
                logger.error(f"异步流式降级失败: {fallback_error}")
                raise LLMFallbackError("异步流式降级失败", fallback_error)
    
    def get_token_count(self, text: str) -> int:
        """
        计算文本的token数量
        
        Args:
            text: 输入文本
            
        Returns:
            int: token数量
        """
        return self.primary_client.get_token_count(text)
    
    def get_messages_token_count(self, messages: List[Any]) -> int:
        """
        计算消息列表的token数量
        
        Args:
            messages: 消息列表
            
        Returns:
            int: token数量
        """
        return self.primary_client.get_messages_token_count(messages)
    
    def supports_function_calling(self) -> bool:
        """
        检查是否支持函数调用
        
        Returns:
            bool: 是否支持函数调用
        """
        return self.primary_client.supports_function_calling()
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        获取模型信息
        
        Returns:
            Dict[str, Any]: 模型信息
        """
        info = self.primary_client.get_model_info()
        info['fallback_models'] = self.fallback_models
        info['fallback_enabled'] = True
        return info
    
    def _try_fallback(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs
    ) -> LLMResponse:
        """
        尝试降级调用
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_error: 主客户端错误
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 降级响应
        """
        factory = get_global_factory()
        
        # 尝试每个降级模型
        for model_name in self.fallback_models:
            try:
                logger.info(f"尝试降级到模型: {model_name}")
                
                # 获取降级客户端
                fallback_client = factory.get_cached_client(model_name)
                if fallback_client is None:
                    # 创建降级客户端配置
                    fallback_config = self._create_fallback_config(model_name)
                    fallback_client = factory.create_client(fallback_config)
                    factory.cache_client(model_name, fallback_client)
                
                # 调用降级客户端
                response = fallback_client.generate(messages, parameters, **kwargs)
                
                # 标记为降级响应
                response.metadata = response.metadata or {}
                response.metadata['fallback_model'] = model_name
                response.metadata['fallback_reason'] = str(primary_error)
                
                logger.info(f"降级成功: {model_name}")
                return response
                
            except Exception as fallback_error:
                logger.warning(f"降级到模型 {model_name} 失败: {fallback_error}")
                continue
        
        # 所有降级都失败
        raise LLMFallbackError("所有降级模型都失败", primary_error)
    
    async def _try_fallback_async(
        self,
        messages: List[Any],
        parameters: Optional[Dict[str, Any]],
        primary_error: Exception,
        **kwargs
    ) -> LLMResponse:
        """
        尝试异步降级调用
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_error: 主客户端错误
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: 降级响应
        """
        factory = get_global_factory()
        
        # 尝试每个降级模型
        for model_name in self.fallback_models:
            try:
                logger.info(f"尝试异步降级到模型: {model_name}")
                
                # 获取降级客户端
                fallback_client = factory.get_cached_client(model_name)
                if fallback_client is None:
                    # 创建降级客户端配置
                    fallback_config = self._create_fallback_config(model_name)
                    fallback_client = factory.create_client(fallback_config)
                    factory.cache_client(model_name, fallback_client)
                
                # 调用降级客户端
                response = await fallback_client.generate_async(messages, parameters, **kwargs)
                
                # 标记为降级响应
                response.metadata = response.metadata or {}
                response.metadata['fallback_model'] = model_name
                response.metadata['fallback_reason'] = str(primary_error)
                
                logger.info(f"异步降级成功: {model_name}")
                return response
                
            except Exception as fallback_error:
                logger.warning(f"异步降级到模型 {model_name} 失败: {fallback_error}")
                continue
        
        # 所有降级都失败
        raise LLMFallbackError("所有异步降级模型都失败", primary_error)
    
    def _create_fallback_config(self, model_name: str) -> Dict[str, Any]:
        """
        创建降级模型配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            Dict[str, Any]: 降级配置
        """
        # 根据模型名称推断模型类型
        if "gpt" in model_name.lower() or "openai" in model_name.lower():
            model_type = "openai"
        elif "gemini" in model_name.lower():
            model_type = "gemini"
        elif "claude" in model_name.lower() or "anthropic" in model_name.lower():
            model_type = "anthropic"
        else:
            model_type = "mock"  # 默认使用mock
        
        return {
            "model_type": model_type,
            "model_name": model_name
        }
    
    def get_fallback_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        return self.fallback_manager.get_stats()
    
    def reset_fallback_stats(self) -> None:
        """重置降级统计信息"""
        self.fallback_manager.reset_stats()