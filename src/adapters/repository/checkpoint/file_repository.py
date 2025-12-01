"""文件检查点Repository实现"""

import asyncio
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from ..file_base import FileBaseRepository
from ..utils import TimeUtils, IdUtils, FileUtils


class FileCheckpointRepository(FileBaseRepository, ICheckpointRepository):
    """文件检查点Repository实现"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件检查点Repository"""
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
                
                # 保存到文件
                self._save_item(checkpoint_data["thread_id"], checkpoint_id, full_checkpoint)
                
                self._log_operation("文件检查点保存", True, checkpoint_id)
                return checkpoint_id
            
            return await asyncio.get_event_loop().run_in_executor(None, _save)
            
        except Exception as e:
            self._handle_exception("保存文件检查点", e)
            raise # 重新抛出异常
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            def _load():
                # 在所有thread目录中查找checkpoint
                from pathlib import Path
                base_path = Path(self.base_path)
                
                for thread_dir in base_path.iterdir():
                    if thread_dir.is_dir():
                        checkpoint = self._load_item(thread_dir.name, checkpoint_id)
                        if checkpoint:
                            self._log_operation("文件检查点加载", True, checkpoint_id)
                            return checkpoint
                return None
            
            return await asyncio.get_event_loop().run_in_executor(None, _load)
            
        except Exception as e:
            self._handle_exception("加载文件检查点", e)
            raise # 重新抛出异常
    
    async def list_checkpoints(self, thread_id: str) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            def _list():
                checkpoints = self._list_items(thread_id)
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                self._log_operation("列出文件检查点", True, f"{thread_id}, 共{len(checkpoints)}条")
                return checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _list)
            
        except Exception as e:
            self._handle_exception("列出文件检查点", e)
            raise # 重新抛出异常
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            def _delete():
                # 在所有thread目录中查找并删除checkpoint
                from pathlib import Path
                base_path = Path(self.base_path)
                
                for thread_dir in base_path.iterdir():
                    if thread_dir.is_dir():
                        deleted = self._delete_item(thread_dir.name, checkpoint_id)
                        if deleted:
                            self._log_operation("文件检查点删除", True, checkpoint_id)
                            return True
                return False
            
            return await asyncio.get_event_loop().run_in_executor(None, _delete)
            
        except Exception as e:
            self._handle_exception("删除文件检查点", e)
            raise # 重新抛出异常
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            def _get_latest():
                checkpoints = self._list_items(thread_id)
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                return checkpoints[0] if checkpoints else None
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_latest)
            
        except Exception as e:
            self._handle_exception("获取最新文件检查点", e)
            raise # 重新抛出异常
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            def _get_by_workflow():
                checkpoints = self._list_items(thread_id)
                
                # 按创建时间倒序排序
                checkpoints = TimeUtils.sort_by_time(checkpoints, "created_at", True)
                
                # 过滤指定工作流的检查点
                workflow_checkpoints = [
                    cp for cp in checkpoints
                    if cp.get("workflow_id") == workflow_id
                ]
                
                self._log_operation("获取工作流文件检查点", True, f"{thread_id}/{workflow_id}, 共{len(workflow_checkpoints)}条")
                return workflow_checkpoints
            
            return await asyncio.get_event_loop().run_in_executor(None, _get_by_workflow)
            
        except Exception as e:
            self._handle_exception("获取工作流文件检查点", e)
            raise # 重新抛出异常
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            def _cleanup():
                checkpoints = self._list_items(thread_id)
                
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
                    deleted = self._delete_item(thread_id, checkpoint_id)
                    if deleted:
                        deleted_count += 1
                
                self._log_operation("清理文件旧检查点", True, f"{thread_id}, 删除{deleted_count}条")
                return deleted_count
            
            return await asyncio.get_event_loop().run_in_executor(None, _cleanup)
            
        except Exception as e:
            self._handle_exception("清理文件旧检查点", e)
            raise # 重新抛出异常