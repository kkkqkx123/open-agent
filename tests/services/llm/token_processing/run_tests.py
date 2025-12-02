#!/usr/bin/env python3
"""Token处理模块测试运行器

运行所有token_processing模块的测试并生成报告。
"""

import sys
import os
import subprocess
from pathlib import Path


def run_tests():
    """运行所有测试"""
    # 获取当前目录
    current_dir = Path(__file__).parent
    
    # 设置Python路径
    project_root = current_dir.parent.parent.parent.parent
    sys.path.insert(0, str(project_root))
    
    print("=" * 60)
    print("Token处理模块测试运行器")
    print("=" * 60)
    print(f"项目根目录: {project_root}")
    print(f"测试目录: {current_dir}")
    print()
    
    # 运行测试
    try:
        # 运行单元测试
        print("运行单元测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_token_types.py",
            "test_base_implementation.py",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=current_dir, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        unit_success = result.returncode == 0
        
        # 运行混合处理器测试
        print("\n运行混合处理器测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_hybrid_processor.py",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=current_dir, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        hybrid_success = result.returncode == 0
        
        # 运行对话跟踪器测试
        print("\n运行对话跟踪器测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_conversation_tracker.py",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=current_dir, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        tracker_success = result.returncode == 0
        
        # 运行集成测试
        print("\n运行集成测试...")
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "test_integration.py",
            "-v",
            "--tb=short",
            "--color=yes"
        ], cwd=current_dir, capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("错误输出:")
            print(result.stderr)
        
        integration_success = result.returncode == 0
        
        # 生成测试报告
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)
        print(f"TokenUsage测试: {'✓ 通过' if unit_success else '✗ 失败'}")
        print(f"基础实现测试: {'✓ 通过' if unit_success else '✗ 失败'}")
        print(f"混合处理器测试: {'✓ 通过' if hybrid_success else '✗ 失败'}")
        print(f"对话跟踪器测试: {'✓ 通过' if tracker_success else '✗ 失败'}")
        print(f"集成测试: {'✓ 通过' if integration_success else '✗ 失败'}")
        
        all_success = all([unit_success, hybrid_success, tracker_success, integration_success])
        
        print(f"\n总体结果: {'✓ 所有测试通过' if all_success else '✗ 部分测试失败'}")
        
        if all_success:
            print("\n🎉 恭喜！所有测试都通过了！")
            print("Token处理模块实现正确，可以安全使用。")
        else:
            print("\n❌ 有测试失败，请检查上述输出。")
            print("需要修复失败的测试后才能安全使用。")
        
        return 0 if all_success else 1
        
    except Exception as e:
        print(f"运行测试时发生错误: {e}")
        return 1


def run_coverage():
    """运行测试并生成覆盖率报告"""
    current_dir = Path(__file__).parent
    
    print("运行测试并生成覆盖率报告...")
    
    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "--cov=src/services/llm/token_processing",
            "--cov-report=html",
            "--cov-report=term-missing",
            "--cov-fail-under=80",
            "-v"
        ], cwd=current_dir)
        
        return result.returncode
        
    except Exception as e:
        print(f"运行覆盖率测试时发生错误: {e}")
        return 1


def main():
    """主函数"""
    if len(sys.argv) > 1 and sys.argv[1] == "--coverage":
        return run_coverage()
    else:
        return run_tests()


if __name__ == "__main__":
    sys.exit(main())