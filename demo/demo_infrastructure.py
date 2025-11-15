#!/usr/bin/env python3
"""
基础架构演示脚本

展示依赖注入容器、配置加载、环境检查和架构检查的功能。
"""

import os
import sys
from pathlib import Path

# 添加src目录到Python路径
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from src.infrastructure import (
    DependencyContainer,
    FileConfigLoader,
    EnvironmentChecker,
    ArchitectureChecker,
    EnvironmentCheckCommand
)


def demo_dependency_container() -> None:
    """演示依赖注入容器"""
    print("\n=== 依赖注入容器演示 ===")
    
    # 创建容器
    container = DependencyContainer()
    
    # 定义测试接口和实现
    class IService:
        def get_name(self) -> str:
            return ""
    
    class TestService(IService):
        def get_name(self) -> str:
            return "TestService"
    
    # 注册服务
    container.register(IService, TestService)
    
    # 获取服务
    service = container.get(IService)
    print(f"获取的服务: {service.get_name()}")
    
    # 演示多环境支持
    class DevService(IService):
        def get_name(self) -> str:
            return "DevService"
    
    class ProdService(IService):
        def get_name(self) -> str:
            return "ProdService"
    
    container.register(IService, DevService, "development")
    container.register(IService, ProdService, "production")
    
    container.set_environment("development")
    dev_service = container.get(IService)
    print(f"开发环境服务: {dev_service.get_name()}")
    
    container.set_environment("production")
    prod_service = container.get(IService)
    print(f"生产环境服务: {prod_service.get_name()}")


def demo_config_loader() -> None:
    """演示配置加载器"""
    print("\n=== 配置加载器演示 ===")
    
    # 设置环境变量
    os.environ["DEMO_API_KEY"] = "demo_key_123"
    
    try:
        # 创建配置加载器
        loader = FileConfigLoader("configs")
        
        # 加载全局配置
        global_config = loader.load("global.yaml")
        print(f"日志级别: {global_config['log_level']}")
        print(f"环境: {global_config['env']}")
        print(f"调试模式: {global_config['debug']}")
        
        # 加载LLM组配置
        llm_config = loader.load("llms/_group.yaml")
        print(f"OpenAI组URL: {llm_config['openai_group']['base_url']}")
        
        # 演示环境变量解析
        demo_config = {
            "api_key": "${DEMO_API_KEY}",
            "timeout": "${DEMO_TIMEOUT:30}"
        }
        resolved = loader.resolve_env_vars(demo_config)
        print(f"解析的API密钥: {resolved['api_key']}")
        print(f"解析的超时: {resolved['timeout']}")
    
    finally:
        # 清理环境变量
        if "DEMO_API_KEY" in os.environ:
            del os.environ["DEMO_API_KEY"]


def demo_environment_checker() -> None:
    """演示环境检查器"""
    print("\n=== 环境检查器演示 ===")
    
    # 创建环境检查器
    checker = EnvironmentChecker()
    
    # 检查Python版本
    python_result = checker.check_python_version()
    print(f"Python版本检查: {python_result.status} - {python_result.message}")
    
    # 检查必需包
    package_results = checker.check_required_packages()
    for result in package_results[:3]:  # 只显示前3个
        print(f"包检查 {result.component}: {result.status}")
    
    # 生成报告
    report = checker.generate_report()
    print(f"\n环境检查汇总:")
    print(f"  总计: {report['summary']['total']}")
    print(f"  通过: {report['summary']['pass']}")
    print(f"  警告: {report['summary']['warning']}")
    print(f"  错误: {report['summary']['error']}")


def demo_architecture_checker() -> None:
    """演示架构检查器"""
    print("\n=== 架构检查器演示 ===")
    
    # 创建架构检查器
    checker = ArchitectureChecker("src")
    
    # 检查架构
    results = checker.check_architecture()
    
    for result in results:
        print(f"架构检查 {result.component}: {result.status} - {result.message}")
    
    # 生成依赖图
    graph = checker.generate_dependency_graph()
    print(f"\n检测到的层级: {list(graph['layers'].keys())}")


def demo_environment_command() -> None:
    """演示环境检查命令"""
    print("\n=== 环境检查命令演示 ===")
    
    # 创建环境检查命令
    checker = EnvironmentChecker()
    command = EnvironmentCheckCommand(checker)
    
    try:
        # 运行检查（表格格式）
        command.run(format_type="table")
    except SystemExit:
        print("环境检查完成（可能有警告或错误）")


def main() -> None:
    """主演示函数"""
    print("基础架构与环境配置演示")
    print("=" * 50)
    
    try:
        demo_dependency_container()
        demo_config_loader()
        demo_environment_checker()
        demo_architecture_checker()
        demo_environment_command()
        
        print("\n" + "=" * 50)
        print("演示完成！")
        
    except Exception as e:
        print(f"\n演示过程中出现错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()