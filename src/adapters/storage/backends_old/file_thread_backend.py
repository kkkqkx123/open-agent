"""文件系统线程存储后端实现"""

import json
from src.services.logger.injection import get_logger
from pathlib import Path
from typing import Dict, Any, Optional, List

from .thread_base import IThreadStorageBackend
from src.interfaces.storage.exceptions import StorageError

logger = get_logger(__name__)


class FileThreadBackend(IThreadStorageBackend):
    """文件系统线程存储后端 - 专注于线程数据存储"""
    
    def __init__(self, base_path: str = "./threads"):
        """初始化文件系统线程后端
        
        Args:
            base_path: 线程存储基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"File thread backend initialized at {self.base_path}")
    
    def _get_thread_file(self, thread_id: str) -> Path:
        """获取线程文件路径
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程文件路径
        """
        return self.base_path / f"{thread_id}.json"
    
    async def save(self, thread_id: str, data: Dict[str, Any]) -> bool:
        """保存线程数据
        
        Args:
            thread_id: 线程ID
            data: 线程数据字典
            
        Returns:
            是否保存成功
        """
        try:
            thread_file = self._get_thread_file(thread_id)
            with open(thread_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Thread saved to file: {thread_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save thread {thread_id}: {e}")
            raise StorageError(f"Failed to save thread: {e}")
    
    async def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """加载线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            线程数据，不存在返回None
        """
        try:
            thread_file = self._get_thread_file(thread_id)
            if not thread_file.exists():
                return None
            
            with open(thread_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Thread loaded from file: {thread_id}")
                return data
        except Exception as e:
            logger.error(f"Failed to load thread {thread_id}: {e}")
            raise StorageError(f"Failed to load thread: {e}")
    
    async def delete(self, thread_id: str) -> bool:
        """删除线程数据
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否删除成功
        """
        try:
            thread_file = self._get_thread_file(thread_id)
            if thread_file.exists():
                thread_file.unlink()
                logger.debug(f"Thread deleted: {thread_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete thread {thread_id}: {e}")
            raise StorageError(f"Failed to delete thread: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有线程键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            线程ID列表
        """
        try:
            if prefix:
                pattern = f"{prefix}*.json"
            else:
                pattern = "*.json"
            
            files = list(self.base_path.glob(pattern))
            keys = [f.stem for f in files]
            logger.debug(f"Listed {len(keys)} thread keys with prefix '{prefix}'")
            return keys
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise StorageError(f"Failed to list keys: {e}")
    
    async def exists(self, thread_id: str) -> bool:
        """检查线程是否存在
        
        Args:
            thread_id: 线程ID
            
        Returns:
            是否存在
        """
        try:
            thread_file = self._get_thread_file(thread_id)
            return thread_file.exists()
        except Exception as e:
            logger.error(f"Failed to check thread existence: {e}")
            raise StorageError(f"Failed to check thread existence: {e}")
    
    async def close(self) -> None:
        """关闭后端连接"""
        logger.debug("File thread backend connection closed")
