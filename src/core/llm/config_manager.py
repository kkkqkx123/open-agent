"""增强的LLM配置管理器

使用混合架构，复用通用配置系统，保留LLM特定功能。
"""

from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from threading import Lock

from src.services.logger import get_logger
from src.core.common.exceptions.config import ConfigError, ConfigNotFoundError
from src.core.config.config_loader import IConfigLoader, ConfigLoader
from src.core.config.config_manager import ConfigManager
from src.core.llm.config_validator_adapter import LLMConfigValidatorAdapter
from src.core.llm.config_merger_adapter import LLMConfigMergerAdapter
from src.core.llm.provider_config_discovery import ProviderConfigDiscovery

logger = get_logger(__name__)


class LLMConfigManager:
    """增强的LLM配置管理器
    
    使用混合架构：
    - 复用通用配置加载器进行文件I/O
    - 使用LLM特定适配器进行验证和合并
    - 保留LLM特定的发现和管理逻辑
    """
    
    def __init__(self, 
                 config_loader: Optional[IConfigLoader] = None,
                 base_path: str = "configs/llms",
                 enable_provider_configs: bool = True):
        """初始化增强的LLM配置管理器
        
        Args:
            config_loader: 通用配置加载器
            base_path: LLM配置基础路径
            enable_provider_configs: 是否启用Provider配置
        """
        self.base_path = Path(base_path)
        
        # 初始化通用配置加载器
        self.config_loader = config_loader or ConfigLoader(self.base_path)
        
        # 初始化通用配置管理器
        self.config_manager = ConfigManager(
            base_path=self.base_path,
            use_cache=True,
            auto_reload=False
        )
        
        # 初始化LLM特定适配器
        self.validator_adapter = LLMConfigValidatorAdapter()
        self.merger_adapter = LLMConfigMergerAdapter()
        
        # Provider配置发现器
        self.provider_discovery: Optional[ProviderConfigDiscovery] = None
        if enable_provider_configs:
            self.provider_discovery = ProviderConfigDiscovery(
                self.config_loader, 
                str(self.base_path)
            )
        
        # 配置缓存
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        
        logger.info(f"增强LLM配置管理器初始化完成，基础路径: {self.base_path}")
    
    def load_llm_config(self, config_path: str, validate: bool = True) -> Dict[str, Any]:
        """加载LLM配置
        
        Args:
            config_path: 配置文件路径
            validate: 是否验证配置
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        with self._lock:
            # 检查缓存
            cache_key = f"llm:{config_path}"
            if cache_key in self._config_cache:
                logger.debug(f"从缓存加载LLM配置: {config_path}")
                return self._config_cache[cache_key]
            
            try:
                # 使用通用配置管理器加载配置
                config = self.config_manager.load_config(config_path, module_type="llm")
                
                # 使用LLM验证器适配器验证
                if validate:
                    validation_result = self.validator_adapter.validate_llm_config(config)
                    if not validation_result.is_valid:
                        error_msg = f"LLM配置验证失败 {config_path}: " + "; ".join(validation_result.errors)
                        logger.error(error_msg)
                        raise ConfigError(error_msg)
                    
                    # 记录警告和信息
                    for warning in validation_result.warnings:
                        logger.warning(f"LLM配置警告 {config_path}: {warning}")
                    for info in validation_result.info:
                        logger.info(f"LLM配置信息 {config_path}: {info}")
                
                # 缓存配置
                self._config_cache[cache_key] = config
                
                logger.info(f"LLM配置加载成功: {config_path}")
                return config
                
            except Exception as e:
                logger.error(f"加载LLM配置失败 {config_path}: {e}")
                raise
    
    def load_provider_config(self, provider_name: str, model_name: str, 
                           validate: bool = True) -> Dict[str, Any]:
        """加载Provider配置
        
        Args:
            provider_name: Provider名称
            model_name: 模型名称
            validate: 是否验证配置
            
        Returns:
            Dict[str, Any]: 配置数据
        """
        if not self.provider_discovery:
            raise ConfigError("Provider配置发现器未启用")
        
        with self._lock:
            cache_key = f"provider:{provider_name}:{model_name}"
            if cache_key in self._config_cache:
                logger.debug(f"从缓存加载Provider配置: {provider_name}/{model_name}")
                return self._config_cache[cache_key]
            
            try:
                # 使用Provider配置发现器加载配置
                config = self.provider_discovery.get_provider_config(provider_name, model_name)
                
                if not config:
                    raise ConfigNotFoundError(f"未找到Provider配置: {provider_name}/{model_name}")
                
                # 使用LLM验证器适配器验证
                if validate:
                    validation_result = self.validator_adapter.validate_provider_config(config)
                    if not validation_result.is_valid:
                        error_msg = f"Provider配置验证失败 {provider_name}/{model_name}: " + "; ".join(validation_result.errors)
                        logger.error(error_msg)
                        raise ConfigError(error_msg)
                
                # 缓存配置
                self._config_cache[cache_key] = config
                
                logger.info(f"Provider配置加载成功: {provider_name}/{model_name}")
                return config
                
            except Exception as e:
                logger.error(f"加载Provider配置失败 {provider_name}/{model_name}: {e}")
                raise
    
    def merge_llm_configs(self, config_paths: List[str], 
                         validate: bool = True) -> Dict[str, Any]:
        """合并多个LLM配置
        
        Args:
            config_paths: 配置文件路径列表
            validate: 是否验证合并后的配置
            
        Returns:
            Dict[str, Any]: 合并后的配置
        """
        try:
            # 加载所有配置
            configs = []
            for config_path in config_paths:
                config = self.load_llm_config(config_path, validate=False)
                configs.append(config)
            
            # 使用LLM合并适配器合并配置
            merged_config = self.merger_adapter.merge_llm_configs(configs)
            
            # 验证合并后的配置
            if validate:
                validation_result = self.validator_adapter.validate_llm_config(merged_config)
                if not validation_result.is_valid:
                    error_msg = f"合并配置验证失败: " + "; ".join(validation_result.errors)
                    logger.error(error_msg)
                    raise ConfigError(error_msg)
            
            logger.info(f"LLM配置合并成功: {len(config_paths)} 个配置")
            return merged_config
            
        except Exception as e:
            logger.error(f"合并LLM配置失败: {e}")
            raise
    
    def discover_providers(self) -> Dict[str, Any]:
        """发现所有可用的Provider
        
        Returns:
            Dict[str, Any]: Provider信息
        """
        if not self.provider_discovery:
            return {}
        
        return self.provider_discovery.discover_providers()
    
    def list_provider_models(self, provider_name: str) -> List[str]:
        """列出Provider的所有模型
        
        Args:
            provider_name: Provider名称
            
        Returns:
            List[str]: 模型名称列表
        """
        if not self.provider_discovery:
            return []
        
        return self.provider_discovery.list_provider_models(provider_name)
    
    def validate_config(self, config: Dict[str, Any], 
                       config_type: str = "llm") -> bool:
        """验证配置
        
        Args:
            config: 配置数据
            config_type: 配置类型 ("llm" 或 "provider")
            
        Returns:
            bool: 是否有效
        """
        try:
            if config_type == "llm":
                result = self.validator_adapter.validate_llm_config(config)
            elif config_type == "provider":
                result = self.validator_adapter.validate_provider_config(config)
            else:
                logger.error(f"不支持的配置类型: {config_type}")
                return False
            
            return result.is_valid
            
        except Exception as e:
            logger.error(f"配置验证失败: {e}")
            return False
    
    def reload_config(self, config_path: str) -> Dict[str, Any]:
        """重新加载配置
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            Dict[str, Any]: 重新加载的配置
        """
        with self._lock:
            # 清除缓存
            keys_to_remove = [key for key in self._config_cache.keys() 
                           if config_path in key]
            for key in keys_to_remove:
                del self._config_cache[key]
            
            # 清除通用配置管理器缓存
            self.config_manager.invalidate_cache(config_path)
            
            # 重新加载
            return self.load_llm_config(config_path)
    
    def clear_cache(self) -> None:
        """清除所有缓存"""
        with self._lock:
            self._config_cache.clear()
            self.config_manager.invalidate_cache()
            logger.debug("已清除所有配置缓存")
    
    def get_config_status(self) -> Dict[str, Any]:
        """获取配置管理器状态
        
        Returns:
            Dict[str, Any]: 状态信息
        """
        status = {
            "base_path": str(self.base_path),
            "config_loader_type": type(self.config_loader).__name__,
            "cache_size": len(self._config_cache),
            "cached_configs": list(self._config_cache.keys()),
            "validator_rules": self.validator_adapter.get_llm_rules_summary(),
            "merger_rules": self.merger_adapter.get_merge_rules_summary()
        }
        
        if self.provider_discovery:
            status["provider_discovery"] = self.provider_discovery.get_discovery_status()
        
        return status
    
    def register_custom_validator(self, field_path: str, 
                                validator: Callable,
                                error_message: str,
                                severity: str = "error") -> None:
        """注册自定义验证规则
        
        Args:
            field_path: 字段路径
            validator: 验证函数
            error_message: 错误消息
            severity: 严重程度
        """
        from src.core.config.validation import ValidationSeverity
        from src.core.llm.config_validator_adapter import LLMValidationRule
        
        severity_enum = ValidationSeverity(severity.lower())
        
        rule = LLMValidationRule(
            field_path=field_path,
            validator=validator,
            error_message=error_message,
            severity=severity_enum,
            description=f"自定义验证规则: {field_path}"
        )
        
        self.validator_adapter.add_llm_rule(rule)
        logger.info(f"已注册自定义验证规则: {field_path}")
    
    def register_custom_merge_rule(self, field_path: str, 
                                 merge_strategy: str,
                                 priority: int = 50) -> None:
        """注册自定义合并规则
        
        Args:
            field_path: 字段路径
            merge_strategy: 合并策略
            priority: 优先级
        """
        from src.core.llm.config_merger_adapter import LLMMergeRule
        
        rule = LLMMergeRule(
            field_path=field_path,
            merge_strategy=merge_strategy,
            priority=priority,
            description=f"自定义合并规则: {field_path}"
        )
        
        self.merger_adapter.add_merge_rule(rule)
        logger.info(f"已注册自定义合并规则: {field_path}")