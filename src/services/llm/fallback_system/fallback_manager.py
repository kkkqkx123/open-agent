"""降级管理器 - 轻量级协调器

整合了 Core 层和 Services 层的降级管理功能，通过组合多个专门的组件来实现功能。
"""

import time
import asyncio
from typing import Any, Optional, Sequence, Dict, List, Tuple
from src.infrastructure.messages.base import BaseMessage

from src.interfaces.llm import IFallbackStrategy, IClientFactory, IFallbackLogger, LLMResponse
# 从基础设施层导入降级配置和组件
from src.infrastructure.llm.fallback import FallbackConfig, FallbackAttempt, FallbackSession, FallbackEngine, FallbackTracker

# 新组件导入
from .fallback_strategy_manager import FallbackStrategyManager
from .fallback_config_manager import FallbackConfigManager

# 修复导入路径
from src.interfaces.llm.exceptions import LLMCallError

# Services 层的导入
from src.interfaces.llm import ITaskGroupManager, IPollingPoolManager
from src.core.llm.wrappers.fallback_manager import DefaultFallbackLogger


class FallbackManager:
    """降级管理器 - 轻量级协调器
    
    通过组合多个专门的组件来实现降级管理功能：
    1. FallbackEngine - 负责降级执行和编排逻辑
    2. FallbackTracker - 负责统计信息和会话管理
    3. FallbackStrategyManager - 负责策略管理
    4. FallbackConfigurationManager - 负责配置管理
    """
    
    def __init__(self, 
                 # Core 层参数
                 config: Optional[FallbackConfig] = None,
                 client_factory: Optional[IClientFactory] = None,
                 logger: Optional[IFallbackLogger] = None,
                 # Services 层参数
                 task_group_manager: Optional[ITaskGroupManager] = None,
                 polling_pool_manager: Optional[IPollingPoolManager] = None):
        """
        初始化降级管理器
        
        Args:
            config: 降级配置（Core 层）
            client_factory: 客户端工厂（Core 层）
            logger: 日志记录器（Core 层）
            task_group_manager: 任务组管理器（Services 层）
            polling_pool_manager: 轮询池管理器（Services 层）
        """
        # 处理日志记录器 - 直接创建默认日志记录器
        if logger is not None:
            fallback_logger = logger
        else:
            fallback_logger = DefaultFallbackLogger()
        
        # 初始化各个组件
        self._config_manager = FallbackConfigManager(config, client_factory)
        self._tracker = FallbackTracker()
        self._strategy_manager = FallbackStrategyManager(config, task_group_manager, polling_pool_manager)
        self._engine = FallbackEngine(
            config=config,
            client_factory=client_factory,
            logger=fallback_logger,
            task_group_manager=task_group_manager,
            polling_pool_manager=polling_pool_manager
        )
    
    # === Core 层方法 ===
    
    async def generate_with_fallback(
        self, 
        messages: Sequence[BaseMessage], 
        parameters: Optional[Dict[str, Any]] = None,
        primary_model: Optional[str] = None,
        **kwargs: Any
    ) -> LLMResponse:
        """
        带降级的异步生成（Core 层方法）
        
        Args:
            messages: 消息列表
            parameters: 生成参数
            primary_model: 主模型名称
            **kwargs: 其他参数
            
        Returns:
            LLM响应
            
        Raises:
            LLMCallError: 所有尝试都失败
        """
        # 委托给执行器
        response, session = await self._engine.generate_with_fallback(messages, parameters, primary_model, **kwargs)
        
        # 管理会话和统计
        self._tracker.add_session(session)
        
        return response
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取降级统计信息（整合 Core 和 Services 层）
        
        Returns:
            统计信息字典
        """
        return self._tracker.get_stats()
    
    def get_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取降级会话记录（Core 层方法）
        
        Args:
            limit: 限制返回数量
            
        Returns:
            会话记录列表
        """
        return self._tracker.get_sessions(limit)
    
    def clear_sessions(self) -> None:
        """清空会话记录（Core 层方法）"""
        self._tracker.clear_sessions()
    
    def is_enabled(self) -> bool:
        """检查降级是否启用（Core 层方法）"""
        return self._config_manager.is_enabled()
    
    def get_available_models(self) -> List[str]:
        """获取可用的模型列表（Core 层方法）"""
        return self._config_manager.get_available_models()
    
    def update_config(self, config: FallbackConfig) -> None:
        """
        更新降级配置（Core 层方法）
        
        Args:
            config: 新的降级配置
        """
        self._config_manager.update_config(config)
        self._engine.update_config(config)
        self._strategy_manager.update_config(config)
    
    # === Services 层方法 ===
    
    async def execute_with_fallback(
        self,
        primary_target: str,
        fallback_groups: List[str],
        prompt: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Any:
        """
        执行带降级的请求（Services 层方法）
        
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
        # 更新统计
        self._tracker.increment_total_requests()
        
        try:
            # 委托给编排器
            result = await self._engine.execute_with_fallback(
                primary_target, fallback_groups, prompt, parameters, **kwargs
            )
            
            # 更新统计
            self._tracker.increment_successful_requests()
            
            # 检查是否使用了降级
            if self._engine._is_polling_pool_target(primary_target):
                self._tracker.increment_pool_fallbacks()
            else:
                self._tracker.increment_group_fallbacks()
            
            return result
            
        except Exception as e:
            self._tracker.increment_failed_requests()
            raise LLMCallError(f"降级执行失败: {e}")
    
    def reset_stats(self) -> None:
        """重置所有统计信息"""
        self._tracker.reset_stats()
    
    # === 扩展方法 ===
    
    def get_core_stats(self) -> Dict[str, Any]:
        """
        获取 Core 层统计信息
        
        Returns:
            Core 层统计信息字典
        """
        return self._tracker.get_core_stats()
    
    def get_services_stats(self) -> Dict[str, Any]:
        """
        获取 Services 层统计信息
        
        Returns:
            Services 层统计信息字典
        """
        return self._tracker.get_services_stats()
    
    def get_successful_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取成功的会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            成功的会话记录列表
        """
        return self._tracker.get_successful_sessions(limit)
    
    def get_failed_sessions(self, limit: Optional[int] = None) -> List[FallbackSession]:
        """
        获取失败的会话记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            失败的会话记录列表
        """
        return self._tracker.get_failed_sessions(limit)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        获取配置摘要
        
        Returns:
            配置摘要字典
        """
        return self._config_manager.get_config_summary()
    
    def export_config(self) -> Dict[str, Any]:
        """
        导出配置为字典
        
        Returns:
            配置字典
        """
        return self._config_manager.export_config()
    
    def import_config(self, config_dict: Dict[str, Any]) -> None:
        """
        从字典导入配置
        
        Args:
            config_dict: 配置字典
        """
        self._config_manager.import_config(config_dict)
        config = self._config_manager.get_config()
        if config:
            self.update_config(config)
    
    def get_most_used_models(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取最常用的模型列表
        
        Args:
            limit: 返回的模型数量限制
            
        Returns:
            按使用次数排序的模型列表
        """
        return self._tracker.get_most_used_models(limit)
    
    def get_error_summary(self, limit: int = 10) -> List[Tuple[str, int]]:
        """
        获取错误摘要
        
        Args:
            limit: 返回的错误类型数量限制
            
        Returns:
            按出现次数排序的错误类型列表
        """
        return self._tracker.get_error_summary(limit)