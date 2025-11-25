"""文件 Repository 基类"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .base import BaseRepository
from .utils import FileUtils


class FileBaseRepository(BaseRepository):
    """文件Repository基类"""
    
    def __init__(self, config: Dict[str, Any]):
        """初始化文件基类
        
        Args:
            config: 配置参数
        """
        super().__init__(config)
        self.base_path = config.get("base_path", "data/files")
        FileUtils.ensure_directory(self.base_path)
        self.logger.info(f"{self.__class__.__name__}初始化完成: {self.base_path}")
    
    def _get_item_file(self, category: str, item_id: str) -> Any:
        """获取项目文件路径"""
        return Path(self.base_path) / category / f"{item_id}.json"
    
    def _save_item(self, category: str, item_id: str, data: Dict[str, Any]) -> None:
        """保存项目到文件"""
        file_path = self._get_item_file(category, item_id)
        FileUtils.save_json(file_path, data)
    
    def _load_item(self, category: str, item_id: str) -> Optional[Dict[str, Any]]:
        """从文件加载项目"""
        file_path = self._get_item_file(category, item_id)
        return FileUtils.load_json(file_path)
    
    def _delete_item(self, category: str, item_id: str) -> bool:
        """删除项目文件"""
        file_path = self._get_item_file(category, item_id)
        return FileUtils.delete_file(file_path)
    
    def _list_items(self, category: str) -> List[Dict[str, Any]]:
        """列出分类下的所有项目"""
        category_dir = Path(self.base_path) / category
        return FileUtils.load_all_json(category_dir)