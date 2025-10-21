"""TUI回调管理器"""

from typing import Dict, Any, Callable, Optional, List


class CallbackManager:
    """回调管理器，统一管理各种回调函数"""
    
    def __init__(self) -> None:
        """初始化回调管理器"""
        self.callbacks: Dict[str, List[Callable]] = {}
    
    def register_callback(self, event_type: str, callback: Callable) -> None:
        """注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
        """
        if event_type not in self.callbacks:
            self.callbacks[event_type] = []
        
        self.callbacks[event_type].append(callback)
    
    def unregister_callback(self, event_type: str, callback: Callable) -> bool:
        """取消注册回调函数
        
        Args:
            event_type: 事件类型
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        if event_type in self.callbacks:
            try:
                self.callbacks[event_type].remove(callback)
                return True
            except ValueError:
                pass
        return False
    
    def trigger_callback(self, event_type: str, *args, **kwargs) -> None:
        """触发回调函数
        
        Args:
            event_type: 事件类型
            *args: 位置参数
            **kwargs: 关键字参数
        """
        if event_type in self.callbacks:
            for callback in self.callbacks[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    print(f"回调函数执行错误 ({event_type}): {e}")
    
    def clear_callbacks(self, event_type: Optional[str] = None) -> None:
        """清空回调函数
        
        Args:
            event_type: 事件类型，如果为None则清空所有
        """
        if event_type:
            if event_type in self.callbacks:
                self.callbacks[event_type].clear()
        else:
            self.callbacks.clear()
    
    def get_callback_count(self, event_type: str) -> int:
        """获取指定事件类型的回调函数数量
        
        Args:
            event_type: 事件类型
            
        Returns:
            int: 回调函数数量
        """
        return len(self.callbacks.get(event_type, []))
    
    def has_callbacks(self, event_type: str) -> bool:
        """检查是否有指定事件类型的回调函数
        
        Args:
            event_type: 事件类型
            
        Returns:
            bool: 是否有回调函数
        """
        return event_type in self.callbacks and len(self.callbacks[event_type]) > 0


class TUICallbackManager(CallbackManager):
    """TUI专用回调管理器，包含预定义的回调类型"""
    
    # 预定义的回调事件类型
    EVENT_SESSION_SELECTED = "session_selected"
    EVENT_SESSION_CREATED = "session_created"
    EVENT_SESSION_DELETED = "session_deleted"
    EVENT_AGENT_SELECTED = "agent_selected"
    EVENT_ANALYTICS_DATA_REFRESHED = "analytics_data_refreshed"
    EVENT_VISUALIZATION_NODE_SELECTED = "visualization_node_selected"
    EVENT_STUDIO_STARTED = "studio_started"
    EVENT_STUDIO_STOPPED = "studio_stopped"
    EVENT_CONFIG_RELOADED = "config_reloaded"
    EVENT_ERROR_FEEDBACK_SUBMITTED = "error_feedback_submitted"
    EVENT_INPUT_SUBMIT = "input_submit"
    EVENT_COMMAND = "command"
    EVENT_KEY_PRESSED = "key_pressed"
    EVENT_SUBVIEW_SWITCHED = "subview_switched"
    EVENT_DIALOG_OPENED = "dialog_opened"
    EVENT_DIALOG_CLOSED = "dialog_closed"
    
    def __init__(self) -> None:
        """初始化TUI回调管理器"""
        super().__init__()
    
    def register_session_selected_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话选择回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.register_callback(self.EVENT_SESSION_SELECTED, callback)
    
    def register_session_created_callback(self, callback: Callable[[str, Optional[str]], None]) -> None:
        """注册会话创建回调
        
        Args:
            callback: 回调函数，接收workflow_config和agent_config参数
        """
        self.register_callback(self.EVENT_SESSION_CREATED, callback)
    
    def register_session_deleted_callback(self, callback: Callable[[str], None]) -> None:
        """注册会话删除回调
        
        Args:
            callback: 回调函数，接收session_id参数
        """
        self.register_callback(self.EVENT_SESSION_DELETED, callback)
    
    def register_agent_selected_callback(self, callback: Callable[[Any], None]) -> None:
        """注册Agent选择回调
        
        Args:
            callback: 回调函数，接收agent_config参数
        """
        self.register_callback(self.EVENT_AGENT_SELECTED, callback)
    
    def register_analytics_data_refreshed_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册分析监控数据刷新回调
        
        Args:
            callback: 回调函数，接收data参数
        """
        self.register_callback(self.EVENT_ANALYTICS_DATA_REFRESHED, callback)
    
    def register_visualization_node_selected_callback(self, callback: Callable[[str], None]) -> None:
        """注册可视化节点选择回调
        
        Args:
            callback: 回调函数，接收node_id参数
        """
        self.register_callback(self.EVENT_VISUALIZATION_NODE_SELECTED, callback)
    
    def register_studio_started_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册Studio启动回调
        
        Args:
            callback: 回调函数，接收studio_status参数
        """
        self.register_callback(self.EVENT_STUDIO_STARTED, callback)
    
    def register_studio_stopped_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册Studio停止回调
        
        Args:
            callback: 回调函数，接收studio_status参数
        """
        self.register_callback(self.EVENT_STUDIO_STOPPED, callback)
    
    def register_config_reloaded_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册配置重载回调
        
        Args:
            callback: 回调函数，接收config_data参数
        """
        self.register_callback(self.EVENT_CONFIG_RELOADED, callback)
    
    def register_error_feedback_submitted_callback(self, callback: Callable[[Dict[str, Any]], None]) -> None:
        """注册错误反馈提交回调
        
        Args:
            callback: 回调函数，接收feedback_data参数
        """
        self.register_callback(self.EVENT_ERROR_FEEDBACK_SUBMITTED, callback)
    
    def register_input_submit_callback(self, callback: Callable[[str], None]) -> None:
        """注册输入提交回调
        
        Args:
            callback: 回调函数，接收input_text参数
        """
        self.register_callback(self.EVENT_INPUT_SUBMIT, callback)
    
    def register_command_callback(self, callback: Callable[[str, List[str]], None]) -> None:
        """注册命令回调
        
        Args:
            callback: 回调函数，接收command和args参数
        """
        self.register_callback(self.EVENT_COMMAND, callback)
    
    def register_key_pressed_callback(self, callback: Callable[[str], bool]) -> None:
        """注册按键回调
        
        Args:
            callback: 回调函数，接收key参数，返回是否处理了该按键
        """
        self.register_callback(self.EVENT_KEY_PRESSED, callback)
    
    def register_subview_switched_callback(self, callback: Callable[[Optional[str]], None]) -> None:
        """注册子界面切换回调
        
        Args:
            callback: 回调函数，接收subview_name参数
        """
        self.register_callback(self.EVENT_SUBVIEW_SWITCHED, callback)
    
    def register_dialog_opened_callback(self, callback: Callable[[str], None]) -> None:
        """注册对话框打开回调
        
        Args:
            callback: 回调函数，接收dialog_type参数
        """
        self.register_callback(self.EVENT_DIALOG_OPENED, callback)
    
    def register_dialog_closed_callback(self, callback: Callable[[str], None]) -> None:
        """注册对话框关闭回调
        
        Args:
            callback: 回调函数，接收dialog_type参数
        """
        self.register_callback(self.EVENT_DIALOG_CLOSED, callback)
    
    # 触发回调的便捷方法
    def trigger_session_selected(self, session_id: str) -> None:
        """触发会话选择回调"""
        self.trigger_callback(self.EVENT_SESSION_SELECTED, session_id)
    
    def trigger_session_created(self, workflow_config: str, agent_config: Optional[str] = None) -> None:
        """触发会话创建回调"""
        self.trigger_callback(self.EVENT_SESSION_CREATED, workflow_config, agent_config)
    
    def trigger_session_deleted(self, session_id: str) -> None:
        """触发会话删除回调"""
        self.trigger_callback(self.EVENT_SESSION_DELETED, session_id)
    
    def trigger_agent_selected(self, agent_config: Any) -> None:
        """触发Agent选择回调"""
        self.trigger_callback(self.EVENT_AGENT_SELECTED, agent_config)
    
    def trigger_analytics_data_refreshed(self, data: Dict[str, Any]) -> None:
        """触发分析监控数据刷新回调"""
        self.trigger_callback(self.EVENT_ANALYTICS_DATA_REFRESHED, data)
    
    def trigger_visualization_node_selected(self, node_id: str) -> None:
        """触发可视化节点选择回调"""
        self.trigger_callback(self.EVENT_VISUALIZATION_NODE_SELECTED, node_id)
    
    def trigger_studio_started(self, studio_status: Dict[str, Any]) -> None:
        """触发Studio启动回调"""
        self.trigger_callback(self.EVENT_STUDIO_STARTED, studio_status)
    
    def trigger_studio_stopped(self, studio_status: Dict[str, Any]) -> None:
        """触发Studio停止回调"""
        self.trigger_callback(self.EVENT_STUDIO_STOPPED, studio_status)
    
    def trigger_config_reloaded(self, config_data: Dict[str, Any]) -> None:
        """触发配置重载回调"""
        self.trigger_callback(self.EVENT_CONFIG_RELOADED, config_data)
    
    def trigger_error_feedback_submitted(self, feedback_data: Dict[str, Any]) -> None:
        """触发错误反馈提交回调"""
        self.trigger_callback(self.EVENT_ERROR_FEEDBACK_SUBMITTED, feedback_data)
    
    def trigger_input_submit(self, input_text: str) -> None:
        """触发输入提交回调"""
        self.trigger_callback(self.EVENT_INPUT_SUBMIT, input_text)
    
    def trigger_command(self, command: str, args: List[str]) -> None:
        """触发命令回调"""
        self.trigger_callback(self.EVENT_COMMAND, command, args)
    
    def trigger_key_pressed(self, key: str) -> bool:
        """触发按键回调，返回是否有处理器处理了该按键"""
        handled = False
        if self.EVENT_KEY_PRESSED in self.callbacks:
            for callback in self.callbacks[self.EVENT_KEY_PRESSED]:
                try:
                    if callback(key):
                        handled = True
                        break
                except Exception as e:
                    print(f"按键回调执行错误: {e}")
        return handled
    
    def trigger_subview_switched(self, subview_name: Optional[str]) -> None:
        """触发子界面切换回调"""
        self.trigger_callback(self.EVENT_SUBVIEW_SWITCHED, subview_name)
    
    def trigger_dialog_opened(self, dialog_type: str) -> None:
        """触发对话框打开回调"""
        self.trigger_callback(self.EVENT_DIALOG_OPENED, dialog_type)
    
    def trigger_dialog_closed(self, dialog_type: str) -> None:
        """触发对话框关闭回调"""
        self.trigger_callback(self.EVENT_DIALOG_CLOSED, dialog_type)