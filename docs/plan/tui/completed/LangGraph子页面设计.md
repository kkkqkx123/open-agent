# LangGraph子页面设计文档

## 功能概述

LangGraph子页面将提供完整的LangGraph工作流调试和监控功能，取代当前在主界面右侧显示的LangGraph面板。用户可以通过快捷键Alt+6快速访问此页面。

## 界面设计

### 布局结构
```
┌─────────────────────────────────────────────────────────────┐
│             模块化代理框架 - LangGraph调试                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┬─────────────────────────────────────┐  │
│  │   当前节点      │           执行路径                  │  │
│  │                 │                                     │  │
│  │  ▶️ 思考节点    │  📍 输入处理                       │  │
│  │  运行中 (2.3s)  │  📍 工具调用                       │  │
│  │                 │  📍 思考节点 (当前)                │  │
│  │  输入: {...}    │  📍 输出生成                       │  │
│  │  输出: 等待中   │                                     │  │
│  └─────────────────┴─────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   状态快照                              │  │
│  │                                                         │  │
│  │  {                                                     │  │
│  │    "messages": [...],                                  │  │
│  │    "current_step": "thinking",                         │  │
│  │    "iteration": 3                                      │  │
│  │  }                                                     │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────────────────────────────────────────────────┐  │
│  │                   节点详情                              │  │
│  │                                                         │  │
│  │  节点: thinking                                        │  │
│  │  状态: 运行中                                          │  │
│  │  开始时间: 14:30:25                                    │  │
│  │  运行时长: 2.3s                                        │  │
│  │  输入参数: {query: "Hello"}                            │  │
│  │  输出结果: 等待中                                      │  │
│  │  元数据: {attempts: 1, tokens: 150}                   │  │
│  └─────────────────────────────────────────────────────────┘  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 组件设计

### 1. LangGraphSubview类

```python
# src/presentation/tui/subviews/langgraph.py
class LangGraphSubview(BaseSubview):
    """LangGraph调试子界面"""
    
    def __init__(self, config: TUIConfig):
        super().__init__(config)
        
        # 当前节点数据
        self.current_node_data = {
            "name": "未运行",
            "status": "idle",
            "start_time": None,
            "duration": 0.0,
            "input": {},
            "output": None,
            "metadata": {}
        }
        
        # 执行路径
        self.execution_path: List[Dict[str, Any]] = []
        
        # 状态快照
        self.state_snapshot: Dict[str, Any] = {}
        
        # 节点详情
        self.node_details: Dict[str, Any] = {}
        
        # 可视化设置
        self.visualization_settings = {
            "show_input": True,
            "show_output": True,
            "show_metadata": True,
            "auto_refresh": True,
            "refresh_interval": 1.0
        }
    
    def get_title(self) -> str:
        """获取子界面标题"""
        return "🔍 LangGraph调试"
    
    def render(self) -> Panel:
        """渲染LangGraph界面"""
        # 创建主要内容区域
        content = self._create_main_content()
        
        return Panel(
            content,
            title=self.create_header(),
            border_style="cyan",
            subtitle=self.create_help_text()
        )
    
    def _create_main_content(self) -> Layout:
        """创建主要内容"""
        from rich.layout import Layout
        
        layout = Layout()
        
        # 第一行：当前节点和执行路径
        top_row = Layout()
        top_row.split_row(
            Layout(self._create_current_node_panel(), size=30),
            Layout(self._create_execution_path_panel())
        )
        
        # 第二行：状态快照和节点详情
        bottom_row = Layout()
        bottom_row.split_row(
            Layout(self._create_snapshot_panel()),
            Layout(self._create_node_details_panel(), size=35)
        )
        
        # 垂直组合
        layout.split_column(
            Layout(top_row),
            Layout(bottom_row)
        )
        
        return layout
    
    def _create_current_node_panel(self) -> Panel:
        """创建当前节点面板"""
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("当前节点", style="bold")
        table.add_column("状态", justify="center")
        
        node = self.current_node_data
        
        # 状态指示器
        status_indicators = {
            "idle": ("⏸️", "dim"),
            "running": ("▶️", "green"),
            "completed": ("✅", "blue"),
            "error": ("❌", "red"),
            "paused": ("⏸️", "yellow")
        }
        
        indicator, color = status_indicators.get(node["status"], ("❓", "white"))
        
        table.add_row(
            Text(node["name"], style=f"bold {color}"),
            Text(f"{indicator} {node['status']}", style=color)
        )
        
        # 运行时间
        if node["status"] == "running" and node["duration"] > 0:
            table.add_row("运行时间", f"{node['duration']:.1f}s")
        
        # 输入数据
        if self.visualization_settings["show_input"] and node["input"]:
            input_preview = self._preview_data(node["input"])
            table.add_row("输入", input_preview)
        
        # 输出数据
        if self.visualization_settings["show_output"] and node["output"] is not None:
            output_preview = self._preview_data(node["output"])
            table.add_row("输出", output_preview)
        
        return Panel(
            table,
            title="🎯 当前节点",
            border_style="green"
        )
    
    def _create_execution_path_panel(self) -> Panel:
        """创建执行路径面板"""
        tree = Tree("📋 执行路径")
        
        for i, step in enumerate(self.execution_path):
            node_name = step.get("node", "未知节点")
            status = step.get("status", "completed")
            duration = step.get("duration", 0.0)
            
            # 状态样式
            status_styles = {
                "completed": ("✅", "green"),
                "running": ("▶️", "yellow"),
                "error": ("❌", "red"),
                "pending": ("⏳", "dim")
            }
            
            indicator, color = status_styles.get(status, ("❓", "white"))
            
            # 创建节点文本
            node_text = Text()
            node_text.append(f"{indicator} ", style=color)
            node_text.append(node_name, style="bold")
            
            if duration > 0:
                node_text.append(f" ({duration:.1f}s)", style="dim")
            
            # 标记当前节点
            if i == len(self.execution_path) - 1 and status == "running":
                node_text.append(" [当前]", style="bold yellow")
            
            tree.add(node_text)
        
        return Panel(
            tree,
            title="🔄 执行路径",
            border_style="blue"
        )
    
    def _create_snapshot_panel(self) -> Panel:
        """创建状态快照面板"""
        from rich.syntax import Syntax
        
        # 格式化状态快照
        snapshot_json = json.dumps(self.state_snapshot, indent=2, ensure_ascii=False)
        syntax = Syntax(
            snapshot_json,
            "json",
            theme="monokai",
            line_numbers=True,
            word_wrap=True
        )
        
        return Panel(
            syntax,
            title="📊 状态快照",
            border_style="magenta"
        )
    
    def _create_node_details_panel(self) -> Panel:
        """创建节点详情面板"""
        table = Table(show_header=False, box=None)
        table.add_column("属性", style="bold", width=12)
        table.add_column("值", style="dim")
        
        node = self.current_node_data
        
        table.add_row("节点", node["name"])
        table.add_row("状态", self._get_status_text(node["status"]))
        
        if node["start_time"]:
            start_time = node["start_time"].strftime("%H:%M:%S")
            table.add_row("开始时间", start_time)
        
        if node["duration"] > 0:
            table.add_row("运行时长", f"{node['duration']:.1f}s")
        
        # 输入参数
        if node["input"]:
            input_count = len(node["input"])
            table.add_row("输入参数", f"{input_count} 个参数")
        
        # 输出结果
        if node["output"] is not None:
            output_type = type(node["output"]).__name__
            table.add_row("输出类型", output_type)
        
        # 元数据
        if node["metadata"]:
            meta_count = len(node["metadata"])
            table.add_row("元数据", f"{meta_count} 项")
        
        return Panel(
            table,
            title="📋 节点详情",
            border_style="yellow"
        )
    
    def _preview_data(self, data: Any, max_length: int = 50) -> str:
        """预览数据，限制长度"""
        data_str = str(data)
        if len(data_str) > max_length:
            return data_str[:max_length] + "..."
        return data_str
    
    def _get_status_text(self, status: str) -> Text:
        """获取状态文本"""
        status_colors = {
            "idle": "dim",
            "running": "green",
            "completed": "blue",
            "error": "red",
            "paused": "yellow"
        }
        color = status_colors.get(status, "white")
        return Text(status, style=color)
    
    def update_current_node(self, node_data: Dict[str, Any]) -> None:
        """更新当前节点数据"""
        self.current_node_data.update(node_data)
    
    def add_execution_step(self, step: Dict[str, Any]) -> None:
        """添加执行步骤"""
        self.execution_path.append(step)
        # 限制执行路径长度，避免内存溢出
        if len(self.execution_path) > 100:
            self.execution_path = self.execution_path[-50:]
    
    def update_state_snapshot(self, snapshot: Dict[str, Any]) -> None:
        """更新状态快照"""
        self.state_snapshot = snapshot
    
    def clear_execution_path(self) -> None:
        """清空执行路径"""
        self.execution_path = []
    
    def handle_key(self, key: str) -> bool:
        """处理键盘输入"""
        if key == "escape":
            return True
        
        # 切换显示设置
        if key == "i":
            self.visualization_settings["show_input"] = not self.visualization_settings["show_input"]
            return True
        
        if key == "o":
            self.visualization_settings["show_output"] = not self.visualization_settings["show_output"]
            return True
        
        if key == "m":
            self.visualization_settings["show_metadata"] = not self.visualization_settings["show_metadata"]
            return True
        
        if key == "r":
            self.visualization_settings["auto_refresh"] = not self.visualization_settings["auto_refresh"]
            return True
        
        if key == "c":
            self.clear_execution_path()
            return True
        
        return super().handle_key(key)
    
    def create_help_text(self) -> str:
        """创建帮助文本"""
        return "快捷键: [i]输入 [o]输出 [m]元数据 [r]自动刷新 [c]清空路径 [ESC]返回"
