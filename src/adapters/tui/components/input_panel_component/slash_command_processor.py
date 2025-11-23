"""斜杠命令处理器

负责处理 '/' 触发的系统命令执行和管理
"""

from typing import List, Tuple, Optional, Dict, Any, Callable
from .base_command_processor import BaseCommandProcessor
from ...logger import get_tui_silent_logger


class SlashCommandProcessor(BaseCommandProcessor):
    """斜杠命令处理器"""
    
    def __init__(self):
        """初始化斜杠命令处理器"""
        super().__init__("/")
        self.commands: Dict[str, Callable] = {}
        self.command_aliases: Dict[str, str] = {}
        self.command_help: Dict[str, str] = {}
        
        # 注册内置命令
        self._register_rest_commands()
        
        # 更新调试日志记录器
        self.tui_logger = get_tui_silent_logger("slash_command_processor")
    
    def _register_rest_commands(self) -> None:
        """注册内置命令"""
        self.register_command("help", self._cmd_help, "显示帮助信息", ["h", "?"])
        self.register_command("clear", self._cmd_clear, "清空屏幕", ["cls"])
        self.register_command("exit", self._cmd_exit, "退出程序", ["quit", "q"])
        self.register_command("history", self._cmd_history, "显示历史记录", ["hist"])
        self.register_command("save", self._cmd_save, "保存会话")
        self.register_command("load", self._cmd_load, "加载会话")
        self.register_command("new", self._cmd_new, "创建新会话")
        self.register_command("pause", self._cmd_pause, "暂停工作流")
        self.register_command("resume", self._cmd_resume, "恢复工作流")
        self.register_command("stop", self._cmd_stop, "停止工作流")
        self.register_command("studio", self._cmd_studio, "打开Studio", ["sg"])
        self.register_command("sessions", self._cmd_sessions, "打开会话管理", ["sess"])
        self.register_command("agents", self._cmd_agents, "打开Agent选择", ["ag"])
    
    def is_command(self, input_text: str) -> bool:
        """检查输入是否是斜杠命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            bool: 是否是斜杠命令
        """
        result = input_text.startswith('/')
        self.tui_logger.debug_input_handling("is_command", f"Checking if '{input_text}' is a slash command: {result}")
        return result
    
    def parse_command(self, input_text: str) -> Tuple[str, List[str]]:
        """解析斜杠命令
        
        Args:
            input_text: 输入文本
            
        Returns:
            Tuple[str, List[str]]: 命令名称和参数列表
        """
        self.tui_logger.debug_input_handling("parse_command", f"Parsing slash command: {input_text}")
        command_text = self._remove_trigger_char(input_text)
        command_name, args = self._split_command_and_args(command_text)
        
        # 检查别名
        if command_name in self.command_aliases:
            original_name = command_name
            command_name = self.command_aliases[command_name]
            self.tui_logger.debug_input_handling("parse_command", f"Resolved alias '{original_name}' to '{command_name}'")
        
        result = command_name, args
        self.tui_logger.debug_input_handling("parse_command", f"Parsed command result: {result}")
        return result
    
    def execute_command(self, input_text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """执行斜杠命令
        
        Args:
            input_text: 输入文本
            context: 执行上下文
            
        Returns:
            Optional[str]: 执行结果或错误信息
        """
        self.tui_logger.debug_input_handling("execute_command", f"Executing slash command: {input_text}")
        
        command_name, args = self.parse_command(input_text)
        
        if not command_name:
            result = "无效的命令格式"
            self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
            return result
        
        if command_name not in self.commands:
            result = f"未知命令: {command_name}"
            self.tui_logger.debug_input_handling("execute_command", f"Command result: {result}")
            return result
        
        try:
            handler = self.commands[command_name]
            self.tui_logger.debug_input_handling("execute_command", f"Executing handler for command: {command_name}")
            if context:
                result = handler(args, context)
            else:
                result = handler(args)
            self.tui_logger.debug_input_handling("execute_command", f"Command execution result: {result}")
            return result
        except Exception as e:
            result = f"命令执行错误: {str(e)}"
            self.tui_logger.debug_input_handling("execute_command", f"Command execution error: {result}")
            return result
    
    def get_suggestions(self, partial_input: str) -> List[str]:
        """获取命令补全建议
        
        Args:
            partial_input: 部分输入
            
        Returns:
            List[str]: 补全建议列表
        """
        self.tui_logger.debug_input_handling("get_suggestions", f"Getting slash command suggestions for: {partial_input}")
        
        if not self.is_command(partial_input):
            self.tui_logger.debug_input_handling("get_suggestions", "Not a slash command, returning empty list")
            return []
        
        command_text = self._remove_trigger_char(partial_input)
        
        # 如果没有输入，返回所有命令
        if not command_text:
            suggestions = [f"/{cmd}" for cmd in self.commands.keys()]
            self.tui_logger.debug_input_handling("get_suggestions", f"Returning all commands: {len(suggestions)} items")
            return suggestions
        
        # 查找匹配的命令
        matches = [cmd for cmd in self.commands.keys()
                  if cmd.startswith(command_text)]
        suggestions = [f"/{cmd}" for cmd in matches]
        
        self.tui_logger.debug_input_handling("get_suggestions", f"Returning filtered suggestions: {len(suggestions)} items for prefix '{command_text}'")
        return suggestions
    
    def register_command(
        self,
        name: str,
        handler: Callable,
        help_text: str = "",
        aliases: Optional[List[str]] = None
    ) -> None:
        """注册命令
        
        Args:
            name: 命令名称
            handler: 处理函数
            help_text: 帮助文本
            aliases: 别名列表
        """
        self.commands[name] = handler
        self.command_help[name] = help_text
        
        if aliases:
            for alias in aliases:
                self.command_aliases[alias] = name
    
    def unregister_command(self, name: str) -> None:
        """注销命令
        
        Args:
            name: 命令名称
        """
        if name in self.commands:
            del self.commands[name]
        
        if name in self.command_help:
            del self.command_help[name]
        
        # 删除相关别名
        aliases_to_remove = [alias for alias, cmd in self.command_aliases.items() if cmd == name]
        for alias in aliases_to_remove:
            del self.command_aliases[alias]
    
    def get_command_help(self, command_name: Optional[str] = None) -> str:
        """获取命令帮助
        
        Args:
            command_name: 命令名称，None表示显示所有命令
            
        Returns:
            str: 帮助文本
        """
        if command_name:
            if command_name in self.command_help:
                return f"/{command_name}: {self.command_help[command_name]}"
            else:
                return f"未知命令: {command_name}"
        
        # 显示所有命令
        help_text = "可用命令:\n"
        for name, help_str in self.command_help.items():
            aliases = [k for k, v in self.command_aliases.items() if v == name]
            alias_text = f" (别名: {', '.join(aliases)})" if aliases else ""
            help_text += f"  /{name}{alias_text} - {help_str}\n"
        
        return help_text
    
    # 内置命令处理函数
    def _cmd_help(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """帮助命令"""
        if args:
            return self.get_command_help(args[0])
        return self.get_command_help()
    
    def _cmd_clear(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """清屏命令"""
        return "CLEAR_SCREEN"
    
    def _cmd_exit(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """退出命令"""
        return "EXIT"
    
    def _cmd_history(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """历史记录命令"""
        if context and 'input_history' in context:
            history = context['input_history'].get_recent_history(10)
            if history:
                result = "最近输入历史:\n"
                for i, entry in enumerate(history, 1):
                    result += f"  {i}. {entry}\n"
                return result
        return "无历史记录"
    
    def _cmd_save(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """保存命令"""
        return "SAVE_SESSION"
    
    def _cmd_load(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """加载命令"""
        if args:
            return f"LOAD_SESSION:{args[0]}"
        return "请指定会话ID"
    
    def _cmd_new(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """新建会话命令"""
        return "NEW_SESSION"
    
    def _cmd_pause(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """暂停命令"""
        return "PAUSE_WORKFLOW"
    
    def _cmd_resume(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """恢复命令"""
        return "RESUME_WORKFLOW"
    
    def _cmd_stop(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """停止命令"""
        return "STOP_WORKFLOW"
    
    def _cmd_studio(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Studio命令"""
        return "OPEN_STUDIO"
    
    def _cmd_sessions(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """会话管理命令"""
        return "OPEN_SESSIONS"
    
    def _cmd_agents(self, args: List[str], context: Optional[Dict[str, Any]] = None) -> str:
        """Agent选择命令"""
        return "OPEN_AGENTS"