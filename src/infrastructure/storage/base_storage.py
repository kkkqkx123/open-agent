"""基础存储实现和适配器"""

from typing import Dict, Any, Optional, List

from src.interfaces.storage.base import IStorage
from src.infrastructure.common.serialization import Serializer
from src.infrastructure.common.utils.temporal import TemporalManager
from src.infrastructure.common.utils.metadata import MetadataManager
from src.infrastructure.common.cache import CacheManager


class BaseStorage(IStorage):
    """存储基类，提供通用功能"""
    
    def __init__(
        self,
        serializer: Optional[Serializer] = None,
        temporal_manager: Optional[TemporalManager] = None,
        metadata_manager: Optional[MetadataManager] = None,
        cache_manager: Optional[CacheManager] = None
    ):
        """初始化基础存储
        
        Args:
            serializer: 序列化器
            temporal_manager: 时间管理器
            metadata_manager: 元数据管理器
            cache_manager: 缓存管理器（异步）
        """
        self.serializer = serializer or Serializer()
        self.temporal = temporal_manager or TemporalManager()
        self.metadata = metadata_manager or MetadataManager()
        self.cache = cache_manager
    
    async def save_with_metadata(
        self,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        ttl: Optional[int] = None
    ) -> str:
        """保存数据并处理元数据
        
        Args:
            data: 要保存的数据
            metadata: 元数据
            ttl: 缓存TTL
            
        Returns:
            保存的数据ID
        """
        # 添加时间戳
        data["created_at"] = self.temporal.format_timestamp(
            self.temporal.now(), "iso"
        )
        data["updated_at"] = data["created_at"]
        
        # 处理元数据
        if metadata:
            normalized_metadata = self.metadata.normalize_metadata(metadata)
            data["metadata"] = normalized_metadata
        
        # 保存数据
        data_id = await self.save(data)
        
        # 缓存数据
        if self.cache and data.get("id"):
            await self.cache.set(data["id"], data, ttl=ttl)
        
        return data_id
    
    async def load_with_cache(self, id: str) -> Optional[Dict[str, Any]]:
        """加载数据（优先从缓存）
        
        Args:
            id: 数据ID
            
        Returns:
            数据字典，如果不存在则返回None
        """
        # 先从缓存获取
        if self.cache:
            cached_data = await self.cache.get(id)
            if cached_data:
                return cached_data
        
        # 从存储加载
        data = await self.load(id)
        
        # 缓存结果
        if data and self.cache:
            await self.cache.set(id, data)
        
        return data
    
    async def update_with_metadata(
        self,
        id: str,
        updates: Dict[str, Any],
        metadata_updates: Optional[Dict[str, Any]] = None
    ) -> bool:
        """更新数据并处理元数据
        
        Args:
            id: 数据ID
            updates: 更新数据
            metadata_updates: 元数据更新
            
        Returns:
            是否更新成功
        """
        # 加载现有数据
        existing_data = await self.load(id)
        if not existing_data:
            return False
        
        # 更新数据
        existing_data.update(updates)
        existing_data["updated_at"] = self.temporal.format_timestamp(
            self.temporal.now(), "iso"
        )
        
        # 更新元数据
        if metadata_updates and "metadata" in existing_data:
            updated_metadata = self.metadata.merge_metadata(
                existing_data["metadata"], metadata_updates
            )
            existing_data["metadata"] = updated_metadata
        
        # 保存更新
        data_id = await self.save(existing_data)
        
        # 更新缓存
        if self.cache and data_id:
            await self.cache.set(id, existing_data)
        
        return bool(data_id)
    
    async def list_by_metadata(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据元数据过滤列表
        
        Args:
            filters: 元数据过滤条件
            limit: 限制数量
            
        Returns:
            符合条件的数据列表
        """
        all_data = await self.list({})
        
        # 过滤数据
        filtered_data = []
        for item in all_data:
            metadata = item.get("metadata", {})
            match = True
            
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_data.append(item)
                if limit and len(filtered_data) >= limit:
                    break
        
        return filtered_data
    
    async def delete_with_cache(self, id: str) -> bool:
        """删除数据并清理缓存
        
        Args:
            id: 数据ID
            
        Returns:
            是否删除成功
        """
        # 删除数据
        success = await self.delete(id)
        
        # 清理缓存
        if success and self.cache:
            await self.cache.delete(id)
        
        return success