"""状态持久化服务实现

协调历史记录和快照的持久化操作，提供事务支持和数据一致性保证。
"""

from src.interfaces.dependency_injection import get_logger
import asyncio
import contextlib
from typing import Dict, Any, List, Optional, Tuple, Generator, AsyncGenerator
from datetime import datetime
from contextlib import contextmanager

from src.core.state import StateSnapshot, StateHistoryEntry
from src.interfaces.repository import IHistoryRepository, ISnapshotRepository


logger = get_logger(__name__)


class StatePersistenceService:
    """状态持久化服务
    
    协调状态数据的持久化操作，确保数据一致性。
    """
    
    def __init__(self,
                 history_repository: IHistoryRepository,
                 snapshot_repository: ISnapshotRepository,
                 enable_transactions: bool = True):
        """初始化持久化服务
        
        Args:
            history_repository: 历史记录Repository
            snapshot_repository: 快照Repository
            enable_transactions: 是否启用事务支持
        """
        self._history_repository = history_repository
        self._snapshot_repository = snapshot_repository
        self._enable_transactions = enable_transactions
        self._transaction_active = False
    
    async def save_state_with_history_async(self,
                                          thread_id: str,
                                          state_data: Dict[str, Any],
                                          old_state: Dict[str, Any],
                                          action: str,
                                          create_snapshot: bool = False,
                                          snapshot_name: str = "") -> Tuple[str, Optional[str]]:
        """异步保存状态并记录历史
        
        Args:
            thread_id: 线程ID
            state_data: 状态数据
            old_state: 旧状态
            action: 执行动作
            create_snapshot: 是否创建快照
            snapshot_name: 快照名称
            
        Returns:
            (历史记录ID, 快照ID)
        """
        try:
            async with self._transaction_async():
                # 记录历史
                history_entry = StateHistoryEntry(
                    history_id=self._generate_id(),
                    thread_id=thread_id,
                    timestamp=datetime.now().isoformat(),
                    action=action,
                    state_diff=self._calculate_diff(old_state, state_data),
                    metadata={
                        "old_state_keys": list(old_state.keys()),
                        "new_state_keys": list(state_data.keys())
                    }
                )
                
                # 转换为字典格式保存到Repository
                history_dict = {
                    "history_id": history_entry.history_id,
                    "thread_id": history_entry.thread_id,
                    "timestamp": history_entry.timestamp,
                    "action": history_entry.action,
                    "state_diff": history_entry.state_diff,
                    "metadata": history_entry.metadata
                }
                
                # 保存到历史Repository
                await self._history_repository.save_history(history_dict)
                history_id = history_entry.history_id
                
                # 创建快照（如果需要）
                snapshot_id = None
                if create_snapshot:
                    snapshot = StateSnapshot(
                        snapshot_id=self._generate_id(),
                        thread_id=thread_id,
                        domain_state=state_data,
                        timestamp=datetime.now().isoformat(),
                        snapshot_name=snapshot_name or f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                        metadata={
                            "history_id": history_id,
                            "action": action
                        }
                    )
                    
                    # 转换为字典格式保存到Repository
                    snapshot_dict = {
                        "snapshot_id": snapshot.snapshot_id,
                        "thread_id": snapshot.thread_id,
                        "domain_state": snapshot.domain_state,
                        "timestamp": snapshot.timestamp,
                        "snapshot_name": snapshot.snapshot_name,
                        "metadata": snapshot.metadata
                    }
                    
                    # 保存到快照Repository
                    snapshot_id = await self._snapshot_repository.save_snapshot(snapshot_dict)
                
                logger.debug(f"状态保存成功: history_id={history_id}, snapshot_id={snapshot_id}")
                return history_id, snapshot_id
                
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            raise
    
    async def restore_state_from_snapshot_async(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """异步从快照恢复状态
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的快照，如果失败则返回None
        """
        try:
            async with self._transaction_async():
                # 从快照Repository加载
                snapshot_dict = await self._snapshot_repository.load_snapshot(snapshot_id)
                if not snapshot_dict:
                    return None
                
                # 创建StateSnapshot对象
                snapshot = StateSnapshot(
                    snapshot_id=snapshot_dict["snapshot_id"],
                    thread_id=snapshot_dict["thread_id"],
                    domain_state=snapshot_dict["domain_state"],
                    timestamp=snapshot_dict["timestamp"],
                    snapshot_name=snapshot_dict.get("snapshot_name", ""),
                    metadata=snapshot_dict.get("metadata", {})
                )
                
                # 记录恢复操作
                restore_entry = StateHistoryEntry(
                    history_id=self._generate_id(),
                    thread_id=snapshot.thread_id,
                    timestamp=datetime.now().isoformat(),
                    action="restore_snapshot",
                    state_diff={},
                    metadata={
                        "snapshot_id": snapshot_id,
                        "snapshot_name": snapshot.snapshot_name,
                        "snapshot_timestamp": snapshot.timestamp
                    }
                )
                
                # 转换为字典格式保存到历史Repository
                history_dict = {
                    "history_id": restore_entry.history_id,
                    "thread_id": restore_entry.thread_id,
                    "timestamp": restore_entry.timestamp,
                    "action": restore_entry.action,
                    "state_diff": restore_entry.state_diff,
                    "metadata": restore_entry.metadata
                }
                
                await self._history_repository.save_history(history_dict)
                
                logger.debug(f"状态恢复成功: snapshot_id={snapshot_id}")
                return snapshot
                
        except Exception as e:
            logger.error(f"恢复状态失败: {e}")
            return None
    
    async def batch_save_history_entries_async(self, entries: List[StateHistoryEntry]) -> List[str]:
        """异步批量保存历史记录
        
        Args:
            entries: 历史记录列表
            
        Returns:
            成功保存的历史记录ID列表
        """
        try:
            async with self._transaction_async():
                # 并发保存所有历史记录
                save_tasks = []
                for entry in entries:
                    # 转换为字典格式保存到Repository
                    history_dict = {
                        "history_id": entry.history_id,
                        "thread_id": entry.thread_id,
                        "timestamp": entry.timestamp,
                        "action": entry.action,
                        "state_diff": entry.state_diff,
                        "metadata": entry.metadata
                    }
                    
                    save_tasks.append(self._history_repository.save_history(history_dict))
                
                # 等待所有保存操作完成
                await asyncio.gather(*save_tasks)
                
                saved_ids = [entry.history_id for entry in entries]
                logger.debug(f"批量保存历史记录成功: {len(saved_ids)} 条")
                return saved_ids
                
        except Exception as e:
            logger.error(f"批量保存历史记录失败: {e}")
            raise
    
    async def batch_save_snapshots_async(self, snapshots: List[StateSnapshot]) -> List[str]:
        """异步批量保存快照
        
        Args:
            snapshots: 快照列表
            
        Returns:
            成功保存的快照ID列表
        """
        try:
            async with self._transaction_async():
                # 并发保存所有快照
                tasks = []
                for snapshot in snapshots:
                    # 转换为字典格式保存到Repository
                    snapshot_dict = {
                        "snapshot_id": snapshot.snapshot_id,
                        "thread_id": snapshot.thread_id,
                        "domain_state": snapshot.domain_state,
                        "timestamp": snapshot.timestamp,
                        "snapshot_name": snapshot.snapshot_name,
                        "metadata": snapshot.metadata
                    }
                    tasks.append(self._snapshot_repository.save_snapshot(snapshot_dict))
                
                # 并发执行所有保存操作
                saved_ids = await asyncio.gather(*tasks)
                logger.debug(f"批量保存快照成功: {len(saved_ids)} 个")
                return saved_ids
                
        except Exception as e:
            logger.error(f"批量保存快照失败: {e}")
            raise
    
    def batch_save_snapshots(self, snapshots: List[StateSnapshot]) -> List[str]:
        """批量保存快照（同步适配器）
        
        Args:
            snapshots: 快照列表
            
        Returns:
            成功保存的快照ID列表
        """
        # 添加弃用警告
        import warnings
        warnings.warn(
            "batch_save_snapshots is deprecated, use batch_save_snapshots_async instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        # 调用异步版本
        return asyncio.run(self.batch_save_snapshots_async(snapshots))
    
    async def cleanup_thread_data_async(self, thread_id: str,
                                     keep_history: int = 100,
                                     keep_snapshots: int = 10) -> Dict[str, int]:
        """异步清理线程数据
        
        Args:
            thread_id: 线程ID
            keep_history: 保留的历史记录数量
            keep_snapshots: 保留的快照数量
            
        Returns:
            清理统计信息
        """
        try:
            async with self._transaction_async():
                # 并发获取历史记录和快照
                history_task = self._history_repository.get_history(thread_id, limit=1000)
                snapshots_task = self._snapshot_repository.get_snapshots(thread_id, limit=1000)
                
                history_entries_dicts, snapshots_dicts = await asyncio.gather(history_task, snapshots_task)
                
                # 清理历史记录
                deleted_history = 0
                if len(history_entries_dicts) > keep_history:
                    to_delete = history_entries_dicts[:-keep_history]
                    # 并发删除历史记录
                    delete_tasks = [
                        self._history_repository.delete_history(entry_dict["history_id"])
                        for entry_dict in to_delete
                    ]
                    delete_results = await asyncio.gather(*delete_tasks)
                    deleted_history = sum(1 for result in delete_results if result)
                
                # 清理快照
                deleted_snapshots = 0
                if len(snapshots_dicts) > keep_snapshots:
                    to_delete = snapshots_dicts[:-keep_snapshots]
                    # 并发删除快照
                    delete_tasks = [
                        self._snapshot_repository.delete_snapshot(snapshot_dict["snapshot_id"])
                        for snapshot_dict in to_delete
                    ]
                    delete_results = await asyncio.gather(*delete_tasks)
                    deleted_snapshots = sum(1 for result in delete_results if result)
                
                cleanup_stats: Dict[str, int] = {
                    "deleted_history": deleted_history,
                    "deleted_snapshots": deleted_snapshots
                }
                
                logger.info(f"线程数据清理完成: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"清理代理数据失败: {e}")
            raise
    
    async def get_comprehensive_statistics_async(self) -> Dict[str, Any]:
        """异步获取综合统计信息
        
        Returns:
            包含历史和快照的统计信息
        """
        try:
            # 并发获取历史和快照统计信息
            history_task = self._history_repository.get_history_statistics()
            snapshot_task = self._snapshot_repository.get_snapshot_statistics()
            
            history_stats, snapshot_stats = await asyncio.gather(history_task, snapshot_task)
            
            combined_stats = {
                "history": history_stats,
                "snapshots": snapshot_stats,
                "total_storage_size": history_stats.get("storage_size_bytes", 0) +
                                   snapshot_stats.get("storage_size_bytes", 0),
                "last_updated": datetime.now().isoformat()
            }
            
            return combined_stats
            
        except Exception as e:
            logger.error(f"获取综合统计信息失败: {e}")
            return {}
    
    async def export_thread_data_async(self, thread_id: str,
                                    include_history: bool = True,
                                    include_snapshots: bool = True) -> Dict[str, Any]:
        """异步导出线程数据
        
        Args:
            thread_id: 线程ID
            include_history: 是否包含历史记录
            include_snapshots: 是否包含快照
            
        Returns:
            导出的数据
        """
        try:
            export_data: Dict[str, Any] = {
                "thread_id": thread_id,
                "export_timestamp": datetime.now().isoformat(),
                "history": [],
                "snapshots": []
            }
            
            # 并发获取历史记录和快照
            tasks = []
            if include_history:
                tasks.append(self._history_repository.get_history(thread_id, limit=10000))
            if include_snapshots:
                tasks.append(self._snapshot_repository.get_snapshots(thread_id, limit=1000))
            
            results = await asyncio.gather(*tasks)
            
            if include_history:
                export_data["history"] = results[0] if isinstance(results[0], list) else []
                if include_snapshots:
                    export_data["snapshots"] = results[1] if isinstance(results[1], list) else []
            elif include_snapshots:
                export_data["snapshots"] = results[0] if isinstance(results[0], list) else []
            
            logger.debug(f"线程数据导出完成: thread_id={thread_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"导出代理数据失败: {e}")
            raise
    
    async def import_thread_data_async(self, import_data: Dict[str, Any],
                                    overwrite: bool = False) -> Dict[str, int]:
        """异步导入线程数据
        
        Args:
            import_data: 导入的数据
            overwrite: 是否覆盖现有数据
            
        Returns:
            导入统计信息
        """
        try:
            thread_id = import_data.get("thread_id")
            if not thread_id:
                raise ValueError("导入数据缺少thread_id")
            
            async with self._transaction_async():
                # 如果需要覆盖，先清理现有数据
                if overwrite:
                    await self._history_repository.clear_thread_history(thread_id)
                
                # 并发导入历史记录
                history_tasks = [
                    self._history_repository.save_history(history_data)
                    for history_data in import_data.get("history", [])
                ]
                history_ids = await asyncio.gather(*history_tasks)
                imported_history = len(history_ids)
                
                # 并发导入快照
                snapshot_tasks = [
                    self._snapshot_repository.save_snapshot(snapshot_data)
                    for snapshot_data in import_data.get("snapshots", [])
                ]
                snapshot_ids = await asyncio.gather(*snapshot_tasks)
                imported_snapshots = len(snapshot_ids)
                
                import_stats = {
                    "imported_history": imported_history,
                    "imported_snapshots": imported_snapshots,
                    "thread_id": thread_id
                }
                
                logger.info(f"线程数据导入完成: {import_stats}")
                return import_stats
                
        except Exception as e:
            logger.error(f"导入代理数据失败: {e}")
            raise
    
    async def get_all_thread_ids_async(self) -> List[str]:
        """获取所有线程ID
        
        通过历史记录和快照的统计信息获取所有线程ID列表。
        
        Returns:
            线程ID列表
        """
        try:
            # 获取历史记录和快照的统计信息
            history_stats = await self._history_repository.get_history_statistics()
            snapshot_stats = await self._snapshot_repository.get_snapshot_statistics()
            
            # 从统计信息中提取线程ID
            thread_ids = set()
            
            # 从历史记录统计中获取线程ID
            if isinstance(history_stats, dict):
                # 如果统计信息包含thread_ids字段
                if "thread_ids" in history_stats:
                    thread_ids.update(history_stats["thread_ids"])
                # 如果统计信息包含threads字段
                elif "threads" in history_stats:
                    thread_ids.update(history_stats["threads"].keys())
            
            # 从快照统计中获取线程ID
            if isinstance(snapshot_stats, dict):
                # 如果统计信息包含thread_ids字段
                if "thread_ids" in snapshot_stats:
                    thread_ids.update(snapshot_stats["thread_ids"])
                # 如果统计信息包含threads字段
                elif "threads" in snapshot_stats:
                    thread_ids.update(snapshot_stats["threads"].keys())
            
            # 如果统计信息中没有线程ID，尝试通过查询获取
            if not thread_ids:
                logger.warning("无法从统计信息获取线程ID，尝试通过查询获取")
                
                # 尝试通过历史记录获取线程ID
                # 这里需要Repository提供获取所有线程ID的方法
                # 暂时使用空列表，需要在Repository接口中添加相应方法
                logger.warning("Repository接口需要添加获取所有线程ID的方法")
            
            thread_id_list = sorted(list(thread_ids))
            logger.debug(f"获取到 {len(thread_id_list)} 个线程ID: {thread_id_list}")
            return thread_id_list
            
        except Exception as e:
            logger.error(f"获取所有线程ID失败: {e}")
            return []
    
    async def get_all_threads_data_async(self) -> Dict[str, Dict[str, Any]]:
        """获取所有线程的完整数据
        
        Returns:
            线程ID到线程数据的映射
        """
        try:
            # 获取所有线程ID
            thread_ids = await self.get_all_thread_ids_async()
            
            if not thread_ids:
                logger.warning("没有找到任何线程ID")
                return {}
            
            logger.info(f"开始获取 {len(thread_ids)} 个线程的完整数据")
            
            # 并发获取所有线程的数据
            tasks = [
                self.export_thread_data_async(
                    thread_id=thread_id,
                    include_history=True,
                    include_snapshots=True
                )
                for thread_id in thread_ids
            ]
            
            # 等待所有任务完成
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理结果
            threads_data = {}
            successful_exports = 0
            failed_exports = 0
            
            for i, result in enumerate(results):
                thread_id = thread_ids[i]
                
                if isinstance(result, Exception):
                    logger.error(f"获取线程 {thread_id} 数据失败: {result}")
                    failed_exports += 1
                    # 为失败的线程创建空数据结构
                    threads_data[thread_id] = {
                        "thread_id": thread_id,
                        "export_timestamp": datetime.now().isoformat(),
                        "history": [],
                        "snapshots": [],
                        "error": str(result)
                    }
                elif isinstance(result, dict):
                    threads_data[thread_id] = result
                    successful_exports += 1
                else:
                    logger.error(f"获取线程 {thread_id} 数据返回了无效类型: {type(result)}")
                    failed_exports += 1
                    threads_data[thread_id] = {
                        "thread_id": thread_id,
                        "export_timestamp": datetime.now().isoformat(),
                        "history": [],
                        "snapshots": [],
                        "error": f"Invalid data type: {type(result)}"
                    }
            
            logger.info(f"线程数据获取完成: 成功 {successful_exports}, 失败 {failed_exports}")
            return threads_data
            
        except Exception as e:
            logger.error(f"获取所有线程数据失败: {e}")
            return {}
    
    @contextmanager
    def _transaction(self) -> Generator[None, None, None]:
        """事务上下文管理器 - 简化版本，Repository本身处理事务"""
        if not self._enable_transactions:
            yield
            return
        
        if self._transaction_active:
            # 嵌套事务，直接执行
            yield
            return
        
        self._transaction_active = True
        try:
            yield
            logger.debug("操作执行成功")
        except Exception as e:
            logger.error(f"操作执行失败: {e}")
            raise
        finally:
            self._transaction_active = False
    
    @contextlib.asynccontextmanager
    async def _transaction_async(self) -> AsyncGenerator[None, None]:
        """异步事务上下文管理器 - 简化版本，Repository本身处理事务"""
        if not self._enable_transactions:
            yield
            return
        
        if self._transaction_active:
            # 嵌套事务，直接执行
            yield
            return
        
        self._transaction_active = True
        try:
            yield
            logger.debug("异步操作执行成功")
        except Exception as e:
            logger.error(f"异步操作执行失败: {e}")
            raise
        finally:
            self._transaction_active = False
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        import uuid
        return str(uuid.uuid4())
    
    def _calculate_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异"""
        from src.core.state.entities import StateDiff
        diff = StateDiff.calculate(old_state, new_state)
        return diff.to_dict()


class StateBackupService:
    """状态备份服务
    
    提供状态数据的备份和恢复功能。
    """
    
    def __init__(self, persistence_service: StatePersistenceService):
        """初始化备份服务
        
        Args:
            persistence_service: 持久化服务
        """
        self._persistence_service = persistence_service
    
    async def create_full_backup_async(self, backup_path: str) -> bool:
        """异步创建完整备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功创建备份
        """
        try:
            import json
            import os
            import aiofiles
            
            # 确保备份目录存在
            backup_dir = os.path.dirname(backup_path)
            if backup_dir and not os.path.exists(backup_dir):
                os.makedirs(backup_dir, exist_ok=True)
            
            logger.info(f"开始创建完整备份: {backup_path}")
            
            # 获取所有线程的数据
            threads_data = await self._persistence_service.get_all_threads_data_async()
            
            # 构建备份数据结构
            backup_data = {
                "backup_metadata": {
                    "backup_timestamp": datetime.now().isoformat(),
                    "version": "1.0",
                    "total_threads": len(threads_data),
                    "backup_type": "full_backup"
                },
                "threads": threads_data,
                "statistics": {
                    "total_history_entries": sum(
                        len(thread_data.get("history", []))
                        for thread_data in threads_data.values()
                    ),
                    "total_snapshots": sum(
                        len(thread_data.get("snapshots", []))
                        for thread_data in threads_data.values()
                    )
                }
            }
            
            # 异步写入备份文件
            async with aiofiles.open(backup_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(backup_data, ensure_ascii=False, indent=2))
            
            # 记录备份统计信息
            stats = backup_data.get("statistics", {})
            if isinstance(stats, dict):
                metadata = backup_data.get("backup_metadata", {})
                if isinstance(metadata, dict):
                    logger.info(f"完整备份创建成功: {backup_path}")
                    logger.info(f"备份统计: 线程数量 {metadata.get('total_threads', 0)}, "
                               f"历史记录 {stats.get('total_history_entries', 0)}, "
                               f"快照 {stats.get('total_snapshots', 0)}")
                else:
                    logger.info(f"完整备份创建成功: {backup_path}")
            else:
                logger.info(f"完整备份创建成功: {backup_path}")
            
            return True
            
        except Exception as e:
            logger.error(f"创建完整备份失败: {e}")
            return False
    
    async def restore_full_backup_async(self, backup_path: str) -> bool:
        """异步从完整备份恢复
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功恢复
        """
        try:
            import json
            import os
            import aiofiles
            
            # 检查备份文件是否存在
            if not os.path.exists(backup_path):
                logger.error(f"备份文件不存在: {backup_path}")
                return False
            
            logger.info(f"开始从备份恢复: {backup_path}")
            
            # 异步读取备份文件
            async with aiofiles.open(backup_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                backup_data = json.loads(content)
            
            # 验证备份数据格式
            if "agents" not in backup_data:
                logger.error("备份数据格式错误: 缺少agents字段")
                return False
            
            threads_data = backup_data.get("threads", {})
            total_threads = len(threads_data)
            
            if total_threads == 0:
                logger.warning("备份文件中没有线程数据")
                return True
            
            logger.info(f"准备恢复 {total_threads} 个线程的数据")
            
            # 并发恢复数据
            restore_tasks = []
            for thread_id, thread_data in threads_data.items():
                restore_tasks.append(self._persistence_service.import_thread_data_async(thread_data, overwrite=True))
            
            # 并发执行所有恢复操作
            restore_results = await asyncio.gather(*restore_tasks, return_exceptions=True)
            
            # 统计结果
            successful_restores = 0
            failed_restores = 0
            
            for i, result in enumerate(restore_results):
                thread_id = list(threads_data.keys())[i]
                if isinstance(result, Exception):
                    failed_restores += 1
                    logger.error(f"线程 {thread_id} 恢复失败: {result}")
                else:
                    successful_restores += 1
                    logger.debug(f"线程 {thread_id} 恢复成功")
            
            # 记录恢复统计信息
            logger.info(f"备份恢复完成: {backup_path}")
            logger.info(f"恢复统计: 成功 {successful_restores}, 失败 {failed_restores}")
            
            if failed_restores > 0:
                logger.warning(f"有 {failed_restores} 个线程恢复失败")
            
            return failed_restores == 0
            
        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")
            return False
    
    def create_full_backup(self, backup_path: str) -> bool:
        """创建完整备份（同步适配器）
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功创建备份
        """
        # 添加弃用警告
        import warnings
        warnings.warn(
            "create_full_backup is deprecated, use create_full_backup_async instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        # 调用异步版本
        return asyncio.run(self.create_full_backup_async(backup_path))
    
    def restore_full_backup(self, backup_path: str) -> bool:
        """从完整备份恢复（同步适配器）
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功恢复
        """
        # 添加弃用警告
        import warnings
        warnings.warn(
            "restore_full_backup is deprecated, use restore_full_backup_async instead",
            DeprecationWarning,
            stacklevel=2
        )
        
        # 调用异步版本
        return asyncio.run(self.restore_full_backup_async(backup_path))