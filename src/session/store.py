"""会话存储模块

提供会话数据的持久化存储功能。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import shutil


class ISessionStore(ABC):
    """会话存储接口"""

    @abstractmethod
    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据

        Args:
            session_id: 会话ID
            session_data: 会话数据

        Returns:
            bool: 是否成功保存
        """
        pass

    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据

        Args:
            session_id: 会话ID

        Returns:
            Optional[Dict[str, Any]]: 会话数据，如果不存在则返回None
        """
        pass

    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """删除会话数据

        Args:
            session_id: 会话ID

        Returns:
            bool: 是否成功删除
        """
        pass

    @abstractmethod
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话

        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        pass

    @abstractmethod
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在

        Args:
            session_id: 会话ID

        Returns:
            bool: 会话是否存在
        """
        pass


class FileSessionStore(ISessionStore):
    """基于文件系统的会话存储实现"""

    def __init__(self, storage_path: Path) -> None:
        """初始化文件会话存储

        Args:
            storage_path: 存储路径
        """
        self.storage_path = storage_path
        self.storage_path.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_id: str) -> Path:
        """获取会话文件路径

        Args:
            session_id: 会话ID

        Returns:
            Path: 会话文件路径
        """
        return self.storage_path / f"{session_id}.json"

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        try:
            session_file = self._get_session_file(session_id)
            
            # 创建临时文件
            temp_file = session_file.with_suffix(".tmp")
            
            # 写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            # 原子性替换
            temp_file.replace(session_file)
            
            return True
        except Exception:
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        try:
            session_file = self._get_session_file(session_id)
            if not session_file.exists():
                return None
                
            with open(session_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        try:
            session_file = self._get_session_file(session_id)
            if session_file.exists():
                session_file.unlink()
            return True
        except Exception:
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        
        try:
            for session_file in self.storage_path.glob("*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                        
                    # 添加基本信息
                    metadata = session_data.get("metadata", {})
                    sessions.append({
                        "session_id": metadata.get("session_id", session_file.stem),
                        "workflow_config_path": metadata.get("workflow_config_path"),
                        "created_at": metadata.get("created_at"),
                        "updated_at": metadata.get("updated_at"),
                        "status": metadata.get("status", "unknown")
                    })
                except Exception:
                    # 跳过损坏的会话文件
                    continue
                    
        except Exception:
            pass
            
        return sessions

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        session_file = self._get_session_file(session_id)
        return session_file.exists()


class MemorySessionStore(ISessionStore):
    """基于内存的会话存储实现（用于测试）"""

    def __init__(self) -> None:
        """初始化内存会话存储"""
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> bool:
        """保存会话数据"""
        try:
            self._sessions[session_id] = session_data.copy()
            return True
        except Exception:
            return False

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话数据"""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """删除会话数据"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话"""
        sessions = []
        
        for session_id, session_data in self._sessions.items():
            metadata = session_data.get("metadata", {})
            sessions.append({
                "session_id": metadata.get("session_id", session_id),
                "workflow_config_path": metadata.get("workflow_config_path"),
                "created_at": metadata.get("created_at"),
                "updated_at": metadata.get("updated_at"),
                "status": metadata.get("status", "unknown")
            })
            
        return sessions

    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        return session_id in self._sessions

    def clear(self) -> None:
        """清除所有会话（仅用于测试）"""
        self._sessions.clear()


class SessionStoreFactory:
    """会话存储工厂"""

    @staticmethod
    def create_store(store_type: str, **kwargs) -> ISessionStore:
        """创建会话存储实例

        Args:
            store_type: 存储类型，支持 "file" 或 "memory"
            **kwargs: 存储特定参数

        Returns:
            ISessionStore: 会话存储实例

        Raises:
            ValueError: 不支持的存储类型
        """
        if store_type == "file":
            storage_path = kwargs.get("storage_path", Path("./sessions"))
            return FileSessionStore(storage_path)
        elif store_type == "memory":
            return MemorySessionStore()
        else:
            raise ValueError(f"不支持的存储类型: {store_type}")