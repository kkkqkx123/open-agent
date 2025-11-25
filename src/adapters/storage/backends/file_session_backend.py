"""文件系统会话存储后端实现"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List

from .base import ISessionStorageBackend
from src.core.common.exceptions import StorageError

logger = logging.getLogger(__name__)


class FileSessionBackend(ISessionStorageBackend):
    """文件系统会话存储后端"""
    
    def __init__(self, base_path: str = "./sessions"):
        """初始化文件系统后端
        
        Args:
            base_path: 会话存储基础路径
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"File session backend initialized at {self.base_path}")
    
    def _get_session_file(self, session_id: str) -> Path:
        """获取会话文件路径
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话文件路径
        """
        return self.base_path / f"{session_id}.json"
    
    async def save(self, session_id: str, data: Dict[str, Any]) -> bool:
        """保存会话数据
        
        Args:
            session_id: 会话ID
            data: 会话数据字典
            
        Returns:
            是否保存成功
        """
        try:
            session_file = self._get_session_file(session_id)
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Session saved to file: {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save session {session_id}: {e}")
            raise StorageError(f"Failed to save session: {e}")
    
    async def load(self, session_id: str) -> Optional[Dict[str, Any]]:
        """加载会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            会话数据，不存在返回None
        """
        try:
            session_file = self._get_session_file(session_id)
            if not session_file.exists():
                return None
            
            with open(session_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.debug(f"Session loaded from file: {session_id}")
                return data
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            raise StorageError(f"Failed to load session: {e}")
    
    async def delete(self, session_id: str) -> bool:
        """删除会话数据
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否删除成功
        """
        try:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
                logger.debug(f"Session deleted: {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            raise StorageError(f"Failed to delete session: {e}")
    
    async def list_keys(self, prefix: str = "") -> List[str]:
        """列举所有会话键
        
        Args:
            prefix: 键前缀过滤
            
        Returns:
            会话ID列表
        """
        try:
            if prefix:
                pattern = f"{prefix}*.json"
            else:
                pattern = "*.json"
            
            files = list(self.base_path.glob(pattern))
            keys = [f.stem for f in files]
            logger.debug(f"Listed {len(keys)} session keys with prefix '{prefix}'")
            return keys
        except Exception as e:
            logger.error(f"Failed to list keys: {e}")
            raise StorageError(f"Failed to list keys: {e}")
    
    async def exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            是否存在
        """
        try:
            session_file = self._get_session_file(session_id)
            return session_file.exists()
        except Exception as e:
            logger.error(f"Failed to check session existence: {e}")
            raise StorageError(f"Failed to check session existence: {e}")
    
    async def close(self) -> None:
        """关闭后端连接"""
        logger.debug("File backend connection closed")
