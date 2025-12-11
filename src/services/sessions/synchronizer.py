"""Session-Thread同步器实现"""

from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from src.interfaces.sessions.association import (
    ISessionThreadAssociationRepository,
    ISessionThreadSynchronizer
)
from interfaces.repository.session import ISessionRepository
from src.interfaces.threads.storage import IThreadRepository
from src.core.sessions.association import SessionThreadAssociation
from src.interfaces.storage.exceptions import StorageError
from src.interfaces.container.exceptions import ValidationError

logger = get_logger(__name__)


class SessionThreadSynchronizer(ISessionThreadSynchronizer):
    """Session-Thread同步器实现"""
    
    def __init__(
        self,
        association_repository: ISessionThreadAssociationRepository,
        session_repository: ISessionRepository,
        thread_repository: IThreadRepository
    ):
        """初始化同步器
        
        Args:
            association_repository: 关联仓储
            session_repository: 会话仓储
            thread_repository: 线程仓储
        """
        self._association_repository = association_repository
        self._session_repository = session_repository
        self._thread_repository = thread_repository
        logger.info("SessionThreadSynchronizer initialized")
    
    async def sync_session_threads(self, session_id: str) -> Dict[str, Any]:
        """同步Session的Thread关联
        
        Args:
            session_id: 会话ID
            
        Returns:
            同步结果统计
        """
        try:
            logger.info(f"Starting sync for session: {session_id}")
            
            # 1. 获取Session中记录的thread_ids
            session = await self._session_repository.get(session_id)
            if not session:
                raise ValidationError(f"Session not found: {session_id}")
            
            recorded_thread_ids = set(session.thread_ids)
            
            # 2. 获取关联表中记录的Thread
            associations = await self._association_repository.list_by_session(session_id)
            active_associations = [assoc for assoc in associations if assoc.is_active]
            associated_thread_ids = {assoc.thread_id for assoc in active_associations}
            
            # 3. 查询实际存在的Thread
            actual_threads = await self._thread_repository.list_by_session(session_id)
            actual_thread_ids = {thread.id for thread in actual_threads}
            
            # 4. 分析差异
            sync_stats: Dict[str, Any] = {
                "session_id": session_id,
                "recorded_threads": len(recorded_thread_ids),
                "associated_threads": len(associated_thread_ids),
                "actual_threads": len(actual_thread_ids),
                "discrepancies": [],
                "fixes_applied": []
            }
            
            # 5. 修复差异
            # 5.1 修复Session中多余的thread_ids
            orphan_thread_ids = recorded_thread_ids - actual_thread_ids
            for thread_id in orphan_thread_ids:
                session.thread_ids.remove(thread_id)
                sync_stats["fixes_applied"].append(f"Removed orphan thread {thread_id} from session")
                sync_stats["discrepancies"].append(f"Orphan thread in session: {thread_id}")
            
            # 5.2 修复Session中缺失的thread_ids
            missing_thread_ids = actual_thread_ids - recorded_thread_ids
            for thread_id in missing_thread_ids:
                session.thread_ids.append(thread_id)
                sync_stats["fixes_applied"].append(f"Added missing thread {thread_id} to session")
                sync_stats["discrepancies"].append(f"Missing thread in session: {thread_id}")
            
            # 5.3 修复关联表中缺失的关联
            for thread in actual_threads:
                if thread.id not in associated_thread_ids:
                    association = SessionThreadAssociation(
                        session_id=session_id,
                        thread_id=thread.id,
                        thread_name=thread.metadata.title or thread.id,
                        metadata={"auto_created": True, "sync_timestamp": datetime.now().isoformat()}
                    )
                    await self._association_repository.create(association)
                    sync_stats["fixes_applied"].append(f"Created missing association for thread {thread.id}")
                    sync_stats["discrepancies"].append(f"Missing association for thread: {thread.id}")
            
            # 5.4 修复关联表中多余的关联
            for association in active_associations:  # type: ignore
                if association.thread_id not in actual_thread_ids:
                    association.deactivate()
                    await self._association_repository.update(association)
                    sync_stats["fixes_applied"].append(f"Deactivated orphan association {association.association_id}")
                    sync_stats["discrepancies"].append(f"Orphan association: {association.association_id}")
            
            # 6. 更新Session
            if sync_stats["fixes_applied"]:
                await self._session_repository.update(session)
                logger.info(f"Session {session_id} synchronized with {len(sync_stats['fixes_applied'])} fixes")
            else:
                logger.info(f"Session {session_id} already synchronized")
            
            sync_stats["sync_timestamp"] = datetime.now().isoformat()
            return sync_stats
            
        except Exception as e:
            logger.error(f"Failed to sync session {session_id}: {e}")
            raise StorageError(f"Session sync failed: {e}")
    
    async def validate_consistency(self, session_id: str) -> List[str]:
        """验证Session-Thread一致性
        
        Args:
            session_id: 会话ID
            
        Returns:
            发现的问题列表
        """
        try:
            issues = []
            
            # 1. 检查Session是否存在
            session = await self._session_repository.get(session_id)
            if not session:
                issues.append(f"Session not found: {session_id}")
                return issues
            
            # 2. 获取相关数据
            recorded_thread_ids = set(session.thread_ids)
            associations = await self._association_repository.list_by_session(session_id)
            active_associations = [assoc for assoc in associations if assoc.is_active]
            associated_thread_ids = {assoc.thread_id for assoc in active_associations}
            actual_threads = await self._thread_repository.list_by_session(session_id)
            actual_thread_ids = {thread.id for thread in actual_threads}
            
            # 3. 检查一致性
            # 3.1 检查Session中的孤儿Thread
            orphan_in_session = recorded_thread_ids - actual_thread_ids
            for thread_id in orphan_in_session:
                issues.append(f"Orphan thread in session: {thread_id}")
            
            # 3.2 检查Session中缺失的Thread
            missing_in_session = actual_thread_ids - recorded_thread_ids
            for thread_id in missing_in_session:
                issues.append(f"Missing thread in session: {thread_id}")
            
            # 3.3 检查关联表中缺失的关联
            for thread in actual_threads:
                if thread.id not in associated_thread_ids:
                    issues.append(f"Missing association for thread: {thread.id}")
            
            # 3.4 检查关联表中多余的关联
            for association in active_associations:
                if association.thread_id not in actual_thread_ids:
                    issues.append(f"Orphan association: {association.association_id}")
            
            # 3.5 检查Thread配置中的session_id一致性
            for thread in actual_threads:
                config_session_id = thread.config.get("session_id")
                if config_session_id and config_session_id != session_id:
                    issues.append(f"Thread {thread.id} has inconsistent session_id in config: {config_session_id}")
            
            # 3.6 检查关联名称一致性
            for association in active_associations:
                thread = next((t for t in actual_threads if t.id == association.thread_id), None)  # type: ignore
                if thread is not None:
                    config_thread_name = thread.metadata.title or thread.id
                    if association.thread_name != config_thread_name:
                        issues.append(f"Association name mismatch for thread {thread.id}: {association.thread_name} vs {config_thread_name}")
            
            logger.info(f"Validation completed for session {session_id}: {len(issues)} issues found")
            return issues
            
        except Exception as e:
            logger.error(f"Failed to validate session {session_id}: {e}")
            raise StorageError(f"Session validation failed: {e}")
    
    async def repair_inconsistencies(self, session_id: str) -> Dict[str, Any]:
        """修复不一致问题
        
        Args:
            session_id: 会话ID
            
        Returns:
            修复结果统计
        """
        try:
            logger.info(f"Starting repair for session: {session_id}")
            
            # 1. 验证一致性
            issues = await self.validate_consistency(session_id)
            
            repair_stats: Dict[str, Any] = {
                "session_id": session_id,
                "issues_found": len(issues),
                "repairs_attempted": 0,
                "repairs_successful": 0,
                "repairs_failed": [],
                "repair_timestamp": datetime.now().isoformat()
            }
            
            if not issues:
                logger.info(f"No issues found for session {session_id}")
                return repair_stats
            
            # 2. 执行修复
            for issue in issues:
                repair_stats["repairs_attempted"] += 1
                
                try:
                    if "Orphan thread in session" in issue:
                        # 修复Session中的孤儿Thread
                        thread_id = issue.split(": ")[1]
                        await self._remove_orphan_thread_from_session(session_id, thread_id)
                        repair_stats["repairs_successful"] += 1
                        
                    elif "Missing thread in session" in issue:
                        # 修复Session中缺失的Thread
                        thread_id = issue.split(": ")[1]
                        await self._add_missing_thread_to_session(session_id, thread_id)
                        repair_stats["repairs_successful"] += 1
                        
                    elif "Missing association for thread" in issue:
                        # 修复缺失的关联
                        thread_id = issue.split(": ")[1]
                        await self._create_missing_association(session_id, thread_id)
                        repair_stats["repairs_successful"] += 1
                        
                    elif "Orphan association" in issue:
                        # 修复多余的关联
                        association_id = issue.split(": ")[1]
                        await self._deactivate_orphan_association(association_id)
                        repair_stats["repairs_successful"] += 1
                        
                    elif "inconsistent session_id in config" in issue:
                        # 修复Thread配置中的session_id
                        thread_id = issue.split(" ")[1]
                        await self._fix_thread_config_session_id(thread_id, session_id)
                        repair_stats["repairs_successful"] += 1
                        
                    elif "Association name mismatch" in issue:
                        # 修复关联名称不匹配
                        thread_id = issue.split(" ")[2]
                        await self._fix_association_name_mismatch(session_id, thread_id)
                        repair_stats["repairs_successful"] += 1
                        
                    else:
                        repair_stats["repairs_failed"].append(f"Unknown issue type: {issue}")
                        
                except Exception as e:
                    repair_stats["repairs_failed"].append(f"Failed to repair '{issue}': {e}")
                    logger.error(f"Failed to repair issue '{issue}': {e}")
            
            logger.info(f"Repair completed for session {session_id}: {repair_stats['repairs_successful']}/{repair_stats['repairs_attempted']} successful")
            return repair_stats
            
        except Exception as e:
            logger.error(f"Failed to repair session {session_id}: {e}")
            raise StorageError(f"Session repair failed: {e}")
    
    # === 私有辅助方法 ===
    
    async def _remove_orphan_thread_from_session(self, session_id: str, thread_id: str) -> None:
        """从Session中移除孤儿Thread"""
        session = await self._session_repository.get(session_id)
        if session and thread_id in session.thread_ids:
            session.thread_ids.remove(thread_id)
            await self._session_repository.update(session)
            logger.debug(f"Removed orphan thread {thread_id} from session {session_id}")
    
    async def _add_missing_thread_to_session(self, session_id: str, thread_id: str) -> None:
        """向Session添加缺失的Thread"""
        session = await self._session_repository.get(session_id)
        if session and thread_id not in session.thread_ids:
            session.thread_ids.append(thread_id)
            await self._session_repository.update(session)
            logger.debug(f"Added missing thread {thread_id} to session {session_id}")
    
    async def _create_missing_association(self, session_id: str, thread_id: str) -> None:
        """创建缺失的关联"""
        thread = await self._thread_repository.get(thread_id)
        if thread:
            association = SessionThreadAssociation(
                session_id=session_id,
                thread_id=thread_id,
                thread_name=thread.metadata.title or thread_id,
                metadata={"auto_created": True, "repair_timestamp": datetime.now().isoformat()}
            )
            await self._association_repository.create(association)
            logger.debug(f"Created missing association for thread {thread_id}")
    
    async def _deactivate_orphan_association(self, association_id: str) -> None:
        """停用孤儿关联"""
        association = await self._association_repository.get(association_id)
        if association:
            association.deactivate()
            await self._association_repository.update(association)
            logger.debug(f"Deactivated orphan association {association_id}")
    
    async def _fix_thread_config_session_id(self, thread_id: str, correct_session_id: str) -> None:
        """修复Thread配置中的session_id"""
        thread = await self._thread_repository.get(thread_id)
        if thread:
            thread.config["session_id"] = correct_session_id
            await self._thread_repository.update(thread)
            logger.debug(f"Fixed session_id in thread {thread_id} config")
    
    async def _fix_association_name_mismatch(self, session_id: str, thread_id: str) -> None:
        """修复关联名称不匹配"""
        thread = await self._thread_repository.get(thread_id)
        if thread:
            association = await self._association_repository.get_by_session_and_thread(session_id, thread_id)
            if association:
                correct_name = thread.metadata.title or thread_id
                association.thread_name = correct_name
                association.update_metadata({"repair_timestamp": datetime.now().isoformat()})
                await self._association_repository.update(association)
                logger.debug(f"Fixed association name for thread {thread_id}")