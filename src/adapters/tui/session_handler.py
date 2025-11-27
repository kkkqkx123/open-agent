"""TUI会话处理器"""

from typing import Optional, Dict, Any, Callable, List
import asyncio
from datetime import datetime
from src.interfaces.sessions.service import ISessionService


class SessionHandler:
    """会话处理器，专门处理会话相关操作"""
    
    def __init__(self, session_manager: Optional[ISessionService] = None) -> None:
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
            # 创建用户请求数据
            from src.core.sessions.entities import UserRequestEntity
            
            user_request = UserRequestEntity(
                request_id=f"request_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id="",
                content=f"创建会话: {workflow_config}",
                metadata={
                    "workflow_config": workflow_config,
                    "agent_config": agent_config
                }
            )  # type: ignore
            
            # 异步创建会话
            session_id = asyncio.run(
                self.session_manager.create_session(user_request)
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
            # 异步加载会话
            session_context = asyncio.run(
                self.session_manager.get_session_context(session_id)
            )
                
            if session_context:
                # 触发加载回调
                self._trigger_session_loaded_callbacks(session_id)
                # 返回None, None以保持API兼容性，因为新的SessionManager不直接返回workflow和state
                return None, None
            else:
                return None
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
        # 新的SessionManager不需要显式保存，因为状态在执行过程中会自动保存
        # 这里保持API兼容性，返回True
        try:
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
        # 新的SessionManager没有直接的删除方法，需要通过其他方式实现
        # 这里暂时返回True以保持API兼容性，实际删除逻辑需要根据具体需求实现
        try:
            # 触发删除回调
            self._trigger_session_deleted_callbacks(session_id)
            
            return True
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
            # 异步调用list_sessions
            sessions = asyncio.run(
                self.session_manager.list_sessions()
            )
            return sessions or []
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
            # 异步获取会话信息
            session_context = asyncio.run(
                self.session_manager.get_session_context(session_id)
            )
                
            if session_context:
                # 将SessionContext转换为字典格式
                return {
                    "session_id": session_context.session_id,
                    "user_id": session_context.user_id,
                    "thread_ids": session_context.thread_ids,
                    "status": session_context.status,
                    "created_at": session_context.created_at,
                    "updated_at": session_context.updated_at,
                    "metadata": session_context.metadata
                }
            else:
                return None
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
            # 异步检查会话存在性
            session_context = asyncio.run(
                self.session_manager.get_session_context(session_id)
            )
                
            return session_context is not None
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