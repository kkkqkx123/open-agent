"""将基于状态机的工作流配置转换为基于图的配置格式"""
"""例如把configs/workflows/ultra_thinking_workflow.yaml改为configs/workflows/ultra_thinking_workflow_convert.yaml"""

import yaml
import os
from typing import Dict, Any, List

def convert_states_to_graph(config_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    将基于状态机的配置转换为基于图的配置
    
    Args:
        config_data: 原始配置数据（包含states字段）
        
    Returns:
        转换后的配置数据（包含nodes和edges字段）
    """
    if 'states' not in config_data:
        raise ValueError("配置数据不包含states字段，无法转换")
    
    # 创建新的配置结构
    converted_config = {
        'name': config_data.get('name', 'converted_workflow'),
        'description': config_data.get('description', '转换后的工作流'),
        'version': config_data.get('version', '1.0.0'),
        'config_type': 'workflow',
        'workflow_name': config_data.get('name', 'converted_workflow'),
        'max_iterations': config_data.get('max_iterations', 10),
        'timeout': config_data.get('timeout', 300),
        'nodes': {},
        'edges': [],
        'state_schema': config_data.get('state_schema', {
            'name': 'WorkflowState',
            'fields': {
                'messages': {
                    'type': 'List[dict]',
                    'default': [],
                    'reducer': 'extend',
                    'description': '消息列表'
                },
                'input': {
                    'type': 'str',
                    'default': '',
                    'description': '输入文本'
                },
                'output': {
                    'type': 'str',
                    'default': '',
                    'description': '输出文本'
                },
                'errors': {
                    'type': 'List[str]',
                    'default': [],
                    'reducer': 'extend',
                    'description': '错误列表'
                }
            }
        })
    }
    
    # 转换状态为节点
    states = config_data['states']
    entry_point = None
    
    for state_name, state_config in states.items():
        # 确定节点类型
        node_type = state_config.get('type', 'process')
        
        # 创建节点配置
        node_config = {
            'function': f"{state_name}_node",
            'description': state_config.get('description', f'{state_name}节点'),
            'config': state_config.get('config', {})
        }
        
        # 根据状态类型设置不同的节点配置
        if node_type == 'start':
            node_config['function'] = 'start_node'
            entry_point = state_name
        elif node_type == 'end':
            node_config['function'] = 'end_node'
        elif node_type == 'llm_node':
            node_config['function'] = 'llm_node'
        elif node_type == 'deep_thinking_node':
            node_config['function'] = 'deep_thinking_node'
        elif node_type == 'analysis_node':
            node_config['function'] = 'analysis_node'
        elif node_type == 'parallel_node':
            node_config['function'] = 'parallel_node'
        elif node_type == 'agent_config_node':
            node_config['function'] = 'agent_config_node'
        elif node_type == 'collaboration_node':
            node_config['function'] = 'collaboration_node'
        
        converted_config['nodes'][state_name] = node_config
    
    # 转换状态转移为边
    for state_name, state_config in states.items():
        transitions = state_config.get('transitions', [])
        
        for transition in transitions:
            target_state = transition.get('target')
            condition = transition.get('condition', 'always')
            description = transition.get('description', f'从{state_name}到{target_state}')
            
            if target_state in states:
                # 创建边配置
                edge_config = {
                    'from': state_name,
                    'to': target_state,
                    'type': 'conditional' if condition != 'always' else 'simple',
                    'description': description
                }
                
                # 添加条件配置
                if condition != 'always':
                    edge_config['condition'] = condition
                
                converted_config['edges'].append(edge_config)
    
    # 设置入口点
    if entry_point:
        converted_config['entry_point'] = entry_point
    else:
        # 如果没有明确的start状态，使用第一个状态作为入口点
        first_state = list(states.keys())[0]
        converted_config['entry_point'] = first_state
    
    # 保留原始配置的元数据
    if 'metadata' in config_data:
        converted_config['metadata'] = config_data['metadata']
    
    # 保留输入模式
    if 'input_schema' in config_data:
        converted_config['input_schema'] = config_data['input_schema']
    
    # 保留错误处理配置
    if 'error_handling' in config_data:
        converted_config['error_handling'] = config_data['error_handling']
    
    # 保留监控配置
    if 'monitoring' in config_data:
        converted_config['monitoring'] = config_data['monitoring']
    
    return converted_config

def convert_workflow_file(input_file: str, output_file: str | None = None) -> bool:
    """
    转换工作流配置文件
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（可选，默认为输入文件加_converted后缀）
        
    Returns:
        bool: 转换是否成功
    """
    try:
        # 读取输入文件
        with open(input_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        print(f"📖 读取配置文件: {input_file}")
        print(f"   工作流名称: {config_data.get('name', '未命名')}")
        print(f"   状态数量: {len(config_data.get('states', {}))}")
        
        # 转换配置
        converted_config = convert_states_to_graph(config_data)
        
        # 确定输出文件路径
        if output_file is None:
            base_name = os.path.splitext(input_file)[0]
            output_file = f"{base_name}_converted.yaml"
        
        # 写入输出文件
        with open(output_file, 'w', encoding='utf-8') as f:
            yaml.dump(converted_config, f, default_flow_style=False, allow_unicode=True, indent=2)
        
        print(f"✅ 转换完成: {output_file}")
        print(f"   节点数量: {len(converted_config['nodes'])}")
        print(f"   边数量: {len(converted_config['edges'])}")
        print(f"   入口节点: {converted_config.get('entry_point', '未设置')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 转换失败: {e}")
        return False

def validate_converted_config(config_file: str) -> bool:
    """
    验证转换后的配置文件
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        bool: 验证是否通过
    """
    try:
        # 导入验证器（需要确保路径正确）
        import sys
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        from src.core.workflow.core.validator import WorkflowValidator
        
        validator = WorkflowValidator()
        issues = validator.validate_config_file(config_file)
        
        print(f"\n🔍 验证转换后的配置文件: {config_file}")
        
        if issues:
            error_count = sum(1 for issue in issues if issue.severity.value == "error")
            warning_count = sum(1 for issue in issues if issue.severity.value == "warning")
            
            print(f"   发现 {len(issues)} 个问题 (错误: {error_count}, 警告: {warning_count})")
            
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. [{issue.severity.value}] {issue.message}")
                if issue.suggestion:
                    print(f"      建议: {issue.suggestion}")
            
            return error_count == 0
        else:
            print("   ✅ 验证通过，无问题")
            return True
            
    except Exception as e:
        print(f"   ❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("工作流配置格式转换工具")
    print("=" * 60)
    
    # 转换Deep Thinking工作流
    print("\n1. 转换Deep Thinking工作流配置:")
    deep_thinking_input = "configs/workflows/deep_thinking_workflow.yaml"
    deep_thinking_output = "configs/workflows/deep_thinking_workflow_converted.yaml"
    
    deep_success = convert_workflow_file(deep_thinking_input, deep_thinking_output)
    
    if deep_success:
        validate_converted_config(deep_thinking_output)
    
    # 转换Ultra Thinking工作流
    print("\n2. 转换Ultra Thinking工作流配置:")
    ultra_thinking_input = "configs/workflows/ultra_thinking_workflow.yaml"
    ultra_thinking_output = "configs/workflows/ultra_thinking_workflow_converted.yaml"
    
    ultra_success = convert_workflow_file(ultra_thinking_input, ultra_thinking_output)
    
    if ultra_success:
        validate_converted_config(ultra_thinking_output)
    
    print("\n" + "=" * 60)
    print("转换结果汇总:")
    print(f"Deep Thinking: {'✅ 成功' if deep_success else '❌ 失败'}")
    print(f"Ultra Thinking: {'✅ 成功' if ultra_success else '❌ 失败'}")
    
    if deep_success and ultra_success:
        print("\n🎉 所有工作流配置转换完成！")
        print("转换后的配置文件已保存到configs/workflows/目录")
        print("这些文件现在可以被工作流系统正确解析")
    else:
        print("\n⚠️  部分转换失败，需要手动检查配置")

if __name__ == "__main__":
    main()