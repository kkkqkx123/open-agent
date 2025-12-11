"""LLM配置实现

提供LLM模块的配置加载、转换和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
from pathlib import Path
import logging

from .base_impl import BaseConfigImpl
from .base_impl import IConfigSchema, IConfigProcessorChain

if TYPE_CHECKING:
    from src.interfaces.config import IConfigLoader
from ..processor.validation_processor import ValidationProcessor
from ..processor.transformation_processor import TransformationProcessor
from ..processor.environment_processor import EnvironmentProcessor
from ..processor.inheritance_processor import InheritanceProcessor
from ..processor.reference_processor import ReferenceProcessor

logger = logging.getLogger(__name__)


class LLMConfigImpl(BaseConfigImpl):
    """LLM配置实现类
    
    负责LLM模块的配置加载、转换和管理。
    支持多种LLM提供商的配置：OpenAI、Gemini、Anthropic、Mock等。
    """
    
    def __init__(self, 
                 config_loader: 'IConfigLoader',
                 processor_chain: IConfigProcessorChain,
                 schema: IConfigSchema):
        """初始化LLM配置实现
        
        Args:
            config_loader: 配置加载器
            processor_chain: 处理器链
            schema: 配置模式
        """
        super().__init__("llm", config_loader, processor_chain, schema)
        
        # LLM特定的配置映射
        self._model_type_mapping = {
            "openai": "openai",
            "gpt": "openai",
            "chatgpt": "openai",
            "gemini": "gemini",
            "anthropic": "anthropic",
            "claude": "anthropic",
            "mock": "mock",
            "human_relay": "human_relay",
            "human-relay": "human_relay",
            "human-relay-s": "human_relay",
            "human-relay-m": "human_relay"
        }
        
        # 支持的模型类型
        self._supported_model_types = {
            "openai", "gemini", "anthropic", "mock", "human_relay"
        }
        
        logger.debug("LLM配置实现初始化完成")
    
    def transform_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """转换LLM配置
        
        将原始配置转换为标准化的LLM配置格式。
        
        Args:
            config: 原始配置数据
            
        Returns:
            转换后的配置数据
        """
        logger.debug("开始转换LLM配置")
        
        # 1. 标准化模型类型
        config = self._normalize_model_type(config)
        
        # 2. 处理客户端配置
        config = self._process_client_configs(config)
        
        # 3. 处理模块配置
        config = self._process_module_config(config)
        
        # 4. 设置默认值
        config = self._set_default_values(config)
        
        # 5. 验证配置完整性
        config = self._validate_config_structure(config)
        
        logger.debug("LLM配置转换完成")
        return config
    
    def _normalize_model_type(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """标准化模型类型
        
        Args:
            config: 配置数据
            
        Returns:
            标准化后的配置数据
        """
        # 处理客户端配置中的模型类型
        if "clients" in config:
            for client_name, client_config in config["clients"].items():
                if "model_type" in client_config:
                    model_type = client_config["model_type"].lower()
                    normalized_type = self._model_type_mapping.get(model_type, model_type)
                    client_config["model_type"] = normalized_type
                    
                    # 验证模型类型是否支持
                    if normalized_type not in self._supported_model_types:
                        logger.warning(f"不支持的模型类型: {normalized_type}")
        
        return config
    
    def _process_client_configs(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理客户端配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "clients" not in config:
            config["clients"] = {}
        
        # 确保每个客户端配置都有必要的字段
        for client_name, client_config in config["clients"].items():
            # 设置默认值
            client_config.setdefault("timeout", 30)
            client_config.setdefault("max_retries", 3)
            client_config.setdefault("temperature", 0.7)
            client_config.setdefault("top_p", 1.0)
            client_config.setdefault("stream", False)
            client_config.setdefault("fallback_enabled", True)
            client_config.setdefault("fallback_models", [])
            client_config.setdefault("max_fallback_attempts", 3)
            
            # 处理连接池配置
            if "connection_pool_config" not in client_config:
                client_config["connection_pool_config"] = {
                    "max_connections": 10,
                    "max_keepalive": 10,
                    "connection_timeout": 30.0,
                    "read_timeout": 30.0,
                    "write_timeout": 30.0,
                    "connect_retries": 3,
                    "pool_timeout": 30.0
                }
            
            # 处理元数据配置
            if "metadata_config" not in client_config:
                client_config["metadata_config"] = {}
        
        return config
    
    def _process_module_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """处理模块配置
        
        Args:
            config: 配置数据
            
        Returns:
            处理后的配置数据
        """
        if "module" not in config:
            config["module"] = {}
        
        module_config = config["module"]
        
        # 设置默认值
        module_config.setdefault("default_model", "openai-gpt4")
        module_config.setdefault("default_timeout", 30)
        module_config.setdefault("default_max_retries", 3)
        module_config.setdefault("cache_enabled", True)
        module_config.setdefault("cache_ttl", 3600)
        module_config.setdefault("cache_max_size", 100)
        module_config.setdefault("hooks_enabled", True)
        module_config.setdefault("log_requests", True)
        module_config.setdefault("log_responses", True)
        module_config.setdefault("log_errors", True)
        module_config.setdefault("fallback_enabled", True)
        module_config.setdefault("global_fallback_models", [])
        module_config.setdefault("max_concurrent_requests", 10)
        module_config.setdefault("request_queue_size", 100)
        module_config.setdefault("metrics_enabled", True)
        module_config.setdefault("performance_tracking", True)
        module_config.setdefault("connection_pool_enabled", True)
        module_config.setdefault("default_max_connections", 10)
        module_config.setdefault("default_max_keepalive", 10)
        module_config.setdefault("default_connection_timeout", 30.0)
        
        return config
    
    def _set_default_values(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """设置默认值
        
        Args:
            config: 配置数据
            
        Returns:
            设置默认值后的配置数据
        """
        # 全局默认值
        config.setdefault("version", "1.0")
        config.setdefault("description", "LLM模块配置")
        
        return config
    
    def _validate_config_structure(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置结构
        
        Args:
            config: 配置数据
            
        Returns:
            验证后的配置数据
        """
        # 验证必要的顶级字段
        required_fields = ["clients"]
        for field in required_fields:
            if field not in config:
                raise ValueError(f"缺少必要的配置字段: {field}")
        
        # 验证客户端配置
        if not config["clients"]:
            raise ValueError("至少需要配置一个客户端")
        
        for client_name, client_config in config["clients"].items():
            # 验证客户端必要字段
            required_client_fields = ["model_type", "model_name"]
            for field in required_client_fields:
                if field not in client_config:
                    raise ValueError(f"客户端 {client_name} 缺少必要字段: {field}")
        
        return config
    
    def get_client_config(self, model_name: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """获取客户端配置
        
        Args:
            model_name: 模型名称
            use_cache: 是否使用缓存
            
        Returns:
            客户端配置，如果不存在则返回None
        """
        # 检查缓存
        cache_key = f"client_config:{model_name}"
        if use_cache:
            cached_config = self.cache_manager.get(cache_key)
            if cached_config is not None:
                logger.debug(f"从缓存获取客户端配置: {model_name}")
                return cached_config
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        
        # 查找匹配的客户端配置
        client_config = None
        for client_name, config_data in config.get("clients", {}).items():
            if config_data.get("model_name") == model_name:
                client_config = config_data.copy()
                break
        
        # 如果没有找到，尝试使用默认模型
        if client_config is None:
            default_model = config.get("module", {}).get("default_model")
            if default_model and default_model == model_name:
                # 返回第一个可用的配置
                clients = config.get("clients", {})
                if clients:
                    client_config = list(clients.values())[0].copy()
        
        # 缓存结果
        if client_config and use_cache:
            self.cache_manager.set(cache_key, client_config)
        
        return client_config
    
    def get_module_config(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取模块配置
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            模块配置
        """
        # 检查缓存
        cache_key = "module_config"
        if use_cache:
            cached_config = self.cache_manager.get(cache_key)
            if cached_config is not None:
                logger.debug("从缓存获取模块配置")
                return cached_config
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        module_config = config.get("module", {}).copy()
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, module_config)
        
        return module_config
    
    def list_available_models(self, use_cache: bool = True) -> List[str]:
        """列出可用的模型
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            可用模型列表
        """
        # 检查缓存
        cache_key = "available_models"
        if use_cache:
            cached_models = self.cache_manager.get(cache_key)
            if cached_models is not None:
                logger.debug("从缓存获取可用模型列表")
                return cached_models
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        models = []
        
        for client_config in config.get("clients", {}).values():
            model_name = client_config.get("model_name")
            if model_name:
                models.append(model_name)
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, models)
        
        return models
    
    def get_models_by_type(self, model_type: str) -> List[str]:
        """根据类型获取模型列表
        
        Args:
            model_type: 模型类型
            
        Returns:
            指定类型的模型列表
        """
        config = self.get_config()
        models = []
        
        for client_config in config.get("clients", {}).values():
            if client_config.get("model_type") == model_type:
                model_name = client_config.get("model_name")
                if model_name:
                    models.append(model_name)
        
        return models
    
    def validate_client_config(self, model_name: str) -> bool:
        """验证客户端配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            配置是否有效
        """
        client_config = self.get_client_config(model_name)
        if not client_config:
            return False
        
        # 验证必要字段
        required_fields = ["model_type", "model_name"]
        for field in required_fields:
            if field not in client_config:
                return False
        
        # 验证模型类型
        model_type = client_config["model_type"]
        if model_type not in self._supported_model_types:
            return False
        
        return True
    
    def get_config_summary(self, use_cache: bool = True) -> Dict[str, Any]:
        """获取配置摘要
        
        Args:
            use_cache: 是否使用缓存
            
        Returns:
            配置摘要信息
        """
        # 检查缓存
        cache_key = "config_summary"
        if use_cache:
            cached_summary = self.cache_manager.get(cache_key)
            if cached_summary is not None:
                logger.debug("从缓存获取配置摘要")
                return cached_summary
        
        # 从主配置获取
        config = self.get_config(use_cache=False)
        
        summary = {
            "version": config.get("version", "unknown"),
            "total_clients": len(config.get("clients", {})),
            "model_types": {},
            "default_model": config.get("module", {}).get("default_model"),
            "cache_enabled": config.get("module", {}).get("cache_enabled", False),
            "fallback_enabled": config.get("module", {}).get("fallback_enabled", False)
        }
        
        # 统计模型类型
        for client_config in config.get("clients", {}).values():
            model_type = client_config.get("model_type", "unknown")
            summary["model_types"][model_type] = summary["model_types"].get(model_type, 0) + 1
        
        # 缓存结果
        if use_cache:
            self.cache_manager.set(cache_key, summary)
        
        return summary
    
    def invalidate_cache(self, cache_key: Optional[str] = None) -> None:
        """清除缓存
        
        Args:
            cache_key: 缓存键，如果为None则清除所有相关缓存
        """
        if cache_key:
            self.cache_manager.delete(cache_key)
        else:
            # 清除LLM相关的所有缓存
            cache_keys = [
                "module_config",
                "available_models",
                "config_summary"
            ]
            
            # 清除客户端配置缓存
            models = self.list_available_models(use_cache=False)
            for model in models:
                cache_keys.append(f"client_config:{model}")
            
            for key in cache_keys:
                self.cache_manager.delete(key)
            
            logger.debug("清除LLM模块所有缓存")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return self.cache_manager.get_stats()