"""TUI响应式布局管理器"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List, Callable
from dataclasses import dataclass
from enum import Enum
import time
from src.interfaces.dependency_injection import get_logger

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
    WORKFLOW = "workflow"
    STATUS = "status"
    NAVIGATION = "navigation"


@dataclass
class RegionConfig:
    """区域配置"""
    name: str
    min_size: int
    max_size: Optional[int] = None
    ratio: int = 1
    resizable: bool = True
    visible: bool = True
    # 新增尺寸约束
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None


@dataclass
class LayoutConfig:
    """布局配置"""
    regions: Dict[LayoutRegion, RegionConfig]
    min_terminal_width: int = 80
    min_terminal_height: int = 24
    responsive_breakpoints: Optional[Dict[str, Tuple[int, int]]] = None
    # 新增配置项
    resize_threshold: Tuple[int, int] = (6, 3)  # (width, height) 变化阈值
    resize_throttle_ms: int = 30  # resize 事件节流时间
    sidebar_width_range: Tuple[int, int] = (20, 40)  # 侧边栏宽度范围
    workflow_width_range: Tuple[int, int] = (15, 30)  # 工作流区域宽度范围
    
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

    @abstractmethod
    def clear_region_contents(self) -> None:
        """清除所有区域内容缓存，强制下次更新时触发渲染"""
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
        self._last_breakpoint: str = "small"  # 记录上一次断点
        
        # 新增属性用于优化
        self.layout_changed_callbacks: List[Callable[[str, Tuple[int, int]], None]] = []
        self.region_content_cache: Dict[LayoutRegion, Any] = {}
        self.last_resize_time: float = 0
        self.resize_debounce_delay: float = self.config.resize_throttle_ms / 1000.0  # 转换为秒
        self.breakpoint_buffer_threshold: int = 3  # 增加断点切换缓冲阈值，减少频繁切换
        
        # 记录区域父级方向，用于尺寸计算
        self.region_parent_direction: Dict[str, str] = {}
        
    def _create_default_config(self) -> LayoutConfig:
        """创建默认布局配置"""
        regions = {
            LayoutRegion.HEADER: RegionConfig(
                name="标题栏",
                min_size=3,
                max_size=5,
                ratio=1,
                resizable=False,
                min_height=3,
                max_height=5
            ),
            LayoutRegion.SIDEBAR: RegionConfig(
                name="侧边栏",
                min_size=15,
                max_size=25,
                ratio=1,
                resizable=True,
                min_width=15,
                max_width=40
            ),
            LayoutRegion.MAIN: RegionConfig(
                name="主内容区",
                min_size=30,
                ratio=3,
                resizable=True,
                min_width=30
            ),
            LayoutRegion.INPUT: RegionConfig(
                name="输入栏",
                min_size=3,
                max_size=5,
                ratio=1,
                resizable=False,
                min_height=3,
                max_height=5
            ),
            LayoutRegion.WORKFLOW: RegionConfig(
                name="工作流面板",
                min_size=15,
                max_size=30,
                ratio=1,
                resizable=True,
                visible=False,  # 默认隐藏
                min_width=15,
                max_width=30
            ),
            LayoutRegion.STATUS: RegionConfig(
                name="状态栏",
                min_size=1,
                max_size=1,
                ratio=1,
                resizable=False,
                min_height=1,
                max_height=1
            ),
            LayoutRegion.NAVIGATION: RegionConfig(
                name="导航栏",
                min_size=2,
                max_size=3,
                ratio=1,
                resizable=False,
                min_height=2,
                max_height=3
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
        # 分割为上下五部分
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),           # 主内容区占据最大空间
            Layout(name="input", size=3),
            Layout(name="status", size=1),
            Layout(name="navigation", size=2)  # 新增导航栏
        )
        
        # 记录垂直布局区域
        self.region_parent_direction["header"] = "column"
        self.region_parent_direction["main"] = "column"
        self.region_parent_direction["input"] = "column"
        self.region_parent_direction["status"] = "column"
        self.region_parent_direction["navigation"] = "column"
        
        # 设置区域内容
        self._update_layout_regions()
        
        return layout
    
    def _create_compact_layout(self, layout: Layout) -> Layout:
        """创建紧凑布局（适用于小屏幕）"""
        # 小屏幕时隐藏侧边栏或将其移到底部
        if self.current_breakpoint == "small":
            # 分割为上下五部分
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="input", size=3),
                Layout(name="status", size=1),
                Layout(name="navigation", size=2)  # 新增导航栏
            )
            # 记录区域父级方向
            self.region_parent_direction["header"] = "column"
            self.region_parent_direction["main"] = "column"
            self.region_parent_direction["input"] = "column"
            self.region_parent_direction["status"] = "column"
            self.region_parent_direction["navigation"] = "column"
        else:  # medium
            # 分割为上下五部分
            layout.split_column(
                Layout(name="header", size=3),
                Layout(name="main"),
                Layout(name="input", size=3),
                Layout(name="status", size=1),
                Layout(name="navigation", size=2)  # 新增导航栏
            )
            
            # 记录区域父级方向
            self.region_parent_direction["header"] = "column"
            self.region_parent_direction["main"] = "column"
            self.region_parent_direction["input"] = "column"
            self.region_parent_direction["status"] = "column"
            self.region_parent_direction["navigation"] = "column"
        
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
        if self.layout is not None and self._has_region("header"):
            header_content = self.region_contents.get(LayoutRegion.HEADER)
            if header_content:
                self.layout["header"].update(header_content)
            else:
                self.layout["header"].update(self._create_default_header())
        
        # 更新侧边栏
        if self.layout is not None and self._has_region("sidebar"):
            sidebar_content = self.region_contents.get(LayoutRegion.SIDEBAR)
            if sidebar_content:
                self.layout["sidebar"].update(sidebar_content)
            else:
                self.layout["sidebar"].update(self._create_default_sidebar())
        
        # 更新主内容区
        if self.layout is not None and self._has_region("main"):
            main_content = self.region_contents.get(LayoutRegion.MAIN)
            if main_content:
                self.layout["main"].update(main_content)
            else:
                self.layout["main"].update(self._create_default_main())
        
        # 更新输入栏
        if self.layout is not None and self._has_region("input"):
            input_content = self.region_contents.get(LayoutRegion.INPUT)
            if input_content:
                self.layout["input"].update(input_content)
            else:
                self.layout["input"].update(self._create_default_input())
        
        # 更新工作流面板
        if self.layout is not None and self._has_region("workflow"):
            workflow_content = self.region_contents.get(LayoutRegion.WORKFLOW)
            if workflow_content:
                self.layout["workflow"].update(workflow_content)
            else:
                self.layout["workflow"].update(self._create_default_workflow())
        
        # 更新状态栏
        if self.layout is not None and self._has_region("status"):
            status_content = self.region_contents.get(LayoutRegion.STATUS)
            if status_content:
                self.layout["status"].update(status_content)
            else:
                self.layout["status"].update(self._create_default_status())
        
        # 更新导航栏
        if self.layout is not None and self._has_region("navigation"):
            navigation_content = self.region_contents.get(LayoutRegion.NAVIGATION)
            if navigation_content:
                self.layout["navigation"].update(navigation_content)
            else:
                self.layout["navigation"].update(self._create_default_navigation())
    
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
    
    def _create_default_workflow(self) -> Panel:
        """创建默认工作流面板"""
        content = Text("工作流状态面板\n\n", style="bold")
        content.append("当前节点: 未运行\n", style="dim")
        content.append("执行路径: 无历史\n", style="dim")
        content.append("状态快照: 无快照\n\n", style="dim")
        content.append("Studio: 未启动", style="dim")
        
        return Panel(
            content,
            title="工作流状态",
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
    
    def _create_default_navigation(self) -> Panel:
        """创建默认导航栏"""
        nav_text = Text()
        
        # 关键状态信息摘要
        nav_text.append("💾 会话: ", style="bold blue")
        nav_text.append("未连接 | ", style="dim")
        nav_text.append("🤖 Agent: ", style="bold cyan")
        nav_text.append("未运行 | ", style="dim")
        nav_text.append("🔄 工作流: ", style="bold yellow")
        nav_text.append("未启动 | ", style="dim")
        nav_text.append("进度: ", style="bold")
        nav_text.append("████████░░ 80% | ", style="dim")
        nav_text.append("消息: ", style="bold")
        nav_text.append("15 | Token: 2,345", style="dim")
        
        return Panel(nav_text, style="dim", border_style="dim")
    
    def update_region_content(self, region: LayoutRegion, content: Any) -> None:
        """更新区域内容"""
        # 检查内容是否真正发生变化
        old_content = self.region_contents.get(region)
        if old_content != content:
            self.region_contents[region] = content
            # 立即更新布局对象中的内容
            self._update_layout_regions_for_region(region, content)
            
            # 使用TUI静默日志记录器记录调试信息
            try:
                from .logger import get_tui_silent_logger
                logger = get_tui_silent_logger("layout")
                import hashlib
                old_hash = hashlib.md5(str(old_content).encode() if old_content else b'').hexdigest()[:8]
                new_hash = hashlib.md5(str(content).encode() if content else b'').hexdigest()[:8]
                logger.debug_render_operation("layout", f"region_{region.value}_updated", 
                                           old_hash=old_hash, new_hash=new_hash)
            except Exception:
                # 如果日志记录失败，静默忽略，避免影响TUI运行
                pass
    
    def clear_region_contents(self) -> None:
        """清除所有区域内容缓存，强制下次更新时触发渲染"""
        self.region_contents.clear()
        # 使用TUI静默日志记录器记录调试信息
        try:
            from .logger import get_tui_silent_logger
            logger = get_tui_silent_logger("layout")
            logger.debug_render_operation("layout", "clear_region_contents")
        except Exception:
            # 如果日志记录失败，静默忽略，避免影响TUI运行
            pass
    
    def _update_layout_regions_for_region(self, region: LayoutRegion, content: Any) -> None:
        """只更新指定区域的内容
         
        Args:
            region: 区域类型
            content: 区域内容
        """
        if not self.layout:
            return
        
        # 将区域枚举转换为布局名称
        region_name = region.value
        
        # 检查布局中是否存在该区域
        if not self._has_region(region_name):
            return
        
        # 更新指定区域的内容
        try:
            self.layout[region_name].update(content)
        except (KeyError, AttributeError, TypeError):
            # 如果更新失败，记录错误但不抛出异常
            pass
    
    def resize_layout(self, terminal_size: Tuple[int, int]) -> None:
        """改进的布局调整方法"""
        current_time = time.time()
        
        # 防抖处理，避免频繁调整
        if current_time - self.last_resize_time < self.resize_debounce_delay:
            return
        
        self.last_resize_time = current_time
        old_breakpoint = self.current_breakpoint
        
        # 检查断点是否变化
        new_breakpoint = self._determine_breakpoint(terminal_size)
        
        # 如果断点变化，强制重建布局
        if old_breakpoint != new_breakpoint:
            # 缓存当前内容
            self._cache_region_contents()
            
            self.terminal_size = terminal_size
            self.current_breakpoint = new_breakpoint
            self._last_breakpoint = new_breakpoint
            
            # 重建布局
            self.layout = self._create_layout_structure(new_breakpoint)
            
            # 恢复缓存的内容
            self._restore_region_contents()
            
            # 触发布局变化回调
            self._trigger_layout_changed_callbacks()
        else:
            # 检查尺寸变化是否超过阈值
            width_delta = abs(terminal_size[0] - self.terminal_size[0])
            height_delta = abs(terminal_size[1] - self.terminal_size[1])
            
            if (width_delta >= self.config.resize_threshold[0] or 
                height_delta >= self.config.resize_threshold[1]):
                
                # 缓存当前内容
                self._cache_region_contents()
                
                self.terminal_size = terminal_size
                
                # 相同断点但尺寸变化较大，只调整尺寸
                self._adjust_region_sizes_gradual()
                
                # 恢复缓存的内容
                self._restore_region_contents()
                
                # 触发布局变化回调
                self._trigger_layout_changed_callbacks()
    
    def _determine_breakpoint(self, terminal_size: Tuple[int, int]) -> str:
        """改进的断点检测，添加缓冲机制"""
        width, height = terminal_size
        
        # 使用配置中的断点设置
        breakpoints = self.config.responsive_breakpoints or {
            "xlarge": (140, 50),
            "large": (120, 40),
            "medium": (100, 30),
            "small": (80, 24)
        }
        
        # 首先找到最适合的断点（不考虑缓冲）
        target_breakpoint = None
        for breakpoint_name, (min_width, min_height) in sorted(
            breakpoints.items(),
            key=lambda x: x[1][0],  # 按宽度排序
            reverse=True
        ):
            if width >= min_width and height >= min_height:
                target_breakpoint = breakpoint_name
                break
        
        if not target_breakpoint:
            target_breakpoint = "small"
        
        # 如果没有当前断点，直接返回目标断点
        if not self.current_breakpoint:
            return target_breakpoint
        
        # 如果目标断点与当前断点相同，检查缓冲机制
        if target_breakpoint == self.current_breakpoint:
            return target_breakpoint
        
        # 如果目标断点比当前断点高（升级），直接切换
        breakpoint_order = ["small", "medium", "large", "xlarge"]
        current_index = breakpoint_order.index(self.current_breakpoint)
        target_index = breakpoint_order.index(target_breakpoint)
        
        if target_index > current_index:
            # 升级断点，直接切换
            return target_breakpoint
        else:
            # 降级断点，检查缓冲机制
            current_threshold = breakpoints.get(self.current_breakpoint)
            if current_threshold:
                # 如果仍在当前断点的缓冲范围内，保持当前断点
                if (width >= current_threshold[0] - self.breakpoint_buffer_threshold and 
                    height >= current_threshold[1] - self.breakpoint_buffer_threshold):
                    return self.current_breakpoint
                else:
                    # 超出缓冲范围，降级
                    return target_breakpoint
        
        return target_breakpoint
    
    def _adjust_region_sizes(self) -> None:
        """调整区域大小（保留原方法以兼容性）"""
        self._adjust_region_sizes_gradual()
    
    def _adjust_region_sizes_gradual(self) -> None:
        """改进的区域尺寸调整"""
        if not self.layout:
            return
        
        # 计算最优尺寸
        optimal_sizes = self._calculate_optimal_sizes()
        
        # 应用尺寸调整
        for region_name, size in optimal_sizes.items():
            if self.layout is not None and self._has_region(region_name) and size is not None:
                try:
                    self.layout[region_name].size = size
                except (KeyError, AttributeError, TypeError):
                    # 忽略无法调整的区域
                    pass
    
    def _calculate_optimal_sizes(self) -> Dict[str, Optional[int]]:
        """计算各区域最优尺寸"""
        width, height = self.terminal_size
        
        # 固定尺寸区域
        header_size = 3
        input_size = 3
        status_size = 1
        navigation_size = 2
        
        # 可用空间计算
        available_height = height - header_size - input_size - status_size - navigation_size
        
        if self.current_breakpoint in ["small", "medium"]:
            # 紧凑布局
            if self.current_breakpoint == "small":
                # 小屏幕：隐藏侧边栏
                return {
                    "header": header_size,
                    "main": available_height,
                    "input": input_size,
                    "status": status_size,
                    "navigation": navigation_size,
                    "sidebar": None,
                    "workflow": None
                }
            else:
                # 中等屏幕：侧边栏在右侧
                # 侧边栏宽度基于终端总宽度比例计算，而不是高度
                sidebar_width = self._clamp_width(
                    int(width * 0.22),  # 22% 的宽度
                    self.config.sidebar_width_range[0],
                    self.config.sidebar_width_range[1]
                )
                main_width = width - sidebar_width
                
                return {
                    "header": header_size,
                    "main": available_height,
                    "sidebar": sidebar_width,
                    "input": input_size,
                    "status": status_size,
                    "navigation": navigation_size,
                    "workflow": None
                }
        else:
            # 完整布局
            # 侧边栏宽度基于终端总宽度比例计算
            sidebar_width = self._clamp_width(
                int(width * 0.22),  # 22% 的宽度
                self.config.sidebar_width_range[0],
                self.config.sidebar_width_range[1]
            )
            
            # 检查是否需要显示工作流面板
            workflow_width = None
            if self.config.regions[LayoutRegion.WORKFLOW].visible:
                workflow_width = self._clamp_width(
                    int(width * 0.18),  # 18% 的宽度
                    self.config.workflow_width_range[0],
                    self.config.workflow_width_range[1]
                )
            
            # 主区域宽度 = 总宽 - 左右栏占用
            main_width = width - sidebar_width - (workflow_width or 0)
            
            return {
                "header": header_size,
                "sidebar": sidebar_width,
                "main": available_height,
                "workflow": workflow_width,
                "input": input_size,
                "status": status_size,
                "navigation": navigation_size
            }
    
    def _clamp_width(self, width: int, min_width: int, max_width: int) -> int:
        """限制宽度在指定范围内"""
        return max(min_width, min(width, max_width))
    
    def get_region_size(self, region: LayoutRegion) -> Tuple[int, int]:
        """获取区域尺寸"""
        if not self.layout:
            return (0, 0)
        
        region_name = region.value
        if not self._has_region(region_name):
            return (0, 0)
        
        # 获取区域的实际尺寸
        region_layout = self.layout[region_name]
        if hasattr(region_layout, 'size') and region_layout.size is not None:
            # 根据父级方向决定返回的尺寸
            parent_direction = self.region_parent_direction.get(region_name, "column")
            
            if parent_direction == "column":
                # 垂直布局：区域占据全宽，高度为设定值
                return (self.terminal_size[0], region_layout.size)
            else:
                # 水平布局：区域宽度为设定值，高度为父容器高度
                # 需要计算父容器的可用高度
                if region_name in ["sidebar", "main", "workflow"]:
                    # 这些区域在body或content中，需要减去header、input、status的高度
                    available_height = self.terminal_size[1] - 3 - 3 - 1  # header + input + status
                    return (region_layout.size, available_height)
                else:
                    return (region_layout.size, self.terminal_size[1])
        
        # 如果没有设置size，尝试从计算的最优尺寸中获取
        optimal_sizes = self._calculate_optimal_sizes()
        if region_name in optimal_sizes and optimal_sizes[region_name] is not None:
            size = optimal_sizes[region_name]
            # 确保size是int类型
            if size is None:
                size = 0
            parent_direction = self.region_parent_direction.get(region_name, "column")
            
            if parent_direction == "column":
                # 垂直布局：区域占据全宽，高度为设定值
                return (self.terminal_size[0], size)
            else:
                # 水平布局：区域宽度为设定值，高度为父容器高度
                if region_name in ["sidebar", "main", "workflow"]:
                    available_height = self.terminal_size[1] - 3 - 3 - 1  # header + input + status
                    return (size, available_height)
                else:
                    return (size, self.terminal_size[1])
        
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
    
    def set_region_visible(self, region_name: str, visible: bool) -> None:
        """设置区域可见性
        
        Args:
            region_name: 区域名称
            visible: 是否可见
        """
        try:
            region = LayoutRegion(region_name)
            self.config.regions[region].visible = visible
            
            # 如果是工作流区域且当前是大屏布局，需要重建布局
            if region == LayoutRegion.WORKFLOW and self.current_breakpoint in ["large", "xlarge"]:
                self._cache_region_contents()
                self.layout = self._create_layout_structure(self.current_breakpoint)
                self._restore_region_contents()
                self._trigger_layout_changed_callbacks()
        except ValueError:
            # 无效的区域名称
            pass
    
    def trigger_rerender(self) -> None:
        """触发重新渲染"""
        if self.layout:
            self._update_layout_regions()
    
    # 新增的优化方法
    
    def register_layout_changed_callback(self, callback: Callable[[str, Tuple[int, int]], None]) -> None:
        """注册布局变化回调
        
        Args:
            callback: 回调函数，接收断点和终端尺寸参数
        """
        self.layout_changed_callbacks.append(callback)
    
    def unregister_layout_changed_callback(self, callback: Callable[[str, Tuple[int, int]], None]) -> bool:
        """取消注册布局变化回调
        
        Args:
            callback: 要取消的回调函数
            
        Returns:
            bool: 是否成功取消
        """
        try:
            self.layout_changed_callbacks.remove(callback)
            return True
        except ValueError:
            return False
    
    def _trigger_layout_changed_callbacks(self) -> None:
        """触发布局变化回调"""
        for callback in self.layout_changed_callbacks:
            try:
                callback(self.current_breakpoint, self.terminal_size)
            except Exception as e:
                logging.warning(f"布局变化回调执行失败: {e}")
    
    def _cache_region_contents(self) -> None:
        """缓存区域内容"""
        if not self.layout:
            return
        
        for region in LayoutRegion:
            region_name = region.value
            if self.layout is not None and self._has_region(region_name):
                try:
                    # 获取当前区域内容
                    region_layout = self.layout[region_name]
                    if hasattr(region_layout, 'renderable'):
                        self.region_content_cache[region] = region_layout.renderable
                except (KeyError, AttributeError, TypeError):
                    continue
    
    def _restore_region_contents(self) -> None:
        """恢复区域内容"""
        if not self.layout:
            return
        
        for region, content in self.region_content_cache.items():
            region_name = region.value
            if self.layout is not None and self._has_region(region_name) and content:
                try:
                    self.layout[region_name].update(content)
                except (KeyError, AttributeError, TypeError):
                    continue
        
        # 清空缓存
        self.region_content_cache.clear()
    
    def _gradual_layout_transition(self, old_breakpoint: str, new_breakpoint: str) -> None:
        """渐进式布局过渡"""
        # 创建新布局结构
        self.layout = self._create_layout_structure(new_breakpoint)
        
        # 渐进式调整区域尺寸
        self._transition_region_sizes(old_breakpoint, new_breakpoint)
        
        # 渐进式调整区域可见性
        self._transition_region_visibility(old_breakpoint, new_breakpoint)
    
    def _create_layout_structure(self, breakpoint: str) -> Layout:
        """根据断点创建布局结构"""
        layout = Layout()
        
        if breakpoint in ["small", "medium"]:
            layout = self._create_compact_layout(layout)
        else:
            layout = self._create_full_layout(layout)
        
        return layout
    
    def _transition_region_sizes(self, old_breakpoint: str, new_breakpoint: str) -> None:
        """渐进式调整区域尺寸"""
        # 根据新旧断点计算过渡尺寸
        transition_sizes = self._calculate_transition_sizes(old_breakpoint, new_breakpoint)
        
        for region_name, target_size in transition_sizes.items():
            if self.layout is not None and self._has_region(region_name) and target_size is not None:
                try:
                    # 直接设置目标尺寸（简化版本，实际可以添加动画）
                    self.layout[region_name].size = target_size
                except (KeyError, AttributeError, TypeError):
                    continue
    
    def _transition_region_visibility(self, old_breakpoint: str, new_breakpoint: str) -> None:
        """渐进式调整区域可见性"""
        old_visibility = self._get_breakpoint_visibility(old_breakpoint)
        new_visibility = self._get_breakpoint_visibility(new_breakpoint)
        
        for region in LayoutRegion:
            old_visible = old_visibility.get(region, False)
            new_visible = new_visibility.get(region, False)
            
            if old_visible != new_visible:
                # 这里可以添加淡入淡出效果，目前直接切换
                pass
    
    def _calculate_transition_sizes(self, old_breakpoint: str, new_breakpoint: str) -> Dict[str, Optional[int]]:
        """计算过渡尺寸"""
        return self._calculate_optimal_sizes()
    
    def _get_breakpoint_visibility(self, breakpoint: str) -> Dict[LayoutRegion, bool]:
        """获取断点对应的区域可见性"""
        visibility = {}
        
        for region in LayoutRegion:
            if breakpoint == "small":
                # 小屏幕：显示header, main, input, status, navigation
                visibility[region] = region in [
                    LayoutRegion.HEADER, LayoutRegion.MAIN,
                    LayoutRegion.INPUT, LayoutRegion.STATUS, LayoutRegion.NAVIGATION
                ]
            elif breakpoint == "medium":
                # 中等屏幕：显示header, main, input, status, navigation
                visibility[region] = region in [
                    LayoutRegion.HEADER, LayoutRegion.MAIN,
                    LayoutRegion.INPUT, LayoutRegion.STATUS, LayoutRegion.NAVIGATION
                ]
            else:
                # 大屏幕：显示header, main, input, status, navigation
                visibility[region] = region in [
                    LayoutRegion.HEADER, LayoutRegion.MAIN,
                    LayoutRegion.INPUT, LayoutRegion.STATUS, LayoutRegion.NAVIGATION
                ]
        
        return visibility