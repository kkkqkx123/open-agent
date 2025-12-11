"""Session-Thread事务管理实现"""

from src.interfaces.dependency_injection import get_logger
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadTransaction
)
from interfaces.repository.session import ISessionRepository
from src.interfaces.threads.storage import IThreadRepository
from src.interfaces.threads.service import IThreadService
from src.core.sessions.association import SessionThreadAssociation
from src.interfaces.container.exceptions import ValidationError
from src.interfaces.storage.exceptions import StorageError

logger = get_logger(__name__)


class SessionThreadTransaction(ISessionThreadTransaction):
    """Session-Thread事务管理实现"""
    
    def __init__(
        self,
        association_repository: ISessionThreadAssociationRepository,
        session_repository: ISessionRepository,
        thread_repository: IThreadRepository,
        thread_service: IThreadService
    ):
        """初始化事务管理器
        
        Args:
            association_repository: 关联仓储
            session_repository: 会话仓储
            thread_repository: 线程仓储
            thread_service: 线程服务
        """
        self._association_repository = association_repository
        self._session_repository = session_repository
        self._thread_repository = thread_repository
        self._thread_service = thread_service
        logger.info("SessionThreadTransaction initialized")
    
    async def create_thread_with_session(
        self,
        session_id: str,
        thread_config: Dict[str, Any],
        thread_name: str
    ) -> str:
        """原子性地创建Thread并建立Session关联
        
        Args:
            session_id: 会话ID
            thread_config: 线程配置
            thread_name: 线程名称
            
        Returns:
            创建的Thread ID
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        # 记录操作开始
        operation_id = str(uuid.uuid4())
        logger.info(f"Starting transaction {operation_id}: create_thread_with_session")
        
        # 保存原始状态用于回滚
        rollback_data = {}
        
        try:
            # 1. 验证Session存在
            session = await self._session_repository.get(session_id)
            if not session:
                raise ValidationError(f"Session not found: {session_id}")
            
            rollback_data["session_original"] = session.to_dict()
            
            # 2. 检查Thread名称是否已存在于Session中
            existing_associations = await self._association_repository.list_by_session(session_id)
            for assoc in existing_associations:
                if assoc.is_active and assoc.thread_name == thread_name:
                    raise ValidationError(f"Thread name '{thread_name}' already exists in session {session_id}")
            
            # 3. 准备Thread配置
            thread_config = thread_config.copy()
            thread_config["session_id"] = session_id
            thread_config["thread_name"] = thread_name
            
            # 4. 创建Thread
            thread_id = await self._thread_service.create_thread_with_session(thread_config, session_id)
            logger.debug(f"Created thread {thread_id} for session {session_id}")
            
            # 5. 验证Thread创建成功
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise StorageError(f"Thread creation failed: {thread_id}")
            
            rollback_data["thread_created"] = thread_id
            
            # 6. 创建关联
            association = SessionThreadAssociation(
                session_id=session_id,
                thread_id=thread_id,
                thread_name=thread_name,
                metadata={
                    "operation_id": operation_id,
                    "created_by": "transaction",
                    "transaction_timestamp": datetime.now().isoformat()
                }
            )
            
            association_created = await self._association_repository.create(association)
            if not association_created:
                raise StorageError(f"Failed to create association for thread {thread_id}")
            
            rollback_data["association_created"] = association.association_id
            logger.debug(f"Created association {association.association_id}")
            
            # 7. 更新Session的thread_ids列表
            if thread_id not in session.thread_ids:
                session.thread_ids.append(thread_id)
                session.update_timestamp()
                session_updated = await self._session_repository.update(session)
                if not session_updated:
                    raise StorageError(f"Failed to update session {session_id}")
                
                rollback_data["session_updated"] = True
                logger.debug(f"Updated session {session_id} with thread {thread_id}")
            
            logger.info(f"Transaction {operation_id} completed successfully: thread {thread_id}")
            return thread_id
            
        except Exception as e:
            logger.error(f"Transaction {operation_id} failed: {e}")
            await self._rollback_create_thread_with_session(operation_id, rollback_data)
            raise StorageError(f"Transaction failed: {e}")
    
    async def remove_thread_from_session(
        self,
        session_id: str,
        thread_id: str
    ) -> bool:
        """原子性地从Session中移除Thread
        
        Args:
            session_id: 会话ID
            thread_id: 线程ID
            
        Returns:
            是否移除成功
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        operation_id = str(uuid.uuid4())
        logger.info(f"Starting transaction {operation_id}: remove_thread_from_session")
        
        rollback_data = {}
        
        try:
            # 1. 验证Session存在
            session = await self._session_repository.get(session_id)
            if not session:
                raise ValidationError(f"Session not found: {session_id}")
            
            rollback_data["session_original"] = session.to_dict()
            
            # 2. 验证Thread存在
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValidationError(f"Thread not found: {thread_id}")
            
            # 3. 查找关联
            association = await self._association_repository.get_by_session_and_thread(session_id, thread_id)
            if not association:
                raise ValidationError(f"Association not found for session {session_id} and thread {thread_id}")
            
            rollback_data["association_original"] = association.to_dict()
            
            # 4. 停用关联
            association.deactivate()
            association.update_metadata({
                "operation_id": operation_id,
                "deactivated_by": "transaction",
                "transaction_timestamp": datetime.now().isoformat()
            })
            
            association_updated = await self._association_repository.update(association)
            if not association_updated:
                raise StorageError(f"Failed to update association {association.association_id}")
            
            rollback_data["association_deactivated"] = True
            logger.debug(f"Deactivated association {association.association_id}")
            
            # 5. 从Session中移除thread_id
            if thread_id in session.thread_ids:
                session.thread_ids.remove(thread_id)
                session.update_timestamp()
                session_updated = await self._session_repository.update(session)
                if not session_updated:
                    raise StorageError(f"Failed to update session {session_id}")
                
                rollback_data["session_updated"] = True
                logger.debug(f"Removed thread {thread_id} from session {session_id}")
            
            # 6. 可选：删除Thread（根据业务需求）
            # 这里选择保留Thread，只是解除关联
            
            logger.info(f"Transaction {operation_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Transaction {operation_id} failed: {e}")
            await self._rollback_remove_thread_from_session(operation_id, rollback_data)
            raise StorageError(f"Transaction failed: {e}")
    
    async def transfer_thread_between_sessions(
        self,
        thread_id: str,
        from_session_id: str,
        to_session_id: str,
        new_thread_name: Optional[str] = None
    ) -> bool:
        """原子性地在线程间转移Thread
        
        Args:
            thread_id: 线程ID
            from_session_id: 源会话ID
            to_session_id: 目标会话ID
            new_thread_name: 新线程名称
            
        Returns:
            是否转移成功
            
        Raises:
            SessionThreadException: 操作失败时抛出
        """
        operation_id = str(uuid.uuid4())
        logger.info(f"Starting transaction {operation_id}: transfer_thread_between_sessions")
        
        rollback_data = {}
        
        try:
            # 1. 验证所有实体存在
            from_session = await self._session_repository.get(from_session_id)
            if not from_session:
                raise ValidationError(f"Source session not found: {from_session_id}")
            
            to_session = await self._session_repository.get(to_session_id)
            if not to_session:
                raise ValidationError(f"Target session not found: {to_session_id}")
            
            thread = await self._thread_repository.get(thread_id)
            if not thread:
                raise ValidationError(f"Thread not found: {thread_id}")
            
            # 2. 查找现有关联
            old_association = await self._association_repository.get_by_session_and_thread(
                from_session_id, thread_id
            )
            if not old_association:
                raise ValidationError(f"Thread {thread_id} not associated with session {from_session_id}")
            
            # 3. 检查目标Session中的名称冲突
            if new_thread_name:
                existing_associations = await self._association_repository.list_by_session(to_session_id)
                for assoc in existing_associations:
                    if assoc.is_active and assoc.thread_name == new_thread_name:
                        raise ValidationError(f"Thread name '{new_thread_name}' already exists in target session")
            else:
                new_thread_name = old_association.thread_name
            
            # 保存原始状态
            rollback_data.update({
                "from_session_original": from_session.to_dict(),
                "to_session_original": to_session.to_dict(),
                "thread_original": thread.to_dict(),
                "old_association_original": old_association.to_dict()
            })
            
            # 4. 停用旧关联
            old_association.deactivate()
            old_association.update_metadata({
                "operation_id": operation_id,
                "transferred_from": from_session_id,
                "transferred_to": to_session_id,
                "transaction_timestamp": datetime.now().isoformat()
            })
            
            old_association_updated = await self._association_repository.update(old_association)
            if not old_association_updated:
                raise StorageError(f"Failed to update old association {old_association.association_id}")
            
            rollback_data["old_association_deactivated"] = True
            logger.debug(f"Deactivated old association {old_association.association_id}")
            
            # 5. 创建新关联
            new_association = SessionThreadAssociation(
                session_id=to_session_id,
                thread_id=thread_id,
                thread_name=new_thread_name,
                metadata={
                    "operation_id": operation_id,
                    "transferred_from": from_session_id,
                    "created_by": "transaction",
                    "transaction_timestamp": datetime.now().isoformat()
                }
            )
            
            new_association_created = await self._association_repository.create(new_association)
            if not new_association_created:
                raise StorageError(f"Failed to create new association for thread {thread_id}")
            
            rollback_data["new_association_created"] = new_association.association_id
            logger.debug(f"Created new association {new_association.association_id}")
            
            # 6. 更新Thread配置
            thread.config["session_id"] = to_session_id
            if new_thread_name != old_association.thread_name:
                # ThreadMetadata 是 Pydantic BaseModel，需要使用 model_copy 或直接更新属性
                thread.metadata.title = new_thread_name
            
            thread_updated = await self._thread_repository.update(thread)
            if not thread_updated:
                raise StorageError(f"Failed to update thread {thread_id}")
            
            rollback_data["thread_updated"] = True
            logger.debug(f"Updated thread {thread_id} configuration")
            
            # 7. 更新源Session
            if thread_id in from_session.thread_ids:
                from_session.thread_ids.remove(thread_id)
                from_session.update_timestamp()
                from_session_updated = await self._session_repository.update(from_session)
                if not from_session_updated:
                    raise StorageError(f"Failed to update source session {from_session_id}")
                
                rollback_data["from_session_updated"] = True
                logger.debug(f"Removed thread {thread_id} from source session {from_session_id}")
            
            # 8. 更新目标Session
            if thread_id not in to_session.thread_ids:
                to_session.thread_ids.append(thread_id)
                to_session.update_timestamp()
                to_session_updated = await self._session_repository.update(to_session)
                if not to_session_updated:
                    raise StorageError(f"Failed to update target session {to_session_id}")
                
                rollback_data["to_session_updated"] = True
                logger.debug(f"Added thread {thread_id} to target session {to_session_id}")
            
            logger.info(f"Transaction {operation_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Transaction {operation_id} failed: {e}")
            await self._rollback_transfer_thread_between_sessions(operation_id, rollback_data)
            raise StorageError(f"Transaction failed: {e}")
    
    # === 私有回滚方法 ===
    
    async def _rollback_create_thread_with_session(self, operation_id: str, rollback_data: Dict[str, Any]) -> None:
        """回滚创建Thread操作"""
        logger.warning(f"Rolling back transaction {operation_id}")
        
        try:
            # 回滚Session更新
            if "session_updated" in rollback_data and rollback_data["session_updated"]:
                session_original = rollback_data["session_original"]
                from src.core.sessions.entities import Session
                session = Session.from_dict(session_original)
                await self._session_repository.update(session)
                logger.debug(f"Rolled back session update")
            
            # 回滚关联创建
            if "association_created" in rollback_data:
                association_id = rollback_data["association_created"]
                await self._association_repository.delete(association_id)
                logger.debug(f"Rolled back association creation: {association_id}")
            
            # 回滚Thread创建
            if "thread_created" in rollback_data:
                thread_id = rollback_data["thread_created"]
                await self._thread_repository.delete(thread_id)
                logger.debug(f"Rolled back thread creation: {thread_id}")
                
        except Exception as e:
            logger.error(f"Rollback failed for transaction {operation_id}: {e}")
    
    async def _rollback_remove_thread_from_session(self, operation_id: str, rollback_data: Dict[str, Any]) -> None:
        """回滚移除Thread操作"""
        logger.warning(f"Rolling back transaction {operation_id}")
        
        try:
            # 回滚Session更新
            if "session_updated" in rollback_data and rollback_data["session_updated"]:
                session_original = rollback_data["session_original"]
                from src.core.sessions.entities import Session
                session = Session.from_dict(session_original)
                await self._session_repository.update(session)
                logger.debug(f"Rolled back session update")
            
            # 回滚关联停用
            if "association_deactivated" in rollback_data and rollback_data["association_deactivated"]:
                association_original = rollback_data["association_original"]
                from src.core.sessions.association import SessionThreadAssociation
                association = SessionThreadAssociation.from_dict(association_original)
                await self._association_repository.update(association)
                logger.debug(f"Rolled back association deactivation: {association.association_id}")
                
        except Exception as e:
            logger.error(f"Rollback failed for transaction {operation_id}: {e}")
    
    async def _rollback_transfer_thread_between_sessions(self, operation_id: str, rollback_data: Dict[str, Any]) -> None:
        """回滚Thread转移操作"""
        logger.warning(f"Rolling back transaction {operation_id}")
        
        try:
            # 回滚目标Session更新
            if "to_session_updated" in rollback_data and rollback_data["to_session_updated"]:
                to_session_original = rollback_data["to_session_original"]
                from src.core.sessions.entities import Session
                to_session = Session.from_dict(to_session_original)
                await self._session_repository.update(to_session)
                logger.debug(f"Rolled back target session update")
            
            # 回滚源Session更新
            if "from_session_updated" in rollback_data and rollback_data["from_session_updated"]:
                from_session_original = rollback_data["from_session_original"]
                from src.core.sessions.entities import Session
                from_session = Session.from_dict(from_session_original)
                await self._session_repository.update(from_session)
                logger.debug(f"Rolled back source session update")
            
            # 回滚Thread更新
            if "thread_updated" in rollback_data and rollback_data["thread_updated"]:
                thread_original = rollback_data["thread_original"]
                from src.core.threads.entities import Thread
                thread = Thread.from_dict(thread_original)
                await self._thread_repository.update(thread)
                logger.debug(f"Rolled back thread update")
            
            # 回滚新关联创建
            if "new_association_created" in rollback_data:
                association_id = rollback_data["new_association_created"]
                await self._association_repository.delete(association_id)
                logger.debug(f"Rolled back new association creation: {association_id}")
            
            # 回滚旧关联停用
            if "old_association_deactivated" in rollback_data and rollback_data["old_association_deactivated"]:
                association_original = rollback_data["old_association_original"]
                from src.core.sessions.association import SessionThreadAssociation
                association = SessionThreadAssociation.from_dict(association_original)
                await self._association_repository.update(association)
                logger.debug(f"Rolled back old association deactivation: {association.association_id}")
                
        except Exception as e:
            logger.error(f"Rollback failed for transaction {operation_id}: {e}")