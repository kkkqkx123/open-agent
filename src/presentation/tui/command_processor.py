"""TUI命令处理器"""

from typing import List, Dict, Any, Callable, Optional


class CommandProcessor:
    """命令处理器，负责解析和执行命令"""
    
    def __init__(self, app: Any) -> None:
        """初始化命令处理器
        
        Args:
            app: TUI应用程序实例
        """
        self.app = app
        self.commands: Dict[str, Callable[[], None]] = {}
        self.commands_with_args: Dict[str, Callable[[List[str]], None]] = {}
        
        # 注册默认命令
        self._register_default_commands()
    
    def _register_default_commands(self) -> None:
        """注册默认命令"""
        # 无参数命令
        self.commands["help"] = self._handle_help
        self.commands["clear"] = self._handle_clear
        self.commands["exit"] = self._handle_exit
        self.commands["save"] = self._handle_save
        self.commands["new"] = self._handle_new
        self.commands["pause"] = self._handle_pause
        self.commands["resume"] = self._handle_resume
        self.commands["stop"] = self._handle_stop
        self.commands["studio"] = self._handle_studio
        self.commands["performance"] = self._handle_performance
        self.commands["debug"] = self._handle_debug
        
        # 带参数命令
        self.commands_with_args["load"] = self._handle_load
    
    def register_command(self, command: str, handler: Callable[[], None]) -> None:
        """注册无参数命令
        
        Args:
            command: 命令名称
            handler: 处理函数
        """
        self.commands[command] = handler
    
    def register_command_with_args(self, command: str, handler: Callable[[List[str]], None]) -> None:
        """注册带参数命令
        
        Args:
            command: 命令名称
            handler: 处理函数
        """
        self.commands_with_args[command] = handler
    
    def process_command(self, command: str, args: List[str]) -> None:
        """处理命令
        
        Args:
            command: 命令名称
            args: 命令参数
        """
        # 首先检查无参数命令
        if command in self.commands:
            self.commands[command]()
        # 然后检查带参数命令
        elif command in self.commands_with_args:
            self.commands_with_args[command](args)
        else:
            self.app.state_manager.add_system_message(f"未知命令: {command}")
    
    def _handle_help(self) -> None:
        """处理help命令"""
        help_text = """
可用命令:
  /help - 显示帮助
  /clear - 清空屏幕
  /exit - 退出应用
  /save - 保存会话
  /load <session_id> - 加载会话
  /new - 创建新会话
  /pause - 暂停工作流
  /resume - 恢复工作流
  /stop - 停止工作流
  /studio - 打开系统管理界面
  /performance - 打开分析监控界面
  /debug - 打开可视化调试界面
  
子界面命令:
  /analytics - 打开分析监控界面
  /visualization - 打开可视化调试界面
  /system - 打开系统管理界面
  /errors - 打开错误反馈界面
  /sessions - 打开会话管理
  /agents - 打开Agent选择
  /main - 返回主界面

快捷键:
  Alt+1 - 分析监控
  Alt+2 - 可视化调试
  Alt+3 - 系统管理
  Alt+4 - 错误反馈
  ESC - 返回主界面
"""
        self.app.state_manager.add_system_message(help_text)
        if self.app.main_content_component:
            self.app.main_content_component.add_assistant_message(help_text)
    
    def _handle_clear(self) -> None:
        """处理clear命令"""
        self.app.state_manager.clear_message_history()
        if self.app.main_content_component:
            self.app.main_content_component.clear_all()
        self.app.state_manager.add_system_message("屏幕已清空")
    
    def _handle_exit(self) -> None:
        """处理exit命令"""
        self.app.running = False
    
    def _handle_save(self) -> None:
        """处理save命令"""
        if self.app.session_handler:
            success = self.app.session_handler.save_session(
                self.app.state_manager.session_id,
                self.app.state_manager.current_workflow,
                self.app.state_manager.current_state
            )
            if success:
                self.app.state_manager.add_system_message(f"会话 {self.app.state_manager.session_id[:8]}... 已保存")
            else:
                self.app.state_manager.add_system_message("保存会话失败")
        else:
            self.app.state_manager.add_system_message("无活动会话可保存")
    
    def _handle_load(self, args: List[str]) -> None:
        """处理load命令"""
        if not args:
            self.app.state_manager.add_system_message("请指定会话ID")
            return
        
        session_id = args[0]
        if self.app.session_handler:
            success = self.app.session_handler.load_session(session_id)
            if success:
                self.app.state_manager.session_id = session_id
                self.app.state_manager.add_system_message(f"会话 {session_id[:8]}... 已加载")
            else:
                self.app.state_manager.add_system_message("加载会话失败")
        else:
            self.app.state_manager.add_system_message("会话处理器未初始化")
    
    def _handle_new(self) -> None:
        """处理new命令"""
        self.app.state_manager.create_new_session()
        if self.app.main_content_component:
            self.app.main_content_component.clear_all()
        self.app.state_manager.add_system_message("已创建新会话")
    
    def _handle_pause(self) -> None:
        """处理pause命令"""
        self.app.state_manager.add_system_message("工作流已暂停")
    
    def _handle_resume(self) -> None:
        """处理resume命令"""
        self.app.state_manager.add_system_message("工作流已恢复")
    
    def _handle_stop(self) -> None:
        """处理stop命令"""
        self.app.state_manager.add_system_message("工作流已停止")
    
    def _handle_studio(self) -> None:
        """处理studio命令"""
        # 重定向到系统管理子界面
        self.app.state_manager.switch_to_subview("system")
    
    def _handle_performance(self) -> None:
        """处理performance命令"""
        # 重定向到分析监控子界面
        self.app.state_manager.switch_to_subview("analytics")
    
    def _handle_debug(self) -> None:
        """处理debug命令"""
        # 重定向到可视化调试子界面
        self.app.state_manager.switch_to_subview("visualization")