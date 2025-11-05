# TUI模块Agent到Workflow重构方案

## 概述

当前TUI模块仍然包含与已移除agent层相关的组件和功能。本方案详细说明如何将这些agent相关代码重构为基于workflow的实现，使TUI与项目当前架构保持一致。

## 当前问题分析

### 1. 仍存在的Agent相关组件

- **AgentSelectDialog**: Agent选择对话框组件
- **AgentConfigItem**: Agent配置项类
- **AgentListSection**: Agent列表组件
- **AgentDetailSection**: Agent详情组件
- **AgentInfo**: Agent信息类（在SidebarComponent中）

### 2. 仍存在的Agent相关配置

- `configs/agents/default.yaml`
- `configs/agents/advanced.yaml`
- TUI仍在加载`configs/agents/`目录下的配置文件

### 3. 仍存在的Agent相关状态管理

- `StateManager.set_show_agent_dialog()`
- `StateManager.show_agent_dialog`属性
- `SidebarComponent.AgentInfo`相关显示

### 4. 仍存在的Agent相关命令

- `/agents`命令用于打开Agent选择对话框
- 帮助文档中仍显示agent相关命令

## 重构目标

将所有agent相关功能替换为workflow相关功能：

1. **Agent选择 → Workflow选择**：用户选择workflow而不是agent
2. **Agent配置 → Workflow配置**：使用workflow配置文件替代agent配置
3. **Agent信息 → Workflow信息**：侧边栏显示workflow信息而不是agent信息

## Workflow配置结构分析

基于现有workflow配置文件分析，workflow包含以下关键信息：

```yaml
# react_workflow.yaml 示例
metadata:
  name: "react_workflow"
  version: "1.1.0"
  description: "ReAct模式工作流"
  author: "system"

workflow_name: "react_workflow"
description: "ReAct模式工作流，支持思考-行动-观察循环"

max_iterations: 20
timeout: 600

nodes:
  # 各种节点配置...

edges:
  # 边配置...

entry_point: "start_node"
```

## 详细重构方案

### 1. 创建Workflow选择组件

#### 1.1 WorkflowConfigItem类
```python
# src/presentation/tui/components/workflow_dialog.py

class WorkflowConfigItem:
    """Workflow配置项"""
    
    def __init__(self, config_path: str, config_data: Dict[str, Any]):
        self.config_path = config_path
        self.config_data = config_data
        self.name = config_data.get("workflow_name", config_data.get("name", Path(config_path).stem))
        self.description = config_data.get("description", "无描述")
        self.version = config_data.get("metadata", {}).get("version", "未知版本")
        self.author = config_data.get("metadata", {}).get("author", "未知作者")
        self.max_iterations = config_data.get("max_iterations", 10)
        self.timeout = config_data.get("timeout", 300)
        self.entry_point = config_data.get("entry_point", "start_node")
        
        # 节点和边信息
        self.nodes = config_data.get("nodes", {})
        self.edges = config_data.get("edges", [])
    
    def get_summary(self) -> str:
        """获取配置摘要"""
        node_count = len(self.nodes) if isinstance(self.nodes, dict) else 0
        edge_count = len(self.edges) if isinstance(self.edges, list) else 0
        return f"{self.name} v{self.version} ({node_count} 节点, {edge_count} 边)"
```

#### 1.2 WorkflowListSection类
```python
class WorkflowListSection:
    """Workflow列表组件"""
    
    def __init__(self):
        self.workflows: List[WorkflowConfigItem] = []
        self.selected_index = 0
        self.filter_text = ""
        self.sort_by = "name"  # name, version, nodes
    
    # 类似于AgentListSection的实现，但针对workflow
```

