"""
LLM管理服务

提供LLM客户端的统一管理和协调功能。
"""

from typing import Any, Dict, List, Optional, Union, Sequence, AsyncGenerator, TYPE_CHECKING
from src.interfaces.dependency_injection import get_logger

from src.interfaces.llm import ILLMClient, ILLMManager, IFallbackManager, ITaskGroupManager, ILLMCallHook, LLMResponse
from src.interfaces.messages import IBaseMessage
from src.core.llm.factory import LLMFactory
from src.core.config.models import LLMConfig
from src.interfaces.llm.exceptions import LLMError
from src.services.llm.state_machine import StateMachine, LLMManagerState
from src.services.llm.utils.metadata_service import ClientMetadataService
from src.core.config.config_manager import ConfigManager
from src.services.llm.core.client_manager import LLMClientManager
from src.services.llm.core.request_executor import LLMRequestExecutor
from src.services.llm.core.manager_registry import manager_registry, ManagerStatus
from src.infrastructure.validation.result import ValidationResult

logger = get_logger(__name__)


class LLMManager(ILLMManager):
    """LLM管理器实现
    
    重构后专注于：
    1. 协调各个服务组件
    2. 提供统一的对外接口
    3. 管理整体初始化流程
    4. 管理器间通信协调
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        fallback_manager: IFallbackManager,
        task_group_manager: ITaskGroupManager,
        metadata_service: ClientMetadataService
    ) -> None:
        """初始化LLM管理器
        
        Args:
            factory: LLM工厂
            fallback_manager: 降级管理器
            task_group_manager: 任务组管理器
            metadata_service: 元数据服务
        """
        self._factory = factory
        self._fallback_manager = fallback_manager
        self._task_group_manager = task_group_manager
        self._metadata_service = metadata_service
        
        # 历史记录钩子
        self._history_hooks: List[ILLMCallHook] = []
        
        # 创建状态机
        self._state_machine = StateMachine()
        
        # 创建配置管理器
        self._config_manager = ConfigManager()
        
        
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
        
        # 注册到管理器注册表
        self._register_with_registry()
    
    def _register_with_registry(self) -> None:
        """注册到管理器注册表"""
        # 注册自身
        manager_registry.register_manager(
            name="llm_manager",
            manager_instance=self,
            dependencies=["config_manager", "client_manager", "request_executor"],
            metadata={"type": "main_coordinator"}
        )
        
        # 注册子管理器
        manager_registry.register_manager(
            name="config_manager",
            manager_instance=self._config_manager,
            dependencies=[],
            metadata={"type": "config_management"}
        )
        
        manager_registry.register_manager(
            name="client_manager",
            manager_instance=self._client_manager,
            dependencies=["metadata_service"],
            metadata={"type": "client_lifecycle"}
        )
        
        manager_registry.register_manager(
            name="request_executor",
            manager_instance=self._request_executor,
            dependencies=["fallback_manager", "task_group_manager"],
            metadata={"type": "request_execution"}
        )
        
        # 注册通信处理器
        self._register_communication_handlers()
    
    def _register_communication_handlers(self) -> None:
        """注册通信处理器"""
        # 处理配置更新事件
        manager_registry.register_communication_handler(
            "llm_manager", "config_updated", self._handle_config_updated
        )
        
        # 处理客户端状态变更事件
        manager_registry.register_communication_handler(
            "llm_manager", "client_status_changed", self._handle_client_status_changed
        )
        
        # 处理降级状态变更事件
        manager_registry.register_communication_handler(
            "llm_manager", "fallback_status_changed", self._handle_fallback_status_changed
        )
    
    def _handle_config_updated(self, from_manager: str, config_data: Any) -> None:
        """处理配置更新事件"""
        logger.info(f"收到配置更新事件，来源: {from_manager}")
        # 可以在这里实现配置热更新逻辑
        try:
            # 清除所有缓存以强制重新加载
            self._config_manager.invalidate_cache()
            logger.info("配置热更新完成")
        except Exception as e:
            logger.error(f"配置热更新失败: {e}")
    
    def _handle_client_status_changed(self, from_manager: str, status_data: Any) -> None:
        """处理客户端状态变更事件"""
        logger.debug(f"收到客户端状态变更事件，来源: {from_manager}, 数据: {status_data}")
        # 可以在这里实现客户端状态同步逻辑
    
    def _handle_fallback_status_changed(self, from_manager: str, status_data: Any) -> None:
        """处理降级状态变更事件"""
        logger.debug(f"收到降级状态变更事件，来源: {from_manager}, 数据: {status_data}")
        # 可以在这里实现降级状态同步逻辑
    
    async def initialize(self) -> None:
        """初始化LLM管理器
        
        创建配置中指定的所有LLM客户端。
        """
        if self._state_machine.current_state != LLMManagerState.UNINITIALIZED:
            return
        
        try:
            # 更新状态
            manager_registry.update_manager_status("llm_manager", ManagerStatus.INITIALIZING)
            self._state_machine.transition_to(LLMManagerState.INITIALIZING)
            logger.info("初始化LLM管理器...")
            
            # 使用工厂创建客户端
            # 注：这里可以根据需要从配置加载客户端信息
            clients = {}
            
            # 使用客户端管理器加载客户端
            self._client_manager.load_clients_from_dict(clients)
            
            # 设置默认客户端
            if self._client_manager.get_client_count() > 0:
                # 如果有多个客户端，使用第一个作为默认
                first_client = self._client_manager.list_clients()[0]
                self._client_manager.set_default_client(first_client)
            
            # 更新状态
            self._state_machine.transition_to(LLMManagerState.READY)
            manager_registry.update_manager_status("llm_manager", ManagerStatus.READY)
            
            logger.info(f"LLM管理器初始化完成，加载了 {self._client_manager.get_client_count()} 个客户端")
            
            # 广播初始化完成事件
            manager_registry.broadcast_message("llm_manager", "initialization_completed", {
                "client_count": self._client_manager.get_client_count(),
                "default_client": self._client_manager.default_client
            })
            
        except Exception as e:
            # 更新状态
            self._state_machine.transition_to(LLMManagerState.ERROR, e)
            manager_registry.update_manager_status("llm_manager", ManagerStatus.ERROR, str(e))
            logger.error(f"LLM管理器初始化失败: {e}")
            raise LLMError(f"LLM管理器初始化失败: {e}") from e
    
    async def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端
        
        Args:
            name: 客户端名称
            client: LLM客户端实例
        """
        self._client_manager.register_client(name, client)
        
        # 广播客户端注册事件
        manager_registry.broadcast_message("llm_manager", "client_registered", {
            "name": name,
            "client_class": client.__class__.__name__
        })
    
    async def unregister_client(self, name: str) -> None:
        """注销LLM客户端
        
        Args:
            name: 客户端名称
        """
        self._client_manager.unregister_client(name)
        
        # 广播客户端注销事件
        manager_registry.broadcast_message("llm_manager", "client_unregistered", {
            "name": name
        })
    
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
        messages: Sequence[IBaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
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
        
        # 执行前钩子
        await self._execute_before_hooks(messages, parameters, **kwargs)
        
        try:
            # 将IBaseMessage转换为BaseMessage（类型兼容性）
            # IBaseMessage是接口，BaseMessage是实现，传递messages时直接转换
            from src.infrastructure.messages.base import BaseMessage
            base_messages = [msg if isinstance(msg, BaseMessage) else msg for msg in messages]
            
            # 使用请求执行器执行请求
            response = await self._request_executor.execute_with_fallback(
                client=client,
                messages=base_messages,  # type: ignore
                task_type=task_type,
                parameters=parameters,
                **kwargs
            )
            
            # 执行后钩子
            await self._execute_after_hooks(response, messages, parameters, **kwargs)
            
            return response
            
        except Exception as e:
            # 执行错误钩子
            error_response = await self._execute_error_hooks(e, messages, parameters, **kwargs)
            if error_response is not None:
                return error_response
            raise
    
    async def stream_with_fallback(
        self,
        messages: Sequence[IBaseMessage],
        task_type: Optional[str] = None,
        preferred_client: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
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
        
        # 执行前钩子
        await self._execute_before_hooks(messages, parameters, **kwargs)
        
        try:
            # 将IBaseMessage转换为BaseMessage（类型兼容性）
            from src.infrastructure.messages.base import BaseMessage
            base_messages = [msg if isinstance(msg, BaseMessage) else msg for msg in messages]
            
            # 使用请求执行器执行流式请求
            response_chunks = []
            async for chunk in self._request_executor.stream_with_fallback(
                client=client,
                messages=base_messages,  # type: ignore
                task_type=task_type,
                parameters=parameters,
                **kwargs
            ):
                response_chunks.append(chunk)
                yield chunk
            
            # 创建响应对象用于后钩子
            response = LLMResponse(
                content=''.join(response_chunks),
                model=getattr(client, 'model_name', 'unknown'),
                finish_reason='stop',
                tokens_used=0,
                metadata=kwargs.get('metadata', {})
            )
            
            # 执行后钩子
            await self._execute_after_hooks(response, messages, parameters, **kwargs)
            
        except Exception as e:
            # 执行错误钩子
            error_response = await self._execute_error_hooks(e, messages, parameters, **kwargs)
            if error_response is not None:
                for chunk in error_response.content:
                    yield chunk
            else:
                raise
    
    async def reload_clients(self) -> None:
        """重新加载所有LLM客户端
        
        清除当前客户端并重新加载配置中的客户端。
        """
        logger.info("重新加载LLM客户端...")
        
        try:
            # 广播重新加载开始事件
            manager_registry.broadcast_message("llm_manager", "reload_started", {})
            
            # 清除当前客户端
            self._client_manager.clear_all_clients()
            
            # 重新初始化
            self._state_machine.transition_to(LLMManagerState.UNINITIALIZED)
            await self.initialize()
            
            logger.info("LLM客户端重新加载完成")
            
            # 广播重新加载完成事件
            manager_registry.broadcast_message("llm_manager", "reload_completed", {
                "client_count": self._client_manager.get_client_count()
            })
            
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
    
    async def validate_client_config(self, config: Union[Dict[str, Any], LLMConfig]) -> bool:
        """验证客户端配置
        
        Args:
            config: LLM客户端配置（字典或LLMConfig对象）
            
        Returns:
            bool: 验证是否通过
        """
        # 如果是LLMConfig对象，转换为字典
        if isinstance(config, LLMConfig):
            config_dict = config.model_dump() if hasattr(config, 'model_dump') else vars(config)
        else:
            config_dict = config
        result = self._config_manager.validate_config(config_dict)
        return result.is_valid
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态
        
        Returns:
            Dict[str, Any]: 配置状态信息
        """
        return self._config_manager.get_config_status()
    
    def get_registry_status(self) -> Dict[str, Any]:
        """获取管理器注册表状态
        
        Returns:
            Dict[str, Any]: 注册表状态信息
        """
        return manager_registry.get_registry_status()
    
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
        
        # 广播默认客户端变更事件
        manager_registry.broadcast_message("llm_manager", "default_client_changed", {
            "name": name
        })
    
    def add_history_hook(self, hook: ILLMCallHook) -> None:
        """添加历史记录钩子
        
        Args:
            hook: 历史记录钩子实例
        """
        self._history_hooks.append(hook)
        logger.info(f"添加历史记录钩子: {hook.__class__.__name__}")
    
    def remove_history_hook(self, hook: ILLMCallHook) -> None:
        """移除历史记录钩子
        
        Args:
            hook: 历史记录钩子实例
        """
        if hook in self._history_hooks:
            self._history_hooks.remove(hook)
            logger.info(f"移除历史记录钩子: {hook.__class__.__name__}")
    
    def clear_history_hooks(self) -> None:
        """清除所有历史记录钩子"""
        count = len(self._history_hooks)
        self._history_hooks.clear()
        logger.info(f"清除了 {count} 个历史记录钩子")
    
    def get_history_hooks_count(self) -> int:
        """获取历史记录钩子数量"""
        return len(self._history_hooks)
    
    async def _execute_before_hooks(
        self,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """执行前钩子"""
        for hook in self._history_hooks:
            try:
                hook.before_call(messages, parameters, **kwargs)
            except Exception as e:
                logger.warning(f"执行前钩子失败: {e}")
    
    async def _execute_after_hooks(
        self,
        response: LLMResponse,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """执行后钩子"""
        for hook in self._history_hooks:
            try:
                hook.after_call(response, messages, parameters, **kwargs)
            except Exception as e:
                logger.warning(f"执行后钩子失败: {e}")
    
    async def _execute_error_hooks(
        self,
        error: Exception,
        messages: Sequence[IBaseMessage],
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> Optional[LLMResponse]:
        """执行错误钩子"""
        for hook in self._history_hooks:
            try:
                response = hook.on_error(error, messages, parameters, **kwargs)
                if response is not None:
                    return response
            except Exception as e:
                logger.warning(f"执行错误钩子失败: {e}")
        return None