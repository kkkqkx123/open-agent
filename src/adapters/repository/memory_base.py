"""内存 Repository 基类"""

from typing import Dict, Any, List, Optional

from .base import BaseRepository


class MemoryBaseRepository(BaseRepository):
    """内存Repository基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化内存基类
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self._storage: Dict[str, Dict[str, Any]] = {}
        self._indexes: Dict[str, Dict[str, List[str]]] = {}
        self.logger.info(f"{self.__class__.__name__}初始化完成")
    
    def _add_to_index(self, index_name: str, key: str, item_id: str) -> None:
        """添加到索引"""
        if index_name not in self._indexes:
            self._indexes[index_name] = {}
        if key not in self._indexes[index_name]:
            self._indexes[index_name][key] = []
        if item_id not in self._indexes[index_name][key]:
            self._indexes[index_name][key].append(item_id)
    
    def _remove_from_index(self, index_name: str, key: str, item_id: str) -> None:
        """从索引中移除"""
        if (index_name in self._indexes and 
            key in self._indexes[index_name] and 
            item_id in self._indexes[index_name][key]):
            self._indexes[index_name][key].remove(item_id)
            if not self._indexes[index_name][key]:
                del self._indexes[index_name][key]
            if not self._indexes[index_name]:
                del self._indexes[index_name]
    
    def _get_from_index(self, index_name: str, key: str) -> List[str]:
        """从索引获取"""
        return self._indexes.get(index_name, {}).get(key, [])
    
    def _save_item(self, item_id: str, data: Dict[str, Any]) -> None:
        """保存项目"""
        self._storage[item_id] = data.copy()
    
    def _load_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """加载项目"""
        item = self._storage.get(item_id)
        return item.copy() if item else None
    
    def _delete_item(self, item_id: str) -> bool:
        """删除项目"""
        if item_id in self._storage:
            del self._storage[item_id]
            return True
        return False