#### 1.3 WorkflowDetailSection类
```python
class WorkflowDetailSection:
    """Workflow详情组件"""
    
    def __init__(self):
        self.current_workflow: Optional[WorkflowConfigItem] = None
    
    def render(self) -> Panel:
        """渲染workflow详情"""
        if not self.current_workflow:
            content = Text("请选择一个Workflow配置", style="dim")
            return Panel(content, title="Workflow详情", border_style="gray")
        
        # 创建详情树
        tree = Tree("⚙️ Workflow详情", style="bold cyan")
        
        # 基本信息
        basic_info = tree.add("📋 基本信息")
        basic_info.add(f"名称: {self.current_workflow.name}")
        basic_info.add(f"版本: {self.current_workflow.version}")
        basic_info.add(f"作者: {self.current_workflow.author}")
        basic_info.add(f"描述: {self.current_workflow.description}")
        basic_info.add(f"配置文件: {self.current_workflow.config_path}")
        
        # 配置信息
        config_info = tree.add("⚙️ 配置参数")
        config_info.add(f"最大迭代: {self.current_workflow.max_iterations}")
        config_info.add(f"超时时间: {self.current_workflow.timeout}s")
        config_info.add(f"入口点: {self.current_workflow.entry_point}")
        
        # 结构信息
        structure_info = tree.add("🏗️ 结构信息")
        node_count = len(self.current_workflow.nodes) if isinstance(self.current_workflow.nodes, dict) else 0
        edge_count = len(self.current_workflow.edges) if isinstance(self.current_workflow.edges, list) else 0
        structure_info.add(f"节点数: {node_count}")
        structure_info.add(f"边数: {edge_count}")
        
        return Panel(tree, title=f"Workflow详情 - {self.current_workflow.name}", border_style="green")
```

#### 1.4 WorkflowSelectDialog类
```python
class WorkflowSelectDialog:
    """Workflow选择对话框"""
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.current_mode = "select"  # select, confirm
        self.workflow_list = WorkflowListSection()
        self.workflow_detail = WorkflowDetailSection()
        self.selected_workflow: Optional[WorkflowConfigItem] = None
        
        # 回调函数
        self.on_workflow_selected: Optional[Callable[[WorkflowConfigItem], None]] = None
    
    def load_workflow_configs(self, config_dir: str = "configs/workflows") -> None:
        """加载Workflow配置"""
        workflows = []
        config_path = Path(config_dir)
        
        # 加载所有YAML配置文件（排除_group.yaml）
        for yaml_file in config_path.glob("*.yaml"):
            if yaml_file.name.startswith("_group"):
                continue
                
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        workflow_item = WorkflowConfigItem(str(yaml_file), config_data)
                        workflows.append(workflow_item)
            except Exception as e:
                print(f"加载配置文件失败 {yaml_file}: {e}")
        
        self.workflow_list.update_workflows(workflows)
        
        # 更新详情显示
        selected = self.workflow_list.get_selected_workflow()
        self.workflow_detail.update_workflow(selected)
    
    def render(self) -> Panel:
        """渲染对话框"""
        if self.current_mode == "select":
            list_panel = self.workflow_list.render()
            detail_panel = self.workflow_detail.render()
            content = Columns([list_panel, detail_panel], equal=True)
            title = "选择Workflow (方向键=选择, Enter=确认, Esc=关闭)"
        elif self.current_mode == "confirm":
            if self.selected_workflow:
                content = Text(
                    f"确定选择Workflow: {self.selected_workflow.name}?\\n\\n"
                    f"版本: {self.selected_workflow.version}\\n"
                    f"描述: {self.selected_workflow.description}\\n"
                    f"节点数: {len(self.selected_workflow.nodes) if self.selected_workflow.nodes else 0}\\n\\n"
                    f"按 Y 确认，按 N 取消",
                    style="yellow"
                )
                title = "确认选择"
            else:
                content = Text("无Workflow可确认", style="red")
                title = "错误"
        
        return Panel(content, title=title, border_style="blue", padding=(1, 1))
```

### 2. 更新状态管理

#### 2.1 StateManager修改
```python
class StateManager:
    def __init__(self, session_manager: Optional[ISessionManager] = None):
        # ... 现有代码 ...
        
        # UI状态
        self._show_session_dialog = False
        self._show_workflow_dialog = False  # 替换 _show_agent_dialog
        self.current_subview: Optional[str] = None
        
        # ... 现有代码 ...
    
    def set_show_workflow_dialog(self, show: bool = True) -> None:
        """显示/隐藏Workflow对话框"""
        self._show_workflow_dialog = show
    
    @property
    def show_workflow_dialog(self) -> bool:
        """获取Workflow对话框显示状态"""
        return self._show_workflow_dialog
    
    # 移除agent相关方法
    # def set_show_agent_dialog(self, show: bool = True) -> None:  # 删除
    # @property
    # def show_agent_dialog(self) -> bool:  # 删除
```

