"""测试工作流配置解析能力"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.infrastructure.graph.workflow_validator import WorkflowValidator
from infrastructure.config.loader.file_config_loader import FileConfigLoader

def test_workflow_validation(workflow_name, config_path):
    """测试工作流配置验证"""
    print(f"\n=== 开始验证{workflow_name}工作流配置 ===")
    
    # 1. 使用验证器验证配置文件
    validator = WorkflowValidator()
    issues = validator.validate_config_file(config_path)
    
    print(f"验证结果: 发现 {len(issues)} 个问题")
    
    error_count = 0
    warning_count = 0
    info_count = 0
    
    for i, issue in enumerate(issues, 1):
        if issue.severity.value == "error":
            error_count += 1
        elif issue.severity.value == "warning":
            warning_count += 1
        else:
            info_count += 1
            
        print(f"\n问题 {i}:")
        print(f"  严重程度: {issue.severity.value}")
        print(f"  消息: {issue.message}")
        if issue.location:
            print(f"  位置: {issue.location}")
        if issue.suggestion:
            print(f"  建议: {issue.suggestion}")
    
    print(f"\n问题统计: 错误={error_count}, 警告={warning_count}, 信息={info_count}")
    
    # 2. 使用配置加载器加载配置文件
    print("\n=== 测试配置加载器 ===")
    try:
        config_loader = FileConfigLoader()
        config_data = config_loader.load(config_path)
        print(f"✅ 配置加载成功")
        print(f"工作流名称: {config_data.get('name', config_data.get('workflow_name', '未定义'))}")
        print(f"节点数量: {len(config_data.get('nodes', {}))}")
        print(f"边数量: {len(config_data.get('edges', []))}")
        
        # 检查配置类型
        if 'states' in config_data:
            print("⚠️  检测到基于状态机的配置格式（states字段）")
            print(f"状态数量: {len(config_data.get('states', {}))}")
        else:
            print("✅ 使用基于图的配置格式（nodes和edges字段）")
            
    except Exception as e:
        print(f"❌ 配置加载失败: {e}")
        return False, error_count
    
    return error_count == 0, error_count

def test_config_structure(workflow_name, config_path):
    """测试配置结构是否符合要求"""
    print(f"\n=== 测试{workflow_name}配置结构 ===")
    
    config_loader = FileConfigLoader()
    
    try:
        config_data = config_loader.load(config_path)
        
        # 检查配置格式类型
        has_nodes_edges = 'nodes' in config_data and 'edges' in config_data
        has_states = 'states' in config_data
        
        if has_states and not has_nodes_edges:
            print("⚠️  使用基于状态机的配置格式")
            
            # 检查状态机格式的必需字段
            required_fields = ['name', 'description', 'states']
            missing_fields = []
            
            for field in required_fields:
                if field not in config_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必需字段: {missing_fields}")
                return False
            else:
                print("✅ 所有状态机必需字段都存在")
            
            # 检查状态配置
            states = config_data.get('states', {})
            if not states:
                print("❌ 状态配置为空")
                return False
            
            print(f"✅ 状态配置正常，包含 {len(states)} 个状态")
            
            # 检查是否有初始状态
            initial_state = None
            for state_name, state_config in states.items():
                if state_config.get('type') == 'start':
                    initial_state = state_name
                    break
            
            if not initial_state:
                print("❌ 未找到初始状态（type为start的状态）")
                return False
            
            print(f"✅ 找到初始状态: {initial_state}")
            
            return True
            
        elif has_nodes_edges:
            print("✅ 使用基于图的配置格式")
            
            # 检查基于图格式的必需字段
            required_fields = ['name', 'description', 'nodes', 'edges', 'entry_point']
            missing_fields = []
            
            for field in required_fields:
                if field not in config_data:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"❌ 缺少必需字段: {missing_fields}")
                return False
            else:
                print("✅ 所有基于图的必需字段都存在")
            
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
        else:
            print("❌ 配置格式不明确，既没有nodes/edges也没有states字段")
            return False
        
    except Exception as e:
        print(f"❌ 配置结构测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("工作流配置解析能力测试")
    print("=" * 60)
    
    # 测试Deep Thinking工作流
    deep_thinking_path = "workflows/deep_thinking_workflow.yaml"
    deep_thinking_valid, deep_thinking_errors = test_workflow_validation("Deep Thinking", deep_thinking_path)
    deep_thinking_structure = test_config_structure("Deep Thinking", deep_thinking_path)
    
    # 测试Ultra Thinking工作流
    ultra_thinking_path = "workflows/ultra_thinking_workflow.yaml"
    ultra_thinking_valid, ultra_thinking_errors = test_workflow_validation("Ultra Thinking", ultra_thinking_path)
    ultra_thinking_structure = test_config_structure("Ultra Thinking", ultra_thinking_path)
    
    # 测试基础工作流（作为参考）
    base_workflow_path = "workflows/base_workflow.yaml"
    base_valid, base_errors = test_workflow_validation("基础工作流", base_workflow_path)
    base_structure = test_config_structure("基础工作流", base_workflow_path)
    
    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("-" * 60)
    
    print(f"Deep Thinking工作流:")
    print(f"  验证通过: {'✅' if deep_thinking_valid else '❌'}")
    print(f"  结构正确: {'✅' if deep_thinking_structure else '❌'}")
    print(f"  错误数量: {deep_thinking_errors}")
    
    print(f"\nUltra Thinking工作流:")
    print(f"  验证通过: {'✅' if ultra_thinking_valid else '❌'}")
    print(f"  结构正确: {'✅' if ultra_thinking_structure else '❌'}")
    print(f"  错误数量: {ultra_thinking_errors}")
    
    print(f"\n基础工作流（参考）:")
    print(f"  验证通过: {'✅' if base_valid else '❌'}")
    print(f"  结构正确: {'✅' if base_structure else '❌'}")
    print(f"  错误数量: {base_errors}")
    
    print("\n" + "=" * 60)
    
    # 分析兼容性问题
    if deep_thinking_errors > 0 or ultra_thinking_errors > 0:
        print("\n📋 兼容性分析:")
        print("-" * 40)
        
        if deep_thinking_errors > 0:
            print("❌ Deep Thinking工作流配置存在兼容性问题:")
            print("   - 使用了基于状态机的配置格式（states字段）")
            print("   - 当前系统期望基于图的配置格式（nodes和edges字段）")
            print("   - 需要将states格式转换为nodes/edges格式")
        
        if ultra_thinking_errors > 0:
            print("❌ Ultra Thinking工作流配置存在兼容性问题:")
            print("   - 需要检查具体配置格式")
        
        if base_errors == 0:
            print("\n✅ 基础工作流配置格式正确，可作为转换参考")
            print("   - 使用nodes和edges字段定义工作流结构")
            print("   - 包含entry_point指定入口节点")
            print("   - 使用state_schema定义状态模式")
    
    # 总体结论
    all_passed = (deep_thinking_valid and deep_thinking_structure and 
                  ultra_thinking_valid and ultra_thinking_structure)
    
    if all_passed:
        print("\n🎉 所有工作流配置都可以被正确解析！")
    else:
        print("\n⚠️  部分工作流配置需要修复才能被正确解析")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)