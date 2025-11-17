"""
LLM管理服务

提供LLM客户端的创建、管理和降级功能。
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
from src.services.llm.config_validator import LLMConfigValidator, ValidationResult
from src.services.llm.metadata_service import ClientMetadataService

logger = logging.getLogger(__name__)


class LLMManager(ILLMManager):
    """LLM管理器实现
    
    负责LLM客户端的创建、管理和降级处理。
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
        self._clients: Dict[str, ILLMClient] = {}
        self._state_machine = StateMachine()
        self._default_client: Optional[str] = None
    
    async def initialize(self) -> None:
        """初始化LLM管理器
        
        创建配置中指定的所有LLM客户端。
        """
        if self._state_machine.current_state != LLMManagerState.UNINITIALIZED:
            return
        
        try:
            self._state_machine.transition_to(LLMManagerState.INITIALIZING)
            logger.info("初始化LLM管理器...")
            
            # 加载LLM客户端
            await self._load_clients_from_config()
            
            # 设置默认客户端
            default_client = self._config.get("default_client")
            if default_client and default_client in self._clients:
                self._default_client = default_client
            elif self._clients:
                # 如果没有指定默认客户端，使用第一个
                self._default_client = next(iter(self._clients.keys()))
            
            self._state_machine.transition_to(LLMManagerState.READY)
            logger.info(f"LLM管理器初始化完成，加载了 {len(self._clients)} 个客户端")
            
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
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        try:
            self._clients[name] = client
            logger.debug(f"LLM客户端 {name} 注册成功")
            
        except Exception as e:
            logger.error(f"LLM客户端 {name} 注册失败: {e}")
            raise LLMError(f"LLM客户端 {name} 注册失败: {e}") from e
    
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
            raise LLMError(f"LLM客户端 {name} 注销失败: {e}") from e
    
    async def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            name: 客户端名称，如果为None则返回默认客户端
            
        Returns:
            ILLMClient: LLM客户端实例
            
        Raises:
            ServiceError: 客户端不存在
        """
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        if name is None:
            name = self._default_client
        
        if not name:
            raise LLMError("没有可用的LLM客户端")
        
        client = self._clients.get(name)
        if not client:
            raise LLMError(f"LLM客户端 {name} 不存在")
        
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
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            await self.initialize()
        
        try:
            # 首选客户端逻辑
            if preferred_client and preferred_client in self._clients:
                return self._clients[preferred_client]
            
            # 使用任务组管理器获取适合的模型
            if task_type:
                try:
                    models = self._task_group_manager.get_models_for_group(task_type)
                    if models:
                        # 从任务组中获取第一个可用的客户端
                        for model_name in models:
                            if model_name in self._clients:
                                return self._clients[model_name]
                except Exception as e:
                    logger.warning(f"从任务组获取模型失败: {e}")
            
            # 使用默认客户端
            if self._default_client and self._default_client in self._clients:
                return self._clients[self._default_client]
            
            raise LLMError("没有可用的LLM客户端")
            
        except Exception as e:
            logger.error(f"获取任务 {task_type} 的LLM客户端失败: {e}")
            raise LLMError(f"获取任务 {task_type} 的LLM客户端失败: {e}") from e
    
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
        
        try:
            # 获取适合的客户端
            client = await self.get_client_for_task(task_type or "default", preferred_client)
            
            # 使用客户端执行请求
            return await client.generate_async(messages, parameters, **kwargs)
            
        except Exception as e:
            logger.error(f"执行LLM请求失败: {e}")
            raise LLMError(f"执行LLM请求失败: {e}") from e
    
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
        
        try:
            # 获取适合的客户端
            client = await self.get_client_for_task(task_type or "default", preferred_client)
            
            # 使用客户端执行流式请求
            async for chunk in client.stream_generate_async(messages, parameters, **kwargs):
                yield chunk
                
        except Exception as e:
            logger.error(f"执行流式LLM请求失败: {e}")
            raise LLMError(f"执行流式LLM请求失败: {e}") from e
    
    def _build_fallback_targets(self, task_type: Optional[str], preferred_client: Optional[str]) -> List[str]:
        """构建降级目标列表
        
        Args:
            task_type: 任务类型
            preferred_client: 首选客户端
            
        Returns:
            List[str]: 降级目标列表
        """
        targets = []
        
        # 添加任务组相关的降级目标
        if task_type:
            try:
                task_groups = self._task_group_manager.get_fallback_groups(task_type)
                targets.extend(task_groups)
            except Exception as e:
                logger.warning(f"获取任务组降级目标失败: {e}")
        
        # 添加默认客户端作为最后的降级选项
        if self._default_client and self._default_client != preferred_client:
            targets.append(self._default_client)
        
        return targets
    
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
            self._state_machine.transition_to(LLMManagerState.UNINITIALIZED)
            await self.initialize()
            
            logger.info("LLM客户端重新加载完成")
            
        except Exception as e:
            self._state_machine.transition_to(LLMManagerState.ERROR, e)
            logger.error(f"LLM客户端重新加载失败: {e}")
            raise LLMError(f"LLM客户端重新加载失败: {e}") from e
    
    async def _load_clients_from_config(self) -> None:
        """从配置加载LLM客户端"""
        clients_config = self._config.get("clients", [])
        if not clients_config:
            logger.info("配置中没有指定LLM客户端")
            return
        
        for client_config in clients_config:
            try:
                # 使用配置验证器验证配置
                validation_result = self._config_validator.validate_config(client_config)
                if not validation_result.is_valid:
                    client_name = self._get_config_name(client_config)
                    logger.error(f"LLM客户端配置验证失败 {client_name}: {validation_result.errors}")
                    strict_mode = self._config.get("strict_mode", False)
                    if strict_mode:
                        raise LLMError(f"LLM客户端配置验证失败 {client_name}: {validation_result.errors}")
                    else:
                        # 非严格模式下，跳过验证失败的客户端
                        continue
                
                # 注册验证通过的客户端
                client = validation_result.client
                if client:
                    client_name = self._get_config_name(client_config)
                    if isinstance(client_name, str):
                        await self.register_client(client_name, client)
                    
            except Exception as e:
                client_name = self._get_config_name(client_config)
                logger.error(f"加载LLM客户端 {client_name} 失败: {e}")
                strict_mode = self._config.get("strict_mode", False)
                if strict_mode:
                    raise
                else:
                    # 非严格模式下，跳过失败的客户端
                    continue
    
    def _get_config_name(self, config: Union[Dict[str, Any], LLMClientConfig]) -> str:
        """获取配置名称
        
        Args:
            config: 配置对象
            
        Returns:
            str: 配置名称
        """
        if isinstance(config, LLMClientConfig):
            return config.model_name
        
        if isinstance(config, dict):
            return config.get("name", config.get("model_name", "unknown"))
        
        return "unknown"
    
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
        
        # 使用元数据服务获取客户端信息
        return self._metadata_service.get_client_info(client, name)
    
    async def validate_client_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> bool:
        """验证客户端配置
        
        Args:
            config: LLM客户端配置（字典或LLMClientConfig对象）
            
        Returns:
            bool: 验证是否通过
        """
        try:
            # 使用配置验证器验证配置
            result = self._config_validator.validate_config(config)
            return result.is_valid
            
        except Exception as e:
            logger.error(f"LLM客户端配置验证失败: {e}")
            return False
    
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
        return self._default_client
    
    def set_default_client(self, name: str) -> None:
        """设置默认客户端
        
        Args:
            name: 客户端名称
            
        Raises:
            ServiceError: 客户端不存在
        """
        if name not in self._clients:
            raise LLMError(f"LLM客户端 {name} 不存在")
        
        self._default_client = name
        logger.info(f"设置默认LLM客户端: {name}")