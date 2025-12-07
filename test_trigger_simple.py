#!/usr/bin/env python3
"""简单测试触发器迁移

只测试我们迁移的模块，避免其他依赖问题。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_impl_imports():
    """测试实现模块导入"""
    try:
        # 直接导入实现类
        from src.core.workflow.graph.extensions.trigger_functions.impl.time_impl import TimeTriggerImplementation
        from src.core.workflow.graph.extensions.trigger_functions.impl.state_impl import StateTriggerImplementation
        from src.core.workflow.graph.extensions.trigger_functions.impl.event_impl import EventTriggerImplementation
        from src.core.workflow.graph.extensions.trigger_functions.impl.tool_error_impl import ToolErrorTriggerImplementation
        from src.core.workflow.graph.extensions.trigger_functions.impl.iteration_impl import IterationLimitTriggerImplementation
        
        print("✓ 实现类导入成功")
        return True
    except ImportError as e:
        print(f"✗ 实现类导入失败: {e}")
        return False

def test_builtin_functions():
    """测试内置函数"""
    try:
        from src.core.workflow.graph.extensions.trigger_functions.builtin import BuiltinTriggerFunctions
        
        # 创建模拟状态和上下文
        state = {
            "messages": [],
            "tool_results": [],
            "iteration_count": 5
        }
        context = {
            "trigger_config": {
                "max_iterations": 10
            }
        }
        
        # 测试迭代限制触发器函数
        result = BuiltinTriggerFunctions.iteration_limit_evaluate(state, context)
        assert result == False, "迭代限制评估应该返回 False"
        
        # 修改迭代次数
        state["iteration_count"] = 15
        result = BuiltinTriggerFunctions.iteration_limit_evaluate(state, context)
        assert result == True, "迭代限制评估应该返回 True"
        
        print("✓ 内置函数测试通过")
        return True
    except Exception as e:
        print(f"✗ 内置函数测试失败: {e}")
        return False

def test_implementation_classes():
    """测试实现类"""
    try:
        from src.core.workflow.graph.extensions.trigger_functions.impl.iteration_impl import IterationLimitTriggerImplementation
        
        # 创建模拟状态和上下文
        state = {
            "messages": [],
            "tool_results": [],
            "iteration_count": 5
        }
        context = {
            "trigger_config": {
                "max_iterations": 10
            }
        }
        
        # 测试评估
        result = IterationLimitTriggerImplementation.evaluate(state, context)
        assert result == False, "实现类评估应该返回 False"
        
        # 修改迭代次数
        state["iteration_count"] = 15
        result = IterationLimitTriggerImplementation.evaluate(state, context)
        assert result == True, "实现类评估应该返回 True"
        
        print("✓ 实现类测试通过")
        return True
    except Exception as e:
        print(f"✗ 实现类测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始简单测试触发器迁移...")
    print("-" * 50)
    
    tests = [
        test_impl_imports,
        test_builtin_functions,
        test_implementation_classes,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("-" * 50)
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！触发器迁移成功！")
        return 0
    else:
        print("❌ 部分测试失败，请检查迁移结果。")
        return 1

if __name__ == "__main__":
    sys.exit(main())