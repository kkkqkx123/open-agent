#!/usr/bin/env python3
"""测试新的工作流模板系统核心功能"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入模板模块，避免复杂的依赖链
from src.core.workflow.templates.base import BaseWorkflowTemplate
from src.core.workflow.templates.react import ReActWorkflowTemplate
from src.core.workflow.templates.plan_execute import PlanExecuteWorkflowTemplate
from src.core.workflow.templates.registry import WorkflowTemplateRegistry, get_global_template_registry


def test_base_template():
    """测试基础模板类"""
    print("=== 测试基础模板类 ===")
    
    template = BaseWorkflowTemplate()
    template._name = "test_template"
    template._description = "测试模板"
    template._category = "test"
    template._version = "1.0"
    template._parameters = [
        {
            "name": "test_param",
            "type": "string",
            "description": "测试参数",
            "required": True
        }
    ]
    
    print(f"模板名称: {template.name}")
    print(f"模板描述: {template.description}")
    print(f"模板类别: {template.category}")
    print(f"模板版本: {template.version}")
    
    # 测试参数验证
    test_config = {"test_param": "test_value"}
    errors = template.validate_parameters(test_config)
    
    if errors:
        print(f"参数验证错误: {errors}")
        return False
    
    print("参数验证通过")
    return True


def test_react_template():
    """测试ReAct模板"""
    print("\n=== 测试ReAct模板 ===")
    
    template = ReActWorkflowTemplate()
    
    print(f"模板名称: {template.name}")
    print(f"模板描述: {template.description}")
    print(f"模板类别: {template.category}")
    print(f"模板版本: {template.version}")
    
    # 获取参数定义
    params = template.get_parameters()
    print(f"参数定义数量: {len(params)}")
    
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
    return True


def test_plan_execute_template():
    """测试Plan-Execute模板"""
    print("\n=== 测试Plan-Execute模板 ===")
    
    template = PlanExecuteWorkflowTemplate()
    
    print(f"模板名称: {template.name}")
    print(f"模板描述: {template.description}")
    print(f"模板类别: {template.category}")
    print(f"模板版本: {template.version}")
    
    # 获取参数定义
    params = template.get_parameters()
    print(f"参数定义数量: {len(params)}")
    
    # 测试参数验证
    test_config = {
        "llm_client": "default",
        "max_steps": 3,
        "planning_tools": ["research_tool"],
        "execution_tools": ["action_tool"]
    }
    
    errors = template.validate_parameters(test_config)
    if errors:
        print(f"参数验证错误: {errors}")
        return False
    
    print("参数验证通过")
    return True


def test_template_registry():
    """测试模板注册表"""
    print("\n=== 测试模板注册表 ===")
    
    registry = WorkflowTemplateRegistry()
    
    # 注册模板
    react_template = ReActWorkflowTemplate()
    registry.register_template(react_template)
    
    plan_execute_template = PlanExecuteWorkflowTemplate()
    registry.register_template(plan_execute_template)
    
    # 列出模板
    templates = registry.list_templates()
    print(f"注册的模板: {templates}")
    
    # 获取模板
    retrieved_template = registry.get_template("react")
    if retrieved_template and retrieved_template.name == "react":
        print("模板获取成功")
    else:
        print("模板获取失败")
        return False
    
    # 搜索模板
    search_results = registry.search_templates("react")
    print(f"搜索结果: {search_results}")
    
    # 按类别获取
    agent_templates = registry.get_templates_by_category("agent")
    print(f"Agent类别模板: {agent_templates}")
    
    return True


def test_global_registry():
    """测试全局注册表"""
    print("\n=== 测试全局注册表 ===")
    
    registry = get_global_template_registry()
    
    # 列出所有模板
    templates = registry.list_templates()
    print(f"全局注册的模板: {templates}")
    
    # 获取统计信息
    stats = registry.get_statistics()
    print(f"统计信息: {stats}")
    
    return True


def main():
    """主测试函数"""
    print("开始测试新的工作流模板系统核心功能...")
    
    try:
        # 测试基础模板
        if not test_base_template():
            print("基础模板测试失败")
            return False
        
        # 测试ReAct模板
        if not test_react_template():
            print("ReAct模板测试失败")
            return False
        
        # 测试Plan-Execute模板
        if not test_plan_execute_template():
            print("Plan-Execute模板测试失败")
            return False
        
        # 测试模板注册表
        if not test_template_registry():
            print("模板注册表测试失败")
            return False
        
        # 测试全局注册表
        if not test_global_registry():
            print("全局注册表测试失败")
            return False
        
        print("\n=== 所有核心测试通过 ===")
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)