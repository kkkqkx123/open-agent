"""文件选择处理器

负责处理 '@' 触发的文件选择和自动补全功能
"""

import os
from typing import List, Tuple, Optional, Dict, Any
from .base_command_processor import BaseCommandProcessor
from ...logger import get_tui_silent_logger


class FileSelectorProcessor(BaseCommandProcessor):
    """文件选择处理器"""
    
    def __init__(self):
        """初始化文件选择处理器"""
        super().__init__("@")
        self.current_directory = os.getcwd()
        self.file_cache: Dict[str, List[str]] = {}
        
        # 更新调试日志记录器
        self.tui_logger = get_tui_silent_logger("file_selector_processor")
    
    def is_command(self, input_text: str) -> bool:
        """检查输入是否是文件选择命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            bool: 是否是文件选择命令
        """
        result = input_text.startswith("@")
        self.tui_logger.debug_input_handling("is_command", f"Checking if '{input_text}' is a file command: {result}")
        return result
    
    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """解析文件选择命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            Tuple[str, List[str]]: 文件路径和参数列表
        """
        self.tui_logger.debug_input_handling("parse_command", f"Parsing command: {input_text}")
        command_text = self._remove_trigger_char(input_text)
        result = self._split_command_and_args(command_text)
        self.tui_logger.debug_input_handling("parse_command", f"Parsed command result: {result}")
        return result
    
    def execute_command(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """执行文件选择命令
        
        Args:
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            Optional[str]: 执行结果或错误信息
        """
        self.tui_logger.debug_input_handling("execute_command", f"Executing file command: {input_text}")
        
        file_path, args = self.parse_command(input_text)
        
        if not file_path:
            result = "请指定文件路径"
            self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
            return result
        
        # 处理相对路径
        if not os.path.isabs(file_path):
            full_path = os.path.join(self.current_directory, file_path)
        else:
            full_path = file_path
        
        self.tui_logger.debug_input_handling("execute_command", f"Resolved path: {full_path}")
        
        # 检查文件是否存在
        if not os.path.exists(full_path):
            result = f"文件不存在: {full_path}"
            self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
            return result
        
        # 如果是目录，列出内容
        if os.path.isdir(full_path):
            try:
                files = os.listdir(full_path)
                if files:
                    result = f"目录 {full_path} 的内容:\n"
                    for i, file in enumerate(files[:10], 1):  # 限制显示前10个
                        file_type = "📁" if os.path.isdir(os.path.join(full_path, file)) else "📄"
                        result += f"  {i}. {file_type} {file}\n"
                    if len(files) > 10:
                        result += f"  ... 还有 {len(files) - 10} 个文件\n"
                    self.tui_logger.debug_input_handling("execute_command", f"Directory listing result: {len(files)} items")
                    return result
                else:
                    result = f"目录 {full_path} 为空"
                    self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
                    return result
            except PermissionError:
                result = f"无权限访问目录: {full_path}"
                self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
                return result
        
        # 如果是文件，返回文件信息
        if os.path.isfile(full_path):
            try:
                file_size = os.path.getsize(full_path)
                file_mtime = os.path.getmtime(full_path)
                import datetime
                mtime_str = datetime.datetime.fromtimestamp(file_mtime).strftime("%Y-%m-%d %H:%M:%S")
                
                result = f"文件: {full_path}\n大小: {file_size} 字节\n修改时间: {mtime_str}"
                self.tui_logger.debug_input_handling("execute_command", f"File info result: size={file_size}, modified={mtime_str}")
                return result
            except Exception as e:
                result = f"获取文件信息失败: {str(e)}"
                self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
                return result
        
        result = f"无法处理路径: {full_path}"
        self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
        return result
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """获取文件路径补全建议
        
        Args:
            partial_input: 部分输入
            
        Returns:
            List[str]: 补全建议列表
        """
        self.tui_logger.debug_input_handling("get_suggestions", f"Getting suggestions for: {partial_input}")
        
        if not self.is_command(partial_input):
            self.tui_logger.debug_input_handling("get_suggestions", "Not a file command, returning empty list")
            return []
        
        command_text = self._remove_trigger_char(partial_input)
        
        # 如果没有输入，返回当前目录的文件
        if not command_text:
            suggestions = self._get_directory_files(self.current_directory)
            self.tui_logger.debug_input_handling("get_suggestions", f"Returning all files in current directory: {len(suggestions)} items")
            return suggestions
        
        # 解析路径
        if os.path.isabs(command_text):
            directory = os.path.dirname(command_text) or "/"
            prefix = os.path.basename(command_text)
        else:
            directory = os.path.join(self.current_directory, os.path.dirname(command_text))
            prefix = os.path.basename(command_text)
        
        # 获取目录文件
        if os.path.isdir(directory):
            files = self._get_directory_files(directory)
            # 过滤匹配前缀的文件
            suggestions = [f"@{os.path.join(os.path.dirname(command_text), file)}"
                          for file in files if file.startswith(prefix)]
            self.tui_logger.debug_input_handling("get_suggestions", f"Returning filtered suggestions: {len(suggestions)} items for prefix '{prefix}'")
            return suggestions
        
        self.tui_logger.debug_input_handling("get_suggestions", "Directory not found, returning empty list")
        return []
    
    def _get_directory_files(self, directory: str) -> List[str]:
        """获取目录文件列表
        
        Args:
            directory: 目录路径
            
        Returns:
            List[str]: 文件列表
        """
        # 使用缓存提高性能
        if directory in self.file_cache:
            return self.file_cache[directory]
        
        try:
            files = []
            for item in os.listdir(directory):
                if item.startswith('.'):  # 跳过隐藏文件
                    continue
                
                full_path = os.path.join(directory, item)
                if os.path.isdir(full_path):
                    files.append(item + "/")  # 目录添加斜杠标识
                else:
                    files.append(item)
            
            # 排序并缓存
            files.sort()
            self.file_cache[directory] = files
            return files
        except (PermissionError, OSError):
            return []
    
    def set_current_directory(self, directory: str) -> None:
        """设置当前工作目录
        
        Args:
            directory: 目录路径
        """
        if os.path.isdir(directory):
            self.current_directory = directory
            # 清除缓存
            self.file_cache.clear()
    
    def get_command_help(self, command_name: Optional[str] = None) -> str:
        """获取文件选择命令帮助
        
        Args:
            command_name: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助文本
        """
        if command_name:
            return f"@{command_name}: 文件选择命令"
        
        return """文件选择命令 (使用 @ 触发):
  @path/to/file      - 选择文件
  @path/to/directory - 浏览目录
  @                  - 显示当前目录文件
  
支持相对路径和绝对路径，使用 Tab 键自动补全"""