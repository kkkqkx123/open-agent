"""Thread元数据存储实现"""

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

logger = logging.getLogger(__name__)


class IThreadMetadataStore(ABC):
    """Thread元数据存储接口"""
    
    @abstractmethod
    async def save_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """保存Thread元数据
        
        Args:
            thread_id: Thread ID
            metadata: 元数据字典
            
        Returns:
            保存是否成功
        """
        pass
    
    @abstractmethod
    async def get_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取Thread元数据
        
        Args:
            thread_id: Thread ID
            
        Returns:
            元数据字典，如果不存在则返回None
        """
        pass
    
    @abstractmethod
    async def update_metadata(self, thread_id: str, updates: Dict[str, Any]) -> bool:
        """更新Thread元数据
        
        Args:
            thread_id: Thread ID
            updates: 要更新的字段
            
        Returns:
            更新是否成功
        """
        pass
    
    @abstractmethod
    async def delete_metadata(self, thread_id: str) -> bool:
        """删除Thread元数据
        
        Args:
            thread_id: Thread ID
            
        Returns:
            删除是否成功
        """
        pass
    
    @abstractmethod
    async def list_threads(self) -> List[Dict[str, Any]]:
        """列出所有Thread元数据
        
        Returns:
            Thread元数据列表
        """
        pass
    
    @abstractmethod
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在
        
        Args:
            thread_id: Thread ID
            
        Returns:
            Thread是否存在
        """
        pass


class FileThreadMetadataStore(IThreadMetadataStore):
    """基于文件系统的Thread元数据存储实现"""
    
    def __init__(self, storage_path: Path):
        """初始化文件存储
        
        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path / "thread_metadata"
        self.storage_path.mkdir(parents=True, exist_ok=True)
    
    async def save_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """保存Thread元数据到文件"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        temp_file = metadata_file.with_suffix(".tmp")
        
        try:
            # 原子性写入
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            temp_file.replace(metadata_file)
            logger.debug(f"Thread元数据保存成功: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存Thread元数据失败: {thread_id}, 错误: {e}")
            # 清理临时文件
            if temp_file.exists():
                temp_file.unlink()
            return False
    
    async def get_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """从文件获取Thread元数据"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        if not metadata_file.exists():
            logger.debug(f"Thread元数据文件不存在: {thread_id}")
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            logger.debug(f"Thread元数据读取成功: {thread_id}")
            return metadata
            
        except Exception as e:
            logger.error(f"读取Thread元数据失败: {thread_id}, 错误: {e}")
            return None
    
    async def update_metadata(self, thread_id: str, updates: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        current_metadata = await self.get_metadata(thread_id)
        if not current_metadata:
            logger.warning(f"Thread不存在，无法更新元数据: {thread_id}")
            return False
        
        # 合并更新
        current_metadata.update(updates)
        
        # 保存更新后的元数据
        return await self.save_metadata(thread_id, current_metadata)
    
    async def delete_metadata(self, thread_id: str) -> bool:
        """删除Thread元数据文件"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        if not metadata_file.exists():
            logger.warning(f"Thread元数据文件不存在: {thread_id}")
            return False
        
        try:
            metadata_file.unlink()
            logger.debug(f"Thread元数据删除成功: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除Thread元数据失败: {thread_id}, 错误: {e}")
            return False
    
    async def list_threads(self) -> List[Dict[str, Any]]:
        """列出所有Thread元数据"""
        threads = []
        
        try:
            for metadata_file in self.storage_path.glob("*.json"):
                metadata = await self.get_metadata(metadata_file.stem)
                if metadata:
                    threads.append(metadata)
            
            logger.debug(f"列出 {len(threads)} 个Threads")
            
        except Exception as e:
            logger.error(f"列出Threads失败: {e}")
        
        return threads
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread元数据文件是否存在"""
        metadata_file = self.storage_path / f"{thread_id}.json"
        return metadata_file.exists()


class MemoryThreadMetadataStore(IThreadMetadataStore):
    """基于内存的Thread元数据存储实现（主要用于测试）"""
    
    def __init__(self):
        """初始化内存存储"""
        self._metadata_store: Dict[str, Dict[str, Any]] = {}
    
    async def save_metadata(self, thread_id: str, metadata: Dict[str, Any]) -> bool:
        """保存Thread元数据到内存"""
        try:
            self._metadata_store[thread_id] = metadata.copy()
            logger.debug(f"Thread元数据保存到内存成功: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"保存Thread元数据到内存失败: {thread_id}, 错误: {e}")
            return False
    
    async def get_metadata(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """从内存获取Thread元数据"""
        metadata = self._metadata_store.get(thread_id)
        if metadata:
            # 返回副本以避免外部修改
            return metadata.copy()
        return None
    
    async def update_metadata(self, thread_id: str, updates: Dict[str, Any]) -> bool:
        """更新Thread元数据"""
        if thread_id not in self._metadata_store:
            logger.warning(f"Thread不存在，无法更新元数据: {thread_id}")
            return False
        
        try:
            self._metadata_store[thread_id].update(updates)
            logger.debug(f"Thread元数据更新成功: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新Thread元数据失败: {thread_id}, 错误: {e}")
            return False
    
    async def delete_metadata(self, thread_id: str) -> bool:
        """从内存删除Thread元数据"""
        if thread_id not in self._metadata_store:
            logger.warning(f"Thread不存在，无法删除元数据: {thread_id}")
            return False
        
        try:
            del self._metadata_store[thread_id]
            logger.debug(f"Thread元数据从内存删除成功: {thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"删除Thread元数据失败: {thread_id}, 错误: {e}")
            return False
    
    async def list_threads(self) -> List[Dict[str, Any]]:
        """列出所有Thread元数据"""
        # 返回副本以避免外部修改
        return [metadata.copy() for metadata in self._metadata_store.values()]
    
    async def thread_exists(self, thread_id: str) -> bool:
        """检查Thread是否存在于内存中"""
        return thread_id in self._metadata_store
    
    def clear(self) -> None:
        """清空所有元数据（主要用于测试）"""
        self._metadata_store.clear()