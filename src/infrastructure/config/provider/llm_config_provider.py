"""LLM配置提供者

提供LLM模块的配置获取、缓存和管理功能。
"""

from typing import Dict, Any, Optional, List, Union, TYPE_CHECKING
import logging
import time
from threading import RLock
from datetime import datetime

from .base_provider import BaseConfigProvider
from ..impl.llm_config_impl import LLMConfigImpl
from ..impl.base_impl import IConfigImpl

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class LLMConfigProvider(BaseConfigProvider):
    """LLM配置提供者
    
    提供LLM模块的配置获取、缓存和管理功能。
    支持客户端配置、模块配置的获取和管理。
    """
    
    def __init__(self, config_impl: IConfigImpl):
        """初始化LLM配置提供者
        
        Args:
            config_impl: LLM配置实现
        """
        super().__init__("llm", config_impl)
        
        # 确保配置实现是LLMConfigImpl
        if not isinstance(config_impl, LLMConfigImpl):
            raise TypeError("config_impl必须是LLMConfigImpl实例")
        
        self._llm_impl: LLMConfigImpl = config_impl
        
        # 客户端配置缓存
        self._client_cache: Dict[str, Dict[str, Any]] = {}
        self._client_cache_timestamps: Dict[str, float] = {}
        self._client_cache_lock = RLock()
        
        # 模块配置缓存
        self._module_cache: Optional[Dict[str, Any]] = None
        self._module_cache_timestamp: Optional[float] = None
        self._module_cache_lock = RLock()
        
        logger.debug("LLM配置提供者初始化完成")
    
    def get_client_config(self, model_name: str) -> Optional[Dict[str, Any]]:
        """获取客户端配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            客户端配置，如果不存在则返回None
        """
        with self._client_cache_lock:
            # 检查缓存
            if model_name in self._client_cache:
                # 检查缓存是否有效
                if self._is_cache_valid_for_client(model_name):
                    logger.debug(f"从缓存获取客户端配置: {model_name}")
                    return self._client_cache[model_name].copy()
                else:
                    # 缓存过期，清除
                    del self._client_cache[model_name]
                    del self._client_cache_timestamps[model_name]
            
            # 从配置实现获取
            client_config = self._llm_impl.get_client_config(model_name)
            
            if client_config:
                # 缓存配置
                self._client_cache[model_name] = client_config.copy()
                self._client_cache_timestamps[model_name] = time.time()
                logger.debug(f"获取并缓存客户端配置: {model_name}")
            
            return client_config
    
    def get_module_config(self) -> Dict[str, Any]:
        """获取模块配置
        
        Returns:
            模块配置
        """
        with self._module_cache_lock:
            # 检查缓存
            if (self._module_cache is not None and 
                self._module_cache_timestamp is not None):
                logger.debug("从缓存获取模块配置")
                return self._module_cache.copy()
            
            # 从配置实现获取
            module_config = self._llm_impl.get_module_config()
            
            # 缓存配置
            self._module_cache = module_config.copy()
            self._module_cache_timestamp = time.time()
            logger.debug("获取并缓存模块配置")
            
            return module_config
    
    def get_config_value(self, model_name: str, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            model_name: 模型名称
            key: 配置键
            default: 默认值
            
        Returns:
            配置值
        """
        client_config = self.get_client_config(model_name)
        if client_config and key in client_config:
            return client_config[key]
        
        # 如果客户端配置中没有，尝试从模块配置获取
        module_config = self.get_module_config()
        if key in module_config:
            return module_config[key]
        
        return default
    
    def list_available_models(self) -> List[str]:
        """列出可用的模型
        
        Returns:
            可用模型列表
        """
        return self._llm_impl.list_available_models()
    
    def get_models_by_type(self, model_type: str) -> List[str]:
        """根据类型获取模型列表
        
        Args:
            model_type: 模型类型
            
        Returns:
            指定类型的模型列表
        """
        return self._llm_impl.get_models_by_type(model_type)
    
    def validate_client_config(self, model_name: str) -> bool:
        """验证客户端配置
        
        Args:
            model_name: 模型名称
            
        Returns:
            配置是否有效
        """
        return self._llm_impl.validate_client_config(model_name)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """获取配置摘要
        
        Returns:
            配置摘要信息
        """
        return self._llm_impl.get_config_summary()
    
    def clear_client_cache(self, model_name: Optional[str] = None):
        """清除客户端配置缓存
        
        Args:
            model_name: 模型名称，如果为None则清除所有客户端缓存
        """
        with self._client_cache_lock:
            if model_name:
                if model_name in self._client_cache:
                    del self._client_cache[model_name]
                    del self._client_cache_timestamps[model_name]
                    logger.debug(f"清除客户端配置缓存: {model_name}")
            else:
                self._client_cache.clear()
                self._client_cache_timestamps.clear()
                logger.debug("清除所有客户端配置缓存")
    
    def clear_module_cache(self):
        """清除模块配置缓存"""
        with self._module_cache_lock:
            self._module_cache = None
            self._module_cache_timestamp = None
            logger.debug("清除模块配置缓存")
    
    def clear_cache(self, config_name: Optional[str] = None):
        """清除缓存
        
        Args:
            config_name: 配置名称，如果为None则清除所有缓存
        """
        if config_name is None:
            self.clear_client_cache()
            self.clear_module_cache()
        else:
            # 尝试清除客户端缓存
            self.clear_client_cache(config_name)
            # 如果是模块配置，清除模块缓存
            if config_name == "module":
                self.clear_module_cache()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        with self._client_cache_lock, self._module_cache_lock:
            return {
                "client_cache_size": len(self._client_cache),
                "client_cache_keys": list(self._client_cache.keys()),
                "module_cache_cached": self._module_cache is not None,
                "module_cache_timestamp": self._module_cache_timestamp,
                "cache_ttl": self.cache_ttl,
                "cache_enabled": self.cache_enabled
            }
    
    def preload_common_configs(self):
        """预加载常用配置
        
        预加载默认模型和常用模型的配置到缓存中。
        """
        logger.debug("开始预加载常用配置")
        
        # 获取模块配置
        module_config = self.get_module_config()
        
        # 预加载默认模型配置
        default_model = module_config.get("default_model")
        if default_model:
            self.get_client_config(default_model)
        
        # 预加载前几个模型的配置
        models = self.list_available_models()
        for model in models[:5]:  # 预加载前5个模型
            self.get_client_config(model)
        
        logger.debug("常用配置预加载完成")
    
    def refresh_config(self, model_name: Optional[str] = None):
        """刷新配置
        
        Args:
            model_name: 模型名称，如果为None则刷新所有配置
        """
        logger.debug(f"刷新配置: {model_name or '全部'}")
        
        # 清除相关缓存
        self.clear_cache(model_name)
        
        # 重新加载配置
        if model_name:
            self.get_client_config(model_name)
        else:
            self.get_module_config()
            self.preload_common_configs()
        
        logger.debug("配置刷新完成")
    
    def get_provider_stats(self) -> Dict[str, Any]:
        """获取提供者统计信息
        
        Returns:
            提供者统计信息
        """
        # 获取基础缓存统计
        stats = self._get_cache_stats()
        
        # 添加LLM特定的统计信息
        llm_stats = {
            "total_models": len(self.list_available_models()),
            "model_types": {},
            "default_model": self.get_module_config().get("default_model"),
            "cache_stats": self.get_cache_stats()
        }
        
        # 统计模型类型
        for model_type in ["openai", "gemini", "anthropic", "mock", "human_relay"]:
            models = self.get_models_by_type(model_type)
            if models:
                llm_stats["model_types"][model_type] = len(models)
        
        stats.update({"llm_specific": llm_stats})
        return stats
    
    def _create_config_model(self, config_data: Dict[str, Any]) -> Any:
        """创建配置模型
        
        Args:
            config_data: 配置数据
            
        Returns:
            配置模型实例
        """
        # 对于LLM配置，直接返回配置数据
        # 在实际应用中，可以转换为Pydantic模型
        return config_data
    
    def _is_cache_valid_for_client(self, model_name: str) -> bool:
        """检查客户端缓存是否有效（内部使用的辅助方法）
        
        Args:
            model_name: 模型名称
            
        Returns:
            缓存是否有效
        """
        if not self.cache_enabled:
            return False
        
        if model_name not in self._client_cache_timestamps:
            return False
        
        age = time.time() - self._client_cache_timestamps[model_name]
        return age < self.cache_ttl