"""提示词缓存管理器

提供多级提示词缓存功能，复用核心CacheManager实现。
支持状态级、线程级和会话级缓存。
"""

import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from ...core.state import WorkflowState, StateCacheAdapter
from ...core.common.cache import CacheManager, CacheEntry
from ...interfaces.prompts import IPromptRegistry

logger = logging.getLogger(__name__)


class PromptCacheManager:
    """提示词缓存管理器
    
    提供多级缓存功能：
    - 状态级缓存：当前工作流执行期间有效
    - 线程级缓存：当前线程/会话期间有效
    - 会话级缓存：跨工作流执行保持
    
    使用CacheManager作为底层实现，避免重复代码。
    """
    
    def __init__(self, 
                 state_cache_adapter: Optional[StateCacheAdapter] = None,
                 max_cache_size: int = 1000,
                 default_ttl: int = 3600):
        """初始化提示词缓存管理器
        
        Args:
            state_cache_adapter: 状态缓存适配器
            max_cache_size: 最大缓存大小
            default_ttl: 默认TTL（秒）
        """
        self._state_cache = state_cache_adapter or StateCacheAdapter("prompts")
        self._max_cache_size = max_cache_size
        self._default_ttl = default_ttl
        
        # 为三个级别分别创建CacheManager实例
        self._managers = {
            "state": CacheManager(max_size=max_cache_size, default_ttl=default_ttl),
            "thread": CacheManager(max_size=max_cache_size, default_ttl=default_ttl),
            "session": CacheManager(max_size=max_cache_size, default_ttl=default_ttl)
        }
        
        # 缓存统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "total_requests": 0
        }
        
        logger.debug(f"初始化提示词缓存管理器，最大缓存大小: {max_cache_size}, 默认TTL: {default_ttl}s")
    
    def _generate_cache_key(self,
                           prompt_ref: str,
                           variables: Dict[str, Any],
                           context: Dict[str, Any]) -> str:
        """生成缓存键
        
        Args:
            prompt_ref: 提示词引用
            variables: 变量字典
            context: 上下文字典
            
        Returns:
            缓存键
        """
        from ...core.common.utils.cache_key_generator import CacheKeyGenerator
        
        return CacheKeyGenerator.generate_reference_key(prompt_ref, variables, context)
    
    async def get_cached_prompt(self, 
                               prompt_ref: str,
                               state: WorkflowState,
                               cache_scope: str = "state",
                               variables: Optional[Dict[str, Any]] = None,
                               context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """获取缓存的提示词
        
        Args:
            prompt_ref: 提示词引用
            state: 工作流状态
            cache_scope: 缓存范围 ("state", "thread", "session")
            variables: 变量字典
            context: 上下文字典
            
        Returns:
            缓存的提示词内容，如果未找到则返回None
        """
        self._stats["total_requests"] += 1
        
        variables = variables or {}
        context = context or {}
        
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt_ref, variables, context)
        
        try:
            # 根据缓存范围获取缓存
            if cache_scope not in self._managers:
                logger.warning(f"未知的缓存范围: {cache_scope}")
                self._stats["misses"] += 1
                return None
            
            manager = self._managers[cache_scope]
            content = await manager.get(cache_key)
            
            if content is not None:
                self._stats["hits"] += 1
                logger.debug(f"缓存命中: {prompt_ref} (范围: {cache_scope})")
                return content
            else:
                self._stats["misses"] += 1
                logger.debug(f"缓存未命中: {prompt_ref} (范围: {cache_scope})")
                return None
                
        except Exception as e:
            logger.warning(f"获取缓存失败: {prompt_ref}, 错误: {e}")
            self._stats["misses"] += 1
            return None
    
    async def cache_prompt(self,
                          prompt_ref: str,
                          content: str,
                          state: WorkflowState,
                          cache_scope: str = "state",
                          ttl: Optional[int] = None,
                          variables: Optional[Dict[str, Any]] = None,
                          context: Optional[Dict[str, Any]] = None,
                          metadata: Optional[Dict[str, Any]] = None) -> None:
        """缓存提示词
        
        Args:
            prompt_ref: 提示词引用
            content: 提示词内容
            state: 工作流状态
            cache_scope: 缓存范围
            ttl: 生存时间（秒）
            variables: 变量字典
            context: 上下文字典
            metadata: 元数据
        """
        variables = variables or {}
        context = context or {}
        metadata = metadata or {}
        ttl = ttl or self._default_ttl
        
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt_ref, variables, context)
        
        # 为缓存值添加元数据
        cache_value = {
            "content": content,
            "prompt_ref": prompt_ref,
            "variables": variables,
            "context_keys": list(context.keys()),
            "timestamp": datetime.now().isoformat(),
            **metadata
        }
        
        try:
            # 根据缓存范围存储缓存
            if cache_scope not in self._managers:
                logger.warning(f"未知的缓存范围: {cache_scope}")
                return
            
            manager = self._managers[cache_scope]
            await manager.set(cache_key, cache_value, ttl)
            
            logger.debug(f"缓存已存储: {prompt_ref} (范围: {cache_scope}, TTL: {ttl}s)")
            
        except Exception as e:
            logger.warning(f"存储缓存失败: {prompt_ref}, 错误: {e}")
    
    async def invalidate_cache(self, 
                              prompt_ref: Optional[str] = None,
                              cache_scope: str = "all") -> None:
        """失效缓存
        
        Args:
            prompt_ref: 提示词引用，如果为None则清理所有缓存
            cache_scope: 缓存范围 ("state", "thread", "session", "all")
        """
        try:
            scopes = [cache_scope] if cache_scope != "all" else list(self._managers.keys())
            
            for scope in scopes:
                if scope not in self._managers:
                    continue
                
                manager = self._managers[scope]
                
                if prompt_ref:
                    # 清理特定的提示词缓存（需要遍历所有键）
                    try:
                        keys = await manager.get_all_keys()
                        for key in keys:
                            # 获取条目以检查元数据
                            if 'default' in manager._cache_entries and key in manager._cache_entries['default']:
                                entry = manager._cache_entries['default'][key]
                                if isinstance(entry.value, dict) and entry.value.get("prompt_ref") == prompt_ref:
                                    await manager.delete(key)
                    except Exception as e:
                        logger.warning(f"清理特定提示词缓存失败 {prompt_ref}: {e}")
                else:
                    # 清理所有缓存
                    await manager.clear()
            
            logger.debug(f"缓存已清理: 提示词={prompt_ref}, 范围={cache_scope}")
            
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
    
    async def preload_common_prompts(self, 
                                    prompt_refs: List[str],
                                    registry: IPromptRegistry,
                                    cache_scope: str = "session") -> None:
        """预加载常用提示词
        
        Args:
            prompt_refs: 提示词引用列表
            registry: 提示词注册表
            cache_scope: 缓存范围
        """
        try:
            for ref in prompt_refs:
                try:
                    # 获取提示词内容
                    prompt = await registry.get(ref)
                    if prompt:
                        await self.cache_prompt(
                            ref,
                            prompt.content,
                            WorkflowState(),  # 使用空状态
                            cache_scope=cache_scope,
                            metadata={"preloaded": True}
                        )
                except Exception as e:
                    logger.warning(f"预加载提示词失败: {ref}, 错误: {e}")
            
            logger.info(f"预加载完成，共处理 {len(prompt_refs)} 个提示词")
            
        except Exception as e:
            logger.error(f"预加载提示词失败: {e}")
    
    def get_cache_statistics(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        hit_rate = 0.0
        if self._stats["total_requests"] > 0:
            hit_rate = self._stats["hits"] / self._stats["total_requests"]
        
        # 汇总各个scope的统计
        scope_stats = {}
        for scope, manager in self._managers.items():
            try:
                stats = manager._stats
                scope_stats[scope] = {
                    "hits": stats.hits,
                    "misses": stats.misses,
                    "evictions": stats.evictions,
                    "size": len(manager._cache_entries.get('default', {}))
                }
            except Exception as e:
                logger.warning(f"获取 {scope} 缓存统计失败: {e}")
                scope_stats[scope] = {"error": str(e)}
        
        return {
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "evictions": self._stats["evictions"],
            "total_requests": self._stats["total_requests"],
            "hit_rate": hit_rate,
            "scope_statistics": scope_stats,
            "max_cache_size": self._max_cache_size,
            "default_ttl": self._default_ttl
        }
    
    async def cleanup_expired(self) -> int:
        """清理过期的缓存条目
        
        Returns:
            清理的条目数量
        """
        cleaned_count = 0
        
        try:
            # 清理所有scope的过期缓存
            for scope, manager in self._managers.items():
                try:
                    count = await manager.cleanup_expired()
                    cleaned_count += count
                except Exception as e:
                    logger.warning(f"清理 {scope} 缓存失败: {e}")
            
            logger.debug(f"清理过期缓存完成，共清理 {cleaned_count} 个条目")
            
        except Exception as e:
            logger.warning(f"清理过期缓存失败: {e}")
        
        return cleaned_count
