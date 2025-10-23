#!/usr/bin/env python3
"""实际运行TUI界面来验证修复效果"""

import os
import sys
from pathlib import Path

# 设置环境变量启用调试
os.environ["TUI_DEBUG"] = "1"

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """主函数"""
    print("启动TUI界面测试...")
    print("请按以下步骤测试:")
    print("1. 在输入区域输入一些文本")
    print("2. 按回车键提交")
    print("3. 检查主内容区是否显示了您的输入")
    print("4. 检查是否收到了助手的回复")
    print("5. 按ESC键退出")
    print("\n如果输入和回复都正常显示，说明修复成功！")
    print("\n按任意键启动TUI界面...")
    input()
    
    try:
        from presentation.tui.app import TUIApp
        app = TUIApp()
        app.run()
    except KeyboardInterrupt:
        print("\nTUI界面已退出")
    except Exception as e:
        print(f"\n运行TUI界面时发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()