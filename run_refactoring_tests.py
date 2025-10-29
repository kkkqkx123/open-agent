#!/usr/bin/env python3
"""重构测试运行脚本

运行所有与依赖注入重构相关的测试，包括单元测试、集成测试、性能测试和并发测试。
"""

import sys
import os
import time
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def run_command(cmd: List[str], description: str) -> Dict[str, Any]:
    """运行命令并返回结果
    
    Args:
        cmd: 要执行的命令
        description: 命令描述
        
    Returns:
        Dict[str, Any]: 执行结果
    """
    print(f"\n{'='*60}")
    print(f"运行: {description}")
    print(f"命令: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"执行时间: {duration:.2f}秒")
        print(f"返回码: {result.returncode}")
        
        if result.stdout:
            print(f"标准输出:\n{result.stdout}")
        
        if result.stderr:
            print(f"标准错误:\n{result.stderr}")
        
        return {
            'success': result.returncode == 0,
            'duration': duration,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"执行失败: {e}")
        print(f"执行时间: {duration:.2f}秒")
        
        return {
            'success': False,
            'duration': duration,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }


def run_unit_tests(verbose: bool = False) -> Dict[str, Any]:
    """运行单元测试"""
    cmd = ["python", "-m", "pytest", "tests/unit/application/sessions/test_manager.py"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "SessionManager单元测试")


def run_state_manager_tests(verbose: bool = False) -> Dict[str, Any]:
    """运行状态管理测试"""
    cmd = ["python", "-m", "pytest", "tests/unit/presentation/tui/test_state_manager.py"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "StateManager单元测试")


def run_integration_tests(verbose: bool = False) -> Dict[str, Any]:
    """运行集成测试"""
    cmd = ["python", "-m", "pytest", "tests/integration/test_di_integration.py"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "依赖注入集成测试")


def run_performance_tests(verbose: bool = False) -> Dict[str, Any]:
    """运行性能测试"""
    cmd = ["python", "-m", "pytest", "tests/performance/test_di_performance.py"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "性能基准测试")


def run_concurrency_tests(verbose: bool = False) -> Dict[str, Any]:
    """运行并发测试"""
    cmd = ["python", "-m", "pytest", "tests/performance/test_concurrency.py"]
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "并发测试")


def run_memory_optimization_demo() -> Dict[str, Any]:
    """运行内存优化演示"""
    cmd = ["python", "-c", """
import sys
sys.path.insert(0, 'src')
from infrastructure.memory_optimizer import get_global_memory_optimizer, start_memory_monitoring, optimize_memory, get_memory_report

# 启动内存监控
print("启动内存监控...")
start_memory_monitoring()

# 获取初始内存报告
print("\\n初始内存报告:")
report = get_memory_report()
print(f"进程内存使用: {report['current_stats']['process_mb']:.2f}MB")
print(f"系统内存使用率: {report['current_stats']['percent']:.1f}%")

# 创建一些对象进行测试
print("\\n创建测试对象...")
optimizer = get_global_memory_optimizer()
test_objects = []
for i in range(1000):
    obj = {"data": list(range(100)), "id": i}
    optimizer.track_object("test_objects", obj)
    test_objects.append(obj)

print(f"跟踪对象数量: {optimizer.get_tracked_objects_count()}")

# 执行内存优化
print("\\n执行内存优化...")
result = optimize_memory(aggressive=True)
print(f"释放内存: {result.freed_mb:.2f}MB")
print(f"回收对象: {result.objects_collected}")
print(f"使用策略: {', '.join(result.strategies_used)}")

# 获取最终内存报告
print("\\n最终内存报告:")
report = get_memory_report()
print(f"进程内存使用: {report['current_stats']['process_mb']:.2f}MB")
print(f"系统内存使用率: {report['current_stats']['percent']:.1f}%")

# 检测内存泄漏
issues = optimizer.detect_memory_leaks()
if issues:
    print(f"\\n检测到的问题: {issues}")
else:
    print("\\n未检测到内存问题")

print("\\n内存优化演示完成")
"""]
    
    return run_command(cmd, "内存优化演示")


