import pickle
import zlib
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass, field

from .interfaces import IStateHistoryManager, StateHistoryEntry


class StateHistoryManager(IStateHistoryManager):
    """状态历史管理器"""
    
    def __init__(self, max_history_size: int = 1000):
        self.max_history_size = max_history_size
        self._setup_storage()
    
    def _setup_storage(self):
        """设置存储后端"""
        # 使用内存存储作为默认实现
        self.history_entries: List[StateHistoryEntry] = []
        self.agent_history: Dict[str, List[str]] = {}  # agent_id -> history_id列表
        self.history_index: Dict[str, StateHistoryEntry] = {}  # history_id -> entry
    
    def record_state_change(self, agent_id: str, old_state: Dict[str, Any], 
                          new_state: Dict[str, Any], action: str) -> str:
        """记录状态变化"""
        # 计算状态差异
        state_diff = self._calculate_state_diff(old_state, new_state)
        
        # 创建历史记录
        history_entry = StateHistoryEntry(
            history_id=self._generate_history_id(),
            agent_id=agent_id,
            timestamp=datetime.now(),
            action=action,
            state_diff=state_diff,
            metadata={
                "old_state_keys": list(old_state.keys()),
                "new_state_keys": list(new_state.keys())
            }
        )
        
        # 压缩差异数据
        history_entry.compressed_diff = self._compress_diff(state_diff)
        
        # 保存记录
        self._save_history_entry(history_entry)
        
        # 清理旧记录
        self._cleanup_old_entries(agent_id)
        
        return history_entry.history_id
    
    def _calculate_state_diff(self, old_state: Dict[str, Any], new_state: Dict[str, Any]) -> Dict[str, Any]:
        """计算状态差异"""
        diff = {}
        
        # 检查新增和修改的键
        for key, new_value in new_state.items():
            if key not in old_state:
                diff[f"added_{key}"] = new_value
            elif old_state[key] != new_value:
                diff[f"modified_{key}"] = {
                    "old": old_state[key],
                    "new": new_value
                }
        
        # 检查删除的键
        for key in old_state:
            if key not in new_state:
                diff[f"removed_{key}"] = old_state[key]
        
        return diff
    
    def _compress_diff(self, diff: Dict[str, Any]) -> bytes:
        """压缩差异数据"""
        serialized_diff = pickle.dumps(diff)
        return zlib.compress(serialized_diff)
    
    def _decompress_diff(self, compressed_diff: bytes) -> Dict[str, Any]:
        """解压缩差异数据"""
        decompressed_data = zlib.decompress(compressed_diff)
        return pickle.loads(decompressed_data)
    
    def _generate_history_id(self) -> str:
        """生成历史记录ID"""
        return str(uuid.uuid4())
    
    def _save_history_entry(self, entry: StateHistoryEntry):
        """保存历史记录"""
        # 添加到全局索引
        self.history_index[entry.history_id] = entry
        
        # 添加到Agent历史列表
        if entry.agent_id not in self.agent_history:
            self.agent_history[entry.agent_id] = []
        
        self.agent_history[entry.agent_id].append(entry.history_id)
        
        # 添加到全局列表
        self.history_entries.append(entry)
    
    def _cleanup_old_entries(self, agent_id: str):
        """清理旧记录"""
        if agent_id in self.agent_history:
            history_ids = self.agent_history[agent_id]
            if len(history_ids) > self.max_history_size:
                # 删除最旧的记录
                excess_count = len(history_ids) - self.max_history_size
                for i in range(excess_count):
                    oldest_history_id = history_ids.pop(0)
                    if oldest_history_id in self.history_index:
                        del self.history_index[oldest_history_id]
                
                # 同时清理全局列表
                self.history_entries = [
                    entry for entry in self.history_entries 
                    if entry.agent_id != agent_id or entry.history_id in history_ids
                ]
    
    def get_state_history(self, agent_id: str, limit: int = 100) -> List[StateHistoryEntry]:
        """获取状态历史"""
        if agent_id not in self.agent_history:
            return []
        
        # 获取最新的历史记录ID
        history_ids = self.agent_history[agent_id][-limit:]
        history_entries = []
        
        for history_id in history_ids:
            entry = self.history_index.get(history_id)
            if entry:
                # 如果需要，解压缩差异数据
                if entry.compressed_diff and not entry.state_diff:
                    entry.state_diff = self._decompress_diff(entry.compressed_diff)
                history_entries.append(entry)
        
        # 按时间戳排序（最新的在前）
        history_entries.sort(key=lambda x: x.timestamp, reverse=True)
        return history_entries
    
    def replay_history(self, agent_id: str, base_state: Dict[str, Any], 
                      until_timestamp: Optional[datetime] = None) -> Dict[str, Any]:
        """重放历史记录到指定时间点"""
        current_state = base_state.copy()
        history_entries = self.get_state_history(agent_id, limit=1000)
        
        # 按时间顺序应用变化（从最旧到最新）
        history_entries.sort(key=lambda x: x.timestamp)
        
        for entry in history_entries:
            if until_timestamp and entry.timestamp > until_timestamp:
                break
            current_state = self._apply_state_diff(current_state, entry.state_diff)
        
        return current_state
    
    def _apply_state_diff(self, current_state: Dict[str, Any], diff: Dict[str, Any]) -> Dict[str, Any]:
        """应用状态差异"""
        new_state = current_state.copy()
        
        for key, value in diff.items():
            if key.startswith("added_"):
                new_key = key[6:]  # 移除 "added_" 前缀
                new_state[new_key] = value
            elif key.startswith("modified_"):
                new_key = key[9:]  # 移除 "modified_" 前缀
                if isinstance(value, dict) and "new" in value:
                    new_state[new_key] = value["new"]
            elif key.startswith("removed_"):
                new_key = key[8:]  # 移除 "removed_" 前缀
                if new_key in new_state:
                    del new_state[new_key]
        
        return new_state