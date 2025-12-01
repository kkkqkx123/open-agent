"""Session基础抽象类"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from src.interfaces.state.session import ISessionState
    from src.interfaces.state.session import ISessionStateManager


class SessionBase(ABC):
    """Session基础抽象类 - 提供Session实体的基础功能"""
    
    def __init__(self, session_data: Dict[str, Any],
                 session_state: Optional['ISessionState'] = None,
                 session_state_manager: Optional['ISessionStateManager'] = None):
        """初始化Session基础类
        
        Args:
            session_data: 会话数据
            session_state: 会话状态对象（可选）
            session_state_manager: 会话状态管理器（可选）
        """
        self._session_data = session_data
        self._session_state = session_state
        self._session_state_manager = session_state_manager
    
    @property
    def id(self) -> str:
        """获取会话ID"""
        return str(self._session_data.get("id", ""))
    
    @property
    def status(self) -> str:
        """获取会话状态"""
        return str(self._session_data.get("status", ""))
    
    @property
    def graph_id(self) -> Optional[str]:
        """获取关联的图ID"""
        return self._session_data.get("graph_id")
    
    @property
    def thread_id(self) -> Optional[str]:
        """获取关联的线程ID"""
        return self._session_data.get("thread_id")
    
    @property
    def created_at(self) -> datetime:
        """获取创建时间"""
        created_at = self._session_data.get("created_at")
        if isinstance(created_at, str):
            return datetime.fromisoformat(created_at)
        return created_at or datetime.utcnow()
    
    @property
    def updated_at(self) -> datetime:
        """获取更新时间"""
        updated_at = self._session_data.get("updated_at")
        if isinstance(updated_at, str):
            return datetime.fromisoformat(updated_at)
        return updated_at or datetime.utcnow()
    
    @property
    def metadata(self) -> Dict[str, Any]:
        """获取会话元数据"""
        result = self._session_data.get("metadata", {})
        return result if isinstance(result, dict) else {}
    
    @property
    def config(self) -> Dict[str, Any]:
        """获取会话配置"""
        result = self._session_data.get("config", {})
        return result if isinstance(result, dict) else {}
    
    @property
    def state(self) -> Dict[str, Any]:
        """获取会话状态"""
        if self._session_state:
            result = self._session_state.to_dict()['data']
            return result if isinstance(result, dict) else {}
        result = self._session_data.get("state", {})
        return result if isinstance(result, dict) else {}
    
    @state.setter
    def state(self, value: Dict[str, Any]) -> None:
        """设置会话状态"""
        if self._session_state:
            self._session_state.set_data("session_data", value)
            self._sync_state_to_session_data()
        else:
            self._session_data["state"] = value
    
    @property
    def message_count(self) -> int:
        """获取消息计数"""
        if self._session_state:
            return self._session_state.message_count
        return int(self._session_data.get("message_count", 0))
    
    @message_count.setter
    def message_count(self, value: int) -> None:
        """设置消息计数"""
        if self._session_state:
            # 通过直接赋值来设置私有属性（实现类应该支持此操作）
            try:
                object.__setattr__(self._session_state, '_message_count', value)
            except (AttributeError, TypeError):
                pass
            self._sync_state_to_session_data()
        else:
            self._session_data["message_count"] = value
    
    @property
    def checkpoint_count(self) -> int:
        """获取检查点计数"""
        if self._session_state:
            return self._session_state.checkpoint_count
        return int(self._session_data.get("checkpoint_count", 0))
    
    @checkpoint_count.setter
    def checkpoint_count(self, value: int) -> None:
        """设置检查点计数"""
        if self._session_state:
            # 通过直接赋值来设置私有属性（实现类应该支持此操作）
            try:
                object.__setattr__(self._session_state, '_checkpoint_count', value)
            except (AttributeError, TypeError):
                pass
            self._sync_state_to_session_data()
        else:
            self._session_data["checkpoint_count"] = value
    
    def get_session_data(self) -> Dict[str, Any]:
        """获取完整的会话数据"""
        return self._session_data.copy()
    
    def update_session_data(self, new_data: Dict[str, Any]) -> None:
        """更新会话数据
        
        Args:
            new_data: 新的会话数据
        """
        self._session_data.update(new_data)
        
        # 如果有状态对象，同步更新
        if self._session_state:
            if 'state' in new_data:
                self._session_state.set_data("session_data", new_data['state'])
            if 'message_count' in new_data:
                try:
                    object.__setattr__(self._session_state, '_message_count', new_data['message_count'])
                except (AttributeError, TypeError):
                    pass
            if 'checkpoint_count' in new_data:
                try:
                    object.__setattr__(self._session_state, '_checkpoint_count', new_data['checkpoint_count'])
                except (AttributeError, TypeError):
                    pass
            if 'config' in new_data:
                self._session_state.update_config(new_data['config'])
    
    @abstractmethod
    def validate(self) -> bool:
        """验证会话数据的有效性
        
        Returns:
            数据有效返回True，无效返回False
        """
        pass
    
    # 状态管理相关方法
    def _create_default_state(self) -> 'ISessionState':
        """创建默认的会话状态对象"""
        from src.core.state.implementations.session_state import SessionStateImpl
        
        session_id = self.id or self._session_data.get("session_id", "")
        user_id = self._session_data.get("user_id")
        config = self._session_data.get("config", {})
        message_count = self._session_data.get("message_count", 0)
        checkpoint_count = self._session_data.get("checkpoint_count", 0)
        thread_ids = self._session_data.get("thread_ids", [])
        
        return SessionStateImpl(
            session_id=session_id,
            user_id=user_id,
            session_config=config,
            message_count=message_count,
            checkpoint_count=checkpoint_count,
            thread_ids=thread_ids
        )
    
    def _sync_state_to_session_data(self) -> None:
        """将状态对象同步到session_data"""
        if self._session_state:
            state_dict = self._session_state.to_dict()
            self._session_data.update({
                "state": state_dict.get('data', {}),
                "message_count": self._session_state.message_count,
                "checkpoint_count": self._session_state.checkpoint_count,
                "config": self._session_state.session_config,
                "thread_ids": self._session_state.thread_ids,
                "user_id": self._session_state.user_id
            })
    
    def _sync_session_data_to_state(self) -> None:
        """将session_data同步到状态对象"""
        if self._session_state:
            self._session_state.set_data("session_data", self._session_data.get("state", {}))
            try:
                object.__setattr__(self._session_state, '_message_count', self._session_data.get("message_count", 0))
            except (AttributeError, TypeError):
                pass
            try:
                object.__setattr__(self._session_state, '_checkpoint_count', self._session_data.get("checkpoint_count", 0))
            except (AttributeError, TypeError):
                pass
            self._session_state.update_config(self._session_data.get("config", {}))
            
            # 同步线程ID
            thread_ids = self._session_data.get("thread_ids", [])
            try:
                object.__setattr__(self._session_state, '_thread_ids', set(thread_ids))
            except (AttributeError, TypeError):
                pass
    
    def initialize_state(self) -> None:
        """初始化状态对象（如果尚未初始化）"""
        if not self._session_state:
            self._session_state = self._create_default_state()
            self._sync_session_data_to_state()
    
    def save_state(self) -> None:
        """保存状态到状态管理器"""
        if self._session_state and self._session_state_manager:
            self._session_state_manager.save_session_state(self._session_state)
    
    def load_state(self) -> None:
        """从状态管理器加载状态"""
        if self._session_state_manager:
            session_id = self.id or self._session_data.get("session_id", "")
            if session_id:
                loaded_state = self._session_state_manager.get_session_state(session_id)
                if loaded_state:
                    self._session_state = loaded_state
                    self._sync_state_to_session_data()
    
    def increment_message_count(self) -> None:
        """增加消息计数"""
        if self._session_state:
            self._session_state.increment_message_count()
            self._sync_state_to_session_data()
        else:
            current_count = self._session_data.get("message_count", 0)
            self._session_data["message_count"] = current_count + 1
    
    def increment_checkpoint_count(self) -> None:
        """增加检查点计数"""
        if self._session_state:
            self._session_state.increment_checkpoint_count()
            self._sync_state_to_session_data()
        else:
            current_count = self._session_data.get("checkpoint_count", 0)
            self._session_data["checkpoint_count"] = current_count + 1
    
    def add_thread(self, thread_id: str) -> None:
        """添加关联线程"""
        if self._session_state:
            self._session_state.add_thread(thread_id)
            self._sync_state_to_session_data()
        else:
            thread_ids = self._session_data.get("thread_ids", [])
            if thread_id not in thread_ids:
                thread_ids.append(thread_id)
                self._session_data["thread_ids"] = thread_ids
    
    def remove_thread(self, thread_id: str) -> None:
        """移除关联线程"""
        if self._session_state:
            self._session_state.remove_thread(thread_id)
            self._sync_state_to_session_data()
        else:
            thread_ids = self._session_data.get("thread_ids", [])
            if thread_id in thread_ids:
                thread_ids.remove(thread_id)
                self._session_data["thread_ids"] = thread_ids
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新会话配置"""
        if self._session_state:
            self._session_state.update_config(config)
            self._sync_state_to_session_data()
        else:
            current_config = self._session_data.get("config", {})
            current_config.update(config)
            self._session_data["config"] = current_config
    
    def get_session_summary(self) -> Dict[str, Any]:
        """获取会话摘要信息"""
        if self._session_state:
            return self._session_state.get_session_summary()
        else:
            return {
                "session_id": self.id,
                "user_id": self._session_data.get("user_id"),
                "message_count": self.message_count,
                "checkpoint_count": self.checkpoint_count,
                "thread_count": len(self._session_data.get("thread_ids", [])),
                "thread_ids": self._session_data.get("thread_ids", []),
                "config_keys": list(self._session_data.get("config", {}).keys()),
                "state_keys": list(self._session_data.get("state", {}).keys())
            }
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式
        
        Returns:
            会话数据的字典表示
        """
        pass