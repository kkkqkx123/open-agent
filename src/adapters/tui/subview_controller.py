"""TUI子界面控制器"""

from typing import Optional, Dict, Any, Callable

from .subviews import (
    AnalyticsSubview,
    VisualizationSubview,
    SystemSubview,
    ErrorFeedbackSubview
)


class SubviewController:
    """子界面控制器，负责管理子界面的切换和状态"""
    
    def __init__(self, subviews: Dict[str, Any]) -> None:
        """初始化子界面控制器
        
        Args:
            subviews: 子界面字典
        """
        self.subviews = subviews
        self.current_subview: Optional[str] = None
        
        # 子界面切换回调
        self.subview_switched_callbacks: list[Callable[[Optional[str]], None]] = []
    
    def switch_to_subview(self, subview_name: str) -> bool:
        """切换到指定子界面
        
        Args:
            subview_name: 子界面名称
            
        Returns:
            bool: 切换是否成功
        """
        valid_subviews = ["analytics", "visualization", "system", "errors", "status_overview"]
        if subview_name not in valid_subviews:
            return False
        
        old_subview = self.current_subview
        self.current_subview = subview_name
        
        # 触发切换回调
        self._trigger_subview_switched_callbacks(old_subview, subview_name)
        
        return True
    
    def return_to_main_view(self) -> None:
        """返回主界面"""
        old_subview = self.current_subview
        self.current_subview = None
        
        # 触发切换回调
        self._trigger_subview_switched_callbacks(old_subview, None)
    
    def get_current_subview(self) -> Optional[Any]:
        """获取当前子界面对象
        
        Returns:
            BaseSubview: 当前子界面对象
        """
        if not self.current_subview:
            return None
        
        return self.subviews.get(self.current_subview)
    
    def get_current_subview_name(self) -> Optional[str]:
        """获取当前子界面名称
        
        Returns:
            str: 当前子界面名称
        """
        return self.current_subview
    
    def is_in_subview(self) -> bool:
        """检查是否在子界面中
        
        Returns:
            bool: 是否在子界面中
        """
        return self.current_subview is not None
    
    def handle_key(self, key: str) -> bool:
        """处理按键输入
        
        Args:
            key: 按键字符串
            
        Returns:
            bool: 是否处理了该按键
        """
        # ESC键现在由主应用统一处理，不再在这里处理
        if key == "escape":
            return False  # 返回False让主应用处理
        
        # 其他按键交给具体子界面处理
        current_subview = self.get_current_subview()
        if current_subview and hasattr(current_subview, 'handle_key'):
            return current_subview.handle_key(key)
        return False
    
    def register_subview_switched_callback(self, callback: Callable[[Optional[str]], None]) -> None:
        """注册子界面切换回调
        
        Args:
            callback: 回调函数，接收新的子界面名称参数
        """
        self.subview_switched_callbacks.append(callback)
    
    def unregister_subview_switched_callback(self, callback: Callable[[Optional[str]], None]) -> bool:
        """取消注册子界面切换回调
        
        Args:
            callback: 回调函数
            
        Returns:
            bool: 是否成功取消注册
        """
        try:
            self.subview_switched_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def _trigger_subview_switched_callbacks(self, old_subview: Optional[str], new_subview: Optional[str]) -> None:
        """触发子界面切换回调
        
        Args:
            old_subview: 旧的子界面名称
            new_subview: 新的子界面名称
        """
        for callback in self.subview_switched_callbacks:
            try:
                callback(new_subview)
            except Exception as e:
                print(f"子界面切换回调错误: {e}")
    
    def update_subview_data(self, data_type: str, data: Dict[str, Any]) -> None:
        """更新子界面数据
        
        Args:
            data_type: 数据类型
            data: 数据内容
        """
        if self.current_subview == "analytics":
            self._update_analytics_data(data_type, data)
        elif self.current_subview == "visualization":
            self._update_visualization_data(data_type, data)
        elif self.current_subview == "system":
            self._update_system_data(data_type, data)
        elif self.current_subview == "errors":
            self._update_errors_data(data_type, data)
    
    def _update_analytics_data(self, data_type: str, data: Dict[str, Any]) -> None:
        """更新分析监控子界面数据
        
        Args:
            data_type: 数据类型
            data: 数据内容
        """
        analytics_view = self.subviews.get("analytics")
        if not analytics_view:
            return
        
        if data_type == "performance":
            analytics_view.update_performance_data(data)
        elif data_type == "system_metrics":
            analytics_view.update_system_metrics(data)
    
    def _update_visualization_data(self, data_type: str, data: Dict[str, Any]) -> None:
        """更新可视化调试子界面数据
        
        Args:
            data_type: 数据类型
            data: 数据内容
        """
        visualization_view = self.subviews.get("visualization")
        if not visualization_view:
            return
        
        if data_type == "workflow":
            visualization_view.update_workflow_data(data)
    
    def _update_system_data(self, data_type: str, data: Dict[str, Any]) -> None:
        """更新系统管理子界面数据
        
        Args:
            data_type: 数据类型
            data: 数据内容
        """
        system_view = self.subviews.get("system")
        if not system_view:
            return
        
        if data_type == "studio_status":
            system_view.update_studio_status(data)
    
    def _update_errors_data(self, data_type: str, data: Any) -> None:
        """更新错误反馈子界面数据
        
        Args:
            data_type: 数据类型
            data: 数据内容
        """
        errors_view = self.subviews.get("errors")
        if not errors_view:
            return
        
        if data_type == "error":
            errors_view.add_error(data)
    
    def refresh_current_subview(self) -> None:
        """刷新当前子界面"""
        current_subview = self.get_current_subview()
        if current_subview and hasattr(current_subview, 'refresh'):
            current_subview.refresh()
    
    def get_subview_info(self) -> Dict[str, Any]:
        """获取子界面信息
        
        Returns:
            Dict[str, Any]: 子界面信息
        """
        return {
            "current_subview": self.current_subview,
            "in_subview": self.is_in_subview(),
            "available_subviews": list(self.subviews.keys())
        }
    
    def setup_subview_callbacks(self, callback_manager: Any) -> None:
        """设置子界面回调
        
        Args:
            callback_manager: 回调管理器
        """
        # 设置分析监控子界面回调
        analytics_view = self.subviews.get("analytics")
        if analytics_view and hasattr(analytics_view, 'set_callback'):
            analytics_view.set_callback("data_refreshed", callback_manager.trigger_analytics_data_refreshed)
        
        # 设置可视化调试子界面回调
        visualization_view = self.subviews.get("visualization")
        if visualization_view and hasattr(visualization_view, 'set_callback'):
            visualization_view.set_callback("node_selected", callback_manager.trigger_visualization_node_selected)
        
        # 设置系统管理子界面回调
        system_view = self.subviews.get("system")
        if system_view and hasattr(system_view, 'set_callback'):
            system_view.set_callback("studio_started", callback_manager.trigger_studio_started)
            system_view.set_callback("studio_stopped", callback_manager.trigger_studio_stopped)
            system_view.set_callback("config_reloaded", callback_manager.trigger_config_reloaded)
        
        # 设置错误反馈子界面回调
        errors_view = self.subviews.get("errors")
        if errors_view and hasattr(errors_view, 'set_callback'):
            errors_view.set_callback("feedback_submitted", callback_manager.trigger_error_feedback_submitted)