```

## 数据集成

### 1. 与现有组件集成

```python
# 在渲染控制器中集成
class RenderController:
    def _update_subviews_data(self, state_manager: Any) -> None:
        """更新子界面数据"""
        # ... 其他子界面更新
        
        # 更新LangGraph子界面数据
        if self.langgraph_view and state_manager.current_state:
            # 获取当前节点信息
            current_node = getattr(state_manager.current_state, 'current_step', '未运行')
            node_status = "running" if state_manager.current_state.iteration_count < state_manager.current_state.max_iterations else "idle"
            
            # 更新当前节点数据
            node_data = {
                "name": current_node,
                "status": node_status,
                "start_time": getattr(state_manager.current_state, 'start_time', None),
                "duration": getattr(state_manager.current_state, 'current_step_duration', 0.0),
                "input": getattr(state_manager.current_state, 'current_input', {}),
                "output": getattr(state_manager.current_state, 'current_output', None),
                "metadata": getattr(state_manager.current_state, 'current_metadata', {})
            }
            self.langgraph_view.update_current_node(node_data)
            
            # 更新执行路径
            execution_history = getattr(state_manager.current_state, 'execution_history', [])
            if execution_history:
                latest_step = execution_history[-1]
                self.langgraph_view.add_execution_step(latest_step)
            
            # 更新状态快照
            state_snapshot = {
                "messages": getattr(state_manager.current_state, 'messages', []),
                "current_step": current_node,
                "iteration": getattr(state_manager.current_state, 'iteration_count', 0),
                "max_iterations": getattr(state_manager.current_state, 'max_iterations', 10),
                "tools": getattr(state_manager.current_state, 'available_tools', [])
            }
            self.langgraph_view.update_state_snapshot(state_snapshot)
