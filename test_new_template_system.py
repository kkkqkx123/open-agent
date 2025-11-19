#!/usr/bin/env python3
"""测试新的工作流模板系统"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.workflow.templates import get_global_template_registry
from src.core.workflow.templates.react import ReActWorkflowTemplate
from src.core.workflow.templates.plan_execute import PlanExecuteWorkflowTemplate


def test_template_registry():
    """测试模板注册表"""
    print("=== 测试模板注册表 ===")
    
    # 获取全局注册表
    registry = get_global_template_registry()
    
    # 列出所有模板
    templates = registry.list_templates()
    print(f"注册的模板: {templates}")
    
    # 获取模板信息
    for template_name in templates:
        info = registry.get_template_info(template_name)
        if info:
            print(f"模板 '{template_name}' 信息:")
            print(f"  描述: {info['description']}")
            print(f"  类别: {info['category']}")
            print(f"  版本: {info['version']}")
            print(f"  参数数量: {len(info['parameters'])}")
    
    return True


def test_react_template():
    """测试ReAct模板"""
    print("\n=== 测试ReAct模板 ===")
    
    registry = get_global_template_registry()
    template = registry.get_template("react")
    
    if not template:
        print("错误: 找不到ReAct模板")
        return False
    
    print(f"模板名称: {template.name}")
    print(f"模板描述: {template.description}")
    print(f"模板类别: {template.category}")
    print(f"模板版本: {template.version}")
    
    # 获取参数定义
    params = template.get_parameters()
    print(f"参数定义数量: {len(params)}")
    
    for param in params:
        print(f"  - {param['name']}: {param['description']} (类型: {param['type']})")
    
    # 测试参数验证
    test_config = {
        "llm_client": "default",
        "max_iterations": 5,
        "system_prompt": "测试提示词",
        "tools": ["tool1", "tool2"]
    }
    
    errors = template.validate_parameters(test_config)
    if errors:
        print(f"参数验证错误: {errors}")
        return False
    
    print("参数验证通过")
    
    # 测试创建工作流
    try:
        workflow = template.create_workflow(
            name="test_react_workflow",
            description="测试ReAct工作流",
            config=test_config
        )
        
        print(f"工作流创建成功: {workflow.name}")
        print(f"工作流ID: {workflow.workflow_id}")
        print(f"工作流节点数量: {len(workflow._nodes)}")
        print(f"工作流转换数量: {len(workflow._edges)}")
        
        return True
        
    except Exception as e:
        print(f"工作流创建失败: {e}")
        return False


def test_plan_execute_template():
    """测试Plan-Execute模板"""
    print("\n=== 测试Plan-Execute模板 ===")
    
    registry = get_global_template_registry()
    template = registry.get_template("plan_execute")
    
    if not template:
        print("错误: 找不到Plan-Execute模板")
        return False
    
    print(f"模板名称: {template.name}")
    print(f"模板描述: {template.description}")
    
    # 测试创建工作流
    test_config = {
        "llm_client": "default",
        "max_steps": 3,
        "planning_tools": ["research_tool"],
        "execution_tools": ["action_tool"]
    }
    
    try:
        workflow = template.create_workflow(
            name="test_plan_execute_workflow",
            description="测试Plan-Execute工作流",
            config=test_config
        )
        
        print(f"工作流创建成功: {workflow.name}")
        print(f"工作流ID: {workflow.workflow_id}")
        print(f"工作流节点数量: {len(workflow._nodes)}")
        print(f"工作流转换数量: {len(workflow._edges)}")
        
        return True
        
    except Exception as e:
        print(f"工作流创建失败: {e}")
        return False


def main():
    """主测试函数"""
    print("开始测试新的工作流模板系统...")
    
    try:
        # 测试模板注册表
        if not test_template_registry():
            print("模板注册表测试失败")
            return False
        
        # 测试ReAct模板
        if not test_react_template():
            print("ReAct模板测试失败")
            return False
        
        # 测试Plan-Execute模板
        if not test_plan_execute_template():
            print("Plan-Execute模板测试失败")
            return False
        
        print("\n=== 所有测试通过 ===")
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)