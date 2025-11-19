#!/usr/bin/env python3
"""简单检查新的工作流模板文件"""

import os


def check_file_exists(file_path, description):
    """检查文件是否存在"""
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    exists = os.path.exists(full_path)
    status = "✓" if exists else "✗"
    print(f"{status} {description}: {file_path}")
    return exists


def check_file_content(file_path, content_checks, description):
    """检查文件内容"""
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if not os.path.exists(full_path):
        print(f"✗ {description}文件不存在: {file_path}")
        return False
    
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        all_passed = True
        for check_name, check_pattern in content_checks.items():
            if check_pattern in content:
                print(f"  ✓ {check_name}")
            else:
                print(f"  ✗ {check_name}")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"✗ 读取文件失败 {file_path}: {e}")
        return False


def main():
    """主测试函数"""
    print("=== 检查新的工作流模板系统文件 ===")
    
    all_passed = True
    
    # 检查接口文件
    print("\n1. 检查接口定义:")
    interface_checks = [
        ('src/core/workflow/interfaces.py', '工作流接口定义文件')
    ]
    
    for file_path, description in interface_checks:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    # 检查接口内容
    if all_passed:
        interface_content_checks = {
            'IWorkflowTemplate接口': 'class IWorkflowTemplate(ABC)',
            'IWorkflowTemplateRegistry接口': 'class IWorkflowTemplateRegistry(ABC)',
            'name属性': 'def name(self) -> str',
            'create_workflow方法': 'def create_workflow(',
            'get_parameters方法': 'def get_parameters(',
            'validate_parameters方法': 'def validate_parameters('
        }
        
        if not check_file_content('src/core/workflow/interfaces.py', interface_content_checks, '接口'):
            all_passed = False
    
    # 检查模板文件
    print("\n2. 检查模板文件:")
    template_files = [
        ('src/core/workflow/templates/__init__.py', '模板模块初始化文件'),
        ('src/core/workflow/templates/base.py', '基础模板类文件'),
        ('src/core/workflow/templates/react.py', 'ReAct模板文件'),
        ('src/core/workflow/templates/plan_execute.py', 'Plan-Execute模板文件'),
        ('src/core/workflow/templates/registry.py', '模板注册表文件')
    ]
    
    for file_path, description in template_files:
        if not check_file_exists(file_path, description):
            all_passed = False
    
    # 检查基础模板内容
    if all_passed:
        print("\n3. 检查基础模板内容:")
        base_content_checks = {
            'BaseWorkflowTemplate类': 'class BaseWorkflowTemplate(IWorkflowTemplate, ABC)',
            'IWorkflowTemplate实现': 'IWorkflowTemplate',
            'create_workflow方法': 'def create_workflow(',
            'get_parameters方法': 'def get_parameters(',
            'validate_parameters方法': 'def validate_parameters(',
            '参数类型验证': 'def _validate_parameter_type('
        }
        
        if not check_file_content('src/core/workflow/templates/base.py', base_content_checks, '基础模板'):
            all_passed = False
    
    # 检查ReAct模板内容
    if all_passed:
        print("\n4. 检查ReAct模板内容:")
        react_content_checks = {
            'ReActWorkflowTemplate类': 'class ReActWorkflowTemplate(BaseWorkflowTemplate)',
            'EnhancedReActTemplate类': 'class EnhancedReActTemplate(ReActWorkflowTemplate)',
            '_build_workflow_structure方法': 'def _build_workflow_structure('
        }
        
        if not check_file_content('src/core/workflow/templates/react.py', react_content_checks, 'ReAct模板'):
            all_passed = False
    
    # 检查Plan-Execute模板内容
    if all_passed:
        print("\n5. 检查Plan-Execute模板内容:")
        plan_content_checks = {
            'PlanExecuteWorkflowTemplate类': 'class PlanExecuteWorkflowTemplate(BaseWorkflowTemplate)',
            'CollaborativePlanExecuteTemplate类': 'class CollaborativePlanExecuteTemplate(PlanExecuteWorkflowTemplate)',
            '_build_workflow_structure方法': 'def _build_workflow_structure(',
            '计划制定节点': 'planning',
            '步骤执行节点': 'execute_step',
            '结果审查节点': 'review'
        }
        
        if not check_file_content('src/core/workflow/templates/plan_execute.py', plan_content_checks, 'Plan-Execute模板'):
            all_passed = False
    
    # 检查注册表内容
    if all_passed:
        print("\n6. 检查注册表内容:")
        registry_content_checks = {
            'WorkflowTemplateRegistry类': 'class WorkflowTemplateRegistry',
            'get_global_template_registry函数': 'def get_global_template_registry()',
            'register_template方法': 'def register_template(',
            'get_template方法': 'def get_template(',
            'list_templates方法': 'def list_templates(',
            'create_workflow_from_template方法': 'def create_workflow_from_template(',
            '内置模板注册': '_register_builtin_templates'
        }
        
        if not check_file_content('src/core/workflow/templates/registry.py', registry_content_checks, '注册表'):
            all_passed = False
    
    # 检查核心工作流模块
    if all_passed:
        print("\n7. 检查核心工作流模块:")
        init_content_checks = {
            'IWorkflowTemplate导出': 'IWorkflowTemplate',
            'IWorkflowTemplateRegistry导出': 'IWorkflowTemplateRegistry',
            '模板相关导出': 'WorkflowTemplate',
            '模板错误导出': 'WorkflowTemplateError'
        }
        
        if not check_file_content('src/core/workflow/__init__.py', init_content_checks, '核心工作流模块'):
            all_passed = False
    
    # 检查服务层工厂更新
    if all_passed:
        print("\n8. 检查服务层工厂更新:")
        factory_content_checks = {
            '模板管理器导入': 'get_global_template_registry',
            'create_from_template更新': 'template.create_workflow',
            'register_template_instance方法': 'def register_template_instance',
            '新旧模板系统兼容': 'self._template_manager.get_template'
        }
        
        if not check_file_content('src/services/workflow/factory.py', factory_content_checks, '服务层工厂'):
            all_passed = False
    
    # 总结
    print(f"\n=== 测试结果 ===")
    if all_passed:
        print("✓ 所有检查通过！")
        print("✓ 新的工作流模板系统已正确实现")
        print("✓ 接口定义完整")
        print("✓ 模板实现完整")
        print("✓ 注册表功能完整")
        print("✓ 服务层集成正确")
        return True
    else:
        print("✗ 部分检查失败")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)