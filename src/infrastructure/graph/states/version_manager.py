"""状态版本管理器

提供状态版本控制和历史追踪功能。
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import copy

from .base_manager import BaseStateManager


class VersionStateManager(BaseStateManager):
    """状态版本管理器
    
    提供状态版本控制和历史追踪功能。
    """
    
    def __init__(self):
        super().__init__()
        self._state_versions: Dict[str, Dict[str, Any]] = {}
        self._version_history: Dict[str, List[Dict[str, Any]]] = {}
    
    def create_state_version(self, state_id: str, state: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None) -> str:
        """创建状态版本
        
        Args:
            state_id: 状态ID
            state: 状态对象
            metadata: 版本元数据
            
        Returns:
            版本ID
        """
        version_key = f"{state_id}_v{len(self._state_versions) + 1}"
        self._state_versions[version_key] = {
            "state": copy.deepcopy(state),
            "metadata": metadata or {},
            "timestamp": datetime.now(),
            "state_id": state_id
        }
        return version_key
    
    def get_state_version(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取指定版本的状态
        
        Args:
            version_id: 版本ID
            
        Returns:
            指定版本的状态，如果不存在则返回None
        """
        if version_id in self._state_versions:
            return copy.deepcopy(self._state_versions[version_id]["state"])
        return None
    
    def get_state_versions(self, state_id: str) -> List[Dict[str, Any]]:
        """获取指定状态的所有版本
        
        Args:
            state_id: 状态ID
            
        Returns:
            状态版本列表
        """
        versions = []
        for version_id, version_data in self._state_versions.items():
            if version_data["state_id"] == state_id:
                versions.append(copy.deepcopy(version_data["state"]))
        return versions
    
    def get_version_metadata(self, version_id: str) -> Optional[Dict[str, Any]]:
        """获取版本元数据
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本元数据，如果不存在则返回None
        """
        if version_id in self._state_versions:
            return copy.deepcopy(self._state_versions[version_id]["metadata"])
        return None
    
    def get_version_timestamp(self, version_id: str) -> Optional[datetime]:
        """获取版本时间戳
        
        Args:
            version_id: 版本ID
            
        Returns:
            版本时间戳，如果不存在则返回None
        """
        if version_id in self._state_versions:
            return self._state_versions[version_id]["timestamp"]
        return None
    
    def compare_versions(self, version1_id: str, version2_id: str) -> Dict[str, Any]:
        """比较两个版本的差异
        
        Args:
            version1_id: 第一个版本ID
            version2_id: 第二个版本ID
            
        Returns:
            差异字典
        """
        state1 = self.get_state_version(version1_id)
        state2 = self.get_state_version(version2_id)
        
        if state1 is None or state2 is None:
            return {}
        
        return self.compare_states(state1, state2)
    
    def rollback_to_version(self, state_id: str, version_id: str) -> bool:
        """回滚到指定版本
        
        Args:
            state_id: 状态ID
            version_id: 版本ID
            
        Returns:
            是否成功回滚
        """
        version_state = self.get_state_version(version_id)
        if version_state is None:
            return False
        
        # 更新当前状态
        self._states[state_id] = copy.deepcopy(version_state)
        return True