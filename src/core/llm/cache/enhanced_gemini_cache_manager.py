"""增强的Gemini缓存管理器，整合客户端和服务器端缓存"""

from typing import Any, Optional, List, Dict, Union, Sequence
from langchain_core.messages import BaseMessage

from .cache_manager import CacheManager
from .cache_config import CacheConfig
from .gemini_cache_manager import GeminiCacheManager
from .gemini_server_cache_manager import GeminiServerCacheManager


class EnhancedGeminiCacheManager(CacheManager):
    """增强的Gemini缓存管理器，支持客户端和服务器端缓存"""
    
    def __init__(self, config: CacheConfig, gemini_client: Optional[Any] = None):
        """
        初始化增强的Gemini缓存管理器
        
        Args:
            config: 缓存配置
            gemini_client: Gemini客户端实例（用于服务器端缓存）
        """
        super().__init__(config)
        
        # 客户端缓存管理器
        self._client_cache_manager = GeminiCacheManager(config)
        
        # 服务器端缓存管理器
        self._server_cache_manager: Optional[GeminiServerCacheManager] = None
        if gemini_client is not None:
            model_name = getattr(config, 'model_name', None)
            if not model_name:
                raise ValueError("服务器端缓存需要配置model_name")
            self._server_cache_manager = GeminiServerCacheManager(
                gemini_client, 
                model_name
            )
        
        # 缓存策略配置
        self._server_cache_enabled = getattr(config, 'server_cache_enabled', False)
        self._auto_server_cache = getattr(config, 'auto_server_cache', False)
        self._large_content_threshold = getattr(config, 'large_content_threshold', 1048576)  # 1MB
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存，优先从客户端缓存获取
        
        Args:
            key: 缓存键
            
        Returns:
            缓存的内容，如果不存在则返回None
        """
        # 先尝试客户端缓存
        result = self._client_cache_manager.get(key)
        if result is not None:
            return result
        
        # 如果客户端缓存没有，尝试服务器端缓存（需要特殊处理）
        # 注意：服务器端缓存的使用方式不同，这里只是占位
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        设置缓存，只存储到客户端缓存
        
        Args:
            key: 缓存键
            value: 缓存内容
            ttl: 生存时间（秒）
        """
        self._client_cache_manager.set(key, value, ttl)
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        return self._client_cache_manager.delete(key)
    
    def clear(self) -> None:
        """清除所有客户端缓存"""
        self._client_cache_manager.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        stats = {
            "client_cache": self._client_cache_manager.get_stats(),
            "server_cache_enabled": self._server_cache_enabled
        }
        
        if self._server_cache_manager:
            stats["server_cache"] = self._server_cache_manager.get_cache_stats()
        
        return stats
    
    def create_server_cache(
        self,
        contents: List[Any],
        system_instruction: Optional[str] = None,
        ttl: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        创建服务器端缓存
        
        Args:
            contents: 要缓存的内容列表
            system_instruction: 系统指令
            ttl: 生存时间（如"300s", "1h"）
            display_name: 缓存显示名称
            
        Returns:
            创建的缓存对象，如果失败则返回None
        """
        if not self._server_cache_manager or not self._server_cache_enabled:
            return None
        
        try:
            result = self._server_cache_manager.create_cache(
                contents, system_instruction, ttl, display_name
            )
            # 检查结果是否为None（在测试环境中可能表示失败）
            # 如果创建了模拟缓存对象但实际调用失败，也应返回None
            return result
        except Exception as e:
            # 记录错误但不抛出异常
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"创建服务器端缓存失败: {e}")
            return None
    
    def use_server_cache(self, cache_name: str, contents: Any) -> Optional[Any]:
        """
        使用服务器端缓存生成内容
        
        Args:
            cache_name: 缓存名称
            contents: 查询内容
            
        Returns:
            生成的内容响应，如果失败则返回None
        """
        if not self._server_cache_manager or not self._server_cache_enabled:
            return None
        
        try:
            return self._server_cache_manager.use_cache(cache_name, contents)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"使用服务器端缓存失败: {e}")
            return None
    
    def get_or_create_server_cache(
        self, 
        contents: List[Any], 
        system_instruction: Optional[str] = None,
        ttl: Optional[str] = None,
        display_name: Optional[str] = None
    ) -> Optional[Any]:
        """
        获取或创建服务器端缓存
        
        Args:
            contents: 要缓存的内容列表
            system_instruction: 系统指令
            ttl: 生存时间
            display_name: 缓存显示名称
            
        Returns:
            缓存对象，如果失败则返回None
        """
        if not self._server_cache_manager or not self._server_cache_enabled:
            return None
        
        try:
            return self._server_cache_manager.get_or_create_cache(
                contents, system_instruction, ttl, display_name
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"获取或创建服务器端缓存失败: {e}")
            return None
    
    def delete_server_cache(self, cache_name: str) -> bool:
        """
        删除服务器端缓存
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            是否删除成功
        """
        if not self._server_cache_manager:
            return False
        
        return self._server_cache_manager.delete_cache(cache_name)
    
    def list_server_caches(self) -> List[Any]:
        """
        列出所有服务器端缓存
        
        Returns:
            缓存对象列表
        """
        if not self._server_cache_manager:
            return []
        
        return self._server_cache_manager.list_caches()
    
    def cleanup_expired_server_caches(self) -> int:
        """
        清理过期的服务器端缓存
        
        Returns:
            清理的缓存数量
        """
        if not self._server_cache_manager:
            return 0
        
        return self._server_cache_manager.cleanup_expired_caches()
    
    def should_use_server_cache(self, contents: List[Any]) -> bool:
        """
        判断是否应该使用服务器端缓存
        
        Args:
            contents: 内容列表
            
        Returns:
            是否应该使用服务器端缓存
        """
        if not self._server_cache_manager or not self._server_cache_enabled:
            return False
        
        return self._server_cache_manager.should_use_server_cache(
            contents, self._large_content_threshold
        )
    
    def smart_cache_decision(
        self, 
        messages: Sequence[BaseMessage], 
        contents: Optional[List[Any]] = None,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        智能缓存决策
        
        Args:
            messages: 消息列表
            contents: 内容列表（用于服务器端缓存）
            system_instruction: 系统指令
            
        Returns:
            缓存决策结果
        """
        decision = {
            "use_client_cache": True,
            "use_server_cache": False,
            "server_cache_name": None,
            "reason": "default"
        }
        
        # 检查是否应该使用服务器端缓存
        if self._auto_server_cache and contents and self.should_use_server_cache(contents):
            decision["use_server_cache"] = True
            decision["reason"] = "large_content_detected"
            
            # 尝试获取或创建服务器端缓存
            cache = self.get_or_create_server_cache(
                contents, 
                system_instruction,
                ttl=getattr(self.config, 'server_cache_ttl', "3600s"),
                display_name=getattr(self.config, 'server_cache_display_name', None)
            )
            
            if cache:
                decision["server_cache_name"] = cache.name
            else:
                decision["use_server_cache"] = False
                decision["reason"] = "server_cache_creation_failed"
        
        return decision
    
    def get_client_cache_response(
        self, 
        messages: Sequence[BaseMessage], 
        model: str = "", 
        parameters: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """
        获取客户端缓存响应
        
        Args:
            messages: 消息列表
            model: 模型名称
            parameters: 生成参数
            
        Returns:
            缓存的响应，如果不存在则返回None
        """
        return self._client_cache_manager.get_gemini_response(messages, model, parameters)
    
    def set_client_cache_response(
        self, 
        messages: Sequence[BaseMessage], 
        response: Any, 
        model: str = "", 
        parameters: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> None:
        """
        设置客户端缓存响应
        
        Args:
            messages: 消息列表
            response: 响应内容
            model: 模型名称
            parameters: 生成参数
            ttl: 生存时间（秒）
        """
        self._client_cache_manager.set_gemini_response(
            messages, response, model, parameters, ttl
        )
    
    def get_cache_config(self) -> Dict[str, Any]:
        """
        获取缓存配置信息
        
        Returns:
            缓存配置信息
        """
        return {
            "client_cache_enabled": self.config.enabled,
            "server_cache_enabled": self._server_cache_enabled,
            "auto_server_cache": self._auto_server_cache,
            "large_content_threshold": self._large_content_threshold,
            "server_cache_ttl": getattr(self.config, 'server_cache_ttl', "3600s"),
            "server_cache_display_name": getattr(self.config, 'server_cache_display_name', None)
        }