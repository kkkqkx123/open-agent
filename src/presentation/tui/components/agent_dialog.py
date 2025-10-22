"""Agent选择对话框组件

包含Agent配置选择、预览和管理功能
"""

from typing import Optional, Dict, Any, List, Callable
from pathlib import Path
import yaml

from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.columns import Columns
from rich.align import Align
from rich.console import Console, ConsoleOptions, RenderResult
from rich.tree import Tree
from rich.markdown import Markdown

from ..config import TUIConfig


class AgentConfigItem:
    """Agent配置项"""
    
    def __init__(self, config_path: str, config_data: Dict[str, Any]):
        self.config_path = config_path
        self.config_data = config_data
        self.name = config_data.get("name", Path(config_path).stem)
        self.description = config_data.get("description", "无描述")
        # 使用llm字段而不是model字段，符合AgentConfig模型
        self.model = config_data.get("llm", config_data.get("model", "未知模型"))
        self.tools = config_data.get("tools", [])
        self.tool_sets = config_data.get("tool_sets", [])
        self.system_prompt = config_data.get("system_prompt", "")
        self.rules = config_data.get("rules", [])
        self.user_command = config_data.get("user_command", "")
        self.capabilities = config_data.get("capabilities", [])
    
    def get_summary(self) -> str:
        """获取配置摘要
        
        Returns:
            str: 配置摘要
        """
        tool_count = len(self.get_tool_list())
        tool_set_count = len(self.tool_sets) if self.tool_sets else 0
        tool_info = f"{tool_count} 工具"
        if tool_set_count > 0:
            tool_info += f", {tool_set_count} 工具集"
        return f"{self.name} - {self.model} ({tool_info})"
    
    def get_tool_list(self) -> List[str]:
        """获取工具列表
        
        Returns:
            List[str]: 工具列表
        """
        if isinstance(self.tools, list):
            return self.tools
        elif isinstance(self.tools, dict):
            return list(self.tools.keys())
        return []
    
    def get_capability_list(self) -> List[str]:
        """获取能力列表
        
        Returns:
            List[str]: 能力列表
        """
        if isinstance(self.capabilities, list):
            return self.capabilities
        return []