```

### 2. 快捷键注册

```python
# 在状态管理器中注册快捷键
# Alt+6: 切换到LangGraph子页面
```

## 性能优化

### 1. 数据更新策略
- **增量更新**：只更新变化的数据
- **节流更新**：限制更新频率，避免频繁渲染
- **选择性渲染**：根据设置决定显示哪些数据

### 2. 内存管理
- **执行路径限制**：最多保留100个步骤
- **状态快照压缩**：只保留必要字段
- **数据清理**：定期清理过期数据

## 用户体验优化

### 1. 实时更新
- 工作流执行时自动刷新显示
- 支持手动刷新和自动刷新模式

### 2. 交互功能
- 快捷键切换显示选项
- 执行路径可清空
- 状态快照可折叠/展开

### 3. 视觉反馈
- 颜色编码的状态指示
- 进度和时长显示
- 错误状态高亮

## 测试策略

### 1. 单元测试
- 测试各个面板的渲染逻辑
- 测试数据更新和状态管理
- 测试快捷键处理

### 2. 集成测试
- 测试与渲染控制器的集成
- 测试与状态管理器的数据同步
- 测试布局适配性

### 3. 性能测试
- 测试大数据量下的渲染性能
- 测试内存使用情况
- 测试响应时间

此设计提供了完整的LangGraph调试功能，同时保持了界面的清晰和易用性。