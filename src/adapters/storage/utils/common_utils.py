"""通用存储工具类

提供跨存储类型的通用工具方法，减少代码重复。

注意：序列化、压缩、过滤、过期检查和备份功能已统一迁移到 core/state 层：
- 序列化/压缩: src/core/state/base.py
- 过滤器: src/core/state/filters.py
- 过期检查: src/core/state/expiration.py
- 备份策略: src/core/state/backup_policy.py
- 统计信息: src/core/state/statistics.py
"""

import json
import time
from src.interfaces.dependency_injection import get_logger
from typing import Dict, Any, Optional
from pathlib import Path

from src.interfaces.storage.exceptions import StorageError
from src.core.state.filters import MemoryFilterBuilder, FilterValidator
from src.core.state.expiration import ExpirationManager


logger = get_logger(__name__)


class StorageCommonUtils:
    """通用存储工具类
    
    提供跨存储类型的通用静态工具方法。
    
    核心功能已迁移到 src/core/state 层，此处仅保留 adapters 特定的工具方法。
    """
    
    # 使用 core 层的过滤器和过期管理器
    _filter_builder = MemoryFilterBuilder()
    _expiration_manager = ExpirationManager()
    
    @staticmethod
    def serialize_data(data: Dict[str, Any]) -> str:
        """序列化数据为JSON字符串
        
        这是适配器层级别的 JSON 序列化方法。
        核心的压缩/序列化请使用 src/core/state/base.py 中的 StateSerializer。
        
        Args:
            data: 要序列化的数据
            
        Returns:
            序列化后的JSON字符串
        """
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))
    
    @staticmethod
    def deserialize_data(data: str) -> Dict[str, Any]:
        """从JSON字符串反序列化数据
        
        这是适配器层级别的 JSON 反序列化方法。
        核心的解压缩/反序列化请使用 src/core/state/base.py 中的 StateSerializer。
        
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
    def matches_filters(data: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查数据是否匹配过滤器
        
        委托给 src/core/state/filters.py 中的 MemoryFilterBuilder。
        
        Args:
            data: 要检查的数据
            filters: 过滤条件
            
        Returns:
            是否匹配过滤器
        """
        if not FilterValidator.validate_filters(filters):
            logger.warning(f"Invalid filters detected: {filters}")
            return False
        
        return StorageCommonUtils._filter_builder.matches(data, filters)
    
    @staticmethod
    def is_data_expired(data: Dict[str, Any], current_time: Optional[float] = None) -> bool:
        """检查数据是否过期
        
        委托给 src/core/state/expiration.py 中的 ExpirationManager。
        
        Args:
            data: 数据字典
            current_time: 当前时间戳（可选）
            
        Returns:
            是否过期
        """
        return StorageCommonUtils._expiration_manager.is_expired(data, current_time)
    
    @staticmethod
    def calculate_cutoff_time(retention_days: int, current_time: Optional[float] = None) -> float:
        """计算保留期限的截止时间
        
        委托给 src/core/state/expiration.py 中的 ExpirationManager。
        
        Args:
            retention_days: 保留天数
            current_time: 当前时间戳（可选）
            
        Returns:
            截止时间戳
        """
        return ExpirationManager.calculate_cutoff_time(retention_days, current_time)
    
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
    
    # 备份清理功能已移至 src/core/state/backup_policy.py
    # 使用 BackupManager 代替 cleanup_old_backups()
    
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
    
    # 健康检查响应准备已移至 src/core/state/statistics.py
    # 使用 HealthCheckHelper.prepare_health_check_response() 代替