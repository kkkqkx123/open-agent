"""文件处理工具类

提供Repository中文件操作的通用方法。
"""

import json
from src.interfaces.dependency_injection import get_logger
from pathlib import Path
from typing import Dict, Any, List, Optional

logger = get_logger(__name__)


class FileUtils:
    """文件处理工具类"""
    
    @staticmethod
    def ensure_directory(path: Path) -> None:
        """确保目录存在
        
        Args:
            path: 目录路径
        """
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"创建目录失败 {path}: {e}")
            raise
    
    @staticmethod
    def save_json(file_path: Path, data: Dict[str, Any], ensure_ascii: bool = False, indent: int = 2) -> None:
        """保存数据为JSON文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
        """
        try:
            FileUtils.ensure_directory(file_path.parent)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=ensure_ascii, indent=indent)
        except Exception as e:
            logger.error(f"保存JSON文件失败 {file_path}: {e}")
            raise
    
    @staticmethod
    def load_json(file_path: Path) -> Optional[Dict[str, Any]]:
        """加载JSON文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据，如果文件不存在返回None
        """
        try:
            if not file_path.exists():
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载JSON文件失败 {file_path}: {e}")
            raise
    
    @staticmethod
    def load_json_safe(file_path: Path) -> Dict[str, Any]:
        """安全加载JSON文件，失败时返回空字典
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据，失败时返回空字典
        """
        try:
            data = FileUtils.load_json(file_path)
            return data if data is not None else {}
        except Exception as e:
            logger.warning(f"安全加载JSON文件失败 {file_path}: {e}")
            return {}
    
    @staticmethod
    def delete_file(file_path: Path) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if file_path.exists():
                file_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"删除文件失败 {file_path}: {e}")
            return False
    
    @staticmethod
    def list_json_files(directory: Path) -> List[Path]:
        """列出目录中的所有JSON文件
        
        Args:
            directory: 目录路径
            
        Returns:
            JSON文件路径列表
        """
        try:
            if not directory.exists():
                return []
            
            return list(directory.glob("*.json"))
        except Exception as e:
            logger.error(f"列出JSON文件失败 {directory}: {e}")
            return []
    
    @staticmethod
    def load_all_json(directory: Path) -> List[Dict[str, Any]]:
        """加载目录中的所有JSON文件
        
        Args:
            directory: 目录路径
            
        Returns:
            加载的数据列表
        """
        results = []
        for file_path in FileUtils.list_json_files(directory):
            try:
                data = FileUtils.load_json(file_path)
                if data is not None:
                    results.append(data)
            except Exception as e:
                logger.warning(f"加载JSON文件失败 {file_path}: {e}")
                continue
        
        return results
    
    @staticmethod
    def find_file_in_directories(base_dir: Path, filename: str) -> Optional[Path]:
        """在所有子目录中查找文件
        
        Args:
            base_dir: 基础目录
            filename: 文件名
            
        Returns:
            找到的文件路径，未找到返回None
        """
        try:
            for subdir in base_dir.iterdir():
                if subdir.is_dir():
                    file_path = subdir / filename
                    if file_path.exists():
                        return file_path
            return None
        except Exception as e:
            logger.error(f"查找文件失败 {base_dir}/{filename}: {e}")
            return None