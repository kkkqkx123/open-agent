"""任务组LLM包装器"""

import asyncio
from src.services.logger.injection import get_logger
import time
from typing import Dict, Any, Optional, List, Sequence
from datetime import datetime

from .base_wrapper import BaseLLMWrapper
from src.interfaces.llm.exceptions import TaskGroupWrapperError, WrapperExecutionError
from src.interfaces.llm import ITaskGroupManager, IFallbackManager, LLMResponse
from ..models import TokenUsage
from src.interfaces.llm.exceptions import LLMError

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
        self._fallback_history = []
        
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
        return target
    
    async def _generate_with_fallback(
        self, 
        messages: Sequence, 
        parameters: Optional[Dict[str, Any]], 
        **kwargs
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
        **kwargs
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
            
            # TODO: 这里需要创建实际的LLM客户端
            # 暂时返回模拟响应
            prompt = self._messages_to_prompt(messages)
            content = f"模拟响应 from {model_name}: {prompt[:50]}..."
            
            return self._create_llm_response(
                content=content,
                model=model_name
            )
            
        except Exception as e:
            logger.error(f"直接生成失败: {e}")
            raise e
    
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
        
        return []
    
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
        prompt_tokens = max(1, len(content) // 4)  # 简单估算：字符数除以4
        completion_tokens = prompt_tokens // 2  # 简单估算
        
        final_token_usage = token_usage or TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens
        )
        
        final_metadata = metadata or {}
        final_metadata.update({
            "wrapper": "task_group",
            "target": self._current_target,
            "attempt_count": self._attempt_count
        })
        
        return super()._create_llm_response(
            content=content,
            model=model,
            token_usage=final_token_usage,
            message=message,
            metadata=final_metadata
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