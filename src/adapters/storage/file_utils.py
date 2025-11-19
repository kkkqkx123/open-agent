"""文件存储工具类

提供文件存储相关的静态工具方法。
"""

import json
import os
import shutil
import threading
import time
import logging
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from src.core.state.exceptions import StorageError, StorageConnectionError


logger = logging.getLogger(__name__)


class FileStorageUtils:
    """文件存储工具类
    
    提供文件存储相关的静态工具方法。
    """
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> None:
        """确保目录存在
        
        Args:
            dir_path: 目录路径
        """
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> str:
        """序列化数据
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    @staticmethod
    def deserialize_data(data: str) -> Dict[str, Any]:
        """反序列化数据
        
        Args:
            data: 要反序列化的JSON字符串
            
        Returns:
            反序列化后的数据
        """
        return json.loads(data)
    
    @staticmethod
    def save_data_to_file(file_path: str, data: Dict[str, Any]) -> None:
        """保存数据到文件
        
        Args:
            file_path: 文件路径
            data: 要保存的数据
        """
        # 确保目录存在
        FileStorageUtils.ensure_directory_exists(os.path.dirname(file_path))
        
        # 序列化数据
        serialized_data = FileStorageUtils.serialize_data(data)
        
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
                return FileStorageUtils.deserialize_data(data)
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
    def matches_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        Args:
            data: 数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in data:
                return False
            
            if isinstance(value, dict):
                # 处理特殊操作符
                if "$gt" in value and not (data[key] > value["$gt"]):
                    return False
                elif "$lt" in value and not (data[key] < value["$lt"]):
                    return False
                elif "$gte" in value and not (data[key] >= value["$gte"]):
                    return False
                elif "$lte" in value and not (data[key] <= value["$lte"]):
                    return False
                elif "$ne" in value and data[key] == value["$ne"]:
                    return False
                elif "$like" in value and value["$like"] not in str(data[key]):
                    return False
            elif isinstance(value, (list, tuple)):
                # IN查询
                if data[key] not in value:
                    return False
            elif data[key] != value:
                return False
        
        return True
    
    @staticmethod
    def calculate_directory_size(dir_path: str) -> int:
        """计算目录大小
        
        Args:
            dir_path: 目录路径
            
        Returns:
            目录大小（字节）
        """
        if not os.path.exists(dir_path):
            return 0
        
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(dir_path):
            for filename in filenames:
                file_path = os.path.join(dirpath, filename)
                if os.path.exists(file_path):
                    total_size += os.path.getsize(file_path)
        
        return total_size
    
    @staticmethod
    def cleanup_expired_files(dir_path: str, current_time: float) -> int:
        """清理过期文件
        
        Args:
            dir_path: 目录路径
            current_time: 当前时间戳
            
        Returns:
            清理的文件数
        """
        if not os.path.exists(dir_path):
            return 0
        
        cleaned_count = 0
        
        for file_path in FileStorageUtils.list_files_in_directory(dir_path, "*.json", recursive=True):
            try:
                # 加载数据检查过期时间
                data = FileStorageUtils.load_data_from_file(file_path)
                if data and "expires_at" in data and data["expires_at"] < current_time:
                    FileStorageUtils.delete_file(file_path)
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup expired file {file_path}: {e}")
        
        return cleaned_count
    
    @staticmethod
    def cleanup_old_files(dir_path: str, cutoff_time: float) -> int:
        """清理旧文件
        
        Args:
            dir_path: 目录路径
            cutoff_time: 截止时间戳
            
        Returns:
            清理的文件数
        """
        if not os.path.exists(dir_path):
            return 0
        
        cleaned_count = 0
        
        for file_path in FileStorageUtils.list_files_in_directory(dir_path, "*.json", recursive=True):
            try:
                file_time = FileStorageUtils.get_file_modified_time(file_path)
                if file_time < cutoff_time:
                    FileStorageUtils.delete_file(file_path)
                    cleaned_count += 1
            except Exception as e:
                logger.error(f"Failed to cleanup old file {file_path}: {e}")
        
        return cleaned_count
    
    @staticmethod
    def backup_directory(source_dir: str, backup_dir: str) -> bool:
        """备份目录
        
        Args:
            source_dir: 源目录
            backup_dir: 备份目录
            
        Returns:
            是否备份成功
        """
        try:
            # 确保备份目录存在
            FileStorageUtils.ensure_directory_exists(backup_dir)
            
            # 备份目录
            if os.path.exists(source_dir):
                shutil.copytree(source_dir, backup_dir, dirs_exist_ok=True)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to backup directory {source_dir} to {backup_dir}: {e}")
            return False
    
    @staticmethod
    def restore_directory(backup_dir: str, target_dir: str) -> bool:
        """恢复目录
        
        Args:
            backup_dir: 备份目录
            target_dir: 目标目录
            
        Returns:
            是否恢复成功
        """
        try:
            # 确保目标目录存在
            FileStorageUtils.ensure_directory_exists(target_dir)
            
            # 恢复目录
            if os.path.exists(backup_dir):
                shutil.copytree(backup_dir, target_dir, dirs_exist_ok=True)
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to restore directory {backup_dir} to {target_dir}: {e}")
            return False
    
    @staticmethod
    def compress_data(data: Dict[str, Any]) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
        """
        import gzip
        
        # 序列化数据
        serialized_data = FileStorageUtils.serialize_data(data)
        
        # 压缩数据
        compressed_data = gzip.compress(serialized_data.encode('utf-8'))
        
        return compressed_data
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> Dict[str, Any]:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
        """
        import gzip
        
        # 解压缩数据
        decompressed_data = gzip.decompress(compressed_data).decode('utf-8')
        
        # 反序列化数据
        return FileStorageUtils.deserialize_data(decompressed_data)
    
    @staticmethod
    def should_compress_data(data: Dict[str, Any], threshold: int = 1024) -> bool:
        """判断是否应该压缩数据
        
        Args:
            data: 数据
            threshold: 压缩阈值（字节）
            
        Returns:
            是否应该压缩
        """
        serialized_data = FileStorageUtils.serialize_data(data)
        return len(serialized_data.encode('utf-8')) > threshold
    
    @staticmethod
    def get_storage_info(dir_path: str) -> Dict[str, Any]:
        """获取存储信息
        
        Args:
            dir_path: 目录路径
            
        Returns:
            存储信息
        """
        if not os.path.exists(dir_path):
            return {
                "directory_exists": False,
                "total_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
        
        # 统计文件数量和大小
        files = FileStorageUtils.list_files_in_directory(dir_path, "*.json", recursive=True)
        total_size = sum(FileStorageUtils.get_file_size(file_path) for file_path in files)
        
        return {
            "directory_exists": True,
            "directory_path": dir_path,
            "total_files": len(files),
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }