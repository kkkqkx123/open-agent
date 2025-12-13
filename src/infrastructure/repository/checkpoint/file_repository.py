"""文件检查点Repository实现"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.interfaces.repository import ICheckpointRepository
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class FileCheckpointRepository(ICheckpointRepository):
    """文件检查点Repository实现 - 直接使用文件系统"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件检查点Repository"""
        self.base_path = Path(config.get("base_path", "./checkpoints"))
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def save_checkpoint(self, checkpoint_data: Dict[str, Any]) -> str:
        """保存checkpoint数据"""
        try:
            checkpoint_id = checkpoint_data.get("checkpoint_id")
            if not checkpoint_id:
                import uuid
                checkpoint_id = str(uuid.uuid4())
            
            # 添加时间戳
            current_time = time.time()
            full_checkpoint = {
                "checkpoint_id": checkpoint_id,
                "created_at": current_time,
                "updated_at": current_time,
                **checkpoint_data
            }
            
            # 创建线程目录
            thread_dir = self.base_path / checkpoint_data["thread_id"]
            thread_dir.mkdir(exist_ok=True)
            
            # 保存到文件
            checkpoint_file = thread_dir / f"{checkpoint_id}.json"
            with open(checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(full_checkpoint, f, indent=2, ensure_ascii=False)
            
            logger.debug(f"File checkpoint saved: {checkpoint_id}")
            return checkpoint_id
            
        except Exception as e:
            logger.error(f"Failed to save file checkpoint: {e}")
            raise
    
    async def load_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """加载checkpoint数据"""
        try:
            # 在所有thread目录中查找checkpoint
            for thread_dir in self.base_path.iterdir():
                if thread_dir.is_dir():
                    checkpoint_file = thread_dir / f"{checkpoint_id}.json"
                    if checkpoint_file.exists():
                        with open(checkpoint_file, 'r', encoding='utf-8') as f:
                            checkpoint = json.load(f)
                            logger.debug(f"File checkpoint loaded: {checkpoint_id}")
                            return checkpoint
            return None
            
        except Exception as e:
            logger.error(f"Failed to load file checkpoint {checkpoint_id}: {e}")
            raise
    
    async def list_checkpoints(
        self, 
        thread_id: str,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出指定thread的所有checkpoint"""
        try:
            thread_dir = self.base_path / thread_id
            if not thread_dir.exists():
                return []
            
            checkpoints = []
            for checkpoint_file in thread_dir.glob("*.json"):
                try:
                    with open(checkpoint_file, 'r', encoding='utf-8') as f:
                        checkpoint = json.load(f)
                        checkpoints.append(checkpoint)
                except Exception as e:
                    logger.warning(f"Failed to load checkpoint file {checkpoint_file}: {e}")
                    continue
            
            # 按创建时间倒序排序
            checkpoints.sort(key=lambda x: x.get("created_at", 0), reverse=True)
            
            # 应用limit限制
            if limit is not None:
                checkpoints = checkpoints[:limit]
            
            logger.debug(f"Listed file checkpoints for {thread_id}: {len(checkpoints)} items")
            return checkpoints
            
        except Exception as e:
            logger.error(f"Failed to list file checkpoints for {thread_id}: {e}")
            raise
    
    async def delete_checkpoint(self, checkpoint_id: str) -> bool:
        """删除指定的checkpoint"""
        try:
            # 在所有thread目录中查找并删除checkpoint
            for thread_dir in self.base_path.iterdir():
                if thread_dir.is_dir():
                    checkpoint_file = thread_dir / f"{checkpoint_id}.json"
                    if checkpoint_file.exists():
                        checkpoint_file.unlink()
                        logger.debug(f"File checkpoint deleted: {checkpoint_id}")
                        return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file checkpoint {checkpoint_id}: {e}")
            raise
    
    async def get_latest_checkpoint(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """获取thread的最新checkpoint"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            return checkpoints[0] if checkpoints else None
            
        except Exception as e:
            logger.error(f"Failed to get latest file checkpoint for {thread_id}: {e}")
            raise
    
    async def get_checkpoints_by_workflow(self, thread_id: str, workflow_id: str) -> List[Dict[str, Any]]:
        """获取指定工作流的所有checkpoint"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            # 过滤指定工作流的检查点
            workflow_checkpoints = [
                cp for cp in checkpoints
                if cp.get("workflow_id") == workflow_id
            ]
            
            logger.debug(f"Got workflow checkpoints for {thread_id}/{workflow_id}: {len(workflow_checkpoints)} items")
            return workflow_checkpoints
            
        except Exception as e:
            logger.error(f"Failed to get workflow file checkpoints for {thread_id}/{workflow_id}: {e}")
            raise
    
    async def cleanup_old_checkpoints(self, thread_id: str, max_count: int) -> int:
        """清理旧的checkpoint，保留最新的max_count个"""
        try:
            checkpoints = await self.list_checkpoints(thread_id)
            
            if len(checkpoints) <= max_count:
                return 0
            
            # 需要删除的checkpoint
            to_delete = checkpoints[max_count:]
            
            # 删除旧checkpoint
            deleted_count = 0
            thread_dir = self.base_path / thread_id
            for checkpoint in to_delete:
                checkpoint_id = checkpoint["checkpoint_id"]
                checkpoint_file = thread_dir / f"{checkpoint_id}.json"
                if checkpoint_file.exists():
                    checkpoint_file.unlink()
                    deleted_count += 1
            
            logger.debug(f"Cleaned up old file checkpoints for {thread_id}: deleted {deleted_count} items")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old file checkpoints for {thread_id}: {e}")
            raise