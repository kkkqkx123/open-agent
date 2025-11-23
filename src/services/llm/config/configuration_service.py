"""LLM客户端配置服务

重构后专注于LLM客户端的创建和初始化，配置管理委托给ConfigManager。
"""

from typing import Any, Dict, List, Optional, Union
import logging

from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMClientConfig
from core.common.exceptions.llm import LLMError
from .config_validator import LLMConfigValidator, ValidationResult
from .config_manager import ConfigManager

logger = logging.getLogger(__name__)


class LLMClientConfigurationService:
    """LLM客户端配置服务
    
    重构后专注于：
    1. LLM客户端的创建和初始化
    2. 客户端配置的特定验证
    3. 客户端相关的错误处理
    
    配置管理委托给ConfigManager。
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        config_validator: LLMConfigValidator,
        config_manager: ConfigManager
    ) -> None:
        """初始化配置服务
        
        Args:
            factory: LLM工厂
            config_validator: 配置验证器
            config_manager: 配置管理器
        """
        self._factory = factory
        self._config_validator = config_validator
        self._config_manager = config_manager
    
    def load_clients_from_config(self) -> Dict[str, Any]:
        """从配置加载LLM客户端
        
        委托给ConfigManager处理
        
        Returns:
            Dict[str, Any]: 客户端名称到客户端实例的映射
            
        Raises:
            LLMError: 配置加载失败
        """
        return self._config_manager.load_clients_from_config()
    
    def validate_client_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> ValidationResult:
        """验证客户端配置
        
        委托给ConfigManager处理
        
        Args:
            config: LLM客户端配置（字典或LLMClientConfig对象）
            
        Returns:
            ValidationResult: 验证结果
        """
        return self._config_manager.validate_config("client", config)
    
    def get_default_client_name(self) -> Optional[str]:
        """获取默认客户端名称
        
        委托给ConfigManager处理
        
        Returns:
            Optional[str]: 默认客户端名称，如果未配置则返回None
        """
        return self._config_manager.get_default_client_name()
    
    def is_strict_mode(self) -> bool:
        """检查是否为严格模式
        
        委托给ConfigManager处理
        
        Returns:
            bool: 是否为严格模式
        """
        return self._config_manager.is_strict_mode()
    
    def create_client_from_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> Any:
        """从配置创建LLM客户端
        
        专注于客户端创建逻辑
        
        Args:
            config: LLM客户端配置
            
        Returns:
            LLM客户端实例
            
        Raises:
            LLMError: 客户端创建失败
        """
        try:
            # 验证配置
            validation_result = self.validate_client_config(config)
            if not validation_result.is_valid:
                raise LLMError(f"客户端配置验证失败: {validation_result.errors}")
            
            # 返回验证通过的客户端
            return validation_result.client
            
        except Exception as e:
            logger.error(f"创建LLM客户端失败: {e}")
            raise LLMError(f"创建LLM客户端失败: {e}") from e
    
    def create_clients_batch(self, configs: List[Union[Dict[str, Any], LLMClientConfig]]) -> Dict[str, Any]:
        """批量创建LLM客户端
        
        Args:
            configs: 客户端配置列表
            
        Returns:
            Dict[str, Any]: 客户端名称到客户端实例的映射
        """
        clients = {}
        errors = []
        
        for config in configs:
            try:
                client = self.create_client_from_config(config)
                client_name = self._get_config_name(config)
                if client_name and isinstance(client_name, str):
                    clients[client_name] = client
                    logger.debug(f"成功创建LLM客户端: {client_name}")
                
            except Exception as e:
                client_name = self._get_config_name(config)
                error_msg = f"创建LLM客户端 {client_name} 失败: {e}"
                errors.append(error_msg)
                logger.error(error_msg)
                
                # 严格模式下，遇到错误就停止
                if self.is_strict_mode():
                    raise LLMError(error_msg)
        
        if errors and not clients:
            raise LLMError(f"所有客户端创建失败: {'; '.join(errors)}")
        
        logger.info(f"批量创建了 {len(clients)} 个LLM客户端")
        return clients
    
    def reload_clients_config(self) -> None:
        """重新加载客户端配置
        
        委托给ConfigManager处理
        """
        self._config_manager.reload_config()
        logger.info("客户端配置已重新加载")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态
        
        委托给ConfigManager处理
        
        Returns:
            Dict[str, Any]: 配置状态信息
        """
        return self._config_manager.get_config_status()
    
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