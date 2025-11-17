"""降级管理器服务实现

Services层负责业务编排，包括：
- 调用Core层的降级策略
- 管理执行流程和错误处理
- 记录监控指标
- 日志和统计
"""

from typing import Any, Optional, Dict, List
from langchain_core.messages import BaseMessage

from src.core.llm.interfaces import IFallbackManager, ITaskGroupManager, IPollingPoolManager, IClientFactory
from src.core.llm.wrappers.fallback_manager import (
    GroupBasedFallbackStrategy,
    PollingPoolFallbackStrategy,
    DefaultFallbackLogger,
)
from src.core.llm.exceptions import LLMCallError


class FallbackManager(IFallbackManager):
    """降级管理器服务实现
    
    负责：
    1. 调用Core层的降级策略获取降级目标
    2. 执行具体的LLM调用
    3. 管理统计和监控
    4. 错误处理和日志记录
    """
    
    def __init__(self, 
                 task_group_manager: ITaskGroupManager,
                 polling_pool_manager: IPollingPoolManager,
                 client_factory: IClientFactory,
                 logger: Optional[Any] = None):
        """
        初始化降级管理器
        
        Args:
            task_group_manager: 任务组管理器接口
            polling_pool_manager: 轮询池管理器接口
            client_factory: 客户端工厂接口
            logger: 日志记录器
        """
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.client_factory = client_factory
        self.logger = logger or DefaultFallbackLogger()
        
        # 使用Core层的策略类
        self._group_strategy = GroupBasedFallbackStrategy(task_group_manager)
        self._pool_strategy = PollingPoolFallbackStrategy(polling_pool_manager)
        
        # 统计信息
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }
    
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        执行带降级的请求
        
        Services层的核心编排逻辑：
        1. 判断是任务组还是轮询池
        2. 调用相应的执行方法
        3. 处理错误并进行降级重试
        
        Args:
            primary_target: 主要目标
            fallback_groups: 降级组列表
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        self._stats["total_requests"] += 1
        
        try:
            # 判断是任务组还是轮询池
            if self._is_polling_pool_target(primary_target):
                return await self._execute_with_pool_fallback(primary_target, prompt, parameters, **kwargs)
            else:
                return await self._execute_with_group_fallback(primary_target, prompt, parameters, **kwargs)
                
        except Exception as e:
            self._stats["failed_requests"] += 1
            self.logger.log_fallback_failure(primary_target, e, 1)
            raise LLMCallError(f"降级执行失败: {e}")
    
    async def _execute_with_group_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用任务组降级策略执行
        
        编排流程：
        1. 获取目标模型
        2. 创建客户端执行调用
        3. 如果失败，使用Core层的策略获取降级目标
        4. 重复直到成功或达到尝试次数限制
        
        Args:
            primary_target: 主要目标
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        current_target = primary_target
        attempt = 0
        last_error = None
        
        while attempt < 5:  # 最大尝试5次
            try:
                # 获取目标模型列表
                models = self.task_group_manager.get_models_for_group(current_target)
                if not models:
                    raise ValueError(f"没有找到模型: {current_target}")
                
                # 选择第一个模型
                model_name = models[0]
                
                # 创建客户端并执行
                client = self.client_factory.create_client(model_name)
                messages = [BaseMessage(content=prompt)]
                response = await client.generate_async(messages, parameters or {}, **kwargs)
                
                # 记录成功 - 使用Core层的策略记录
                self._group_strategy.record_success(current_target)
                self._stats["successful_requests"] += 1
                
                if attempt > 0:
                    self._stats["group_fallbacks"] += 1
                    self.logger.log_fallback_success(primary_target, current_target, response, attempt + 1)
                
                return response
                
            except Exception as e:
                last_error = e
                # 记录失败 - 使用Core层的策略记录
                self._group_strategy.record_failure(current_target, e)
                
                # 获取降级目标 - 使用Core层的策略获取
                fallback_targets = self._group_strategy.get_fallback_targets(current_target, e)
                
                if not fallback_targets or attempt >= 4:
                    break
                
                # 选择下一个降级目标
                current_target = fallback_targets[0]
                attempt += 1
                
                # 记录降级尝试 - Services层负责日志记录
                self.logger.log_fallback_attempt(primary_target, current_target, e, attempt + 1)
        
        # 所有尝试都失败
        raise last_error or LLMCallError("任务组降级失败")
    
    async def _execute_with_pool_fallback(
        self,
        primary_target: str,
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        使用轮询池降级策略执行
        
        编排流程：
        1. 获取轮询池
        2. 使用轮询池执行调用
        3. 轮询池内部处理实例轮换和降级
        
        Args:
            primary_target: 主要目标（轮询池名称）
            prompt: 提示词
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            执行结果
        """
        pool = self.polling_pool_manager.get_pool(primary_target)
        if not pool:
            raise ValueError(f"轮询池不存在: {primary_target}")
        
        try:
            # 轮询池内部处理实例轮换和降级
            result = await pool.call_llm(prompt, **kwargs)
            
            self._stats["successful_requests"] += 1
            self._stats["pool_fallbacks"] += 1
            
            return result
            
        except Exception as e:
            raise LLMCallError(f"轮询池执行失败: {e}")
    
    def _is_polling_pool_target(self, target: str) -> bool:
        """
        判断目标是否是轮询池
        
        Args:
            target: 目标名称
            
        Returns:
            是否是轮询池
        """
        # 检查是否是已知的轮询池
        pools = self.polling_pool_manager.list_all_status()
        return target in pools
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            统计信息字典
        """
        return self._stats.copy()
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "group_fallbacks": 0,
            "pool_fallbacks": 0
        }