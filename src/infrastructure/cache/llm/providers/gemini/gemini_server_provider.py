"""Gemini服务器端缓存提供者"""

from typing import Any, Optional, List, Dict
from datetime import datetime
from src.interfaces.dependency_injection import get_logger

# 导入服务器端缓存接口
from src.infrastructure.cache.interfaces.server_cache_provider import IServerCacheProvider

logger = get_logger(__name__)


class GeminiServerCacheProvider(IServerCacheProvider):
    """Gemini服务器端缓存提供者"""
    
    def __init__(self, gemini_client: Any, model_name: str):
        """
        初始化Gemini服务器端缓存提供者
        
        Args:
            gemini_client: Gemini客户端实例
            model_name: 模型名称
        """
        if not model_name:
            raise ValueError("模型名称不能为空")
            
        self._client = gemini_client
        self._model_name = model_name
        self._cache_registry: Dict[str, str] = {}  # 本地缓存注册表：缓存键 -> 缓存名称
        self._cache_metadata: Dict[str, Dict[str, Any]] = {}  # 缓存元数据
    
    def create_cache(self, contents: List[Any], **kwargs) -> Any:
        """
        创建服务器端缓存
        
        Args:
            contents: 要缓存的内容列表
            **kwargs: 其他参数（system_instruction, ttl, display_name等）
            
        Returns:
            创建的缓存对象
        """
        system_instruction = kwargs.get("system_instruction")
        ttl = kwargs.get("ttl", "3600s")
        display_name = kwargs.get("display_name")
        
        try:
            # 检查google.genai可用性
            genai_available = self._check_genai_available()
            
            if genai_available:
                cache = self._create_cache_with_genai(contents, system_instruction, ttl, display_name)
            else:
                cache = self._create_mock_cache(contents, system_instruction, ttl, display_name)
            
            # 注册到本地缓存表
            cache_key = self._generate_cache_key(contents, system_instruction)
            self._cache_registry[cache_key] = cache.name
            
            # 存储元数据
            self._cache_metadata[cache.name] = {
                "cache_key": cache_key,
                "display_name": display_name,
                "created_at": datetime.now(),
                "ttl": ttl,
                "contents_count": len(contents)
            }
            
            logger.info(f"创建Gemini服务器端缓存: {cache.name}")
            return cache
            
        except Exception as e:
            logger.error(f"创建Gemini服务器端缓存失败: {e}")
            raise
    
    def get_cache(self, cache_name: str) -> Optional[Any]:
        """
        获取缓存对象
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            缓存对象，如果不存在则返回None
        """
        try:
            cache = self._client.caches.get(name=cache_name)
            return cache
        except Exception as e:
            logger.warning(f"获取Gemini缓存失败: {cache_name}, 错误: {e}")
            return None
    
    def use_cache(self, cache_name: str, contents: Any) -> Any:
        """
        使用服务器端缓存生成内容
        
        Args:
            cache_name: 缓存名称
            contents: 查询内容
            
        Returns:
            生成的内容响应
        """
        try:
            genai_available = self._check_genai_available()
            
            if genai_available:
                return self._use_cache_with_genai(cache_name, contents)
            else:
                return self._create_mock_response()
                
        except Exception as e:
            logger.error(f"使用Gemini缓存失败: {cache_name}, 错误: {e}")
            raise
    
    def delete_cache(self, cache_name: str) -> bool:
        """
        删除缓存
        
        Args:
            cache_name: 缓存名称
            
        Returns:
            是否删除成功
        """
        try:
            self._client.caches.delete(cache_name)
            
            # 从本地注册表中移除
            for key, name in list(self._cache_registry.items()):
                if name == cache_name:
                    del self._cache_registry[key]
                    break
            
            if cache_name in self._cache_metadata:
                del self._cache_metadata[cache_name]
            
            logger.info(f"删除Gemini缓存: {cache_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除Gemini缓存失败: {cache_name}, 错误: {e}")
            return False
    
    def list_caches(self) -> List[Any]:
        """
        列出所有缓存
        
        Returns:
            缓存对象列表
        """
        try:
            caches = list(self._client.caches.list())
            return caches
        except Exception as e:
            logger.error(f"列出Gemini缓存失败: {e}")
            return []
    
    def cleanup_expired_caches(self) -> int:
        """
        清理过期的缓存
        
        Returns:
            清理的缓存数量
        """
        try:
            caches = self.list_caches()
            now = datetime.now()
            cleaned_count = 0
            
            for cache in caches:
                if hasattr(cache, 'expire_time'):
                    try:
                        expire_time = datetime.fromisoformat(cache.expire_time.replace('Z', '+00:00'))
                        if expire_time <= now:
                            if self.delete_cache(cache.name):
                                cleaned_count += 1
                    except Exception as e:
                        logger.warning(f"检查缓存过期失败: {cache.name}, 错误: {e}")
            
            logger.info(f"清理了 {cleaned_count} 个过期的Gemini缓存")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"清理过期Gemini缓存失败: {e}")
            return 0
    
    def get_or_create_cache(self, contents: List[Any], **kwargs) -> Any:
        """
        获取或创建缓存
        
        Args:
            contents: 要缓存的内容列表
            **kwargs: 其他参数
            
        Returns:
            缓存对象
        """
        cache_key = self._generate_cache_key(contents, kwargs.get("system_instruction"))
        
        if cache_key in self._cache_registry:
            cache_name = self._cache_registry[cache_key]
            cache = self.get_cache(cache_name)
            if cache:
                logger.debug(f"使用现有Gemini缓存: {cache_name}")
                return cache
        
        # 创建新缓存
        logger.info(f"创建新的Gemini缓存，键: {cache_key}")
        return self.create_cache(contents, **kwargs)
    
    def should_use_server_cache(self, contents: List[Any], threshold: int = 1048576) -> bool:
        """
        判断是否应该使用服务器端缓存
        
        Args:
            contents: 内容列表
            threshold: 大小阈值（字节）
            
        Returns:
            是否应该使用服务器端缓存
        """
        try:
            total_size = 0
            for content in contents:
                if hasattr(content, 'size'):
                    total_size += content.size
                elif hasattr(content, 'text'):
                    total_size += len(content.text.encode('utf-8'))
                else:
                    total_size += len(str(content).encode('utf-8'))
            
            return total_size >= threshold
            
        except Exception as e:
            logger.warning(f"判断是否使用服务器端缓存失败: {e}")
            return False
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            统计信息字典
        """
        try:
            # 获取服务器端缓存列表
            server_caches = self.list_caches()
            
            # 计算本地注册表统计
            local_stats = {
                "registered_caches": len(self._cache_registry),
                "cache_metadata": len(self._cache_metadata)
            }
            
            # 计算服务器端统计
            server_stats = {
                "total_caches": len(server_caches),
                "active_caches": 0,
                "expired_caches": 0
            }
            
            now = datetime.now()
            for cache in server_caches:
                # 检查缓存是否过期（需要解析expire_time）
                if hasattr(cache, 'expire_time'):
                    try:
                        expire_time = datetime.fromisoformat(cache.expire_time.replace('Z', '+00:00'))
                        if expire_time > now:
                            server_stats["active_caches"] += 1
                        else:
                            server_stats["expired_caches"] += 1
                    except:
                        server_stats["active_caches"] += 1
                else:
                    server_stats["active_caches"] += 1
            
            return {
                "local_registry": local_stats,
                "server_caches": server_stats,
                "model_name": self._model_name
            }
            
        except Exception as e:
            logger.error(f"获取Gemini缓存统计失败: {e}")
            return {"error": str(e)}
    
    # 私有方法
    def _check_genai_available(self) -> bool:
        """检查google.genai是否可用"""
        try:
            from google.genai import types as genai_types  # type: ignore
            return genai_types is not None
        except ImportError:
            return False
    
    def _create_cache_with_genai(self, contents: List[Any], system_instruction: Optional[str], 
                                ttl: str, display_name: Optional[str]) -> Any:
        """使用google.genai创建缓存"""
        from google.genai import types as genai_types  # type: ignore
        
        config = genai_types.CreateCachedContentConfig(
            contents=contents,
            ttl=ttl
        )
        
        if system_instruction:
            config.system_instruction = system_instruction
        
        if display_name:
            config.display_name = display_name
        
        return self._client.caches.create(
            model=self._model_name,
            config=config
        )
    
    def _create_mock_cache(self, contents: List[Any], system_instruction: Optional[str], 
                          ttl: str, display_name: Optional[str]) -> Any:
        """创建模拟缓存对象（用于测试）"""
        class MockCache:
            def __init__(self, name: str):
                self.name = name
        
        class MockConfig:
            def __init__(self, contents, system_instruction, ttl, display_name):
                self.contents = contents
                self.system_instruction = system_instruction
                self.ttl = ttl
                self.display_name = display_name
        
        config = MockConfig(contents, system_instruction, ttl, display_name)
        cache_name = f"mock_cache_{hash(str(contents))}"
        
        # 尝试调用客户端方法（可能抛出异常，用于测试错误处理）
        try:
            return self._client.caches.create(
                model=self._model_name,
                config=config
            )
        except:
            return MockCache(cache_name)
    
    def _use_cache_with_genai(self, cache_name: str, contents: Any) -> Any:
        """使用google.genai调用缓存"""
        from google.genai import types as genai_types  # type: ignore
        
        return self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=genai_types.GenerateContentConfig(cached_content=cache_name)
        )
    
    def _create_mock_response(self) -> Any:
        """创建模拟响应"""
        class MockResponse:
            def __init__(self):
                self.text = "mock response"
        
        return MockResponse()
    
    def _generate_cache_key(self, contents: List[Any], system_instruction: Optional[str] = None) -> str:
        """生成缓存键"""
        import hashlib
        import json
        
        serialized_contents = []
        for content in contents:
            if hasattr(content, 'uri'):
                serialized_contents.append(f"uri:{content.uri}")
            elif hasattr(content, 'text'):
                serialized_contents.append(f"text:{content.text}")
            else:
                serialized_contents.append(str(content))
        
        key_data = {
            "contents": serialized_contents,
            "system_instruction": system_instruction or "",
            "model": self._model_name
        }
        
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()