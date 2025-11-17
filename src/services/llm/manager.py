"""
LLM管理服务

提供LLM客户端的创建、管理和降级功能。
"""

from typing import Any, Dict, List, Optional, Union
import logging
from enum import Enum

from src.core.llm.interfaces import ILLMClient, ILLMManager
from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMConfig, LLMRegistryConfig
from core.llm.wrappers.fallback_manager import EnhancedFallbackManager
from src.services.llm.task_group_manager import TaskGroupManager
from src.core.common.exceptions import ServiceError

logger = logging.getLogger(__name__)


class LLMManagerState(Enum):
    """LLM管理器状态"""
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"


class LLMManager(ILLMManager):
    """LLM管理器实现
    
    负责LLM客户端的创建、管理和降级处理。
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        fallback_manager: EnhancedFallbackManager,
        task_group_manager: TaskGroupManager,
        config: Optional[LLMRegistryConfig] = None
    ) -> None:
        """初始化LLM管理器
        
        Args:
            factory: LLM工厂
            fallback_manager: 降级管理器
            task_group_manager: 任务组管理器
            config: LLM注册表配置
        """
        self._factory = factory
        self._fallback_manager = fallback_manager
        self._task_group_manager = task_group_manager
        self._config = config or LLMRegistryConfig()
        self._clients: Dict[str, ILLMClient] = {}
        self._state = LLMManagerState.UNINITIALIZED
        self._default_client: Optional[str] = None
    
    async def initialize(self) -> None:
        """初始化LLM管理器
        
        创建配置中指定的所有LLM客户端。
        """
        if self._state != LLMManagerState.UNINITIALIZED:
            return
        
        self._state = LLMManagerState.INITIALIZING
        logger.info("初始化LLM管理器...")
        
        try:
            # 初始化降级管理器和任务组管理器
            await self._fallback_manager.initialize()
            await self._task_group_manager.initialize()
            
            # 加载LLM客户端
            await self._load_clients_from_config()
            
            # 设置默认客户端
            if self._config.default_client and self._config.default_client in self._clients:
                self._default_client = self._config.default_client
            elif self._clients:
                # 如果没有指定默认客户端，使用第一个
                self._default_client = next(iter(self._clients.keys()))
            
            self._state = LLMManagerState.READY
            logger.info(f"LLM管理器初始化完成，加载了 {len(self._clients)} 个客户端")
            
        except Exception as e:
            self._state = LLMManagerState.ERROR
            logger.error(f"LLM管理器初始化失败: {e}")
            raise ServiceError(f"LLM管理器初始化失败: {e}")
    
    async def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端
        
        Args:
            name: 客户端名称
            client: LLM客户端实例
        """
        if self._state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        try:
            self._clients[name] = client
            logger.debug(f"LLM客户端 {name} 注册成功")
            
        except Exception as e:
            logger.error(f"LLM客户端 {name} 注册失败: {e}")
            raise ServiceError(f"LLM客户端 {name} 注册失败: {e}")
    
    async def unregister_client(self, name: str) -> None:
        """注销LLM客户端
        
        Args:
            name: 客户端名称
        """
        try:
            if name in self._clients:
                del self._clients[name]
                if self._default_client == name:
                    # 重新选择默认客户端
                    self._default_client = next(iter(self._clients.keys())) if self._clients else None
            logger.debug(f"LLM客户端 {name} 注销成功")
            
        except Exception as e:
            logger.error(f"LLM客户端 {name} 注销失败: {e}")
            raise ServiceError(f"LLM客户端 {name} 注销失败: {e}")
    
    async def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            name: 客户端名称，如果为None则返回默认客户端
            
        Returns:
            ILLMClient: LLM客户端实例
            
        Raises:
            ServiceError: 客户端不存在
        """
        if self._state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        if name is None:
            name = self._default_client
        
        if not name:
            raise ServiceError("没有可用的LLM客户端")
        
        client = self._clients.get(name)
        if not client:
            raise ServiceError(f"LLM客户端 {name} 不存在")
        
        return client
    
    async def list_clients(self) -> List[str]:
        """列出所有已注册的客户端名称
        
        Returns:
            List[str]: 客户端名称列表
        """
        return list(self._clients.keys())
    
    async def get_client_for_task(
        self,
        task_type: str,
        preferred_client: Optional[str] = None
    ) -> ILLMClient:
        """根据任务类型获取最适合的LLM客户端
        
        Args:
            task_type: 任务类型
            preferred_client: 首选客户端名称
            
        Returns:
            ILLMClient: 适合的LLM客户端实例
        """
        if self._state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        try:
            # 使用任务组管理器获取适合的客户端
            client_name = await self._task_group_manager.get_client_for_task(
                task_type, preferred_client
            )
            
            if client_name and client_name in self._clients:
                return self._clients[client_name]
            
            # 如果任务组管理器没有返回合适的客户端，使用默认逻辑
            if preferred_client and preferred_client in self._clients:
                return self._clients[preferred_client]
            
            if self._default_client and self._default_client in self._clients:
                return self._clients[self._default_client]
            
            raise ServiceError("没有可用的LLM客户端")
            
        except Exception as e:
            logger.error(f"获取任务 {task_type} 的LLM客户端失败: {e}")
            raise ServiceError(f"获取任务 {task_type} 的LLM客户端失败: {e}")
    
    async def execute_with_fallback(
        self,
        prompt: str,
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        **kwargs
    ) -> str:
        """使用降级机制执行LLM请求
        
        Args:
            prompt: 提示词
            task_type: 任务类型
            preferred_client: 首选客户端名称
            **kwargs: 其他参数
            
        Returns:
            str: LLM响应
        """
        if self._state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        try:
            # 使用降级管理器执行请求
            result = await self._fallback_manager.execute_with_fallback(
                prompt=prompt,
                task_type=task_type,
                preferred_client=preferred_client,
                clients=self._clients,
                **kwargs
            )
            
            return result
            
        except Exception as e:
            logger.error(f"执行LLM请求失败: {e}")
            raise ServiceError(f"执行LLM请求失败: {e}")
    
    async def reload_clients(self) -> None:
        """重新加载所有LLM客户端
        
        清除当前客户端并重新加载配置中的客户端。
        """
        logger.info("重新加载LLM客户端...")
        
        try:
            # 清除当前客户端
            self._clients.clear()
            self._default_client = None
            
            # 重新初始化
            self._state = LLMManagerState.UNINITIALIZED
            await self.initialize()
            
            logger.info("LLM客户端重新加载完成")
            
        except Exception as e:
            self._state = LLMManagerState.ERROR
            logger.error(f"LLM客户端重新加载失败: {e}")
            raise ServiceError(f"LLM客户端重新加载失败: {e}")
    
    async def _load_clients_from_config(self) -> None:
        """从配置加载LLM客户端"""
        if not self._config.clients:
            logger.info("配置中没有指定LLM客户端")
            return
        
        for client_config in self._config.clients:
            try:
                # 使用工厂创建客户端
                client = await self._factory.create_client(client_config)
                if client:
                    await self.register_client(client_config.name, client)
                    
            except Exception as e:
                logger.error(f"加载LLM客户端 {client_config.name} 失败: {e}")
                if self._config.strict_mode:
                    raise
                else:
                    # 非严格模式下，跳过失败的客户端
                    continue
    
    def get_client_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取客户端信息
        
        Args:
            name: 客户端名称
            
        Returns:
            Optional[Dict[str, Any]]: 客户端信息，如果不存在则返回None
        """
        client = self._clients.get(name)
        if not client:
            return None
        
        return {
            "name": name,
            "model": getattr(client, 'model', 'unknown'),
            "provider": getattr(client, 'provider', 'unknown'),
            "is_default": name == self._default_client,
            "supports_function_calling": getattr(client, 'supports_function_calling', lambda: False)(),
        }
    
    async def validate_client_config(self, config: LLMConfig) -> bool:
        """验证客户端配置
        
        Args:
            config: LLM配置
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 尝试创建客户端实例来验证配置
            client = await self._factory.create_client(config)
            return client is not None
            
        except Exception as e:
            logger.error(f"LLM客户端配置验证失败: {e}")
            return False
    
    @property
    def factory(self) -> LLMFactory:
        """获取LLM工厂"""
        return self._factory
    
    @property
    def fallback_manager(self) -> EnhancedFallbackManager:
        """获取降级管理器"""
        return self._fallback_manager
    
    @property
    def task_group_manager(self) -> TaskGroupManager:
        """获取任务组管理器"""
        return self._task_group_manager
    
    @property
    def state(self) -> LLMManagerState:
        """获取管理器状态"""
        return self._state
    
    @property
    def default_client(self) -> Optional[str]:
        """获取默认客户端名称"""
        return self._default_client
    
    def set_default_client(self, name: str) -> None:
        """设置默认客户端
        
        Args:
            name: 客户端名称
            
        Raises:
            ServiceError: 客户端不存在
        """
        if name not in self._clients:
            raise ServiceError(f"LLM客户端 {name} 不存在")
        
        self._default_client = name
        logger.info(f"设置默认LLM客户端: {name}")