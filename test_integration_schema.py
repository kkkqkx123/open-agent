"""集成测试：验证Schema生成器和节点修改

测试从配置文件生成Schema的功能是否正常工作。
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_schema_generator():
    """测试Schema生成器"""
    print("=== 测试Schema生成器 ===")
    
    try:
        from src.core.workflow.config.schema_generator import get_schema_generator
        
        # 获取Schema生成器
        generator = get_schema_generator()
        print("✓ Schema生成器初始化成功")
        
        # 测试LLM节点Schema生成
        llm_schema = generator.generate_schema_from_config('llm_node')
        print("✓ LLM节点Schema生成成功")
        print(f"  - Schema类型: {llm_schema.get('type')}")
        print(f"  - 属性数量: {len(llm_schema.get('properties', {}))}")
        print(f"  - 必需字段: {llm_schema.get('required', [])}")
        
        # 测试工具节点Schema生成
        tool_schema = generator.generate_schema_from_config('tool_node')
        print("✓ 工具节点Schema生成成功")
        print(f"  - Schema类型: {tool_schema.get('type')}")
        print(f"  - 属性数量: {len(tool_schema.get('properties', {}))}")
        print(f"  - 必需字段: {tool_schema.get('required', [])}")
        
        # 测试START节点Schema生成
        start_schema = generator.generate_schema_from_config('start_node')
        print("✓ START节点Schema生成成功")
        print(f"  - Schema类型: {start_schema.get('type')}")
        print(f"  - 属性数量: {len(start_schema.get('properties', {}))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Schema生成器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_node_schema_methods():
    """测试节点Schema方法"""
    print("\n=== 测试节点Schema方法 ===")
    
    try:
        # 测试LLM节点
        from src.core.workflow.graph.nodes.llm_node import LLMNode
        llm_node = LLMNode()
        llm_schema = llm_node.get_config_schema()
        print("✓ LLM节点get_config_schema()方法正常")
        print(f"  - Schema类型: {llm_schema.get('type')}")
        
        # 测试工具节点
        from src.core.workflow.graph.nodes.tool_node import ToolNode
        from src.interfaces.tool.base import IToolRegistry
        
        # 创建模拟的工具注册器
        class MockToolRegistry(IToolRegistry):
            def get_tool(self, name: str):
                return None
            def register_tool(self, tool):
                pass
            def list_tools(self):
                return []
            def unregister_tool(self, name: str) -> bool:
                return False
        
        tool_node = ToolNode(MockToolRegistry())
        tool_schema = tool_node.get_config_schema()
        print("✓ 工具节点get_config_schema()方法正常")
        print(f"  - Schema类型: {tool_schema.get('type')}")
        
        # 测试START节点
        from src.core.workflow.graph.nodes.start_node import StartNode
        start_node = StartNode()
        start_schema = start_node.get_config_schema()
        print("✓ START节点get_config_schema()方法正常")
        print(f"  - Schema类型: {start_schema.get('type')}")
        
        # 测试END节点
        from src.core.workflow.graph.nodes.end_node import EndNode
        end_node = EndNode()
        end_schema = end_node.get_config_schema()
        print("✓ END节点get_config_schema()方法正常")
        print(f"  - Schema类型: {end_schema.get('type')}")
        
        # 测试条件节点
        from src.core.workflow.graph.nodes.condition_node import ConditionNode
        condition_node = ConditionNode()
        condition_schema = condition_node.get_config_schema()
        print("✓ 条件节点get_config_schema()方法正常")
        print(f"  - Schema类型: {condition_schema.get('type')}")
        
        # 测试等待节点
        from src.core.workflow.graph.nodes.wait_node import WaitNode
        wait_node = WaitNode()
        wait_schema = wait_node.get_config_schema()
        print("✓ 等待节点get_config_schema()方法正常")
        print(f"  - Schema类型: {wait_schema.get('type')}")
        
        return True
        
    except Exception as e:
        print(f"✗ 节点Schema方法测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_config_loading():
    """测试配置加载"""
    print("\n=== 测试配置加载 ===")
    
    try:
        from src.core.workflow.config.node_config_loader import get_node_config_loader
        
        # 获取配置加载器
        loader = get_node_config_loader()
        print("✓ 节点配置加载器初始化成功")
        
        # 加载配置
        loader.load_configs()
        print("✓ 配置加载完成")
        
        # 测试获取LLM节点配置
        llm_config = loader.get_config('llm_node')
        print(f"✓ LLM节点配置获取成功，包含 {len(llm_config)} 个配置项")
        
        # 测试获取工具节点配置
        tool_config = loader.get_config('tool_node')
        print(f"✓ 工具节点配置获取成功，包含 {len(tool_config)} 个配置项")
        
        # 测试获取START节点配置
        start_config = loader.get_config('start_node')
        print(f"✓ START节点配置获取成功，包含 {len(start_config)} 个配置项")
        
        return True
        
    except Exception as e:
        print(f"✗ 配置加载测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("开始集成测试：Schema生成器和节点修改")
    print("=" * 50)
    
    results = []
    
    # 运行测试
    results.append(test_config_loading())
    results.append(test_schema_generator())
    results.append(test_node_schema_methods())
    
    # 输出结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = sum(results)
    total = len(results)
    
    print(f"通过: {passed}/{total}")
    
    if passed == total:
        print("🎉 所有测试通过！Schema生成器和节点修改工作正常。")
        return True
    else:
        print("❌ 部分测试失败，请检查错误信息。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)