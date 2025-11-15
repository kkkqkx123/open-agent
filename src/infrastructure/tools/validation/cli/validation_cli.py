"""
工具检验模块命令行接口
提供命令行工具来验证工具配置和加载
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from src.infrastructure.container import get_global_container
from src.infrastructure.di_config import DIConfig
from src.infrastructure.tools.validation.manager import ToolValidationManager


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="工具检验工具")
    parser.add_argument(
        "--tool",
        help="要验证的特定工具名称"
    )
    parser.add_argument(
        "--config-dir",
        default="configs/tools",
        help="工具配置目录路径"
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="输出格式"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出模式"
    )
    
    args = parser.parse_args()
    
    try:
        # 获取全局依赖容器并配置核心服务
        container = get_global_container()
        di_config = DIConfig(container)
        di_config.configure_core_services()
        
        # 获取服务
        from infrastructure.config.loader.file_config_loader import IConfigLoader
        from src.infrastructure.logger.logger import Logger
        from src.infrastructure.tools.interfaces import IToolManager
        
        config_loader = container.get(IConfigLoader)
        logger = Logger("ToolValidation")
        tool_manager = container.get(IToolManager)
        
        # 创建检验管理器
        validation_manager = ToolValidationManager(config_loader, logger, tool_manager)
        
        # 执行验证
        if args.tool:
            # 验证单个工具
            config_path = f"{args.tool}.yaml"
            results = validation_manager.validate_tool(args.tool, config_path)
            all_results = {args.tool: results}
        else:
            # 验证所有工具
            # 确保config_dir是相对于配置加载器base_path的路径
            config_dir = args.config_dir
            if config_dir.startswith("configs/"):
                config_dir = config_dir[8:]  # 移除"configs/"前缀（8个字符）
            all_results = validation_manager.validate_all_tools(config_dir)
        
        # 生成报告
        report = validation_manager.generate_report(all_results, args.format)
        print(report)
        
        # 检查是否有错误
        has_errors = False
        for tool_results in all_results.values():
            for result in tool_results.values():
                if not result.is_successful():
                    has_errors = True
                    break
            if has_errors:
                break
        
        # 如果有错误且不是JSON格式，返回非零退出码
        if has_errors and args.format != "json":
            sys.exit(1)
            
    except Exception as e:
        print(f"执行工具检验时出错: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()