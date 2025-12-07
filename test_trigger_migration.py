#!/usr/bin/env python3
"""测试触发器迁移

验证新的触发器架构是否正常工作。
"""

import sys
import os

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_trigger_functions_import():
    """测试触发器函数导入"""
    try:
        from src.core.workflow.graph.extensions.trigger_functions import (
            BuiltinTriggerFunctions,
            TimeTriggerImplementation,
            StateTriggerImplementation,
            EventTriggerImplementation,
            ToolErrorTriggerImplementation,
            IterationLimitTriggerImplementation,
        )
        print("✓ 触发器函数导入成功")
        return True
    except ImportError as e:
        print(f"✗ 触发器函数导入失败: {e}")
        return False

def test_trigger_classes_import():
    """测试触发器类导入"""
    try:
        from src.core.workflow.graph.extensions.triggers import (
            TimeTrigger,
            StateTrigger,
            EventTrigger,
            CustomTrigger,
            ToolErrorTrigger,
            IterationLimitTrigger,
        )
        print("✓ 触发器类导入成功")
        return True
    except ImportError as e:
        print(f"✗ 触发器类导入失败: {e}")
        return False

def test_function_implementation():
    """测试函数实现"""
    try:
        from src.core.workflow.graph.extensions.trigger_functions import BuiltinTriggerFunctions
        
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
        
        print("✓ 函数实现测试通过")
        return True
    except Exception as e:
        print(f"✗ 函数实现测试失败: {e}")
        return False

def test_trigger_class_implementation():
    """测试触发器类实现"""
    try:
        from src.core.workflow.graph.extensions.triggers import IterationLimitTrigger
        
        # 创建迭代限制触发器
        trigger = IterationLimitTrigger("test_trigger", 10)
        
        # 创建模拟状态和上下文
        state = {
            "messages": [],
            "tool_results": [],
            "iteration_count": 5
        }
        context = {}
        
        # 测试评估
        result = trigger.evaluate(state, context)
        assert result == False, "触发器评估应该返回 False"
        
        # 修改迭代次数
        state["iteration_count"] = 15
        result = trigger.evaluate(state, context)
        assert result == True, "触发器评估应该返回 True"
        
        print("✓ 触发器类实现测试通过")
        return True
    except Exception as e:
        print(f"✗ 触发器类实现测试失败: {e}")
        return False

def main():
    """主函数"""
    print("开始测试触发器迁移...")
    print("-" * 50)
    
    tests = [
        test_trigger_functions_import,
        test_trigger_classes_import,
        test_function_implementation,
        test_trigger_class_implementation,
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