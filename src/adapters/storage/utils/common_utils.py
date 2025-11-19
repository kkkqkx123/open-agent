"""通用存储工具类

提供跨存储类型的通用工具方法，减少代码重复。
"""

import gzip
import json
import time
import logging
from typing import Dict, Any, Optional, List, Union
from pathlib import Path

from src.core.state.exceptions import StorageError


logger = logging.getLogger(__name__)


class StorageCommonUtils:
    """通用存储工具类
    
    提供跨存储类型的通用静态工具方法。
    """
    
    @staticmethod
    def compress_data(data: Dict[str, Any]) -> bytes:
        """压缩数据
        
        Args:
            data: 要压缩的数据
            
        Returns:
            压缩后的数据
            
        Raises:
            StorageError: 压缩失败时抛出
        """
        try:
            # 序列化为JSON
            json_str = json.dumps(data, default=str)
            # 压缩
            return gzip.compress(json_str.encode('utf-8'))
        except Exception as e:
            raise StorageError(f"Failed to compress data: {e}")
    
    @staticmethod
    def decompress_data(compressed_data: bytes) -> Dict[str, Any]:
        """解压缩数据
        
        Args:
            compressed_data: 压缩的数据
            
        Returns:
            解压缩后的数据
            
        Raises:
            StorageError: 解压缩失败时抛出
        """
        try:
            # 解压缩
            json_str = gzip.decompress(compressed_data).decode('utf-8')
            # 反序列化
            result = json.loads(json_str)
            # 确保返回的是 Dict[str, Any] 类型
            if isinstance(result, dict):
                return result
            else:
                raise StorageError(f"Decompressed data is not a dict: {type(result)}")
        except Exception as e:
            raise StorageError(f"Failed to decompress data: {e}")
    
    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> str:
        """序列化数据为JSON字符串
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    @staticmethod
    def deserialize_data(data: str) -> Dict[str, Any]:
        """从JSON字符串反序列化数据
        
        Args:
            data: 要反序列化的JSON字符串
            
        Returns:
            反序列化后的数据
            
        Raises:
            StorageError: 反序列化失败或数据类型不正确时抛出
        """
        try:
            result = json.loads(data)
            if isinstance(result, dict):
                return result
            raise StorageError(f"Expected dict, got {type(result)}")
        except Exception as e:
            raise StorageError(f"Failed to deserialize data: {e}")
    
    @staticmethod
    def should_compress_data(data: Dict[str, Any], threshold: int = 1024) -> bool:
        """判断是否应该压缩数据
        
        Args:
            data: 要检查的数据
            threshold: 压缩阈值（字节）
            
        Returns:
            是否应该压缩
        """
        return len(json.dumps(data, default=str)) > threshold
    
    @staticmethod
    def matches_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配过滤器
        """
        if not filters:
            return True
        
        for key, value in filters.items():
            if key not in data:
                return False
            
            if isinstance(value, dict):
                # 支持操作符
                if "$eq" in value and data[key] != value["$eq"]:
                    return False
                elif "$ne" in value and data[key] == value["$ne"]:
                    return False
                elif "$in" in value and data[key] not in value["$in"]:
                    return False
                elif "$nin" in value and data[key] in value["$nin"]:
                    return False
                elif "$gt" in value and data[key] <= value["$gt"]:
                    return False
                elif "$gte" in value and data[key] < value["$gte"]:
                    return False
                elif "$lt" in value and data[key] >= value["$lt"]:
                    return False
                elif "$lte" in value and data[key] > value["$lte"]:
                    return False
            elif data[key] != value:
                return False
        
        return True
    
    @staticmethod
    def is_data_expired(data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否过期
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否过期
        """
        if current_time is None:
            current_time = time.time()
        
        expires_at = data.get("expires_at")
        if expires_at and isinstance(expires_at, (int, float)) and expires_at < current_time:
            return True
        
        return False
    
    @staticmethod
    def calculate_cutoff_time(retention_days: int, current_time: Optional[float] = None) -> float:
        """计算保留期限的截止时间
        
        Args:
            retention_days: 保留天数
            current_time: 当前时间戳（可选）
            
        Returns:
            截止时间戳
        """
        if current_time is None:
            current_time = time.time()
        
        return current_time - (retention_days * 24 * 3600)
    
    @staticmethod
    def ensure_directory_exists(dir_path: str) -> None:
        """确保目录存在
        
        Args:
            dir_path: 目录路径
        """
        Path(dir_path).mkdir(parents=True, exist_ok=True)
    
    @staticmethod
    def generate_timestamp_filename(prefix: str = "backup", extension: str = "") -> str:
        """生成带时间戳的文件名
        
        Args:
            prefix: 文件名前缀
            extension: 文件扩展名（可选）
            
        Returns:
            带时间戳的文件名
        """
        import time
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        if extension:
            return f"{prefix}_{timestamp}.{extension}"
        else:
            return f"{prefix}_{timestamp}"
    
    @staticmethod
    def cleanup_old_backups(backup_dir: str, max_files: int, pattern: str = "*") -> int:
        """清理旧备份文件
        
        Args:
            backup_dir: 备份目录
            max_files: 最大文件数量
            pattern: 文件匹配模式
            
        Returns:
            删除的文件数量
        """
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return 0
            
            # 获取所有备份文件
            backup_files = list(backup_path.glob(pattern))
            
            # 按修改时间排序
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 删除超出限制的文件
            deleted_count = 0
            if len(backup_files) > max_files:
                for backup_file in backup_files[max_files:]:
                    try:
                        if backup_file.is_file():
                            backup_file.unlink()
                        else:
                            import shutil
                            shutil.rmtree(backup_file)
                        deleted_count += 1
                        logger.debug(f"Deleted old backup: {backup_file}")
                    except Exception as e:
                        logger.error(f"Failed to delete backup {backup_file}: {e}")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0
    
    @staticmethod
    def validate_data_id(data: Dict[str, Any]) -> str:
        """验证并生成数据ID
        
        Args:
            data: 数据字典
            
        Returns:
            数据ID
        """
        if "id" not in data:
            import uuid
            data["id"] = str(uuid.uuid4())
        return data["id"]
    
    @staticmethod
    def add_metadata_timestamps(data: Dict[str, Any], enable_ttl: bool = False, 
                              default_ttl_seconds: int = 3600, current_time: Optional[float] = None) -> None:
        """添加元数据时间戳
        
        Args:
            data: 数据字典
            enable_ttl: 是否启用TTL
            default_ttl_seconds: 默认TTL秒数
            current_time: 当前时间戳（可选）
        """
        if current_time is None:
            current_time = time.time()
        
        data["created_at"] = data.get("created_at", current_time)
        data["updated_at"] = current_time
        
        if enable_ttl and "expires_at" not in data:
            data["expires_at"] = current_time + default_ttl_seconds
    
    @staticmethod
    def prepare_health_check_response(status: str, config: Dict[str, Any], 
                                    stats: Dict[str, Any], **additional_info) -> Dict[str, Any]:
        """准备健康检查响应
        
        Args:
            status: 状态
            config: 配置信息
            stats: 统计信息
            **additional_info: 额外信息
            
        Returns:
            健康检查响应字典
        """
        response = {
            "status": status,
            "total_operations": stats.get("total_operations", 0),
            "config": config
        }
        
        # 添加统计信息
        for key, value in stats.items():
            if key.startswith(("total_", "expired_", "compression_", "backup_", "memory_", "database_")):
                response[key] = value
        
        # 添加额外信息
        response.update(additional_info)
        
        return response