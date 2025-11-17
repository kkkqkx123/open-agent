"""LLM配置管理器

整合所有配置相关的功能，包括配置加载、验证和管理。
"""

from typing import Any, Dict, List, Optional, Union
import logging
from pathlib import Path

from src.core.llm.factory import LLMFactory
from src.core.llm.config import LLMClientConfig
from src.core.llm.exceptions import LLMError
from .config_validator import LLMConfigValidator, ValidationResult

logger = logging.getLogger(__name__)


class ConfigManager:
    """LLM配置管理器
    
    负责：
    1. 统一的配置加载和管理
    2. 配置验证
    3. 配置缓存和性能优化
    4. 多种配置源的支持
    """
    
    def __init__(
        self,
        factory: LLMFactory,
        config_validator: LLMConfigValidator,
        config_loader: Optional[Any] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> None:
        """初始化配置管理器
        
        Args:
            factory: LLM工厂
            config_validator: 配置验证器
            config_loader: 配置加载器
            config: LLM配置字典
        """
        self._factory = factory
        self._config_validator = config_validator
        self._config_loader = config_loader
        self._config = config or {}
        
        # 配置缓存
        self._config_cache: Dict[str, Any] = {}
        self._validation_cache: Dict[str, ValidationResult] = {}
        
        # 配置基础路径
        self._config_base_path = "llms"
    
    def get_config(self, config_type: str, use_cache: bool = True) -> Dict[str, Any]:
        """获取指定类型的配置
        
        Args:
            config_type: 配置类型（如 "task_groups", "polling_pools", "clients"）
            use_cache: 是否使用缓存
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        if use_cache and config_type in self._config_cache:
            return self._config_cache[config_type]
        
        config = self._load_config_by_type(config_type)
        
        if use_cache:
            self._config_cache[config_type] = config
        
        return config
    
    def validate_config(self, config_type: str, config: Union[Dict[str, Any], LLMClientConfig]) -> ValidationResult:
        """验证指定类型的配置
        
        Args:
            config_type: 配置类型
            config: 配置对象
            
        Returns:
            ValidationResult: 验证结果
        """
        cache_key = f"{config_type}_{hash(str(config))}"
        
        if cache_key in self._validation_cache:
            return self._validation_cache[cache_key]
        
        result = self._config_validator.validate_config(config)
        
        self._validation_cache[cache_key] = result
        return result
    
    def load_clients_from_config(self) -> Dict[str, Any]:
        """从配置加载LLM客户端
        
        Returns:
            Dict[str, Any]: 客户端名称到客户端实例的映射
            
        Raises:
            LLMError: 配置加载失败
        """
        clients = {}
        clients_config = self.get_config("clients")
        
        if not clients_config:
            logger.info("配置中没有指定LLM客户端")
            return clients
        
        for client_config in clients_config:
            try:
                # 使用配置验证器验证配置
                validation_result = self.validate_config("client", client_config)
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
    
    def get_task_groups(self) -> Dict[str, Any]:
        """获取任务组配置
        
        Returns:
            Dict[str, Any]: 任务组配置字典
        """
        return self.get_config("task_groups")
    
    def get_polling_pools(self) -> Dict[str, Any]:
        """获取轮询池配置
        
        Returns:
            Dict[str, Any]: 轮询池配置字典
        """
        return self.get_config("polling_pools")
    
    def get_global_fallback(self) -> Dict[str, Any]:
        """获取全局降级配置
        
        Returns:
            Dict[str, Any]: 全局降级配置字典
        """
        return self.get_config("global_fallback")
    
    def get_concurrency_control(self) -> Dict[str, Any]:
        """获取并发控制配置
        
        Returns:
            Dict[str, Any]: 并发控制配置字典
        """
        return self.get_config("concurrency_control")
    
    def get_rate_limiting(self) -> Dict[str, Any]:
        """获取速率限制配置
        
        Returns:
            Dict[str, Any]: 速率限制配置字典
        """
        return self.get_config("rate_limiting")
    
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
    
    def reload_config(self) -> None:
        """重新加载配置，清除缓存"""
        self._config_cache.clear()
        self._validation_cache.clear()
        logger.info("配置缓存已清除，将重新加载")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态
        
        Returns:
            Dict[str, Any]: 配置状态信息
        """
        return {
            "config_loaded": True,
            "cache_size": len(self._config_cache),
            "validation_cache_size": len(self._validation_cache),
            "task_groups_count": len(self.get_task_groups()),
            "polling_pools_count": len(self.get_polling_pools()),
            "task_groups": list(self.get_task_groups().keys()),
            "polling_pools": list(self.get_polling_pools().keys()),
            "global_fallback_enabled": bool(self.get_global_fallback()),
            "concurrency_control_enabled": bool(self.get_concurrency_control()),
            "rate_limiting_enabled": bool(self.get_rate_limiting())
        }
    
    def _load_config_by_type(self, config_type: str) -> Dict[str, Any]:
        """根据类型加载配置
        
        Args:
            config_type: 配置类型
            
        Returns:
            Dict[str, Any]: 配置字典
        """
        if config_type == "clients":
            return self._config.get("clients", [])
        elif config_type == "task_groups":
            return self._load_task_groups()
        elif config_type == "polling_pools":
            return self._load_polling_pools()
        elif config_type == "global_fallback":
            return self._load_global_fallback()
        elif config_type == "concurrency_control":
            return self._load_concurrency_control()
        elif config_type == "rate_limiting":
            return self._load_rate_limiting()
        else:
            logger.warning(f"未知的配置类型: {config_type}")
            return {}
    
    def _load_task_groups(self) -> Dict[str, Any]:
        """加载任务组配置"""
        if not self._config_loader:
            logger.warning("配置加载器未初始化，返回空的任务组配置")
            return {}
        
        task_groups = {}
        
        try:
            # 首先加载注册表配置
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self._config_loader.load(registry_path)
            
            # 从注册表获取任务组配置文件列表
            task_groups_registry = registry_config.get("task_groups", {})
            
            # 加载每个启用的任务组配置
            for group_name, group_info in task_groups_registry.items():
                if not group_info.get("enabled", True):
                    logger.debug(f"任务组 {group_name} 已禁用，跳过加载")
                    continue
                
                group_file = group_info.get("file")
                if not group_file:
                    logger.warning(f"任务组 {group_name} 缺少文件路径配置")
                    continue
                
                try:
                    config_path = f"{self._config_base_path}/{group_file}"
                    group_config = self._config_loader.load(config_path)
                    
                    # 验证配置中的名称是否与注册表中的名称一致
                    config_name = group_config.get("name")
                    if config_name and config_name != group_name:
                        logger.warning(f"任务组配置文件中的名称 '{config_name}' 与注册表中的名称 '{group_name}' 不匹配")
                    
                    task_groups[group_name] = group_config
                    logger.debug(f"成功加载任务组配置: {group_name}")
                    
                except Exception as e:
                    logger.warning(f"加载任务组配置失败 {group_name} ({group_file}): {e}")
                    
        except Exception as e:
            logger.error(f"加载任务组注册表失败: {e}")
            # 如果注册表加载失败，使用默认的任务组列表作为后备
            return self._load_default_task_groups()
        
        return task_groups
    
    def _load_default_task_groups(self) -> Dict[str, Any]:
        """加载默认任务组配置（后备方案）"""
        logger.info("使用默认任务组配置")
        return {}
    
    def _load_polling_pools(self) -> Dict[str, Any]:
        """加载轮询池配置"""
        if not self._config_loader:
            logger.warning("配置加载器未初始化，返回空的轮询池配置")
            return {}
        
        polling_pools = {}
        
        try:
            # 首先加载注册表配置
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self._config_loader.load(registry_path)
            
            # 从注册表获取轮询池配置文件列表
            polling_pools_registry = registry_config.get("polling_pools", {})
            
            # 加载每个启用的轮询池配置
            for pool_name, pool_info in polling_pools_registry.items():
                if not pool_info.get("enabled", True):
                    logger.debug(f"轮询池 {pool_name} 已禁用，跳过加载")
                    continue
                
                pool_file = pool_info.get("file")
                if not pool_file:
                    logger.warning(f"轮询池 {pool_name} 缺少文件路径配置")
                    continue
                
                try:
                    config_path = f"{self._config_base_path}/{pool_file}"
                    pool_config = self._config_loader.load(config_path)
                    
                    # 验证配置中的名称是否与注册表中的名称一致
                    config_name = pool_config.get("name")
                    if config_name and config_name != pool_name:
                        logger.warning(f"轮询池配置文件中的名称 '{config_name}' 与注册表中的名称 '{pool_name}' 不匹配")
                    
                    polling_pools[pool_name] = pool_config
                    logger.debug(f"成功加载轮询池配置: {pool_name}")
                    
                except Exception as e:
                    logger.warning(f"加载轮询池配置失败 {pool_name} ({pool_file}): {e}")
                    
        except Exception as e:
            logger.error(f"加载轮询池注册表失败: {e}")
            # 如果注册表加载失败，使用默认的轮询池列表作为后备
            return self._load_default_polling_pools()
        
        return polling_pools
    
    def _load_default_polling_pools(self) -> Dict[str, Any]:
        """加载默认轮询池配置（后备方案）"""
        logger.info("使用默认轮询池配置")
        return {}
    
    def _load_global_fallback(self) -> Dict[str, Any]:
        """加载全局降级配置"""
        if not self._config_loader:
            return self._config.get("global_fallback", {})
        
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self._config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            global_fallback_info = global_configs.get("global_fallback", {})
            
            if not global_fallback_info.get("enabled", True):
                logger.debug("全局降级配置已禁用")
                return {}
            
            fallback_file = global_fallback_info.get("file")
            if fallback_file:
                config_path = f"{self._config_base_path}/{fallback_file}"
                config = self._config_loader.load(config_path)
                logger.debug("从注册表成功加载全局降级配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载全局降级配置失败: {e}")
        
        # 如果注册表加载失败，直接返回配置中的全局降级配置
        return self._config.get("global_fallback", {})
    
    def _load_concurrency_control(self) -> Dict[str, Any]:
        """加载并发控制配置"""
        if not self._config_loader:
            return self._config.get("concurrency_control", {})
        
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self._config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            concurrency_control_info = global_configs.get("concurrency_control", {})
            
            if not concurrency_control_info.get("enabled", True):
                logger.debug("并发控制配置已禁用")
                return {}
            
            concurrency_file = concurrency_control_info.get("file")
            if concurrency_file:
                config_path = f"{self._config_base_path}/{concurrency_file}"
                config = self._config_loader.load(config_path)
                logger.debug("从注册表成功加载并发控制配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载并发控制配置失败: {e}")
        
        # 如果注册表加载失败，直接返回配置中的并发控制配置
        return self._config.get("concurrency_control", {})
    
    def _load_rate_limiting(self) -> Dict[str, Any]:
        """加载速率限制配置"""
        if not self._config_loader:
            return self._config.get("rate_limiting", {})
        
        try:
            registry_path = f"{self._config_base_path}/groups/_task_groups.yaml"
            registry_config = self._config_loader.load(registry_path)
            
            # 从注册表获取全局配置文件列表
            global_configs = registry_config.get("global_configs", {})
            rate_limiting_info = global_configs.get("rate_limiting", {})
            
            if not rate_limiting_info.get("enabled", True):
                logger.debug("速率限制配置已禁用")
                return {}
            
            rate_limiting_file = rate_limiting_info.get("file")
            if rate_limiting_file:
                config_path = f"{self._config_base_path}/{rate_limiting_file}"
                config = self._config_loader.load(config_path)
                logger.debug("从注册表成功加载速率限制配置")
                return config
                
        except Exception as e:
            logger.warning(f"从注册表加载速率限制配置失败: {e}")
        
        # 如果注册表加载失败，直接返回配置中的速率限制配置
        return self._config.get("rate_limiting", {})
    
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