"""
GraphWorkflow 端到端测试运行器

运行所有 GraphWorkflow 集成测试并生成报告。
"""

import sys
import pytest
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_integration_tests():
    """运行所有集成测试"""
    print("🚀 GraphWorkflow 集成测试启动")
    print("=" * 60)
    
    # 测试文件列表
    test_files = [
        "tests/integration/test_graph_workflow_integration.py",
        "tests/integration/test_graph_workflow_config.py", 
        "tests/integration/test_graph_workflow_execution.py"
    ]
    
    # 检查测试文件是否存在
    missing_files = []
    for test_file in test_files:
        if not Path(test_file).exists():
            missing_files.append(test_file)
    
    if missing_files:
        print(f"❌ 缺少测试文件: {missing_files}")
        return False
    
    # 运行测试
    start_time = datetime.now()
    
    try:
        # 配置 pytest 参数
        pytest_args = [
            "-v",  # 详细输出
            "--tb=short",  # 简短错误跟踪
            "--color=yes",  # 彩色输出
            "--durations=10",  # 显示最慢的10个测试
            "--html=reports/graph_workflow_integration_tests.html",  # HTML报告
            "--self-contained-html",  # 自包含HTML报告
        ] + test_files
        
        print(f"📋 运行测试文件:")
        for test_file in test_files:
            print(f"   - {test_file}")
        print()
        
        # 运行测试
        result = pytest.main(pytest_args)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n" + "=" * 60)
        print(f"⏱️  测试耗时: {duration:.2f} 秒")
        
        if result == 0:
            print("✅ 所有测试通过!")
            return True
        else:
            print(f"❌ 测试失败 (退出码: {result})")
            return False
            
    except Exception as e:
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n❌ 测试运行失败: {e}")
        print(f"⏱️  运行时间: {duration:.2f} 秒")
        return False


def run_specific_test(test_name):
    """运行特定测试"""
    print(f"🎯 运行特定测试: {test_name}")
    print("=" * 60)
    
    try:
        # 查找包含指定测试的测试文件
        test_files = [
            "tests/integration/test_graph_workflow_integration.py",
            "tests/integration/test_graph_workflow_config.py",
            "tests/integration/test_graph_workflow_execution.py"
        ]
        
        # 运行特定测试
        pytest_args = [
            "-v",
            "--tb=short",
            "--color=yes",
            "-k", test_name  # 只运行匹配的测试
        ] + test_files
        
        result = pytest.main(pytest_args)
        
        if result == 0:
            print(f"✅ 测试 '{test_name}' 通过!")
            return True
        else:
            print(f"❌ 测试 '{test_name}' 失败")
            return False
            
    except Exception as e:
        print(f"❌ 运行测试失败: {e}")
        return False


def generate_test_report():
    """生成测试报告"""
    report_dir = Path("reports")
    report_dir.mkdir(exist_ok=True)
    
    # 运行测试并生成报告
    print("📊 生成测试报告...")
    
    pytest_args = [
        "tests/integration/",
        "--html=reports/graph_workflow_complete_report.html",
        "--self-contained-html",
        "--json=reports/graph_workflow_test_results.json",
        "--cov=src/application/workflow/",  # 覆盖率报告
        "--cov-report=html:reports/coverage",
        "--cov-report=term-missing",
        "-v"
    ]
    
    try:
        result = pytest.main(pytest_args)
        
        print(f"📄 报告已生成:")
        print(f"   - HTML报告: reports/graph_workflow_complete_report.html")
        print(f"   - JSON结果: reports/graph_workflow_test_results.json")
        print(f"   - 覆盖率报告: reports/coverage/index.html")
        
        return result == 0
        
    except Exception as e:
        print(f"❌ 生成报告失败: {e}")
        return False


def check_test_environment():
    """检查测试环境"""
    print("🔍 检查测试环境...")
    
    # 检查必要的模块
    required_modules = [
        "pytest",
        "pytest-html",
        "pytest-cov",
        "pytest-asyncio"
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module.replace("-", "_"))
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print(f"⚠️  缺少依赖模块: {missing_modules}")
        print("   请运行: pip install " + " ".join(missing_modules))
        return False
    
    # 检查测试文件
    test_dir = Path("tests/integration")
    if not test_dir.exists():
        print(f"❌ 测试目录不存在: {test_dir}")
        return False
    
    test_files = list(test_dir.glob("test_*.py"))
    if not test_files:
        print(f"❌ 未找到测试文件在: {test_dir}")
        return False
    
    print(f"✅ 环境检查通过，找到 {len(test_files)} 个测试文件")
    return True


def main():
    """主函数"""
    print("🧪 GraphWorkflow 端到端测试系统")
    print("=" * 60)
    
    # 检查环境
    if not check_test_environment():
        print("❌ 环境检查失败，请修复后重试")
        sys.exit(1)
    
    # 解析命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "run":
            # 运行所有测试
            success = run_integration_tests()
            sys.exit(0 if success else 1)
            
        elif command == "report":
            # 生成完整报告
            success = generate_test_report()
            sys.exit(0 if success else 1)
            
        elif command == "specific":
            # 运行特定测试
            if len(sys.argv) > 2:
                test_name = sys.argv[2]
                success = run_specific_test(test_name)
                sys.exit(0 if success else 1)
            else:
                print("❌ 请指定测试名称")
                print("用法: python test_runner.py specific <test_name>")
                sys.exit(1)
                
        elif command == "help":
            print_help()
            
        else:
            print(f"❌ 未知命令: {command}")
            print_help()
            sys.exit(1)
    else:
        # 默认运行所有测试
        success = run_integration_tests()
        sys.exit(0 if success else 1)


def print_help():
    """打印帮助信息"""
    print("""
GraphWorkflow 端到端测试系统

用法:
    python test_runner.py [命令] [参数]

命令:
    run         - 运行所有集成测试
    report      - 生成完整测试报告（包含覆盖率）
    specific    - 运行特定测试（需要测试名称）
    help        - 显示此帮助信息

示例:
    python test_runner.py run
    python test_runner.py report
    python test_runner.py specific test_create_workflow_from_dict
    python test_runner.py help

测试文件:
    tests/integration/test_graph_workflow_integration.py
    tests/integration/test_graph_workflow_config.py
    tests/integration/test_graph_workflow_execution.py

输出:
    控制台输出测试进度和结果
    reports/ 目录下生成 HTML 和 JSON 报告
""")


if __name__ == "__main__":
    main()