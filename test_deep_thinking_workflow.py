"""测试Deep Thinking工作流配置解析"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.graph.workflow_validator import WorkflowValidator
from infrastructure.config.config_loader import YamlConfigLoader
from src.application.workflow.factory import WorkflowFactory

def test_deep_thinking_workflow_validation():
    """测试Deep Thinking工作流配置验证"""
    print("=== 开始验证Deep Thinking工作流配置 ===")
    
    # 配置文件路径 - 修正为相对路径
    config_path = "workflows/deep_thinking_workflow.yaml"
    
    # 1. 使用验证器验证配置文件
    validator = WorkflowValidator()
    issues = validator.validate_config_file(config_path)
    
    print(f"验证结果: 发现 {len(issues)} 个问题")
    
    for i, issue in enumerate(issues, 1):
        print(f"\n问题 {i}:")
        print(f"  严重程度: {issue.severity.value}")
        print(f"  消息: {issue.message}")
        if issue.location:
            print(f"  位置: {issue.location}")
        if issue.suggestion:
            print(f"  建议: {issue.suggestion}")
    
    # 2. 使用配置加载器加载配置文件
    print("\n=== 测试配置加载器 ===")
    try:
        config_loader = YamlConfigLoader()
        config_data = config_loader.load(config_path)
        print(f"✅ 配置加载成功")
        print(f"工作流名称: {config_data.get('name', '未定义')}")
        print(f"节点数量: {len(config_data.get('nodes', {}))}")
        print(f"边数量: {len(config_data.get('edges', []))}")
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False
    
    # 3. 测试工作流工厂
    print("\n=== 测试工作流工厂 ===")
    try:
        factory = WorkflowFactory(config_loader=config_loader)
        workflow_config = factory.load_workflow_config(config_path)
        print(f"✅ 工作流配置加载成功")
        print(f"工作流名称: {workflow_config.name}")
        print(f"入口节点: {workflow_config.entry_point}")
        print(f"最大迭代次数: {workflow_config.max_iterations}")
    except Exception as e:
        print(f"❌ 工作流工厂加载失败: {e}")
        return False
    
    return len(issues) == 0

def test_config_structure():
    """测试配置结构是否符合要求"""
    print("\n=== 测试配置结构 ===")
    
    config_path = "configs/workflows/deep_thinking_workflow.yaml"
    config_loader = YamlConfigLoader()
    
    try:
        config_data = config_loader.load(config_path)
        
        # 检查必需字段
        required_fields = ['name', 'description', 'entry_point', 'nodes', 'edges']
        missing_fields = []
        
        for field in required_fields:
            if field not in config_data:
                missing_fields.append(field)
        
        if missing_fields:
            print(f"❌ 缺少必需字段: {missing_fields}")
            return False
        else:
            print("✅ 所有必需字段都存在")
        
        # 检查节点配置
        nodes = config_data.get('nodes', {})
        if not nodes:
            print("❌ 节点配置为空")
            return False
        
        print(f"✅ 节点配置正常，包含 {len(nodes)} 个节点")
        
        # 检查边配置
        edges = config_data.get('edges', [])
        if not edges:
            print("❌ 边配置为空")
            return False
        
        print(f"✅ 边配置正常，包含 {len(edges)} 条边")
        
        # 检查入口节点是否存在
        entry_point = config_data.get('entry_point')
        if entry_point not in nodes:
            print(f"❌ 入口节点 '{entry_point}' 不存在于节点列表中")
            return False
        
        print(f"✅ 入口节点 '{entry_point}' 存在")
        
        return True
        
    except Exception as e:
        print(f"❌ 配置结构测试失败: {e}")
        return False

if __name__ == "__main__":
    print("Deep Thinking工作流配置解析测试")
    print("=" * 50)
    
    # 运行验证测试
    validation_passed = test_deep_thinking_workflow_validation()
    
    # 运行结构测试
    structure_passed = test_config_structure()
    
    print("\n" + "=" * 50)
    if validation_passed and structure_passed:
        print("🎉 所有测试通过！Deep Thinking工作流配置可以被正确解析")
    else:
        print("❌ 部分测试失败，需要修复配置问题")
    
    sys.exit(0 if (validation_passed and structure_passed) else 1)