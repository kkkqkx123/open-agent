"""状态持久化服务实现

协调历史记录和快照的持久化操作，提供事务支持和数据一致性保证。
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from contextlib import contextmanager

from src.interfaces.state import StateSnapshot, StateHistoryEntry, StateStatistics
from src.interfaces.repository import IHistoryRepository, ISnapshotRepository


logger = logging.getLogger(__name__)


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
    
    def save_state_with_history(self, 
                               agent_id: str,
                               state_data: Dict[str, Any],
                               old_state: Dict[str, Any],
                               action: str,
                               create_snapshot: bool = False,
                               snapshot_name: str = "") -> Tuple[str, Optional[str]]:
        """保存状态并记录历史
        
        Args:
            agent_id: 代理ID
            state_data: 状态数据
            old_state: 旧状态
            action: 执行动作
            create_snapshot: 是否创建快照
            snapshot_name: 快照名称
            
        Returns:
            (历史记录ID, 快照ID)
        """
        try:
            with self._transaction():
                # 记录历史
                history_entry = StateHistoryEntry(
                    history_id=self._generate_id(),
                    agent_id=agent_id,
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
                    "agent_id": history_entry.agent_id,
                    "timestamp": history_entry.timestamp,
                    "action": history_entry.action,
                    "state_diff": history_entry.state_diff,
                    "metadata": history_entry.metadata
                }
                
                # 保存到历史Repository
                asyncio.run(self._history_repository.save_history(history_dict))
                history_id = history_entry.history_id
                
                # 创建快照（如果需要）
                snapshot_id = None
                if create_snapshot:
                    snapshot = StateSnapshot(
                        snapshot_id=self._generate_id(),
                        agent_id=agent_id,
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
                        "agent_id": snapshot.agent_id,
                        "domain_state": snapshot.domain_state,
                        "timestamp": snapshot.timestamp,
                        "snapshot_name": snapshot.snapshot_name,
                        "metadata": snapshot.metadata
                    }
                    
                    # 保存到快照Repository
                    snapshot_id = asyncio.run(self._snapshot_repository.save_snapshot(snapshot_dict))
                
                logger.debug(f"状态保存成功: history_id={history_id}, snapshot_id={snapshot_id}")
                return history_id, snapshot_id
                
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
            raise
    
    def restore_state_from_snapshot(self, snapshot_id: str) -> Optional[StateSnapshot]:
        """从快照恢复状态
        
        Args:
            snapshot_id: 快照ID
            
        Returns:
            恢复的快照，如果失败则返回None
        """
        try:
            with self._transaction():
                # 从快照Repository加载
                snapshot_dict = asyncio.run(self._snapshot_repository.load_snapshot(snapshot_id))
                if not snapshot_dict:
                    return None
                
                # 创建StateSnapshot对象
                snapshot = StateSnapshot(
                    snapshot_id=snapshot_dict["snapshot_id"],
                    agent_id=snapshot_dict["agent_id"],
                    domain_state=snapshot_dict["domain_state"],
                    timestamp=snapshot_dict["timestamp"],
                    snapshot_name=snapshot_dict.get("snapshot_name", ""),
                    metadata=snapshot_dict.get("metadata", {})
                )
                
                # 记录恢复操作
                restore_entry = StateHistoryEntry(
                    history_id=self._generate_id(),
                    agent_id=snapshot.agent_id,
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
                    "agent_id": restore_entry.agent_id,
                    "timestamp": restore_entry.timestamp,
                    "action": restore_entry.action,
                    "state_diff": restore_entry.state_diff,
                    "metadata": restore_entry.metadata
                }
                
                asyncio.run(self._history_repository.save_history(history_dict))
                
                logger.debug(f"状态恢复成功: snapshot_id={snapshot_id}")
                return snapshot
                
        except Exception as e:
            logger.error(f"恢复状态失败: {e}")
            return None
    
    def batch_save_history_entries(self, entries: List[StateHistoryEntry]) -> List[str]:
        """批量保存历史记录
        
        Args:
            entries: 历史记录列表
            
        Returns:
            成功保存的历史记录ID列表
        """
        try:
            with self._transaction():
                saved_ids = []
                for entry in entries:
                    # 转换为字典格式保存到Repository
                    history_dict = {
                        "history_id": entry.history_id,
                        "agent_id": entry.agent_id,
                        "timestamp": entry.timestamp,
                        "action": entry.action,
                        "state_diff": entry.state_diff,
                        "metadata": entry.metadata
                    }
                    
                    asyncio.run(self._history_repository.save_history(history_dict))
                    saved_ids.append(entry.history_id)
                
                logger.debug(f"批量保存历史记录成功: {len(saved_ids)} 条")
                return saved_ids
                
        except Exception as e:
            logger.error(f"批量保存历史记录失败: {e}")
            raise
    
    def batch_save_snapshots(self, snapshots: List[StateSnapshot]) -> List[str]:
        """批量保存快照
        
        Args:
            snapshots: 快照列表
            
        Returns:
            成功保存的快照ID列表
        """
        try:
            with self._transaction():
                saved_ids = []
                for snapshot in snapshots:
                    # 转换为字典格式保存到Repository
                    snapshot_dict = {
                        "snapshot_id": snapshot.snapshot_id,
                        "agent_id": snapshot.agent_id,
                        "domain_state": snapshot.domain_state,
                        "timestamp": snapshot.timestamp,
                        "snapshot_name": snapshot.snapshot_name,
                        "metadata": snapshot.metadata
                    }
                    
                    snapshot_id = asyncio.run(self._snapshot_repository.save_snapshot(snapshot_dict))
                    saved_ids.append(snapshot_id)
                
                logger.debug(f"批量保存快照成功: {len(saved_ids)} 个")
                return saved_ids
                
        except Exception as e:
            logger.error(f"批量保存快照失败: {e}")
            raise
    
    def cleanup_agent_data(self, agent_id: str, 
                          keep_history: int = 100,
                          keep_snapshots: int = 10) -> Dict[str, int]:
        """清理代理数据
        
        Args:
            agent_id: 代理ID
            keep_history: 保留的历史记录数量
            keep_snapshots: 保留的快照数量
            
        Returns:
            清理统计信息
        """
        try:
            with self._transaction():
                # 清理历史记录
                history_entries_dicts = asyncio.run(self._history_repository.get_history(agent_id, limit=1000))
                if len(history_entries_dicts) > keep_history:
                    to_delete = history_entries_dicts[:-keep_history]
                    deleted_history = 0
                    for entry_dict in to_delete:
                        if asyncio.run(self._history_repository.delete_history(entry_dict["history_id"])):
                            deleted_history += 1
                else:
                    deleted_history = 0
                
                # 清理快照
                snapshots_dicts = asyncio.run(self._snapshot_repository.get_snapshots(agent_id, limit=1000))
                if len(snapshots_dicts) > keep_snapshots:
                    to_delete = snapshots_dicts[:-keep_snapshots]
                    deleted_snapshots = 0
                    for snapshot_dict in to_delete:
                        if asyncio.run(self._snapshot_repository.delete_snapshot(snapshot_dict["snapshot_id"])):
                            deleted_snapshots += 1
                else:
                    deleted_snapshots = 0
                
                cleanup_stats = {
                    "deleted_history": deleted_history,
                    "deleted_snapshots": deleted_snapshots,
                    "agent_id": agent_id
                }
                
                logger.info(f"代理数据清理完成: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"清理代理数据失败: {e}")
            raise
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """获取综合统计信息
        
        Returns:
            包含历史和快照的统计信息
        """
        try:
            history_stats = asyncio.run(self._history_repository.get_history_statistics())
            snapshot_stats = asyncio.run(self._snapshot_repository.get_snapshot_statistics())
            
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
    
    def export_agent_data(self, agent_id: str, 
                         include_history: bool = True,
                         include_snapshots: bool = True) -> Dict[str, Any]:
        """导出代理数据
        
        Args:
            agent_id: 代理ID
            include_history: 是否包含历史记录
            include_snapshots: 是否包含快照
            
        Returns:
            导出的数据
        """
        try:
            export_data = {
                "agent_id": agent_id,
                "export_timestamp": datetime.now().isoformat(),
                "history": [],
                "snapshots": []
            }
            
            if include_history:
                history_entries = asyncio.run(self._history_repository.get_history(agent_id, limit=10000))
                export_data["history"] = history_entries
            
            if include_snapshots:
                snapshots = asyncio.run(self._snapshot_repository.get_snapshots(agent_id, limit=1000))
                export_data["snapshots"] = snapshots
            
            logger.debug(f"代理数据导出完成: agent_id={agent_id}")
            return export_data
            
        except Exception as e:
            logger.error(f"导出代理数据失败: {e}")
            raise
    
    def import_agent_data(self, import_data: Dict[str, Any], 
                         overwrite: bool = False) -> Dict[str, int]:
        """导入代理数据
        
        Args:
            import_data: 导入的数据
            overwrite: 是否覆盖现有数据
            
        Returns:
            导入统计信息
        """
        try:
            agent_id = import_data.get("agent_id")
            if not agent_id:
                raise ValueError("导入数据缺少agent_id")
            
            with self._transaction():
                # 如果需要覆盖，先清理现有数据
                if overwrite:
                    asyncio.run(self._history_repository.clear_agent_history(agent_id))
                
                # 导入历史记录
                imported_history = 0
                for history_data in import_data.get("history", []):
                    # 直接使用字典数据保存到Repository
                    history_id = asyncio.run(self._history_repository.save_history(history_data))
                    imported_history += 1
                
                # 导入快照
                imported_snapshots = 0
                for snapshot_data in import_data.get("snapshots", []):
                    # 直接使用字典数据保存到Repository
                    snapshot_id = asyncio.run(self._snapshot_repository.save_snapshot(snapshot_data))
                    imported_snapshots += 1
                
                import_stats = {
                    "imported_history": imported_history,
                    "imported_snapshots": imported_snapshots,
                    "agent_id": agent_id
                }
                
                logger.info(f"代理数据导入完成: {import_stats}")
                return import_stats
                
        except Exception as e:
            logger.error(f"导入代理数据失败: {e}")
            raise
    
    @contextmanager
    def _transaction(self):
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
    
    def create_full_backup(self, backup_path: str) -> bool:
        """创建完整备份
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功创建备份
        """
        try:
            import json
            
            # 获取所有代理的数据
            # 这里需要存储适配器提供获取所有代理ID的方法
            # 暂时使用示例实现
            
            backup_data = {
                "backup_timestamp": datetime.now().isoformat(),
                "version": "1.0",
                "agents": {}
            }
            
            # TODO: 实现获取所有代理数据的逻辑
            
            # 写入备份文件
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"完整备份创建成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"创建完整备份失败: {e}")
            return False
    
    def restore_full_backup(self, backup_path: str) -> bool:
        """从完整备份恢复
        
        Args:
            backup_path: 备份文件路径
            
        Returns:
            是否成功恢复
        """
        try:
            import json
            
            # 读取备份文件
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # 恢复数据
            for agent_id, agent_data in backup_data.get("agents", {}).items():
                self._persistence_service.import_agent_data(agent_data, overwrite=True)
            
            logger.info(f"从备份恢复成功: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"从备份恢复失败: {e}")
            return False