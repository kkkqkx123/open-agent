"""LLM包装器工厂"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Type, Coroutine

from .base_wrapper import BaseLLMWrapper
from .task_group_wrapper import TaskGroupWrapper
from .polling_pool_wrapper import PollingPoolWrapper
from src.interfaces.llm.exceptions import WrapperFactoryError, WrapperConfigError
from ....interfaces.llm import ITaskGroupManager, IPollingPoolManager, IFallbackManager

logger = get_logger(__name__)


class LLMWrapperFactory:
    """LLM包装器工厂"""
    
    def __init__(self,
                 task_group_manager: ITaskGroupManager,
                 polling_pool_manager: Optional[IPollingPoolManager] = None,
                 fallback_manager: Optional[IFallbackManager] = None):
        """
        初始化包装器工厂
        
        Args:
            task_group_manager: 任务组管理器接口
            polling_pool_manager: 轮询池管理器接口
            fallback_manager: 降级管理器接口
        """
        self.task_group_manager = task_group_manager
        self.polling_pool_manager = polling_pool_manager
        self.fallback_manager = fallback_manager
        self._wrappers: Dict[str, BaseLLMWrapper] = {}
        
        # 注册包装器类型
        self._wrapper_types: Dict[str, Type[BaseLLMWrapper]] = {
            "task_group": TaskGroupWrapper,
            "polling_pool": PollingPoolWrapper
        }
        
        logger.info("LLM包装器工厂初始化完成")
    
    def create_task_group_wrapper(self, 
                                 name: str, 
                                 config: Optional[Dict[str, Any]] = None) -> TaskGroupWrapper:
        """创建任务组包装器"""
        try:
            wrapper = TaskGroupWrapper(
                name=name,
                task_group_manager=self.task_group_manager,
                fallback_manager=self.fallback_manager,
                config=config or {}
            )
            
            self._wrappers[name] = wrapper
            logger.info(f"创建任务组包装器: {name}")
            return wrapper
            
        except Exception as e:
            logger.error(f"创建任务组包装器失败 {name}: {e}")
            raise WrapperFactoryError(f"创建任务组包装器失败 {name}: {e}")
    
    def create_polling_pool_wrapper(self, 
                                   name: str, 
                                   config: Optional[Dict[str, Any]] = None) -> PollingPoolWrapper:
        """创建轮询池包装器"""
        if not self.polling_pool_manager:
            raise WrapperFactoryError("轮询池管理器未配置，无法创建轮询池包装器")
        
        try:
            wrapper = PollingPoolWrapper(
                name=name,
                polling_pool_manager=self.polling_pool_manager,
                config=config or {}
            )
            
            self._wrappers[name] = wrapper
            logger.info(f"创建轮询池包装器: {name}")
            return wrapper
            
        except Exception as e:
            logger.error(f"创建轮询池包装器失败 {name}: {e}")
            raise WrapperFactoryError(f"创建轮询池包装器失败 {name}: {e}")
    
    def create_wrapper_from_config(self, 
                                  name: str, 
                                  wrapper_type: str, 
                                  config: Optional[Dict[str, Any]] = None) -> BaseLLMWrapper:
        """从配置创建包装器"""
        if wrapper_type not in self._wrapper_types:
            raise WrapperFactoryError(f"不支持的包装器类型: {wrapper_type}")
        
        wrapper_class = self._wrapper_types[wrapper_type]
        
        try:
            if wrapper_type == "task_group":
                return self.create_task_group_wrapper(name, config)
            elif wrapper_type == "polling_pool":
                return self.create_polling_pool_wrapper(name, config)
            else:
                # 直接实例化
                wrapper = wrapper_class(name=name, config=config or {})
                self._wrappers[name] = wrapper
                logger.info(f"创建包装器: {name} (类型: {wrapper_type})")
                return wrapper
                
        except Exception as e:
            logger.error(f"创建包装器失败 {name} (类型: {wrapper_type}): {e}")
            raise WrapperFactoryError(f"创建包装器失败 {name} (类型: {wrapper_type}): {e}")
    
    def get_wrapper(self, name: str) -> Optional[BaseLLMWrapper]:
        """获取包装器"""
        return self._wrappers.get(name)
    
    def list_wrappers(self) -> Dict[str, str]:
        """列出所有包装器"""
        return {name: type(wrapper).__name__ for name, wrapper in self._wrappers.items()}
    
    def remove_wrapper(self, name: str) -> bool:
        """移除包装器"""
        if name in self._wrappers:
            del self._wrappers[name]
            logger.info(f"移除包装器: {name}")
            return True
        return False
    
    def register_wrapper_type(self, 
                             wrapper_type: str, 
                             wrapper_class: Type[BaseLLMWrapper]) -> None:
        """注册新的包装器类型"""
        if not issubclass(wrapper_class, BaseLLMWrapper):
            raise WrapperFactoryError(f"包装器类必须继承自BaseLLMWrapper: {wrapper_class}")
        
        self._wrapper_types[wrapper_type] = wrapper_class
        logger.info(f"注册包装器类型: {wrapper_type}")
    
    def create_wrappers_from_config(self, 
                                   wrappers_config: Dict[str, Any]) -> Dict[str, BaseLLMWrapper]:
        """从配置批量创建包装器"""
        created_wrappers = {}
        
        for name, config in wrappers_config.items():
            try:
                wrapper_type = config.get("type")
                if not wrapper_type:
                    logger.warning(f"包装器 {name} 缺少类型配置，跳过创建")
                    continue
                
                wrapper = self.create_wrapper_from_config(name, wrapper_type, config)
                created_wrappers[name] = wrapper
                
            except Exception as e:
                logger.error(f"创建包装器失败 {name}: {e}")
                # 继续创建其他包装器
                continue
        
        logger.info(f"批量创建包装器完成，成功: {len(created_wrappers)}, 总计: {len(wrappers_config)}")
        return created_wrappers
    
    def get_wrapper_stats(self) -> Dict[str, Any]:
        """获取所有包装器的统计信息"""
        stats = {
            "total_wrappers": len(self._wrappers),
            "wrapper_types": {},
            "wrapper_stats": {}
        }
        
        # 统计包装器类型
        for wrapper in self._wrappers.values():
            wrapper_type = type(wrapper).__name__
            stats["wrapper_types"][wrapper_type] = stats["wrapper_types"].get(wrapper_type, 0) + 1
        
        # 获取每个包装器的统计信息
        for name, wrapper in self._wrappers.items():
            try:
                wrapper_stats = wrapper.get_stats()
                stats["wrapper_stats"][name] = {
                    "type": type(wrapper).__name__,
                    "stats": wrapper_stats
                }
            except Exception as e:
                logger.warning(f"获取包装器统计信息失败 {name}: {e}")
                stats["wrapper_stats"][name] = {
                    "type": type(wrapper).__name__,
                    "error": str(e)
                }
        
        return stats
    def health_check_all(self) -> Dict[str, Any]:
        """对所有包装器执行健康检查"""
        health_status = {}
        
        for name, wrapper in self._wrappers.items():
            try:
                # 检查包装器是否有health_check方法
                health_check_method = getattr(wrapper, 'health_check', None)
                if health_check_method is not None and callable(health_check_method):
                    # 异步健康检查
                    import asyncio
                    try:
                        # 尝试获取事件循环
                        try:
                            loop = asyncio.get_event_loop()
                        except RuntimeError:
                            # 如果没有事件循环，则创建一个新的
                            loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(loop)
                            
                        coro = health_check_method()
                        if not isinstance(coro, Coroutine):
                            # 如果不是协程，直接调用
                            health_status[name] = coro
                        elif loop.is_running():
                            # 如果事件循环正在运行，使用 asyncio.run_coroutine_threadsafe
                            import concurrent.futures
                            with concurrent.futures.ThreadPoolExecutor() as executor:
                                future = executor.submit(asyncio.run, coro)
                                health_status[name] = future.result(timeout=5)
                        else:
                            health_status[name] = loop.run_until_complete(coro)
                    except Exception as e:
                        health_status[name] = {"healthy": False, "error": str(e)}
                else:
                    # 简单健康检查：检查包装器是否可访问
                    health_status[name] = {
                        "healthy": True,
                        "type": type(wrapper).__name__,
                        "note": "无健康检查方法"
                    }
            except Exception as e:
                health_status[name] = {"healthy": False, "error": str(e)}
        
        return health_status
        return health_status
    
    def reset_all_stats(self) -> None:
        """重置所有包装器的统计信息"""
        for name, wrapper in self._wrappers.items():
            try:
                reset_stats_method = getattr(wrapper, 'reset_stats', None)
                if reset_stats_method is not None and callable(reset_stats_method):
                    reset_stats_method()
                else:
                    reset_fallback_method = getattr(wrapper, 'reset_fallback_history', None)
                    if reset_fallback_method is not None and callable(reset_fallback_method):
                        reset_fallback_method()
                    else:
                        reset_rotation_method = getattr(wrapper, 'reset_rotation_history', None)
                        if reset_rotation_method is not None and callable(reset_rotation_method):
                            reset_rotation_method()
            except Exception as e:
                logger.warning(f"重置包装器统计信息失败 {name}: {e}")
        
        logger.info("已重置所有包装器的统计信息")
    
    def shutdown(self) -> None:
        """关闭包装器工厂"""
        # 清理所有包装器
        self._wrappers.clear()
        logger.info("包装器工厂已关闭")