"""降级编排器

负责 Services 层的业务编排逻辑，包括任务组降级和轮询池降级。
"""

from typing import Any, Optional, Dict, List
from langchain_core.messages import BaseMessage

from .interfaces import IFallbackLogger, IClientFactory
from .fallback_config import FallbackConfig, FallbackAttempt, FallbackSession

# 修复导入路径
from src.core.llm.models import LLMResponse
from src.core.llm.exceptions import LLMCallError

# Services 层的导入
from src.core.llm.interfaces import ITaskGroupManager, IPollingPoolManager
from src.core.llm.wrappers.fallback_manager import (
    GroupBasedFallbackStrategy,
    PollingPoolFallbackStrategy,
)


class FallbackOrchestrator:
    """降级编排器
    
    负责 Services 层的业务编排逻辑，包括：
    1. 任务组降级策略执行
    2. 轮询池降级策略执行
    3. 降级目标判断和选择
    4. 业务流程编排
    """
    
    def __init__(self, 
                 client_factory: Optional[IClientFactory] = None,
                 logger: Optional[IFallbackLogger] = None,
                 task_group_manager: Optional[ITaskGroupManager] = None,
                 polling_pool_manager: Optional[IPollingPoolManager] = None):
        """
        初始化降级编排器
        
        Args:
            client_factory: 客户端工厂
            logger: 日志记录器
            task_group_manager: 任务组管理器
            polling_pool_manager: 轮询池管理器
        """
        self.client_factory = client_factory
        self.logger = logger
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        
        # Services 层策略
        self._group_strategy = None
        self._pool_strategy = None
        
        # 延迟初始化策略，避免循环依赖
        self._strategies_initialized = False
    
    def _initialize_strategies(self):
        """延迟初始化策略，避免循环依赖"""
        if self._strategies_initialized:
            return
            
        # Services 层策略初始化
        if self.task_group_manager:
            self._group_strategy = GroupBasedFallbackStrategy(self.task_group_manager)
        if self.polling_pool_manager:
            self._pool_strategy = PollingPoolFallbackStrategy(self.polling_pool_manager)
            
        self._strategies_initialized = True
    
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
        self._initialize_strategies()
        
        try:
            # 判断是任务组还是轮询池
            if self._is_polling_pool_target(primary_target):
                return await self._execute_with_pool_fallback(primary_target, prompt, parameters, **kwargs)
            else:
                return await self._execute_with_group_fallback(primary_target, prompt, parameters, **kwargs)
                
        except Exception as e:
            if self.logger:
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
                if not self.task_group_manager:
                    raise LLMCallError("任务组管理器未初始化")
                    
                models = self.task_group_manager.get_models_for_group(current_target)
                if not models:
                    raise ValueError(f"没有找到模型: {current_target}")
                
                # 选择第一个模型
                model_name = models[0]
                
                # 创建客户端并执行
                if not self.client_factory:
                    raise LLMCallError("客户端工厂未初始化")
                    
                client = self.client_factory.create_client(model_name)
                messages = [BaseMessage(content=prompt)]
                response = await client.generate_async(messages, parameters or {}, **kwargs)
                
                # 记录成功 - 使用Core层的策略记录
                if self._group_strategy:
                    self._group_strategy.record_success(current_target)
                
                if attempt > 0 and self.logger:
                    self.logger.log_fallback_success(primary_target, current_target, response, attempt + 1)
                
                return response
                
            except Exception as e:
                last_error = e
                # 记录失败 - 使用Core层的策略记录
                if self._group_strategy:
                    self._group_strategy.record_failure(current_target, e)
                
                # 获取降级目标 - 使用Core层的策略获取
                if self._group_strategy:
                    fallback_targets = self._group_strategy.get_fallback_targets(current_target, e)
                    
                    if not fallback_targets or attempt >= 4:
                        break
                    
                    # 选择下一个降级目标
                    current_target = fallback_targets[0]
                    attempt += 1
                    
                    # 记录降级尝试 - Services层负责日志记录
                    if self.logger:
                        self.logger.log_fallback_attempt(primary_target, current_target, e, attempt + 1)
                else:
                    break
        
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
        if not self.polling_pool_manager:
            raise LLMCallError("轮询池管理器未初始化")
            
        pool = self.polling_pool_manager.get_pool(primary_target)
        if not pool:
            raise ValueError(f"轮询池不存在: {primary_target}")
        
        try:
            # 轮询池内部处理实例轮换和降级
            result = await pool.call_llm(prompt, **kwargs)
            
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
        if not self.polling_pool_manager:
            return False
        pools = self.polling_pool_manager.list_all_status()
        return target in pools