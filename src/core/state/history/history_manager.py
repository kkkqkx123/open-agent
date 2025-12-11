"""状态历史管理器

提供状态历史记录、查询和回放功能。
"""

import json
from src.interfaces.dependency_injection import get_logger
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Union, Sequence

from src.interfaces.state.base import IState
from src.infrastructure.state import IHistoryStorage, MemoryHistoryStorage, HistoryEntry
from .history_recorder import StateHistoryRecorder
from .history_player import StateHistoryPlayer
from src.interfaces.state.exceptions import StateError, StateValidationError
from src.interfaces.history.exceptions import HistoryError
from src.infrastructure.error_management import handle_error, ErrorCategory, ErrorSeverity, operation_with_retry

logger = get_logger(__name__)


class StateHistoryManager:
    """状态历史管理器
    
    提供完整的状态历史管理功能，包括记录、存储、查询和回放。
    """
    
    def __init__(self, 
                 storage: Optional[IHistoryStorage] = None,
                 max_history_size: int = 1000) -> None:
        """初始化历史管理器
        
        Args:
            storage: 历史存储后端
            max_history_size: 最大历史记录数量
        """
        self._storage = storage or MemoryHistoryStorage()
        self._max_history_size = max_history_size
        self._recorder = StateHistoryRecorder()
        self._player = StateHistoryPlayer()
    
    def record_state_change(self,
                           state: IState,
                           operation: str = "update",
                           context: Optional[Dict[str, Any]] = None) -> str:
        """记录状态变化
        
        Args:
            state: 状态对象
            operation: 操作类型
            context: 上下文信息
            
        Returns:
            str: 历史记录ID
            
        Raises:
            StateValidationError: 输入验证失败
            HistoryError: 记录操作失败
        """
        try:
            # 输入验证
            if state is None:
                raise StateValidationError("状态对象不能为None")
            
            if not isinstance(state, IState):
                raise StateValidationError(
                    f"状态对象必须实现IState接口，实际类型: {type(state).__name__}"
                )
            
            if not operation:
                raise StateValidationError("操作类型不能为空")
            
            if not isinstance(operation, str):
                raise StateValidationError(
                    f"操作类型必须是字符串，实际类型: {type(operation).__name__}"
                )
            
            # 验证状态数据可以序列化
            try:
                state_dict = state.to_dict()
                json.dumps(state_dict)  # 测试序列化
            except Exception as e:
                raise StateValidationError(
                    f"状态数据无法序列化: {e}",
                    details={"state_type": type(state).__name__}
                ) from e
            
            # 验证上下文数据可以序列化
            if context is not None:
                if not isinstance(context, dict):
                    raise StateValidationError(
                        f"上下文必须是字典类型，实际类型: {type(context).__name__}"
                    )
                try:
                    json.dumps(context)  # 测试序列化
                except Exception as e:
                    raise StateValidationError(
                        f"上下文数据无法序列化: {e}",
                        details={"context_keys": list(context.keys()) if isinstance(context, dict) else None}
                    ) from e
            
            # 创建历史记录
            try:
                history_entry = self._recorder.record_change(state, operation, context)
            except Exception as e:
                raise HistoryError(f"创建历史记录失败: {e}") from e
            
            # 验证历史记录
            if not hasattr(history_entry, 'id') or not history_entry.id:
                raise HistoryError("创建的历史记录缺少有效的ID")
            
            # 存储历史记录（带重试）
            try:
                self._store_with_retry(history_entry)
            except Exception as e:
                raise HistoryError(f"存储历史记录失败: {e}") from e
            
            # 清理旧记录
            try:
                self._cleanup_old_records()
            except Exception as e:
                # 清理失败不应该影响主要功能，只记录警告
                logger.warning(f"清理旧记录失败: {e}")
            
            logger.info(f"成功记录状态变化: {history_entry.id}")
            return history_entry.id
            
        except (StateValidationError, HistoryError):
            # 重新抛出已知异常
            raise
        except Exception as e:
            # 包装其他异常
            error_context = {
                "state_id": state.get_id() if hasattr(state, 'get_id') else None,
                "state_type": type(state).__name__ if state else None,
                "operation": operation,
                "context_keys": list(context.keys()) if context and isinstance(context, dict) else None
            }
            
            # 使用统一错误处理
            handle_error(e, error_context)
            
            raise HistoryError(
                f"记录状态变化失败: {e}",
                details={"original_error": str(e), **error_context}
            ) from e
    
    def _store_with_retry(self, history_entry, max_retries: int = 3) -> None:
        """带重试的存储操作
        
        Args:
            history_entry: 历史记录条目
            max_retries: 最大重试次数
            
        Raises:
            HistoryError: 存储失败
        """
        try:
            # 使用统一框架的重试机制
            def store_entry():
                return self._storage.save_history_entry(history_entry)
            
            # 定义可重试的异常类型
            retryable_exceptions = (
                ConnectionError,
                OSError,
                TimeoutError,
                IOError
            )
            
            # 使用统一框架的重试函数
            operation_with_retry(
                store_entry,
                max_retries=max_retries,
                retryable_exceptions=retryable_exceptions,
                context={
                    "operation": "save_history_entry",
                    "entry_id": getattr(history_entry, 'id', 'unknown'),
                    "entry_type": type(history_entry).__name__
                }
            )
            
        except Exception as e:
            # 所有重试都失败，抛出HistoryError
            raise HistoryError(
                f"存储历史记录失败，重试{max_retries}次后放弃: {e}",
                details={"last_error": str(e)}
            ) from e
    
    def get_state_history(self, 
                         state_id: str,
                         limit: Optional[int] = None) -> List[HistoryEntry]:
        """获取状态历史
        
        Args:
            state_id: 状态ID
            limit: 限制返回数量
            
        Returns:
            List[HistoryEntry]: 历史记录列表
        """
        return self._storage.get_state_history(state_id, limit)
    
    def get_state_at_time(self, 
                         state_id: str,
                         timestamp: datetime) -> Optional[IState]:
        """获取指定时间点的状态
        
        Args:
            state_id: 状态ID
            timestamp: 时间戳
            
        Returns:
            Optional[IState]: 状态对象
        """
        history_entries = self._storage.get_state_history_before(state_id, timestamp)
        
        if not history_entries:
            return None
        
        # 使用回放器重建状态
        return self._player.replay_state(history_entries)
    
    def get_state_at_version(self, 
                           state_id: str,
                           version: int) -> Optional[IState]:
        """获取指定版本的状态
        
        Args:
            state_id: 状态ID
            version: 版本号
            
        Returns:
            Optional[IState]: 状态对象
        """
        history_entries = self._storage.get_state_history_up_to_version(state_id, version)
        
        if not history_entries:
            return None
        
        # 使用回放器重建状态
        return self._player.replay_state(history_entries)
    
    def compare_states(self, 
                      state_id: str,
                      version1: int,
                      version2: int) -> Dict[str, Any]:
        """比较两个版本的状态
        
        Args:
            state_id: 状态ID
            version1: 版本1
            version2: 版本2
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        state1 = self.get_state_at_version(state_id, version1)
        state2 = self.get_state_at_version(state_id, version2)
        
        if state1 is None or state2 is None:
            return {"error": "One or both states not found"}
        
        # 比较状态数据
        differences = self._compare_state_data(state1, state2)
        
        return {
            "state_id": state_id,
            "version1": version1,
            "version2": version2,
            "differences": differences,
            "timestamp1": state1.get_updated_at(),
            "timestamp2": state2.get_updated_at()
        }
    
    def rollback_to_version(self, 
                           state_id: str,
                           version: int) -> Optional[IState]:
        """回滚到指定版本
        
        Args:
            state_id: 状态ID
            version: 版本号
            
        Returns:
            Optional[IState]: 回滚后的状态对象
        """
        target_state = self.get_state_at_version(state_id, version)
        
        if target_state is None:
            return None
        
        # 记录回滚操作
        self.record_state_change(
            target_state,
            operation="rollback",
            context={"rollback_to_version": version}
        )
        
        return target_state
    
    def rollback_to_time(self, 
                        state_id: str,
                        timestamp: datetime) -> Optional[IState]:
        """回滚到指定时间点
        
        Args:
            state_id: 状态ID
            timestamp: 时间戳
            
        Returns:
            Optional[IState]: 回滚后的状态对象
        """
        target_state = self.get_state_at_time(state_id, timestamp)
        
        if target_state is None:
            return None
        
        # 记录回滚操作
        self.record_state_change(
            target_state,
            operation="rollback",
            context={"rollback_to_timestamp": timestamp.isoformat()}
        )
        
        return target_state
    
    def get_state_timeline(self, 
                          state_id: str) -> List[Dict[str, Any]]:
        """获取状态时间线
        
        Args:
            state_id: 状态ID
            
        Returns:
            List[Dict[str, Any]]: 时间线事件列表
        """
        history_entries = self._storage.get_state_history(state_id)
        
        timeline = []
        for entry in history_entries:
            timeline.append({
                "timestamp": entry.timestamp,
                "version": entry.version,
                "operation": entry.operation,
                "context": entry.context
            })
        
        return timeline
    
    def get_statistics(self, state_id: str) -> Dict[str, Any]:
        """获取状态统计信息
        
        Args:
            state_id: 状态ID
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        history_entries = self._storage.get_state_history(state_id)
        
        if not history_entries:
            return {"error": "No history found for state"}
        
        # 计算统计信息
        total_changes = len(history_entries)
        operations = {}
        
        for entry in history_entries:
            op = entry.operation
            operations[op] = operations.get(op, 0) + 1
        
        first_change = history_entries[0].timestamp
        last_change = history_entries[-1].timestamp
        
        return {
            "state_id": state_id,
            "total_changes": total_changes,
            "operations": operations,
            "first_change": first_change,
            "last_change": last_change,
            "duration": (last_change - first_change).total_seconds() if first_change and last_change else 0
        }
    
    def clear_history(self, state_id: str) -> None:
        """清除状态历史
        
        Args:
            state_id: 状态ID
        """
        self._storage.clear_state_history(state_id)
    
    def export_history(self, 
                      state_id: str,
                      format: str = "json") -> str:
        """导出状态历史
        
        Args:
            state_id: 状态ID
            format: 导出格式
            
        Returns:
            str: 导出的历史数据
        """
        history_entries = self._storage.get_state_history(state_id)
        
        if format.lower() == "json":
            import json
            return json.dumps([entry.to_dict() for entry in history_entries], indent=2)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    def import_history(self, 
                      state_id: str,
                      data: str,
                      format: str = "json") -> None:
        """导入状态历史
        
        Args:
            state_id: 状态ID
            data: 历史数据
            format: 数据格式
        """
        if format.lower() == "json":
            import json
            history_data = json.loads(data)
            
            for entry_data in history_data:
                # 重建历史记录对象
                history_entry = self._recorder.create_from_dict(entry_data)
                self._storage.save_history_entry(history_entry)
        else:
            raise ValueError(f"Unsupported import format: {format}")
    
    def _cleanup_old_records(self) -> None:
        """清理旧记录"""
        # 获取所有状态ID
        all_state_ids = self._storage.get_all_state_ids()
        
        for state_id in all_state_ids:
            # 获取状态历史
            history = self._storage.get_state_history(state_id)
            
            # 如果超过最大数量，删除最旧的记录
            if len(history) > self._max_history_size:
                excess_count = len(history) - self._max_history_size
                oldest_entries = history[:excess_count]
                
                for entry in oldest_entries:
                    self._storage.delete_history_entry(entry.id)
    
    def _compare_state_data(self, state1: IState, state2: IState) -> Dict[str, Any]:
        """比较状态数据
        
        Args:
            state1: 状态1
            state2: 状态2
            
        Returns:
            Dict[str, Any]: 比较结果
        """
        differences = {
            "added": {},
            "removed": {},
            "modified": {}
        }
        
        # 比较数据
        data1 = state1.to_dict()
        data2 = state2.to_dict()
        
        # 找出添加的字段
        for key in data2:
            if key not in data1:
                differences["added"][key] = data2[key]
        
        # 找出删除的字段
        for key in data1:
            if key not in data2:
                differences["removed"][key] = data1[key]
        
        # 找出修改的字段
        for key in data1:
            if key in data2 and data1[key] != data2[key]:
                differences["modified"][key] = {
                    "old": data1[key],
                    "new": data2[key]
                }
        
        return differences


# 便捷函数
def create_history_manager(storage: Optional[IHistoryStorage] = None,
                          max_history_size: int = 1000) -> StateHistoryManager:
    """创建状态历史管理器的便捷函数
    
    Args:
        storage: 历史存储后端
        max_history_size: 最大历史记录数量
        
    Returns:
        StateHistoryManager: 历史管理器实例
    """
    return StateHistoryManager(storage, max_history_size)