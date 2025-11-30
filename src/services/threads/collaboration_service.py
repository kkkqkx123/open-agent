"""线程协作服务"""

import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging

from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.threads.collaboration import IThreadCollaborationService
from src.core.common.exceptions import ValidationError, StorageNotFoundError as EntityNotFoundError
from .base_service import BaseThreadService

logger = logging.getLogger(__name__)


class ThreadCollaborationService(BaseThreadService, IThreadCollaborationService):
    """线程协作服务 - 负责线程间的协作和交互"""
    
    def __init__(
        self,
        thread_repository: IThreadRepository,
    ):
        """初始化协作服务
        
        Args:
            thread_repository: 线程仓储接口
        """
        super().__init__(thread_repository)
        self._collaboration_store: Dict[str, Dict[str, Any]] = {}  # 简化的协作存储，实际应用中应使用数据库
    
    async def create_collaborative_thread(
        self, 
        graph_id: str, 
        participants: List[str], 
        collaboration_config: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """创建协作线程
        
        Args:
            graph_id: 关联的图ID
            participants: 参与者列表
            collaboration_config: 协作配置
            metadata: 线程元数据
            
        Returns:
            新创建的协作线程ID
        """
        try:
            self._log_operation("create_collaborative_thread", metadata=metadata, 
                              participants=participants)
            
            if not participants:
                raise ValidationError("Participants list cannot be empty")
            
            # 创建基础线程
            from src.core.threads.interfaces import IThreadCore
            from src.core.threads.entities import ThreadType
            
            # 这里需要注入thread_core，简化处理
            thread_id = str(uuid.uuid4())
            
            # 创建协作元数据
            collaboration_metadata = {
                "is_collaborative": True,
                "participants": participants,
                "collaboration_config": collaboration_config or {},
                "created_at": datetime.now().isoformat(),
                **(metadata or {})
            }
            
            # 存储协作信息
            self._collaboration_store[thread_id] = {
                "thread_id": thread_id,
                "participants": {p: {"role": "member", "permissions": ["read", "write"]} for p in participants},
                "collaboration_config": collaboration_config or {},
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            
            return thread_id
            
        except Exception as e:
            self._handle_exception(e, "create collaborative thread")
            raise
    
    async def add_participant(self, thread_id: str, participant_id: str, role: str) -> bool:
        """添加参与者
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            role: 参与者角色
            
        Returns:
            添加成功返回True，失败返回False
        """
        try:
            self._log_operation("add_participant", thread_id, 
                              participant_id=participant_id, role=role)
            
            # 验证线程存在
            await self._validate_thread_exists(thread_id)
            
            # 获取协作信息
            collaboration_info = self._collaboration_store.get(thread_id)
            if not collaboration_info:
                raise ValidationError(f"Thread {thread_id} is not a collaborative thread")
            
            # 添加参与者
            collaboration_info["participants"][participant_id] = {
                "role": role,
                "permissions": self._get_default_permissions(role),
                "joined_at": datetime.now()
            }
            collaboration_info["updated_at"] = datetime.now()
            
            return True
            
        except Exception as e:
            self._handle_exception(e, "add participant")
            return False
    
    async def remove_participant(self, thread_id: str, participant_id: str) -> bool:
        """移除参与者
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            
        Returns:
            移除成功返回True，失败返回False
        """
        try:
            self._log_operation("remove_participant", thread_id, participant_id=participant_id)
            
            # 验证线程存在
            await self._validate_thread_exists(thread_id)
            
            # 获取协作信息
            collaboration_info = self._collaboration_store.get(thread_id)
            if not collaboration_info:
                raise ValidationError(f"Thread {thread_id} is not a collaborative thread")
            
            # 移除参与者
            if participant_id in collaboration_info["participants"]:
                del collaboration_info["participants"][participant_id]
                collaboration_info["updated_at"] = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            self._handle_exception(e, "remove participant")
            return False
    
    async def get_thread_participants(self, thread_id: str) -> List[Dict[str, Any]]:
        """获取线程的参与者
        
        Args:
            thread_id: 线程ID
            
        Returns:
            参与者信息列表
        """
        try:
            self._log_operation("get_thread_participants", thread_id)
            
            # 验证线程存在
            await self._validate_thread_exists(thread_id)
            
            # 获取协作信息
            collaboration_info = self._collaboration_store.get(thread_id)
            if not collaboration_info:
                return []
            
            # 返回参与者信息
            participants = []
            for participant_id, info in collaboration_info["participants"].items():
                participants.append({
                    "participant_id": participant_id,
                    "role": info["role"],
                    "permissions": info["permissions"],
                    "joined_at": info.get("joined_at", datetime.now()).isoformat()
                })
            
            return participants
            
        except Exception as e:
            self._handle_exception(e, "get thread participants")
            return []
    
    async def update_participant_role(self, thread_id: str, participant_id: str, new_role: str) -> bool:
        """更新参与者角色
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            new_role: 新角色
            
        Returns:
            更新成功返回True，失败返回False
        """
        try:
            self._log_operation("update_participant_role", thread_id, 
                              participant_id=participant_id, new_role=new_role)
            
            # 验证线程存在
            await self._validate_thread_exists(thread_id)
            
            # 获取协作信息
            collaboration_info = self._collaboration_store.get(thread_id)
            if not collaboration_info:
                raise ValidationError(f"Thread {thread_id} is not a collaborative thread")
            
            # 更新参与者角色
            if participant_id in collaboration_info["participants"]:
                collaboration_info["participants"][participant_id]["role"] = new_role
                collaboration_info["participants"][participant_id]["permissions"] = self._get_default_permissions(new_role)
                collaboration_info["updated_at"] = datetime.now()
                return True
            
            return False
            
        except Exception as e:
            self._handle_exception(e, "update participant role")
            return False
    
    async def get_thread_permissions(self, thread_id: str, participant_id: str) -> Dict[str, Any]:
        """获取参与者在线程中的权限
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            
        Returns:
            权限信息字典
        """
        try:
            self._log_operation("get_thread_permissions", thread_id, participant_id=participant_id)
            
            # 验证线程存在
            await self._validate_thread_exists(thread_id)
            
            # 获取协作信息
            collaboration_info = self._collaboration_store.get(thread_id)
            if not collaboration_info:
                return {}
            
            # 返回参与者权限
            participant_info = collaboration_info["participants"].get(participant_id)
            if not participant_info:
                return {}
            
            return {
                "participant_id": participant_id,
                "role": participant_info["role"],
                "permissions": participant_info["permissions"]
            }
            
        except Exception as e:
            self._handle_exception(e, "get thread permissions")
            return {}
    
    async def can_participant_access(self, thread_id: str, participant_id: str, action: str) -> bool:
        """检查参与者是否可以执行指定操作
        
        Args:
            thread_id: 线程ID
            participant_id: 参与者ID
            action: 操作类型
            
        Returns:
            有权限返回True，否则返回False
        """
        try:
            self._log_operation("can_participant_access", thread_id, 
                              participant_id=participant_id, action=action)
            
            # 获取参与者权限
            permissions = await self.get_thread_permissions(thread_id, participant_id)
            if not permissions:
                return False
            
            # 检查权限
            return action in permissions.get("permissions", [])
            
        except Exception:
            return False
    
    def _get_default_permissions(self, role: str) -> List[str]:
        """获取角色的默认权限
        
        Args:
            role: 角色名称
            
        Returns:
            权限列表
        """
        role_permissions = {
            "owner": ["read", "write", "delete", "manage_participants", "manage_permissions"],
            "admin": ["read", "write", "manage_participants"],
            "editor": ["read", "write"],
            "viewer": ["read"],
            "member": ["read", "write"]
        }
        
        return role_permissions.get(role, ["read"])