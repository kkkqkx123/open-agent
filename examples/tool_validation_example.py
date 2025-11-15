"""
工具检验模块使用示例
展示如何使用工具检验模块验证工具配置和加载
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.container import get_global_container
from src.infrastructure.tools.validation.manager import ToolValidationManager
from infrastructure.config.loader.file_config_loader import IConfigLoader
from src.infrastructure.logger.logger import ILogger
from src.infrastructure.tools.manager import IToolManager


def validate_single_tool():
    """验证单个工具"""
    print("开始验证单个工具...")
    
    # 创建依赖容器
    container = get_global_container()
    
    # 获取服务
    config_loader = container.get(IConfigLoader)
    logger = container.get(ILogger)
    tool_manager = container.get(IToolManager)
    
    # 创建检验管理器
    validation_manager = ToolValidationManager(config_loader, logger, tool_manager)
    
    # 验证Hash转换工具
    results = validation_manager.validate_tool(
        "hash_convert", 
        "configs/tools/hash_convert.yaml"
    )
    
    # 生成报告
    report = validation_manager.generate_report(
        {"hash_convert": results}, 
        format="text"
    )
    print(report)
    
    return results


def validate_all_tools():
    """验证所有工具"""
    print("\n开始验证所有工具...")
    
    container = get_global_container()
    config_loader = container.get(IConfigLoader)
    logger = container.get(ILogger)
    tool_manager = container.get(IToolManager)
    
    # 创建检验管理器
    validation_manager = ToolValidationManager(config_loader, logger, tool_manager)
    
    # 验证所有工具
    all_results = validation_manager.validate_all_tools()
    
    # 生成详细报告
    report = validation_manager.generate_report(all_results, format="text")
    print(report)
    
    # 生成JSON报告
    json_report = validation_manager.generate_report(all_results, format="json")
    print("\nJSON格式报告:")
    print(json_report)
    
    return all_results


def check_validation_results(all_results):
    """检查验证结果"""
    print("\n验证结果统计:")
    
    total_tools = len(all_results)
    successful_tools = 0
    error_count = 0
    
    for tool_name, tool_results in all_results.items():
        tool_successful = True
        for stage, result in tool_results.items():
            if not result.is_successful():
                tool_successful = False
                error_count += len(result.issues)
        
        if tool_successful:
            successful_tools += 1
    
    print(f"  总工具数: {total_tools}")
    print(f"  成功工具: {successful_tools}")
    print(f"  失败工具: {total_tools - successful_tools}")
    print(f"  总错误数: {error_count}")
    
    if total_tools == successful_tools:
        print("✓ 所有工具验证通过")
        return True
    else:
        print(f"✗ 有 {total_tools - successful_tools} 个工具验证失败")
        return False


if __name__ == "__main__":
    print("工具检验模块使用示例")
    print("=" * 50)
    
    try:
        # 验证单个工具
        single_results = validate_single_tool()
        
        # 验证所有工具
        all_results = validate_all_tools()
        
        # 检查结果
        success = check_validation_results(all_results)
        
        # 根据结果退出
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"执行工具检验时出错: {e}")
        sys.exit(1)