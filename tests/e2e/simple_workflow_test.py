"""简化的工作流测试脚本

测试base_workflow.yaml配置的加载和执行
"""

import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

def test_workflow_loading():
    """测试工作流加载"""
    print("=== 测试工作流加载 ===")
    
    try:
        from src.infrastructure.graph.config import GraphConfig
        import yaml
        
        # 加载配置文件
        config_path = project_root / "configs" / "workflows" / "base_workflow.yaml"
        print(f"加载配置文件: {config_path}")
        
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        print(f"配置数据: {config_data}")
        
        # 转换为GraphConfig对象
        graph_config = GraphConfig.from_dict(config_data)
        
        print(f"图配置名称: {graph_config.name}")
        print(f"图配置描述: {graph_config.description}")
        print(f"图配置版本: {graph_config.version}")
        print(f"节点数量: {len(graph_config.nodes)}")
        print(f"边数量: {len(graph_config.edges)}")
        print(f"入口点: {graph_config.entry_point}")
        
        print("✅ 工作流加载成功!")
        return True
        
    except Exception as e:
        print(f"❌ 工作流加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_graph_building():
    """测试图构建"""
    print("\n=== 测试图构建 ===")
    
    try:
        from src.infrastructure.graph.config import GraphConfig
        from src.infrastructure.graph.builder import GraphBuilder
        from src.infrastructure.graph.registry import get_global_registry
        import yaml
        
        # 加载配置文件
        config_path = project_root / "configs" / "workflows" / "base_workflow.yaml"
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        graph_config = GraphConfig.from_dict(config_data)
        
        # 创建图构建器
        node_registry = get_global_registry()
        graph_builder = GraphBuilder(node_registry=node_registry)
        
        # 注册自定义节点函数
        from src.infrastructure.graph.function_registry import FunctionType
        
        def start_node(state):
            """开始节点函数"""
            messages = state.get("messages", [])
            input_text = state.get("input", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流开始执行，输入: {input_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"处理输入: {input_text}"
            }

        def end_node(state):
            """结束节点函数"""
            messages = state.get("messages", [])
            output_text = state.get("output", "")
            
            messages.append({
                "role": "system",
                "content": f"工作流执行完成，输出: {output_text}"
            })
            
            return {
                **state,
                "messages": messages,
                "output": f"最终输出: {output_text}"
            }
        
        # 注册函数
        graph_builder.register_function("start_node", start_node, FunctionType.NODE_FUNCTION)
        graph_builder.register_function("end_node", end_node, FunctionType.NODE_FUNCTION)
        
        # 构建图
        graph = graph_builder.build_graph(graph_config)
        
        print("✅ 图构建成功!")
        return True, graph
        
    except Exception as e:
        print(f"❌ 图构建失败: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def test_workflow_execution(graph):
    """测试工作流执行"""
    print("\n=== 测试工作流执行 ===")
    
    try:
        # 初始状态
        initial_state = {
            "input": "测试输入",
            "messages": []
        }
        
        print(f"初始状态: {initial_state}")
        
        # 执行工作流
        result = graph.invoke(initial_state)
        
        print(f"执行结果: {result}")
        
        # 验证结果
        assert "messages" in result
        assert "output" in result
        assert len(result["messages"]) >= 2
        assert "工作流开始执行" in result["messages"][0]["content"]
        assert "工作流执行完成" in result["messages"][-1]["content"]
        assert "最终输出: 处理输入: 测试输入" == result["output"]
        
        print("✅ 工作流执行成功!")
        return True
        
    except Exception as e:
        print(f"❌ 工作流执行失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("开始工作流端到端测试")
    print("=" * 50)
    
    # 测试工作流加载
    load_success = test_workflow_loading()
    if not load_success:
        return False
    
    # 测试图构建
    build_success, graph = test_graph_building()
    if not build_success:
        return False
    
    # 测试工作流执行
    exec_success = test_workflow_execution(graph)
    if not exec_success:
        return False
    
    print("\n" + "=" * 50)
    print("🎉 所有测试通过!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)