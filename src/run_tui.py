"""TUI应用程序入口点"""

import sys
from pathlib import Path

# 将项目根目录添加到Python路径中
project_root = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(project_root))

# 设置依赖注入容器
from src.adapters.cli.commands import setup_container
setup_container()

# 导入并运行TUI应用
from src.adapters.tui.app import TUIApp

def main():
    """主函数"""
    app = TUIApp()
    app.run()

if __name__ == "__main__":
    main()