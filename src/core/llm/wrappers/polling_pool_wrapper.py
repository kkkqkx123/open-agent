"""轮询池LLM包装器"""

import asyncio
from src.infrastructure.llm.models import TokenUsage
from src.interfaces.dependency_injection import get_logger
import time
from typing import Dict, Any, Optional, List, Sequence
from datetime import datetime

from .base_wrapper import BaseLLMWrapper
from src.interfaces.llm.exceptions import PollingPoolWrapperError, WrapperExecutionError
from src.interfaces.llm import IPollingPoolManager, LLMResponse

logger = get_logger(__name__)


class PollingPoolWrapper(BaseLLMWrapper):
    """轮询池LLM包装器"""
    
    def __init__(self,
                 name: str,
                 polling_pool_manager: IPollingPoolManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化轮询池包装器
        
        Args:
            name: 包装器名称
            polling_pool_manager: 轮询池管理器接口
            config: 包装器配置
        """
        super().__init__(name, config or {})
        self.polling_pool_manager = polling_pool_manager
        self._pool = None
        self._attempt_count = 0
        self._rotation_history: List[Dict[str, Any]] = []
        self._client_cache: Dict[str, Any] = {}  # 缓存LLM客户端实例
        
        # 更新元数据
        self._metadata.update({
            "polling_pool_manager": polling_pool_manager is not None,
            "wrapper_type": "polling_pool"
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
            # 获取轮询池
            pool = self._get_pool()
            if not pool:
                raise PollingPoolWrapperError(f"轮询池不可用: {self.name}")
            
            # 使用轮询池调用
            prompt = self._messages_to_prompt(messages)
            
            # 使用简单降级策略
            result = await self._call_with_simple_fallback(pool, prompt, parameters, **kwargs)
            
            success = True
            model_name = getattr(pool, 'name', 'polling_pool')
            return self._create_llm_response(
                content=str(result),
                model=f"{model_name}_pool"
            )
            
        except Exception as e:
            logger.error(f"轮询池包装器生成失败: {e}")
            raise PollingPoolWrapperError(f"轮询池包装器生成失败: {e}")
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
            logger.error(f"轮询池包装器同步生成失败: {e}")
            raise PollingPoolWrapperError(f"轮询池包装器同步生成失败: {e}")
    
    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        pool = self._get_pool()
        pool_info = {}
        if pool:
            pool_info = {
                "name": pool.name,
                "task_groups": pool.config.get("task_groups", []),
                "rotation_strategy": pool.config.get("rotation_strategy", "round_robin"),
                "instance_count": len(pool.instances),
                "healthy_instances": len([i for i in pool.instances if i.status.value == "healthy"]),
                "health_check_interval": pool.config.get("health_check_interval", 30),
                "failure_threshold": pool.config.get("failure_threshold", 3),
                "recovery_time": pool.config.get("recovery_time", 60)
            }
        
        return {
            "type": "polling_pool_wrapper",
            "name": self.name,
            "pool_info": pool_info,
            "attempt_count": self._attempt_count,
            "rotation_history": self._rotation_history
        }
    
    def _get_pool(self) -> Any:
        """获取轮询池实例"""
        if self._pool is None:
            self._pool = self.polling_pool_manager.get_pool(self.name)
        return self._pool
    
    async def _call_with_simple_fallback(
        self,
        pool: Any,
        prompt: str,
        parameters: Optional[Dict[str, Any]],
        **kwargs: Any
    ) -> Any:
        """使用简单降级策略调用"""
        max_attempts = self.config.get("max_instance_attempts", 2)
        instance = None
        last_error = None
        
        for attempt in range(max_attempts):
            try:
                # 从轮询池获取实例
                instance = await pool.get_instance()
                if not instance:
                    continue
                
                # 记录旋转历史
                self._rotation_history.append({
                    "instance_id": instance.instance_id,
                    "attempt": attempt + 1,
                    "timestamp": datetime.now().isoformat()
                })
                
                # 调用实例
                response = await self._call_instance(instance, prompt, parameters, **kwargs)
                
                # 更新统计
                try:
                    instance.success_count += 1
                except (TypeError, AttributeError):
                    pass  # 忽略无法更新计数的情况
                self._attempt_count += 1
                
                # 释放实例
                pool.release_instance(instance)
                
                return response
                
            except Exception as e:
                last_error = e
                if instance is not None:
                    logger.warning(f"实例调用失败: {instance.instance_id}, 错误: {e}")
                    try:
                        instance.failure_count += 1
                    except (TypeError, AttributeError):
                        pass  # 忽略无法更新计数的情况
                else:
                    logger.warning(f"实例调用失败: {e}")
                
                self._attempt_count += 1
                
                # 释放实例
                if instance is not None:
                    pool.release_instance(instance)
                
                continue
        
        raise PollingPoolWrapperError(f"轮询池所有实例尝试失败，尝试次数: {max_attempts}。最后错误: {last_error}")
    
    async def _call_instance(
        self,
        instance: Any,
        prompt: str,
        parameters: Optional[Dict[str, Any]],
        **kwargs: Any
    ) -> Any:
        """调用具体实例"""
        try:
            # 获取或创建实例的LLM客户端
            client = await self._get_or_create_client_for_instance(instance)
            
            if client is None:
                raise PollingPoolWrapperError(f"无法为实例 {instance.instance_id} 创建LLM客户端")
            
            # 将prompt转换为消息格式
            messages = self._prompt_to_messages(prompt)
            
            # 调用LLM客户端
            response = await client.generate(messages, parameters, **kwargs)
            
            return response
            
        except Exception as e:
            logger.error(f"调用实例 {instance.instance_id} 失败: {e}")
            raise e
    
    async def _get_or_create_client_for_instance(self, instance: Any) -> Any:
        """获取或为实例创建LLM客户端"""
        instance_id = getattr(instance, 'instance_id', str(id(instance)))
        
        # 首先尝试从缓存获取
        if instance_id in self._client_cache:
            return self._client_cache[instance_id]
        
        # 尝试从实例获取已存在的客户端
        client = getattr(instance, 'client', None)
        if client is not None:
            self._client_cache[instance_id] = client
            return client
        
        # 创建新的客户端
        client = await self._create_client_for_instance(instance)
        if client is not None:
            self._client_cache[instance_id] = client
            # 同时缓存到实例
            instance.client = client
        
        return client
    
    async def _create_client_for_instance(self, instance: Any) -> Any:
        """为实例创建LLM客户端"""
        try:
            # 获取实例配置
            instance_config = getattr(instance, 'config', {})
            if not instance_config:
                logger.warning(f"实例 {instance.instance_id} 没有配置信息")
                return None
            
            # 导入LLM工厂
            from ..factory import get_global_factory
            
            # 创建客户端配置
            client_config = {
                "model_type": instance_config.get("model_type", "openai"),
                "model_name": instance_config.get("model_name", "gpt-3.5-turbo"),
                "api_key": instance_config.get("api_key"),
                "base_url": instance_config.get("base_url"),
                "temperature": instance_config.get("temperature", 0.7),
                "max_tokens": instance_config.get("max_tokens"),
                "timeout": instance_config.get("timeout", 30),
                "max_retries": instance_config.get("max_retries", 3)
            }
            
            # 使用工厂创建客户端
            factory = get_global_factory()
            client = factory.create_client(client_config)
            
            return client
            
        except Exception as e:
            logger.error(f"为实例 {instance.instance_id} 创建客户端失败: {e}")
            return None
    
    def _prompt_to_messages(self, prompt: str) -> Sequence:
        """将提示词转换为消息格式"""
        try:
            from src.infrastructure.messages.types import HumanMessage
            return [HumanMessage(content=prompt)]
        except ImportError:
            # 如果无法导入消息类型，返回简单格式
            return [{"role": "user", "content": prompt}]
    
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
        
        # 合并元数据
        response_metadata = metadata or {}
        response_metadata.update({
            "wrapper": "polling_pool",
            "attempt_count": self._attempt_count,
            "rotation_history_count": len(self._rotation_history)
        })
        
        return super()._create_llm_response(
            content=content,
            model=model,
            token_usage=token_usage,
            message=message,
            metadata=response_metadata
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
            
            # 使用默认模型类型进行计算
            model_type = "openai"  # 默认使用openai类型
            model_name = "gpt-3.5-turbo"  # 默认模型
            
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
    
    def get_rotation_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取旋转历史"""
        return self._rotation_history[-limit:]
    
    def reset_rotation_history(self) -> None:
        """重置旋转历史"""
        self._rotation_history = []
        self._attempt_count = 0
    
    def get_pool_status(self) -> Optional[Dict[str, Any]]:
        """获取轮询池状态"""
        pool = self._get_pool()
        if pool:
            return pool.get_status()  # type: ignore
        return None
    
    def supports_function_calling(self) -> bool:
        """检查是否支持函数调用"""
        # 轮询池通常不支持函数调用，因为它主要用于简单的单轮对话
        return False
    
    async def health_check(self) -> Dict[str, Any]:
        """执行健康检查"""
        pool = self._get_pool()
        if not pool:
            return {
                "healthy": False,
                "error": "轮询池不可用"
            }
        
        try:
            # 检查池中健康实例数量
            try:
                instances = pool.instances
            except Exception as e:
                # 如果访问pool.instances时发生异常
                return {
                    "healthy": False,
                    "error": str(e)
                }
            
            # 检查是否是可迭代对象
            if hasattr(instances, '__iter__') and not isinstance(instances, (str, bytes)):
                # 正常处理可迭代对象
                instances_list = list(instances)
                healthy_instances = len([i for i in instances_list if hasattr(i, 'status') and hasattr(i.status, 'value') and i.status.value == "healthy"])
                total_instances = len(instances_list)
            else:
                # 如果instances不可迭代，可能是异常或错误
                return {
                    "healthy": False,
                    "error": f"'{type(instances)}' object is not iterable"
                }
            
            # 如果健康实例少于总数的50%，认为不健康
            # 需要超过一半才算健康
            is_healthy = healthy_instances > total_instances / 2
            
            return {
                "healthy": is_healthy,
                "healthy_instances": healthy_instances,
                "total_instances": total_instances,
                "health_ratio": healthy_instances / total_instances if total_instances > 0 else 0
            }
        except Exception as e:
            return {
                "healthy": False,
                "error": str(e)
            }