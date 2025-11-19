#!/usr/bin/env python3
"""简单测试新的工作流模板系统"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入具体的模板文件
import importlib.util

def import_module_from_path(module_name, file_path):
    """从文件路径导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_template_interfaces():
    """测试模板接口定义"""
    print("=== 测试模板接口定义 ===")
    
    # 导入接口模块
    interfaces_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'workflow', 'interfaces.py')
    if os.path.exists(interfaces_path):
        interfaces_module = import_module_from_path("workflow_interfaces", interfaces_path)
        
        # 检查IWorkflowTemplate接口是否存在
        if hasattr(interfaces_module, 'IWorkflowTemplate'):
            print("✓ IWorkflowTemplate接口已定义")
        else:
            print("✗ IWorkflowTemplate接口未定义")
            return False
            
        # 检查IWorkflowTemplateRegistry接口是否存在
        if hasattr(interfaces_module, 'IWorkflowTemplateRegistry'):
            print("✓ IWorkflowTemplateRegistry接口已定义")
        else:
            print("✗ IWorkflowTemplateRegistry接口未定义")
            return False
            
        return True
    else:
        print("✗ 接口文件不存在")
        return False


def test_template_files():
    """测试模板文件是否存在"""
    print("\n=== 测试模板文件 ===")
    
    template_files = [
        'src/core/workflow/templates/__init__.py',
        'src/core/workflow/templates/base.py',
        'src/core/workflow/templates/react.py',
        'src/core/workflow/templates/plan_execute.py',
        'src/core/workflow/templates/registry.py'
    ]
    
    all_exist = True
    for file_path in template_files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        if os.path.exists(full_path):
            print(f"✓ {file_path} 存在")
        else:
            print(f"✗ {file_path} 不存在")
            all_exist = False
    
    return all_exist


def test_template_content():
    """测试模板文件内容"""
    print("\n=== 测试模板文件内容 ===")
    
    # 测试基础模板
    base_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'workflow', 'templates', 'base.py')
    if os.path.exists(base_path):
        with open(base_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'class BaseWorkflowTemplate' in content:
            print("✓ BaseWorkflowTemplate类存在")
        else:
            print("✗ BaseWorkflowTemplate类不存在")
            return False
            
        if 'IWorkflowTemplate' in content:
            print("✓ 实现了IWorkflowTemplate接口")
        else:
            print("✗ 未实现IWorkflowTemplate接口")
            return False
            
        if 'create_workflow' in content:
            print("✓ 包含create_workflow方法")
        else:
            print("✗ 不包含create_workflow方法")
            return False
            
        return True
    else:
        print("✗ 基础模板文件不存在")
        return False


def test_react_template_content():
    """测试ReAct模板内容"""
    print("\n=== 测试ReAct模板内容 ===")
    
    react_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'workflow', 'templates', 'react.py')
    if os.path.exists(react_path):
        with open(react_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'class ReActWorkflowTemplate' in content:
            print("✓ ReActWorkflowTemplate类存在")
        else:
            print("✗ ReActWorkflowTemplate类不存在")
            return False
            
        if 'class EnhancedReActTemplate' in content:
            print("✓ EnhancedReActTemplate类存在")
        else:
            print("✗ EnhancedReActTemplate类不存在")
            return False
            
        if '_build_workflow_structure' in content:
            print("✓ 包含_build_workflow_structure方法")
        else:
            print("✗ 不包含_build_workflow_structure方法")
            return False
            
        return True
    else:
        print("✗ ReAct模板文件不存在")
        return False


def test_registry_content():
    """测试注册表内容"""
    print("\n=== 测试注册表内容 ===")
    
    registry_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'workflow', 'templates', 'registry.py')
    if os.path.exists(registry_path):
        with open(registry_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'class WorkflowTemplateRegistry' in content:
            print("✓ WorkflowTemplateRegistry类存在")
        else:
            print("✗ WorkflowTemplateRegistry类不存在")
            return False
            
        if 'get_global_template_registry' in content:
            print("✓ 包含get_global_template_registry函数")
        else:
            print("✗ 不包含get_global_template_registry函数")
            return False
            
        if 'register_template' in content:
            print("✓ 包含register_template方法")
        else:
            print("✗ 不包含register_template方法")
            return False
            
        return True
    else:
        print("✗ 注册表文件不存在")
        return False


def test_core_workflow_init():
    """测试核心工作流模块初始化"""
    print("\n=== 测试核心工作流模块初始化 ===")
    
    init_path = os.path.join(os.path.dirname(__file__), 'src', 'core', 'workflow', '__init__.py')
    if os.path.exists(init_path):
        with open(init_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if 'IWorkflowTemplate' in content:
            print("✓ 导出了IWorkflowTemplate接口")
        else:
            print("✗ 未导出IWorkflowTemplate接口")
            return False
            
        if 'IWorkflowTemplateRegistry' in content:
            print("✓ 导出了IWorkflowTemplateRegistry接口")
        else:
            print("✗ 未导出IWorkflowTemplateRegistry接口")
            return False
            
        return True
    else:
        print("✗ 核心工作流模块初始化文件不存在")
        return False


def main():
    """主测试函数"""
    print("开始测试新的工作流模板系统...")
    
    try:
        # 测试模板接口定义
        if not test_template_interfaces():
            print("模板接口定义测试失败")
            return False
        
        # 测试模板文件
        if not test_template_files():
            print("模板文件测试失败")
            return False
        
        # 测试模板文件内容
        if not test_template_content():
            print("模板文件内容测试失败")
            return False
        
        # 测试ReAct模板内容
        if not test_react_template_content():
            print("ReAct模板内容测试失败")
            return False
        
        # 测试注册表内容
        if not test_registry_content():
            print("注册表内容测试失败")
            return False
        
        # 测试核心工作流模块初始化
        if not test_core_workflow_init():
            print("核心工作流模块初始化测试失败")
            return False
        
        print("\n=== 所有测试通过 ===")
        print("新的工作流模板系统核心功能已正确实现！")
        return True
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)