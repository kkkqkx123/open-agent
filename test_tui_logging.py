#!/usr/bin/env python3
"""测试TUI日志功能"""

import sys
from pathlib import Path

# 将项目根目录添加到Python路径中
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_tui_logging():
    """测试TUI日志功能"""
    print("开始测试TUI日志功能...")
    
    # 设置依赖注入容器
    from src.presentation.cli.commands import setup_container
    setup_container()
    
    # 导入并初始化TUI应用
    from src.presentation.tui.app import TUIApp
    from src.presentation.tui.logger import get_tui_debug_logger
    
    print("创建TUI应用实例...")
    app = TUIApp()
    
    print("获取TUI调试日志记录器...")
    logger = get_tui_debug_logger("test")
    
    print("写入测试日志...")
    logger.info("这是一个测试信息日志")
    logger.warning("这是一个测试警告日志")
    logger.error("这是一个测试错误日志")
    logger.debug("这是一个测试调试日志")
    
    print("检查logs目录...")
    logs_dir = Path("logs")
    if logs_dir.exists():
        print(f"logs目录存在: {logs_dir.absolute()}")
        log_files = list(logs_dir.glob("*.log"))
        print(f"日志文件: {log_files}")
        
        for log_file in log_files:
            print(f"文件: {log_file.name}, 大小: {log_file.stat().st_size} 字节")
            if log_file.stat().st_size > 0:
                print("文件内容预览:")
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines[-5:]:  # 显示最后5行
                        print(f"  {line.rstrip()}")
    else:
        print("logs目录不存在")
    
    print("TUI日志功能测试完成")

if __name__ == "__main__":
    test_tui_logging()