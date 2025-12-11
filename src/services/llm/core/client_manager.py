"""LLM客户端管理器

专注于LLM客户端的生命周期管理。
"""

from typing import Any, Dict, List, Optional
from src.interfaces.dependency_injection import get_logger

from src.interfaces.llm import ILLMClient
from src.interfaces.llm.exceptions import LLMError
from src.services.llm.state_machine import StateMachine, LLMManagerState
from src.services.llm.utils.metadata_service import ClientMetadataService

logger = get_logger(__name__)


class LLMClientManager:
    """LLM客户端管理器
    
    专注于：
    1. 客户端的注册和注销
    2. 客户端的获取和列表
    3. 默认客户端管理
    4. 状态管理
    """
    
    def __init__(
        self,
        metadata_service: ClientMetadataService,
        state_machine: Optional[StateMachine] = None
    ) -> None:
        """初始化客户端管理器
        
        Args:
            metadata_service: 元数据服务
            state_machine: 状态机，如果未提供则创建新实例
        """
        self._metadata_service = metadata_service
        self._state_machine = state_machine or StateMachine()
        self._clients: Dict[str, ILLMClient] = {}
        self._default_client: Optional[str] = None
    
    @property
    def state(self) -> LLMManagerState:
        """获取管理器状态"""
        return self._state_machine.current_state
    
    @property
    def default_client(self) -> Optional[str]:
        """获取默认客户端名称"""
        return self._default_client
    
    def initialize_state(self) -> None:
        """初始化状态机"""
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            try:
                self._state_machine.transition_to(LLMManagerState.INITIALIZING)
                self._state_machine.transition_to(LLMManagerState.READY)
                logger.info("客户端管理器初始化完成")
            except Exception as e:
                self._state_machine.transition_to(LLMManagerState.ERROR, e)
                logger.error(f"客户端管理器初始化失败: {e}")
                raise LLMError(f"客户端管理器初始化失败: {e}") from e
    
    def register_client(self, name: str, client: ILLMClient) -> None:
        """注册LLM客户端
        
        Args:
            name: 客户端名称
            client: LLM客户端实例
            
        Raises:
            LLMError: 注册失败
        """
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            self.initialize_state()
        
        try:
            self._clients[name] = client
            logger.debug(f"LLM客户端 {name} 注册成功")
            
        except Exception as e:
            logger.error(f"LLM客户端 {name} 注册失败: {e}")
            raise LLMError(f"LLM客户端 {name} 注册失败: {e}") from e
    
    def unregister_client(self, name: str) -> None:
        """注销LLM客户端
        
        Args:
            name: 客户端名称
            
        Raises:
            LLMError: 注销失败
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
    
    def get_client(self, name: Optional[str] = None) -> ILLMClient:
        """获取LLM客户端
        
        Args:
            name: 客户端名称，如果为None则返回默认客户端
            
        Returns:
            ILLMClient: LLM客户端实例
            
        Raises:
            LLMError: 客户端不存在
        """
        if self._state_machine.current_state == LLMManagerState.UNINITIALIZED:
            self.initialize_state()
        
        if name is None:
            name = self._default_client
        
        if not name:
            raise LLMError("没有可用的LLM客户端")
        
        client = self._clients.get(name)
        if not client:
            raise LLMError(f"LLM客户端 {name} 不存在")
        
        return client
    
    def list_clients(self) -> List[str]:
        """列出所有已注册的客户端名称
        
        Returns:
            List[str]: 客户端名称列表
        """
        return list(self._clients.keys())
    
    def set_default_client(self, name: str) -> None:
        """设置默认客户端
        
        Args:
            name: 客户端名称
            
        Raises:
            LLMError: 客户端不存在
        """
        if name not in self._clients:
            raise LLMError(f"LLM客户端 {name} 不存在")
        
        self._default_client = name
        logger.info(f"设置默认LLM客户端: {name}")
    
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
    
    def clear_all_clients(self) -> None:
        """清除所有客户端"""
        self._clients.clear()
        self._default_client = None
        logger.info("已清除所有LLM客户端")
    
    def load_clients_from_dict(self, clients: Dict[str, ILLMClient]) -> None:
        """从字典加载客户端
        
        Args:
            clients: 客户端名称到客户端实例的映射
        """
        self.clear_all_clients()
        for name, client in clients.items():
            self.register_client(name, client)
        
        # 如果没有默认客户端，设置第一个为默认
        if not self._default_client and self._clients:
            self._default_client = next(iter(self._clients.keys()))
        
        logger.info(f"加载了 {len(self._clients)} 个LLM客户端")
    
    def has_client(self, name: str) -> bool:
        """检查客户端是否存在
        
        Args:
            name: 客户端名称
            
        Returns:
            bool: 客户端是否存在
        """
        return name in self._clients
    
    def get_client_count(self) -> int:
        """获取客户端数量
        
        Returns:
            int: 客户端数量
        """
        return len(self._clients)