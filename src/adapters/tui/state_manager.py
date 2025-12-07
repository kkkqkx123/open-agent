"""TUI状态管理器"""

from typing import Optional, Dict, Any, List, Callable
from typing import cast
import asyncio
from datetime import datetime
from src.interfaces.sessions.service import ISessionService
from src.core.state import WorkflowState


class StateManager:
    """状态管理器，负责管理应用状态、会话状态、UI状态"""
    
    def __init__(self, session_manager: Optional[ISessionService] = None) -> None:
        """初始化状态管理器
        
        Args:
            session_manager: 会话管理器
        """
        self.session_manager = session_manager
        self.session_id: Optional[str] = None
        self.current_state: Optional[Dict[str, Any]] = None
        self.current_workflow: Optional[Any] = None
        self.message_history: List[Dict[str, Any]] = []
        self.input_buffer = ""
        
        # 钩子列表
        self._user_message_hooks = []
        self._assistant_message_hooks = []
        self._tool_call_hooks = []
        
        # UI状态
        self._show_session_dialog = False
        self._show_agent_dialog = False
        self.current_subview: Optional[str] = None  # None, "analytics", "system", "errors"
        
        # 强制刷新标记 - 用于界面切换等场景
        self._force_refresh: bool = False
    
    def add_user_message_hook(self, hook: Callable[[str], None]) -> None:
        self._user_message_hooks.append(hook)
    
    def add_assistant_message_hook(self, hook: Callable[[str], None]) -> None:
        self._assistant_message_hooks.append(hook)
    
    def add_tool_call_hook(self, hook: Callable[[str, dict, Optional[dict]], None]) -> None:
        self._tool_call_hooks.append(hook)
    
    def create_session(self, workflow_config: str, agent_config: Optional[str] = None) -> bool:
        """创建新会话
        
        Args:
            workflow_config: 工作流配置
            agent_config: 代理配置
            
        Returns:
            bool: 创建是否成功
        """
        try:
            if not self.session_manager:
                return False
            
            # 创建用户请求
            from src.core.sessions.entities import UserRequestEntity
            user_request = UserRequestEntity(
                request_id=f"request_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                user_id="",
                content=f"创建会话: {workflow_config}",
                metadata={
                    "workflow_config": workflow_config,
                    "agent_config": agent_config
                },
                timestamp=datetime.now()
            )
            
            # 直接异步创建会话
            self.session_id = asyncio.run(
                self.session_manager.create_session(user_request)
            )
            
            if not self.session_id:
                return False

            # 清空消息历史
            self.message_history = []
            
            # 添加系统消息
            self.message_history.append({
                "type": "system",
                "content": f"新会话已创建: {self.session_id[:8]}..."
            })
            
            return True
            
        except Exception as e:
            print(f"创建会话失败: {e}")
            return False
    
    def load_session(self, session_id: str) -> bool:
        """加载会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 加载是否成功
        """
        if not self.session_manager:
            return False
        
        try:
            # 直接异步加载会话
            session_context = asyncio.run(
                self.session_manager.get_session_context(session_id)
            )
                
            if session_context:
                self.session_id = session_id
                self.message_history = []
                self.message_history.append({
                    "type": "system",
                    "content": f"会话 {session_id[:8]}... 已加载"
                })
                return True
            else:
                return False
        except Exception:
            return False
    
    def save_session(self) -> bool:
        """保存会话
        
        Returns:
            bool: 保存是否成功
        """
        # 新的SessionManager不需要显式保存，因为状态在执行过程中会自动保存
        # 这里保留方法但不执行任何操作以保持API兼容性
        return True
    def delete_session(self, session_id: str) -> bool:
        """删除会话
        
        Args:
            session_id: 会话ID
            
        Returns:
            bool: 删除是否成功
        """
        # 新的SessionManager没有直接的删除方法，需要通过其他方式实现
        # 这里暂时返回True以保持API兼容性，实际删除逻辑需要根据具体需求实现
        if self.session_id == session_id:
            self.session_id = None
            self.current_state = None
            self.current_workflow = None
            self.message_history = []
        return True
    
    def create_new_session(self) -> None:
        """创建新会话（重置状态）"""
        self.session_id = None
        self.current_state = {}
        self.current_workflow = None
        self.message_history = []
        self.input_buffer = ""
    
    def add_user_message(self, content: str) -> None:
        """添加用户消息
        
        Args:
            content: 消息内容
        """
        self.message_history.append({
            "type": "user",
            "content": content
        })
        
        # 更新状态
        if self.current_state:
            try:
                # 创建消息字典
                human_message = {"type": "human", "content": content}
                # WorkflowState是TypedDict，不支持add_message方法，需要使用字典方式添加消息
                messages = self.current_state.get('messages', [])
                messages.append(human_message)
                self.current_state['messages'] = messages
            except Exception:
                # 如果出错，使用字典方式
                simple_message = {"type": "human", "content": content}
                messages = self.current_state.get('messages', [])
                messages.append(simple_message)
                self.current_state['messages'] = messages
        
        # 触发钩子
        for hook in self._user_message_hooks:
            try:
                hook(content)
            except Exception:
                pass # 忽略钩子错误
    
    def add_assistant_message(self, content: str) -> None:
        """添加助手消息
        
        Args:
            content: 消息内容
        """
        self.message_history.append({
            "type": "assistant",
            "content": content
        })
        
        # 触发钩子
        for hook in self._assistant_message_hooks:
            try:
                hook(content)
            except Exception:
                pass # 忽略钩子错误
    
    def add_tool_call(self, tool_name: str, tool_input: dict, tool_output: Optional[dict] = None) -> None:
        """添加工具调用记录
        
        Args:
            tool_name: 工具名称
            tool_input: 工具输入
            tool_output: 工具输出（可选）
        """
        self.message_history.append({
            "type": "tool_call",
            "tool_name": tool_name,
            "tool_input": tool_input,
            "tool_output": tool_output
        })
        
        # 触发钩子
        for hook in self._tool_call_hooks:
            try:
                hook(tool_name, tool_input, tool_output)
            except Exception:
                pass # 忽略钩子错误
    
    def add_system_message(self, content: str) -> None:
        """添加系统消息
        
        Args:
            content: 消息内容
        """
        self.message_history.append({
            "type": "system",
            "content": content
        })
    
    def set_input_buffer(self, text: str) -> None:
        """设置输入缓冲区
        
        Args:
            text: 输入文本
        """
        self.input_buffer = text
    
    def clear_input_buffer(self) -> None:
        """清空输入缓冲区"""
        self.input_buffer = ""
    
    def clear_message_history(self) -> None:
        """清空消息历史"""
        self.message_history = []
    
    def switch_to_subview(self, subview_name: str) -> bool:
        """切换到指定子界面
        
        Args:
            subview_name: 子界面名称
            
        Returns:
            bool: 切换是否成功
        """
        valid_subviews = ["analytics", "visualization", "system", "errors", "status_overview"]
        if subview_name in valid_subviews:
            self.current_subview = subview_name
            return True
        return False
    
    def return_to_main_view(self) -> None:
        """返回主界面"""
        self.current_subview = None
    
    def set_show_session_dialog(self, show: bool = True) -> None:
        """显示/隐藏会话对话框
        
        Args:
            show: 是否显示
        """
        self._show_session_dialog = show
    
    def set_show_agent_dialog(self, show: bool = True) -> None:
        """显示/隐藏Agent对话框
        
        Args:
            show: 是否显示
        """
        self._show_agent_dialog = show
    
    @property
    def show_session_dialog(self) -> bool:
        """获取会话对话框显示状态"""
        return self._show_session_dialog
    
    @property
    def show_agent_dialog(self) -> bool:
        """获取Agent对话框显示状态"""
        return self._show_agent_dialog
    
    def get_performance_data(self) -> Dict[str, Any]:
        """获取性能数据
        
        Returns:
            Dict[str, Any]: 性能数据
        """
        if not self.current_state:
            return {}
        
        return {
            "total_requests": self.current_state.get('total_requests', 0),
            "avg_response_time": self.current_state.get('avg_response_time', 0.0),
            "success_rate": self.current_state.get('success_rate', 100.0),
            "error_count": self.current_state.get('error_count', 0),
            "tokens_used": self.current_state.get('tokens_used', 0),
            "cost_estimate": self.current_state.get('cost_estimate', 0.0)
        }
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标
        
        Returns:
            Dict[str, Any]: 系统指标
        """
        if not self.current_state:
            return {}
        
        return {
            "cpu_usage": self.current_state.get('cpu_usage', 0.0),
            "memory_usage": self.current_state.get('memory_usage', 0.0),
            "disk_usage": self.current_state.get('disk_usage', 0.0),
            "network_io": self.current_state.get('network_io', 0.0)
        }
    
    def get_workflow_data(self) -> Dict[str, Any]:
        """获取工作流数据
        
        Returns:
            Dict[str, Any]: 工作流数据
        """
        if not self.current_state:
            return {}
        
        return {
            "nodes": self.current_state.get('workflow_nodes', []),
            "edges": self.current_state.get('workflow_edges', []),
            "current_node": self.current_state.get('current_step', None),
            "execution_path": self.current_state.get('execution_path', []),
            "node_states": self.current_state.get('node_states', {})
        }
    
    def get_studio_status(self) -> Dict[str, Any]:
        """获取Studio状态
        
        Returns:
            Dict[str, Any]: Studio状态
        """
        if not self.current_state:
            return {}
        
        return {
            "running": self.current_state.get('studio_running', False),
            "port": self.current_state.get('studio_port', 8079),
            "url": self.current_state.get('studio_url', ""),
            "start_time": self.current_state.get('studio_start_time', None),
            "version": "1.0.0",
            "connected_clients": self.current_state.get('studio_clients', 0)
        }
    
    def get_errors(self) -> List[Dict[str, Any]]:
        """获取错误列表
        
        Returns:
            List[Dict[str, Any]]: 错误列表
        """
        if not self.current_state or not self.current_state.get('errors', None):
            return []
        
        errors = self.current_state.get('errors', [])
        # 如果错误是字符串列表，需要转换为字典列表
        if errors and isinstance(errors, list) and len(errors) > 0 and isinstance(errors[0], str):
            # 将字符串列表转换为字典列表
            return [{"message": error, "type": "error"} for error in errors]
        elif isinstance(errors, list):
            return errors
        else:
            return []