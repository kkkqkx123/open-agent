"""导航栏组件"""

from typing import Any, Dict, Optional
from rich.panel import Panel
from rich.text import Text


class NavigationBarComponent:
    """导航栏组件 - 显示关键状态摘要"""
    
    def __init__(self, config: Optional[Any] = None) -> None:
        """初始化导航栏组件
        
        Args:
            config: 组件配置
        """
        self.config = config
        self.session_status = "未连接"
        self.agent_status = "未运行"
        self.workflow_status = "未启动"
        self.progress = 0.8  # 80%
        self.message_count = 15
        self.token_count = 2345
    
    def update_from_state(self, state: Any) -> None:
        """从状态更新导航栏信息
        
        Args:
            state: 当前状态
        """
        if state:
            # 更新会话状态
            if hasattr(state, 'session_id') and state.session_id:
                self.session_status = "已连接"
            else:
                self.session_status = "未连接"
            
            # 更新Agent状态
            if hasattr(state, 'agent_name') and state.agent_name:
                self.agent_status = state.agent_name
            else:
                self.agent_status = "未运行"
            
            # 更新工作流状态
            if hasattr(state, 'workflow_name') and state.workflow_name:
                self.workflow_status = state.workflow_name
            else:
                self.workflow_status = "未启动"
            
            # 更新进度
            if hasattr(state, 'progress'):
                self.progress = state.progress
            
            # 更新消息计数
            if hasattr(state, 'message_count'):
                self.message_count = state.message_count
            elif hasattr(state, 'messages'):
                self.message_count = len(state.messages)
            
            # 更新Token计数
            if hasattr(state, 'token_count'):
                self.token_count = state.token_count
    
    def render(self) -> Panel:
        """渲染导航栏"""
        nav_text = Text()
        
        # 关键状态信息摘要
        nav_text.append("💾 会话: ", style="bold blue")
        nav_text.append(f"{self.session_status} | ", style="dim")
        nav_text.append("🤖 Agent: ", style="bold cyan")
        nav_text.append(f"{self.agent_status} | ", style="dim")
        nav_text.append("🔄 工作流: ", style="bold yellow")
        nav_text.append(f"{self.workflow_status} | ", style="dim")
        
        # 进度条
        nav_text.append("进度: ", style="bold")
        progress_bar = "█" * int(self.progress * 10) + "░" * (10 - int(self.progress * 10))
        nav_text.append(f"{progress_bar} {int(self.progress * 100)}% | ", style="dim")
        
        # 消息和Token计数
        nav_text.append("消息: ", style="bold")
        nav_text.append(f"{self.message_count} | Token: {self.token_count:,}", style="dim")
        
        return Panel(nav_text, style="dim", border_style="dim")
    
    def get_height(self) -> int:
        """获取导航栏高度"""
        return 2  # 2行高度