"""简单的TUI组件测试脚本"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

try:
    from rich.console import Console
    from presentation.tui.components import (
        SidebarComponent,
        LangGraphPanelComponent,
        MainContentComponent,
        InputPanelComponent
    )
    from presentation.tui.config import get_tui_config
    from prompts.agent_state import AgentState, HumanMessage, ToolResult
    
    console = Console()
    
    console.print("[bold green]开始测试TUI组件[/bold green]")
    
    # 获取配置
    config = get_tui_config()
    
    # 创建组件
    sidebar = SidebarComponent(config)
    langgraph = LangGraphPanelComponent(config)
    main_content = MainContentComponent(config)
    input_panel = InputPanelComponent(config)
    
    # 创建测试状态
    state = AgentState()
    state.add_message(HumanMessage(content="测试消息"))
    state.tool_results.append(ToolResult(
        tool_name="test_tool",
        success=True,
        result="测试结果"
    ))
    state.current_step = "test_step"
    state.iteration_count = 1
    state.max_iterations = 5
    
    # 更新组件
    sidebar.update_from_state(state)
    langgraph.update_from_state(state, "test_step", "running")
    main_content.update_from_state(state)
    
    # 渲染组件
    console.print("\n[bold cyan]侧边栏组件:[/bold cyan]")
    console.print(sidebar.render())
    
    console.print("\n[bold cyan]LangGraph面板组件:[/bold cyan]")
    console.print(langgraph.render())
    
    console.print("\n[bold cyan]主内容区组件:[/bold cyan]")
    console.print(main_content.render())
    
    console.print("\n[bold cyan]输入面板组件:[/bold cyan]")
    console.print(input_panel.render())
    
    console.print("\n[bold green]✅ 所有组件测试成功![/bold green]")
    
except ImportError as e:
    # 如果导入失败，使用print而不是console
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    # 其他异常，尝试导入Console，如果失败则使用print
    try:
        from rich.console import Console
        console = Console()
        console.print(f"\n[bold red]❌ 测试失败: {e}[/bold red]")
        import traceback
        console.print(traceback.format_exc())
    except ImportError:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()