### 3. 更新侧边栏组件

#### 3.1 SidebarComponent修改
```python
class WorkflowInfo:
    """Workflow信息类"""
    
    def __init__(self):
        self.name = "未选择Workflow"
        self.version = "未知版本"
        self.status = "未加载"
        self.nodes = 0
        self.edges = 0
        self.max_iterations = 10
        self.timeout = 300
    
    def update_workflow_info(self, name: str, version: str, nodes: int = 0, 
                          edges: int = 0, status: str = "未加载", 
                          max_iterations: int = 10, timeout: int = 300) -> None:
        """更新Workflow信息"""
        self.name = name
        self.version = version
        self.nodes = nodes
        self.edges = edges
        self.status = status
        self.max_iterations = max_iterations
        self.timeout = timeout
    
    def __getitem__(self, key: str) -> Any:
        return getattr(self, key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        setattr(self, key, value)


class SidebarComponent:
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        
        # Workflow基本信息（替换AgentInfo）
        self.workflow_info = WorkflowInfo()
        
        # 会话信息（保持不变）
        self.session_info = {
            "session_id": None,
            "workflow_config": "",
            "status": "未连接",
            "created_time": None
        }
        
        # 工作流状态（保持不变，但现在指workflow的执行状态）
        self.workflow_status = {
            "name": "未加载",
            "state": "停止",
            "progress": 0
        }
        
        # 核心指标（保持不变）
        self.core_metrics = {
            "messages": 0,
            "tokens": 0,
            "cost": 0.0,
            "duration": "0:00"
        }
    
    def update_workflow_info(self, name: str, version: str, status: str = "就绪") -> None:
        """更新Workflow信息"""
        self.workflow_info["name"] = name
        self.workflow_info["version"] = version
        self.workflow_info["status"] = status
    
    def render(self) -> Panel:
        """渲染精简侧边栏"""
        content = self._create_content()
        return Panel(content, title="📊 状态概览", border_style="green")
    
    def _create_content(self) -> Table:
        """创建内容表格"""
        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column("属性", style="bold", width=12)
        table.add_column("值", style="dim")
        
        # 会话信息（保持不变）
        if self.session_info["session_id"]:
            table.add_row("", "", style="bold blue")
            table.add_row("💾 会话", self.session_info["session_id"][:8] + "...", style="bold blue")
            table.add_row("状态", self._get_session_status_text(self.session_info["status"]))
            if self.session_info["workflow_config"]:
                workflow_name = self.session_info["workflow_config"].split('/')[-1]
                table.add_row("工作流", workflow_name)
        
        # Workflow基本信息（替换Agent信息）
        table.add_row("", "", style="bold cyan")
        table.add_row("⚙️ Workflow", self.workflow_info["name"], style="bold cyan")
        table.add_row("版本", self.workflow_info["version"])
        table.add_row("状态", self._get_status_text(self.workflow_info["status"]))
        
        # 工作流执行状态（保持不变）
        table.add_row("", "", style="bold yellow")
        table.add_row("🔄 执行状态", self.workflow_status["name"], style="bold yellow")
        table.add_row("状态", self._get_workflow_state_text(self.workflow_status["state"]))
        
        # 进度条（保持不变）
        if self.workflow_status["progress"] > 0:
            progress_bar = self._create_progress_bar(self.workflow_status["progress"])
            table.add_row("进度", progress_bar)
        
        # 核心指标（保持不变）
        table.add_row("", "", style="bold magenta")
        table.add_row("📈 指标", "", style="bold magenta")
        table.add_row("消息", str(self.core_metrics["messages"]))
        table.add_row("Token", str(self.core_metrics["tokens"]))
        table.add_row("成本", f"${self.core_metrics['cost']:.4f}")
        table.add_row("时长", self.core_metrics["duration"])
        
        return table
```

### 4. 更新TUI应用主文件

