"""文件日志处理器"""

import os
import threading
from typing import Any, Dict, Optional

from ....interfaces.logger import LogLevel
from ..formatters.text_formatter import TextFormatter
from .base_handler import BaseHandler


class FileHandler(BaseHandler):
    """文件处理器"""

    def __init__(
        self,
        filename: str,
        level: LogLevel = LogLevel.INFO,
        formatter: Optional[TextFormatter] = None,
        encoding: str = "utf-8",
        mode: str = "a",
        max_bytes: Optional[int] = None,
        backup_count: int = 0,
    ):
        """初始化文件处理器

        Args:
            filename: 日志文件名
            level: 日志级别
            formatter: 格式化器
            encoding: 文件编码
            mode: 文件打开模式
            max_bytes: 最大文件字节数，用于日志轮转
            backup_count: 备份文件数量
        """
        super().__init__(level, formatter or TextFormatter())
        
        self.filename = filename
        self.encoding = encoding
        self.mode = mode
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        
        # 确保目录存在
        self._ensure_directory_exists()
        
        # 文件句柄
        self._file = None
        self._should_close_file = True

    def _ensure_directory_exists(self) -> None:
        """确保日志文件目录存在"""
        directory = os.path.dirname(self.filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _open_file(self) -> None:
        """打开日志文件"""
        if self._file is None:
            try:
                self._file = open(self.filename, self.mode, encoding=self.encoding)
            except Exception as e:
                # 无法打开文件时的fallback
                print(f"无法打开日志文件 {self.filename}: {e}")

    def _close_file(self) -> None:
        """关闭日志文件"""
        if self._file and self._should_close_file:
            try:
                self._file.close()
            except Exception:
                pass
            finally:
                self._file = None

    def _should_rotate(self) -> bool:
        """检查是否需要轮转日志文件

        Returns:
            是否需要轮转
        """
        if self.max_bytes is None:
            return False
        
        try:
            return os.path.getsize(self.filename) >= self.max_bytes
        except OSError:
            return False

    def _rotate_file(self) -> None:
        """轮转日志文件"""
        if not self._should_rotate():
            return
        
        # 关闭当前文件
        self._close_file()
        
        try:
            # 轮转文件
            if self.backup_count > 0:
                # 删除最老的备份文件
                oldest_backup = f"{self.filename}.{self.backup_count}"
                if os.path.exists(oldest_backup):
                    os.remove(oldest_backup)
                
                # 重命名现有备份文件
                for i in range(self.backup_count - 1, 0, -1):
                    old_backup = f"{self.filename}.{i}"
                    new_backup = f"{self.filename}.{i + 1}"
                    if os.path.exists(old_backup):
                        os.rename(old_backup, new_backup)
                
                # 重命名当前文件为第一个备份
                if os.path.exists(self.filename):
                    os.rename(self.filename, f"{self.filename}.1")
            else:
                # 没有备份，直接清空文件
                if os.path.exists(self.filename):
                    open(self.filename, 'w').close()
        except Exception as e:
            print(f"日志文件轮转失败: {e}")

    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录，写入文件

        Args:
            record: 日志记录字典
        """
        if not self.should_handle(record):
            return

        try:
            # 检查是否需要轮转
            if self._should_rotate():
                self._rotate_file()
            
            # 确保文件已打开
            if self._file is None:
                self._open_file()
            
            if self._file:
                formatted_message = self.format_record(record)
                self._write_to_file(formatted_message)
        except Exception as e:
            # 处理失败时的fallback
            error_message = f"FileHandler error: {e}. Original record: {record}"
            print(error_message)

    def _write_to_file(self, message: str) -> None:
        """写入消息到文件

        Args:
            message: 要写入的消息
        """
        with self._lock:
            try:
                if self._file:
                    self._file.write(message + '\n')
                    self._file.flush()
            except Exception as e:
                print(f"写入日志文件失败: {e}")
                # 尝试重新打开文件
                self._close_file()
                self._open_file()

    def flush(self) -> None:
        """刷新缓冲区"""
        with self._lock:
            try:
                if self._file:
                    self._file.flush()
            except Exception:
                pass

    def close(self) -> None:
        """关闭处理器"""
        self._close_file()

    def get_file_size(self) -> int:
        """获取当前文件大小

        Returns:
            文件大小（字节）
        """
        try:
            return os.path.getsize(self.filename)
        except OSError:
            return 0

    def file_exists(self) -> bool:
        """检查日志文件是否存在

        Returns:
            文件是否存在
        """
        return os.path.exists(self.filename)