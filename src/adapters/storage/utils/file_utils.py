"""文件存储工具类

提供文件存储相关的静态工具方法。
"""

import os
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, List, Optional
from pathlib import Path

from .common_utils import StorageCommonUtils


logger = get_logger(__name__)


class FileStorageUtils:
    """文件存储工具类
    
    提供文件存储特定的静态工具方法。
    """
    
    @staticmethod
    def save_data_to_file(file_path: str, data: Dict[str, Any]) -> None:
        """保存数据到文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        # 确保目录存在
        StorageCommonUtils.ensure_directory_exists(os.path.dirname(file_path))
        
        # 序列化数据
        serialized_data = StorageCommonUtils.serialize_data(data)
        
        # 写入文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(serialized_data)
    
    @staticmethod
    def load_data_from_file(file_path: str) -> Optional[Dict[str, Any]]:
        """从文件加载数据
        
        Args:
            file_path: 文件路径
            
        Returns:
            加载的数据或None
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = f.read()
                return StorageCommonUtils.deserialize_data(data)
        except Exception as e:
            logger.error(f"Failed to load data from file {file_path}: {e}")
            return None
    
    @staticmethod
    def delete_file(file_path: str) -> bool:
        """删除文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            是否删除成功
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {file_path}: {e}")
            return False
    
    @staticmethod
    def file_exists(file_path: str) -> bool:
        """检查文件是否存在
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件是否存在
        """
        return os.path.exists(file_path)
    
    @staticmethod
    def get_file_modified_time(file_path: str) -> float:
        """获取文件修改时间
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件修改时间戳
        """
        if not os.path.exists(file_path):
            return 0.0
        
        return os.path.getmtime(file_path)
    
    @staticmethod
    def get_file_size(file_path: str) -> int:
        """获取文件大小
        
        Args:
            file_path: 文件路径
            
        Returns:
            文件大小（字节）
        """
        if not os.path.exists(file_path):
            return 0
        
        return os.path.getsize(file_path)
    
    @staticmethod
    def list_files_in_directory(
        dir_path: str, 
        pattern: str = "*.json",
        recursive: bool = False
    ) -> List[str]:
        """列出目录中的文件
        
        Args:
            dir_path: 目录路径
            pattern: 文件模式
            recursive: 是否递归搜索
            
        Returns:
            文件路径列表
        """
        if not os.path.exists(dir_path):
            return []
        
        path_obj = Path(dir_path)
        
        if recursive:
            files = list(path_obj.rglob(pattern))
        else:
            files = list(path_obj.glob(pattern))
        
        return [str(f) for f in files]
    
    @staticmethod
    def calculate_directory_size(directory: str) -> int:
        """获取目录总大小
        
        Args:
            directory: 目录路径
            
        Returns:
            目录大小（字节），如果目录不存在返回0
        """
        if not os.path.exists(directory):
            return 0
        
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    if os.path.isfile(file_path) and os.path.exists(file_path):
                        try:
                            total_size += os.path.getsize(file_path)
                        except (OSError, IOError):
                            # 忽略无法访问的文件
                            pass
        except (OSError, IOError) as e:
            logger.error(f"Error calculating directory size for {directory}: {e}")
        
        return total_size
    
    @staticmethod
    def validate_file_size(file_path: str, max_size: int) -> bool:
        """验证文件大小是否超过限制
        
        Args:
            file_path: 文件路径
            max_size: 最大大小（字节）
            
        Returns:
            文件大小是否在限制内
        """
        if not os.path.exists(file_path):
            return True  # 不存在的文件认为有效
        
        try:
            file_size = os.path.getsize(file_path)
            return file_size <= max_size
        except (OSError, IOError):
            return False
    
    @staticmethod
    def count_files_in_directory(
        directory: str,
        pattern: str = "*.json",
        recursive: bool = True
    ) -> int:
        """计算目录中文件的数量
        
        Args:
            directory: 目录路径
            pattern: 文件模式
            recursive: 是否递归计数
            
        Returns:
            文件数量
        """
        if not os.path.exists(directory):
            return 0
        
        path_obj = Path(directory)
        
        if recursive:
            files = list(path_obj.rglob(pattern))
        else:
            files = list(path_obj.glob(pattern))
        
        return len(files)
    
    @staticmethod
    def validate_directory_structure(
        base_path: str,
        max_files_per_directory: Optional[int] = None,
        max_directory_size: Optional[int] = None
    ) -> Dict[str, Any]:
        """验证目录结构是否符合限制
        
        Args:
            base_path: 基础路径
            max_files_per_directory: 每个目录的最大文件数（可选）
            max_directory_size: 最大目录大小（字节，可选）
            
        Returns:
            验证结果字典，包含：
                - is_valid: 是否有效
                - violations: 违规列表
                - current_files: 当前文件数
                - current_size_bytes: 当前大小
                - current_size_mb: 当前大小（MB）
        """
        result: Dict[str, Any] = {
            "is_valid": True,
            "violations": []
        }
        
        if not os.path.exists(base_path):
            return result
        
        # 统计文件数
        current_files = FileStorageUtils.count_files_in_directory(base_path)
        result["current_files"] = current_files
        
        # 统计目录大小
        current_size = FileStorageUtils.calculate_directory_size(base_path)
        result["current_size_bytes"] = current_size
        result["current_size_mb"] = round(current_size / (1024 * 1024), 2)
        
        # 检查文件数限制
        if max_files_per_directory and current_files > max_files_per_directory:
            result["is_valid"] = False
            result["violations"].append(
                f"File count {current_files} exceeds limit {max_files_per_directory}"
            )
        
        # 检查目录大小限制
        if max_directory_size and current_size > max_directory_size:
            result["is_valid"] = False
            result["violations"].append(
                f"Directory size {current_size} bytes exceeds limit {max_directory_size} bytes"
            )
        
        return result
    
    @staticmethod
    def get_directory_structure_info(
        base_path: str,
        directory_structure: str = "flat"
    ) -> Dict[str, Any]:
        """获取目录结构的详细信息
        
        Args:
            base_path: 基础路径
            directory_structure: 目录组织方式
            
        Returns:
            目录结构信息
        """
        if not os.path.exists(base_path):
            return {
                "structure": directory_structure,
                "directory_exists": False
            }
        
        info: Dict[str, Any] = {
            "structure": directory_structure,
            "directory_exists": True,
            "base_path": base_path
        }
        
        if directory_structure == "flat":
            # 平结构 - 统计根目录文件
            files = list(Path(base_path).glob("*.json"))
            info["file_count"] = len(files)
            info["subdirectories"] = []
        
        elif directory_structure == "by_date":
            # 日期结构
            subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            info["years"] = subdirs
            info["subdirectories"] = subdirs
        
        elif directory_structure == "by_agent":
            # Agent结构
            subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            info["agents"] = subdirs
            info["subdirectories"] = subdirs
        
        elif directory_structure == "by_hash":
            # 哈希结构
            subdirs = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
            info["hash_buckets"] = subdirs
            info["subdirectories"] = subdirs
        
        else:
            info["subdirectories"] = [d for d in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, d))]
        
        return info
    
    @staticmethod
    def calculate_file_path(
        base_path: str,
        data_id: str,
        directory_structure: str = "flat",
        extension: str = "json"
    ) -> str:
        """根据目录结构计算文件路径
        
        支持多种目录组织方式：
        - flat: 所有文件放在根目录
        - by_type: 按类型分目录
        - by_date: 按日期分目录 (YYYY/MM/DD)
        - by_agent: 按agent_id分目录
        - by_hash: 按ID哈希分目录 (first 2 chars)
        
        Args:
            base_path: 基础路径
            data_id: 数据ID
            directory_structure: 目录组织方式
            extension: 文件扩展名
            
        Returns:
            计算后的文件路径
        """
        import time
        from datetime import datetime
        
        base = Path(base_path)
        filename = f"{data_id}.{extension}" if extension else data_id
        
        if directory_structure == "flat":
            # 所有文件放在根目录
            return str(base / filename)
        
        elif directory_structure == "by_date":
            # 按日期分目录
            now = datetime.now()
            year = str(now.year)
            month = f"{now.month:02d}"
            day = f"{now.day:02d}"
            return str(base / year / month / day / filename)
        
        elif directory_structure == "by_agent":
            # 按agent_id分目录（如果data_id包含agent信息）
            # 这里假设data_id可能包含agent前缀或者需要从别处获取
            # 简单起见，使用data_id的前缀
            agent_dir = data_id.split("_")[0] if "_" in data_id else "default"
            return str(base / agent_dir / filename)
        
        elif directory_structure == "by_hash":
            # 按哈希分目录 (first 2 chars)
            hash_prefix = data_id[:2] if len(data_id) >= 2 else "00"
            return str(base / hash_prefix / filename)
        
        elif directory_structure == "by_type":
            # 按类型分目录
            type_dir = "default"
            return str(base / type_dir / filename)
        
        else:
            # 默认使用flat结构
            logger.warning(f"Unknown directory structure: {directory_structure}, using flat")
            return str(base / filename)
    