#### 4.1 TUIApp修改
```python
class TUIApp:
    def __init__(self, config_path: Optional[Path] = None):
        # ... 现有初始化代码 ...
        
        # 替换agent对话框为workflow对话框
        self.workflow_dialog = WorkflowSelectDialog(self.config)
        # 移除 self.agent_dialog = AgentSelectDialog(self.config)
        
        # 更新组件字典
        self.components = {
            "sidebar": self.sidebar_component,
            "langgraph": self.langgraph_component,
            "main_content": self.main_content_component,
            "input": self.input_component,
            "workflow_control": self.workflow_control_panel,
            "error_feedback": self.error_feedback_panel,
            "config_reload": self.config_reload_panel,
            "session_dialog": self.session_dialog,
            "workflow_dialog": self.workflow_dialog,  # 替换 agent_dialog
            "navigation": self.navigation_component
        }
        
        # ... 现有代码 ...
    
    def _setup_callbacks(self):
        """设置回调函数"""
        # ... 现有回调设置 ...
        
        # 设置Workflow对话框回调（替换Agent对话框）
        self.workflow_dialog.set_workflow_selected_callback(self._on_workflow_selected)
        # 移除 self.agent_dialog.set_agent_selected_callback(self._on_agent_selected)
        
        # ... 现有代码 ...
    
    def _register_global_shortcuts(self):
        """注册全局快捷键"""
        # ... 现有快捷键 ...
        # 保持其他快捷键不变
        
        # 暂时保留Alt+6作为workflow快捷键，或者可以重新分配
        self.event_engine.register_key_handler(KEY_ALT_6, lambda _: self._switch_to_subview("status_overview"))
    
    def _handle_global_key(self, key: Key) -> bool:
        """处理全局按键"""
        # ... ESC键和其他按键处理 ...
        
        # 处理workflow对话框中的按键（替换agent对话框）
        if self.state_manager.show_workflow_dialog:
            self.tui_logger.debug_key_event(key.to_string(), True, "workflow_dialog")
            result = self.workflow_dialog.handle_key(key.to_string())
            return result is not None
        
        # 移除agent对话框处理
        # elif self.state_manager.show_agent_dialog:
        #     ...
        
        # ... 现有代码 ...
    
    def _handle_escape_key(self, key: Key) -> bool:
        """处理ESC键"""
        # ... 现有ESC处理逻辑 ...
        
        elif self.state_manager.show_workflow_dialog:
            self.state_manager.set_show_workflow_dialog(False)
            self.tui_logger.debug_component_event("escape", "close_workflow_dialog")
            return True
        
        # 移除agent对话框的ESC处理
        # elif self.state_manager.show_agent_dialog:
        #     ...
        
        # ... 现有代码 ...
    
    def _handle_command(self, command: str, args: List[str]) -> None:
        """处理命令"""
        # ... 现有命令处理 ...
        
        elif command == "workflows":
            self.state_manager.set_show_workflow_dialog(True)
            self.state_manager.add_system_message("已打开Workflow选择对话框")
            self.tui_logger.debug_component_event("command", "open_workflows_dialog")
        
        # 移除agent命令
        # elif command == "agents":
        #     self.state_manager.set_show_agent_dialog(True)
        #     ...
        
        # ... 现有代码 ...
    
    def _on_workflow_selected(self, workflow_config: WorkflowConfigItem) -> None:
        """Workflow选择回调（替换agent选择回调）"""
        try:
            # 更新侧边栏的Workflow信息
            self.sidebar_component.update_workflow_info(
                name=workflow_config.name,
                version=workflow_config.version,
                status="就绪"
            )
            
            self.state_manager.set_show_workflow_dialog(False)
            self.state_manager.add_system_message(f"已选择Workflow: {workflow_config.name}")
            
            # 可以在这里加载workflow配置到当前会话
            # self.state_manager.current_workflow = workflow_config
            
        except Exception as e:
            self.state_manager.add_system_message(f"选择Workflow失败: {e}")
    
    # 移除agent选择回调
    # def _on_agent_selected(self, agent_config: Any) -> None:
    #     ...
```

### 5. 更新命令处理器

#### 5.1 CommandProcessor修改
```python
class CommandProcessor:
    def _register_default_commands(self) -> None:
        """注册默认命令"""
        # ... 现有命令 ...
        
        # 保持其他命令不变，agent相关命令将被workflow命令替换
    
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
  /workflows - 打开Workflow选择  # 替换 /agents
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
```

