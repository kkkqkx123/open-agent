"""提示词缓存管理器

提供多级提示词缓存功能，复用核心CacheManager实现。
支持状态级、线程级和会话级缓存。
"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timedelta
from functools import wraps

from ...core.state import WorkflowState
from ...infrastructure.cache.config.cache_config import BaseCacheConfig
from ...infrastructure.cache.providers.memory.memory_provider import MemoryCacheProvider
from ...infrastructure.cache.core.key_generator import DefaultCacheKeyGenerator as CacheKeyGenerator
from ...interfaces.prompts import IPromptRegistry

logger = get_logger(__name__)


def handle_cache_errors(default_return=None):
    """缓存操作错误处理装饰器
    
    Args:
        default_return: 发生错误时的默认返回值
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValueError as e:
                logger.error(f"参数错误 in {func.__name__}: {e}")
                return default_return
            except KeyError as e:
                logger.error(f"缺少必要参数 in {func.__name__}: {e}")
                return default_return
            except Exception as e:
                logger.error(f"未预期错误 in {func.__name__}: {e}", exc_info=True)
                return default_return
        return wrapper
    return decorator


def validate_prompt_ref(func: Callable) -> Callable:
    """提示词引用验证装饰器
    
    Args:
        func: 被装饰的函数
        
    Returns:
        装饰器函数
    """
    @wraps(func)
    async def wrapper(self, prompt_ref: str, *args, **kwargs):
        if not prompt_ref:
            logger.error("提示词引用不能为空")
            return None
        
        if not isinstance(prompt_ref, str):
            logger.error(f"提示词引用必须是字符串，当前类型: {type(prompt_ref)}")
            return None
        
        return await func(self, prompt_ref, *args, **kwargs)
    return wrapper


