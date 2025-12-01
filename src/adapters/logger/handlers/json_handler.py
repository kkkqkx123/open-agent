"""JSON格式日志处理器"""

import json
import os
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from .base_handler import BaseHandler
from ...core.logger.log_level import LogLevel


class JsonHandler(BaseHandler):
    """JSON格式日志处理器"""

    def __init__(
        self, level: LogLevel = LogLevel.INFO, config: Optional[Dict[str, Any]] = None
    ):
        """初始化JSON处理器

        Args:
            level: 日志级别
            config: 配置
        """
        super().__init__(level, config)
        
        # 从配置获取文件路径，如果没有则使用默认路径
        self.filename = config.get("filename", "app.json") if config else "app.json"
        self.mode = config.get("mode", "a") if config else "a"
        self.encoding = config.get("encoding", "utf-8") if config else "utf-8"
        self.ensure_ascii = config.get("ensure_ascii", False) if config else False
        
        # 确保目录存在
        directory = os.path.dirname(self.filename)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        # 打开文件
        self.stream = open(self.filename, self.mode, encoding=self.encoding)
        self._lock = threading.Lock()

    def emit(self, record: Dict[str, Any]) -> None:
        """输出JSON格式日志记录

        Args:
            record: 日志记录
        """
        # 转换日志记录为JSON可序列化的格式
        json_record = self._prepare_json_record(record)
        
        json_str = json.dumps(json_record, ensure_ascii=self.ensure_ascii, default=str)
        
        with self._lock:
            try:
                if self.stream is not None:
                    self.stream.write(json_str + "\n")
                    self.stream.flush()
            except Exception:
                self.handleError(record)

    def _prepare_json_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """准备JSON格式的日志记录

        Args:
            record: 原始日志记录

        Returns:
            JSON可序列化的日志记录
        """
        json_record = {}
        for key, value in record.items():
            if isinstance(value, datetime):
                json_record[key] = value.isoformat()
            elif isinstance(value, LogLevel):
                json_record[key] = value.name
            elif isinstance(value, dict):
                # 递归处理嵌套字典
                json_record[key] = self._prepare_json_record(value)
            elif isinstance(value, list):
                # 处理列表，对列表中的每个元素进行处理
                json_record[key] = [self._prepare_json_value(item) for item in value]
            else:
                json_record[key] = value
        return json_record

    def _prepare_json_value(self, value: Any) -> Any:
        """准备JSON格式的单个值

        Args:
            value: 原始值

        Returns:
            JSON可序列化的值
        """
        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, LogLevel):
            return value.name
        elif isinstance(value, dict):
            return self._prepare_json_record(value)
        elif isinstance(value, list):
            return [self._prepare_json_value(item) for item in value]
        else:
            return value

    def flush(self) -> None:
        """刷新文件流"""
        with self._lock:
            if self.stream is not None and hasattr(self.stream, "flush"):
                self.stream.flush()

    def close(self) -> None:
        """关闭文件"""
        if self.stream and not self.stream.closed:
            self.flush()
            self.stream.close()
            self.stream = None

    def __del__(self):
        """析构函数"""
        self.close()