### 6. 更新组件导入

#### 6.1 components模块更新
```python
# src/presentation/tui/components/__init__.py

# 移除agent相关导入
# from .agent_dialog import AgentSelectDialog, AgentConfigItem

# 添加workflow相关导入
from .workflow_dialog import WorkflowSelectDialog, WorkflowConfigItem

# 更新__all__列表
__all__ = [
    "SidebarComponent",
    "LangGraphPanelComponent", 
    "MainContentComponent",
    "UnifiedMainContentComponent",
    "InputPanel",
    "SessionManagerDialog",
    # "AgentSelectDialog",  # 移除
    "WorkflowSelectDialog",  # 添加
    "WorkflowControlPanel",
    "ErrorFeedbackPanel", 
    "ConfigReloadPanel",
    "NavigationBarComponent"
]
```

### 7. 更新应用初始化

#### 7.1 app.py导入更新
```python
# src/presentation/tui/app.py

from .components import (
    SidebarComponent,
    LangGraphPanelComponent,
    MainContentComponent,
    UnifiedMainContentComponent,
    InputPanel,
    SessionManagerDialog,
    # AgentSelectDialog,  # 移除
    WorkflowSelectDialog,  # 添加
    WorkflowControlPanel,
    ErrorFeedbackPanel,
    ConfigReloadPanel,
    NavigationBarComponent
)
```

### 8. 清理配置文件

#### 8.1 移除agent配置目录
```bash
# 可选：移除agent配置目录（如果确定不再需要）
# rm -rf configs/agents/

# 或者保留但标记为废弃
# echo "# 此目录已废弃，请使用 configs/workflows/ 中的workflow配置" > configs/agents/DEPRECATED.md
```

## 实施步骤

### 第一阶段：创建新组件
1. 创建`WorkflowConfigItem`、`WorkflowListSection`、`WorkflowDetailSection`类
2. 创建`WorkflowSelectDialog`类
3. 创建`WorkflowInfo`类

### 第二阶段：更新状态管理
1. 修改`StateManager`，移除agent相关属性和方法
2. 添加workflow相关属性和方法

### 第三阶段：更新UI组件
1. 修改`SidebarComponent`，替换AgentInfo为WorkflowInfo
2. 更新组件导入和初始化

### 第四阶段：更新应用逻辑
1. 修改`TUIApp`，替换AgentSelectDialog为WorkflowSelectDialog
2. 更新回调和事件处理逻辑
3. 更新命令处理器

### 第五阶段：清理和测试
1. 移除agent相关文件和配置
2. 更新帮助文档
3. 进行全面测试

## 兼容性考虑

### 1. 向后兼容
- 保持现有会话管理功能不变
- 保持其他UI组件功能不变
- 保持大部分快捷键不变

### 2. 配置迁移
- 如果需要，可以创建配置迁移工具
- 将agent配置中的有用信息（如系统提示词）迁移到workflow配置中

### 3. 用户体验
- 保持相似的操作流程
- 提供清晰的过渡说明
- 确保功能完整性

## 测试计划

### 1. 单元测试
- 测试所有新创建的组件类
- 测试状态管理器的修改
- 测试命令处理器的更新

### 2. 集成测试
- 测试workflow选择对话框的完整流程
- 测试侧边栏信息显示
- 测试命令处理和快捷键

### 3. 用户测试
- 测试完整的用户工作流程
- 验证所有功能正常工作
- 收集用户反馈

## 风险评估

### 1. 高风险
- 配置文件结构变化可能影响现有功能
- 状态管理修改可能引入新的bug

### 2. 中风险
- UI显示变化可能需要用户适应
- 快捷键重新分配可能影响用户习惯

### 3. 低风险
- 文档更新不及时
- 部分边缘情况处理不完善

## 总结

通过这个重构方案，TUI模块将完全移除对已移除agent层的依赖，转而使用workflow作为核心概念。这不仅保持了架构的一致性，还为用户提供了更强大的workflow选择和管理功能。重构后的TUI将更好地支持项目的多workflow架构，提供更灵活和强大的用户体验。