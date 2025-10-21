"""TUI会话处理器"""

from typing import Optional, Dict, Any, Callable, List
from src.session.manager import ISessionManager


class SessionHandler:
    """会话处理器，专门处理会话相关操作"""
    
    def __init__(self, session_manager: Optional[ISessionManager] = None) -> None:
        """初始化会话处理器
        
        Args:
            session_manager: 会话管理器
        """
        self.session_manager = session_manager
        
        # 会话事件回调
        self.session_created_callbacks: List[Callable[[str], None]] = []
        self.session_loaded_callbacks: List[Callable[[str], None]] = []
        self.session_saved_callbacks: List[Callable[[str], None]] = []
        self.session_deleted_callbacks: List[Callable[[str], None]] = []
    
    def create_session(self, workflow_config: str, agent_config: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """创建新会话
        
        Args:
            workflow_config: 工作流配置
            agent_config: 代理配置
            
        Returns:
            str: 会话ID，失败返回None
        """
        if not self.session_manager:
            return None
        
        try:
            session_id = self.session_manager.create_session(
                workflow_config_path=workflow_config,
                agent_config=agent_config
            )
            
            if session_id:
                # 触发创建回调
                self._trigger_session_created_callbacks(session_id)
            
            return session_id
        except Exception as e:
            print(f"创建会话失败: {e}")
            return None
    
    def load_session(self, session_id: str) -> Optional[tuple]:
        """加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            tuple: (workflow, state)，失败返回None
        """
        if not self.session_manager:
            return None
        
        try:
            workflow, state = self.session_manager.restore_session(session_id)
            
            if workflow and state:
                # 触发加载回调
                self._trigger_session_loaded_callbacks(session_id)
            
            return workflow, state
        except Exception as e:
            print(f"加载会话失败: {e}")
            return None
    
    def save_session(self, session_id: str, workflow: Any, state: Any) -> bool:
        """保存会话
        
        Args:
            session_id: 会话ID
            workflow: 工作流对象
            state: 状态对象
            
        Returns:
            bool: 保存是否成功
        """
        if not self.session_manager:
            return False
        
        try:
            self.session_manager.save_session(session_id, workflow, state)
            
            # 触发保存回调
            self._trigger_session_saved_callbacks(session_id)
            
            return True
        except Exception as e:
            print(f"保存会话失败: {e}")
            return False
    
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        if not self.session_manager:
            return False
        
        try:
            success = self.session_manager.delete_session(session_id)
            
            if success:
                # 触发删除回调
                self._trigger_session_deleted_callbacks(session_id)
            
            return success
        except Exception as e:
            print(f"删除会话失败: {e}")
            return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """列出所有会话
        
        Returns:
            List[Dict[str, Any]]: 会话列表
        """
        if not self.session_manager:
            return []
        
        try:
            return self.session_manager.list_sessions()
        except Exception as e:
            print(f"列出会话失败: {e}")
            return []
    
    def get_session_info(self, session_id: str) -> Optional[Dict[str, Any]]:
        """获取会话信息
        
        Args:
            session_id: 会话ID
            
        Returns:
            Dict[str, Any]: 会话信息，失败返回None
        """
        if not self.session_manager:
            return None
        
        try:
            return self.session_manager.get_session_info(session_id)
        except Exception as e:
            print(f"获取会话信息失败: {e}")
            return None
    
    def session_exists(self, session_id: str) -> bool:
        """检查会话是否存在
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 会话是否存在
        """
        if not self.session_manager:
            return False
        
        try:
            return self.session_manager.session_exists(session_id)
        except Exception as e:
            print(f"检查会话存在性失败: {e}")
            return False
    
    def register_session_created_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话创建回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.session_created_callbacks.append(callback)
    
    def register_session_loaded_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话加载回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.session_loaded_callbacks.append(callback)
    
    def register_session_saved_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话保存回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.session_saved_callbacks.append(callback)
    
    def register_session_deleted_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话删除回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.session_deleted_callbacks.append(callback)
    
    def unregister_session_created_callback(self, callback: Callable[[str], None]) -> bool:
        """取消注册会话创建回调
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        try:
            self.session_created_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def unregister_session_loaded_callback(self, callback: Callable[[str], None]) -> bool:
        """取消注册会话加载回调
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        try:
            self.session_loaded_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def unregister_session_saved_callback(self, callback: Callable[[str], None]) -> bool:
        """取消注册会话保存回调
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        try:
            self.session_saved_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def unregister_session_deleted_callback(self, callback: Callable[[str], None]) -> bool:
        """取消注册会话删除回调
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        try:
            self.session_deleted_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def _trigger_session_created_callbacks(self, session_id: str) -> None:
        """触发会话创建回调
        
        Args:
            session_id: 会话ID
        """
        for callback in self.session_created_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                print(f"会话创建回调错误: {e}")
    
    def _trigger_session_loaded_callbacks(self, session_id: str) -> None:
        """触发会话加载回调
        
        Args:
            session_id: 会话ID
        """
        for callback in self.session_loaded_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                print(f"会话加载回调错误: {e}")
    
    def _trigger_session_saved_callbacks(self, session_id: str) -> None:
        """触发会话保存回调
        
        Args:
            session_id: 会话ID
        """
        for callback in self.session_saved_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                print(f"会话保存回调错误: {e}")
    
    def _trigger_session_deleted_callbacks(self, session_id: str) -> None:
        """触发会话删除回调
        
        Args:
            session_id: 会话ID
        """
        for callback in self.session_deleted_callbacks:
            try:
                callback(session_id)
            except Exception as e:
                print(f"会话删除回调错误: {e}")
    
    def get_session_statistics(self) -> Dict[str, Any]:
        """获取会话统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        sessions = self.list_sessions()
        
        total_sessions = len(sessions)
        active_sessions = len([s for s in sessions if s.get("active", False)])
        
        # 计算会话年龄统计
        import time
        current_time = time.time()
        ages = []
        for session in sessions:
            created_time = session.get("created_time", 0)
            if created_time:
                age_seconds = current_time - created_time
                ages.append(age_seconds)
        
        avg_age = sum(ages) / len(ages) if ages else 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "average_age_seconds": avg_age,
            "oldest_session_age": max(ages) if ages else 0,
            "newest_session_age": min(ages) if ages else 0
        }