def run_di_configuration_demo() -> Dict[str, Any]:
    """运行依赖注入配置演示"""
    cmd = ["python", "-c", """
import sys
import tempfile
import shutil
from pathlib import Path

sys.path.insert(0, 'src')

# 创建临时配置目录
temp_dir = tempfile.mkdtemp()
config_dir = Path(temp_dir) / "configs"
config_dir.mkdir(exist_ok=True)

# 创建配置文件
global_config = config_dir / "global.yaml"
global_config.write_text(\"\"\"
logging:
  level: INFO
secrets:
  openai_api_key: "test_key"
\"\"\")

application_config = config_dir / "application.yaml"
application_config.write_text(\"\"\"
version: "1.0"
application:
  environment: test
  config_path: "configs"
\"\"\")

try:
    from infrastructure.di_config import create_container, get_global_container, reset_global_container
    from infrastructure.lifecycle_manager import get_global_lifecycle_manager, reset_global_lifecycle_manager
    
    print("创建依赖注入容器...")
    container = create_container(
        config_path=str(config_dir),
        environment="test"
    )
    
    print("验证核心服务注册...")
    from infrastructure.config_loader import IConfigLoader
    from application.workflow.manager import IWorkflowManager
    from application.sessions.manager import ISessionManager
    
    services = [
        ("IConfigLoader", IConfigLoader),
        ("IWorkflowManager", IWorkflowManager),
        ("ISessionManager", ISessionManager)
    ]
    
    for name, service_type in services:
        if container.has_service(service_type):
            service = container.get(service_type)
            print(f"✓ {name}: {type(service).__name__}")
        else:
            print(f"✗ {name}: 未注册")
    
    print("\\n测试全局容器...")
    reset_global_container()
    global_container = get_global_container(
        config_path=str(config_dir),
        environment="test"
    )
    
    print("✓ 全局容器创建成功")
    
    print("\\n测试生命周期管理器...")
    lifecycle_manager = get_global_lifecycle_manager()
    metrics = lifecycle_manager.get_metrics()
    print(f"✓ 生命周期管理器: {metrics['total_services']} 个服务")
    
    print("\\n依赖注入配置演示完成")
    
finally:
    # 清理临时目录
    shutil.rmtree(temp_dir)
"""]
    
    return run_command(cmd, "依赖注入配置演示")


def generate_summary_report(results: List[Dict[str, Any]]) -> None:
    """生成总结报告
    
    Args:
        results: 测试结果列表
    """
    print(f"\n{'='*80}")
    print("重构测试总结报告")
    print(f"{'='*80}")
    
    total_tests = len(results)
    passed_tests = sum(1 for r in results if r['success'])
    failed_tests = total_tests - passed_tests
    total_duration = sum(r['duration'] for r in results)
    
    print(f"总测试数: {total_tests}")
    print(f"通过测试: {passed_tests}")
    print(f"失败测试: {failed_tests}")
    print(f"总执行时间: {total_duration:.2f}秒")
    print(f"成功率: {passed_tests/total_tests*100:.1f}%")
    
    print(f"\n详细结果:")
    for i, result in enumerate(results, 1):
        status = "✓ 通过" if result['success'] else "✗ 失败"
        print(f"{i}. {status} - {result['duration']:.2f}秒")
    
    if failed_tests > 0:
        print(f"\n失败的测试:")
        for i, result in enumerate(results, 1):
            if not result['success']:
                print(f"- 测试 {i}: 返回码 {result['returncode']}")
                if result['stderr']:
                    print(f"  错误: {result['stderr'][:200]}...")
    
    print(f"\n{'='*80}")
    
    if failed_tests == 0:
        print("🎉 所有测试通过！重构成功完成。")
    else:
        print("⚠️  部分测试失败，请检查相关代码。")
    
    print(f"{'='*80}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="运行依赖注入重构测试")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")
    parser.add_argument("--unit-only", action="store_true", help="只运行单元测试")
    parser.add_argument("--performance-only", action="store_true", help="只运行性能测试")
    parser.add_argument("--demo-only", action="store_true", help="只运行演示")
    parser.add_argument("--no-demo", action="store_true", help="不运行演示")
    
    args = parser.parse_args()
    
    print("依赖注入重构测试套件")
    print("=" * 80)
    
    results = []
    
    if args.demo_only:
        # 只运行演示
        results.append(run_di_configuration_demo(args.verbose))
        results.append(run_memory_optimization_demo())
    else:
        # 运行测试
        if not args.performance_only:
            # 单元测试
            results.append(run_unit_tests(args.verbose))
            results.append(run_state_manager_tests(args.verbose))
            
            # 集成测试
            results.append(run_integration_tests(args.verbose))
        
        # 性能和并发测试
        results.append(run_performance_tests(args.verbose))
        results.append(run_concurrency_tests(args.verbose))
        
        # 演示
        if not args.no_demo:
            results.append(run_di_configuration_demo(args.verbose))
            results.append(run_memory_optimization_demo())
    
    # 生成总结报告
    generate_summary_report(results)
    
    # 返回适当的退出码
    failed_tests = sum(1 for r in results if not r['success'])
    return 1 if failed_tests > 0 else 0


if __name__ == "__main__":
    sys.exit(main())