"""
LLM管理服务

提供LLM客户端的统一管理和协调功能。
"""

from typing import Any, Dict, List, Optional, Union, Sequence, AsyncGenerator
import logging
from langchain_core.messages import BaseMessage

from src.core.llm.interfaces import ILLMClient, ILLMManager, IFallbackManager, ITaskGroupManager
from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMClientConfig
from src.core.llm.exceptions import LLMError
from src.core.llm.models import LLMResponse
from src.services.llm.state_machine import StateMachine, LLMManagerState
from src.services.llm.config.config_validator import LLMConfigValidator, ValidationResult
from src.services.llm.metadata_service import ClientMetadataService
from src.services.llm.config.configuration_service import LLMClientConfigurationService
from services.llm.core.client_manager import LLMClientManager
from services.llm.core.request_executor import LLMRequestExecutor

logger = logging.getLogger(__name__)


class LLMManager(ILLMManager):
    """LLM管理器实现
    
    重构后专注于：
    1. 协调各个服务组件
    2. 提供统一的对外接口
    3. 管理整体初始化流程
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        fallback_manager: IFallbackManager,
        task_group_manager: ITaskGroupManager,
        config_validator: LLMConfigValidator,
        metadata_service: ClientMetadataService,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化LLM管理器
        
        Args:
            factory: LLM工厂
            fallback_manager: 降级管理器
            task_group_manager: 任务组管理器
            config_validator: 配置验证器
            metadata_service: 元数据服务
            config: LLM配置字典
        """
        self._factory = factory
        self._fallback_manager = fallback_manager
        self._task_group_manager = task_group_manager
        self._config_validator = config_validator
        self._metadata_service = metadata_service
        self._config = config or {}
        
        # 创建状态机
        self._state_machine = StateMachine()
        
        # 创建配置服务
        self._config_service = LLMClientConfigurationService(
            factory=factory,
            config_validator=config_validator,
            config=config
        )
        
        # 创建客户端管理器
        self._client_manager = LLMClientManager(
            metadata_service=metadata_service,
            state_machine=self._state_machine
        )
        
        # 创建请求执行器
        self._request_executor = LLMRequestExecutor(
            fallback_manager=fallback_manager,
            task_group_manager=task_group_manager
        )
    
    async def initialize(self) -> None:
        """初始化LLM管理器
        
        创建配置中指定的所有LLM客户端。
        """
        if self._state_machine.current_state != LLMManagerState.UNINITIALIZED:
            return
        
        try:
            self._state_machine.transition_to(LLMManagerState.INITIALIZING)
            logger.info("初始化LLM管理器...")
            
            # 使用配置服务加载客户端
            clients = self._config_service.load_clients_from_config()
            
            # 使用客户端管理器加载客户端
            self._client_manager.load_clients_from_dict(clients)
            
            # 设置默认客户端
            default_client_name = self._config_service.get_default_client_name()
            if default_client_name and self._client_manager.has_client(default_client_name):
                self._client_manager.set_default_client(default_client_name)
            elif self._client_manager.get_client_count() > 0:
                # 如果没有指定默认客户端，使用第一个
                first_client = self._client_manager.list_clients()[0]
                self._client_manager.set_default_client(first_client)
            
            self._state_machine.transition_to(LLMManagerState.READY)
            logger.info(f"LLM管理器初始化完成，加载了 {self._client_manager.get_client_count()} 个客户端")
            
        except Exception as e:
            self._state_machine.transition_to(LLMManagerState.ERROR, e)
            logger.error(f"LLM管理器初始化失败: {e}")
            raise LLMError(f"LLM管理器初始化失败: {e}") from e
    
    async def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端
        
        Args:
            name: 客户端名称
            client: LLM客户端实例
        """
        self._client_manager.register_client(name, client)
    
    async def unregister_client(self, name: str) -> None:
        """注销LLM客户端
        
        Args:
            name: 客户端名称
        """
        self._client_manager.unregister_client(name)
    
    async def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            name: 客户端名称，如果为None则返回默认客户端
            
        Returns:
            ILLMClient: LLM客户端实例
        """
        return self._client_manager.get_client(name)
    
    async def list_clients(self) -> List[str]:
        """列出所有已注册的客户端名称
        
        Returns:
            List[str]: 客户端名称列表
        """
        return self._client_manager.list_clients()
    
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
        # 获取所有可用客户端
        available_clients = {}
        for client_name in self._client_manager.list_clients():
            available_clients[client_name] = self._client_manager.get_client(client_name)
        
        # 使用请求执行器选择合适的客户端
        return self._request_executor.get_client_for_task(
            task_type=task_type,
            available_clients=available_clients,
            preferred_client=preferred_client
        )
    
    async def execute_with_fallback(
        self,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> LLMResponse:
        """使用降级机制执行LLM请求
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            preferred_client: 首选客户端名称
            parameters: 参数
            **kwargs: 其他参数
            
        Returns:
            LLMResponse: LLM响应
        """
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        # 获取适合的客户端
        client = await self.get_client_for_task(task_type or "default", preferred_client)
        
        # 使用请求执行器执行请求
        return await self._request_executor.execute_with_fallback(
            client=client,
            messages=messages,
            task_type=task_type,
            parameters=parameters,
            **kwargs
        )
    
    async def stream_with_fallback(
        self,
        messages: Sequence[BaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """使用降级机制执行流式LLM请求
        
        Args:
            messages: 消息列表
            task_type: 任务类型
            preferred_client: 首选客户端名称
            parameters: 参数
            **kwargs: 其他参数
            
        Yields:
            str: LLM响应片段
        """
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        # 获取适合的客户端
        client = await self.get_client_for_task(task_type or "default", preferred_client)
        
        # 使用请求执行器执行流式请求
        async for chunk in self._request_executor.stream_with_fallback(
            client=client,
            messages=messages,
            task_type=task_type,
            parameters=parameters,
            **kwargs
        ):
            yield chunk
    
    async def reload_clients(self) -> None:
        """重新加载所有LLM客户端
        
        清除当前客户端并重新加载配置中的客户端。
        """
        logger.info("重新加载LLM客户端...")
        
        try:
            # 清除当前客户端
            self._client_manager.clear_all_clients()
            
            # 重新初始化
            self._state_machine.transition_to(LLMManagerState.UNINITIALIZED)
            await self.initialize()
            
            logger.info("LLM客户端重新加载完成")
            
        except Exception as e:
            self._state_machine.transition_to(LLMManagerState.ERROR, e)
            logger.error(f"LLM客户端重新加载失败: {e}")
            raise LLMError(f"LLM客户端重新加载失败: {e}") from e
    
    def get_client_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取客户端信息
        
        Args:
            name: 客户端名称
            
        Returns:
            Optional[Dict[str, Any]]: 客户端信息，如果不存在则返回None
        """
        return self._client_manager.get_client_info(name)
    
    async def validate_client_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> bool:
        """验证客户端配置
        
        Args:
            config: LLM客户端配置（字典或LLMClientConfig对象）
            
        Returns:
            bool: 验证是否通过
        """
        result = self._config_service.validate_client_config(config)
        return result.is_valid
    
    @property
    def factory(self) -> LLMFactory:
        """获取LLM工厂"""
        return self._factory
    
    @property
    def fallback_manager(self) -> IFallbackManager:
        """获取降级管理器"""
        return self._fallback_manager
    
    @property
    def task_group_manager(self) -> ITaskGroupManager:
        """获取任务组管理器"""
        return self._task_group_manager
    
    @property
    def state(self) -> LLMManagerState:
        """获取管理器状态"""
        return self._state_machine.current_state
    
    @property
    def default_client(self) -> Optional[str]:
        """获取默认客户端名称"""
        return self._client_manager.default_client
    
    def set_default_client(self, name: str) -> None:
        """设置默认客户端
        
        Args:
            name: 客户端名称
            
        Raises:
            ServiceError: 客户端不存在
        """
        self._client_manager.set_default_client(name)