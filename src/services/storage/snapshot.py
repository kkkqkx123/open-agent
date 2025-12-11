"""快照服务

提供数据快照的创建、管理和恢复功能。
"""

import time
import json
from typing import Dict, Any, Optional, List, AsyncIterator
from src.interfaces.storage.base import IStorage
from src.interfaces.storage.exceptions import StorageError
from src.interfaces.dependency_injection import get_logger


logger = get_logger(__name__)


class SnapshotService:
    """快照服务
    
    提供数据快照的创建、管理和恢复功能。
    """
    
    def __init__(self, storage: IStorage) -> None:
        """初始化快照服务
        
        Args:
            storage: 存储实例
        """
        self.storage = storage
        self.logger = get_logger(self.__class__.__name__)
    
    async def create_snapshot(
        self,
        snapshot_data: Dict[str, Any],
        snapshot_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        description: Optional[str] = None
    ) -> str:
        """创建快照
        
        Args:
            snapshot_data: 快照数据
            snapshot_id: 快照ID，None表示自动生成
            metadata: 元数据
            description: 快照描述
            
        Returns:
            快照ID
            
        Raises:
            StorageError: 创建失败
        """
        try:
            # 准备数据
            data = {
                "type": "snapshot",
                "data": snapshot_data,
                "description": description or "",
                "created_at": time.time()
            }
            
            # 设置快照ID
            if snapshot_id:
                data["id"] = snapshot_id
            
            # 添加元数据
            if metadata:
                data["metadata"] = metadata
            
            # 添加快照统计信息
            data["stats"] = self._calculate_snapshot_stats(snapshot_data)
            
            # 保存快照
            result_id = await self.storage.save(data)
            
            self.logger.info(f"快照创建成功，ID: {result_id}")
            return result_id
            
        except Exception as e:
            self.logger.error(f"创建快照失败: {e}")
            raise StorageError(f"Failed to create snapshot: {e}")
    
    async def load_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """加载快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照数据，不存在则返回None
            
        Raises:
            StorageError: 加载失败
        """
        try:
            # 加载数据
            data = await self.storage.load(snapshot_id)
            
            if data is None:
                return None
            
            # 验证数据类型
            if data.get("type") != "snapshot":
                self.logger.warning(f"数据类型不匹配，期望'snapshot'，实际'{data.get('type')}'")
                return None
            
            self.logger.debug(f"快照加载成功，ID: {snapshot_id}")
            return data
            
        except Exception as e:
            self.logger.error(f"加载快照失败: {e}")
            raise StorageError(f"Failed to load snapshot {snapshot_id}: {e}")
    
    async def restore_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """恢复快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的数据，不存在则返回None
            
        Raises:
            StorageError: 恢复失败
        """
        try:
            # 加载快照
            snapshot = await self.load_snapshot(snapshot_id)
            if snapshot is None:
                return None
            
            # 提取快照数据
            restored_data: Dict[str, Any] = snapshot.get("data", {})
            
            self.logger.info(f"快照恢复成功，ID: {snapshot_id}")
            return restored_data
            
        except Exception as e:
            self.logger.error(f"恢复快照失败: {e}")
            raise StorageError(f"Failed to restore snapshot {snapshot_id}: {e}")
    
    async def delete_snapshot(self, snapshot_id: str) -> bool:
        """删除快照
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            是否删除成功
            
        Raises:
            StorageError: 删除失败
        """
        try:
            # 验证快照存在
            snapshot = await self.load_snapshot(snapshot_id)
            if snapshot is None:
                return False
            
            # 删除快照
            result = await self.storage.delete(snapshot_id)
            
            if result:
                self.logger.debug(f"快照删除成功，ID: {snapshot_id}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"删除快照失败: {e}")
            raise StorageError(f"Failed to delete snapshot {snapshot_id}: {e}")
    
    async def list_snapshots(
        self,
        filters: Optional[Dict[str, Any]] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出快照
        
        Args:
            filters: 过滤条件
            limit: 限制数量
            
        Returns:
            快照列表
            
        Raises:
            StorageError: 查询失败
        """
        try:
            # 准备过滤条件
            query_filters = filters or {}
            query_filters["type"] = "snapshot"
            
            # 查询快照
            snapshots = await self.storage.list(query_filters, limit)
            
            # 按创建时间排序
            snapshots.sort(
                key=lambda s: s.get("created_at", 0),
                reverse=True
            )
            
            self.logger.debug(f"列出快照成功，返回 {len(snapshots)} 条记录")
            return snapshots
            
        except Exception as e:
            self.logger.error(f"列出快照失败: {e}")
            raise StorageError(f"Failed to list snapshots: {e}")
    
    async def get_snapshot_info(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """获取快照信息
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            快照信息，不存在则返回None
        """
        snapshot = await self.load_snapshot(snapshot_id)
        if snapshot is None:
            return None
        
        # 返回不包含数据的快照信息
        info = {
            "id": snapshot.get("id"),
            "type": snapshot.get("type"),
            "description": snapshot.get("description", ""),
            "created_at": snapshot.get("created_at"),
            "metadata": snapshot.get("metadata", {}),
            "stats": snapshot.get("stats", {})
        }
        
        return info
    
    async def get_snapshots_by_time_range(
        self,
        start_time: float,
        end_time: float,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据时间范围获取快照
        
        Args:
            start_time: 开始时间戳
            end_time: 结束时间戳
            limit: 限制数量
            
        Returns:
            快照列表
        """
        try:
            # 获取所有快照
            all_snapshots = await self.list_snapshots()
            
            # 时间过滤
            filtered_snapshots = [
                snapshot for snapshot in all_snapshots
                if start_time <= snapshot.get("created_at", 0) <= end_time
            ]
            
            # 按时间排序
            filtered_snapshots.sort(
                key=lambda s: s.get("created_at", 0),
                reverse=True
            )
            
            # 应用数量限制
            if limit:
                filtered_snapshots = filtered_snapshots[:limit]
            
            return filtered_snapshots
            
        except Exception as e:
            self.logger.error(f"根据时间范围获取快照失败: {e}")
            raise StorageError(f"Failed to get snapshots by time range: {e}")
    
    async def get_recent_snapshots(
        self,
        time_limit: Optional[float] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """获取最近的快照
        
        Args:
            time_limit: 时间限制（秒），None表示不限制
            limit: 数量限制
            
        Returns:
            快照列表
        """
        current_time = time.time()
        
        if time_limit is not None:
            start_time = current_time - time_limit
            return await self.get_snapshots_by_time_range(start_time, current_time, limit)
        else:
            return await self.list_snapshots(limit=limit)
    
    async def get_snapshots_by_metadata(
        self,
        metadata_filters: Dict[str, Any],
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """根据元数据过滤快照
        
        Args:
            metadata_filters: 元数据过滤条件
            limit: 限制数量
            
        Returns:
            快照列表
        """
        # 获取所有快照
        all_snapshots = await self.list_snapshots(limit=limit)
        
        # 过滤元数据
        filtered_snapshots = []
        for snapshot in all_snapshots:
            metadata = snapshot.get("metadata", {})
            match = True
            
            for key, value in metadata_filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered_snapshots.append(snapshot)
        
        return filtered_snapshots
    
    async def cleanup_old_snapshots(
        self,
        retention_days: int,
        keep_latest: int = 5
    ) -> int:
        """清理旧快照
        
        Args:
            retention_days: 保留天数
            keep_latest: 保留最新快照数量
            
        Returns:
            清理的快照数量
        """
        try:
            # 获取所有快照，按时间排序
            all_snapshots = await self.list_snapshots()
            
            if len(all_snapshots) <= keep_latest:
                return 0
            
            # 计算截止时间
            current_time = time.time()
            cutoff_time = current_time - (retention_days * 24 * 3600)
            
            # 保留最新的快照
            snapshots_to_keep = all_snapshots[:keep_latest]
            keep_ids = {s["id"] for s in snapshots_to_keep}
            
            # 找出需要删除的快照
            snapshots_to_delete = []
            for snapshot in all_snapshots[keep_latest:]:
                if (snapshot.get("created_at", 0) < cutoff_time and 
                    snapshot["id"] not in keep_ids):
                    snapshots_to_delete.append(snapshot["id"])
            
            # 批量删除
            if snapshots_to_delete:
                deleted_count = await self.storage.batch_delete(snapshots_to_delete)
                self.logger.info(f"清理旧快照完成，删除了 {deleted_count} 个快照")
                return deleted_count
            
            return 0
            
        except Exception as e:
            self.logger.error(f"清理旧快照失败: {e}")
            raise StorageError(f"Failed to cleanup old snapshots: {e}")
    
    async def export_snapshot(
        self,
        snapshot_id: str,
        format: str = "json"
    ) -> str:
        """导出快照
        
        Args:
            snapshot_id: 快照ID
            format: 导出格式（json）
            
        Returns:
            导出的数据字符串
            
        Raises:
            StorageError: 导出失败
        """
        try:
            # 加载快照
            snapshot = await self.load_snapshot(snapshot_id)
            if snapshot is None:
                raise StorageError(f"Snapshot {snapshot_id} not found")
            
            if format.lower() == "json":
                # 导出为JSON格式
                export_data = {
                    "snapshot_id": snapshot.get("id"),
                    "description": snapshot.get("description", ""),
                    "created_at": snapshot.get("created_at"),
                    "metadata": snapshot.get("metadata", {}),
                    "data": snapshot.get("data", {})
                }
                
                return json.dumps(export_data, indent=2, ensure_ascii=False)
            else:
                raise ValueError(f"Unsupported export format: {format}")
                
        except Exception as e:
            self.logger.error(f"导出快照失败: {e}")
            raise StorageError(f"Failed to export snapshot {snapshot_id}: {e}")
    
    async def import_snapshot(
        self,
        export_data: str,
        format: str = "json",
        new_snapshot_id: Optional[str] = None
    ) -> str:
        """导入快照
        
        Args:
            export_data: 导出的数据字符串
            format: 导入格式（json）
            new_snapshot_id: 新快照ID，None表示使用原ID
            
        Returns:
            快照ID
            
        Raises:
            StorageError: 导入失败
        """
        try:
            if format.lower() == "json":
                # 从JSON导入
                import_data = json.loads(export_data)
                
                # 提取快照数据
                snapshot_data = import_data.get("data", {})
                metadata = import_data.get("metadata", {})
                description = import_data.get("description", "")
                
                # 使用新ID或原ID
                snapshot_id = new_snapshot_id or import_data.get("id")
                
                # 创建快照
                return await self.create_snapshot(
                    snapshot_data=snapshot_data,
                    snapshot_id=snapshot_id,
                    metadata=metadata,
                    description=f"Imported: {description}"
                )
            else:
                raise ValueError(f"Unsupported import format: {format}")
                
        except Exception as e:
            self.logger.error(f"导入快照失败: {e}")
            raise StorageError(f"Failed to import snapshot: {e}")
    
    async def compare_snapshots(
        self,
        snapshot_id1: str,
        snapshot_id2: str
    ) -> Dict[str, Any]:
        """比较两个快照
        
        Args:
            snapshot_id1: 第一个快照ID
            snapshot_id2: 第二个快照ID
            
        Returns:
            比较结果
            
        Raises:
            StorageError: 比较失败
        """
        try:
            # 加载快照
            snapshot1 = await self.load_snapshot(snapshot_id1)
            snapshot2 = await self.load_snapshot(snapshot_id2)
            
            if snapshot1 is None or snapshot2 is None:
                raise StorageError("One or both snapshots not found")
            
            # 提取数据
            data1 = snapshot1.get("data", {})
            data2 = snapshot2.get("data", {})
            
            # 简单比较（可以根据需要实现更复杂的比较逻辑）
            comparison = {
                "snapshot1": {
                    "id": snapshot1.get("id"),
                    "created_at": snapshot1.get("created_at"),
                    "description": snapshot1.get("description", "")
                },
                "snapshot2": {
                    "id": snapshot2.get("id"),
                    "created_at": snapshot2.get("created_at"),
                    "description": snapshot2.get("description", "")
                },
                "data_equal": data1 == data2,
                "size_diff": len(str(data2)) - len(str(data1)),
                "time_diff": snapshot2.get("created_at", 0) - snapshot1.get("created_at", 0)
            }
            
            return comparison
            
        except Exception as e:
            self.logger.error(f"比较快照失败: {e}")
            raise StorageError(f"Failed to compare snapshots: {e}")
    
    def _calculate_snapshot_stats(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """计算快照统计信息
        
        Args:
            data: 快照数据
            
        Returns:
            统计信息字典
        """
        try:
            data_str = json.dumps(data, ensure_ascii=False)
            
            return {
                "size_bytes": len(data_str.encode('utf-8')),
                "size_chars": len(data_str),
                "item_count": self._count_items(data),
                "keys": list(data.keys()) if isinstance(data, dict) else []
            }
        except Exception:
            return {
                "size_bytes": 0,
                "size_chars": 0,
                "item_count": 0,
                "keys": []
            }
    
    def _count_items(self, data: Any) -> int:
        """递归计算数据项数量
        
        Args:
            data: 数据
            
        Returns:
            项目数量
        """
        if isinstance(data, dict):
            return sum(self._count_items(v) for v in data.values())
        elif isinstance(data, list):
            return sum(self._count_items(item) for item in data)
        else:
            return 1
