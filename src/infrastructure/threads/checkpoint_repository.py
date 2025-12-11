"""Thread检查点仓储实现

实现Thread检查点的数据持久化，遵循仓储模式。
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import asyncio
from abc import ABC, abstractmethod

from src.interfaces.dependency_injection import get_logger
from src.core.threads.checkpoints.models import ThreadCheckpoint, CheckpointStatistics, CheckpointStatus


logger = get_logger(__name__)


class ThreadCheckpointRepository:
    """Thread检查点仓储实现
    
    基于内存的简单实现，可以根据需要替换为数据库实现。
    """
    
    def __init__(self):
        """初始化仓储"""
        self._checkpoints: Dict[str, ThreadCheckpoint] = {}
        self._thread_index: Dict[str, List[str]] = {}
        logger.info("ThreadCheckpointRepository initialized")
    
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点"""
        try:
            # 保存到主存储
            self._checkpoints[checkpoint.id] = checkpoint
            
            # 更新线程索引
            if checkpoint.thread_id not in self._thread_index:
                self._thread_index[checkpoint.thread_id] = []
            
            if checkpoint.id not in self._thread_index[checkpoint.thread_id]:
                self._thread_index[checkpoint.thread_id].append(checkpoint.id)
            
            logger.debug(f"Saved checkpoint {checkpoint.id} for thread {checkpoint.thread_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint.id}: {e}")
            return False
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """根据ID查找检查点"""
        try:
            return self._checkpoints.get(checkpoint_id)
            
        except Exception as e:
            logger.error(f"Failed to find checkpoint {checkpoint_id}: {e}")
            return None
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """根据线程ID查找检查点"""
        try:
            checkpoint_ids = self._thread_index.get(thread_id, [])
            checkpoints = []
            
            for checkpoint_id in checkpoint_ids:
                checkpoint = self._checkpoints.get(checkpoint_id)
                if checkpoint:
                    checkpoints.append(checkpoint)
            
            # 按创建时间倒序排列
            checkpoints.sort(key=lambda x: x.created_at, reverse=True)
            
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints for thread {thread_id}: {e}")
            return []
    
    async def find_expired(self) -> List[ThreadCheckpoint]:
        """查找过期的检查点"""
        try:
            expired_checkpoints = []
            
            for checkpoint in self._checkpoints.values():
                if checkpoint.is_expired():
                    expired_checkpoints.append(checkpoint)
            
            return expired_checkpoints
            
        except Exception as e:
            logger.error(f"Failed to find expired checkpoints: {e}")
            return []
    
    async def update(self, checkpoint: ThreadCheckpoint) -> bool:
        """更新检查点"""
        try:
            if checkpoint.id in self._checkpoints:
                self._checkpoints[checkpoint.id] = checkpoint
                logger.debug(f"Updated checkpoint {checkpoint.id}")
                return True
            else:
                logger.warning(f"Checkpoint {checkpoint.id} not found for update")
                return False
                
        except Exception as e:
            logger.error(f"Failed to update checkpoint {checkpoint.id}: {e}")
            return False
    
    async def delete(self, checkpoint_id: str) -> bool:
        """删除检查点"""
        try:
            checkpoint = self._checkpoints.get(checkpoint_id)
            if checkpoint:
                # 从主存储删除
                del self._checkpoints[checkpoint_id]
                
                # 从线程索引删除
                if checkpoint.thread_id in self._thread_index:
                    if checkpoint_id in self._thread_index[checkpoint.thread_id]:
                        self._thread_index[checkpoint.thread_id].remove(checkpoint_id)
                    
                    # 如果线程没有检查点了，删除线程索引
                    if not self._thread_index[checkpoint.thread_id]:
                        del self._thread_index[checkpoint.thread_id]
                
                logger.debug(f"Deleted checkpoint {checkpoint_id}")
                return True
            else:
                logger.warning(f"Checkpoint {checkpoint_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id}: {e}")
            return False
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计线程的检查点数量"""
        try:
            return len(self._thread_index.get(thread_id, []))
            
        except Exception as e:
            logger.error(f"Failed to count checkpoints for thread {thread_id}: {e}")
            return 0
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> CheckpointStatistics:
        """获取统计信息"""
        try:
            if thread_id:
                checkpoints = await self.find_by_thread(thread_id)
            else:
                checkpoints = list(self._checkpoints.values())
            
            if not checkpoints:
                return CheckpointStatistics()
            
            # 基本统计
            total_checkpoints = len(checkpoints)
            active_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.ACTIVE)
            expired_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.EXPIRED)
            corrupted_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.CORRUPTED)
            archived_checkpoints = sum(1 for cp in checkpoints if cp.status == CheckpointStatus.ARCHIVED)
            
            # 大小统计
            total_size_bytes = sum(cp.size_bytes for cp in checkpoints)
            average_size_bytes = total_size_bytes / total_checkpoints if total_checkpoints > 0 else 0
            largest_checkpoint_bytes = max(cp.size_bytes for cp in checkpoints) if checkpoints else 0
            smallest_checkpoint_bytes = min(cp.size_bytes for cp in checkpoints) if checkpoints else 0
            
            # 恢复统计
            total_restores = sum(cp.restore_count for cp in checkpoints)
            average_restores = total_restores / total_checkpoints if total_checkpoints > 0 else 0
            
            # 年龄统计
            now = datetime.now()
            ages_hours = [(now - cp.created_at).total_seconds() / 3600.0 for cp in checkpoints]
            oldest_checkpoint_age_hours = max(ages_hours) if ages_hours else 0
            newest_checkpoint_age_hours = min(ages_hours) if ages_hours else 0
            average_age_hours = sum(ages_hours) / len(ages_hours) if ages_hours else 0
            
            return CheckpointStatistics(
                total_checkpoints=total_checkpoints,
                active_checkpoints=active_checkpoints,
                expired_checkpoints=expired_checkpoints,
                corrupted_checkpoints=corrupted_checkpoints,
                archived_checkpoints=archived_checkpoints,
                total_size_bytes=total_size_bytes,
                average_size_bytes=average_size_bytes,
                largest_checkpoint_bytes=largest_checkpoint_bytes,
                smallest_checkpoint_bytes=smallest_checkpoint_bytes,
                total_restores=total_restores,
                average_restores=average_restores,
                oldest_checkpoint_age_hours=oldest_checkpoint_age_hours,
                newest_checkpoint_age_hours=newest_checkpoint_age_hours,
                average_age_hours=average_age_hours,
            )
            
        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return CheckpointStatistics()


class DatabaseThreadCheckpointRepository:
    """基于数据库的Thread检查点仓储实现
    
    这是一个示例实现，可以根据具体的数据库进行调整。
    """
    
    def __init__(self, db_connection):
        """初始化数据库仓储
        
        Args:
            db_connection: 数据库连接
        """
        self._db = db_connection
        logger.info("DatabaseThreadCheckpointRepository initialized")
    
    async def save(self, checkpoint: ThreadCheckpoint) -> bool:
        """保存检查点到数据库"""
        try:
            query = """
                INSERT OR REPLACE INTO thread_checkpoints 
                (id, thread_id, state_data, metadata, status, checkpoint_type, 
                 created_at, updated_at, expires_at, size_bytes, restore_count, last_restored_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self._db.execute(query, (
                checkpoint.id,
                checkpoint.thread_id,
                json.dumps(checkpoint.state_data),
                json.dumps(checkpoint.metadata),
                checkpoint.status.value,
                checkpoint.checkpoint_type.value,
                checkpoint.created_at.isoformat(),
                checkpoint.updated_at.isoformat(),
                checkpoint.expires_at.isoformat() if checkpoint.expires_at else None,
                checkpoint.size_bytes,
                checkpoint.restore_count,
                checkpoint.last_restored_at.isoformat() if checkpoint.last_restored_at else None
            ))
            
            await self._db.commit()
            logger.debug(f"Saved checkpoint {checkpoint.id} to database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save checkpoint {checkpoint.id} to database: {e}")
            return False
    
    async def find_by_id(self, checkpoint_id: str) -> Optional[ThreadCheckpoint]:
        """从数据库查找检查点"""
        try:
            query = "SELECT * FROM thread_checkpoints WHERE id = ?"
            cursor = await self._db.execute(query, (checkpoint_id,))
            row = await cursor.fetchone()
            
            if row:
                return self._row_to_checkpoint(row)
            return None
            
        except Exception as e:
            logger.error(f"Failed to find checkpoint {checkpoint_id} in database: {e}")
            return None
    
    async def find_by_thread(self, thread_id: str) -> List[ThreadCheckpoint]:
        """从数据库查找线程的检查点"""
        try:
            query = """
                SELECT * FROM thread_checkpoints 
                WHERE thread_id = ? 
                ORDER BY created_at DESC
            """
            cursor = await self._db.execute(query, (thread_id,))
            rows = await cursor.fetchall()
            
            return [self._row_to_checkpoint(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to find checkpoints for thread {thread_id} in database: {e}")
            return []
    
    async def find_expired(self) -> List[ThreadCheckpoint]:
        """从数据库查找过期的检查点"""
        try:
            query = """
                SELECT * FROM thread_checkpoints 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """
            cursor = await self._db.execute(query, (datetime.now().isoformat(),))
            rows = await cursor.fetchall()
            
            return [self._row_to_checkpoint(row) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to find expired checkpoints in database: {e}")
            return []
    
    async def update(self, checkpoint: ThreadCheckpoint) -> bool:
        """更新数据库中的检查点"""
        try:
            query = """
                UPDATE thread_checkpoints SET
                state_data = ?, metadata = ?, status = ?, checkpoint_type = ?,
                updated_at = ?, expires_at = ?, size_bytes = ?, 
                restore_count = ?, last_restored_at = ?
                WHERE id = ?
            """
            
            await self._db.execute(query, (
                json.dumps(checkpoint.state_data),
                json.dumps(checkpoint.metadata),
                checkpoint.status.value,
                checkpoint.checkpoint_type.value,
                checkpoint.updated_at.isoformat(),
                checkpoint.expires_at.isoformat() if checkpoint.expires_at else None,
                checkpoint.size_bytes,
                checkpoint.restore_count,
                checkpoint.last_restored_at.isoformat() if checkpoint.last_restored_at else None,
                checkpoint.id
            ))
            
            await self._db.commit()
            logger.debug(f"Updated checkpoint {checkpoint.id} in database")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update checkpoint {checkpoint.id} in database: {e}")
            return False
    
    async def delete(self, checkpoint_id: str) -> bool:
        """从数据库删除检查点"""
        try:
            query = "DELETE FROM thread_checkpoints WHERE id = ?"
            cursor = await self._db.execute(query, (checkpoint_id,))
            await self._db.commit()
            
            if cursor.rowcount > 0:
                logger.debug(f"Deleted checkpoint {checkpoint_id} from database")
                return True
            else:
                logger.warning(f"Checkpoint {checkpoint_id} not found for deletion")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete checkpoint {checkpoint_id} from database: {e}")
            return False
    
    async def count_by_thread(self, thread_id: str) -> int:
        """统计线程的检查点数量"""
        try:
            query = "SELECT COUNT(*) FROM thread_checkpoints WHERE thread_id = ?"
            cursor = await self._db.execute(query, (thread_id,))
            row = await cursor.fetchone()
            
            return row[0] if row else 0
            
        except Exception as e:
            logger.error(f"Failed to count checkpoints for thread {thread_id} in database: {e}")
            return 0
    
    async def get_statistics(self, thread_id: Optional[str] = None) -> CheckpointStatistics:
        """从数据库获取统计信息"""
        try:
            if thread_id:
                where_clause = "WHERE thread_id = ?"
                params = (thread_id,)
            else:
                where_clause = ""
                params = ()
            
            query = f"""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN status = 'expired' THEN 1 ELSE 0 END) as expired,
                    SUM(CASE WHEN status = 'corrupted' THEN 1 ELSE 0 END) as corrupted,
                    SUM(CASE WHEN status = 'archived' THEN 1 ELSE 0 END) as archived,
                    SUM(size_bytes) as total_size,
                    AVG(size_bytes) as avg_size,
                    MAX(size_bytes) as max_size,
                    MIN(size_bytes) as min_size,
                    SUM(restore_count) as total_restores,
                    AVG(restore_count) as avg_restores
                FROM thread_checkpoints 
                {where_clause}
            """
            
            cursor = await self._db.execute(query, params)
            row = await cursor.fetchone()
            
            if row and row[0] > 0:
                # 获取年龄统计
                age_query = f"""
                    SELECT 
                        MAX((julianday('now') - julianday(created_at)) * 24) as oldest_age,
                        MIN((julianday('now') - julianday(created_at)) * 24) as newest_age,
                        AVG((julianday('now') - julianday(created_at)) * 24) as avg_age
                    FROM thread_checkpoints 
                    {where_clause}
                """
                
                age_cursor = await self._db.execute(age_query, params)
                age_row = await age_cursor.fetchone()
                
                return CheckpointStatistics(
                    total_checkpoints=row[0],
                    active_checkpoints=row[1],
                    expired_checkpoints=row[2],
                    corrupted_checkpoints=row[3],
                    archived_checkpoints=row[4],
                    total_size_bytes=row[5] or 0,
                    average_size_bytes=row[6] or 0,
                    largest_checkpoint_bytes=row[7] or 0,
                    smallest_checkpoint_bytes=row[8] or 0,
                    total_restores=row[9] or 0,
                    average_restores=row[10] or 0,
                    oldest_checkpoint_age_hours=age_row[0] or 0 if age_row else 0,
                    newest_checkpoint_age_hours=age_row[1] or 0 if age_row else 0,
                    average_age_hours=age_row[2] or 0 if age_row else 0,
                )
            
            return CheckpointStatistics()
            
        except Exception as e:
            logger.error(f"Failed to get statistics from database: {e}")
            return CheckpointStatistics()
    
    def _row_to_checkpoint(self, row) -> ThreadCheckpoint:
        """将数据库行转换为检查点对象"""
        return ThreadCheckpoint(
            id=row[0],
            thread_id=row[1],
            state_data=json.loads(row[2]),
            metadata=json.loads(row[3]),
            status=CheckpointStatus(row[4]),
            checkpoint_type=row[5],  # 假设数据库中存储的是枚举值
            created_at=datetime.fromisoformat(row[6]),
            updated_at=datetime.fromisoformat(row[7]),
            expires_at=datetime.fromisoformat(row[8]) if row[8] else None,
            size_bytes=row[9],
            restore_count=row[10],
            last_restored_at=datetime.fromisoformat(row[11]) if row[11] else None,
        )