class PromptCacheManager:
    """提示词缓存管理器
    
    提供多级缓存功能：
    - 状态级缓存：当前工作流执行期间有效
    - 线程级缓存：当前线程/会话期间有效
    - 会话级缓存：跨工作流执行保持
    
    使用CacheManager作为底层实现，避免重复代码。
    """
    
    def __init__(self,
                 max_cache_size: int = 1000,
                 default_ttl: int = 3600):
        """初始化提示词缓存管理器
        
        Args:
            max_cache_size: 最大缓存大小
            default_ttl: 默认TTL（秒）
        """
        self._max_cache_size = max_cache_size
        self._default_ttl = default_ttl
        
        # 为三个级别分别创建内存缓存提供者实例
        self._managers = {
            "state": MemoryCacheProvider(max_size=max_cache_size, default_ttl=default_ttl),
            "thread": MemoryCacheProvider(max_size=max_cache_size, default_ttl=default_ttl),
            "session": MemoryCacheProvider(max_size=max_cache_size, default_ttl=default_ttl)
        }
        
        # 缓存键生成器实例（避免重复创建）
        self._key_generator = CacheKeyGenerator()
        
        # 简化的标签索引，仅用于基于提示词引用的快速失效
        self._prompt_ref_index: Dict[str, set] = {}
        
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
        return self._key_generator.generate_reference_key(prompt_ref, variables, context)
    
    def _add_to_prompt_ref_index(self, cache_key: str, prompt_ref: str, cache_scope: str) -> None:
        """添加到提示词引用索引
        
        Args:
            cache_key: 缓存键
            prompt_ref: 提示词引用
            cache_scope: 缓存范围
        """
        if prompt_ref not in self._prompt_ref_index:
            self._prompt_ref_index[prompt_ref] = set()
        self._prompt_ref_index[prompt_ref].add((cache_scope, cache_key))
    
    def _remove_from_prompt_ref_index(self, cache_key: str, prompt_ref: str, cache_scope: str) -> None:
        """从提示词引用索引中移除
        
        Args:
            cache_key: 缓存键
            prompt_ref: 提示词引用
            cache_scope: 缓存范围
        """
        if prompt_ref in self._prompt_ref_index:
            self._prompt_ref_index[prompt_ref].discard((cache_scope, cache_key))
            # 如果引用下没有缓存项了，删除引用
            if not self._prompt_ref_index[prompt_ref]:
                del self._prompt_ref_index[prompt_ref]
    
    @validate_prompt_ref
    @handle_cache_errors(default_return=None)
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
        variables = variables or {}
        context = context or {}
        
        # 生成缓存键
        cache_key = self._generate_cache_key(prompt_ref, variables, context)
        
        # 验证缓存键
        if not cache_key:
            logger.error(f"生成缓存键失败: {prompt_ref}")
            return None
        
        # 根据缓存范围获取缓存
        if cache_scope not in self._managers:
            logger.warning(f"未知的缓存范围: {cache_scope}，可用范围: {list(self._managers.keys())}")
            return None
        
        manager = self._managers[cache_scope]
        cache_value = manager.get(cache_key)
        
        if cache_value is not None:
            # 验证缓存值结构
            if not isinstance(cache_value, dict):
                logger.warning(f"缓存值结构异常: {prompt_ref} (范围: {cache_scope})")
                return None
            
            content = cache_value.get("content")
            if content is None:
                logger.warning(f"缓存内容为空: {prompt_ref} (范围: {cache_scope})")
                return None
            
            logger.debug(f"缓存命中: {prompt_ref} (范围: {cache_scope}, 键: {cache_key[:8]}...)")
            
            # 记录缓存元数据信息（调试用）
            cache_timestamp = cache_value.get("timestamp", "unknown")
            logger.debug(f"缓存元数据 - 时间戳: {cache_timestamp}")
            
            return content
        else:
            logger.debug(f"缓存未命中: {prompt_ref} (范围: {cache_scope}, 键: {cache_key[:8]}...)")
            return None
    
    @validate_prompt_ref
    @handle_cache_errors(default_return=None)
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
        
        # 根据缓存范围存储缓存
        if cache_scope not in self._managers:
            logger.warning(f"未知的缓存范围: {cache_scope}")
            return
        
        manager = self._managers[cache_scope]
        manager.set(cache_key, cache_value, ttl)
        
        # 添加到提示词引用索引
        self._add_to_prompt_ref_index(cache_key, prompt_ref, cache_scope)
        
        logger.debug(f"缓存已存储: {prompt_ref} (范围: {cache_scope}, TTL: {ttl}s)")
    
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
                    # 使用提示词引用索引进行高效失效
                    self._invalidate_by_prompt_ref_optimized(prompt_ref, scope)
                else:
                    # 清理所有缓存（MemoryCacheProvider不支持clear，所以手动清理）
                    # 清理提示词引用索引中该范围的所有条目
                    self._cleanup_prompt_ref_index_for_scope(scope)
            
            logger.debug(f"缓存已清理: 提示词={prompt_ref}, 范围={cache_scope}")
            
        except Exception as e:
            logger.warning(f"清理缓存失败: {e}")
    
    def _invalidate_by_prompt_ref_optimized(self, prompt_ref: str, scope: str) -> None:
        """使用提示词引用索引进行高效失效
        
        Args:
            prompt_ref: 提示词引用
            scope: 缓存范围
        """
        try:
            if prompt_ref not in self._prompt_ref_index:
                logger.debug(f"提示词引用索引中未找到: {prompt_ref}")
                return
            
            # 获取该引用下的所有缓存键
            keys_to_delete = set()
            for cached_scope, cache_key in self._prompt_ref_index[prompt_ref]:
                if cached_scope == scope:
                    keys_to_delete.add(cache_key)
            
            # MemoryCacheProvider没有delete方法，所以我们只更新索引
            deleted_count = len(keys_to_delete)
            
            # 更新索引
            remaining_items = set()
            for cached_scope, cache_key in self._prompt_ref_index[prompt_ref]:
                if cached_scope != scope or cache_key not in keys_to_delete:
                    remaining_items.add((cached_scope, cache_key))
            
            if remaining_items:
                self._prompt_ref_index[prompt_ref] = remaining_items
            else:
                del self._prompt_ref_index[prompt_ref]
            
            logger.debug(f"已标记 {deleted_count} 个缓存条目: {prompt_ref} (范围: {scope})")
            
        except Exception as e:
            logger.warning(f"优化失效失败 {prompt_ref}: {e}")

    
    def _cleanup_prompt_ref_index_for_scope(self, scope: str) -> None:
        """清理指定范围的提示词引用索引
        
        Args:
            scope: 缓存范围
        """
        try:
            refs_to_cleanup = []
            
            for prompt_ref, items in self._prompt_ref_index.items():
                # 移除该范围的所有条目
                remaining_items = {item for item in items if item[0] != scope}
                
                if remaining_items:
                    self._prompt_ref_index[prompt_ref] = remaining_items
                else:
                    refs_to_cleanup.append(prompt_ref)
            
            # 删除空引用
            for prompt_ref in refs_to_cleanup:
                del self._prompt_ref_index[prompt_ref]
                
        except Exception as e:
            logger.warning(f"清理提示词引用索引失败 (范围: {scope}): {e}")
    
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
                            prompt.content if hasattr(prompt, 'content') else str(prompt),
                            WorkflowState(),  # 使用空状态
                            cache_scope=cache_scope,
                            metadata={"preloaded": True}
                        )
                except Exception as e:
                    logger.warning(f"预加载提示词失败: {ref}, 错误: {e}")
            
            logger.info(f"预加载完成，共处理 {len(prompt_refs)} 个提示词")
            
        except Exception as e:
            logger.error(f"预加载提示词失败: {e}")
    
    async def get_cache_statistics(self, scope: Optional[str] = None) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Args:
            scope: 特定缓存范围，如果为None则返回所有范围的统计
            
        Returns:
            统计信息字典
        """
        # 汇总各个scope的统计
        scope_stats = {}
        total_size = 0
        total_hits = 0
        total_misses = 0
        total_evictions = 0
        total_requests = 0
        
        scopes_to_process = [scope] if scope else list(self._managers.keys())
        
        for scope_name in scopes_to_process:
            if scope_name not in self._managers:
                continue
                
            manager = self._managers[scope_name]
            try:
                # 获取管理器统计信息（MemoryCacheProvider没有get_stats方法）
                manager_stats = getattr(manager, 'get_stats', None)
                
                if manager_stats:
                    scope_stats[scope_name] = {
                        "hits": manager_stats.get("hits", 0),
                        "misses": manager_stats.get("misses", 0),
                        "evictions": manager_stats.get("evictions", 0),
                        "total_requests": manager_stats.get("total_requests", 0),
                        "hit_rate": manager_stats.get("hit_rate", 0.0),
                        "cache_size": manager_stats.get("cache_size", 0),
                        "max_size": manager_stats.get("max_size", self._max_cache_size),
                        "default_ttl": manager_stats.get("default_ttl", self._default_ttl)
                    }
                    
                    # 累计统计
                    total_size += manager_stats.get("cache_size", 0)
                    total_hits += manager_stats.get("hits", 0)
                    total_misses += manager_stats.get("misses", 0)
                    total_evictions += manager_stats.get("evictions", 0)
                    total_requests += manager_stats.get("total_requests", 0)
                else:
                    # MemoryCacheProvider没有统计，返回基础信息
                    cache_size = len(manager._cache) if hasattr(manager, '_cache') else 0
                    scope_stats[scope_name] = {
                        "hits": 0,
                        "misses": 0,
                        "evictions": 0,
                        "total_requests": 0,
                        "hit_rate": 0.0,
                        "cache_size": cache_size,
                        "max_size": self._max_cache_size,
                        "default_ttl": self._default_ttl
                    }
                    total_size += cache_size
                    
            except Exception as e:
                logger.warning(f"获取 {scope_name} 缓存统计失败: {e}")
                scope_stats[scope_name] = {"error": str(e)}
        
        # 计算总体命中率
        overall_hit_rate = 0.0
        if total_requests > 0:
            overall_hit_rate = total_hits / total_requests
        
        # 获取提示词引用索引统计
        ref_index_stats = self.get_prompt_ref_index_statistics()
        
        result = {
            "total_hits": total_hits,
            "total_misses": total_misses,
            "total_evictions": total_evictions,
            "total_requests": total_requests,
            "overall_hit_rate": overall_hit_rate,
            "scope_statistics": scope_stats,
            "max_cache_size": self._max_cache_size,
            "default_ttl": self._default_ttl,
            "total_cache_size": total_size,
            "prompt_ref_index_stats": ref_index_stats,
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果指定了特定范围，添加范围特定的统计
        if scope and scope in scope_stats:
            result["scope_specific"] = scope_stats[scope]
        
        return result
    
    def get_prompt_ref_index_statistics(self) -> Dict[str, Any]:
        """获取提示词引用索引统计信息
        
        Returns:
            提示词引用索引统计信息
        """
        try:
            total_refs = len(self._prompt_ref_index)
            total_indexed_items = sum(len(items) for items in self._prompt_ref_index.values())
            
            scope_distribution = {}
            for items in self._prompt_ref_index.values():
                for scope, _ in items:
                    scope_distribution[scope] = scope_distribution.get(scope, 0) + 1
            
            return {
                "total_prompt_refs": total_refs,
                "total_indexed_items": total_indexed_items,
                "scope_distribution": scope_distribution,
                "average_items_per_ref": total_indexed_items / total_refs if total_refs > 0 else 0
            }
            
        except Exception as e:
            logger.warning(f"获取提示词引用索引统计失败: {e}")
            return {"error": str(e)}
    
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
                    # MemoryCacheProvider的cleanup_expired方法
                    if hasattr(manager, 'cleanup_expired'):
                        count = manager.cleanup_expired()
                        cleaned_count += count
                except Exception as e:
                    logger.warning(f"清理 {scope} 缓存失败: {e}")
            
            logger.debug(f"清理过期缓存完成，共清理 {cleaned_count} 个条目")
            
        except Exception as e:
            logger.warning(f"清理过期缓存失败: {e}")
        
        return cleaned_count
    
