"""内存检查点Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from ..memory_base import MemoryBaseRepository
from ..utils import TimeUtils, IdUtils


class MemoryCheckpointRepository(MemoryBaseRepository, ICheckpointRepository):
    """内存检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存检查点Repository"""
        super().__init__(config)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        try:
            def _save():
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
                if "workflow_id" in checkpoint_data:
                    self._add_to_index("workflow", checkpoint_data["workflow_id"], checkpoint_id)
                
                self._log_operation("内存检查点保存", True, checkpoint_id)
                return checkpoint_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存内存检查点", e)
            raise # 重新抛出异常
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            def _load():
                checkpoint = self._load_item(checkpoint_id)
                if checkpoint:
                    self._log_operation("内存检查点加载", True, checkpoint_id)
                    return checkpoint
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载内存检查点", e)
            raise # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            def _list():
                checkpoint_ids = self._get_from_index("thread", thread_id)
                # 过滤掉None值，确保只返回有效的检查点
                checkpoints = [item for cid in checkpoint_ids if (item := self._load_item(cid)) is not None]
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                self._log_operation("列出内存检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
                return checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出内存检查点", e)
            raise # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            def _delete():
                checkpoint = self._load_item(checkpoint_id)
                if not checkpoint:
                    return False
                
                # 从索引中移除
                self._remove_from_index("thread", checkpoint["thread_id"], checkpoint_id)
                if "workflow_id" in checkpoint:
                    self._remove_from_index("workflow", checkpoint["workflow_id"], checkpoint_id)
                
                # 从存储中删除
                deleted = self._delete_item(checkpoint_id)
                self._log_operation("内存检查点删除", deleted, checkpoint_id)
                return deleted
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除内存检查点", e)
            raise # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            def _get_latest():
                checkpoint_ids = self._get_from_index("thread", thread_id)
                # 过滤掉None值，确保只返回有效的检查点
                checkpoints = [item for cid in checkpoint_ids if (item := self._load_item(cid)) is not None]
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                return checkpoints[0] if checkpoints else None
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_latest)
            
        except Exception as e:
            self._handle_exception("获取最新内存检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            def _get_by_workflow():
                checkpoint_ids = self._get_from_index("workflow", workflow_id)
                # 过滤掉None值，确保只返回有效的检查点
                checkpoints = [item for cid in checkpoint_ids if (item := self._load_item(cid)) is not None]
                
                # 过滤指定thread的检查点
                checkpoints = [cp for cp in checkpoints if cp.get("thread_id") == thread_id]
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                self._log_operation("获取工作流内存检查点", True, f"{thread_id}/{workflow_id}, 共{len(checkpoints)}条")
                return checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_by_workflow)
            
        except Exception as e:
            self._handle_exception("获取工作流内存检查点", e)
            raise # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            def _cleanup():
                checkpoint_ids = self._get_from_index("thread", thread_id)
                # 过滤掉None值，确保只返回有效的检查点
                checkpoints = [item for cid in checkpoint_ids if (item := self._load_item(cid)) is not None]
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                if len(checkpoints) <= max_count:
                    return 0
                
                # 需要删除的checkpoint
                to_delete = checkpoints[max_count:]
                
                # 删除旧checkpoint
                deleted_count = 0
                for checkpoint in to_delete:
                    checkpoint_id = checkpoint["checkpoint_id"]
                    # 从索引中移除
                    self._remove_from_index("thread", checkpoint["thread_id"], checkpoint_id)
                    if "workflow_id" in checkpoint:
                        self._remove_from_index("workflow", checkpoint["workflow_id"], checkpoint_id)
                    
                    # 从存储中删除
                    if self._delete_item(checkpoint_id):
                        deleted_count += 1
                
                self._log_operation("清理内存旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
            
        except Exception as e:
            self._handle_exception("清理内存旧检查点", e)
            raise # 重新抛出异常