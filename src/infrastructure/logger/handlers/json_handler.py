"""JSON日志处理器"""

import os
import threading
from typing import Any, Dict, Optional

from ....interfaces.logger import LogLevel
from ..formatters.json_formatter import JsonFormatter
from .file_handler import FileHandler


class JsonHandler(FileHandler):
    """JSON处理器，输出JSON格式的日志"""

    def __init__(
        self,
        filename: str,
        level: LogLevel = LogLevel.INFO,
        formatter: Optional[JsonFormatter] = None,
        encoding: str = "utf-8",
        mode: str = "a",
        max_bytes: Optional[int] = None,
        backup_count: int = 0,
        ensure_ascii: bool = False,
        indent: Optional[int] = None,
        sort_keys: bool = False,
    ):
        """初始化JSON处理器

        Args:
            filename: 日志文件名
            level: 日志级别
            formatter: JSON格式化器
            encoding: 文件编码
            mode: 文件打开模式
            max_bytes: 最大文件字节数，用于日志轮转
            backup_count: 备份文件数量
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
            sort_keys: 是否排序键
        """
        # 如果没有指定格式化器，创建JSON格式化器
        if formatter is None:
            formatter = JsonFormatter(
                ensure_ascii=ensure_ascii,
                indent=indent,
                sort_keys=sort_keys,
            )
        
        super().__init__(
            filename=filename,
            level=level,
            formatter=formatter,
            encoding=encoding,
            mode=mode,
            max_bytes=max_bytes,
            backup_count=backup_count,
        )

    def handle(self, record: Dict[str, Any]) -> None:
        """处理日志记录，写入JSON格式到文件

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
                # JSON格式化器已经处理了格式化
                formatted_message = self.formatter.format(record)
                self._write_to_file(formatted_message)
        except Exception as e:
            # 处理失败时的fallback
            error_record = {
                "timestamp": record.get("timestamp", ""),
                "level": "ERROR",
                "name": "JsonHandler",
                "message": f"JSONHandler error: {e}",
                "original_record": str(record),
            }
            
            try:
                formatted_error = self.formatter.format(error_record)
                self._write_to_file(formatted_error)
            except Exception:
                # 连错误记录都无法格式化时的最后fallback
                print(f"JSONHandler完全失败: {e}. Original: {record}")

    def validate_json_output(self, sample_record: Dict[str, Any]) -> bool:
        """验证JSON输出是否有效

        Args:
            sample_record: 示例日志记录

        Returns:
            JSON输出是否有效
        """
        try:
            formatted = self.formatter.format(sample_record)
            import json
            json.loads(formatted)
            return True
        except Exception:
            return False

    def get_formatter(self) -> JsonFormatter:
        """获取JSON格式化器

        Returns:
            JSON格式化器实例
        """
        return self.formatter

    def set_json_options(
        self,
        ensure_ascii: Optional[bool] = None,
        indent: Optional[int] = None,
        sort_keys: Optional[bool] = None,
    ) -> None:
        """设置JSON格式选项

        Args:
            ensure_ascii: 是否确保ASCII编码
            indent: 缩进空格数
            sort_keys: 是否排序键
        """
        if isinstance(self.formatter, JsonFormatter):
            if ensure_ascii is not None:
                self.formatter.ensure_ascii = ensure_ascii
            if indent is not None:
                self.formatter.indent = indent
            if sort_keys is not None:
                self.formatter.sort_keys = sort_keys