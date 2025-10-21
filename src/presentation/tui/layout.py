"""TUI响应式布局管理器"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.tree import Tree


class LayoutRegion(Enum):
    """布局区域枚举"""
    HEADER = "header"
    SIDEBAR = "sidebar"
    MAIN = "main"
    INPUT = "input"
    LANGGRAPH = "langgraph"
    STATUS = "status"


@dataclass
class RegionConfig:
    """区域配置"""
    name: str
    min_size: int
    max_size: Optional[int] = None
    ratio: int = 1
    resizable: bool = True
    visible: bool = True


@dataclass
class LayoutConfig:
    """布局配置"""
    regions: Dict[LayoutRegion, RegionConfig]
    min_terminal_width: int = 80
    min_terminal_height: int = 24
    responsive_breakpoints: Optional[Dict[str, Tuple[int, int]]] = None
    
    def __post_init__(self) -> None:
        if self.responsive_breakpoints is None:
            self.responsive_breakpoints = {
                "small": (80, 24),
                "medium": (100, 30),
                "large": (120, 40),
                "xlarge": (140, 50)
            }


class ILayoutManager(ABC):
    """布局管理器接口"""
    
    @abstractmethod
    def create_layout(self, terminal_size: Tuple[int, int]) -> Layout:
        """创建布局
        
        Args:
            terminal_size: 终端尺寸 (width, height)
            
        Returns:
            Layout: Rich布局对象
        """
        pass
    
    @abstractmethod
    def update_region_content(self, region: LayoutRegion, content: Any) -> None:
        """更新区域内容
        
        Args:
            region: 区域类型
            content: 内容
        """
        pass
    
    @abstractmethod
    def resize_layout(self, terminal_size: Tuple[int, int]) -> None:
        """调整布局大小
        
        Args:
            terminal_size: 新的终端尺寸
        """
        pass
    
    @abstractmethod
    def get_region_size(self, region: LayoutRegion) -> Tuple[int, int]:
        """获取区域尺寸
        
        Args:
            region: 区域类型
            
        Returns:
            Tuple[int, int]: 区域尺寸 (width, height)
        """
        pass


class LayoutManager(ILayoutManager):
    """响应式布局管理器实现"""
    
    def __init__(self, config: Optional[LayoutConfig] = None) -> None:
        """初始化布局管理器
        
        Args:
            config: 布局配置
        """
        self.config = config or self._create_default_config()
        self.console = Console()
        self.layout: Optional[Layout] = None
        self.terminal_size: Tuple[int, int] = (80, 24)
        self.region_contents: Dict[LayoutRegion, Any] = {}
        self.current_breakpoint: str = "small"
        
    def _create_default_config(self) -> LayoutConfig:
        """创建默认布局配置"""
        regions = {
            LayoutRegion.HEADER: RegionConfig(
                name="标题栏",
                min_size=3,
                max_size=5,
                ratio=1,
                resizable=False
            ),
            LayoutRegion.SIDEBAR: RegionConfig(
                name="侧边栏",
                min_size=15,  # 减小最小尺寸
                max_size=25,  # 减小最大尺寸
                ratio=1,
                resizable=True
            ),
            LayoutRegion.MAIN: RegionConfig(
                name="主内容区",
                min_size=30,
                ratio=3,
                resizable=True
            ),
            LayoutRegion.INPUT: RegionConfig(
                name="输入栏",
                min_size=3,
                max_size=5,
                ratio=1,
                resizable=False
            ),
            LayoutRegion.LANGGRAPH: RegionConfig(
                name="LangGraph面板",
                min_size=15,
                max_size=30,
                ratio=1,
                resizable=True,
                visible=False  # 默认隐藏
            ),
            LayoutRegion.STATUS: RegionConfig(
                name="状态栏",
                min_size=1,
                max_size=1,
                ratio=1,
                resizable=False
            )
        }
        
        return LayoutConfig(regions=regions)
    
    def create_layout(self, terminal_size: Tuple[int, int]) -> Layout:
        """创建布局"""
        self.terminal_size = terminal_size
        self.current_breakpoint = self._determine_breakpoint(terminal_size)
        
        # 创建Rich布局
        layout = Layout()
        
        # 根据断点调整布局结构
        if self.current_breakpoint in ["small", "medium"]:
            layout = self._create_compact_layout(layout)
        else:
            layout = self._create_full_layout(layout)
        
        self.layout = layout
        return layout
    
    def _create_full_layout(self, layout: Layout) -> Layout:
        """创建完整布局（适用于大屏幕）"""
        # 分割为上下两部分
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="body"),
            Layout(name="input", size=3),
            Layout(name="status", size=1)  # 添加状态栏
        )
        
        # 主体部分分割为两部分（移除LangGraph面板）
        layout["body"].split_row(
            Layout(name="sidebar", size=25),  # 减小侧边栏宽度
            Layout(name="main")
        )
        
        # 设置区域内容
        self._update_layout_regions()
        
        return layout
    
    def _create_compact_layout(self, layout: Layout) -> Layout:
        """创建紧凑布局（适用于小屏幕）"""
        # 小屏幕时隐藏侧边栏或将其移到底部
        if self.current_breakpoint == "small":
            # 分割为上下三部分
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="input", size=3),
                Layout(name="status", size=1)
            )
        else:  # medium
            # 分割为上下两部分，底部包含侧边栏
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="bottom", size=10),
                Layout(name="status", size=1)
            )
            
            # 底部分割为左右两部分
            layout["bottom"].split_row(
                Layout(name="sidebar"),
                Layout(name="info")
            )
        
        # 设置区域内容
        self._update_layout_regions()
        
        return layout
    
    def _has_region(self, region_name: str) -> bool:
        """检查布局中是否存在指定区域
        
        Args:
            region_name: 区域名称
            
        Returns:
            bool: 是否存在该区域
        """
        if not self.layout:
            return False
        
        try:
            _ = self.layout[region_name]
            return True
        except KeyError:
            return False
    
    def _update_layout_regions(self) -> None:
        """更新布局区域内容"""
        if not self.layout:
            return
        
        # 更新标题栏
        header_content = self.region_contents.get(LayoutRegion.HEADER)
        if header_content:
            self.layout["header"].update(header_content)
        else:
            self.layout["header"].update(self._create_default_header())
        
        # 更新侧边栏
        if self.layout:
            try:
                _ = self.layout["sidebar"]
                sidebar_exists = True
            except KeyError:
                sidebar_exists = False
            
            if sidebar_exists:
                sidebar_content = self.region_contents.get(LayoutRegion.SIDEBAR)
                if sidebar_content:
                    self.layout["sidebar"].update(sidebar_content)
                else:
                    self.layout["sidebar"].update(self._create_default_sidebar())
        
        # 更新主内容区
        main_content = self.region_contents.get(LayoutRegion.MAIN)
        if main_content:
            self.layout["main"].update(main_content)
        else:
            self.layout["main"].update(self._create_default_main())
        
        # 更新输入栏
        input_content = self.region_contents.get(LayoutRegion.INPUT)
        if input_content:
            self.layout["input"].update(input_content)
        else:
            self.layout["input"].update(self._create_default_input())
        
        # 更新LangGraph面板
        if self.layout:
            try:
                _ = self.layout["langgraph"]
                langgraph_exists = True
            except KeyError:
                langgraph_exists = False
            
            if langgraph_exists:
                langgraph_content = self.region_contents.get(LayoutRegion.LANGGRAPH)
                if langgraph_content:
                    self.layout["langgraph"].update(langgraph_content)
                else:
                    self.layout["langgraph"].update(self._create_default_langgraph())
        
        # 更新状态栏
        if self.layout:
            try:
                _ = self.layout["status"]
                status_exists = True
            except KeyError:
                status_exists = False
            
            if status_exists:
                status_content = self.region_contents.get(LayoutRegion.STATUS)
                if status_content:
                    self.layout["status"].update(status_content)
                else:
                    self.layout["status"].update(self._create_default_status())
    
    def _create_default_header(self) -> Panel:
        """创建默认标题栏"""
        title = Text("模块化代理框架", style="bold cyan")
        subtitle = Text("TUI界面", style="dim")
        
        header_content = Text()
        header_content.append(title)
        header_content.append(" - ")
        header_content.append(subtitle)
        
        return Panel(
            header_content,
            style="blue",
            border_style="blue"
        )
    
    def _create_default_sidebar(self) -> Panel:
        """创建默认侧边栏"""
        tree = Tree("会话信息")
        tree.add("会话ID: 12345678")
        tree.add("工作流: example.yaml")
        tree.add("状态: 运行中")
        
        return Panel(
            tree,
            title="会话",
            border_style="green"
        )
    
    def _create_default_main(self) -> Panel:
        """创建默认主内容区"""
        content = Text("欢迎使用模块化代理框架TUI界面\n\n", style="bold")
        content.append("这里显示主要内容和对话历史\n\n", style="dim")
        content.append("使用快捷键:\n", style="yellow")
        content.append("Ctrl+C - 退出\n", style="dim")
        content.append("Ctrl+H - 帮助\n", style="dim")
        
        return Panel(
            content,
            title="主内容",
            border_style="white"
        )
    
    def _create_default_input(self) -> Panel:
        """创建默认输入栏"""
        input_text = Text("> ", style="bold green")
        input_text.append("在此输入消息...", style="dim")
        
        return Panel(
            input_text,
            title="输入",
            border_style="green"
        )
    
    def _create_default_langgraph(self) -> Panel:
        """创建默认LangGraph面板"""
        content = Text("LangGraph状态面板\n\n", style="bold")
        content.append("当前节点: 未运行\n", style="dim")
        content.append("执行路径: 无历史\n", style="dim")
        content.append("状态快照: 无快照\n\n", style="dim")
        content.append("Studio: 未启动", style="dim")
        
        return Panel(
            content,
            title="LangGraph状态",
            border_style="cyan"
        )
    
    def _create_default_status(self) -> Panel:
        """创建默认状态栏"""
        status_text = Text()
        status_text.append("快捷键: ", style="bold")
        status_text.append("Alt+1=分析, Alt+2=可视化, Alt+3=系统, Alt+4=错误, ESC=返回", style="dim")
        status_text.append(" | ", style="dim")
        status_text.append("状态: 就绪", style="green")
        
        return Panel(
            status_text,
            style="dim",
            border_style="dim"
        )
    
    def update_region_content(self, region: LayoutRegion, content: Any) -> None:
        """更新区域内容"""
        self.region_contents[region] = content
        if self.layout:
            self._update_layout_regions()
    
    def resize_layout(self, terminal_size: Tuple[int, int]) -> None:
        """调整布局大小"""
        old_breakpoint = self.current_breakpoint
        self.terminal_size = terminal_size
        self.current_breakpoint = self._determine_breakpoint(terminal_size)
        
        # 如果断点发生变化，重新创建布局
        if old_breakpoint != self.current_breakpoint:
            self.create_layout(terminal_size)
        elif self.layout:
            # 否则只调整区域大小
            self._adjust_region_sizes()
    
    def _determine_breakpoint(self, terminal_size: Tuple[int, int]) -> str:
        """确定响应式断点"""
        width, height = terminal_size
        
        for breakpoint_name, (min_width, min_height) in sorted(
            self.config.responsive_breakpoints.items() if self.config.responsive_breakpoints else {}.items(),
            key=lambda x: x[1][0],  # 按宽度排序
            reverse=True
        ):
            if width >= min_width and height >= min_height:
                return breakpoint_name
        
        return "small"
    
    def _adjust_region_sizes(self) -> None:
        """调整区域大小"""
        if not self.layout:
            return
        
        width, height = self.terminal_size
        
        # 根据终端尺寸调整各区域大小
        if self.current_breakpoint == "small":
            # 小屏幕布局
            header_size = min(3, height // 8)
            input_size = min(3, height // 8)
            
            if self._has_region("header"):
                self.layout["header"].size = header_size
            if self._has_region("input"):
                self.layout["input"].size = input_size
        else:
            # 大屏幕布局
            header_size = 3
            input_size = 3
            sidebar_size = min(30, width // 4)
            
            if self._has_region("header"):
                self.layout["header"].size = header_size
            if self._has_region("input"):
                self.layout["input"].size = input_size
            if self._has_region("sidebar"):
                self.layout["sidebar"].size = sidebar_size
    
    def get_region_size(self, region: LayoutRegion) -> Tuple[int, int]:
        """获取区域尺寸"""
        if not self.layout:
            return (0, 0)
        
        region_name = region.value
        if not self._has_region(region_name):
            return (0, 0)
        
        # 获取区域的实际尺寸
        region_layout = self.layout[region_name]
        if hasattr(region_layout, 'size') and region_layout.size:
            # 简化逻辑，直接返回基于终端尺寸和区域大小的结果
            # 这里假设区域是布局的直接子元素
            if hasattr(self.layout, 'split') and self.layout.split == "column":
                # 垂直布局
                return (self.terminal_size[0], region_layout.size)
            else:
                # 水平布局
                return (region_layout.size, self.terminal_size[1])
        
        # 默认返回终端尺寸
        return self.terminal_size
    
    def get_current_breakpoint(self) -> str:
        """获取当前断点"""
        return self.current_breakpoint
    
    def is_region_visible(self, region: LayoutRegion) -> bool:
        """检查区域是否可见"""
        if self.current_breakpoint == "small" and region == LayoutRegion.SIDEBAR:
            return False
        return self.config.regions[region].visible