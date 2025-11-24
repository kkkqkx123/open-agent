"""备份管理工具

提供通用的文件备份功能，可被多个模块使用。
"""

import os
import shutil
import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class BackupManager:
    """备份管理器"""

    def __init__(self, backup_dir: str = "backups", max_backups: int = 10):
        """初始化备份管理器

        Args:
            backup_dir: 备份目录
            max_backups: 最大备份数量
        """
        self.backup_dir = Path(backup_dir)
        self.max_backups = max_backups
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def create_backup(self, file_path: str) -> str:
        """创建文件备份

        Args:
            file_path: 文件路径

        Returns:
            备份文件路径

        Raises:
            RuntimeError: 备份失败
        """
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                raise RuntimeError(f"文件不存在: {file_path}")

            # 生成备份文件名（包含微秒以避免冲突）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            backup_name = f"{source_path.stem}_{timestamp}{source_path.suffix}"
            backup_path = self.backup_dir / backup_name

            # 复制文件
            shutil.copy2(source_path, backup_path)

            # 清理旧备份
            self._cleanup_old_backups(source_path.stem)

            return str(backup_path)

        except Exception as e:
            raise RuntimeError(f"创建备份失败: {e}")

    def restore_backup(
        self, file_path: str, backup_timestamp: Optional[str] = None
    ) -> bool:
        """恢复文件备份

        Args:
            file_path: 文件路径
            backup_timestamp: 备份时间戳，如果为None则恢复最新备份

        Returns:
            是否成功恢复
        """
        try:
            source_path = Path(file_path)
            backup_name_pattern = f"{source_path.stem}_*{source_path.suffix}"

            # 查找备份文件
            if backup_timestamp:
                backup_name = (
                    f"{source_path.stem}_{backup_timestamp}{source_path.suffix}"
                )
                backup_path = self.backup_dir / backup_name
            else:
                # 查找最新备份
                backups = list(self.backup_dir.glob(backup_name_pattern))
                if not backups:
                    return False
                backup_path = max(backups, key=lambda p: p.stat().st_mtime)

            if not backup_path.exists():
                return False

            # 恢复文件
            shutil.copy2(backup_path, source_path)
            return True

        except Exception:
            return False

    def list_backups(self, file_path: str) -> List[Dict[str, Any]]:
        """列出文件的所有备份

        Args:
            file_path: 文件路径

        Returns:
            备份信息列表
        """
        source_path = Path(file_path)
        backup_name_pattern = f"{source_path.stem}_*{source_path.suffix}"

        backups = []
        for backup_path in self.backup_dir.glob(backup_name_pattern):
            stat = backup_path.stat()
            # 从文件名中提取时间戳而不是使用修改时间
            filename = backup_path.name
            # 提取时间戳部分：例如 test_20231201_123456_123456.txt -> 20231201_123456_123456
            parts = filename.split('_')
            if len(parts) >= 3:  # 确保有足够部分来提取完整时间戳
                timestamp = '_'.join(parts[1:]).replace(backup_path.suffix, '')  # 从第二部分开始连接并移除扩展名
            else:
                # 如果无法从文件名提取时间戳，使用修改时间作为后备
                timestamp = datetime.fromtimestamp(stat.st_mtime).strftime(
                    "%Y%m%d_%H%M%S"
                )
            
            backups.append(
                {
                    "path": str(backup_path),
                    "timestamp": timestamp,
                    "size": stat.st_size,
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                }
            )

        # 按时间戳排序（最新的在前）
        backups.sort(key=lambda b: str(b["timestamp"]), reverse=True)
        return backups

    def delete_backup(self, file_path: str, backup_timestamp: str) -> bool:
        """删除指定备份

        Args:
            file_path: 文件路径
            backup_timestamp: 备份时间戳

        Returns:
            是否成功删除
        """
        try:
            source_path = Path(file_path)
            backup_name = f"{source_path.stem}_{backup_timestamp}{source_path.suffix}"
            backup_path = self.backup_dir / backup_name

            if backup_path.exists():
                backup_path.unlink()
                return True
            return False
        except Exception:
            return False

    def delete_all_backups(self, file_path: str) -> int:
        """删除文件的所有备份

        Args:
            file_path: 文件路径

        Returns:
            删除的备份数量
        """
        source_path = Path(file_path)
        backup_name_pattern = f"{source_path.stem}_*{source_path.suffix}"

        count = 0
        for backup_path in self.backup_dir.glob(backup_name_pattern):
            try:
                backup_path.unlink()
                count += 1
            except Exception:
                pass

        return count

    def _cleanup_old_backups(self, file_stem: str) -> None:
        """清理旧备份

        Args:
            file_stem: 文件名（不含扩展名）
        """
        backup_name_pattern = f"{file_stem}_*"
        backups = list(self.backup_dir.glob(backup_name_pattern))

        # 按文件名中的时间戳排序（最新的在前）
        def extract_timestamp_from_filename(backup_path):
            """从备份文件名中提取时间戳用于排序"""
            filename = backup_path.name
            parts = filename.split('_')
            if len(parts) >= 3:  # 确保有足够部分来提取完整时间戳
                # 提取时间戳部分：例如 test_20231201_123456_123456.txt -> 20231201_123456_123456
                timestamp = '_'.join(parts[1:]).replace(backup_path.suffix, '')  # 从第二部分开始连接并移除扩展名
                return timestamp
            else:
                # 如果无法从文件名提取时间戳，使用修改时间作为后备
                return str(backup_path.stat().st_mtime)
        
        backups.sort(key=extract_timestamp_from_filename, reverse=True)

        # 删除超出数量限制的备份
        for backup_path in backups[self.max_backups :]:
            try:
                backup_path.unlink()
            except Exception:
                pass  # 忽略删除错误

    def get_backup_stats(self) -> Dict[str, Any]:
        """获取备份统计信息

        Returns:
            备份统计信息
        """
        total_files = 0
        total_size = 0
        file_groups = {}

        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_file():
                total_files += 1
                stat = backup_path.stat()
                total_size += stat.st_size

                # 按原文件分组
                stem = backup_path.stem.split('_')[0]
                if stem not in file_groups:
                    file_groups[stem] = {"count": 0, "size": 0}
                file_groups[stem]["count"] += 1
                file_groups[stem]["size"] += stat.st_size

        return {
            "total_files": total_files,
            "total_size": total_size,
            "backup_dir": str(self.backup_dir),
            "file_groups": file_groups,
        }

    def cleanup_all_backups(self, older_than_days: int = 30) -> int:
        """清理所有旧备份

        Args:
            older_than_days: 保留天数，超过此天数的备份将被删除

        Returns:
            删除的备份数量
        """
        cutoff_time = time.time() - (older_than_days * 24 * 60 * 60)
        count = 0

        for backup_path in self.backup_dir.iterdir():
            if backup_path.is_file():
                try:
                    if backup_path.stat().st_mtime < cutoff_time:
                        backup_path.unlink()
                        count += 1
                except Exception:
                    pass

        return count