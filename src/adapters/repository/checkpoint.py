"""检查点Repository重构实现

使用基类和工具类重构的检查点Repository实现。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from src.interfaces.repository import ICheckpointRepository
from .base import SQLiteBaseRepository, MemoryBaseRepository, FileBaseRepository
from .utils import JsonUtils, TimeUtils, IdUtils, SQLiteUtils, FileUtils


class SQLiteCheckpointRepository(SQLiteBaseRepository, ICheckpointRepository):
    """SQLite检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化SQLite检查点Repository"""
        table_sql = """
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_id TEXT PRIMARY KEY,
                thread_id TEXT NOT NULL,
                workflow_id TEXT NOT NULL,
                state_data TEXT NOT NULL,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        
        indexes_sql = [
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_thread_id ON checkpoints(thread_id)",
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_id ON checkpoints(workflow_id)",
            "CREATE INDEX IF NOT EXISTS idx_checkpoints_created_at ON checkpoints(created_at)"
        ]
        
        super().__init__(config, "checkpoints", table_sql, indexes_sql)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存检查点"""
        try:
            checkpoint_id = IdUtils.get_or_generate_id(
                checkpoint_data, "checkpoint_id", IdUtils.generate_checkpoint_id
            )
            
            data = {
                "checkpoint_id": checkpoint_id,
                "thread_id": checkpoint_data["thread_id"],
                "workflow_id": checkpoint_data["workflow_id"],
                "state_data": JsonUtils.serialize(checkpoint_data["state_data"]),
                "metadata": JsonUtils.serialize(checkpoint_data.get("metadata", {}))
            }
            
            self._insert_or_replace(data)
            self._log_operation("检查点保存", True, checkpoint_id)
            return checkpoint_id
            
        except Exception as e:
            self._handle_exception("保存检查点", e)
            # 根据接口定义，此方法必须返回str，但在异常情况下抛出异常，不会返回
            # 为了满足mypy类型检查，添加返回语句（实际上不会执行到这里）
            raise  # 重新抛出异常，不会到达下一行
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载检查点"""
        try:
            row = self._find_by_id("checkpoint_id", checkpoint_id)
            if row:
                return {
                    "checkpoint_id": row[0],
                    "thread_id": row[1],
                    "workflow_id": row[2],
                    "state_data": JsonUtils.deserialize(row[3]),
                    "metadata": JsonUtils.deserialize(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None
            
        except Exception as e:
            self._handle_exception("加载检查点", e)
            raise  # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定线程的所有检查点"""
        try:
            query = """
                SELECT checkpoint_id, thread_id, workflow_id, state_data, metadata, created_at, updated_at
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
            
            checkpoints = []
            for row in results:
                checkpoints.append({
                    "checkpoint_id": row[0],
                    "thread_id": row[1],
                    "workflow_id": row[2],
                    "state_data": JsonUtils.deserialize(row[3]),
                    "metadata": JsonUtils.deserialize(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6]
                })
            
            self._log_operation("列出检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
            return checkpoints
            
        except Exception as e:
            self._handle_exception("列出检查点", e)
            raise # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的检查点"""
        try:
            deleted = self._delete_by_id("checkpoint_id", checkpoint_id)
            self._log_operation("检查点删除", deleted, checkpoint_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除检查点", e)
            raise  # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新检查点"""
        try:
            query = """
                SELECT checkpoint_id, thread_id, workflow_id, state_data, metadata, created_at, updated_at
                FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
            
            if results:
                row = results[0]
                return {
                    "checkpoint_id": row[0],
                    "thread_id": row[1],
                    "workflow_id": row[2],
                    "state_data": JsonUtils.deserialize(row[3]),
                    "metadata": JsonUtils.deserialize(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6]
                }
            return None
            
        except Exception as e:
            self._handle_exception("获取最新检查点", e)
            raise  # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有检查点"""
        try:
            query = """
                SELECT checkpoint_id, thread_id, workflow_id, state_data, metadata, created_at, updated_at
                FROM checkpoints
                WHERE thread_id = ? AND workflow_id = ?
                ORDER BY created_at DESC
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (thread_id, workflow_id))
            
            checkpoints = []
            for row in results:
                checkpoints.append({
                    "checkpoint_id": row[0],
                    "thread_id": row[1],
                    "workflow_id": row[2],
                    "state_data": JsonUtils.deserialize(row[3]),
                    "metadata": JsonUtils.deserialize(row[4]),
                    "created_at": row[5],
                    "updated_at": row[6]
                })
            
            self._log_operation("获取工作流检查点", True, f"{thread_id}:{workflow_id}, 共{len(checkpoints)}条")
            return checkpoints
            
        except Exception as e:
            self._handle_exception("获取工作流检查点", e)
            raise # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点，保留最新的max_count个"""
        try:
            # 获取所有检查点ID，按创建时间排序
            query = """
                SELECT checkpoint_id FROM checkpoints
                WHERE thread_id = ?
                ORDER BY created_at DESC
            """
            results = SQLiteUtils.execute_query(self.db_path, query, (thread_id,))
            all_checkpoint_ids = [row[0] for row in results]
            
            if len(all_checkpoint_ids) <= max_count:
                return 0
            
            # 需要删除的检查点
            to_delete_ids = all_checkpoint_ids[max_count:]
            
            # 删除旧检查点
            deleted_count = 0
            for checkpoint_id in to_delete_ids:
                if self._delete_by_id("checkpoint_id", checkpoint_id):
                    deleted_count += 1
            
            self._log_operation("清理旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理旧检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """获取检查点统计信息"""
        try:
            # 总检查点数
            total_count = self._count_records()
            
            # 线程数量
            query_thread = "SELECT COUNT(DISTINCT thread_id) FROM checkpoints"
            thread_count_result = SQLiteUtils.execute_query(self.db_path, query_thread)
            thread_count = thread_count_result[0][0] if thread_count_result else 0
            
            # 工作流数量
            query_workflow = "SELECT COUNT(DISTINCT workflow_id) FROM checkpoints"
            workflow_count_result = SQLiteUtils.execute_query(self.db_path, query_workflow)
            workflow_count = workflow_count_result[0][0] if workflow_count_result else 0
            
            # 按线程统计
            top_threads_results = SQLiteUtils.get_top_records(
                self.db_path, self.table_name, "thread_id", "created_at", 10
            )
            top_threads = [{"thread_id": row[0], "count": row[1]} for row in top_threads_results]
            
            # 按工作流统计
            top_workflows_results = SQLiteUtils.get_top_records(
                self.db_path, self.table_name, "workflow_id", "created_at", 10
            )
            top_workflows = [{"workflow_id": row[0], "count": row[1]} for row in top_workflows_results]
            
            stats = {
                "total_count": total_count,
                "thread_count": thread_count,
                "workflow_count": workflow_count,
                "top_threads": top_threads,
                "top_workflows": top_workflows
            }
            
            self._log_operation("获取检查点统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取检查点统计信息", e)
            raise # 重新抛出异常


class MemoryCheckpointRepository(MemoryBaseRepository, ICheckpointRepository):
    """内存检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存检查点Repository"""
        super().__init__(config)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存检查点"""
        try:
            checkpoint_id = IdUtils.get_or_generate_id(
                checkpoint_data, "checkpoint_id", IdUtils.generate_checkpoint_id
            )
            
            full_checkpoint = TimeUtils.add_timestamp({
                "checkpoint_id": checkpoint_id,
                **checkpoint_data
            })
            
            # 保存到存储
            self._save_item(checkpoint_id, full_checkpoint)
            
            # 更新索引
            self._add_to_index("thread", checkpoint_data["thread_id"], checkpoint_id)
            self._add_to_index("workflow", checkpoint_data["workflow_id"], checkpoint_id)
            
            self._log_operation("内存检查点保存", True, checkpoint_id)
            return checkpoint_id
            
        except Exception as e:
            self._handle_exception("保存内存检查点", e)
            raise # 重新抛出异常
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载检查点"""
        try:
            checkpoint = self._load_item(checkpoint_id)
            if checkpoint:
                self._log_operation("内存检查点加载", True, checkpoint_id)
                return checkpoint
            return None
            
        except Exception as e:
            self._handle_exception("加载内存检查点", e)
            raise # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定线程的所有检查点"""
        try:
            checkpoint_ids = self._get_from_index("thread", thread_id)
            # 过滤掉None值，确保只返回有效的检查点
            checkpoints = [item for cid in checkpoint_ids if (item := self._load_item(cid)) is not None]
            
            # 按创建时间倒序排序
            checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
            
            self._log_operation("列出内存检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
            return checkpoints
            
        except Exception as e:
            self._handle_exception("列出内存检查点", e)
            raise # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的检查点"""
        try:
            checkpoint = self._load_item(checkpoint_id)
            if not checkpoint:
                return False
            
            # 从索引中移除
            self._remove_from_index("thread", checkpoint["thread_id"], checkpoint_id)
            self._remove_from_index("workflow", checkpoint["workflow_id"], checkpoint_id)
            
            # 从存储中删除
            deleted = self._delete_item(checkpoint_id)
            self._log_operation("内存检查点删除", deleted, checkpoint_id)
            return deleted
            
        except Exception as e:
            self._handle_exception("删除内存检查点", e)
            raise # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新检查点"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            self._handle_exception("获取最新内存检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有检查点"""
        try:
            thread_checkpoints = await self.list_checkpoints(thread_id)
            workflow_checkpoints = [
                cp for cp in thread_checkpoints
                if cp.get("workflow_id") == workflow_id
            ]
            
            self._log_operation("获取内存工作流检查点", True, f"{thread_id}:{workflow_id}, 共{len(workflow_checkpoints)}条")
            return workflow_checkpoints
            
        except Exception as e:
            self._handle_exception("获取内存工作流检查点", e)
            raise # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点，保留最新的max_count个"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            if len(checkpoints) <= max_count:
                return 0
            
            # 需要删除的检查点
            to_delete = checkpoints[max_count:]
            
            # 删除旧检查点
            deleted_count = 0
            for checkpoint in to_delete:
                if await self.delete_checkpoint(checkpoint["checkpoint_id"]):
                    deleted_count += 1
            
            self._log_operation("清理内存旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理内存旧检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """获取检查点统计信息"""
        try:
            total_count = len(self._storage)
            thread_count = len(self._indexes.get("thread", {}))
            workflow_count = len(self._indexes.get("workflow", {}))
            
            # 按线程统计
            top_threads = []
            for thread_id, checkpoint_ids in self._indexes.get("thread", {}).items():
                top_threads.append({"thread_id": thread_id, "count": len(checkpoint_ids)})
            # 修复排序函数的类型问题
            top_threads = sorted(top_threads, key=lambda x: x["count"], reverse=True)[:10]  # type: ignore
            
            # 按工作流统计
            top_workflows = []
            for workflow_id, checkpoint_ids in self._indexes.get("workflow", {}).items():
                top_workflows.append({"workflow_id": workflow_id, "count": len(checkpoint_ids)})
            # 修复排序函数的类型问题
            top_workflows = sorted(top_workflows, key=lambda x: x["count"], reverse=True)[:10]  # type: ignore
            
            stats = {
                "total_count": total_count,
                "thread_count": thread_count,
                "workflow_count": workflow_count,
                "top_threads": top_threads,
                "top_workflows": top_workflows
            }
            
            self._log_operation("获取内存检查点统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取内存检查点统计信息", e)
            raise # 重新抛出异常


class FileCheckpointRepository(FileBaseRepository, ICheckpointRepository):
    """文件检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件检查点Repository"""
        super().__init__(config)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存检查点"""
        try:
            checkpoint_id = IdUtils.get_or_generate_id(
                checkpoint_data, "checkpoint_id", IdUtils.generate_checkpoint_id
            )
            
            full_checkpoint = TimeUtils.add_timestamp({
                "checkpoint_id": checkpoint_id,
                **checkpoint_data
            })
            
            # 保存到文件
            self._save_item(checkpoint_data["thread_id"], checkpoint_id, full_checkpoint)
            
            self._log_operation("文件检查点保存", True, checkpoint_id)
            return checkpoint_id
            
        except Exception as e:
            self._handle_exception("保存文件检查点", e)
            raise # 重新抛出异常
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载检查点"""
        try:
            # 在所有线程目录中查找检查点
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for thread_dir in base_path.iterdir():
                if thread_dir.is_dir():
                    checkpoint = self._load_item(thread_dir.name, checkpoint_id)
                    if checkpoint:
                        self._log_operation("文件检查点加载", True, checkpoint_id)
                        return checkpoint
            return None
            
        except Exception as e:
            self._handle_exception("加载文件检查点", e)
            raise # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定线程的所有检查点"""
        try:
            checkpoints = self._list_items(thread_id)
            
            # 按创建时间倒序排序
            checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
            
            self._log_operation("列出文件检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
            return checkpoints
            
        except Exception as e:
            self._handle_exception("列出文件检查点", e)
            raise # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的检查点"""
        try:
            # 在所有线程目录中查找并删除检查点
            from pathlib import Path
            base_path = Path(self.base_path)
            
            for thread_dir in base_path.iterdir():
                if thread_dir.is_dir():
                    deleted = self._delete_item(thread_dir.name, checkpoint_id)
                    if deleted:
                        self._log_operation("文件检查点删除", True, checkpoint_id)
                        return True
            return False
            
        except Exception as e:
            self._handle_exception("删除文件检查点", e)
            raise # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取线程的最新检查点"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            self._handle_exception("获取最新文件检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有检查点"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            # 过滤工作流
            workflow_checkpoints = [
                checkpoint for checkpoint in checkpoints
                if checkpoint.get("workflow_id") == workflow_id
            ]
            
            self._log_operation("获取文件工作流检查点", True, f"{thread_id}:{workflow_id}, 共{len(workflow_checkpoints)}条")
            return workflow_checkpoints
            
        except Exception as e:
            self._handle_exception("获取文件工作流检查点", e)
            raise # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的检查点，保留最新的max_count个"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            if len(checkpoints) <= max_count:
                return 0
            
            # 需要删除的检查点
            to_delete = checkpoints[max_count:]
            
            # 删除旧检查点
            deleted_count = 0
            for checkpoint in to_delete:
                if await self.delete_checkpoint(checkpoint["checkpoint_id"]):
                    deleted_count += 1
            
            self._log_operation("清理文件旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
            return deleted_count
            
        except Exception as e:
            self._handle_exception("清理文件旧检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoint_statistics(self) -> Dict[str, Any]:
        """获取检查点统计信息"""
        try:
            from pathlib import Path
            base_path = Path(self.base_path)
            
            total_count = 0
            thread_count = 0
            workflow_counts: dict[str, int] = {}
            thread_counts: dict[str, int] = {}
            
            for thread_dir in base_path.iterdir():
                if thread_dir.is_dir():
                    checkpoint_files = list(thread_dir.glob("*.json"))
                    thread_id = thread_dir.name
                    thread_count += 1
                    thread_counts[thread_id] = len(checkpoint_files)
                    total_count += len(checkpoint_files)
                    
                    # 统计工作流
                    for file_path in checkpoint_files:
                        checkpoint = FileUtils.load_json(file_path)
                        if checkpoint:
                            workflow_id = checkpoint.get("workflow_id", "unknown")
                            workflow_counts[workflow_id] = workflow_counts.get(workflow_id, 0) + 1
            
            # 排序统计结果
            top_threads_items = sorted(thread_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_threads = [{"thread_id": str(tid), "count": count} for tid, count in top_threads_items]
            
            top_workflows_items = sorted(workflow_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            top_workflows = [{"workflow_id": str(wid), "count": count} for wid, count in top_workflows_items]
            
            stats = {
                "total_count": total_count,
                "thread_count": thread_count,
                "workflow_count": len(workflow_counts),
                "top_threads": top_threads,
                "top_workflows": top_workflows
            }
            
            self._log_operation("获取文件检查点统计信息", True)
            return stats
            
        except Exception as e:
            self._handle_exception("获取文件检查点统计信息", e)
            raise # 重新抛出异常