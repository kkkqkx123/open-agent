"""LLM客户端配置服务

负责LLM客户端的配置加载、验证和管理。
"""

from typing import Any, Dict, List, Optional, Union
import logging

from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMClientConfig
from src.core.llm.exceptions import LLMError
from src.services.llm.config_validator import LLMConfigValidator, ValidationResult

logger = logging.getLogger(__name__)


class LLMClientConfigurationService:
    """LLM客户端配置服务
    
    负责：
    1. 从配置加载LLM客户端
    2. 验证客户端配置
    3. 管理配置相关的错误处理
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        config_validator: LLMConfigValidator,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化配置服务
        
        Args:
            factory: LLM工厂
            config_validator: 配置验证器
            config: LLM配置字典
        """
        self._factory = factory
        self._config_validator = config_validator
        self._config = config or {}
    
    def load_clients_from_config(self) -> Dict[str, Any]:
        """从配置加载LLM客户端
        
        Returns:
            Dict[str, Any]: 客户端名称到客户端实例的映射
            
        Raises:
            LLMError: 配置加载失败
        """
        clients = {}
        clients_config = self._config.get("clients", [])
        
        if not clients_config:
            logger.info("配置中没有指定LLM客户端")
            return clients
        
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
                
                # 获取验证通过的客户端
                client = validation_result.client
                if client:
                    client_name = self._get_config_name(client_config)
                    if isinstance(client_name, str):
                        clients[client_name] = client
                        logger.debug(f"成功加载LLM客户端: {client_name}")
                    
            except Exception as e:
                client_name = self._get_config_name(client_config)
                logger.error(f"加载LLM客户端 {client_name} 失败: {e}")
                strict_mode = self._config.get("strict_mode", False)
                if strict_mode:
                    raise
                else:
                    # 非严格模式下，跳过失败的客户端
                    continue
        
        logger.info(f"从配置加载了 {len(clients)} 个LLM客户端")
        return clients
    
    def validate_client_config(self, config: Union[Dict[str, Any], LLMClientConfig]) -> ValidationResult:
        """验证客户端配置
        
        Args:
            config: LLM客户端配置（字典或LLMClientConfig对象）
            
        Returns:
            ValidationResult: 验证结果
        """
        try:
            # 使用配置验证器验证配置
            result = self._config_validator.validate_config(config)
            return result
            
        except Exception as e:
            logger.error(f"LLM客户端配置验证失败: {e}")
            return ValidationResult.failure([f"配置验证失败: {str(e)}"])
    
    def get_default_client_name(self) -> Optional[str]:
        """获取默认客户端名称
        
        Returns:
            Optional[str]: 默认客户端名称，如果未配置则返回None
        """
        return self._config.get("default_client")
    
    def is_strict_mode(self) -> bool:
        """检查是否为严格模式
        
        Returns:
            bool: 是否为严格模式
        """
        return self._config.get("strict_mode", False)
    
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