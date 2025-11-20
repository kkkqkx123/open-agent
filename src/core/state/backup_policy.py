"""备份策略管理

提供统一的备份和恢复策略接口。
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path


class BackupStrategy(ABC):
    """备份策略基类
    
    定义备份和恢复的接口。
    """
    
    @abstractmethod
    def backup(self, source: str, destination: str) -> bool:
        """执行备份操作
        
        Args:
            source: 源路径
            destination: 目标备份路径
            
        Returns:
            是否备份成功
        """
        pass
    
    @abstractmethod
    def restore(self, source: str, destination: str) -> bool:
        """执行恢复操作
        
        Args:
            source: 备份源路径
            destination: 恢复目标路径
            
        Returns:
            是否恢复成功
        """
        pass
    
    @abstractmethod
    def cleanup_old_backups(self, backup_dir: str, max_backups: int) -> int:
        """清理旧备份
        
        Args:
            backup_dir: 备份目录
            max_backups: 最多保留的备份数
            
        Returns:
            删除的备份数
        """
        pass


class FileBackupStrategy(BackupStrategy):
    """文件系统备份策略
    
    实现文件和目录的备份。
    """
    
    def backup(self, source: str, destination: str) -> bool:
        """执行文件备份
        
        Args:
            source: 源文件或目录
            destination: 目标备份路径
            
        Returns:
            是否备份成功
        """
        try:
            import shutil
            
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return False
            
            # 确保目标目录存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                shutil.copy2(source, destination)
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            
            return True
        except Exception:
            return False
    
    def restore(self, source: str, destination: str) -> bool:
        """执行文件恢复
        
        Args:
            source: 备份源路径
            destination: 恢复目标路径
            
        Returns:
            是否恢复成功
        """
        try:
            import shutil
            
            source_path = Path(source)
            dest_path = Path(destination)
            
            if not source_path.exists():
                return False
            
            # 确保目标目录存在
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            
            if source_path.is_file():
                shutil.copy2(source, destination)
            else:
                shutil.copytree(source, destination, dirs_exist_ok=True)
            
            return True
        except Exception:
            return False
    
    def cleanup_old_backups(self, backup_dir: str, max_backups: int) -> int:
        """清理旧备份文件
        
        按修改时间排序，保留最新的 max_backups 个备份。
        
        Args:
            backup_dir: 备份目录
            max_backups: 最多保留的备份数
            
        Returns:
            删除的备份数
        """
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return 0
            
            # 获取所有备份文件
            backup_files = list(backup_path.glob("*"))
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 删除超出限制的备份
            deleted_count = 0
            if len(backup_files) > max_backups:
                for backup_file in backup_files[max_backups:]:
                    try:
                        if backup_file.is_file():
                            backup_file.unlink()
                        else:
                            import shutil
                            shutil.rmtree(backup_file)
                        deleted_count += 1
                    except Exception:
                        pass
            
            return deleted_count
        except Exception:
            return 0


class DatabaseBackupStrategy(BackupStrategy):
    """数据库备份策略
    
    实现数据库的备份。
    """
    
    def backup(self, source: str, destination: str) -> bool:
        """执行数据库备份
        
        Args:
            source: 源数据库路径
            destination: 目标备份路径
            
        Returns:
            是否备份成功
        """
        try:
            import sqlite3
            from pathlib import Path
            
            if not Path(source).exists():
                return False
            
            # 确保目标目录存在
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建源连接和备份连接
            source_conn = sqlite3.connect(source)
            backup_conn = sqlite3.connect(destination)
            
            # 执行备份
            source_conn.backup(backup_conn)
            
            # 关闭连接
            source_conn.close()
            backup_conn.close()
            
            return True
        except Exception:
            return False
    
    def restore(self, source: str, destination: str) -> bool:
        """执行数据库恢复
        
        Args:
            source: 备份源路径
            destination: 恢复目标路径
            
        Returns:
            是否恢复成功
        """
        try:
            import sqlite3
            from pathlib import Path
            
            if not Path(source).exists():
                return False
            
            # 确保目标目录存在
            Path(destination).parent.mkdir(parents=True, exist_ok=True)
            
            # 创建备份连接和目标连接
            backup_conn = sqlite3.connect(source)
            target_conn = sqlite3.connect(destination)
            
            # 执行恢复
            backup_conn.backup(target_conn)
            
            # 关闭连接
            backup_conn.close()
            target_conn.close()
            
            return True
        except Exception:
            return False
    
    def cleanup_old_backups(self, backup_dir: str, max_backups: int) -> int:
        """清理旧备份文件
        
        按修改时间排序，保留最新的 max_backups 个备份。
        
        Args:
            backup_dir: 备份目录
            max_backups: 最多保留的备份数
            
        Returns:
            删除的备份数
        """
        try:
            backup_path = Path(backup_dir)
            if not backup_path.exists():
                return 0
            
            # 获取所有备份文件（*.db, *.sqlite 等）
            backup_files = list(backup_path.glob("*.db")) + list(backup_path.glob("*.sqlite"))
            
            # 按修改时间排序（最新的在前）
            backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
            
            # 删除超出限制的备份
            deleted_count = 0
            if len(backup_files) > max_backups:
                for backup_file in backup_files[max_backups:]:
                    try:
                        backup_file.unlink()
                        deleted_count += 1
                    except Exception:
                        pass
            
            return deleted_count
        except Exception:
            return 0


class BackupManager:
    """备份管理器
    
    统一管理不同类型的备份。
    """
    
    def __init__(self, strategy: Optional[BackupStrategy] = None):
        """初始化管理器
        
        Args:
            strategy: 备份策略（可选，默认使用文件备份）
        """
        self.strategy = strategy or FileBackupStrategy()
    
    def backup(self, source: str, destination: str) -> bool:
        """执行备份
        
        Args:
            source: 源路径
            destination: 目标备份路径
            
        Returns:
            是否备份成功
        """
        return self.strategy.backup(source, destination)
    
    def restore(self, source: str, destination: str) -> bool:
        """执行恢复
        
        Args:
            source: 备份源路径
            destination: 恢复目标路径
            
        Returns:
            是否恢复成功
        """
        return self.strategy.restore(source, destination)
    
    def cleanup_old_backups(self, backup_dir: str, max_backups: int) -> int:
        """清理旧备份
        
        Args:
            backup_dir: 备份目录
            max_backups: 最多保留的备份数
            
        Returns:
            删除的备份数
        """
        return self.strategy.cleanup_old_backups(backup_dir, max_backups)
    
    def set_strategy(self, strategy: BackupStrategy) -> None:
        """设置备份策略
        
        Args:
            strategy: 新的备份策略
        """
        self.strategy = strategy