class AgentListSection:
    """Agent列表组件"""
    
    def __init__(self) -> None:
        self.agents: List[AgentConfigItem] = []
        self.selected_index = 0
        self.filter_text = ""
        self.sort_by = "name"  # name, model, tools
    
    def update_agents(self, agents: List[AgentConfigItem]) -> None:
        """更新Agent列表
        
        Args:
            agents: Agent配置列表
        """
        self.agents = agents
        self._apply_filter_and_sort()
    
    def set_filter(self, filter_text: str) -> None:
        """设置过滤条件
        
        Args:
            filter_text: 过滤文本
        """
        self.filter_text = filter_text.lower()
        self._apply_filter_and_sort()
    
    def _apply_filter_and_sort(self) -> None:
        """应用过滤和排序"""
        # 过滤
        if self.filter_text:
            filtered_agents = []
            for agent in self.agents:
                if (self.filter_text in agent.name.lower() or 
                    self.filter_text in agent.description.lower() or
                    self.filter_text in agent.model.lower()):
                    filtered_agents.append(agent)
            self.agents = filtered_agents
        
        # 排序
        if self.sort_by == "name":
            self.agents.sort(key=lambda x: x.name)
        elif self.sort_by == "model":
            self.agents.sort(key=lambda x: x.model)
        elif self.sort_by == "tools":
            self.agents.sort(key=lambda x: len(x.get_tool_list()), reverse=True)
    
    def navigate_up(self) -> None:
        """向上导航"""
        if self.selected_index > 0:
            self.selected_index -= 1
    
    def navigate_down(self) -> None:
        """向下导航"""
        if self.selected_index < len(self.agents) - 1:
            self.selected_index += 1
    
    def get_selected_agent(self) -> Optional[AgentConfigItem]:
        """获取选中的Agent
        
        Returns:
            Optional[AgentConfigItem]: 选中的Agent配置
        """
        if 0 <= self.selected_index < len(self.agents):
            return self.agents[self.selected_index]
        return None
    
    def render(self) -> Table:
        """渲染Agent列表
        
        Returns:
            Table: Agent列表表格
        """
        table = Table(
            title="Agent配置列表",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        
        # 添加列
        table.add_column("名称", style="green")
        table.add_column("模型", style="yellow")
        table.add_column("工具数", style="cyan", width=6)
        table.add_column("能力数", style="magenta", width=6)
        table.add_column("描述", style="white")
        
        # 添加行
        for i, agent in enumerate(self.agents):
            tool_count = len(agent.get_tool_list())
            capability_count = len(agent.get_capability_list())
            description = agent.description[:30] + "..." if len(agent.description) > 30 else agent.description
            
            # 选中行高亮
            row_style = "bold reverse" if i == self.selected_index else ""
            
            table.add_row(
                agent.name,
                agent.model,
                str(tool_count),
                str(capability_count),
                description,
                style=row_style
            )
        
        return table


class AgentDetailSection:
    """Agent详情组件"""
    
    def __init__(self) -> None:
        self.current_agent: Optional[AgentConfigItem] = None
    
    def update_agent(self, agent: Optional[AgentConfigItem]) -> None:
        """更新当前Agent
        
        Args:
            agent: Agent配置
        """
        self.current_agent = agent
    
    def render(self) -> Panel:
        """渲染Agent详情
        
        Returns:
            Panel: Agent详情面板
        """
        if not self.current_agent:
            content = Text("请选择一个Agent配置", style="dim")
            return Panel(content, title="Agent详情", border_style="gray")
        
        # 创建详情树
        tree = Tree("🤖 Agent详情", style="bold cyan")
        
        # 基本信息
        basic_info = tree.add("📋 基本信息")
        basic_info.add(f"名称: {self.current_agent.name}")
        basic_info.add(f"模型: {self.current_agent.model}")
        basic_info.add(f"配置文件: {self.current_agent.config_path}")
        
        # 描述
        desc_info = tree.add("📝 描述")
        desc_info.add(self.current_agent.description)
        
        # 工具信息
        tools = self.current_agent.get_tool_list()
        if tools:
            tools_info = tree.add("🔧 可用工具")
            for tool in tools[:10]:  # 最多显示10个工具
                tools_info.add(f"• {tool}")
            if len(tools) > 10:
                tools_info.add(f"... 还有 {len(tools) - 10} 个工具")
        else:
            tree.add("🔧 无可用工具")
        
        # 能力信息
        capabilities = self.current_agent.get_capability_list()
        if capabilities:
            cap_info = tree.add("⚡ 能力")
            for capability in capabilities:
                cap_info.add(f"• {capability}")
        
        # 系统提示词（截断显示）
        if self.current_agent.system_prompt:
            prompt_info = tree.add("💭 系统提示词")
            prompt_preview = self.current_agent.system_prompt[:200]
            if len(self.current_agent.system_prompt) > 200:
                prompt_preview += "..."
            prompt_info.add(prompt_preview)
        
        return Panel(
            tree,
            title=f"Agent详情 - {self.current_agent.name}",
            border_style="green"
        )


class AgentSelectDialog:
    """Agent选择对话框
    
    包含Agent列表、详情预览和选择功能
    """
    
    def __init__(self, config: Optional[TUIConfig] = None):
        self.config = config
        self.current_mode = "select"  # select, confirm
        self.agent_list = AgentListSection()
        self.agent_detail = AgentDetailSection()
        self.selected_agent: Optional[AgentConfigItem] = None
        
        # 回调函数
        self.on_agent_selected: Optional[Callable[[AgentConfigItem], None]] = None
    
    def set_agent_selected_callback(self, callback: Callable[[AgentConfigItem], None]) -> None:
        """设置Agent选择回调
        
        Args:
            callback: 回调函数
        """
        self.on_agent_selected = callback
    
    def load_agent_configs(self, config_dir: str = "configs/agents") -> None:
        """加载Agent配置
        
        Args:
            config_dir: 配置目录
        """
        agents = []
        config_path = Path(config_dir)
        
        if not config_path.exists():
            # 如果目录不存在，创建默认配置
            config_path.mkdir(parents=True, exist_ok=True)
            self._create_default_configs(config_path)
        
        # 加载所有YAML配置文件（排除_group.yaml）
        for yaml_file in config_path.glob("*.yaml"):
            # 跳过组配置文件
            if yaml_file.name.startswith("_group"):
                continue
                
            try:
                with open(yaml_file, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                    if config_data:
                        agent_item = AgentConfigItem(str(yaml_file), config_data)
                        agents.append(agent_item)
            except Exception as e:
                print(f"加载配置文件失败 {yaml_file}: {e}")
        
        self.agent_list.update_agents(agents)
        
        # 更新详情显示
        selected = self.agent_list.get_selected_agent()
        self.agent_detail.update_agent(selected)
    
    def _create_default_configs(self, config_dir: Path) -> None:
        """创建默认配置文件
        
        Args:
            config_dir: 配置目录
        """
        # 默认Agent配置 - 符合AgentConfig模型
        default_config = {
            "name": "默认Agent",
            "llm": "gpt-3.5-turbo",
            "group": "default_group",
            "tools": ["calculator", "weather"],
            "system_prompt": "你是一个有用的AI助手，能够回答问题并使用工具。",
            "description": "基础的对话Agent，具备基本的问题回答能力",
            "max_iterations": 10,
            "timeout": 60,
            "retry_count": 3
        }
        
        default_file = config_dir / "default.yaml"
        with open(default_file, 'w', encoding='utf-8') as f:
            yaml.dump(default_config, f, default_flow_style=False, allow_unicode=True)
        
        # 高级Agent配置 - 符合AgentConfig模型
        advanced_config = {
            "name": "高级Agent",
            "llm": "gpt-4",
            "group": "code_group",
            "tools": ["calculator", "weather", "database", "web_search"],
            "system_prompt": "你是一个高级AI助手，具备强大的问题解决能力和工具使用技能。",
            "description": "功能强大的Agent，支持多种工具和复杂任务处理",
            "max_iterations": 15,
            "timeout": 120,
            "retry_count": 5
        }
        
        advanced_file = config_dir / "advanced.yaml"
        with open(advanced_file, 'w', encoding='utf-8') as f:
            yaml.dump(advanced_config, f, default_flow_style=False, allow_unicode=True)
    
    def handle_key(self, key: str) -> Optional[str]:
        """处理按键输入
        
        Args:
            key: 按键
            
        Returns:
            Optional[str]: 操作结果
        """
        if self.current_mode == "select":
            return self._handle_select_mode_key(key)
        elif self.current_mode == "confirm":
            return self._handle_confirm_mode_key(key)
        
        return None
    
    def _handle_select_mode_key(self, key: str) -> Optional[str]:
        """处理选择模式按键"""
        if key == "up":
            self.agent_list.navigate_up()
            selected = self.agent_list.get_selected_agent()
            self.agent_detail.update_agent(selected)
        elif key == "down":
            self.agent_list.navigate_down()
            selected = self.agent_list.get_selected_agent()
            self.agent_detail.update_agent(selected)
        elif key == "enter":
            selected = self.agent_list.get_selected_agent()
            if selected:
                self.selected_agent = selected
                self.current_mode = "confirm"
        elif key == "escape":
            return "CLOSE_DIALOG"
        elif key.startswith("char:"):
            # 字符输入用于过滤
            char = key[5:]
            if char.isalnum() or char.isspace():
                # 这里可以实现实时过滤功能
                pass
        
        return None
    
    def _handle_confirm_mode_key(self, key: str) -> Optional[str]:
        """处理确认模式按键"""
        if key == "y":
            if self.selected_agent and self.on_agent_selected:
                self.on_agent_selected(self.selected_agent)
                return "AGENT_SELECTED"
        elif key == "n" or key == "escape":
            self.current_mode = "select"
        
        return None
    
    def render(self) -> Panel:
        """渲染对话框
        
        Returns:
            Panel: 对话框面板
        """
        if self.current_mode == "select":
            # 创建左右分栏布局
            list_panel = self.agent_list.render()
            detail_panel = self.agent_detail.render()
            
            content: Any = Columns([list_panel, detail_panel], equal=True)
            title = "选择Agent (方向键=选择, Enter=确认, Esc=关闭)"
        elif self.current_mode == "confirm":
            if self.selected_agent:
                content = Text(
                    f"确定选择Agent: {self.selected_agent.name}?\\n\\n"
                    f"模型: {self.selected_agent.model}\\n"
                    f"描述: {self.selected_agent.description}\\n\\n"
                    f"按 Y 确认，按 N 取消",
                    style="yellow"
                )
                title = "确认选择"
            else:
                content = Text("无Agent可确认", style="red")
                title = "错误"
        else:
            content = Text("未知模式", style="red")
            title = "错误"
        
        return Panel(
            content,
            title=title,
            border_style="blue",
            padding=(1, 1)
        )