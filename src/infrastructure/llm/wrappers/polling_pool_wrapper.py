"""轮询池LLM包装器"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List, Sequence
from datetime import datetime

from .base_wrapper import BaseLLMWrapper
from .exceptions import PollingPoolWrapperError, WrapperExecutionError
from ..polling_pool import PollingPoolManager, LLMInstance
from ..interfaces import ILLMClient
from ..models import LLMResponse, TokenUsage
from ..exceptions import LLMError

logger = logging.getLogger(__name__)


class PollingPoolWrapper(BaseLLMWrapper):
    """轮询池LLM包装器"""
    
    def __init__(self,
                 name: str,
                 polling_pool_manager: PollingPoolManager,
                 config: Optional[Dict[str, Any]] = None):
        """
        初始化轮询池包装器
        
        Args:
            name: 包装器名称
            polling_pool_manager: 轮询池管理器
            config: 包装器配置
        """
        super().__init__(name, config or {})
        self.polling_pool_manager = polling_pool_manager
        self._pool = None
        self._attempt_count = 0
        self._rotation_history = []
        
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
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环已经在运行，创建新的任务
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        lambda: loop.run_until_complete(
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
        **kwargs
    ) -> Any:
        """使用简单降级策略调用"""
        max_attempts = self.config.get("max_instance_attempts", 2)
        instance = None
        
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
                # TODO: 这里需要实际的LLM客户端调用
                result = await self._call_instance(instance, prompt, parameters, **kwargs)
                
                # 更新统计
                instance.success_count += 1
                self._attempt_count += 1
                
                # 释放实例
                pool.release_instance(instance)
                
                return result
                
            except Exception as e:
                if instance is not None:
                    logger.warning(f"实例调用失败: {instance.instance_id}, 错误: {e}")
                    instance.failure_count += 1
                else:
                    logger.warning(f"实例调用失败: {e}")
                
                self._attempt_count += 1
                
                # 释放实例
                if instance is not None:
                    pool.release_instance(instance)
                
                continue
        
        raise PollingPoolWrapperError(f"轮询池所有实例尝试失败，尝试次数: {max_attempts}")
    
    async def _call_instance(
        self, 
        instance, 
        prompt: str, 
        parameters: Optional[Dict[str, Any]], 
        **kwargs
    ) -> Any:
        """调用具体实例"""
        # TODO: 实现实际的LLM调用逻辑
        # 这里应该根据instance.client调用实际的LLM
        await asyncio.sleep(0.1)  # 模拟调用延迟
        return f"轮询池响应 from {instance.instance_id}: {prompt[:50]}..."
    
    def _create_llm_response(
        self,
        content: str,
        model: str,
        token_usage: Optional[TokenUsage] = None,
        message: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """创建LLM响应"""
        # 估算token使用量
        if token_usage is None:
            prompt_tokens = self.get_token_count(content)
            completion_tokens = prompt_tokens // 2  # 简单估算
            token_usage = TokenUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens
            )
        
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
            return pool.get_status()
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
            healthy_instances = len([i for i in pool.instances if i.status.value == "healthy"])
            total_instances = len(pool.instances)
            
            # 如果健康实例少于总数的50%，认为不健康
            is_healthy = healthy_instances >= max(1, total_instances // 2)
            
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