"""任务组LLM包装器"""

import asyncio
from src.infrastructure.llm.models import TokenUsage
from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, Optional, List, Sequence
from datetime import datetime

from .base_wrapper import BaseLLMWrapper
from src.interfaces.llm.exceptions import TaskGroupWrapperError, WrapperExecutionError
from src.interfaces.llm import ITaskGroupManager, IFallbackManager, LLMResponse

logger = get_logger(__name__)


class TaskGroupWrapper(BaseLLMWrapper):
    """任务组LLM包装器"""
    
    def __init__(self,
                 name: str,
                 task_group_manager: ITaskGroupManager,
                 fallback_manager: Optional[IFallbackManager] = None,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化任务组包装器
        
        Args:
            name: 包装器名称
            task_group_manager: 任务组管理器接口
            fallback_manager: 降级管理器接口
            config: 包装器配置
        """
        super().__init__(name, config or {})
        self.task_group_manager = task_group_manager
        self.fallback_manager = fallback_manager
        self._current_target = None
        self._attempt_count = 0
        self._fallback_history: List[Dict[str, Any]] = []
        self._client_cache: Dict[str, Any] = {}  # 缓存LLM客户端实例
        
        # 更新元数据
        self._metadata.update({
            "task_group_manager": task_group_manager is not None,
            "fallback_manager": fallback_manager is not None,
            "wrapper_type": "task_group"
        })
    
    async def generate_async(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """异步生成"""
        start_time = time.time()
        success = False
        result = None
        
        try:
            # 获取目标配置
            target = self._get_target()
            
            # 使用降级管理器执行
            if self.fallback_manager:
                result = await self._generate_with_fallback(messages, parameters, **kwargs)
            else:
                result = await self._generate_direct(messages, parameters, **kwargs)
            
            success = True
            return result
            
        except Exception as e:
            logger.error(f"任务组包装器生成失败: {e}")
            raise TaskGroupWrapperError(f"任务组包装器生成失败: {e}")
        finally:
            # 更新统计信息
            response_time = time.time() - start_time
            self._update_stats(success, response_time)
    
    def generate(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """同步生成"""
        try:
            # 运行异步方法
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                # 如果没有事件循环，则创建一个新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            if loop.is_running():
                # 如果事件循环已经在运行，创建新的任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: asyncio.run(
                            self.generate_async(messages, parameters, **kwargs)
                        )
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self.generate_async(messages, parameters, **kwargs)
                )
        except Exception as e:
            logger.error(f"任务组包装器同步生成失败: {e}")
            raise TaskGroupWrapperError(f"任务组包装器同步生成失败: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        return {
            "type": "task_group_wrapper",
            "name": self.name,
            "current_target": self._current_target,
            "fallback_history": self._fallback_history,
            "task_group_manager": self.task_group_manager is not None,
            "fallback_manager": self.fallback_manager is not None,
            "attempt_count": self._attempt_count
        }
    
    def _get_target(self) -> str:
        """获取当前目标"""
        # 从配置获取目标，如果没有则使用包装器名称
        target = self.config.get("target", self.name)
        self._current_target = target
        return str(target)
    
    async def _generate_with_fallback(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]],
        **kwargs: Any
    ) -> LLMResponse:
        """使用降级机制生成"""
        target = self._get_target()
        
        # 获取降级配置
        fallback_groups = self._get_fallback_groups(target)
        
        try:
            # 使用降级管理器执行
            prompt = self._messages_to_prompt(messages)
            if self.fallback_manager is None:
                raise TaskGroupWrapperError("降级管理器未初始化")
            
            result = await self.fallback_manager.execute_with_fallback(
                primary_target=target,
                fallback_groups=fallback_groups,
                prompt=prompt,
                parameters=parameters,
                **kwargs
            )
            
            # 记录成功
            self._record_success(target)
            return self._create_llm_response(
                content=result,
                model=target
            )
            
        except Exception as e:
            # 记录失败
            self._record_failure(target, str(e))
            raise e
    
    async def _generate_direct(
        self,
        messages: Sequence,
        parameters: Optional[Dict[str, Any]],
        **kwargs: Any
    ) -> LLMResponse:
        """直接生成（无降级）"""
        target = self._get_target()
        
        try:
            # 获取模型列表
            models = self.task_group_manager.get_models_for_group(target)
            if not models:
                raise TaskGroupWrapperError(f"没有找到模型: {target}")
            
            # 选择第一个模型
            model_name = models[0]
            
            # 创建LLM客户端
            client = await self._create_client_for_model(model_name, target)
            if client is None:
                raise TaskGroupWrapperError(f"无法为模型 {model_name} 创建LLM客户端")
            
            # 调用LLM客户端
            response = await client.generate(messages, parameters, **kwargs)
            
            return response  # type: ignore
            
        except Exception as e:
            logger.error(f"直接生成失败: {e}")
            raise e
    
    async def _get_or_create_client_for_model(self, model_name: str, target: str) -> Any:
        """获取或为模型创建LLM客户端"""
        cache_key = f"{target}:{model_name}"
        
        # 首先尝试从缓存获取
        if cache_key in self._client_cache:
            return self._client_cache[cache_key]
        
        # 创建新的客户端
        client = await self._create_client_for_model(model_name, target)
        if client is not None:
            self._client_cache[cache_key] = client
        
        return client
    
    async def _create_client_for_model(self, model_name: str, target: str) -> Any:
        """为模型创建LLM客户端"""
        try:
            # 解析目标配置
            group_name, echelon_or_task = self.task_group_manager.parse_group_reference(target)
            if not group_name:
                logger.warning(f"无法解析目标: {target}")
                return None
            
            # 获取层级配置
            echelon_config = self.task_group_manager.get_echelon_config(group_name, echelon_or_task or "")
            if not echelon_config:
                logger.warning(f"无法获取层级配置: {group_name}/{echelon_or_task}")
                return None
            
            # 导入LLM工厂
            from ..factory import get_global_factory
            
            # 创建客户端配置
            client_config = {
                "model_type": echelon_config.get("model_type", "openai"),
                "model_name": model_name,
                "api_key": echelon_config.get("api_key"),
                "base_url": echelon_config.get("base_url"),
                "temperature": echelon_config.get("temperature", 0.7),
                "max_tokens": echelon_config.get("max_tokens"),
                "timeout": echelon_config.get("timeout", 30),
                "max_retries": echelon_config.get("max_retries", 3)
            }
            
            # 使用工厂创建客户端
            factory = get_global_factory()
            client = factory.create_client(client_config)
            
            return client
            
        except Exception as e:
            logger.error(f"为模型 {model_name} 创建客户端失败: {e}")
            return None
    
    def _get_fallback_groups(self, target: str) -> List[str]:
        """获取降级组列表"""
        # 从配置获取降级组
        config_fallback_groups = self.config.get("fallback_groups", [])
        if config_fallback_groups:
            return config_fallback_groups
        
        # 从任务组配置获取降级组
        try:
            result = self.task_group_manager.parse_group_reference(target)
            if result and len(result) >= 2:
                group_name, _ = result
                if group_name:
                    return self.task_group_manager.get_fallback_groups(target)
        except Exception:
            # 如果解析失败，返回空列表
            pass
        
        return []  # 已确保返回list[str]类型
    
    def _create_llm_response(
        self,
        content: str,
        model: str,
        token_usage: Optional[TokenUsage] = None,
        message: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """创建LLM响应"""
        # 如果没有提供token使用量，尝试从响应中提取或计算
        if token_usage is None:
            token_usage = self._extract_or_calculate_tokens(content, message)
        
        final_metadata = metadata or {}
        final_metadata.update({
            "wrapper": "task_group",
            "target": self._current_target,
            "attempt_count": self._attempt_count
        })
        
        return super()._create_llm_response(
            content=content,
            model=model,
            token_usage=token_usage,
            message=message,
            metadata=final_metadata
        )
    
    def _extract_or_calculate_tokens(self, content: str, message: Optional[Any] = None) -> TokenUsage:
        """从响应中提取token使用量或计算token"""
        # 尝试从消息中提取token使用量
        if message and hasattr(message, 'token_usage'):
            return message.token_usage
        
        # 尝试从响应元数据中提取token使用量
        if message and hasattr(message, 'metadata') and message.metadata:
            if 'token_usage' in message.metadata:
                return TokenUsage(**message.metadata['token_usage'])
            elif 'usage' in message.metadata:
                usage = message.metadata['usage']
                return TokenUsage(
                    prompt_tokens=usage.get('prompt_tokens', 0),
                    completion_tokens=usage.get('completion_tokens', 0),
                    total_tokens=usage.get('total_tokens', 0)
                )
        
        # 如果无法提取，使用更准确的计算方法
        return self._calculate_tokens_accurate(content)
    
    def _calculate_tokens_accurate(self, content: str) -> TokenUsage:
        """使用TokenCalculationService进行准确的token计算"""
        try:
            # 导入TokenCalculationService
            from src.services.llm.token_calculation_service import TokenCalculationService
            
            # 创建token计算服务实例
            token_service = TokenCalculationService()
            
            # 根据当前目标获取模型信息
            model_type = "openai"  # 默认使用openai类型
            model_name = "gpt-3.5-turbo"  # 默认模型
            
            if self._current_target:
                try:
                    # 尝试从目标配置中获取模型信息
                    group_name, echelon_or_task = self.task_group_manager.parse_group_reference(self._current_target)
                    if group_name:
                        echelon_config = self.task_group_manager.get_echelon_config(group_name, echelon_or_task or "")
                        if echelon_config:
                            model_type = echelon_config.get("model_type", "openai")
                            model_name = echelon_config.get("model_name", "gpt-3.5-turbo")
                except Exception:
                    # 如果获取配置失败，使用默认值
                    pass
            
            # 计算completion tokens
            completion_tokens = token_service.calculate_tokens(content, model_type, model_name)
            
            # 估算prompt tokens（假设输入和输出长度相似）
            prompt_tokens = max(completion_tokens, 10)
            
            return TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
            
        except Exception as e:
            logger.error(f"Token计算服务调用失败: {e}，使用简单估算")
            # 回退到最简单的估算
            content_tokens = max(1, len(content) // 4)
            prompt_tokens = max(content_tokens, 10)
            
            return TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=content_tokens,
                total_tokens=prompt_tokens + content_tokens
            )
    
    def _record_success(self, target: str) -> None:
        """记录成功"""
        self._attempt_count += 1
        self._fallback_history.append({
            "target": target,
            "success": True,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录数量
        if len(self._fallback_history) > 100:
            self._fallback_history = self._fallback_history[-100:]
    
    def _record_failure(self, target: str, error: str) -> None:
        """记录失败"""
        self._attempt_count += 1
        self._fallback_history.append({
            "target": target,
            "success": False,
            "error": error,
            "timestamp": datetime.now().isoformat()
        })
        
        # 限制历史记录数量
        if len(self._fallback_history) > 100:
            self._fallback_history = self._fallback_history[-100:]
    
    def get_fallback_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取降级历史"""
        return self._fallback_history[-limit:]
    
    def reset_fallback_history(self) -> None:
        """重置降级历史"""
        self._fallback_history = []
        self._attempt_count = 0
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 检查当前目标是否支持函数调用
        if not self._current_target:
            return False
        
        try:
            group_name, echelon_or_task = self.task_group_manager.parse_group_reference(self._current_target)
            if not group_name or not echelon_or_task:
                return False
            
            echelon_config = self.task_group_manager.get_echelon_config(group_name, echelon_or_task)
            if echelon_config:
                return echelon_config.get("function_calling") is not None
        except Exception:
            pass
        
        return False