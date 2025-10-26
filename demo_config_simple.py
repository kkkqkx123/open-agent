#!/usr/bin/env python3
"""
简化的配置继承功能演示脚本
"""

import yaml
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def demo_yaml_loading():
    """演示YAML文件加载"""
    print("=" * 60)
    print("演示: YAML配置文件加载")
    print("=" * 60)
    
    try:
        # 加载基础工作流配置
        base_config_path = Path("configs/workflows/base_workflow.yaml")
        if base_config_path.exists():
            with open(base_config_path, "r", encoding="utf-8") as f:
                base_config = yaml.safe_load(f)
            
            print("基础工作流配置:")
            print(f"  名称: {base_config.get('metadata', {}).get('name', 'Unknown')}")
            print(f"  版本: {base_config.get('metadata', {}).get('version', 'Unknown')}")
            print(f"  描述: {base_config.get('metadata', {}).get('description', 'Unknown')}")
            print(f"  最大迭代次数: {base_config.get('max_iterations', 'Unknown')}")
            print(f"  节点数量: {len(base_config.get('nodes', {}))}")
            print(f"  边数量: {len(base_config.get('edges', []))}")
        
        # 加载ReAct工作流配置
        react_config_path = Path("configs/workflows/react_workflow.yaml")
        if react_config_path.exists():
            with open(react_config_path, "r", encoding="utf-8") as f:
                react_config = yaml.safe_load(f)
            
            print("\nReAct工作流配置:")
            print(f"  名称: {react_config.get('metadata', {}).get('name', 'Unknown')}")
            print(f"  版本: {react_config.get('metadata', {}).get('version', 'Unknown')}")
            print(f"  描述: {react_config.get('metadata', {}).get('description', 'Unknown')}")
            print(f"  继承自: {react_config.get('inherits_from', '无')}")
            print(f"  最大迭代次数: {react_config.get('max_iterations', 'Unknown')}")
            print(f"  节点数量: {len(react_config.get('nodes', {}))}")
            print(f"  边数量: {len(react_config.get('edges', []))}")
            
            # 对比配置
            print("\n配置对比:")
            base_nodes = len(base_config.get('nodes', {}))
            react_nodes = len(react_config.get('nodes', {}))
            base_edges = len(base_config.get('edges', []))
            react_edges = len(react_config.get('edges', []))
            
            print(f"  基础节点: {base_nodes}, ReAct节点: {react_nodes} (+{react_nodes - base_nodes})")
            print(f"  基础边: {base_edges}, ReAct边: {react_edges} (+{react_edges - base_edges})")
            print(f"  基础迭代: {base_config.get('max_iterations')}, ReAct迭代: {react_config.get('max_iterations')}")
        
    except Exception as e:
        print(f"加载配置失败: {e}")


def demo_config_structure():
    """演示配置结构"""
    print("\n" + "=" * 60)
    print("演示: 配置结构分析")
    print("=" * 60)
    
    try:
        react_config_path = Path("configs/workflows/react_workflow.yaml")
        if react_config_path.exists():
            with open(react_config_path, "r", encoding="utf-8") as f:
                react_config = yaml.safe_load(f)
            
            print("ReAct工作流配置结构:")
            
            # 显示顶层结构
            print("  顶层字段:")
            for key in react_config.keys():
                value = react_config[key]
                if isinstance(value, dict):
                    print(f"    - {key}: dict ({len(value)} 个子字段)")
                elif isinstance(value, list):
                    print(f"    - {key}: list ({len(value)} 个元素)")
                else:
                    print(f"    - {key}: {type(value).__name__} = {value}")
            
            # 显示状态模式
            if 'state_schema' in react_config:
                schema = react_config['state_schema']
                print(f"\n  状态模式:")
                print(f"    名称: {schema.get('name', 'Unknown')}")
                if 'fields' in schema:
                    fields = schema['fields']
                    print(f"    字段数量: {len(fields)}")
                    print("    字段列表:")
                    for field_name, field_config in fields.items():
                        field_type = field_config.get('type', 'unknown')
                        description = field_config.get('description', '')
                        print(f"      - {field_name}: {field_type} - {description}")
            
            # 显示节点配置
            if 'nodes' in react_config:
                nodes = react_config['nodes']
                print(f"\n  节点配置:")
                print(f"    节点数量: {len(nodes)}")
                print("    节点列表:")
                for node_name, node_config in nodes.items():
                    function = node_config.get('function', 'unknown')
                    description = node_config.get('description', '')
                    print(f"      - {node_name}: {function} - {description}")
            
            # 显示边配置
            if 'edges' in react_config:
                edges = react_config['edges']
                print(f"\n  边配置:")
                print(f"    边数量: {len(edges)}")
                print("    边列表:")
                for i, edge in enumerate(edges):
                    from_node = edge.get('from', 'unknown')
                    to_node = edge.get('to', 'unknown')
                    edge_type = edge.get('type', 'unknown')
                    description = edge.get('description', '')
                    print(f"      {i+1}. {from_node} -> {to_node} ({edge_type}) - {description}")
        
    except Exception as e:
        print(f"分析配置结构失败: {e}")


def demo_config_validation():
    """演示配置验证"""
    print("\n" + "=" * 60)
    print("演示: 配置验证")
    print("=" * 60)
    
    try:
        react_config_path = Path("configs/workflows/react_workflow.yaml")
        if react_config_path.exists():
            with open(react_config_path, "r", encoding="utf-8") as f:
                react_config = yaml.safe_load(f)
            
            print("配置验证检查:")
            
            # 检查必需字段
            required_fields = ['metadata', 'workflow_name', 'max_iterations', 'nodes', 'edges', 'entry_point']
            missing_fields = []
            
            for field in required_fields:
                if field not in react_config:
                    missing_fields.append(field)
            
            if missing_fields:
                print(f"  缺少字段: {missing_fields}")
            else:
                print("  ✓ 所有必需字段都存在")
            
            # 检查元数据
            metadata = react_config.get('metadata', {})
            if 'name' in metadata and 'version' in metadata:
                print("  ✓ 元数据完整")
            else:
                print("  ✗ 元数据不完整")
            
            # 检查数值范围
            max_iterations = react_config.get('max_iterations')
            if isinstance(max_iterations, int) and max_iterations > 0:
                print(f"  ✓ 最大迭代次数有效: {max_iterations}")
            else:
                print(f"  ✗ 最大迭代次数无效: {max_iterations}")
            
            # 检查节点和边
            nodes = react_config.get('nodes', {})
            edges = react_config.get('edges', [])
            
            if len(nodes) > 0:
                print(f"  ✓ 节点配置有效: {len(nodes)} 个节点")
            else:
                print("  ✗ 没有节点配置")
            
            if len(edges) > 0:
                print(f"  ✓ 边配置有效: {len(edges)} 条边")
            else:
                print("  ✗ 没有边配置")
            
            # 检查入口点
            entry_point = react_config.get('entry_point')
            if entry_point and entry_point in nodes:
                print(f"  ✓ 入口点有效: {entry_point}")
            else:
                print(f"  ✗ 入口点无效: {entry_point}")
        
    except Exception as e:
        print(f"配置验证失败: {e}")


def main():
    """主函数"""
    print("配置继承系统简化演示")
    print("=" * 60)
    
    # 演示1: YAML文件加载
    demo_yaml_loading()
    
    # 演示2: 配置结构分析
    demo_config_structure()
    
    # 演示3: 配置验证
    demo_config_validation()
    
    print("\n" + "=" * 60)
    print("简化演示完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()